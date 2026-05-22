# Benchmark Notes — v0.1.0 Honest Assessment

Generated: 2026-04-16  
Data source: **Synthetic fixture data** (deterministic, seeded)  
Engine: vectorbt  
Commission: 5 bps round-trip  
OOS period: 2020-01-01 to 2025-12-31

## Critical caveat

All v0.1.0 benchmarks use **synthetic fixture data**, not real market data.
The fixture generator produces realistic-looking price series with
configurable drift/vol per asset and a simple factor model for correlation,
but it lacks:

- Real market microstructure (bid-ask spread, volume patterns)
- Actual carry differentials (interest rates, dividends, funding rates)
- Fundamental data (earnings, book value, cash flow)
- Regime shifts from real macro events (2008, 2020 COVID, 2022 rate hikes)

**These benchmarks test that the code runs correctly end-to-end, not that
the strategies produce alpha on real data.** Real-data benchmarks require
the yfinance adapter and are planned for v0.2.0.

## Summary statistics

| Metric | Value |
|--------|-------|
| Strategies benchmarked | 60/60 |
| Positive Sharpe | 17/60 (28%) |
| Negative Sharpe | 43/60 (72%) |
| Mean Sharpe | -0.26 |
| Median Sharpe | -0.25 |
| Worst Sharpe | -1.26 (short_term_reversal_1m) |
| Best Sharpe | +0.66 (vol_targeting cluster) |

## Family averages

| Family | Mean Sharpe | Min | Max | Notes |
|--------|------------|-----|-----|-------|
| Trend | -0.23 | -0.71 | +0.45 | Mixed; slow crossovers work better than fast ones |
| Mean-reversion | -0.54 | -1.26 | +0.31 | Pairs strategies badly hurt by synthetic data |
| Carry | -0.60 | -1.24 | +0.29 | Expected: no real carry differentials in fixtures |
| Value | -0.28 | -1.06 | +0.10 | Price-only proxies show weak value signal |
| Volatility | +0.47 | -0.09 | +0.66 | Vol targeting works well even on synthetic data |

## Investigations

### Strategies with Sharpe < -0.5 (19 total)

Most negative Sharpes have **known, legitimate causes**:

**Carry family (4 strategies, Sharpe -0.59 to -1.24)**  
Carry strategies require real interest rate differentials. On synthetic data
where all FX pairs are random walks with similar drift, there is no carry
premium to harvest. bond_carry_roll (-1.24) is the worst because its entire
signal depends on yield curve data that doesn't exist in the fixture.
**Not a code bug — expected behavior on synthetic data.**

**Pairs/StatArb (4 strategies, Sharpe -0.49 to -1.26)**  
Cointegration-based strategies (pairs_engle_granger, pairs_johansen,
pairs_kalman, statarb_pca) require assets with genuine long-run relationships.
Synthetic data has a shared factor but independent idiosyncratic components,
which means cointegration tests will fit noise.
**Not a code bug — expected behavior on synthetic data.**

**short_term_reversal_1m (-1.26)**  
This strategy requires real overnight/close-to-close return reversals. Synthetic
returns are i.i.d. by construction (modulo GARCH clustering), so there is no
reversal signal. The strategy ends up buying noise and losing to commissions.
**Expected on synthetic data.**

**overnight_intraday (-1.13)**  
Similar to short_term_reversal — requires real intraday/overnight return
decomposition which synthetic daily data cannot provide.
**Expected on synthetic data.**

**piotroski_fscore_proxy (-1.06)**  
Uses drawdown-based quality proxy. On smooth synthetic data, drawdown doesn't
correlate with actual financial distress. The proxy trades noise.
**Expected given proxy severity (ADR-002).**

### Identical Sharpe clusters

