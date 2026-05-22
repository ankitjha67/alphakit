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

> **Phase 1 honesty note:** 37 of the 60 strategies shipped in v0.1.0 use
> price-derived proxies because real yield/options/fundamental data feeds
> ship in Phase 4. Six vol-strategies collapse to an identical implementation
> until the options engine ships. Four value strategies collapse to the same
> long-term-reversal proxy. All simplifications are documented in
> [`docs/deviations.md`](docs/deviations.md) and per-strategy `paper.md` files.
>
> **v0.2.0+ will ship real data feeds and dedupe these clusters.**

## Why AlphaKit?

- **Paper-cited.** Every strategy has a DOI, arXiv link, or book ISBN. No blog posts.
- **Benchmarked honestly.** Every strategy ships with `benchmark_results.json` from a 5+ year OOS run.
- **Failure modes documented.** "Dies in 2022 rate shock" beats silence.
- **One interface, multiple engines.** `StrategyProtocol` runs on the internal vectorized
  engine, vectorbt, backtrader, and (Phase 2+) LEAN.
- **Modular install.** Install only the families you need (see below).
- **Tested.** ≥85% coverage is a CI hard gate.

## Installation

AlphaKit is a monorepo of independently-installable sub-packages. The root
`pyproject.toml` is for local `uv` development only — it is **not**
pip-installable.

**Install everything from a release tag:**

```bash
# Linux / macOS
curl -sSL https://raw.githubusercontent.com/ankitjha67/alphakit/v0.1.1/scripts/install_from_git.sh \
  | bash -s -- v0.1.1

# Or clone and run locally
git clone https://github.com/ankitjha67/alphakit.git && cd alphakit
bash scripts/install_from_git.sh v0.1.1
```

**Install only what you need:**

```bash
TAG=v0.1.1
REPO=https://github.com/ankitjha67/alphakit.git

# Core (required by all strategy packages)
pip install "alphakit-core @ git+${REPO}@${TAG}#subdirectory=packages/alphakit-core"

# One strategy family
pip install "alphakit-strategies-trend @ git+${REPO}@${TAG}#subdirectory=packages/alphakit-strategies-trend"

# Backtest bridge
pip install "alphakit-bridges @ git+${REPO}@${TAG}#subdirectory=packages/alphakit-bridges"
```

