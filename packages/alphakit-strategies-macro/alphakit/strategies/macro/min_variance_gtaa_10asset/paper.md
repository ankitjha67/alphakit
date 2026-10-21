# Paper — min_variance_gtaa_10asset

Objective: minimum total portfolio variance. Session 2L variant of `min_variance_gtaa` on a wider
universe; same published rule, same shared solver.

## Citations

### Foundational and primary methodology

Haugen, R. A. & Baker, N. L. (1991). *The Efficient Market Inefficiency of Capitalization-Weighted Stock Portfolios*. Journal of Portfolio Management 17(3), 35-40.

DOI: https://doi.org/10.3905/jpm.1991.409335

Verified 2026-10-21 by DOI content negotiation at doi.org.

## Why one paper

One citation covers both roles here, which is a deliberate departure from
the project's usual two-paper pattern.

Haugen and Baker (1991) document that minimum-variance portfolios
historically delivered higher realised returns than capitalization-weighted
portfolios at lower risk, contradicting the CAPM prediction that the market
portfolio is mean-variance efficient. That single result is simultaneously
the construction reference and the expected-return rationale, so a second
paper would add citation volume without adding evidentiary coverage.

The ERC sibling needs two papers because its construction (MRT 2010) and its
rationale (AFP 2012) come from different authors. This one does not.

## Published rules (N-asset implementation)

For each month-end:

1. Compute daily log returns over the trailing `cov_window_days` bars.
2. Estimate the covariance matrix via `rolling_covariance(returns, window,
   shrinkage)`.
3. Solve `min w' Sigma w` subject to `sum_i w_i = 1` and
   `0 <= w_i <= max_weight` via
   `_covariance.solve_min_variance_weights(cov, long_only=True,
   max_weight=max_weight)`, using SciPy SLSQP.
4. Apply the weight vector at the month-end bar; forward-fill daily.

The objective is stated over an arbitrary covariance matrix and carries no
cardinality restriction, so it applies unchanged at N=10. That was verified
empirically rather than assumed: `solve_min_variance_weights` was driven on real 10x10
covariance matrices before this strategy was written, returning finite
long-only weights summing to 1.0 in under 11ms.

## Differentiation from sibling strategies

* `min_variance_gtaa` is the same objective and solver on SPY/TLT/DBC. The only
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

DBC incepts 2006-02-06 and binds the complete-rows intersection. Effective
panel: 5008 rows from 2006-02-06.

Known fidelity gaps: ETFs carry expense ratios and tracking error absent
from index-level analysis; the 2bp commission assumption is flat and models
neither spread nor market impact; and the measured window contains one
crisis (2008) only 20 months after the usable start.

## Measured performance

Through `vectorbt_bridge.run` at 2bp commission, 5007 bars, 2006-02-06 to
2025-12-30:

| metric | this variant | `min_variance_gtaa` |
|---|---|---|
| Sharpe | +0.9212 | +0.5975 |
| max drawdown | -0.0746 | -0.2155 |
| final equity from 100,000 | 152,088 | 263,790 |

The authoritative figure is `benchmark_results.json`, produced by
`BenchmarkRunner`. The table above is the pre-benchmark smoke measurement
and is recorded for provenance.

## Implementation deviations

Haugen and Baker analyse a single-country equity cross-section. This
implementation applies the same objective to a ten-sleeve multi-asset
universe, which is a scope extension rather than a replication. The
objective itself is universe-agnostic, but the paper's reported return
premium was measured on equities and should not be read as a prediction for
this universe.

Long-only is imposed. Haugen and Baker's unconstrained minimum-variance
portfolio permits short positions; the long-only constraint changes the
solution and is the reason corner solutions appear.

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
