# Phase 1 — Documented Simplifications & Deviations

This file aggregates all known simplifications where AlphaKit Phase 1
strategies deviate from the ideal implementation described in the
referenced paper. Each deviation is documented honestly so researchers
can evaluate which results to trust and which to discount.

See [ADR-001](adr/001-carry-data-deferred.md) for the architectural
decision behind carry-data proxies.

See [benchmark_notes.md](benchmark_notes.md) for honest benchmark analysis.

## Known strategy clusters

Two groups of strategies produce **identical benchmark results** in v0.1.0
because they share the same underlying proxy implementation. This is an
intentional, documented limitation — not a bug.

### Cluster 1: Vol proxy (6 strategies, Sharpe +0.6565)

These strategies all reduce to the same vol-scaled equity overlay:

- `vol_targeting` (Moreira & Muir 2017) — the "real" implementation
- `covered_call_proxy` (Whaley 2002) — ADR-002 proxy
- `cash_secured_put_proxy` (Ungar & Moran 2009) — ADR-002 proxy
- `wheel_strategy_proxy` (practitioner) — ADR-002 proxy
- `iron_condor_systematic_proxy` (Israelov & Nielsen 2014) — ADR-002 proxy
- `short_strangle_proxy` (Israelov & Nielsen 2014) — ADR-002 proxy

**Why they are identical:** The 5 `_proxy` strategies require an options
pricing engine to differentiate their payoff profiles (covered call vs.
iron condor vs. strangle). Without options Greeks, delta hedging, or strike
selection, they all collapse to "long equity, scaled by inverse realized
vol." The canonical slugs (without `_proxy`) are reserved for Phase 4
when the real options engine ships.

**When they will diverge:** Phase 4 (v1.0.0), which introduces the options
pricing engine, real Greeks, and strike selection logic.

### Cluster 2: Value proxy (4 strategies, Sharpe +0.0991)

These strategies all reduce to the same long-term-reversal value proxy:

- `pe_value` (Fama & French 1992)
- `pb_value` (Fama & French 1992)
- `ev_ebitda` (standard fundamental screen)
- `fcf_yield` (standard fundamental screen)

**Why they are identical:** All four require fundamental data (earnings,
book value, EBITDA, free cash flow) that is not available in Phase 1.
The proxy uses negative trailing 10-year return as a value signal, which
is the same computation for all four because the only input is price.

**When they will diverge:** Phase 3 (v0.3.0), which introduces fundamental
data feeds from SEC EDGAR / Compustat / similar providers.

---

## Benchmark Summary Table (v0.1.0, synthetic data)

| Strategy | Family | Shipped Sharpe | Paper Sharpe | Delta | Notes |
|----------|--------|---------------:|-------------:|------:|-------|
| vol_targeting | volatility | +0.66 | ~0.7-1.0 | ~-0.2 | Direct impl, no proxy needed |
| vix_roll_short | volatility | +0.58 | ~1.0+ | ~-0.4 | Proxy; real VIX futures would differ |
| sma_cross_50_200 | trend | +0.45 | ~0.3-0.5 | ~0.0 | Reasonable match |
| dual_momentum_gem | trend | +0.44 | ~0.5-0.7 | ~-0.2 | Reasonable on synthetic data |
| gap_fill | meanrev | +0.31 | ~0.4+ | ~-0.1 | Needs real intraday data for accuracy |
| vrp_harvest | volatility | +0.29 | ~0.5-0.8 | ~-0.3 | Vol term structure proxy |
| crypto_funding_carry | carry | +0.29 | ~0.5+ | ~-0.2 | No real funding rates in fixtures |
| xs_momentum_jt | trend | +0.19 | ~0.5-0.7 | ~-0.4 | Cross-sectional weaker on 6 assets |
| ev_ebitda | value | +0.10 | ~0.3-0.5 | ~-0.3 | Return-based proxy, no fundamentals |
| short_term_reversal_1m | meanrev | -1.26 | ~0.5+ | ~-1.8 | Synthetic data has no reversal signal |
| bond_carry_roll | carry | -1.24 | ~0.4-0.6 | ~-1.7 | No yield curve data in fixtures |

Paper Sharpe values are approximate ranges from original publications.
Delta is rough (synthetic data ≠ real data). See benchmark_notes.md for details.

---

## Trend family

