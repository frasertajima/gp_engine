"""GP Engine (preview) — exact mixed-precision Gaussian-process regression
on consumer GPUs.

This is the self-contained Python wrapper around the CUDA Fortran solver core
`gp_solver.so` (which must sit next to this file). All GPU kernels — the
fused implicit-K RBF builders/matvecs and the FP32 SPD factorization with
log-determinant — live in the shared library; this module supplies ctypes
bindings, the FP64 iterative-refinement loop, and the fit/predict API.

Requirements: CuPy (CUDA 12.x), NumPy, a GPU with compute capability 8.6 or
8.9 (Ampere / Ada — the shipped binary targets cc86,cc89).

Quickstart:
    import cupy as cp
    from gp_engine import RBFKernel, gp_fit, gp_predict

    kern = RBFKernel(ell=0.3, sigma_f=1.0, sigma_n2=1e-2)
    fit  = gp_fit(kern, X, y)          # X (n,d) float64, d <= 16; y (n,)
    mean, var = gp_predict(fit, kern, X, X_star)
    fit.logdet                          # log|K + sigma_n^2 I| for the LML

Accuracy contract: the kernel system is factored in FP32 (tensor-class
throughput) and refined to FP64-class accuracy (relative residual ~1e-11)
with residuals computed against K regenerated on the fly from X — the n x n
kernel matrix is never stored in FP64. Operating envelope: condition number
kappa(K + sigma_n^2 I) <~ 1e7, i.e. GP regression with a real noise nugget.
Outside the envelope the engine fails DETECTABLY (FactorError, or
GPFit.converged == False) — never silently.
"""

import ctypes
import math
import os
from dataclasses import dataclass

import cupy as cp
import numpy as np

_MAX_D = 16

_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "gp_solver.so"))

_lib.py_rbf_build_f32.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_double, ctypes.c_double,
                                  ctypes.c_double, ctypes.c_int, ctypes.c_int]
_lib.py_rbf_build_f64.argtypes = _lib.py_rbf_build_f32.argtypes
_lib.py_rbf_matvec_f64.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_void_p, ctypes.c_double,
                                   ctypes.c_double, ctypes.c_double,
                                   ctypes.c_int, ctypes.c_int]
_lib.py_rbf_cross_matvec_f64.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.py_rbf_cross_build_f32.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.py_spd_factor.argtypes = [ctypes.c_void_p, ctypes.c_int,
                               ctypes.POINTER(ctypes.c_double),
                               ctypes.POINTER(ctypes.c_int)]
_lib.py_spd_potrs.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                              ctypes.c_int, ctypes.c_int,
                              ctypes.POINTER(ctypes.c_int)]
for _f in (_lib.py_rbf_build_f32, _lib.py_rbf_build_f64,
           _lib.py_rbf_matvec_f64, _lib.py_rbf_cross_matvec_f64,
           _lib.py_rbf_cross_build_f32, _lib.py_spd_factor,
           _lib.py_spd_potrs):
    _f.restype = None


class FactorError(RuntimeError):
    """FP32 POTRF failed: kappa exceeds the mixed-precision envelope."""


def _raise_on_info(info, where):
    if info > 0:
        raise FactorError(f"{where}: leading minor {info} not positive "
                          f"definite (FP32 kappa wall)")
    if info < 0:
        raise RuntimeError(f"{where}: gp_solver error {info} "
                           f"(-997 cuSOLVER, -998 handle, -999 args)")


class RBFKernel:
    """K_ij = sigma_f^2 exp(-||x_i-x_j||^2 / (2 ell^2)) + sigma_n^2 I, d<=16."""

    def __init__(self, ell, sigma_f=1.0, sigma_n2=1e-4):
        self.ell = float(ell)
        self.sigma_f2 = float(sigma_f) ** 2
        self.sigma_n2 = float(sigma_n2)

    def _scalars(self):
        return (1.0 / (2.0 * self.ell * self.ell), self.sigma_f2,
                self.sigma_n2)

    @staticmethod
    def _check_X(X):
        X = cp.ascontiguousarray(cp.asarray(X, dtype=cp.float64))
        n, d = X.shape
        if d > _MAX_D:
            raise ValueError(f"d={d} > {_MAX_D} not supported in this preview")
        return X, n, d

    def build(self, X, out):
        """Fill out (n x n, F-order, float32 or float64) incl. the nugget."""
        X, n, d = self._check_X(X)
        if not out.flags.f_contiguous:
            raise ValueError("out must be F-contiguous")
        fn = (_lib.py_rbf_build_f32 if out.dtype == cp.float32
              else _lib.py_rbf_build_f64)
        fn(X.data.ptr, out.data.ptr, *self._scalars(), n, d)

    def matvec(self, X, v):
        """(K + sigma_n^2 I) @ v in FP64, K regenerated from X on the fly."""
        X, n, d = self._check_X(X)
        v = cp.ascontiguousarray(cp.asarray(v, dtype=cp.float64))
        y = cp.empty(n, dtype=cp.float64)
        _lib.py_rbf_matvec_f64(X.data.ptr, v.data.ptr, y.data.ptr,
                               *self._scalars(), n, d)
        return y

    def cross_matvec(self, Xstar, X, a):
        """K(X*, X) @ a in FP64 (predictive mean core). No nugget."""
        Xs, m, d = self._check_X(Xstar)
        X, n, d2 = self._check_X(X)
        if d != d2:
            raise ValueError("Xstar and X dimension mismatch")
        a = cp.ascontiguousarray(cp.asarray(a, dtype=cp.float64))
        out = cp.empty(m, dtype=cp.float64)
        inv2l2, sigf2, _ = self._scalars()
        _lib.py_rbf_cross_matvec_f64(Xs.data.ptr, X.data.ptr, a.data.ptr,
                                     out.data.ptr, inv2l2, sigf2, m, n, d)
        return out

    def cross_build_f32(self, X, Xstar, out):
        """K(X, X*) into out (n x m, F-order FP32). No nugget."""
        X, n, d = self._check_X(X)
        Xs, m, d2 = self._check_X(Xstar)
        if d != d2:
            raise ValueError("Xstar and X dimension mismatch")
        if not out.flags.f_contiguous or out.dtype != cp.float32:
            raise ValueError("out must be F-contiguous float32")
        inv2l2, sigf2, _ = self._scalars()
        _lib.py_rbf_cross_build_f32(X.data.ptr, Xs.data.ptr, out.data.ptr,
                                    inv2l2, sigf2, n, m, d)


