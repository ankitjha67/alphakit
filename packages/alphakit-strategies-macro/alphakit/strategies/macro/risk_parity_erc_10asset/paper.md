# Paper — risk_parity_erc_10asset

Objective: equal marginal risk contribution. Session 2L variant of `risk_parity_erc_3asset` on a wider
universe; same published rule, same shared solver.

## Citations

### Foundational

Maillard, S., Roncalli, T. & Teiletche, J. (2010). *The Properties of Equally Weighted Risk Contribution Portfolios*. Journal of Portfolio Management 36(4), 60-70.

DOI: https://doi.org/10.3905/jpm.2010.36.4.060

Verified 2026-10-21 by DOI content negotiation at doi.org.

### Primary methodology

Asness, C. S., Frazzini, A. & Pedersen, L. H. (2012). *Leverage Aversion and Risk Parity*. Financial Analysts Journal 68(1), 47-59.

DOI: https://doi.org/10.2469/faj.v68.n1.1

Verified 2026-10-21 by DOI content negotiation at doi.org.

## Why two papers

MRT (2010) specifies the construction, defining the ERC portfolio as the
weight vector equalising each asset's marginal risk contribution, and gives a
fixed-point iteration for it. It offers no risk-premium rationale.

AFP (2012) supplies the rationale. Leverage-averse investors over-weight
high-volatility assets to reach a target portfolio volatility, suppressing
those assets' expected returns and leaving a premium for low-volatility
tilts. AFP does not specify the ERC solver.

Both are cited so the audit trail covers the mathematics and the economics.

## Published rules (N-asset implementation)

For each month-end:

1. Compute daily log returns over the trailing `cov_window_days` bars.
2. Estimate the covariance matrix via `rolling_covariance(returns, window,
   shrinkage)`, defaulting to Ledoit-Wolf 2004 analytic-optimal shrinkage
   toward a constant-correlation target.
3. Solve ERC weights via `_covariance.solve_erc_weights(cov)`. The helper
   uses Spinu's (2013) convex reformulation
   `min 0.5 * w' Sigma w - (1/N) * sum_i log(w_i)`, convex in `w` and
   globally convergent under L-BFGS-B.
4. Apply the weight vector at the month-end bar; forward-fill daily.

The objective is stated over an arbitrary covariance matrix and carries no
cardinality restriction, so it applies unchanged at N=10. That was verified
empirically rather than assumed: `solve_erc_weights` was driven on real 10x10
covariance matrices before this strategy was written, returning finite
long-only weights summing to 1.0 in under 11ms.

## Differentiation from sibling strategies

* `risk_parity_erc_3asset` is the same objective and solver on SPY/TLT/DBC. The only
  difference is universe cardinality and composition. These two are
  deliberately close; measured correlation is in `known_failures.md`
  section 6.
* The other two 10-asset variants share this universe and this covariance
  estimator and differ only in solver objective. Separating those three
  objectives is the entire purpose of the variant group.
* Phase 1 `vol_targeting` scales a single asset by its own volatility and
  uses no covariance matrix.
* `permanent_portfolio` is a static four-asset allocation. It remains the
  project's correlation magnet, measured at +0.6059 to +0.8514 against this
  group, because its universe includes SHY, the asset these objectives
  concentrate into.

## Architectural note: shared covariance helper and shared universe

Two package-private modules are shared across the variant group.

`_covariance.py` provides the rolling covariance estimator and all three
solvers, established by the Session 2G amendment "covariance-primitive
shared helper module". Keeping one estimator behind three objectives is what
makes the group's pairwise correlations attributable to objective rather
than to estimator differences.

`_gtaa10_universe.py` provides the ten-ticker universe and the shared
validation bounds, added in Session 2L for the same reason at the universe
level. The comparison under test is solver objective at fixed universe. If
the three variants drifted to different ticker lists, any change in their
pairwise correlation would be confounded between "the objectives separate at
higher N" and "the universes differ". Centralising the tuple makes that
drift impossible by construction.

## Data fidelity

Universe is ten liquid US-listed ETFs. Prices are `auto_adjust=True`
closes from yfinance, so they are total-return adjusted for dividends and
splits.

Substrate measured 2026-10-21 via `scripts/audit_etf_universe.py`: every
ticker returns data, zero non-positive bars, maximum consecutive missing run
of 2 business days, and 195 missing business days out of 5478 across 2005 to
2025. That is 9.75 per year and consistent with the US market holiday
calendar, so the S2J-2.6 anomaly filter is not required for this universe.

DBC incepts 2006-02-06 and binds the complete-rows intersection, so a
`dropna(how="any")` panel holds 5008 rows from 2006-02-06. The runner does
not trim that way: for an ETF-only strategy it takes a single-feed shortcut
with no complete-rows trim, so the committed benchmark panel is 5282 bars
from 2005-01-03 with 275 NaN-bearing rows. No covariance is estimated from
incomplete data, because `rolling_covariance` is fed
`daily_log_returns.dropna()`. The 3-asset incumbents get the identical
treatment, so the cardinality comparison stays controlled. See
`known_failures.md` section 4.

Known fidelity gaps: ETFs carry expense ratios and tracking error absent
from index-level analysis; the 2bp commission assumption is flat and models
neither spread nor market impact; and the measured window contains one
crisis (2008) only 20 months after the usable start.

## Measured performance

From the committed `benchmark_results.json`, produced by
`regenerate_benchmarks.py tier1` (`BenchmarkRunner(commission_bps=5.0,
data_start="2005-01-01")`) on real yfinance prices, a 5282-bar panel from
2005-01-03. Sharpe, Sortino, Calmar and max drawdown are out-of-sample
(2020-01-01 to 2025-12-31, the runner's OOS window); return and volatility
are annualized. An earlier draft quoted full-period Sharpes computed by hand;
these are the committed OOS figures.


| metric (OOS 2020-2025, 5bp) | this variant | `risk_parity_erc_3asset` |
|---|---|---|
| Sharpe | +0.5268 | +0.5224 |
| Sortino | +0.4921 | +0.4851 |
| Calmar | +0.2098 | +0.2694 |
| max drawdown | -0.1302 | -0.1953 |
| annualized return | +0.0284 | +0.0573 |
| annualized vol | 0.0539 | 0.1096 |

The authoritative figure is `benchmark_results.json`, produced by
`BenchmarkRunner`. The table above is the pre-benchmark smoke measurement
and is recorded for provenance.

## Implementation deviations

The solver is Spinu's (2013) convex reformulation rather than MRT's
fixed-point iteration. The two have the same optimum; the convex form
converges globally where the fixed-point iteration can stall. This deviation
is inherited from the 3-asset incumbent and the shared `_covariance` helper,
not introduced here.

MRT and AFP both work with asset-class panels rather than ETF proxies. This
implementation uses liquid ETFs as the investable expression of each sleeve,
which introduces tracking error, expense ratios, and ETF-specific liquidity
effects absent from the papers' index-level analysis.

## Limitations

The papers cited establish the objective and its rationale. They do not
establish that this objective applied to this ten-ETF universe over
2006-2025 produces the measured result, and nothing here should be read as
the papers predicting these numbers.

The DOI verification performed this session confirms that each DOI resolves
to the paper claimed, with matching title, authors, year and journal. It does
not constitute reading the papers' full text in this session. Claims above
about what each paper contains are carried forward from the 3-asset
incumbents' documentation, written in Session 2G, and are tagged here as
inherited rather than re-verified.