### residual_momentum
- **Paper**: Blitz, Huij & Martens (2011)
- **Ideal**: Residuals computed from Fama-French 3-factor regression
- **Phase 1**: Uses single-factor (market return) regression. FF3
  factor data requires an external feed not available in the protocol.
- **Impact**: Residuals retain exposure to SMB and HML factors.

### frog_in_the_pan
- **Paper**: Da, Gurun & Warachka (2014)
- **Ideal**: Uses discrete information events (earnings, news)
- **Phase 1**: Approximates "information discreteness" via the
  fraction of positive return days in the lookback window.
- **Impact**: Proxy captures return sign concentration but misses
  the economic content of the original signal.

### ichimoku_cloud
- **Paper**: Hosoda (1969), practitioner lore
- **Ideal**: Ichimoku includes 5 components including Chikou span
  (lagged close plotted 26 periods back)
- **Phase 1**: Implements Tenkan/Kijun cross with Kumo filter.
  Chikou span confirmation omitted for simplicity.
- **Impact**: Slightly more signals than canonical implementation.

### supertrend
- **Paper**: Patel (2020), practitioner indicator
- **Ideal**: Uses Average True Range (ATR) requiring OHLC data
- **Phase 1**: Approximates ATR using close-only data with rolling
  high-low range estimated from log-returns.
- **Impact**: ATR proxy is noisier than true OHLC-based ATR.

### turtle_full
- **Paper**: Curtis Faith (2007), "Way of the Turtle"
- **Ideal**: Uses ATR for position sizing and stop placement
- **Phase 1**: ATR approximated from close-only data (same as
  supertrend).
- **Impact**: Position sizes and stops may differ from canonical.

---

## Mean-reversion family

### overnight_intraday
- **Paper**: Lou, Polk & Skouras (2019)
- **Ideal**: Decompose returns into close-to-open (overnight) and
  open-to-close (intraday) components
- **Phase 1**: Protocol provides only close prices, no open. Uses
  cross-sectional residuals of daily returns as overnight proxy.
- **Impact**: Signal conflates overnight alpha with idiosyncratic
  daily returns. Pure overnight/intraday decomposition impossible
  without open prices.

### crypto_basis_perp
- **Paper**: No formal DOI (exchange mechanics)
- **Ideal**: Separate perpetual futures and spot price feeds
- **Phase 1**: Uses fast/slow MA spread as basis proxy.
- **Impact**: MA spread approximates the premium/discount but misses
  actual funding rate mechanics and settlement timing.

---

## Carry family

### fx_carry_g10
- **Paper**: Lustig, Roussanov & Verdelhan (2011)
- **Ideal**: Sort by interest-rate differential (forward discount)
- **Phase 1**: Uses trailing 63-day return as carry proxy.
- **Impact**: Proxy conflates carry with momentum. True FX carry
  depends on rate differentials, not past returns.

### fx_carry_em
- **Paper**: Burnside et al. (2011)
- **Ideal**: Same as G10 — interest-rate differentials
- **Phase 1**: Same trailing return proxy as G10.
- **Impact**: Same as fx_carry_g10. EM currencies have additional
  data challenges (capital controls, illiquidity).

### dividend_yield
- **Paper**: Litzenberger & Ramaswamy (1979)
- **Ideal**: Trailing 12-month dividend yield from corporate actions
- **Phase 1**: Uses trailing return / trailing volatility as proxy.
- **Impact**: Proxy captures "high-return, low-vol" but conflates
  with quality/low-vol factors, not pure dividend yield.

### equity_carry
- **Paper**: KMPV (2018)
- **Ideal**: Dividend yield + buyback yield + earnings growth
- **Phase 1**: Uses trailing return as carry proxy.
- **Impact**: Trailing return is momentum, not carry. True equity
  carry requires fundamental data (dividends, buybacks).

### bond_carry_roll
- **Paper**: KMPV (2018)
- **Ideal**: Yield + roll-down from yield curve slope
- **Phase 1**: Trailing return proxy for bond indices.
- **Impact**: Trailing return captures both carry and price movement.
  True bond carry requires yield-curve data.

### vol_carry_vrp
- **Paper**: Carr & Wu (2009)
- **Ideal**: Sell variance via short ATM straddles, delta-hedged
- **Phase 1**: Uses fast/slow realized vol spread as VRP proxy.
  No options or VIX data.
- **Impact**: Realized vol term structure is a rough proxy for the
  variance risk premium. Does not capture the actual implied-vs-
  realized vol spread.

