# Paper — max_diversification_10asset

Objective: maximum diversification ratio. Session 2L variant of `max_diversification` on a wider
universe; same published rule, same shared solver.

## Citations

### Foundational

Choueifaty, Y. & Coignard, Y. (2008). *Toward Maximum Diversification*. Journal of Portfolio Management 35(1), 40-51.

DOI: https://doi.org/10.3905/JPM.2008.35.1.40

Verified 2026-10-21 by DOI content negotiation at doi.org.

### Primary methodology

Choueifaty, Y., Froidure, T. & Reynier, J. (2011). *Properties of the Most Diversified Portfolio*.

DOI: https://doi.org/10.2139/ssrn.1895459

Verified 2026-10-21 by DOI content negotiation at doi.org.

## Why two papers

Choueifaty and Coignard (2008) define the diversification ratio
`DR(w) = (w' sigma) / sqrt(w' Sigma w)` and the most-diversified portfolio as
the long-only weight vector maximising it. The paper establishes the
objective but not its formal properties.

Choueifaty, Froidure and Reynier (2011) prove those properties, including
invariance to duplicated assets and to leverage, and supply the empirical
case.

Both are cited so the audit trail covers the definition and the
justification.

Citation-year note: the 2011 DOI resolves to the SSRN version, verified
2026-10-21 by DOI content negotiation. The same work appears in the Journal
of Investment Strategies in 2013, which is why the 3-asset incumbent's
docstring carries a 2013 date. Both refer to one paper; neither date is
wrong.

## Published rules (N-asset implementation)

For each month-end:

1. Compute daily log returns over the trailing `cov_window_days` bars.
2. Estimate the covariance matrix via `rolling_covariance(returns, window,
   shrinkage)`.
3. Maximise `DR(w) = (w' sigma) / sqrt(w' Sigma w)` subject to
   `sum_i w_i = 1` and `0 <= w_i <= max_weight` via
   `_covariance.solve_max_diversification_weights(cov, long_only=True,
   max_weight=max_weight)`, using SciPy SLSQP.
4. Apply the weight vector at the month-end bar; forward-fill daily.

The objective is stated over an arbitrary covariance matrix and carries no
cardinality restriction, so it applies unchanged at N=10. That was verified
empirically rather than assumed: `solve_max_diversification_weights` was driven on real 10x10
covariance matrices before this strategy was written, returning finite
long-only weights summing to 1.0 in under 11ms.

## Differentiation from sibling strategies

* `max_diversification` is the same objective and solver on SPY/TLT/DBC. The only
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


| metric (OOS 2020-2025, 5bp) | this variant | `max_diversification` |
|---|---|---|
| Sharpe | +0.4075 | +0.4620 |
| Sortino | +0.3849 | +0.4346 |
| Calmar | +0.1377 | +0.2283 |
| max drawdown | -0.1344 | -0.1993 |
| annualized return | +0.0195 | +0.0505 |
| annualized vol | 0.0478 | 0.1092 |

The authoritative figure is `benchmark_results.json`, produced by
`BenchmarkRunner`. The table above is the pre-benchmark smoke measurement
and is recorded for provenance.

## Implementation deviations

Choueifaty and Coignard analyse equity universes. This implementation
applies the objective to a ten-sleeve multi-asset universe, a scope
extension rather than a replication.

The papers' invariance-to-duplication property is a selling point for large
universes with redundant names. At N=10 with six distinct sleeves there is
little redundancy to be invariant to, so that property does less work here
than in the papers' setting.

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
