# Known failure modes — min_variance_gtaa_10asset

> The Session 2L variant group trades absolute return for risk-adjusted
> return. Every failure mode below follows from that one structural fact or
> from the covariance estimator the group shares.

Session 2L variant of `min_variance_gtaa`, added in response to the Session 2K-4
dedup-bar breach. The 3-asset original is preserved unchanged. Objective:
minimum total portfolio variance.

## 1. Lower absolute return than the 3-asset incumbent, by construction

Measured through `vectorbt_bridge.run` at 2bp commission, 5007 bars,
2006-02-06 to 2025-12-30:

| metric | this variant | `min_variance_gtaa` |
|---|---|---|
| Sharpe | +0.9212 | +0.5975 |
| max drawdown | -0.0746 | -0.2155 |
| final equity from 100,000 | 152,088 | 263,790 |

Higher Sharpe, shallower drawdown, lower terminal wealth. The mechanism is
direct: the wider universe contains SHY, a 1-3 year Treasury ETF with the
lowest variance in the set, and every covariance-minimising objective
concentrates into it. Measured mean SHY weight was 0.539 for ERC, 0.709 for
minimum variance, and 0.614 for maximum diversification.

A portfolio that is 54 to 71 percent short-duration Treasuries has low
volatility and low return. The improved Sharpe is real, and so is the
roughly 100,000 of forgone terminal wealth against the incumbent over twenty
years.

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

The minimum-variance solution sits at a corner whenever an asset is
dominated, so zero weights are expected and correct rather than a defect.
Measured over the window, six of ten assets carried a mean weight at or
below 0.011, and one asset was effectively never held. Any downstream code
treating a zero weight as an error will misfire on this strategy.

## 4. Effective panel start is 2006-02-06, not the nominal 2005-01-01

DBC incepts 2006-02-06 and binds the complete-rows intersection, so the
usable panel is 5008 rows starting 2006-02-06 against a nominal
`data_start` of 2005-01-01. Inception dates measured 2026-10-21 via
`scripts/audit_etf_universe.py`.

The 3-asset incumbents are bound by the same ticker to the same date, so the
cardinality comparison is controlled. But any comparison against a strategy
whose panel starts earlier is not window-matched, and the 2008 crisis sits
only 20 months into the usable history, so the pre-crisis calibration sample
is short.

Dropping DBC would buy roughly 13 months of extra history, to a GLD-bound
2005-01-03 start. That was measured and rejected: it loses the commodity
sleeve and, more importantly, breaks the window identity with the incumbents
that makes the comparison controlled.

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
* A constant-price or zero-variance leg makes `solve_min_variance_weights` raise
  `ValueError`. That rebalance is skipped and the previous weights persist by
  forward fill, so the strategy degrades rather than failing, but it also
  means a silently broken feed produces stale weights rather than an error.

## 6. Cluster correlation with sibling strategies

### Method

All figures measured 2026-10-21 against real yfinance prices through
`vectorbt_bridge.run` at 2bp commission, the same configuration
`scripts/cluster_analysis.py --feed real` uses. Panel for the 10-asset and
3-asset comparisons: 5007 complete rows, 2006-02-06 to 2025-12-30.
Comparator panel including `permanent_portfolio`: 4712 aligned bars,
2007-04-11 to 2025-12-30.

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

`solve_min_variance_weights` was verified at N=10 on real covariance matrices before this
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