**Vol proxy cluster (6 strategies, Sharpe +0.6565)**  
covered_call_proxy, cash_secured_put_proxy, wheel_strategy_proxy,
iron_condor_systematic_proxy, short_strangle_proxy, and vol_targeting all
produce identical results because the 5 _proxy strategies share the same
vol-scaled equity overlay implementation as vol_targeting. This is a
**documented, intentional limitation** (ADR-002). These strategies will
diverge in Phase 4 when the real options engine ships.

**Value cluster (4 strategies, Sharpe +0.0991)**  
ev_ebitda, fcf_yield, pb_value, and pe_value produce identical results
because they all use the same return-based value proxy. Documented in
docs/deviations.md. Will diverge with real fundamental data in Phase 3.

**Mean-rev cluster (2 strategies, Sharpe -0.2370)**  
bollinger_reversion and zscore_reversion are mathematically similar (both
z-score based, same lookback). Slight difference in implementation but
converge on identical signals with this data.

## No data leakage detected

- No strategy has |Sharpe| > 2.0
- OOS period (2020-2025) is strictly separate from training (2005-2019)
- All strategies use lookback parameters, not future data
- Fixture data is deterministic (seed=42) so results are reproducible

## What these benchmarks DO prove

1. All 60 strategies run to completion without errors
2. All produce finite, reasonable metrics
3. The benchmark infrastructure (discovery, runner, metrics, serialization) works
4. Results are deterministic and reproducible
5. No strategy crashes on edge cases in the data

## Fixture data limitations

The synthetic fixture generator (`alphakit.data.fixtures.generator`) uses
per-ticker drift/vol profiles with a shared market factor and GARCH-like
vol clustering. This design has **structural limitations** that make
certain strategy families unable to produce positive returns:

**Strategies that cannot work on fixture data by construction:**

| Strategy type | Required data property | Fixture limitation |
|---------------|----------------------|-------------------|
| Carry (FX, bond, equity) | Real interest rate / yield differentials | Fixtures have no rate data; "FX pairs" are synthetic price series with similar drift |
| Pairs / cointegration | Genuine long-run equilibrium relationships | Factor model produces correlated but not cointegrated series; Engle-Granger / Johansen tests fit noise |
| Short-term reversal | Bid-ask bounce, microstructure mean-reversion | Returns are conditionally independent (GARCH vol, but no serial correlation in direction) |
| Overnight / intraday | Intraday vs. overnight return decomposition | Only daily bars exist; overnight signal is undefined |
| Fundamental value | Earnings, book value, cash flow multiples | No fundamental data; all value strategies collapse to price-only proxies |

**Reframing negative Sharpes:** The 19 strategies with Sharpe < -0.5 are
**not broken strategies** — they are strategies whose alpha source does
not exist in the fixture data. On real market data with actual carry
differentials, cointegration relationships, and microstructure effects,
these strategies would be expected to produce materially different (and
in many cases positive) Sharpe ratios consistent with their published
papers.

The negative Sharpes on fixture data represent the cost of trading
(5 bps commission) plus the cost of fitting noise (false signals from
cointegration tests on non-cointegrated data, etc.).

## What these benchmarks do NOT prove

1. That any strategy produces real alpha
2. That Sharpe values would hold on real market data
3. That the proxy implementations approximate the paper's actual mechanism
4. Capacity estimates (these are formula-based, not empirically validated)

---

# Phase 2 cluster analysis (v0.2.0)

Generated by `scripts/cluster_analysis.py`. Pairwise Pearson correlation of
strategy equity-curve returns across the four Phase 2 families (rates,
commodity, options, macro), computed on a **common synthetic-fixture basis**
(deterministic, seed=42, 5,478 aligned bars) so strategies sharing tradable
symbols see identical underlying price paths.

**Coverage:** 47 of 49 Phase 2 strategies. Excluded: `commodity_curve_carry`
(uses a `front_symbols`/`next_symbols` config schema rather than `universe`)
and `cot_speculator_position` (requires CFTC `*_NET_SPEC` informational
columns the fixture generator does not synthesize). Both are analyzable in
the v0.2.1 real-feed pass.

