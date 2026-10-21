"""Long-only minimum-variance portfolio on a 10-asset multi-sleeve universe.

Session 2L variant of ``min_variance_gtaa``, added in response to the
Session 2K-4 dedup-bar breach. The 3-asset original is preserved as the
documented small-N convergence case.

Foundational and primary methodology: Haugen, R. A. & Baker, N. L.
(1991). *The Efficient Market Inefficiency of Capitalization-Weighted
Stock Portfolios*. J Portfolio Management 17(3), 35-40.
DOI: https://doi.org/10.3905/jpm.1991.409335
"""

from __future__ import annotations

from alphakit.strategies.macro.min_variance_gtaa_10asset.strategy import (
    MinVarianceGtaa10Asset,
)

__all__ = ["MinVarianceGtaa10Asset"]
