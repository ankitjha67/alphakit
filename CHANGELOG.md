# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-16

### Added

**60 systematic trading strategies across 5 families:**

- **Trend (15)**: tsmom_12_1, tsmom_volscaled, xs_momentum_jt, sma_cross_10_30,
  sma_cross_50_200, ema_cross_12_26, donchian_breakout_20, donchian_breakout_55,
  dual_momentum_gem, supertrend, ichimoku_cloud, turtle_full, frog_in_the_pan,
  residual_momentum, fifty_two_week_high
- **Mean-Reversion (15)**: bollinger_reversion, zscore_reversion, rsi_reversion_14,
  rsi_reversion_2, ou_process_trade, pairs_distance, pairs_engle_granger,
  pairs_johansen, pairs_kalman, statarb_pca, long_term_reversal,
  short_term_reversal_1m, gap_fill, overnight_intraday, crypto_basis_perp
- **Carry (10)**: fx_carry_g10, fx_carry_em, bond_carry_roll, dividend_yield,
  equity_carry, vol_carry_vrp, crypto_funding_carry, repo_carry,
  swap_spread_carry, cross_asset_carry
- **Value (10)**: pe_value, pb_value, ev_ebitda, fcf_yield, shareholder_yield,
  magic_formula, quality_value, piotroski_fscore_proxy, altman_zscore_proxy,
  country_cape_rotation
- **Volatility (10)**: vol_targeting, vix_term_structure, vix_roll_short,
  leveraged_etf_decay, covered_call_proxy, cash_secured_put_proxy,
  wheel_strategy_proxy, iron_condor_systematic_proxy, short_strangle_proxy,
  vrp_harvest

**Infrastructure:**
- `alphakit-core` — Protocols, metrics, Pydantic models
- `alphakit-data` — YFinance adapter with parquet cache, synthetic fixture generator
- `alphakit-bridges` — vectorbt bridge (from_orders-based backtester)
- `alphakit-bench` — Benchmark runner with strategy discovery, extended metrics, CLI
- `scripts/benchmark_all.py` — CLI for running all or individual benchmarks
- `.github/workflows/benchmark.yml` — Weekly cron benchmark with regression detection

**Documentation:**
- `docs/strategy_contract.md` — Per-strategy contract (Appendix C schema)
- `docs/deviations.md` — 37 documented simplifications + benchmark summary table
- `docs/benchmark_notes.md` — Honest v0.1.0 benchmark analysis
- `docs/adr/001-carry-data-deferred.md` — Carry data gap decision
- `docs/adr/002-proxy-suffix-convention.md` — `_proxy` suffix naming convention
- Per-strategy: paper.md, known_failures.md, README.md, config.yaml, benchmark_results.json

### Notes
- All v0.1.0 benchmarks use synthetic fixture data. Real-data benchmarks planned for v0.2.0.
- Options-based strategies use `_proxy` suffix (ADR-002). Phase 4 ships real options engine.
- 17/60 strategies show positive Sharpe on synthetic data. See benchmark_notes.md.

[0.1.0]: https://github.com/ankitjha67/alphakit/releases/tag/v0.1.0
[Unreleased]: https://github.com/ankitjha67/alphakit/compare/v0.1.0...HEAD
