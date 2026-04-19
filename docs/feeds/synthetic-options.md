# Synthetic option chains

**Status:** Primary Phase 2 options feed.
**Registered name:** `synthetic-options`
**API key:** none — fully offline-capable (chain-only).

## Methodology

For each `fetch_chain(underlying, as_of)` call:

1. Fetch ≈ 252 trading-bar history of the underlying's closing prices
   from the injected *underlying feed* (defaults to `yfinance`).
2. Compute trailing 30-/60-/90-day realized volatility from log
   returns. Each expiry uses the window closest to its days-to-expiry:
   * `< 45` DTE → 30-day realized vol.
   * `45 ≤ DTE < 120` → 60-day realized vol.
   * `≥ 120` DTE → 90-day realized vol.
3. Build a 9-point strike grid at `{0.80, 0.85, 0.90, 0.95, 1.00,
   1.05, 1.10, 1.15, 1.20} × spot`.
4. Build a 11-14-point expiry grid (see [expiry grid dedup](#expiry-grid-dedup)).
5. For every `(strike, expiry, right)` combination, price via
   Black-Scholes and populate the `OptionQuote` with BS-computed
   greeks.

All pricing is deterministic: the same `(underlying, as_of)` input
produces a byte-identical `OptionChain`. The shared contract test
`test_adapter_fetch_chain_is_deterministic` enforces this across
every chain-capable adapter.

## Strike grid

Nine symmetric moneyness points: `0.80 × spot` to `1.20 × spot` in
`0.05` increments. The grid captures the usual delta range that
systematic strategies care about (far OTM puts for skew / tail
trades, deep ITM for insurance-style structures, ATM for vol
harvesting). Extending the grid is a one-line change to
`STRIKE_MULTIPLIERS` in `alphakit.data.options.synthetic`.

## Expiry grid

The raw pool combines:

* **4 weekly** expiries — next four Fridays strictly after `as_of`.
* **6 monthly** expiries — the third Friday of the next six calendar
  months (current month included if its third Friday has not yet
  passed).
* **4 quarterly** expiries — the third Friday of the next four
  Mar/Jun/Sep/Dec months.

Raw pool size is 14. After date-level dedup (see below), the grid
typically holds 11-14 distinct expiries.

### Expiry grid dedup

The weekly, monthly, and quarterly lists overlap by construction. A
monthly third Friday that falls within the next four weeks is also a
weekly Friday; a quarterly third Friday is always a monthly third
Friday. A Python `set` collapses these coincidences to unique dates;
the grid is then sorted ascending.

Concrete examples (at the top of a month versus after that month's
third Friday):

| `as_of`          | weekly-only | monthly-only | quarterly-only | dedup count |
|------------------|-------------|--------------|----------------|-------------|
| 2024-01-02 (Tue) | 3           | 5            | 2              | 11          |
| 2024-01-22 (Mon) | 3           | 5            | 2              | 11          |

Total-quote count range: `11-14 expiries × 9 strikes × 2 rights` =
**198–252 quotes per chain**. The upper bound is only reached when
no weekly/monthly/quarterly collision occurs, which is rare in
practice.

## Known limitations

* **Flat vol across strikes.** The realized-vol estimator produces a
  single number per window; that number is used for every strike at a
  given expiry. There is no IV skew, so strategies that monetize skew
  (put-skew premium, risk-reversals, dispersion proxies) back-test
  against an approximation, not a market.
* **No bid-ask spread.** `bid == ask == last == BS-price`.
  Microstructure-dependent strategies have no spread to cross.
* **No volume or open interest.** Liquidity-weighted strategies
  cannot be back-tested faithfully.
* **Synthetic greeks.** Greeks are BS-computed, not market-implied.
  A strategy that relies on the market's disagreement with BS (for
  example, earnings-related vol term-structure crush) has to model
  the disagreement itself, because the synthetic chain does not.
* **Single risk-free rate.** Phase 2 uses a hard-coded
  `DEFAULT_RISK_FREE_RATE = 0.045`. Phase 3 will source it from FRED
  (3-month T-bill yield) per as-of date.

## When it is accurate

* Signal-logic validation — does the strategy compute the right
  strike / expiry selection given a chain in the expected shape?
* Systematic strategy plausibility — does the P&L curve roughly
  track the academic backtest in sign and order of magnitude?
* Regression harnesses — the determinism contract makes synthetic
  chains stable across CI runs and across fresh clones.

## When it is inaccurate

* Absolute return forecasting for any options strategy.
* Skew-dependent structures (put-skew premium, skew reversal,
  dispersion, risk-reversals).
* Microstructure-sensitive structures (bid-ask capture, liquidity
  timing, block-trade behaviour).
* Earnings-vol strategies without a layered earnings-multiplier
  adjustment.

`docs/deviations.md` lists this caveat at the strategy-family level.

## Upgrade path

Swap `FeedRegistry.get("synthetic-options")` to
`FeedRegistry.get("polygon")` once the Phase 3 Polygon integration
ships. No strategy code changes, because strategies depend only on
the `DataFeedProtocol` interface and the `OptionChain` schema —
both of which the synthetic and real feeds implement identically.

## See also

* `docs/adr/005-synthetic-options-chain.md` — decision record.
* `docs/feeds/polygon.md` — the Phase 3 upgrade target.
* `docs/deviations.md` — synthetic-chain limitations called out at
  the strategy level.
