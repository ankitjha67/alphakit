# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial repository scaffolding
- Root `pyproject.toml` with uv workspace configuration
- Apache 2.0 license
- Pre-commit hooks (ruff, black, mypy strict, nbstripout)
- Citation file (`CITATION.cff`)
- Workspace skeleton for `alphakit-core`, `alphakit-data`, `alphakit-bridges`,
  `alphakit-strategies-trend`

<!--
## [0.0.1] - 2026-04-15

### Added
- `StrategyProtocol`, `BacktestEngineProtocol`, `DataFeedProtocol`
- Core data types: `Bar`, `Tick`, `OptionChain`, `OrderBook`
- Instrument hierarchy: `Equity`, `Future`, `Option`, `Bond`, `FXPair`, `CryptoPair`
- Exchange calendar wrapper
- Order / Fill / Slippage / Commission models
- Portfolio, Position, Brinson attribution, rebalance engine
- Metrics: Sharpe, Sortino, Calmar, MaxDD, Ulcer, VaR, CVaR, turnover
- Internal vectorized backtest engine
- vectorbt and backtrader bridge adapters (optional)
- Reference strategy: `tsmom_12_1` (Time-Series Momentum 12/1, Moskowitz-Ooi-Pedersen 2012)
- GitHub Actions CI: ruff + mypy + pytest (≥85% coverage gate)
- MkDocs Material documentation site
-->

[Unreleased]: https://github.com/ankitjha67/alphakit/compare/HEAD...main
