"""Phase 3 (LAB_PLAN.md stretch goal): parental -> hybrid GRM for the G2F
maize hybrid yield table.

MPDOK's gblup lab never touched this file -- it only used the *inbred*
genotype panel (`g2f.npz`, N=2193) with a simulated phenotype (h2=0.50,
README: "Phenotype: Simulated with h^2=0.50 using real GRM structure --
hybrid yield data is in a separate G2F repository"). `1_Training_Trait_Data
_2014_2023.csv` (also sitting in MPDOK/gblup/data/, from the G2F 2024-2025
GxE Prediction Competition release) has the real thing: 161,534 plot records
with REAL yield, for hybrids whose both parents are in the genotyped panel.
Genuinely new ground for both labs.

Hybrid genotype: standard additive approximation (Bernardo 1994; Technow
et al. 2014 use the equivalent two-kernel GCA form) -- a hybrid's marker
dosage is the average of its two parents' dosage,
    X_hybrid = (X_parent1 + X_parent2) / 2
which is the expected gamete-transmission dosage under random assortment,
no dominance term. This lets the hybrid panel go through the exact same
`marker_kernel.py` / `gblup_hyperopt.py` pipeline as wheat/mice -- no new
engine code needed, just a new X/y pair.

IMPORTANT PROTOCOL CAVEAT (checked, not assumed -- see RESULTS_PHASE3.md):
the actual G2F 2024-2025 GxE Prediction Competition trains on 2014-2023 and
scores on a held-out **2024** season (1,063 hybrids, 23 new locations) --
genuinely new environments, not just new hybrid combinations. That 2024 set
is NOT in `1_Training_Trait_Data_2014_2023.csv` (the file name says so) and
is not local -- per the competition's own paper, it "was not available to
participants during the competition, but is now included to allow
post-competition model validation," i.e. it could be fetched separately, but
that's a new-data-acquisition decision, not made here. This module instead
does a **random hybrid-combination holdout on 2014-2023 data only**: yield
is averaged across all of a hybrid's plot records (any year/environment) to
one value per unique Parent1 x Parent2 combination, then split the same
5-fold way as wheat/mice. This tests "known parents, unseen combination,"
NOT "known hybrids, unseen year" -- a materially easier task than the real
competition. Do not compare these r values to a competition leaderboard.
"""

import os

import numpy as np
import pandas as pd

_MPDOK_GBLUP = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..",
    "fortran/examples/collected_examples/matrix_dot/tensor13/"
    "tensor_core_engine_v5/MPDOK/gblup"))
_DATA = os.path.join(_MPDOK_GBLUP, "data")


def load_hybrid_dataset():
    """Returns dict(X (n_hybrids, M) float32 averaged-parent dosage,
    y (n_hybrids,) float64 mean yield (Mg/ha, raw units -- not standardized,
    unlike wheat/mice's Y), n_records (n_hybrids,) int, parent1/parent2
    (n_hybrids,) str -- the two genotyped inbred parent names.
    """
    df = pd.read_csv(os.path.join(_DATA, "1_Training_Trait_Data_2014_2023.csv"))
    g2f = np.load(os.path.join(_DATA, "g2f.npz"), allow_pickle=True)
    samples = np.asarray([str(s) for s in g2f["samples"]])
    idx_of = {s: i for i, s in enumerate(samples)}
    X_inbred = g2f["X"]   # (2193, 48580) float32 dosage

    mask = (df["Hybrid_Parent1"].isin(idx_of) & df["Hybrid_Parent2"].isin(idx_of)
           & df["Yield_Mg_ha"].notna())
    sub = df.loc[mask]
    agg = sub.groupby(["Hybrid_Parent1", "Hybrid_Parent2"])["Yield_Mg_ha"] \
        .agg(["mean", "count"]).reset_index()

    p1_idx = agg["Hybrid_Parent1"].map(idx_of).to_numpy()
    p2_idx = agg["Hybrid_Parent2"].map(idx_of).to_numpy()
    X_hybrid = ((X_inbred[p1_idx].astype(np.float64)
                + X_inbred[p2_idx].astype(np.float64)) / 2.0).astype(np.float32)

    return dict(X=X_hybrid, y=agg["mean"].to_numpy(dtype=np.float64),
               n_records=agg["count"].to_numpy(),
               parent1=agg["Hybrid_Parent1"].to_numpy(),
               parent2=agg["Hybrid_Parent2"].to_numpy())