### crypto_funding_carry
- **Paper**: No formal DOI (exchange mechanics)
- **Ideal**: Actual perpetual funding rate data from exchanges
- **Phase 1**: Uses fast/slow MA spread as funding proxy.
- **Impact**: Same limitation as crypto_basis_perp. MA spread
  approximates but doesn't capture actual 8-hour funding settlements.

### repo_carry
- **Paper**: Duffie (1996)
- **Ideal**: GC repo rate vs special repo rate spread
- **Phase 1**: Uses Z-score of price deviation from rolling mean
  as "specialness" proxy.
- **Impact**: Price-level mean reversion is a poor proxy for repo
  rate specialness. True implementation requires repo market data.

### swap_spread_carry
- **Paper**: Duarte, Longstaff & Yu (2007)
- **Ideal**: Swap rate − Treasury yield spread across tenors
- **Phase 1**: Trailing return cross-sectional ranking.
- **Impact**: Trailing return doesn't capture the actual swap spread.
  True implementation requires swap and Treasury rate data.

### cross_asset_carry
- **Paper**: KMPV (2018)
- **Ideal**: Asset-class-specific carry signals (FX rates, dividend
  yields, bond yields, commodity roll yield) with inverse-vol
  weighting across sleeves.
- **Phase 1**: Single risk-adjusted trailing return signal applied
  uniformly across all assets.
- **Impact**: Loses the asset-class-specific carry definitions that
  are central to the KMPV framework.

---

## Value family

All value strategies use long-term price reversal as the primary
value proxy. This is academically documented (DeBondt & Thaler 1985)
but is NOT equivalent to using actual fundamental ratios.

### pb_value
- **Paper**: Fama & French (1992)
- **Ideal**: Cross-sectional rank by book-to-market ratio (B/M)
- **Phase 1**: 3-year trailing return reversal as P/B proxy.
- **Impact**: Reversal captures value broadly but conflates with
  long-term mean reversion and distress.

### pe_value
- **Paper**: Basu (1977)
- **Ideal**: Cross-sectional rank by earnings yield (E/P)
- **Phase 1**: Same reversal proxy as pb_value.
- **Impact**: Cannot distinguish low P/E from negative earnings.

### ev_ebitda
- **Paper**: Loughran & Wellman (2011)
- **Ideal**: Cross-sectional rank by EBITDA/EV
- **Phase 1**: Same reversal proxy.
- **Impact**: Enterprise value requires debt data; EBITDA requires
  income statement. Reversal proxy misses both.

### fcf_yield
- **Paper**: Lakonishok, Shleifer & Vishny (1994)
- **Ideal**: Cross-sectional rank by FCF/Price
- **Phase 1**: Same reversal proxy.
- **Impact**: FCF requires cash flow statement data.

### shareholder_yield
- **Paper**: Faber (2013)
- **Ideal**: (Dividends + buybacks + debt paydown) / market cap
- **Phase 1**: Fraction of positive monthly returns over 1 year.
- **Impact**: Return regularity is a rough proxy for stable payouts
  but misses actual capital allocation decisions.

### magic_formula
- **Paper**: Greenblatt (2006)
- **Ideal**: Combined rank of EBIT/EV + ROIC
- **Phase 1**: Combined reversal (value) + vol-adjusted return
  (quality) ranking.
- **Impact**: Neither component uses accounting data. The composite
  captures "cheap + strong" in price space, not earnings space.

### piotroski_fscore_proxy ⚠️ SEVERE DEVIATION (ADR-002)
- **Paper**: Piotroski (2000)
- **Ideal**: 9-point score from profitability, leverage/liquidity,
  and operating efficiency — all computed from financial statements
- **Phase 1**: 9 price-derived signals (momentum, vol, trend,
  drawdown). This is NOT the F-Score.
- **Impact**: Zero correlation expected between proxy and true
  F-Score. The proxy is a standalone price-based quality composite.
  The slug `piotroski_fscore` is reserved for Phase 4.

### altman_zscore_proxy ⚠️ SEVERE DEVIATION (ADR-002)
- **Paper**: Altman (1968)
- **Ideal**: Z = 1.2×WC/TA + 1.4×RE/TA + 3.3×EBIT/TA +
  0.6×MVE/BVL + 0.999×Sales/TA — all accounting ratios
- **Phase 1**: Composite of drawdown severity + volatility +
  trend + return. This is NOT the Z-Score.
- **Impact**: Cannot detect actual balance sheet deterioration.
  Drawdown ≠ insolvency. The slug `altman_zscore` is reserved
  for Phase 4.