def spd_factor_inplace(K32):
    """In-place FP32 Cholesky (lower) of K32 (n x n, F-order).

    Returns log|K| accumulated in FP64. Raises FactorError if K32 is not
    positive definite in FP32 (the kappa wall — fall back per the docs)."""
    n = K32.shape[0]
    logdet = ctypes.c_double(0.0)
    info = ctypes.c_int(0)
    _lib.py_spd_factor(K32.data.ptr, n, ctypes.byref(logdet),
                       ctypes.byref(info))
    _raise_on_info(info.value, "py_spd_factor")
    return logdet.value


def potrs_inplace(L32, b):
    """Solve L L^T x = b against the factor; b (n,) or (n,nrhs) overwritten."""
    n = L32.shape[0]
    nrhs = 1 if b.ndim == 1 else b.shape[1]
    info = ctypes.c_int(0)
    _lib.py_spd_potrs(L32.data.ptr, b.data.ptr, n, nrhs, ctypes.byref(info))
    _raise_on_info(info.value, "py_spd_potrs")


def spd_solve_ir(L32, kernel, X, y, tol=1e-11, max_ir=10):
    """FP64 iterative refinement against the FP32 factor.

    Residuals use kernel.matvec (implicit K — nothing stored in FP64).
    Returns (alpha, relres, n_ir, converged)."""
    ynorm = float(cp.linalg.norm(y))
    alpha = cp.zeros(y.shape[0], dtype=cp.float64)
    r = y.copy()
    relres, prev, rises = 1.0, math.inf, 0
    for it in range(1, max_ir + 1):
        rnorm = float(cp.linalg.norm(r))
        if rnorm == 0.0:
            return alpha, 0.0, it - 1, True
        r32 = (r / rnorm).astype(cp.float32)
        potrs_inplace(L32, r32)
        alpha += rnorm * r32.astype(cp.float64)
        r = y - kernel.matvec(X, alpha)
        relres = float(cp.linalg.norm(r)) / ynorm
        if relres <= tol:
            return alpha, relres, it, True
        rises = rises + 1 if relres > prev else 0
        if rises >= 2:
            break
        prev = relres
    return alpha, relres, max_ir, False


@dataclass
class GPFit:
    alpha: cp.ndarray      # (K + sigma_n^2 I)^-1 y, FP64
    logdet: float          # log|K + sigma_n^2 I| from the FP32 factor
    relres: float
    n_ir: int
    converged: bool
    L32: cp.ndarray        # FP32 Cholesky factor (kept for prediction)


def gp_fit(kernel, X, y, tol=1e-11, max_ir=10):
    """Exact GP training solve: build K in FP32, factor, refine to FP64."""
    X = cp.ascontiguousarray(cp.asarray(X, dtype=cp.float64))
    y = cp.ascontiguousarray(cp.asarray(y, dtype=cp.float64))
    n = X.shape[0]
    K32 = cp.empty((n, n), dtype=cp.float32, order="F")
    kernel.build(X, K32)
    logdet = spd_factor_inplace(K32)
    alpha, relres, n_ir, ok = spd_solve_ir(K32, kernel, X, y,
                                           tol=tol, max_ir=max_ir)
    return GPFit(alpha=alpha, logdet=logdet, relres=relres,
                 n_ir=n_ir, converged=ok, L32=K32)


def gp_predict(fit, kernel, X, Xstar, include_noise=False, batch=4096):
    """Predictive mean and variance at Xstar from a GPFit.

    Mean: exact FP64 cross-kernel matvec. Variance: batched FP32 triangular
    solves against the kept factor ("factor once, solve many"); accuracy
    ~1e-6 sigma_f^2 absolute — well below any real noise floor."""
    import cupyx.scipy.linalg as _cpx

    Xs = cp.ascontiguousarray(cp.asarray(Xstar, dtype=cp.float64))
    m = Xs.shape[0]
    n = fit.L32.shape[0]
    mean = kernel.cross_matvec(Xs, X, fit.alpha)
    prior = kernel.sigma_f2 + (kernel.sigma_n2 if include_noise else 0.0)
    var = cp.empty(m, dtype=cp.float64)
    Kbuf = cp.empty((n, batch), dtype=cp.float32, order="F")
    for j0 in range(0, m, batch):
        j1 = min(j0 + batch, m)
        Kb = Kbuf[:, :j1 - j0]
        kernel.cross_build_f32(X, Xs[j0:j1], Kb)
        V = _cpx.solve_triangular(fit.L32, Kb, lower=True,
                                  overwrite_b=True, check_finite=False)
        var[j0:j1] = prior - cp.einsum("ij,ij->j", V, V).astype(cp.float64)
    del Kbuf
    cp.maximum(var, 0.0, out=var)
    return mean, var
