"""Loads the multi-state NURE-HSSR reanalysis CSV (see data/SOURCES.md),
filters to Arizona, and derives the ore/waste classification label this lab
needs (same P95-cutoff convention as mining_gpc_lab's Au lab, applied to Cu
here).

Whole-state Arizona (not a tighter named district cluster) per LAB_PLAN.md's
recommendation -- the classic US porphyry Cu(-Mo) province (Morenci, Bagdad,
Ray, Miami-Globe, Safford, Resolution/Superior, Sierrita/Twin Buttes,
Mission, Silver Bell), 7,633 samples, no filtering beyond State=='AZ'.

Pathfinder suite: Mo/Re (the proximal Cu-Mo-potassic-core pair -- Re
strongly partitions into molybdenite, a well-established Mo pathfinder) and
Au/Ag/Pb/Zn (the classic Lowell & Guilbert 1970 distal halo elements) --
genuinely different pathfinder theory than mining_gpc_lab's Carlin-Trend
As/Sb/Tl, not a relabeling of the same story. See LAB_PLAN.md "What's new."
"""

import csv
import os

import numpy as np

_HERE = os.path.dirname(__file__)
_RAW_CSV = os.path.join(_HERE, "data", "nure_multistate_az_ca_id_mt_nv_nm_ut_or.csv")

STATE = "AZ"

# Lowell-Guilbert proximal pair (Mo, its Re pathfinder) + distal halo
# (Au/Ag/Pb/Zn). Re is 91% below detection in this dataset (checked
# directly, 2026-07-18) -- physically sensible, since detectable Re only
# shows up near real molybdenite mineralization, not background sediment --
# but it means Re's usefulness as a *continuous* log-feature is limited;
# flagged here, not discovered downstream. Au is ~10% below detection.
# Both are floor-imputed (see _log_floor), not dropped, so a pathfinder's
# censoring rate doesn't shrink the primary Cu dataset.
PATHFINDER_ELEMENTS = ["Mo_ppm", "Re_ppm", "Au_sq_ppm", "Ag_ppm", "Pb_ppm", "Zn_ppm"]

_R_EARTH_KM = 6371.0


def _load_raw_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _to_float(rows, col):
    out = np.full(len(rows), np.nan, dtype=np.float64)
    for i, r in enumerate(rows):
        v = r.get(col, "")
        if v not in ("", None):
            out[i] = float(v)
    return out


def _log_floor(values):
    """log-transform with below-detection values (<=0, NURE's convention
    for "below the instrument's detection limit") floored at half the
    column's minimum positive value, rather than dropped -- standard
    censored-geochemistry practice, and it keeps rows with a censored
    pathfinder reading in the dataset (only the target Cu_ppm ever forces a
    row out, same as mining_gpc_lab's Au filter)."""
    values = np.asarray(values, dtype=np.float64)
    positive = values[values > 0]
    floor = positive.min() / 2.0 if positive.size else 1e-3
    floored = np.where(values > 0, values, floor)
    return np.log(floored)


def load_arizona(cutoff_quantile=0.95):
    """Loads and filters the raw CSV to Arizona (State == 'AZ'). No
    below-detection filtering on Cu_ppm itself -- checked directly
    (2026-07-18): zero AZ samples have Cu_ppm <= 0, unlike the pathfinder
    columns, so no row-dropping is needed for the target.

    Returns a dict:
      lat, lon         (n,) degrees, NAD27
      x_km, y_km        (n,) local equirectangular projection centered on
                        the Arizona subset's own centroid
      cu                (n,) raw Cu ppm
      log_cu             (n,) natural log Cu ppm
      pathfinders        dict element -> (n,) raw ppm (NaN-free; Cu_ppm==0
                        rows would be dropped here if any existed, matching
                        mining_gpc_lab's convention, but none do)
      log_pathfinders    dict element -> (n,) floor-imputed log-ppm
      cu_cutoff          scalar Cu ppm threshold at `cutoff_quantile`
      label              (n,) int64, 1 = ore (cu >= cu_cutoff), 0 = waste
    """
    rows = _load_raw_rows(_RAW_CSV)
    state = np.array([r["State"] for r in rows])
    keep = state == STATE

    az_rows = [r for r, k in zip(rows, keep) if k]
    lat = _to_float(az_rows, "Lat_NAD27")
    lon = _to_float(az_rows, "Long_NAD27")
    cu = _to_float(az_rows, "Cu_ppm")

    valid = cu > 0  # checked: 0 AZ rows fail this, kept for parity with mining_gpc_lab's pattern
    az_rows = [r for r, v in zip(az_rows, valid) if v]
    lat, lon, cu = lat[valid], lon[valid], cu[valid]

    lat0, lon0 = lat.mean(), lon.mean()
    lat0_rad = np.radians(lat0)
    x_km = (lon - lon0) * np.cos(lat0_rad) * np.radians(1.0) * _R_EARTH_KM
    y_km = (lat - lat0) * np.radians(1.0) * _R_EARTH_KM

    pathfinders = {el: _to_float(az_rows, el) for el in PATHFINDER_ELEMENTS}
    log_pathfinders = {el: _log_floor(v) for el, v in pathfinders.items()}

    cu_cutoff = float(np.percentile(cu, cutoff_quantile * 100.0))
    label = (cu >= cu_cutoff).astype(np.int64)

    return {
        "lat": lat, "lon": lon, "x_km": x_km, "y_km": y_km,
        "cu": cu, "log_cu": np.log(cu),
        "pathfinders": pathfinders, "log_pathfinders": log_pathfinders,
        "cu_cutoff": cu_cutoff, "cutoff_quantile": cutoff_quantile,
        "label": label,
    }


