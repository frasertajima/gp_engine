"""Spatial kernel builder -- repoints gblup_lab's domain-agnostic GEMM-trick
kernel machinery (marker_kernel.py) at fleet site lat/lon coordinates
instead of SNP marker dosages, the same move climate_cat_lab/spatial_kernel.py
and cvar_gp_lab/asset_kernel.py already made. Same identity, same code;
d=2 here (lat, lon) so the GEMM trick isn't doing the heavy lifting it does
for gblup_lab's thousands-of-markers case, but reusing the identical
function keeps the pattern -- and the correctness -- consistent across
every lab that's repointed it.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gblup_lab"))
from marker_kernel import (  # noqa: E402
    apply_kernel,
    cross_squared_dist,
    median_dist_scale,
    squared_dist_matrix,
)

__all__ = ["apply_kernel", "cross_squared_dist", "median_dist_scale", "squared_dist_matrix"]
