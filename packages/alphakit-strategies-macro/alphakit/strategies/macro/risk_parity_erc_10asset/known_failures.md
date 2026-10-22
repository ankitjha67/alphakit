# Known failure modes — risk_parity_erc_10asset

> The Session 2L variant group trades absolute return for risk-adjusted
> return. Every failure mode below follows from that one structural fact or
> from the covariance estimator the group shares.

Session 2L variant of `risk_parity_erc_3asset`, added in response to the Session 2K-4
dedup-bar breach. The 3-asset original is preserved unchanged. Objective:
equal marginal risk contribution.

## 1. Lower absolute return than the 3-asset incumbent, by construction

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

OOS Sharpe is essentially flat against the incumbent (+0.527 vs +0.522);
the variant's effect is on risk, not risk-adjusted return.

The common mechanism across all three variants: the wider universe contains
SHY, a 1-3 year Treasury ETF with the
lowest variance in the set, and every covariance-minimising objective
concentrates into it. Measured mean SHY weight was 0.539 for ERC, 0.709 for
minimum variance, and 0.614 for maximum diversification.

A portfolio that is 54 to 71 percent short-duration Treasuries has low
volatility and low return. Annualized volatility roughly halves against the
incumbent and so does max drawdown; annualized return falls by a similar
proportion. The risk-adjusted outcome therefore depends on the solver: a
clear gain for minimum variance, a wash for ERC, a small loss for maximum
diversification.

Users wanting the incumbent's return profile should use the 3-asset
original, which is preserved for exactly that reason. These variants exist
to separate the three solver objectives, not to beat the incumbents on
return.

## 2. Single-asset concentration persists despite the wider universe

Widening the universe from 3 to 10 did not stop the concentration; it moved
it. At N=3 all three objectives concentrated into TLT. At N=10 all three
concentrate into SHY, the new lowest-variance asset, and more heavily.

What the wider universe changed is that the three objectives now concentrate
by *different amounts* and distribute the residual differently, which is
enough to decorrelate their return series (see section 6). The
concentration itself is unchanged in kind.

A weight cap would address concentration directly. It is deliberately not
applied: measured at `max_weight=0.25`, capping raised the
`erc` to `minvar` and `minvar` to `maxdiv` correlations from +0.7262 and
+0.6791 to +0.9385 and +0.9391, because a binding constraint rather than the
objective then determines the weights. Capping fixes concentration and
breaks the separation that is this group's purpose. Anyone wanting a capped
variant should treat it as a different strategy with its own cluster
analysis.

## 3. Corner solutions and zero weights

ERC never produces a zero weight. The Spinu log-barrier term
`-(1/N) sum_i log(w_i)` diverges as any weight approaches zero, so every
asset is always held. Measured minimum weight across the window was
+0.0107. This is the main behavioural difference from the minimum-variance
and maximum-diversification siblings, both of which drop dominated assets
at corner solutions.

## 4. The benchmark panel is NOT complete-rows trimmed

Two different dates matter here and conflating them produces wrong numbers.
An earlier draft of this document did exactly that and is corrected below.

DBC incepts 2006-02-06 and binds the complete-rows intersection, so a panel
built with `dropna(how="any")` holds 5008 rows from 2006-02-06. Inception
dates measured 2026-10-21 via `scripts/audit_etf_universe.py`.

The runner does not build the panel that way. For an ETF-only strategy with
no informational columns and one tradable feed, `_fetch_prices` takes a
single-feed shortcut that returns the panel straight after the anomaly
filter, deliberately byte-identical to the pre-S2J path, with no
complete-rows trim. With the anomaly filter off, which is the tier1
configuration, the committed benchmark panel is therefore **5282 bars from
2005-01-03, of which 275 carry NaN** in the late-inception tickers.

The strategy handles those rows correctly rather than by luck.
`(prices <= 0).any().any()` does not reject NaN, because `NaN <= 0` is
False, and `rolling_covariance` is fed `daily_log_returns.dropna()`, which
removes any row with a missing leg before estimation. So no covariance is
ever estimated from incomplete data. The visible consequence is a longer
flat-equity warm-up: weights stay zero from 2005-01-03 through roughly
2007-02, the pre-DBC period plus the 252-day window, rather than from
2006-02-06.

Practical consequences:

* Every performance figure in this document and in `README.md` is measured
  on the 5282-bar runner panel at 5bp commission, not on the 5008-row
  complete-rows panel. Measured on the trimmed panel at 2bp the Sharpe for
  this variant reads roughly 0.03 higher. Quoting a number without its
  panel and commission is meaningless at that precision.