**Local development (requires [uv](https://docs.astral.sh/uv/)):**

```bash
git clone https://github.com/ankitjha67/alphakit.git && cd alphakit
uv sync   # resolves all workspace packages locally
uv run pytest
```

## Quickstart

```python
from alphakit.strategies.trend.tsmom_12_1 import TimeSeriesMomentum12m1m
from alphakit.bridges.vectorbt_bridge import run
from alphakit.data.fixtures.generator import generate_fixture_prices

# 1. Generate (or load) a multi-asset price panel
prices = generate_fixture_prices(symbols=["SPY", "EFA", "EEM", "AGG", "GLD", "DBC"])

# 2. Instantiate the strategy with default config
strategy = TimeSeriesMomentum12m1m()

# 3. Run a vectorized backtest
result = run(strategy=strategy, prices=prices)

# 4. Inspect metrics
print(f"Sharpe:        {result.sharpe:.2f}")
print(f"Max DD:        {result.max_dd:.1%}")
print(f"Annual Return: {result.annualized_return:.1%}")
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

## Benchmark Leaderboard (v0.2.0)

> 109 strategies, 5 bps commission, OOS 2020-2025. v0.2.0 mixes data
> sources: **17 real-feed (yfinance, 2005-2025)** + **92 synthetic-fixture**.
> Each `benchmark_results.json` carries a `data_source` field. Synthetic
> Sharpes — especially the regime-state strategies, which run on favorable
> hand-crafted panels — are **not** real-feed-validated; treat the real-feed
> table below as the meaningful v0.2.0 ranking. See
> [docs/benchmark_notes.md](docs/benchmark_notes.md) for the honest analysis.

**Top 10 real-feed (`yfinance-real`) by Sharpe** — the v0.2.0 headline:

| # | Strategy | Family | Sharpe | Max DD | Ann. Return |
|---|----------|--------|-------:|-------:|------------:|
| 1 | permanent_portfolio | macro | +0.97 | -18.6% | +8.3% |
| 2 | vigilant_asset_allocation_5 | macro | +0.58 | -15.0% | +6.3% |
| 3 | risk_parity_erc_3asset | macro | +0.52 | -19.5% | +5.7% |
| 4 | max_diversification | macro | +0.46 | -19.9% | +5.1% |
| 5 | gtaa_cross_asset_momentum | macro | +0.43 | -68.2% | +17.0% |
| 6 | min_variance_gtaa | macro | +0.43 | -21.6% | +4.7% |
| 7 | real_yield_momentum | rates | +0.37 | -11.2% | +2.5% |
| 8 | bond_carry_rolldown | rates | +0.16 | -30.6% | +1.9% |
| 9 | credit_spread_momentum | rates | +0.09 | -22.8% | +0.9% |
| 10 | g10_bond_carry | rates | +0.07 | -13.7% | +0.6% |

**Top 10 by Sharpe across all 109** (with `data_source`):

| # | Strategy | Family | Sharpe | Max DD | Source |
|---|----------|--------|-------:|-------:|--------|
| 1 | yield_curve_regime_allocation | macro | +1.29 | -16.1% | synthetic ‡ |
| 2 | inflation_regime_allocation | macro | +1.24 | -25.9% | synthetic ‡ |
| 3 | growth_inflation_regime_rotation | macro | +1.20 | -25.9% | synthetic ‡ |
| 4 | permanent_portfolio | macro | +0.97 | -18.6% | **real** |
| 5 | recession_probability_rotation | macro | +0.96 | -18.8% | synthetic ‡ |
| 6 | fed_policy_tilt | macro | +0.77 | -22.1% | synthetic ‡ |
| 7 | vol_targeting (+5 proxies ^1) | volatility | +0.66 | -10.0% | synthetic |
| 8 | vigilant_asset_allocation_5 | macro | +0.58 | -15.0% | **real** |
| 9 | vix_roll_short | volatility | +0.58 | -15.7% | synthetic |
| 10 | risk_parity_erc_3asset | macro | +0.52 | -19.5% | **real** |

‡ **Regime-state strategies run on hand-crafted synthetic panels that
exercise their regimes favorably** (real-feed needs `FRED_API_KEY` + a runner
FRED-merge enhancement, deferred to v0.2.1). Their high synthetic Sharpes are
illustrative, not validated — see [docs/deviations.md](docs/deviations.md)
Phase 2 section.

^1 **Vol proxy cluster:** 5 additional Phase 1 strategies (covered_call_proxy,
cash_secured_put_proxy, wheel_strategy_proxy, iron_condor_systematic_proxy,
short_strangle_proxy) produce this identical Sharpe — same vol-scaled overlay
until the real options engine ships in Phase 4. See
[ADR-002](docs/adr/002-proxy-suffix-convention.md).

Summary: mean Sharpe -0.06, median -0.01, 45/109 positive. Cluster analysis
(49×49, Phase 2) found no undocumented near-duplicates — see
[docs/benchmark_notes.md](docs/benchmark_notes.md).

## Roadmap

| Phase | Strategies | Version |
|---|---|---|
| 0 — Foundation | 1 reference | v0.0.1 |
| 1 — Core families | 60 | v0.1.0 |
| 2 — Asset breadth | 109 (49 new; planned 65) | v0.2.0 |
| 3 — ML / RL | 165 | v0.3.0 |
| 4 — Long tail | 500+ | v1.0.0 |
| 5 — Multi-language | + C# / R | v1.1+ |

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Citation

If you use AlphaKit in academic work, please cite via [CITATION.cff](CITATION.cff).
