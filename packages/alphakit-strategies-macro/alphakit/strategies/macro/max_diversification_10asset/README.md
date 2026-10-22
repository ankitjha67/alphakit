# max_diversification_10asset — Maximum-Diversification Portfolio on a 10-Asset Multi-Sleeve Universe

Maximum-diversification-ratio allocation across ten ETFs spanning six sleeves. Objective: maximise the diversification ratio
`DR(w) = (w' sigma) / sqrt(w' Sigma w)`, the ratio of weighted-average
asset volatility to realised portfolio volatility.

Session 2L variant of [`max_diversification`](../max_diversification/README.md).
Same published rule, same shared `_covariance` solver, wider universe. The
3-asset original is preserved unchanged.

## Why this strategy exists

Session 2K-4's 29x29 real-feed cluster found the three 3-asset
covariance-primitive strategies correlating at rho 0.980 to 0.993,
breaching the Phase 2 master-plan dedup-review bar of rho > 0.95. The
diagnosis was methodological convergence on a small universe, not a coding
defect: all three share one covariance estimator and differ only in solver
objective, and on a 3-asset universe every objective concentrates into the
lowest-variance asset.

This variant widens the universe to ten tickers across six sleeves. Measured
through the bridge, the three objectives separate to a maximum pairwise rho
of +0.9480, below the bar. See [`known_failures.md`](known_failures.md)
section 6 for the full measurement and its caveats.

## Quickstart

```python
from alphakit.strategies.macro.max_diversification_10asset import MaxDiversification10Asset
from alphakit.bridges import vectorbt_bridge
import pandas as pd

# Daily closing prices for all ten universe tickers.
prices: pd.DataFrame = ...   # columns: SPY, TLT, DBC, IEF, SHY, LQD, GLD, VNQ, EFA, EEM

strategy = MaxDiversification10Asset()
result = vectorbt_bridge.run(
    strategy=strategy,
    prices=prices,
    initial_cash=100_000,
    commission_bps=2,
)
```

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `universe` | shared `GTAA10_UNIVERSE` | ordered symbols; at least 3 distinct |
| `cov_window_days` | `252` | rolling covariance window, minimum 60 |
| `shrinkage` | `"ledoit_wolf"` | `"none"`, `"ledoit_wolf"`, or `"constant"` |
| `max_weight` | `1.0` | per-asset cap in (0, 1]; uncapped by default |

## Universe

| Ticker | Sleeve | First observation |
|---|---|---|
| `SPY` | US large-cap equity | 1993-01-29 |
| `TLT` | 20+ year Treasuries | 2002-07-30 |
| `DBC` | broad commodities | 2006-02-06 |
| `IEF` | 7-10 year Treasuries | 2002-07-30 |
| `SHY` | 1-3 year Treasuries | 2002-07-30 |
| `LQD` | investment-grade corporate credit | 2002-07-30 |
| `GLD` | gold | 2004-11-18 |
| `VNQ` | US real estate | 2004-09-29 |
| `EFA` | developed ex-US equity | 2001-08-27 |
| `EEM` | emerging-market equity | 2003-04-14 |

Inception dates measured 2026-10-21 via `scripts/audit_etf_universe.py`.

## Measured performance

From the committed `benchmark_results.json`, produced by
`regenerate_benchmarks.py tier1` (`BenchmarkRunner(commission_bps=5.0,
data_start="2005-01-01")`) on real yfinance prices, a 5282-bar panel from
2005-01-03. Sharpe, Sortino, Calmar and max drawdown are out-of-sample
(2020-01-01 to 2025-12-31, the runner's OOS window); return and volatility
are annualized. An earlier draft quoted full-period Sharpes computed by hand;
these are the committed OOS figures.

| metric (OOS 2020-2025, 5bp) | this variant | 3-asset incumbent |
|---|---|---|
| Sharpe | +0.4075 | +0.4620 |
| Sortino | +0.3849 | +0.4346 |
| Calmar | +0.1377 | +0.2283 |
| max drawdown | -0.1344 | -0.1993 |
| annualized return | +0.0195 | +0.0505 |
| annualized vol | 0.0478 | 0.1092 |

OOS Sharpe is slightly LOWER than the incumbent (+0.408 vs +0.462): this is
the one variant where the wider universe does not improve risk-adjusted
return. Max drawdown still roughly halves (19.9% to 13.4%) and volatility
drops from 10.9% to 4.8%, but the return give-up (5.1% to 2.0%) outweighs the
risk reduction on a ratio basis, and Calmar falls too (0.14 vs 0.23). That trade is structural, not incidental: see
[`known_failures.md`](known_failures.md) section 1.

## Documentation

* Foundational: Choueifaty, Y. & Coignard, Y. (2008). *Toward Maximum Diversification*. Journal of Portfolio Management 35(1), 40-51. DOI: https://doi.org/10.3905/JPM.2008.35.1.40
* Primary methodology: Choueifaty, Y., Froidure, T. & Reynier, J. (2011). *Properties of the Most Diversified Portfolio*. DOI: https://doi.org/10.2139/ssrn.1895459

* [Foundational and primary citations](paper.md)
* [Known failure modes](known_failures.md)
* [Benchmark](benchmark_results.json)

## Tests

```bash
uv run pytest packages/alphakit-strategies-macro/alphakit/strategies/macro/max_diversification_10asset/
```