* This behaviour is inherited and applies to all 20 tier1 ETF strategies,
  including the three 3-asset incumbents, which show the identical 5282
  bars and 275 NaN rows. The cardinality comparison therefore stays
  controlled: both sides carry the same panel treatment.
* The 2008 crisis sits roughly 12 months after the first solvable rebalance,
  so the pre-crisis calibration sample is short either way.

Dropping DBC would buy roughly 13 months of extra complete history, to a
GLD-bound 2005-01-03 intersection. That was measured and rejected: it loses
the commodity sleeve and breaks the window identity with the incumbents that
makes the cardinality comparison controlled.

## 5. Covariance-estimation failure modes

Inherited from the shared `_covariance` helper and from the
`cov_window_days=252` default.

* A 252-day window means the covariance estimate lags regime changes by up
  to a year. Entering 2008 or March 2020, the estimator still reflects the
  prior calm regime and under-states correlations exactly when they spike.
* Ledoit-Wolf shrinkage toward a constant-correlation target reduces
  estimation error but biases toward the average pairwise correlation. On a
  universe with genuinely heterogeneous correlation structure, six sleeves
  here, that bias is not negligible.
* At N=10 with a 252-day window the sample-to-dimension ratio is 25:1. That
  is adequate but not generous; the measured condition number of the
  shrunken covariance was 1.073e+03 against 2.983e+00 at N=3. A larger
  universe on the same window would require revisiting the shrinkage choice.
* A constant-price or zero-variance leg makes `solve_erc_weights` raise
  `ValueError`. That rebalance is skipped and the previous weights persist by
  forward fill, so the strategy degrades rather than failing, but it also
  means a silently broken feed produces stale weights rather than an error.

## 6. Cluster correlation with sibling strategies

### Method

All figures measured 2026-10-21 against real yfinance prices. Two panel
constructions were used and they are not interchangeable, so both are stated.

The pre-build probe used a `dropna(how="any")` panel of 5007 complete rows,
2006-02-06 to 2025-12-30, through `vectorbt_bridge.run` at 2bp commission.

The cluster path, which is what `scripts/cluster_analysis.py --feed real`
actually runs, goes through `BenchmarkRunner._fetch_prices` and so inherits
the single-feed no-trim behaviour described in section 4: 5282 bars from
2005-01-03, 275 of them NaN-bearing, at bridge-default commission.

Running both gives a maximum intra-trio rho of +0.9480 on the probe panel and
+0.9482 on the cluster panel. The two differ by 0.0002, so the conclusion is
robust to the panel and commission choice even though the Sharpe figures in
section 1 are not. An earlier draft of this document claimed the probe panel
was the cluster's own configuration; that was wrong and is corrected here.

Comparator measurements including `permanent_portfolio` used 4712 aligned
bars, 2007-04-11 to 2025-12-30, limited by `gtaa_cross_asset_momentum`'s own
universe inception.

These are measurements, not predictions. The Session 2L plan called for
predictions written before the keyed run, and the Session 2K-4 four-way
calibration lesson supplied a priori bands. Because this variant group was
built after a pre-build probe, both are recorded: the a priori band that the
calibration lesson would have produced blind, and the measured value. The
distinction matters, because scoring measurements against bands derived from
the same measurements would be circular.

### A priori bands versus measured

A priori bands from the Session 2K-4 macro-UNDERSTATE lesson, recorded in
the Session 2L kickoff before any measurement:

| pair group | a priori band | measured | inside band |
|---|---|---|---|
| intra 10-asset trio, erc to minvar | 0.60 to 0.85 | +0.7262 | yes |
| intra 10-asset trio, erc to maxdiv | 0.60 to 0.85 | +0.9480 | no, above |
| intra 10-asset trio, minvar to maxdiv | 0.60 to 0.85 | +0.6791 | yes |
| erc_10 to erc_3 | 0.50 to 0.80 | +0.8665 | no, above |
| minvar_10 to minvar_3 | 0.50 to 0.80 | +0.6254 | yes |
| maxdiv_10 to maxdiv_3 | 0.50 to 0.80 | +0.8854 | no, above |
| erc_10 to permanent_portfolio | 0.60 to 0.80 | +0.8514 | no, above |
| minvar_10 to permanent_portfolio | 0.60 to 0.80 | +0.6059 | yes |
| maxdiv_10 to permanent_portfolio | 0.60 to 0.80 | +0.8243 | no, above |

Score: 4 of 9 inside band. All 5 misses are above the upper bound. The
Session 2K-4 lesson predicted that macro-family predictions UNDERSTATE real
co-movement; 5 of 5 misses fall in that predicted direction, so the lesson's
direction held even where its magnitudes did not.

