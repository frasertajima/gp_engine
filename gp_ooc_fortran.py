"""CUDA Fortran backend for the GP engine's out-of-core solver
(gp_ooc_solver.so).

Thin wrapper only, per PLAN.md Sec.6b's language policy: all panel storage,
tiering, streaming, and the factor/forward/backward math live in
gp_ooc_solver.cuf (design: OOC_FORTRAN_DESIGN.md). This module's job is
launch/glue — ctypes argtypes, pointer plumbing, and the outer IR
iteration/convergence loop (reusing gp_core.spd_solve_ir exactly as
gp_fortran.py already does for the in-core backend).

Same call shape as gp_ooc.py's ooc_gp_fit/ooc_predict, so callers (the lab
harness, run_benchmark.py) don't need to change to switch backends.
"""

import ctypes
import os

import cupy as cp

import gp_core
from gp_core import FactorError, spd_solve_ir

_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "gp_ooc_solver.so"))

_lib.py_ooc_init.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,   # n,d,b,R
    ctypes.c_void_p,                                          # il2_ptr
    ctypes.c_double, ctypes.c_double, ctypes.c_int,            # sigf2,sign2,kind
    ctypes.c_double,                                          # ram_budget_gb
    ctypes.c_void_p, ctypes.c_int,                             # backing_dir, len
    ctypes.POINTER(ctypes.c_int)]                              # info_out
_lib.py_ooc_factor.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_int)]
_lib.py_ooc_potrs.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
_lib.py_ooc_cross_var.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double, ctypes.c_void_p,
    ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
_lib.py_ooc_close.argtypes = []
for _f in (_lib.py_ooc_init, _lib.py_ooc_factor, _lib.py_ooc_potrs,
           _lib.py_ooc_cross_var, _lib.py_ooc_close):
    _f.restype = None


def _raise_on_info(info, where):
    if info > 0:
        raise FactorError(f"{where}: leading minor {info} not positive "
                          f"definite (FP32 kappa wall)")
    if info < 0:
        raise RuntimeError(f"{where}: gp_ooc_solver error {info} "
                           f"(-996 file I/O, -997 cuBLAS/cuSOLVER, "
                           f"-998 handle, -999 args)")


