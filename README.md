# AlphaKit

> The most comprehensive, researcher-defensible, multi-asset, plug-and-play open-source quant strategy library.

[![Release](https://img.shields.io/badge/release-v0.1.0-blue)](https://github.com/ankitjha67/alphakit/releases/tag/v0.1.0)
[![Strategies](https://img.shields.io/badge/strategies-60-brightgreen)](https://github.com/ankitjha67/alphakit)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/ankitjha67/alphakit/actions)
[![Coverage](https://img.shields.io/badge/coverage-%E2%89%A585%25-brightgreen)](https://github.com/ankitjha67/alphakit)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/alphakit/)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://ankitjha67.github.io/alphakit)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

AlphaKit is a modular monorepo of paper-cited, benchmarked, production-grade trading
strategies covering 14+ asset classes. The architecture is a **thin core** (`StrategyProtocol`,
data schemas, metrics, adapters) with **independent sub-packages** by strategy family.
Every strategy ships with paper citation, parameter defaults, OOS benchmarks, documented
failure modes, and unit + integration tests.

## Why AlphaKit?

- **Paper-cited.** Every strategy has a DOI, arXiv link, or book ISBN. No blog posts.
- **Benchmarked honestly.** Every strategy ships with `benchmark_results.json` from a 5+ year OOS run.
- **Failure modes documented.** "Dies in 2022 rate shock" beats silence.
- **One interface, multiple engines.** `StrategyProtocol` runs on the internal vectorized
  engine, vectorbt, backtrader, and (Phase 2+) LEAN.
- **Modular install.** `pip install alphakit[crypto]` does not pull equities or rates deps.
- **Tested.** ≥85% coverage is a CI hard gate.

## Quickstart

```python
from alphakit.strategies.trend.tsmom_12_1 import TimeSeriesMomentum12m1m
from alphakit.bridges.internal import run_backtest
from alphakit.data.synthetic import multi_asset_panel

# 1. Generate (or load) a multi-asset price panel
prices = multi_asset_panel(symbols=["SPY", "EFA", "EEM", "AGG", "GLD", "DBC"], years=20)

# 2. Instantiate the strategy with default config
strategy = TimeSeriesMomentum12m1m(lookback_months=12, skip_months=1, vol_target_annual=0.10)

# 3. Run a vectorized backtest
result = run_backtest(strategy=strategy, prices=prices)

# 4. Inspect metrics
print(f"Sharpe:        {result.metrics.sharpe:.2f}")
print(f"Max DD:        {result.metrics.max_drawdown:.1%}")
print(f"Annual Return: {result.metrics.annualized_return:.1%}")
```

See [docs/quickstart.md](docs/quickstart.md) for the full walkthrough and
[docs/strategy_contract.md](docs/strategy_contract.md) for the per-strategy contract.

## Documentation

Live site: <https://ankitjha67.github.io/alphakit>

- [Quickstart](docs/quickstart.md)
- [Architecture](docs/architecture.md)
- [Strategy contract](docs/strategy_contract.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Benchmark Leaderboard (v0.1.0, synthetic data)

> Benchmarked on deterministic fixture data with 5 bps commission.
> See [docs/benchmark_notes.md](docs/benchmark_notes.md) for honest analysis.

**Top 10 by Sharpe:**

| # | Strategy | Family | Sharpe | Max DD | Ann. Return |
|---|----------|--------|-------:|-------:|------------:|
| 1 | vol_targeting | volatility | +0.66 | -10.0% | +4.7% |
| 2 | vix_roll_short | volatility | +0.58 | -15.7% | +5.8% |
| 3 | sma_cross_50_200 | trend | +0.45 | -20.0% | +2.7% |
| 4 | dual_momentum_gem | trend | +0.44 | -29.7% | +6.2% |
| 5 | gap_fill | meanrev | +0.31 | -2.8% | +0.4% |
| 6 | crypto_funding_carry | carry | +0.29 | -13.2% | +3.3% |
| 7 | vrp_harvest | volatility | +0.29 | -12.0% | +2.1% |
| 8 | xs_momentum_jt | trend | +0.19 | -18.9% | +1.8% |
| 9 | ev_ebitda | value | +0.10 | -12.1% | +0.7% |
| 10 | ou_process_trade | meanrev | -0.03 | -5.1% | -0.1% |

**Top 5 by Calmar (return/max-drawdown):**

| # | Strategy | Family | Calmar | Max DD | Ann. Return |
|---|----------|--------|-------:|-------:|------------:|
| 1 | vol_targeting | volatility | 0.45 | -10.0% | +4.7% |
| 2 | vix_roll_short | volatility | 0.36 | -15.7% | +5.8% |
| 3 | gap_fill | meanrev | 0.28 | -2.8% | +0.4% |
| 4 | vrp_harvest | volatility | 0.24 | -12.0% | +2.1% |
| 5 | dual_momentum_gem | trend | 0.18 | -29.7% | +6.2% |

## Roadmap

| Phase | Strategies | Version |
|---|---|---|
| 0 — Foundation | 1 reference | v0.0.1 |
| 1 — Core families | 60 | v0.1.0 |
| 2 — Asset breadth | 125 | v0.2.0 |
| 3 — ML / RL | 165 | v0.3.0 |
| 4 — Long tail | 500+ | v1.0.0 |
| 5 — Multi-language | + C# / R | v1.1+ |

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Citation

If you use AlphaKit in academic work, please cite via [CITATION.cff](CITATION.cff).