### Cross-family comparators

| comparator | erc_10 | minvar_10 | maxdiv_10 |
|---|---|---|---|
| `permanent_portfolio` | +0.8514 | +0.6059 | +0.8243 |
| `gtaa_cross_asset_momentum` | -0.1604 | -0.0792 | -0.1737 |
| `vigilant_asset_allocation_5` | +0.2520 | +0.0925 | +0.2378 |

`permanent_portfolio` remains the project's correlation magnet, consistent
with the Session 2K-4 finding. Its universe is SPY/TLT/GLD/SHY, which
includes SHY, the asset all three solvers concentrate into. Shared SHY
exposure is the transmission path, not a shared objective.

`gtaa_cross_asset_momentum` is negatively correlated with all three
variants. A momentum rotation and a covariance-minimising allocator load on
opposite sides of the same assets during trends, so the negative sign is
structural rather than noise.

### Dedup-bar status

| configuration | max pairwise rho | vs 0.95 bar |
|---|---|---|
| N=3 incumbents, uncapped | +0.9930 | breached |
| N=10 this universe, uncapped | +0.9480 | below bar |
| N=10 this universe, `max_weight=0.25` | +0.9435 | below bar |
| N=7, single duration sleeve, uncapped | +0.9642 | breached |

The N=10 uncapped configuration clears the bar by 0.0020. That margin is
thin. It was measured through the bridge rather than estimated, and a
bridge-free weight-lagged calculation gives +0.9482 against the bridge's
+0.9480, so bridge mechanics account for roughly 0.0002 and do not explain
the margin away. A different window, commission assumption, or shrinkage
setting could still cross it. The `erc_10` to `maxdiv_10` pair is the one to
watch on every future cluster extension.

No new breach is introduced against the incumbents: the highest new-to-old
correlation is +0.8854.

## 7. Rebalance cadence: monthly signal, daily bridge-side drift correction

The signal is monthly. The vectorbt bridge applies
`SizeType.TargetPercent` semantics, so it generates daily drift-correction
trades on top of the monthly rebalance. Realised turnover and cost are
therefore higher than a literal monthly reading of
`rebalance_frequency` implies. See the Session 2G amendment
"alphakit-wide rebalance-cadence convention" in
`docs/phase-2-amendments.md`.

## 8. Solver convergence

`solve_erc_weights` was verified at N=10 on real covariance matrices before this
strategy was written: finite weights, row sum 1.0 to within 1e-6, long-only
satisfied, solve time between 2.5ms and 10.7ms. No modification was needed
for N=10, so the Session 2L hypothesis that the originals' 3-asset scope was
a solver limitation is not supported; the scope was a universe choice.

Residual risk: SLSQP is a local method. For the minimum-variance and
maximum-diversification objectives the feasible region is convex and the
objective is well-behaved, so a local optimum is the global one. The ERC
log-barrier objective is convex in `w` by construction. Measured ERC
risk-contribution spread was 9.6e-05 at one date at N=10 and 1.81e-04 at
N=3. Sampling 21 rebalance dates raised the worst observed spread to
5.371e-04, so a single-date measurement understates it. Code asserting
exact equal risk contribution will fail; assert to 1e-3.

## 9. Roughly 31 percent of monthly rebalances are silently skipped

Inherited verbatim from the three 3-asset incumbents, measured here for the
first time.

Weights are solved on calendar month-ends from
`leg_prices.resample("ME").last().index`, then transferred to the daily
index by `monthly_weights.reindex(leg_prices.index).ffill()`. A calendar
month-end that is not a trading day is absent from the daily index, so
`reindex` never transfers that month's weights and the previous month's
weights persist instead.

Measured on a 1260-bar business-day panel: 18 of 58 calendar month-ends
(31 percent) were not trading days, examples being 2015-01-31, 2015-02-28
and 2015-05-31, all Saturdays. The strategy therefore rebalanced on 40 of
58 month-ends, an effective cadence closer to every 1.45 months than every
month.

This is not corrected here. The same code is in all three 3-asset
incumbents, whose benchmarks are committed and tagged, so changing the
transfer logic would silently alter published results for six strategies at
once. It needs its own amendment and a coordinated regen rather than a
quiet fix inside a variant build.

Practical consequence: realised turnover is lower than a literal monthly
reading implies, and the signal responds to covariance changes with up to a
two-month lag rather than one.

## Limitations of this document

Every number here is a single-path measurement on one historical window with
one commission assumption. None of it is out-of-sample. The correlations in
section 6 will move as the window extends, and the +0.9480 maximum sits
0.0020 below the dedup bar, which is inside the range that a changed
assumption could move it.
