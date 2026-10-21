"""Maximum-diversification portfolio on a 10-asset multi-sleeve universe.

Session 2L variant of ``max_diversification``, added in response to the
Session 2K-4 dedup-bar breach. The 3-asset original is preserved as the
documented small-N convergence case.

Foundational: Choueifaty, Y. & Coignard, Y. (2008). *Toward Maximum
Diversification*. J Portfolio Management 35(1), 40-51.
DOI: https://doi.org/10.3905/JPM.2008.35.1.40

Primary methodology: Choueifaty, Y., Froidure, T. & Reynier, J. (2011).
*Properties of the Most Diversified Portfolio*.
DOI: https://doi.org/10.2139/ssrn.1895459
"""

from __future__ import annotations

from alphakit.strategies.macro.max_diversification_10asset.strategy import (
    MaxDiversification10Asset,
)

__all__ = ["MaxDiversification10Asset"]
