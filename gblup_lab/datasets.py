"""Read MPDOK's already-prepared genomic panels in place — no copying.

MPDOK/gblup/data/*.npz were built once by MPDOK/gblup/prepare_data.py from the
public BGLR / G2F sources (see MPDOK/gblup/data/SOURCES.md for exact URLs and
citations). This lab reuses those files directly; see LAB_PLAN.md "Non-goals".
"""

import os

import numpy as np

_MPDOK_GBLUP = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "fortran/examples/collected_examples/matrix_dot/tensor13/"
    "tensor_core_engine_v5/MPDOK/gblup"))
_DATA = os.path.join(_MPDOK_GBLUP, "data")


def load_wheat():
    """BGLR wheat (Crossa et al. 2010): N=599, M=1279 SNPs, 4 grain-yield
    environments (E1-E4).

    Returns dict: X (599,1279) float32 marker dosage (0/1, biallelic coding),
    Y (599,4), trait_names, A (599,599) published additive GRM (VanRaden, used
    in Phase 0/1), sets (599,) the BGLR 10-fold CV assignment (unused so far;
    MPDOK's own cv_lambda_sweep uses a fresh random 5-fold split instead).
    """
    d = np.load(os.path.join(_DATA, "wheat.npz"))
    return {k: d[k] for k in d.files}


def load_mice():
    """BGLR mice (Valdar et al. 2006): N=1814, M=10346 SNPs, BMI + body
    length. X (1814,10346) float32 dosage (0/1/2), A (1814,1814) published
    additive GRM, chrom/mbp marker metadata (unused so far).
    """
    d = np.load(os.path.join(_DATA, "mice.npz"))
    return {k: d[k] for k in d.files}


def load_g2f():
    """G2F maize inbred genotypes: N=2193, M=48580 SNPs (int8 dosage, no
    prebuilt GRM -- Phase 1+ builds it from X via the GEMM-trick).
    """
    d = np.load(os.path.join(_DATA, "g2f.npz"))
    return {k: d[k] for k in d.files}


def kfold_indices(n, k=5, seed=42):
    """Same split MPDOK/gblup/grm.py uses -- kept identical so Phase 0 numbers
    are comparable fold-for-fold, not just in aggregate."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    folds = np.array_split(idx, k)
    splits = []
    for i in range(k):
        val = folds[i]
        train = np.concatenate([folds[j] for j in range(k) if j != i])
        splits.append((train, val))
    return splits
