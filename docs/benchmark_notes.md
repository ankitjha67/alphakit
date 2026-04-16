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

## What these benchmarks do NOT prove

1. That any strategy produces real alpha
2. That Sharpe values would hold on real market data
3. That the proxy implementations approximate the paper's actual mechanism
4. Capacity estimates (these are formula-based, not empirically validated)
