# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-05-22

Real-feed validation for the 5 FRED-gated macro regime strategies, on the new
multi-feed benchmark runner (Session 2I). Three correctness bugs that only a
keyed real-feed + Windows dev cycle exposed are fixed.

### Added

- **Multi-feed `BenchmarkRunner`** (Session 2I): routes a strategy's
  informational (FRED) columns to the FRED feed and its tradable columns to
  yfinance, aligning the two via an as-of forward-fill. A `strict_feed` mode
  fails loud on any real-feed failure instead of silently substituting
  fixtures.
- **Real-feed regeneration / analysis entry points:**
  `scripts/regenerate_benchmarks.py tier2 --feed real` and
  `scripts/cluster_analysis.py --feed real` (both need `FRED_API_KEY` +
  `fredapi`; fail loud before any fetch when absent).

### Changed

- Real-feed (yfinance+FRED) benchmarks for the 5 FRED-gated regime macro
  strategies — recession_probability_rotation, growth_inflation_regime_rotation,
  yield_curve_regime_allocation, fed_policy_tilt, inflation_regime_allocation —
  stamped `data_source="yfinance+fred-real"`. OOS Sharpes **0.62–1.02**, modestly
  below the 0.77–1.29 seen on Session 2G hand-crafted synthetic panels: real
  macro regime transitions are noisier than favorably-constructed fixtures, yet
  the strategies still produce meaningful risk-adjusted returns on real data.
- Informational-column validation refined: **tradable** columns must be finite
  and `> 0`; **informational** columns need only be finite (zero and negative
  values now permitted). New `docs/phase-2-amendments.md` 2026-05-22 entry
  supersedes the 2026-05-16 "every column strictly positive" rule.

### Fixed

- **Bridge rejected valid informational data.** vectorbt's `from_orders`
  validates `order.price must be finite and greater than 0` for *every* column,
  including weight-0 informational ones, so a recession probability of 0.0
  crashed the run. The bridge now drops identically-zero-weight columns before
  `from_orders` — exactly P&L-neutral (0 shares × any finite price = 0).
- **FRED alignment dropped real observations.** Mixed-frequency series (quarterly
  GDPC1 on a monthly union index) and daily yields (holiday NaN) carried in-place
  NaN through the old index-based `reindex(method="ffill")`. Replaced with a
  value-based as-of fill over the union index, which also carries the last
  observation across the trailing publication-lag gap.
- **Atomic benchmark write failed on Windows.** `Path.rename` raises
  `FileExistsError` when the target exists (the common regen case); switched to
  `Path.replace` (atomic overwrite on POSIX and Windows).

### Notes

- All three Fixed bugs were surfaced only by a keyed real-feed + real-OS dev
  cycle; the S2I mock-only integration tests (always-positive, single-frequency,
  publication-lag-free panels) passed over them. See
  `docs/sessions/2i-closeout.md` for the process lesson and the v0.2.2 backlog.

## [0.2.0] - 2026-05-22

Multi-feed data architecture + 49 new strategies across four families
(planned 65; 16 honest drops). Total on `main`: **109** (60 Phase 1 + 49
Phase 2). Pre-release / silent build.

### Added

**49 new strategies:**

- **Rates (13)**: bond_tsmom_12_1, curve_steepener_2s10s, curve_flattener_2s10s,
  curve_butterfly_2s5s10s, bond_carry_rolldown, duration_targeted_momentum,
  breakeven_inflation_rotation, real_yield_momentum, yield_curve_pca_trade,
  g10_bond_carry, credit_spread_momentum, swap_spread_mean_rev,
  global_inflation_momentum
- **Commodity (10)**: commodity_tsmom, commodity_curve_carry,
  cot_speculator_position, wti_brent_spread, wti_backwardation_carry,
  ng_contango_short, crack_spread, crush_spread, grain_seasonality,
  metals_momentum
- **Options (15)**: covered_call_systematic, cash_secured_put_systematic,
  bxm_replication, bxmp_overlay, calendar_spread_atm, iron_condor_monthly,
  short_strangle_monthly, delta_hedged_straddle, gamma_scalping_daily,
  variance_risk_premium_synthetic, put_skew_premium, skew_reversal,
  vix_term_structure_roll, vix_3m_basis, weekly_short_volatility
- **Macro / GTAA (11)**: permanent_portfolio, gtaa_cross_asset_momentum,
  vigilant_asset_allocation_5, risk_parity_erc_3asset, min_variance_gtaa,
  max_diversification, recession_probability_rotation,
  growth_inflation_regime_rotation, yield_curve_regime_allocation,
  fed_policy_tilt, inflation_regime_allocation

**Data architecture:** FeedRegistry, disk-backed parquet cache (TTL),
rate-limit coordinator, offline mode (`ALPHAKIT_OFFLINE=1`),
`DataFeedProtocol.fetch_chain` extension. Four free-feed adapters (FRED,
yfinance-futures, EIA, CFTC COT), a Polygon placeholder, and a
synthetic-options chain generator. ADRs 003-007.

**Architectural primitives:** shared `_covariance` helper (Ledoit-Wolf
shrinkage + ERC/MV/MDP solvers); the informational-column pattern (FRED
series at weight 0.0); publication-lag handling; the `discrete_legs`
bridge metadata (Session 2F).

### Changed

- Standardized all 109 benchmarks on `benchmark_results.json` with a
  `data_source` field (`synthetic-fixture` / `yfinance-real`), retiring the
  dual-filename and macro custom-schema variants.
- Real-feed (yfinance) benchmarks for 17 ETF-only strategies (11 rates + 6
  macro). The other 92 remain synthetic-fixture; FRED-gated regime
  strategies, `swap_spread_mean_rev`, `global_inflation_momentum`, and the
  commodity/options families are deferred to a v0.2.1 real-feed pass.

### Fixed

- Benchmark runner test isolation: `test_write_benchmark` no longer mutates
  the tracked `tsmom_12_1/benchmark_results.json` on every run (Issue #1).

### Notes

- **Honest reduction:** 16 strategies dropped from the planned 65 for missing
  peer-reviewed anchors, missing data feeds, or cluster duplication.
- Synthetic benchmarks test that strategies run correctly end-to-end, not
  that they produce alpha. See `docs/benchmark_notes.md` and
  `docs/deviations.md`.

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

### Compatibility
- **Officially tested:** Python 3.10, 3.11, 3.12 (CI matrix on ubuntu + macos).
- **Unofficial:** Python 3.13 and 3.14 are known to install and run basic
  backtests, but are not part of the CI matrix. Dependency wheels (numpy,
  pandas, vectorbt) may not be available on all platforms for 3.14.

[0.1.0]: https://github.com/ankitjha67/alphakit/releases/tag/v0.1.0
[Unreleased]: https://github.com/ankitjha67/alphakit/compare/v0.1.0...HEAD
