"""CUDA Fortran backend for the GP engine (gp_solver.so).

Same API as gp_core; the fused kernels and SPD factor/solve run in the
.cuf-compiled shared library (MPDOK family style). gp_core.py remains the
numerical oracle — test_parity.py checks this backend against it.

The IR loop, hyperopt driver, and the variance trsm remain Python
(gp_core.spd_solve_ir / gp_predict work unchanged with this backend's
kernel + potrs).
"""

import ctypes
import os

import cupy as cp

import gp_core
from gp_core import FactorError, GPFit

_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "gp_solver.so"))

_lib.py_rbf_build_f32.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_double,
                                  ctypes.c_double, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int]
_lib.py_rbf_build_f64.argtypes = _lib.py_rbf_build_f32.argtypes
_lib.py_rbf_matvec_f64.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_double, ctypes.c_double,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.py_rbf_cross_matvec_f64.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_double,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.py_rbf_cross_build_f32.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
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


def _raise_on_info(info, where):
    if info > 0:
        raise FactorError(f"{where}: leading minor {info} not positive "
                          f"definite (FP32 kappa wall)")
    if info < 0:
        raise RuntimeError(f"{where}: gp_solver error {info} "
                           f"(-997 cuSOLVER, -998 handle, -999 args)")


class KernelF(gp_core.Kernel):
    """Stationary kernel (rbf/matern32/matern52, ARD) via gp_solver.so."""

    def build(self, X, out):
        X, n, d = self._check_X(X)
        if not out.flags.f_contiguous:
            raise ValueError("out must be F-contiguous")
        fn = (_lib.py_rbf_build_f32 if out.dtype == cp.float32
              else _lib.py_rbf_build_f64)
        fn(X.data.ptr, self._il2_dev(d).data.ptr, out.data.ptr,
           self.sigma_f2, self.sigma_n2, n, d, self.kind_id)

    def matvec(self, X, v):
        X, n, d = self._check_X(X)
        v = cp.ascontiguousarray(cp.asarray(v, dtype=cp.float64))
        y = cp.empty(n, dtype=cp.float64)
        _lib.py_rbf_matvec_f64(X.data.ptr, self._il2_dev(d).data.ptr,
                               v.data.ptr, y.data.ptr,
                               self.sigma_f2, self.sigma_n2, n, d,
                               self.kind_id)
        return y

    def cross_matvec(self, Xstar, X, a):
        Xs, m, d = self._check_X(Xstar)
        X, n, d2 = self._check_X(X)
        if d != d2:
            raise ValueError("Xstar and X dimension mismatch")
        a = cp.ascontiguousarray(cp.asarray(a, dtype=cp.float64))
        out = cp.empty(m, dtype=cp.float64)
        _lib.py_rbf_cross_matvec_f64(Xs.data.ptr, X.data.ptr,
                                     self._il2_dev(d).data.ptr, a.data.ptr,
                                     out.data.ptr, self.sigma_f2,
                                     m, n, d, self.kind_id)
        return out

    def cross_build_f32(self, X, Xstar, out):
        X, n, d = self._check_X(X)
        Xs, m, d2 = self._check_X(Xstar)
        if d != d2:
            raise ValueError("Xstar and X dimension mismatch")
        if not out.flags.f_contiguous or out.dtype != cp.float32:
            raise ValueError("out must be F-contiguous float32")
        _lib.py_rbf_cross_build_f32(X.data.ptr, Xs.data.ptr,
                                    self._il2_dev(d).data.ptr, out.data.ptr,
                                    self.sigma_f2, n, m, d, self.kind_id)


class RBFKernelF(KernelF):
    """Back-compat alias: RBF via the Fortran backend."""

    def __init__(self, ell, sigma_f=1.0, sigma_n2=1e-4):
        super().__init__(ell, sigma_f=sigma_f, sigma_n2=sigma_n2, kind="rbf")


def spd_factor_inplace(K32):
    """In-place FP32 POTRF via gp_solver.so; returns FP64 logdet."""
    n = K32.shape[0]
    logdet = ctypes.c_double(0.0)
    info = ctypes.c_int(0)
    _lib.py_spd_factor(K32.data.ptr, n, ctypes.byref(logdet),
                       ctypes.byref(info))
    _raise_on_info(info.value, "py_spd_factor")
    return logdet.value


def potrs_inplace(L32, b):
    """Solve against the Fortran-side factor; b (n,) or (n,nrhs) overwritten."""
    n = L32.shape[0]
    nrhs = 1 if b.ndim == 1 else b.shape[1]
    info = ctypes.c_int(0)
    _lib.py_spd_potrs(L32.data.ptr, b.data.ptr, n, nrhs, ctypes.byref(info))
    _raise_on_info(info.value, "py_spd_potrs")


def gp_fit(kernel, X, y, tol=1e-11, max_ir=10):
    """gp_core.gp_fit with the Fortran backend for build/factor/potrs."""
    X = cp.ascontiguousarray(cp.asarray(X, dtype=cp.float64))
    y = cp.ascontiguousarray(cp.asarray(y, dtype=cp.float64))
    n = X.shape[0]
    K32 = cp.empty((n, n), dtype=cp.float32, order="F")
    kernel.build(X, K32)
    logdet = spd_factor_inplace(K32)
    alpha, relres, n_ir, ok = gp_core.spd_solve_ir(
        K32, kernel, X, y, tol=tol, max_ir=max_ir, potrs=potrs_inplace)
    return GPFit(alpha=alpha, logdet=logdet, relres=relres,
                 n_ir=n_ir, converged=ok, L32=K32)
