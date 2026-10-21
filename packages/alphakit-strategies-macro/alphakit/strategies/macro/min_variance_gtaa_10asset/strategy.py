"""Long-only minimum-variance portfolio on a 10-asset multi-sleeve universe.

Session 2L variant of ``min_variance_gtaa``. Same published rule, same
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
separate. See ``risk_parity_erc_10asset/strategy.py`` for the shared
pre-build measurement table covering all four tested configurations.

Two measured results shape this implementation. First, ``max_weight``
defaults to 1.0 rather than a binding cap: capping at 0.25 raised the
ERC-to-min-variance and min-variance-to-max-diversification correlations
from 0.728 and 0.680 to 0.939 and 0.939, because a binding constraint
rather than the objective then determines the weights. Second, the four
fixed-income sleeves are all retained, because the 7-asset variant with a
single duration leg still breached at rho +0.9642.

Implementation notes
====================

Foundational and primary paper
------------------------------
Haugen, R. A. & Baker, N. L. (1991).
*The Efficient Market Inefficiency of Capitalization-Weighted Stock
Portfolios*. Journal of Portfolio Management 17(3), 35-40.
https://doi.org/10.3905/jpm.1991.409335

Haugen and Baker document that minimum-variance portfolios have
historically delivered higher realised returns than
capitalization-weighted portfolios at lower risk, contradicting the
CAPM prediction that the market portfolio is mean-variance efficient.
That result is both the construction reference and the expected-return
rationale for this strategy, so a single citation covers both roles here
rather than the two-paper pattern the ERC sibling needs.

The minimum-variance problem is

    min  w' Sigma w   subject to   sum_i w_i = 1,  0 <= w_i <= max_weight

stated over an arbitrary covariance matrix with no cardinality
restriction, so it applies unchanged at N=10. The shared ``_covariance``
helper solves it with SciPy SLSQP under those constraints.

Differentiation from sibling strategies
---------------------------------------
* ``min_variance_gtaa`` is the same objective and solver on SPY/TLT/DBC.
  The only difference is universe cardinality and composition.
* ``risk_parity_erc_10asset`` equalises marginal risk contribution rather
  than minimising total variance. ERC always holds every asset; minimum
  variance drops assets at corner solutions.
* ``max_diversification_10asset`` maximises the diversification ratio
  rather than minimising variance. The two objectives coincide only when
  all assets share the same volatility.
* Phase 1 ``vol_targeting`` scales a single asset by its own volatility
  and uses no covariance matrix.

Universe
--------
Identical to ``risk_parity_erc_10asset``: SPY, TLT, DBC, IEF, SHY, LQD,
GLD, VNQ, EFA, EEM. Sharing one universe across the three variants is
deliberate, because the comparison under test is solver objective at
fixed universe. See that module's docstring for the substrate measurement
and the DBC-bound effective panel start of 2006-02-06.

Published rules (Haugen-Baker 1991, N-asset implementation)
-----------------------------------------------------------
For each month-end *t*:

1. Compute daily log returns over the trailing ``cov_window_days`` bars.
2. Estimate the covariance matrix via
   ``rolling_covariance(returns, window, shrinkage)``.
3. Solve minimum-variance weights via
   ``solve_min_variance_weights(cov, long_only=True,
   max_weight=max_weight)``.
4. Apply the weight vector at the month-end bar and forward-fill daily
   until the next rebalance.

Sign convention
---------------
Long-only and weights sum to 1.0. Weights are non-negative but **not**
strictly positive: the minimum-variance solution sits at a corner
whenever an asset is dominated, so individual weights of exactly zero are
expected and correct. Measured on this universe over 2006-2025, six of
ten assets carried a mean weight at or below 0.011. This is the main
behavioural difference from the ERC sibling, which holds every asset by
construction. Zero weights on every leg during warm-up.

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
* A ``max_weight`` below ``1 / len(universe)`` makes the budget
  constraint infeasible and is rejected at construction.
* Degenerate covariance makes the solver raise ``ValueError``; that
  rebalance is skipped and previous weights persist by forward fill.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import numpy as np
import pandas as pd
from alphakit.strategies.macro._covariance import (
    ShrinkageMethod,
    rolling_covariance,
    solve_min_variance_weights,
)
from alphakit.strategies.macro._gtaa10_universe import (
    GTAA10_UNIVERSE,
    MIN_COV_WINDOW_DAYS,
    MIN_UNIVERSE_SIZE,
    VALID_SHRINKAGE,
)


class MinVarianceGtaa10Asset:
    """Long-only minimum-variance portfolio on a 10-asset universe.

    Parameters
    ----------
    universe
        Ordered symbols to allocate across. Defaults to the shared
        ten-ticker, six-sleeve universe. Must hold at least three distinct
        non-empty symbols.
    cov_window_days
        Rolling window in trading days for the covariance estimator.
        Defaults to ``252``. Must be at least 60.
    shrinkage
        ``"none"``, ``"ledoit_wolf"`` (default), or ``"constant"``.
    max_weight
        Per-asset weight cap in ``(0, 1]``. Defaults to ``1.0``, meaning
        uncapped. A cap below ``1 / len(universe)`` is infeasible against
        the budget constraint and is rejected. The pre-build measurement
        recorded in ``risk_parity_erc_10asset/strategy.py`` found that a
        binding cap makes the three solver objectives converge rather than
        separate, which is why the default is uncapped.
    """

    name: str = "min_variance_gtaa_10asset"
    family: str = "macro"
    asset_classes: tuple[str, ...] = ("equity", "bonds", "credit", "commodities", "real_estate")
    paper_doi: str = "10.3905/jpm.1991.409335"  # Haugen & Baker 1991
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
        """Return minimum-variance target weights aligned to ``prices``.

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
                solved[month_end] = solve_min_variance_weights(
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
