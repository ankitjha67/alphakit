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
- `alphakit-core`: `StrategyProtocol`, `BacktestEngineProtocol`,
  `DataFeedProtocol`, `BacktestResult`; data schemas (`Bar`, `Tick`,
  `OptionChain`, `OrderBook`); instruments (`Equity`, `Option`, `Future`,
  `FXPair`, `CryptoPair`); `Signal` / `SignalDirection`; `Portfolio` /
  `Position` with rebalance engine; metrics (`sharpe_ratio`, `sortino_ratio`,
  `calmar_ratio`, `information_ratio`, `max_drawdown`, `ulcer_index`,
  `recovery_time`, `var_parametric`, `var_historical`, `cvar`, `tail_ratio`)
- `alphakit-bridges`: `vectorbt_bridge`, `backtrader_bridge`, `lean_bridge`
  stub (Phase 2+)
- `alphakit-strategies-trend`: reference strategy `tsmom_12_1`
  (Moskowitz-Ooi-Pedersen 2012 JFE) with full per-strategy contract:
  `strategy.py`, `config.yaml`, `paper.md`, `known_failures.md`,
  `benchmark_results.json` placeholder, `README.md`, unit and integration
  tests
- `CONTRIBUTING.md` with per-strategy contract spec
- `SECURITY.md` vulnerability reporting policy
- GitHub templates: PR template, new-strategy issue, bug-report issue
- CI workflows: `test.yml` (pytest matrix 3.10/3.11/3.12 × ubuntu/macos,
  coverage gate ≥85%), `lint.yml` (ruff + mypy strict),
  `docs.yml` (MkDocs build + deploy to gh-pages)
- MkDocs Material documentation site with landing page, quickstart,
  architecture, and strategy-contract pages

### TODO

- Add `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1) — tracked
  separately, will land before v0.1.0

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
