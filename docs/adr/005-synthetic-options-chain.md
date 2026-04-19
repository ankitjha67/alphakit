# ADR-005: Synthetic options chain generator for Phase 2

**Status:** Accepted.
**Date:** Phase 2 Session 2C (2026-04-19).
**Deciders:** Project maintainers.

## Context

The Phase 2 options family (20 strategies) needs an `OptionChain`
source that works without paid feeds. Polygon is stubbed (ADR-004).
Free alternatives exist (yfinance has some options data, CBOE has
free end-of-day files) but are inconsistent, incomplete, and
unreliable for systematic backtests.

The cleanest Phase 2 solution is to generate synthetic `OptionChain`
snapshots from historical underlying prices using Black-Scholes
pricing with an implied-volatility estimator derived from realized
volatility.

## Options considered

**Option A — Synthetic chains via Black-Scholes + realized-vol IV
proxy.** For each `(underlying, as_of)` pair, compute a realized-vol
surface (trailing 30-, 60-, 90-day) and use it as the IV for
Black-Scholes pricing. Generate quotes across a reasonable strike
grid (0.80× to 1.20× spot, 5 % increments) and expiry grid (weekly,
monthly, quarterly). Ship as
`alphakit-data/alphakit/data/options/synthetic.py`.

**Option B — yfinance options data.** Use `yf.Ticker.option_chain`.
Free, but only available for current/recent dates, no historical
chains, inconsistent coverage, and yfinance frequently rate-limits or
changes the API shape.

**Option C — CBOE end-of-day files.** Free download of historical
options data. Requires manual curation, large file sizes, and has
licensing ambiguity.

**Option D — Require Polygon.** Don't ship Phase 2 options family at
all until Phase 3's real Polygon integration.

## Decision

Option A (synthetic chains).

## Rationale

Systematic options strategies operate on strike relationships,
expiry term structure, IV skew, and basic greek exposure. Most of
these can be back-tested against synthetic chains produced by a
reasonable pricing model. The results are not production-accurate —
they're approximations — but they demonstrate strategy-logic
correctness and produce benchmark numbers comparable to Phase 1's
other synthetic-data strategies. This matches the honesty framework
established by ADR-002: synthetic data is acceptable for
signal-logic testing, provided it is documented prominently.

Users who want production-accurate backtests can wire up Polygon in a
future phase and re-run the benchmark runner. The strategy code is
feed-agnostic, so no strategy changes are needed.

## Consequences

`packages/alphakit-data/alphakit/data/options/synthetic.py` ships a
`SyntheticOptionsFeed` class implementing `DataFeedProtocol`
(`name="synthetic-options"`). Its `fetch_chain` method:

1. Fetches ≈ 252 trading bars of the underlying's closing prices
   from an injectable *underlying feed* (defaulting to `yfinance` via
   a lazy registry lookup in the `underlying_feed` property).
2. Computes trailing 30-/60-/90-day realized vol from log returns
   and selects one window per expiry based on days-to-expiry.
3. Builds a 9-point strike grid (`{0.80, …, 1.20} × spot`).
4. Builds a 11-14-point expiry grid (weekly + monthly + quarterly
   third-Fridays with date-level dedup).
5. Prices every `(strike, expiry, right)` combination via
   Black-Scholes and populates the `OptionQuote` with BS greeks.

The feed is chain-only: `fetch` raises `NotImplementedError`. The
feed registers with `FeedRegistry` at import time. All Phase 2
options strategies default to it in their integration tests.

Error paths:

* Fewer than 252 non-null underlying bars → `ValueError` naming the
  minimum.
* Non-finite or non-positive prices (post-`dropna`) → `ValueError`.

The shared contract test
(`tests/test_adapter_contract.py::test_adapter_fetch_chain_is_deterministic`)
asserts that two back-to-back calls with the same inputs return
byte-identical chains — preventing a silent backtest-reproducibility
regression.

`docs/feeds/synthetic-options.md` documents methodology, limitations
(flat vol, no bid-ask spread, no volume/OI, BS-only greeks), and the
Phase 3 upgrade path. `docs/deviations.md` gets a dedicated
"Synthetic Options Chains (Phase 2)" section. All 20 Phase 2 options
strategies will include a "Data Fidelity" note in their `paper.md`
explaining the synthetic-chain backtest caveat.

## See also

* `docs/feeds/synthetic-options.md` — user-facing documentation.
* `docs/adr/004-polygon-placeholder-adapter.md` — the Phase 3 upgrade target.
* `docs/deviations.md` — the synthetic-chain caveat at the strategy level.
* `packages/alphakit-data/alphakit/data/options/synthetic.py` — implementation.
* `packages/alphakit-data/alphakit/data/options/bs.py` — Black-Scholes helpers.
