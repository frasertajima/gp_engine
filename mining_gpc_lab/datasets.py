"""Read mining_mpdok's raw NURE-HSSR CSV in place -- no copying, and derives
the ore/waste classification label this lab needs (mining_mpdok itself never
built one; it only ever did continuous grade regression).

Reproduces `mining_mpdok/01_data.ipynb`'s exact Carlin Trend filter (bounding
box + drop non-positive Au, the below-detection-limit artifact) so sample
counts match that notebook's numbers (4,106 samples) and this lab's results
are directly comparable to the existing masking-effect figures. See
LAB_PLAN.md "Data" and "Phase 0".
"""

import csv
import os

import numpy as np

_MPDOK_MINING = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "fortran/examples/collected_examples/matrix_dot/tensor13/"
    "tensor_core_engine_v5/MPDOK/mining_mpdok"))
_RAW_CSV = os.path.join(_MPDOK_MINING, "nevada_nure_raw.csv")

# Carlin Trend bounding box -- identical to 01_data.ipynb's LAT_MIN/LAT_MAX/
# LON_MIN/LON_MAX, kept as the same four constants under the same names.
LAT_MIN, LAT_MAX = 39.5, 42.0
LON_MIN, LON_MAX = -117.5, -114.5

# Carlin-type pathfinder suite already present in the raw CSV (As/Sb/Tl are
# the classic arsenian-pyrite pathfinders per mining_mpdok's README; Ag/Cu/Zn
# included as a base-metal contrast group). All six are strictly positive
# within the Carlin Trend subset (checked directly against the raw CSV -- no
# below-detection-limit negatives here, unlike Au), so no cleaning beyond the
# Au filter is needed before log-transforming them.
PATHFINDER_ELEMENTS = ["As_ppm", "Sb_ppm", "Ag_ppm", "Cu_ppm", "Zn_ppm", "Tl_ppm"]

_R_EARTH_KM = 6371.0


def _load_raw_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _to_float(rows, col):
    return np.array([float(r[col]) for r in rows], dtype=np.float64)


def load_carlin_trend(path=_RAW_CSV, cutoff_quantile=0.95):
    """Loads and filters the raw CSV exactly as `01_data.ipynb` does:
    Nevada -> Carlin Trend bounding box -> drop Au_sq_ppm <= 0 (instrument
    artifact below detection limit). n=4,106, matching the notebook and
    LAB_PLAN.md.

    Returns a dict:
      lat, lon         (n,) degrees, NAD27 (unchanged -- see mining_mpdok's
                        own note that the WGS84 shift is negligible here)
      x_km, y_km        (n,) local equirectangular projection centered on
                        the Carlin Trend centroid, for a kernel whose ARD
                        lengthscale is interpretable in km against the
                        already-fitted variogram range (ell=34.4 km)
      au                (n,) raw Au ppm
      log_au             (n,) natural log Au (mining_mpdok's own convention --
                        gold is never analysed in raw space, see 01_data.ipynb)
      pathfinders       dict element -> (n,) raw ppm, for PATHFINDER_ELEMENTS
      log_pathfinders    dict element -> (n,) log-ppm
      au_cutoff          scalar Au ppm threshold at `cutoff_quantile`
      label              (n,) int64, 1 = ore (au >= au_cutoff), 0 = waste
    """
    rows = _load_raw_rows(path)
    lat_all = _to_float(rows, "Lat_NAD27")
    lon_all = _to_float(rows, "Long_NAD27")
    au_all = _to_float(rows, "Au_sq_ppm")

    in_bbox = ((lat_all >= LAT_MIN) & (lat_all <= LAT_MAX) &
               (lon_all >= LON_MIN) & (lon_all <= LON_MAX))
    keep = in_bbox & (au_all > 0)

    ct_rows = [r for r, k in zip(rows, keep) if k]
    lat = lat_all[keep]
    lon = lon_all[keep]
    au = au_all[keep]

    lat0, lon0 = lat.mean(), lon.mean()
    lat0_rad = np.radians(lat0)
    x_km = (lon - lon0) * np.cos(lat0_rad) * np.radians(1.0) * _R_EARTH_KM
    y_km = (lat - lat0) * np.radians(1.0) * _R_EARTH_KM

    pathfinders = {el: _to_float(ct_rows, el) for el in PATHFINDER_ELEMENTS}
    log_pathfinders = {el: np.log(v) for el, v in pathfinders.items()}

    au_cutoff = float(np.percentile(au, cutoff_quantile * 100.0))
    label = (au >= au_cutoff).astype(np.int64)

    return {
        "lat": lat, "lon": lon, "x_km": x_km, "y_km": y_km,
        "au": au, "log_au": np.log(au),
        "pathfinders": pathfinders, "log_pathfinders": log_pathfinders,
        "au_cutoff": au_cutoff, "cutoff_quantile": cutoff_quantile,
        "label": label,
    }