class OOCCholeskyF:
    """Streaming lower-Cholesky factor, panels/streaming owned by Fortran.

    Duck-types just enough of gp_ooc.py's OOCCholesky (`.shape`, `.n`,
    `.logdet`, `.potrs_inplace`) to drop into spd_solve_ir / ooc_predict
    unchanged."""

    def __init__(self, kernel, X, b=4096, R=8192, verbose=False,
                 backing=None, ram_budget_gb=44.0):
        # R=8192 is the config validated end-to-end at every scale up to
        # n=391,387 (R only affects chunking/VRAM, not numerics).
        self.kernel = kernel
        self.X = cp.ascontiguousarray(cp.asarray(X, dtype=cp.float64))
        self.n, self.d = self.X.shape
        self.b = int(b)
        self.R = int(R)
        self.verbose = verbose
        self.backing = backing
        self.shape = (self.n, self.n)   # duck-type for spd_solve_ir
        self.logdet = None
        self._closed = False

        # Mirror of the Fortran side's greedy tier rule (panel_alloc in
        # gp_ooc_solver.cuf): pinned RAM until ram_budget, then NVMe file.
        # Python-side bookkeeping only, for host_gb()/tier_summary()
        # reporting — the actual decisions live in Fortran.
        nt = (self.n + self.b - 1) // self.b
        budget = float(ram_budget_gb) * 1e9
        used = 0.0
        self._tier_gb = {"pinned": 0.0, "file": 0.0}
        for k in range(nt):
            nrem = self.n - k * self.b
            bk = min(self.b, nrem)
            nbytes = nrem * bk * 4.0
            if used + nbytes <= budget:
                used += nbytes
                self._tier_gb["pinned"] += nbytes / 1e9
            else:
                self._tier_gb["file"] += nbytes / 1e9

        il2 = self.kernel._il2_dev(self.d)
        if backing is not None:
            os.makedirs(backing, exist_ok=True)
            path_bytes = os.fsencode(backing)
            buf = ctypes.create_string_buffer(path_bytes, len(path_bytes))
            backing_ptr = ctypes.cast(buf, ctypes.c_void_p)
            backing_len = len(path_bytes)
            self._backing_buf = buf   # keep alive for the duration of the call
        else:
            backing_ptr = None
            backing_len = 0

        info = ctypes.c_int(0)
        _lib.py_ooc_init(self.n, self.d, self.b, self.R, il2.data.ptr,
                         self.kernel.sigma_f2, self.kernel.sigma_n2,
                         self.kernel.kind_id, float(ram_budget_gb),
                         backing_ptr, backing_len, ctypes.byref(info))
        _raise_on_info(info.value, "py_ooc_init")

    def factor(self):
        logdet = ctypes.c_double(0.0)
        info = ctypes.c_int(0)
        _lib.py_ooc_factor(self.X.data.ptr, ctypes.byref(logdet),
                           ctypes.byref(info))
        _raise_on_info(info.value, "py_ooc_factor")
        self.logdet = logdet.value
        return self.logdet

    def potrs_inplace(self, z):
        z = cp.ascontiguousarray(z)
        info = ctypes.c_int(0)
        _lib.py_ooc_potrs(z.data.ptr, ctypes.byref(info))
        _raise_on_info(info.value, "py_ooc_potrs")
        return z

    def cross_var(self, Xs, prior):
        """var(j) = prior - ||L^-1 K*[:,j]||^2 for a batch of test points."""
        Xs = cp.ascontiguousarray(cp.asarray(Xs, dtype=cp.float64))
        m = Xs.shape[0]
        var = cp.empty(m, dtype=cp.float64)
        info = ctypes.c_int(0)
        _lib.py_ooc_cross_var(self.X.data.ptr, Xs.data.ptr, float(prior),
                              var.data.ptr, m, ctypes.byref(info))
        _raise_on_info(info.value, "py_ooc_cross_var")
        return var

    def host_gb(self):
        return self._tier_gb["pinned"] + self._tier_gb["file"]

    def tier_summary(self):
        return ", ".join(f"{k} {v:.1f}GB"
                         for k, v in self._tier_gb.items() if v > 0)

    def close(self):
        if not self._closed:
            _lib.py_ooc_close()
            self._closed = True

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def ooc_gp_fit(kernel, X, y, b=4096, R=8192, tol=1e-10, max_ir=12,
               verbose=True, backing=None, ram_budget_gb=44.0):
    """Out-of-core GP fit via gp_ooc_solver.so: streaming factor + logdet +
    IR solve to FP64. Same return shape as gp_ooc.py's ooc_gp_fit."""
    import time
    X = cp.ascontiguousarray(cp.asarray(X, dtype=cp.float64))
    y = cp.ascontiguousarray(cp.asarray(y, dtype=cp.float64))
    fac = OOCCholeskyF(kernel, X, b=b, R=R, verbose=verbose, backing=backing,
                       ram_budget_gb=ram_budget_gb)
    t0 = time.perf_counter()
    fac.factor()
    t_factor = time.perf_counter() - t0
    t0 = time.perf_counter()
    alpha, relres, n_ir, ok = spd_solve_ir(
        fac, kernel, X, y, tol=tol, max_ir=max_ir,
        potrs=lambda F, r32: F.potrs_inplace(r32))
    cp.cuda.Device().synchronize()
    t_ir = time.perf_counter() - t0
    return dict(alpha=alpha, logdet=fac.logdet, relres=relres, n_ir=n_ir,
                converged=ok, factor=fac, t_factor=t_factor, t_ir=t_ir,
                t_total=t_factor + t_ir, host_gb=fac.host_gb())


def ooc_predict(fit, kernel, X, Xstar, include_noise=False, batch=2048):
    """Predictive mean + variance from an ooc_gp_fit() result dict.

    Mean: direct FP64 cross-kernel matvec (kernel-backend agnostic, exact
    given alpha). Variance: gp_ooc_solver.so's py_ooc_cross_var, batched
    over test points — the batching loop itself is thin orchestration
    (no memory/streaming complexity), consistent with PLAN.md Sec.6b."""
    fac = fit["factor"]
    X = cp.ascontiguousarray(cp.asarray(X, dtype=cp.float64))
    Xs = cp.ascontiguousarray(cp.asarray(Xstar, dtype=cp.float64))
    m = Xs.shape[0]
    mean = kernel.cross_matvec(Xs, X, fit["alpha"])
    prior = kernel.sigma_f2 + (kernel.sigma_n2 if include_noise else 0.0)
    var = cp.empty(m, dtype=cp.float64)
    for j0 in range(0, m, batch):
        j1 = min(j0 + batch, m)
        var[j0:j1] = fac.cross_var(Xs[j0:j1], prior)
    return mean, var
