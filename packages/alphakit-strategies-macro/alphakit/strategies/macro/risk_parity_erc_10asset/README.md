# risk_parity_erc_10asset — Equal-Risk-Contribution Portfolio on a 10-Asset Multi-Sleeve Universe

Equal-risk-contribution allocation across ten ETFs spanning six sleeves. Objective: equalise each asset's marginal risk contribution
`RC_i = w_i * (Sigma w)_i / sqrt(w' Sigma w)`.

Session 2L variant of [`risk_parity_erc_3asset`](../risk_parity_erc_3asset/README.md).
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
from alphakit.strategies.macro.risk_parity_erc_10asset import RiskParityErc10Asset
from alphakit.bridges import vectorbt_bridge
import pandas as pd

# Daily closing prices for all ten universe tickers.
prices: pd.DataFrame = ...   # columns: SPY, TLT, DBC, IEF, SHY, LQD, GLD, VNQ, EFA, EEM

strategy = RiskParityErc10Asset()
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
| Sharpe | +0.5268 | +0.5224 |
| Sortino | +0.4921 | +0.4851 |
| Calmar | +0.2098 | +0.2694 |
| max drawdown | -0.1302 | -0.1953 |
| annualized return | +0.0284 | +0.0573 |
| annualized vol | 0.0539 | 0.1096 |

OOS Sharpe is essentially flat against the incumbent (+0.527 vs +0.522):
the gain is in risk, not risk-adjusted return. Annualized volatility and max
drawdown both roughly halve, and annualized return falls from 5.7% to 2.8%. That trade is structural, not incidental: see
[`known_failures.md`](known_failures.md) section 1.

## Documentation

* Foundational: Maillard, S., Roncalli, T. & Teiletche, J. (2010). *The Properties of Equally Weighted Risk Contribution Portfolios*. Journal of Portfolio Management 36(4), 60-70. DOI: https://doi.org/10.3905/jpm.2010.36.4.060
* Primary methodology: Asness, C. S., Frazzini, A. & Pedersen, L. H. (2012). *Leverage Aversion and Risk Parity*. Financial Analysts Journal 68(1), 47-59. DOI: https://doi.org/10.2469/faj.v68.n1.1

* [Foundational and primary citations](paper.md)
* [Known failure modes](known_failures.md)
* [Benchmark](benchmark_results.json)

## Tests

```bash
uv run pytest packages/alphakit-strategies-macro/alphakit/strategies/macro/risk_parity_erc_10asset/
```