def spatial_features(data):
    """(n,2) [x_km, y_km] -- the Phase 0/1 baseline feature set, directly
    comparable to the fitted Matern-3/2 variogram (ell=34.4 km)."""
    return np.column_stack([data["x_km"], data["y_km"]])


def spatial_pathfinder_features(data):
    """(n,8) [x_km, y_km, log(As), log(Sb), log(Ag), log(Cu), log(Zn),
    log(Tl)] -- the Phase 4 ARD feature set. d=8, well inside gp_engine's
    validated d<=32 ARD envelope."""
    cols = [data["x_km"], data["y_km"]]
    cols += [data["log_pathfinders"][el] for el in PATHFINDER_ELEMENTS]
    return np.column_stack(cols)


def _stratified_split(X, y, frac_train, frac_val, rng):
    """Splits (X, y) into train/val/test, preserving class balance in each
    split. Matters more here than in place_gpc_lab: at a P95 cutoff the
    positive (ore) class is ~5% of the data, so a plain shuffle-split risks
    a test slice with very few or zero positives."""
    idx_by_class = {c: rng.permutation(np.flatnonzero(y == c)) for c in np.unique(y)}
    train_idx, val_idx, test_idx = [], [], []
    for c, idx in idx_by_class.items():
        n = len(idx)
        n_tr = int(round(n * frac_train))
        n_val = int(round(n * frac_val))
        train_idx.append(idx[:n_tr])
        val_idx.append(idx[n_tr:n_tr + n_val])
        test_idx.append(idx[n_tr + n_val:])
    train_idx = rng.permutation(np.concatenate(train_idx))
    val_idx = rng.permutation(np.concatenate(val_idx))
    test_idx = rng.permutation(np.concatenate(test_idx))
    return (X[train_idx], y[train_idx]), (X[val_idx], y[val_idx]), (X[test_idx], y[test_idx])


def load_split(feature_set="spatial", frac_train=0.6, frac_val=0.2, seed=0,
               cutoff_quantile=0.95, path=_RAW_CSV):
    """Stratified (train, val, test) split, each an (X, y) pair.

    feature_set: "spatial" (d=2, Phase 1 baseline) or "spatial_pathfinder"
    (d=8, Phase 4). Remaining fraction (1 - frac_train - frac_val) -> test.
    """
    if feature_set not in ("spatial", "spatial_pathfinder"):
        raise ValueError(f"unknown feature_set {feature_set!r}")
    data = load_carlin_trend(path=path, cutoff_quantile=cutoff_quantile)
    X = (spatial_features(data) if feature_set == "spatial"
         else spatial_pathfinder_features(data))
    y = data["label"]
    rng = np.random.default_rng(seed)
    return _stratified_split(X, y, frac_train, frac_val, rng)


if __name__ == "__main__":
    data = load_carlin_trend()
    print(f"Carlin Trend samples: {len(data['au']):,}")
    print(f"Au cutoff (p{data['cutoff_quantile']*100:.0f}): {data['au_cutoff']:.4f} ppm")
    print(f"Ore (label=1): {data['label'].sum():,}  "
          f"Waste (label=0): {(data['label'] == 0).sum():,}  "
          f"({data['label'].mean()*100:.1f}% ore)")

    for feature_set in ("spatial", "spatial_pathfinder"):
        (Xtr, ytr), (Xv, yv), (Xte, yte) = load_split(feature_set=feature_set)
        print(f"\n[{feature_set}] d={Xtr.shape[1]}")
        print("  train", Xtr.shape, dict(zip(*np.unique(ytr, return_counts=True))))
        print("  val  ", Xv.shape, dict(zip(*np.unique(yv, return_counts=True))))
        print("  test ", Xte.shape, dict(zip(*np.unique(yte, return_counts=True))))