### quality_value
- **Paper**: Asness, Frazzini & Pedersen (2019)
- **Ideal**: Quality = profitability + growth + safety + payout,
  combined with HML value factor
- **Phase 1**: Quality = low-vol + momentum. Value = reversal.
- **Impact**: "Quality" proxy captures defensive momentum, not
  actual fundamental quality metrics.

### country_cape_rotation
- **Paper**: Faber (2014)
- **Ideal**: Trailing 10-year Shiller CAPE by country
- **Phase 1**: Negative trailing 10-year return as CAPE proxy.
- **Impact**: Long-term return reversal is a reasonable CAPE proxy
  (low past returns → low valuations), but misses earnings normalization
  and composition changes. Mildest deviation in the value family.

---

## Volatility family

### vol_targeting
- **Paper**: Moreira & Muir (2017)
- **Ideal**: Scale position by target_vol / realized_vol
- **Phase 1**: Direct implementation — no proxy needed.
- **Impact**: None. This strategy works with close-only data.

### vix_term_structure
- **Paper**: Simon & Campasano (2014)
- **Ideal**: Trade VIX futures based on term structure slope
- **Phase 1**: Realized vol term structure (5d vs 60d) as VIX proxy.
- **Impact**: Realized vol is not VIX. VIX is forward-looking
  (implied vol); realized vol is backward-looking.

### vix_roll_short
- **Paper**: Alexander & Korovilas (2012)
- **Ideal**: Short VIX futures roll yield
- **Phase 1**: Long equity scaled by inverse of realized vol.
- **Impact**: Does not capture actual VIX futures roll mechanics.
  WARNING: XIV-style blowup risk (Feb 2018: 96% loss in one day).

### leveraged_etf_decay
- **Paper**: Cheng & Madhavan (2009)
- **Ideal**: Short paired leveraged + inverse ETFs
- **Phase 1**: Short exposure proportional to trailing variance.
- **Impact**: Actual decay requires daily-rebalanced ETF mechanics.
  Proxy captures vol-drag concept but not exact compounding.

### covered_call_proxy ⚠️ SEVERE DEVIATION (ADR-002)
- **Paper**: Whaley (2002) — BXM buy-write index
- **Ideal**: Long stock + short ATM call options
- **Phase 1**: Long equity with vol-scaled position sizing. This is
  NOT an options strategy. No actual premium collection.
- **Impact**: Zero correlation with actual covered-call P&L profile.
  Slug `covered_call` reserved for Phase 4.

### cash_secured_put_proxy ⚠️ SEVERE DEVIATION (ADR-002)
- **Paper**: Ungar & Moran (2009) — PUT index
- **Ideal**: Short ATM put options, cash-secured
- **Phase 1**: Same vol-scaled equity overlay as covered_call_proxy.
- **Impact**: Same as covered_call_proxy. No actual put selling.

### wheel_strategy_proxy ⚠️ SEVERE DEVIATION (ADR-002)
- **Paper**: Practitioner folklore (no formal DOI)
- **Ideal**: CSP → assignment → CC → called away loop
- **Phase 1**: Vol-scaled equity overlay. No assignment mechanics.
- **Impact**: Cannot model the wheel's sequential options flow.

### iron_condor_systematic_proxy ⚠️ SEVERE DEVIATION (ADR-002)
- **Paper**: Israelov & Nielsen (2014)
- **Ideal**: Sell 1σ strangles, capped profit/loss
- **Phase 1**: Vol-scaled equity overlay. No spread payoff profile.
- **Impact**: Iron condor has defined max loss; proxy does not.

### short_strangle_proxy ⚠️ SEVERE DEVIATION (ADR-002)
- **Paper**: Israelov & Nielsen (2014)
- **Ideal**: Short strangles with unlimited tail risk
- **Phase 1**: Vol-scaled equity overlay.
- **Impact**: Cannot model the unlimited-loss tail risk of actual
  strangles. Proxy understates tail exposure.

### vrp_harvest
- **Paper**: Carr & Wu (2009)
- **Ideal**: Short variance swaps
- **Phase 1**: Long equity when realized vol term structure is in
  contango (slow > fast), scaled by target_vol/realized_vol.
- **Impact**: Reasonable proxy — the VRP is fundamentally about
  the gap between implied and realized vol. Using realized vol
  term structure captures the directional signal but not the
  exact premium magnitude.
