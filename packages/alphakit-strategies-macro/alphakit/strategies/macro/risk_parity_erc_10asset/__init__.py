"""Equal-Risk-Contribution portfolio on a 10-asset multi-sleeve universe.

Session 2L variant of ``risk_parity_erc_3asset``, added in response to the
Session 2K-4 dedup-bar breach. The 3-asset original is preserved as the
documented small-N convergence case.

Foundational: Maillard, S., Roncalli, T. & Teiletche, J. (2010).
*The Properties of Equally Weighted Risk Contribution Portfolios*.
J Portfolio Management 36(4), 60-70.
DOI: https://doi.org/10.3905/jpm.2010.36.4.060

Primary methodology: Asness, C. S., Frazzini, A. & Pedersen, L. H.
(2012). *Leverage Aversion and Risk Parity*. Financial Analysts
Journal 68(1), 47-59.
DOI: https://doi.org/10.2469/faj.v68.n1.1
"""

from __future__ import annotations

from alphakit.strategies.macro.risk_parity_erc_10asset.strategy import (
    RiskParityErc10Asset,
)

__all__ = ["RiskParityErc10Asset"]
