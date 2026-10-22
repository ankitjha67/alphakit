"""Equal-Risk-Contribution portfolio on a 10-asset multi-sleeve universe.

Session 2L variant of ``risk_parity_erc_3asset``. Same published rule, same
shared ``_covariance`` solver, wider universe. The 3-asset original is
preserved unchanged as the documented small-N convergence case.

Provenance
==========
Session 2K-4's 29x29 real-feed cluster found that the three
covariance-primitive strategies (``risk_parity_erc_3asset``,
``min_variance_gtaa``, ``max_diversification``) correlate at rho 0.980 to
0.993, breaching the Phase 2 master-plan dedup-review bar of rho > 0.95.
The diagnosis recorded in ``docs/sessions/2k-closeout.md`` section 5 was
scenario (b), methodological convergence rather than a coding defect: all
three share one covariance estimator on one 3-asset universe, differ only
in solver objective, and on a universe where TLT carries the lowest
variance all three concentrate into TLT.

Session 2L tests whether a wider, more heterogeneous universe separates
the three objectives. The originals are kept so the convergence case stays
documented and reproducible; these variants are additions, not
replacements.

Pre-build measurement (2026-10-21, this universe, real yfinance prices
2006-02-06 to 2025-12-30 on a ``dropna(how="any")`` panel of 5007 bars,
monthly rebalance, 252-day Ledoit-Wolf covariance, weight-lagged daily
returns). The uncapped N=10 row below was measured three ways and lands in
a 0.0002 range each time: +0.9482 weight-lagged on the trimmed panel,
+0.9480 through the bridge at 2bp on the trimmed panel, and +0.9482 through
the cluster's own untrimmed 5282-bar path. The ranking is therefore robust
to panel and commission choice, unlike the Sharpe figures. See
``known_failures.md`` sections 4 and 6:

    configuration                 max pairwise rho across the three solvers
    N=3 incumbent SPY/TLT/DBC                       +0.9931   breached
    N=10 this universe, uncapped                    +0.9482   below bar
    N=10 this universe, max_weight=0.25             +0.9435   below bar
    N=7 single duration sleeve, uncapped            +0.9642   breached

Two findings from that table shape this implementation.

First, no weight cap is applied. Capping at 0.25 lowers the maximum
pairwise rho slightly but raises the other two pairs from 0.728 and 0.680
to 0.939 and 0.939, because a binding cap makes the constraint rather than
the objective determine the weights. Uncapped weights differentiate the
three objectives better, so ERC here keeps the incumbent's uncapped
behaviour.

Second, trimming the fixed-income sleeves makes separation worse, not
better. The 7-asset variant with one duration leg still breaches at
+0.9642. The duration cluster is part of what separates the objectives, so
all four fixed-income sleeves are retained.

Implementation notes
====================

Foundational paper
------------------
Maillard, S., Roncalli, T. & Teiletche, J. (2010).
*The Properties of Equally Weighted Risk Contribution Portfolios*.
Journal of Portfolio Management 36(4), 60-70.
https://doi.org/10.3905/jpm.2010.36.4.060

MRT (2010) defines the equal-risk-contribution portfolio: each asset's
marginal risk contribution ``RC_i = w_i * (Sigma w)_i / sqrt(w' Sigma w)``
is equal across all *i* at the optimum. The definition is stated over an
arbitrary covariance matrix and carries no cardinality restriction, so it
applies unchanged at N=10. The shared ``_covariance`` helper solves it via
Spinu's (2013) convex reformulation
``min  0.5 * w' Sigma w - (1/N) * sum_i log(w_i)``, which is convex in *w*
and converges globally under L-BFGS-B.

Primary methodology
-------------------
Asness, C. S., Frazzini, A. & Pedersen, L. H. (2012).
*Leverage Aversion and Risk Parity*. Financial Analysts Journal 68(1),
47-59.
https://doi.org/10.2469/faj.v68.n1.1

AFP (2012) supplies the risk-premium rationale. Leverage-averse investors
over-weight high-volatility assets to reach a target portfolio volatility,
suppressing those assets' expected returns and leaving a premium for
low-volatility tilts. ERC captures that premium by under-weighting
high-volatility assets relative to equal weight.

Why two papers
--------------
MRT (2010) specifies the construction without a risk-premium rationale.
AFP (2012) supplies the rationale without specifying the solver. Both are
cited so the audit trail covers the mathematics and the economics.

Differentiation from sibling strategies
---------------------------------------
* ``risk_parity_erc_3asset`` is the same objective and the same solver on
  SPY/TLT/DBC. The only difference is universe cardinality and
  composition. These two are deliberately close and the pair is expected
  to remain correlated. See ``known_failures.md`` section 6 for the
  measured and predicted bands.
* ``min_variance_gtaa_10asset`` and ``max_diversification_10asset`` share
  this universe and this covariance estimator, differing in solver
  objective. Separating those three objectives is the entire purpose of
  this variant group.
* Phase 1 ``vol_targeting`` applies inverse-volatility scaling per asset
  rather than as a joint portfolio construction, and uses no covariance
  matrix.
* ``permanent_portfolio`` is a static four-asset allocation. Session 2K-4
  found it correlates above 0.75 with each member of the 3-asset
  covariance trio and above 0.70 with the regime strategies, making it the
  project's most-correlated strategy.

Universe (10 assets, six sleeves)
---------------------------------
* ``SPY``  US large-cap equity
* ``EFA``  developed ex-US equity
* ``EEM``  emerging-market equity
* ``TLT``  20+ year Treasuries
* ``IEF``  7-10 year Treasuries
* ``SHY``  1-3 year Treasuries
* ``LQD``  investment-grade corporate credit
* ``DBC``  broad commodities
* ``GLD``  gold
* ``VNQ``  US real estate

Substrate measurement (2026-10-21, yfinance, probe window 1990-2026):
every ticker returns data, zero non-positive bars, maximum consecutive
missing run of 2 business days, and 195 missing business days out of 5478
across 2005-2025, which is 9.75 per year and consistent with the US market
holiday calendar. The S2J-2.6 anomaly filter is therefore not required for
this universe, matching the existing ETF real-feed configuration.

DBC incepts 2006-02-06 and binds the complete-rows intersection, so a
``dropna(how="any")`` panel holds 5008 rows from 2006-02-06. The runner does
not trim that way for ETF-only strategies: ``_fetch_prices`` takes a
single-feed shortcut with no complete-rows trim, so the committed benchmark
panel is 5282 bars from 2005-01-03 with 275 NaN-bearing rows. That is safe
because ``rolling_covariance`` receives ``daily_log_returns.dropna()``, so no
covariance is estimated from incomplete data. The 3-asset incumbent gets
identical treatment, so the cardinality comparison is a controlled test
either way. See ``known_failures.md`` section 4.

Published rules (MRT 2010 / AFP 2012, N-asset implementation)
-------------------------------------------------------------
For each month-end *t*:

1. Compute daily log returns over the trailing ``cov_window_days`` bars.
2. Estimate the covariance matrix via
   ``rolling_covariance(returns, window, shrinkage)``, defaulting to
   Ledoit-Wolf 2004 analytic-optimal shrinkage toward a
   constant-correlation target.
3. Solve ERC weights via ``solve_erc_weights(cov)``, giving long-only
   weights summing to 1.0 with equal marginal risk contribution.
4. Apply the weight vector at the month-end bar and forward-fill daily
   until the next rebalance.

Sign convention
---------------
Long-only, weights sum to 1.0, every weight strictly positive. The Spinu
log-barrier formulation guarantees positivity. Zero weights on every leg
during warm-up, before ``cov_window_days`` of history exist.

Rebalance cadence
-----------------
Monthly target signal. The vectorbt bridge applies
``SizeType.TargetPercent`` semantics and produces daily drift-correction
trades on top of the monthly signal. See the Session 2G amendment
"alphakit-wide rebalance-cadence convention" in
``docs/phase-2-amendments.md``. The ``rebalance_frequency`` attribute
documents the signal cadence, not the bridge-event cadence.

Edge cases
----------
* Warm-up requires ``cov_window_days`` bars per asset. Before that every
  weight is zero and the bridge holds cash.
* Missing required columns raise ``KeyError`` naming the missing symbols.
* Non-positive prices raise ``ValueError``.
* Degenerate covariance, for example a constant-price leg, makes
  ``solve_erc_weights`` raise ``ValueError``. That rebalance is skipped and
  the previous weights persist by forward fill.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import numpy as np
import pandas as pd
from alphakit.strategies.macro._covariance import (
    ShrinkageMethod,
    rolling_covariance,
    solve_erc_weights,
)
from alphakit.strategies.macro._gtaa10_universe import (
    GTAA10_UNIVERSE,
    MIN_COV_WINDOW_DAYS,
    MIN_UNIVERSE_SIZE,
    VALID_SHRINKAGE,
)


class RiskParityErc10Asset:
    """Equal-Risk-Contribution portfolio on a 10-asset multi-sleeve universe.

    Parameters
    ----------
    universe
        Ordered symbols to allocate across. Defaults to the shared
        ten-ticker, six-sleeve ``GTAA10_UNIVERSE``. Must hold at least
        three distinct non-empty symbols.
    cov_window_days
        Rolling window in trading days for the covariance estimator.
        Defaults to ``252``, one trading year. Must be at least 60.
    shrinkage
        Covariance shrinkage method: ``"none"`` for the raw sample,
        ``"ledoit_wolf"`` for analytic-optimal intensity toward a
        constant-correlation target (default), or ``"constant"`` for fixed
        alpha of 0.5 toward the same target.
    """

    name: str = "risk_parity_erc_10asset"
    family: str = "macro"
    asset_classes: tuple[str, ...] = ("equity", "bonds", "credit", "commodities", "real_estate")
    paper_doi: str = "10.2469/faj.v68.n1.1"  # AFP 2012
    rebalance_frequency: str = "monthly"

    def __init__(
        self,
        *,
        universe: Sequence[str] | None = None,
        cov_window_days: int = 252,
        shrinkage: ShrinkageMethod = "ledoit_wolf",
    ) -> None:
        resolved = tuple(GTAA10_UNIVERSE if universe is None else universe)

        for sym in resolved:
            if not isinstance(sym, str) or not sym:
                raise ValueError(f"universe entries must be non-empty strings, got {sym!r}")
        if len(resolved) < MIN_UNIVERSE_SIZE:
            raise ValueError(
                f"universe must hold at least {MIN_UNIVERSE_SIZE} symbols "
                f"(below that an ERC construction degenerates), got {len(resolved)}"
            )
        if len(set(resolved)) != len(resolved):
            duplicates = sorted({s for s in resolved if resolved.count(s) > 1})
            raise ValueError(f"universe symbols must be distinct; duplicates: {duplicates}")
        if cov_window_days < MIN_COV_WINDOW_DAYS:
            raise ValueError(
                f"cov_window_days must be >= {MIN_COV_WINDOW_DAYS} "
                f"(minimum sample for stable covariance), got {cov_window_days}"
            )
        if shrinkage not in VALID_SHRINKAGE:
            raise ValueError(f"shrinkage must be one of {VALID_SHRINKAGE}, got {shrinkage!r}")

        self.universe = resolved
        self.cov_window_days = cov_window_days
        self.shrinkage = shrinkage

    @property
    def required_symbols(self) -> tuple[str, ...]:
        """The input columns this strategy requires, in allocation order."""
        return self.universe

    def generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Return ERC target weights aligned to ``prices``.

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
            symbol. Weights are solved monthly on the rolling covariance and
            forward-filled daily. After warm-up every weight is strictly
            positive and the row sums to 1.0; during warm-up every weight is
            zero.
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

        # 1. Daily log returns feed the covariance estimator.
        daily_log_returns = np.log(leg_prices / leg_prices.shift(1))

        # 2. Rolling covariance from the shared helper, returned as a
        # MultiIndex(date, asset_i) frame whose .loc[date] slice is the
        # (N, N) covariance at that date.
        rolling_cov = rolling_covariance(
            daily_log_returns.dropna(),
            window=self.cov_window_days,
            shrinkage=self.shrinkage,
        )
        if rolling_cov.empty:
            return zeros

        # 3. Solve ERC weights at each month-end, using the most recent
        # covariance at or before that date.
        cov_dates = pd.DatetimeIndex(rolling_cov.index.unique(level="date"))
        month_end_index = leg_prices.resample("ME").last().index

        solved: dict[pd.Timestamp, np.ndarray] = {}
        for month_end in month_end_index:
            mask = cov_dates <= month_end
            if not mask.any():
                continue
            cov_matrix = rolling_cov.loc[cov_dates[mask].max()].to_numpy(dtype=float)
            try:
                solved[month_end] = solve_erc_weights(cov_matrix)
            except ValueError:
                # Degenerate covariance at this date, for example a leg with
                # zero sample variance. Skip this rebalance; the previous
                # weights persist through the forward fill below.
                continue

        if not solved:
            return zeros

        # 4. Monthly weights forward-filled to the daily index.
        monthly_weights = pd.DataFrame(
            np.vstack(list(solved.values())),
            index=pd.DatetimeIndex(list(solved.keys())),
            columns=list(self.universe),
        )
        daily_weights = monthly_weights.reindex(leg_prices.index).ffill().fillna(0.0)
        return cast(pd.DataFrame, daily_weights)
