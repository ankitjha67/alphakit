# Phase 1 — Documented Simplifications & Deviations

This file aggregates all known simplifications where AlphaKit Phase 1
strategies deviate from the ideal implementation described in the
referenced paper. Each deviation is documented honestly so researchers
can evaluate which results to trust and which to discount.

See [ADR-001](adr/001-carry-data-deferred.md) for the architectural
decision behind carry-data proxies.

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