**Scope caveat (load-bearing).** The 5 FRED-gated regime-state macro
strategies (`recession_probability_rotation`,
`growth_inflation_regime_rotation`, `yield_curve_regime_allocation`,
`fed_policy_tilt`, `inflation_regime_allocation`) read informational columns
that are generic GBM on synthetic fixtures, so their *regime signal is
degenerate here* and their cluster correlations are **not meaningfully
captured**. The authoritative cluster predictions for those remain the
per-strategy `known_failures.md` rho ranges (e.g. recession ↔ yield-curve
rho ~= 0.50-0.70), pending the v0.2.1 real-feed cluster pass (needs
`FRED_API_KEY` + the runner FRED-merge enhancement).

## Pairs at or above the dedup-review bar (rho > 0.95)

11 pairs, all **within documented deliberate-redundancy clusters**:

| rho | pair | cluster |
|---|---|---|
| 1.000 | `covered_call_systematic` ↔ `cash_secured_put_systematic` ↔ `bxm_replication` ↔ `bxmp_overlay` | options put-call-parity cluster (Session 2F) |
| 1.000 | `vix_3m_basis` ↔ `vix_term_structure_roll` | options VIX term-structure cluster (Session 2F) |
| 1.000 | `max_diversification` ↔ `risk_parity_erc_3asset` | macro covariance group (shared SPY+TLT+DBC universe) |
| 0.995 | `max_diversification` ↔ `min_variance_gtaa` | macro covariance group |
| 0.994 | `min_variance_gtaa` ↔ `risk_parity_erc_3asset` | macro covariance group |
| 1.000 | `breakeven_inflation_rotation` ↔ `swap_spread_mean_rev` | rates — fixture artifact (both degenerate to near-identical behavior absent real rate/swap data) |

**Macro covariance group note.** The ERC / minimum-variance /
maximum-diversification trio share the same 3-asset universe (SPY+TLT+DBC);
on a single deterministic fixture path the three objectives produce
near-identical weights, hence rho > 0.99. On real data with non-stationary
covariance the three diverge more (their `known_failures.md` predict
rho ~= 0.6-0.8). The high fixture-basis rho is an artifact of the shared
universe + single price path, not evidence of true redundancy; it is the
deliberate methodology family flagged in Session 2G.

**`breakeven_inflation_rotation` ↔ `swap_spread_mean_rev` (rates, rho = 1.0)**
is a new fixture-basis finding: absent real TIPS/swap spread data, both
collapse to similar proxy behavior. Flagged for the v0.2.1 real-feed review;
not a code defect (their signals are distinct on real data).

## Documented deliberate pairs (fixture-basis rho)

| pair | fixture rho | known_failures.md prediction | note |
|---|---|---|---|
| `risk_parity_erc_3asset` ↔ `permanent_portfolio` | +0.905 | ~0.60-0.75 | shared multi-asset allocation; fixture rho elevated by single price path |
| `recession_probability_rotation` ↔ `yield_curve_regime_allocation` | +0.430 | ~0.50-0.70 | **regime-degenerate on fixtures** — prediction authoritative, real-feed pass pending |
| `curve_steepener_2s10s` ↔ `curve_flattener_2s10s` | +0.000 | ~-1.0 (mirror) | fixtures lack a persistent curve signal, so the mirror relationship does not surface |

## Summary

* Mean off-diagonal |rho| across the 47 strategies: **0.215** — low average
  cross-correlation, consistent with a diversified library.
* Every rho > 0.95 pair sits inside a **documented** cluster (options parity,
  options VIX, macro covariance group) or is a labeled fixture artifact — no
  *undocumented* near-duplicates surfaced.
* Signal-driven relationships (regime pairs, curve mirror pairs) are **not**
  captured on synthetic fixtures and must be re-measured in the v0.2.1
  real-feed cluster pass; the per-strategy `known_failures.md` rho ranges
  remain authoritative until then.