def spatial_features(data):
    """(n,2) [x_km, y_km] -- the Phase 1 baseline feature set."""
    return np.column_stack([data["x_km"], data["y_km"]])


def spatial_pathfinder_features(data):
    """(n,8) [x_km, y_km, log(Mo), log(Re), log(Au), log(Ag), log(Pb),
    log(Zn)] -- the Phase 4 ARD feature set. d=8, same as mining_gpc_lab's,
    well inside gp_engine's validated d<=32 ARD envelope."""
    cols = [data["x_km"], data["y_km"]]
    cols += [data["log_pathfinders"][el] for el in PATHFINDER_ELEMENTS]
    return np.column_stack(cols)


def _stratified_split(X, y, frac_train, frac_val, rng):
    """Splits (X, y) into train/val/test, preserving class balance in each
    split. Same convention as mining_gpc_lab/datasets.py -- matters here
    too, since a P95 cutoff gives a ~5% positive class."""
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
               cutoff_quantile=0.95):
    """Stratified (train, val, test) split, each an (X, y) pair.

    feature_set: "spatial" (d=2, Phase 1 baseline) or "spatial_pathfinder"
    (d=8, Phase 4). Remaining fraction (1 - frac_train - frac_val) -> test.
    """
    if feature_set not in ("spatial", "spatial_pathfinder"):
        raise ValueError(f"unknown feature_set {feature_set!r}")
    data = load_arizona(cutoff_quantile=cutoff_quantile)
    X = (spatial_features(data) if feature_set == "spatial"
         else spatial_pathfinder_features(data))
    y = data["label"]
    rng = np.random.default_rng(seed)
    return _stratified_split(X, y, frac_train, frac_val, rng)


if __name__ == "__main__":
    data = load_arizona()
    print(f"Arizona samples: {len(data['cu']):,}")
    print(f"Cu cutoff (p{data['cutoff_quantile']*100:.0f}): {data['cu_cutoff']:.2f} ppm")
    print(f"Ore (label=1): {data['label'].sum():,}  "
          f"Waste (label=0): {(data['label'] == 0).sum():,}  "
          f"({data['label'].mean()*100:.1f}% ore)")
    print(f"x_km range: [{data['x_km'].min():.1f}, {data['x_km'].max():.1f}]  "
          f"y_km range: [{data['y_km'].min():.1f}, {data['y_km'].max():.1f}]")

    for el in PATHFINDER_ELEMENTS:
        v = data["pathfinders"][el]
        n_below = int((v <= 0).sum())
        print(f"  {el:10s} below-detection: {n_below}/{len(v)} ({100*n_below/len(v):.1f}%)  "
              f"range=[{v.min():.4g}, {v.max():.4g}]")

    for feature_set in ("spatial", "spatial_pathfinder"):
        (Xtr, ytr), (Xv, yv), (Xte, yte) = load_split(feature_set=feature_set)
        print(f"\n[{feature_set}] d={Xtr.shape[1]}")
        print("  train", Xtr.shape, dict(zip(*np.unique(ytr, return_counts=True))))
        print("  val  ", Xv.shape, dict(zip(*np.unique(yv, return_counts=True))))
        print("  test ", Xte.shape, dict(zip(*np.unique(yte, return_counts=True))))
