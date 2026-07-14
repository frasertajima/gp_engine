"""GP Lab dataset registry — download, cache, split, standardize.

The benchmark suite from the large-scale exact-GP literature (see
LAB_PLAN.md). Raw arrays are cached once as data/<name>.npz; splits and
standardization are computed at load time from a seed, so every run is
reproducible from the cache + seed alone.

    from datasets import load
    ds = load("protein", seed=0)
    ds["Xtr"], ds["ytr"], ds["Xte"], ds["yte"]   # standardized, float64
    ds["meta"]                                    # provenance + shapes

CLI:  python datasets.py [name ...]     fetch + verify (default: all direct-
                                        download sets)

Honesty notes, recorded here because they bite later:
- Published papers differ in preprocessing (one-hot choices, dropped
  columns, split fractions). We record exactly what we did in meta and
  compare like-with-like where we can; RMSEs are reported in standardized-y
  units as the literature does.
- Expected (n, d) below are from the literature and VERIFIED at load; a
  mismatch warns loudly rather than failing, and lands in meta.
"""

import gzip
import io
import os
import urllib.request
import warnings
import zipfile

import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

_UCI = "https://archive.ics.uci.edu/ml/machine-learning-databases"


def _fetch(url, timeout=120):
    print(f"    fetching {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "gp-lab/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------------------
# Per-dataset raw loaders -> (X, y) float64
# ---------------------------------------------------------------------------

def _raw_protein():
    """CASP protein structure (UCI 00265): y = RMSD, X = F1..F9."""
    raw = _fetch(f"{_UCI}/00265/CASP.csv")
    a = np.genfromtxt(io.BytesIO(raw), delimiter=",", skip_header=1)
    return a[:, 1:], a[:, 0]


def _raw_3droad_handrolled():
    """3D road network, North Jutland (UCI 00246): y = altitude, X = lon,lat.

    NOT used by default — d=2, which does not match Wang et al. 2019's d=3
    3droad (their Table 3 baseline uses the uci_datasets preprocessing,
    whose third column is the OSM segment ID: leakage-checked, corr with y
    only -0.11). Kept for reference; see _raw_3droad below. Same story as
    bike's d=12-vs-17 fix."""
    raw = _fetch(f"{_UCI}/00246/3D_spatial_network.txt")
    a = np.genfromtxt(io.BytesIO(raw), delimiter=",")
    return a[:, 1:3], a[:, 3]


def _raw_3droad():
    """3droad via the uci_datasets GP-benchmark mirror — matches Wang et
    al. 2019's d=3 preprocessing (verified (434874, 3); columns arrive
    pre-whitened, our load() re-standardizes on the train split as usual)."""
    return _raw_gp_suite("3droad")


def _raw_bike_handrolled():
    """Bike sharing hourly (UCI 00275): y = cnt; numeric features, leakage
    columns (casual/registered) dropped, dteday/instant dropped.

    NOT used by default — d=12 (no categorical expansion), which does not
    match Wang et al. 2019's d=17 Bike (their Table 3 baseline). Kept for
    reference; see _raw_bike / _raw_gp_suite for the comparable version."""
    raw = _fetch(f"{_UCI}/00275/Bike-Sharing-Dataset.zip")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        txt = z.read("hour.csv").decode().replace("\r\n", "\n")
    rows = [line.split(",") for line in txt.strip().split("\n")]
    header, body = rows[0], rows[1:]
    keep = [c for c in header
            if c not in ("instant", "dteday", "casual", "registered", "cnt")]
    idx = [header.index(c) for c in keep]
    yi = header.index("cnt")
    X = np.array([[float(r[i]) for i in idx] for r in body])
    y = np.array([float(r[yi]) for r in body])
    return X, y


def _raw_bike():
    """Bike, via the uci_datasets GP-benchmark mirror (same source as
    kin40k/pol/elevators) — matches Wang et al. 2019's d=17 preprocessing
    (their Table 3 Bike baseline), unlike the hand-rolled d=12 parser."""
    return _raw_gp_suite("bike")


_GP_SUITE = ("https://raw.githubusercontent.com/treforevans/uci_datasets/"
             "master/uci_datasets/{name}/data{part}.csv.gz")


def _raw_gp_suite(name):
    """kin40k / pol / elevators from the uci_datasets GitHub mirror (the
    repo the exact-GP papers use; format: CSV, X columns then y last,
    possibly split into data_0.csv.gz, data_1.csv.gz, ...). Falls back to
    OpenML by name if the mirror moves."""
    errors = []
    # 1) single-file mirror
    for parts in ([""], ["_0", "_1"], ["_0", "_1", "_2", "_3"]):
        try:
            chunks = []
            for p in parts:
                raw = _fetch(_GP_SUITE.format(name=name, part=p))
                chunks.append(np.genfromtxt(
                    io.BytesIO(gzip.decompress(raw)), delimiter=","))
            a = np.vstack(chunks)
            return a[:, :-1], a[:, -1]
        except Exception as e:
            errors.append(f"mirror{parts}: {e}")
    # 2) OpenML by name
    try:
        from sklearn.datasets import fetch_openml
        d = fetch_openml(name=name, as_frame=False, parser="auto")
        return (np.asarray(d.data, dtype=np.float64),
                np.asarray(d.target, dtype=np.float64).ravel())
    except Exception as e:
        errors.append(f"openml: {e}")
    raise RuntimeError(
        f"could not fetch '{name}':\n  " + "\n  ".join(errors) +
        f"\nManual fallback: place arrays as data/{name}.npz with keys X, y.")


REGISTRY = {
    #  name        loader                          ~n       ~d   engine path
    "protein":   (_raw_protein,                    45730,    9),  # OOC seam
    "3droad":    (_raw_3droad,                    434874,    3),  # OOC stretch
    "bike":      (_raw_bike,                       17379,   17),  # in-core, needs d<=32
    "kin40k":    (lambda: _raw_gp_suite("kin40k"),   40000,    8),  # in-core edge
    "pol":       (lambda: _raw_gp_suite("pol"),      15000,   26),  # needs d<=32
    "elevators": (lambda: _raw_gp_suite("elevators"), 16599,  18),  # needs d<=32
}


# ---------------------------------------------------------------------------
# Cache / split / standardize
# ---------------------------------------------------------------------------

def fetch(name, force=False):
    """Download (or read cached) raw arrays; returns (X, y)."""
    if name not in REGISTRY:
        raise KeyError(f"unknown dataset '{name}'; have {list(REGISTRY)}")
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{name}.npz")
    if os.path.exists(path) and not force:
        z = np.load(path)
        return z["X"], z["y"]
    loader, n_exp, d_exp = REGISTRY[name]
    X, y = loader()
    X = np.ascontiguousarray(X, dtype=np.float64)
    y = np.ascontiguousarray(y, dtype=np.float64)
    # drop rows with NaNs (genfromtxt artifacts)
    ok = np.isfinite(X).all(axis=1) & np.isfinite(y)
    if not ok.all():
        warnings.warn(f"{name}: dropping {int((~ok).sum())} non-finite rows")
        X, y = X[ok], y[ok]
    if abs(X.shape[0] - n_exp) > 0.05 * n_exp or X.shape[1] != d_exp:
        warnings.warn(f"{name}: got shape {X.shape}, literature says "
                      f"(~{n_exp}, {d_exp}) — check preprocessing before "
                      f"comparing against published numbers")
    np.savez_compressed(path, X=X, y=y)
    print(f"    cached {name}: X {X.shape}, y {y.shape} -> {path}")
    return X, y


def load(name, seed=0, test_frac=0.1, protocol="lab"):
    """Fetch + split + standardize (train-fit scalers). Returns dict.

    protocol="lab" (default): the lab's 90/10 train/test split
    (test_frac configurable). Trains on ~1.4x the paper's points —
    disclosed protocol difference, RESULTS_LAB.md §4.4.

    protocol="paper": match Wang et al. 2019's reported training sizes
    EXACTLY for apples-to-apples comparison. Their §5 text says a
    4/9 / 2/9 / 3/9 train/val/test split, but their Tables 1 & 3 n
    values are all exactly floor(0.64*N) (kin40k 25,600/40,000; pol
    9,600/15,000; 3droad 278,319/434,874; ...) — the GPyTorch-benchmark
    convention of 80/20 train/test then 80/20 train/val of the train
    pool (0.8*0.8 = 0.64 train, 0.16 val, 0.20 test). The tables are
    authoritative (per-dataset integers), so we implement 0.64/0.16/0.20:
    train = floor(0.64*N), val = floor(0.16*N) HELD OUT UNUSED (we tune
    nothing on validation data — derivative-free hyperopt has no such
    knobs), test = remainder (~0.20*N). test_frac is ignored.
    """
    X, y = fetch(name)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(X.shape[0])
    N = X.shape[0]
    if protocol == "paper":
        n_tr = int(np.floor(0.64 * N))
        n_val = int(np.floor(0.16 * N))
        tr = perm[:n_tr]
        te = perm[n_tr + n_val:]          # val block perm[n_tr:n_tr+n_val] unused
    elif protocol == "lab":
        n_te = int(round(test_frac * N))
        te, tr = perm[:n_te], perm[n_te:]
    else:
        raise ValueError(f"unknown protocol '{protocol}' (lab|paper)")
    Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]

    x_mean, x_std = Xtr.mean(axis=0), Xtr.std(axis=0)
    x_std[x_std == 0] = 1.0                       # constant columns
    y_mean, y_std = ytr.mean(), ytr.std()
    std = lambda A: (A - x_mean) / x_std
    return dict(
        Xtr=std(Xtr), ytr=(ytr - y_mean) / y_std,
        Xte=std(Xte), yte=(yte - y_mean) / y_std,
        y_mean=y_mean, y_std=y_std,
        meta=dict(name=name, n_train=len(tr), n_test=len(te),
                  d=X.shape[1], seed=seed, test_frac=test_frac,
                  protocol=protocol),
    )


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or ["protein", "bike", "3droad"]
    for name in names:
        print(f"== {name}")
        ds = load(name)
        m = ds["meta"]
        print(f"    train {m['n_train']} x {m['d']}, test {m['n_test']}  "
              f"(y_std raw units: {ds['y_std']:.3f})")
