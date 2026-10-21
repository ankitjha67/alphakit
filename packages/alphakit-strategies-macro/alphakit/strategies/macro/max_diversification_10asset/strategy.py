"""Maximum-diversification portfolio on a 10-asset multi-sleeve universe.

Session 2L variant of ``max_diversification``. Same published rule, same
shared ``_covariance`` solver, wider universe. The 3-asset original is
preserved unchanged as the documented small-N convergence case.

Provenance
==========
Session 2K-4's 29x29 real-feed cluster found the three
covariance-primitive strategies (``risk_parity_erc_3asset``,
``min_variance_gtaa``, ``max_diversification``) correlating at rho 0.980
to 0.993, breaching the dedup-review bar of rho > 0.95. The diagnosis in
``docs/sessions/2k-closeout.md`` section 5 was methodological convergence
on a 3-asset universe where all three objectives concentrate into the
lowest-variance asset, not a coding defect.

This variant widens the universe to test whether the three objectives
separate. The shared pre-build measurement table covering all four tested
configurations is in ``risk_parity_erc_10asset/strategy.py``.

Of the three variants this one is the measured near-breach. Its
correlation with ``risk_parity_erc_10asset`` fell only from +0.9931 at N=3
to +0.9482 at N=10, against +0.728 and +0.680 for the other two pairs. The
pair therefore sits 0.0020 below the dedup bar. That margin was
measured through the vectorbt bridge at 2bp commission, the configuration
the cluster uses, and reads +0.9480 against +0.9482 from a bridge-free
weight-lagged calculation, so bridge mechanics move it by roughly 0.0002
and do not explain the margin away. The margin is nonetheless thin enough
that a different window, commission assumption, or shrinkage setting could
cross the bar. See ``known_failures.md`` section 6.

Implementation notes
====================

Foundational paper
------------------
Choueifaty, Y. & Coignard, Y. (2008).
*Toward Maximum Diversification*. Journal of Portfolio Management 35(1),
40-51.
https://doi.org/10.3905/JPM.2008.35.1.40

Choueifaty and Coignard introduce the diversification ratio

    DR(w) = (w' sigma) / sqrt(w' Sigma w)

the ratio of the weighted-average asset volatility to the realised
portfolio volatility, and define the most-diversified portfolio as the
long-only weight vector maximising it. DR equals 1 for a single asset and
rises as correlations fall, so maximising it targets correlation structure
directly rather than variance level.

Primary methodology
-------------------
Choueifaty, Y., Froidure, T. & Reynier, J. (2011).
*Properties of the Most Diversified Portfolio*.
https://doi.org/10.2139/ssrn.1895459

The follow-up paper establishes the formal properties of the
most-diversified portfolio, including its invariance to duplicated assets
and to leverage, and supplies the empirical performance case. The DOI
resolves to the 2011 SSRN version, retrieved 2026-10-21; the same work
appears in the Journal of Investment Strategies in 2013, which is why the
3-asset incumbent's docstring cites a 2013 date. Both refer to the same
paper.

Why two papers
--------------
Choueifaty-Coignard (2008) defines the objective. Choueifaty-Froidure-
Reynier (2011) proves its properties and supplies the expected-return
case. Both are cited so the audit trail covers the definition and the
justification.

The maximisation is stated over an arbitrary covariance matrix with no
cardinality restriction, so it applies unchanged at N=10. The shared
``_covariance`` helper maximises DR with SciPy SLSQP under
``sum_i w_i = 1`` and ``0 <= w_i <= max_weight``.

Differentiation from sibling strategies
---------------------------------------
* ``max_diversification`` is the same objective and solver on
  SPY/TLT/DBC. The only difference is universe cardinality and
  composition.
* ``min_variance_gtaa_10asset`` minimises total portfolio variance. Max
  diversification instead maximises the volatility-to-portfolio-vol
  ratio, so it tolerates higher absolute variance when that buys lower
  correlation. The two objectives coincide only when every asset shares
  the same volatility.
* ``risk_parity_erc_10asset`` equalises marginal risk contribution. ERC
  holds every asset; max diversification drops assets at corner
  solutions.
* Phase 1 ``vol_targeting`` scales a single asset and uses no covariance
  matrix.

Universe
--------
Identical to the other two 10-asset variants, from the shared
``_gtaa10_universe`` module: SPY, TLT, DBC, IEF, SHY, LQD, GLD, VNQ, EFA,
EEM. Sharing one universe is deliberate, because the comparison under test
is solver objective at fixed universe. Effective panel start is
2006-02-06, bound by DBC inception, matching the 3-asset incumbents
exactly.

Published rules (Choueifaty-Coignard 2008, N-asset implementation)
------------------------------------------------------------------
For each month-end *t*:

1. Compute daily log returns over the trailing ``cov_window_days`` bars.
2. Estimate the covariance matrix via
   ``rolling_covariance(returns, window, shrinkage)``.
3. Solve maximum-diversification weights via
   ``solve_max_diversification_weights(cov, long_only=True,
   max_weight=max_weight)``.
4. Apply the weight vector at the month-end bar and forward-fill daily
   until the next rebalance.

Sign convention
---------------
Long-only and weights sum to 1.0. Weights are non-negative but not
strictly positive: the DR maximum sits at a corner whenever an asset is
dominated. Measured on this universe over 2006 to 2025, four of ten
assets carried a mean weight at or below 0.017. Zero weights on every leg
during warm-up.

Rebalance cadence
-----------------
Monthly target signal. The vectorbt bridge applies
``SizeType.TargetPercent`` semantics and adds daily drift-correction
trades. See the Session 2G amendment "alphakit-wide rebalance-cadence
convention" in ``docs/phase-2-amendments.md``.

Edge cases
----------
* Warm-up requires ``cov_window_days`` bars per asset; before that every
  weight is zero.
* Missing required columns raise ``KeyError`` naming the missing symbols.
* Non-positive prices raise ``ValueError``.
* A ``max_weight`` below ``1 / len(universe)`` is infeasible against the
  budget constraint and is rejected at construction.
* Degenerate covariance, or a zero-volatility asset making DR undefined,
  makes the solver raise ``ValueError``; that rebalance is skipped and
  previous weights persist by forward fill.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import numpy as np
import pandas as pd
from alphakit.strategies.macro._covariance import (
    ShrinkageMethod,
    rolling_covariance,
    solve_max_diversification_weights,
)
from alphakit.strategies.macro._gtaa10_universe import (
    GTAA10_UNIVERSE,
    MIN_COV_WINDOW_DAYS,
    MIN_UNIVERSE_SIZE,
    VALID_SHRINKAGE,
)


class MaxDiversification10Asset:
    """Maximum-diversification portfolio on a 10-asset universe.

    Parameters
    ----------
    universe
        Ordered symbols to allocate across. Defaults to the shared
        ten-ticker, six-sleeve ``GTAA10_UNIVERSE``. Must hold at least
        three distinct non-empty symbols.
    cov_window_days
        Rolling window in trading days for the covariance estimator.
        Defaults to ``252``. Must be at least 60.
    shrinkage
        ``"none"``, ``"ledoit_wolf"`` (default), or ``"constant"``.
    max_weight
        Per-asset weight cap in ``(0, 1]``. Defaults to ``1.0``, meaning
        uncapped. A cap below ``1 / len(universe)`` is infeasible against
        the budget constraint and is rejected. The pre-build measurement
        in ``risk_parity_erc_10asset/strategy.py`` found a binding cap
        makes the three solver objectives converge rather than separate,
        which is why the default is uncapped.
    """

    name: str = "max_diversification_10asset"
    family: str = "macro"
    asset_classes: tuple[str, ...] = ("equity", "bonds", "credit", "commodities", "real_estate")
    paper_doi: str = "10.2139/ssrn.1895459"  # Choueifaty-Froidure-Reynier 2011
    rebalance_frequency: str = "monthly"

    def __init__(
        self,
        *,
        universe: Sequence[str] | None = None,
        cov_window_days: int = 252,
        shrinkage: ShrinkageMethod = "ledoit_wolf",
        max_weight: float = 1.0,
    ) -> None:
        resolved = tuple(GTAA10_UNIVERSE if universe is None else universe)

        for sym in resolved:
            if not isinstance(sym, str) or not sym:
                raise ValueError(f"universe entries must be non-empty strings, got {sym!r}")
        if len(resolved) < MIN_UNIVERSE_SIZE:
            raise ValueError(
                f"universe must hold at least {MIN_UNIVERSE_SIZE} symbols, got {len(resolved)}"
            )
        if len(set(resolved)) != len(resolved):
            duplicates = sorted({s for s in resolved if resolved.count(s) > 1})
            raise ValueError(f"universe symbols must be distinct; duplicates: {duplicates}")
        if cov_window_days < MIN_COV_WINDOW_DAYS:
            raise ValueError(
                f"cov_window_days must be >= {MIN_COV_WINDOW_DAYS}, got {cov_window_days}"
            )
        if shrinkage not in VALID_SHRINKAGE:
            raise ValueError(f"shrinkage must be one of {VALID_SHRINKAGE}, got {shrinkage!r}")
        if max_weight <= 0 or max_weight > 1.0:
            raise ValueError(f"max_weight must be in (0, 1], got {max_weight}")
        if max_weight < 1.0 / len(resolved):
            raise ValueError(
                f"max_weight {max_weight} is infeasible for {len(resolved)} assets: the "
                f"budget constraint needs max_weight >= 1/N = {1.0 / len(resolved):.6f}"
            )

        self.universe = resolved
        self.cov_window_days = cov_window_days
        self.shrinkage = shrinkage
        self.max_weight = max_weight

    @property
    def required_symbols(self) -> tuple[str, ...]:
        """The input columns this strategy requires, in allocation order."""
        return self.universe

    def generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Return maximum-diversification target weights aligned to ``prices``.

        Parameters
        ----------
        prices
            DataFrame indexed by daily timestamps containing every symbol in
            ``universe``. Extra columns are ignored. Values must be strictly
            positive.

        Returns
        -------
        weights
            DataFrame aligned to ``prices`` with one column per universe
            symbol. After warm-up each row is non-negative and sums to 1.0;
            individual weights of zero are expected at corner solutions.
            During warm-up every weight is zero.
        """
        if not isinstance(prices, pd.DataFrame):
            raise TypeError(f"prices must be a DataFrame, got {type(prices).__name__}")

        missing = [s for s in self.universe if s not in prices.columns]
        if missing:
            raise KeyError(
                f"prices is missing required columns for {self.name}: {missing}. "
                f"Required: {list(self.universe)}; got: {list(prices.columns)}"
            )

        leg_prices = prices.loc[:, list(self.universe)]

        if leg_prices.empty:
            return pd.DataFrame(
                index=prices.index,
                columns=list(self.universe),
                dtype=float,
            )

        if not isinstance(leg_prices.index, pd.DatetimeIndex):
            raise TypeError(
                f"prices must have a DatetimeIndex, got {type(leg_prices.index).__name__}"
            )
        if (leg_prices <= 0).any().any():
            raise ValueError(f"prices must be strictly positive for all {len(self.universe)} legs")

        zeros = pd.DataFrame(
            np.zeros(leg_prices.shape, dtype=float),
            index=leg_prices.index,
            columns=list(self.universe),
        )

        daily_log_returns = np.log(leg_prices / leg_prices.shift(1))
        rolling_cov = rolling_covariance(
            daily_log_returns.dropna(),
            window=self.cov_window_days,
            shrinkage=self.shrinkage,
        )
        if rolling_cov.empty:
            return zeros

        cov_dates = pd.DatetimeIndex(rolling_cov.index.unique(level="date"))
        month_end_index = leg_prices.resample("ME").last().index

        solved: dict[pd.Timestamp, np.ndarray] = {}
        for month_end in month_end_index:
            mask = cov_dates <= month_end
            if not mask.any():
                continue
            cov_matrix = rolling_cov.loc[cov_dates[mask].max()].to_numpy(dtype=float)
            try:
                solved[month_end] = solve_max_diversification_weights(
                    cov_matrix, long_only=True, max_weight=self.max_weight
                )
            except ValueError:
                continue

        if not solved:
            return zeros

        monthly_weights = pd.DataFrame(
            np.vstack(list(solved.values())),
            index=pd.DatetimeIndex(list(solved.keys())),
            columns=list(self.universe),
        )
        daily_weights = monthly_weights.reindex(leg_prices.index).ffill().fillna(0.0)
        return cast(pd.DataFrame, daily_weights)
