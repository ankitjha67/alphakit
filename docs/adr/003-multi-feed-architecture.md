# ADR-003: Multi-feed data architecture

- **Status**: Accepted
- **Date**: 2026-04-17
- **Deciders**: Project maintainers
- **Supersedes**: ADR-001 (carry-family data gap)

## Context

Phase 2 introduces four strategy families (rates, commodity, options,
macro/GTAA) that fundamentally require data feeds beyond adjusted-close
price panels. Rates strategies need Treasury yield curves from FRED.
Commodity strategies need futures term structures, CFTC positioning,
and EIA inventory data. Options strategies need option chains with
strikes, expiries, IV, and greeks. Macro/GTAA strategies need economic
indicators.

Phase 1 ADR-001 deferred the multi-feed extension to "Phase 4 when
options chains, order books, and alt-data collectively justify a
general-purpose protocol extension." Phase 2 brings that justification
forward because three of its four families need non-price feeds.

The groundwork is already in place. Phase 1 shipped canonical data
schemas (`Bar`, `OptionChain`, `OrderBook`, `Tick`) in
`alphakit.core.data`. `DataFeedProtocol` exists but has only a single
`fetch()` method returning `pd.DataFrame` — suitable for price panels,
insufficient for `OptionChain` snapshots.

## Options considered

### A) Extend `DataFeedProtocol` with `fetch_chain`

Add a second method to the protocol:

```python
def fetch_chain(self, underlying: str, as_of: datetime) -> OptionChain: ...
```

Feeds that don't provide options (FRED, basic yfinance) inherit a
default implementation that raises `NotImplementedError`. Feeds that
do (Polygon, synthetic) override it properly. Strategies that need
chains call `feed.fetch_chain(...)`.

**Pros**: single protocol, single registry, single import path.
Strategies can be feed-agnostic — switch from synthetic to Polygon by
changing the registry lookup. Matches the `DataFeedProtocol`'s
existing design intent.

**Cons**: violates interface-segregation slightly — feeds advertise a
method they don't support. Mitigated by the default-raising body:
non-options feeds don't have to hand-roll a `NotImplementedError`.

### B) Separate `OptionFeedProtocol`

A second `runtime_checkable` protocol for options-only feeds.
`OptionFeedProtocol` has `fetch_chain`; `DataFeedProtocol` has
`fetch`.

**Pros**: cleaner ISP adherence. Each protocol is minimal.

**Cons**: strategies need to know which protocol to use.
`FeedRegistry` becomes multi-typed. Crossover feeds (a hypothetical
all-asset-class provider) must implement two protocols.

### C) Unified `fetch` with overload

Single `fetch` method that returns `pd.DataFrame` or `OptionChain`
depending on arguments.

**Pros**: one method to call.

**Cons**: the type system fights it. Return type isn't stable.
Strategy code becomes conditional. Reject.

## Decision

**Option A**. Extend `DataFeedProtocol` with `fetch_chain` and a
default `NotImplementedError` body. Introduce a `FeedRegistry` so
strategies look feeds up by name rather than importing them directly.

## Consequences

1. `DataFeedProtocol` gets a second method. Existing adapters
   (yfinance) stay compliant without code changes — they inherit the
   default body.
2. Phase 2 adapters (FRED, EIA, CFTC, yfinance-futures,
   synthetic-options, Polygon placeholder) implement `fetch`,
   `fetch_chain`, or both as appropriate.
3. Strategy code that needs chains documents it in the strategy's
   `paper.md`.
4. `FeedRegistry` (Session 2A) provides name-based lookup.
5. ADR-001 is superseded — its "Phase 4 deferral" rationale is
   overtaken by Phase 2's needs. Carry-family proxies from Phase 1
   remain as-is (ADR-002 proxy-suffix convention still applies);
   Phase 2 does not retroactively upgrade them.

## Related decisions

- ADR-001 (superseded): carry-family data gap handled via
  price-derived proxies. Deferral rationale is now obsolete.
- ADR-002 (still applies): `_proxy` suffix convention for
  severe-deviation strategies.
- ADR-006: feed caching strategy (companion to this ADR).
- ADR-007: rate-limit coordination (companion to this ADR).
