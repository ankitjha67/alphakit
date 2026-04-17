# ADR-006: Feed caching strategy

- **Status**: Accepted
- **Date**: 2026-04-17
- **Deciders**: Project maintainers

## Context

Every Phase 2 integration test that hits a real feed (FRED,
yfinance-futures, EIA, CFTC) has three failure modes: rate-limited by
the provider, network-dependent in CI, slow. Without caching, running
the full benchmark suite on 125 strategies against real feeds would
take hours and likely trip rate limits multiple times.

## Options considered

### A) Disk-backed parquet cache with TTL

Cache key: `sha256(feed_name, symbols, start, end, frequency)`.
Location: `~/.alphakit/cache/` by default, overridable via
`ALPHAKIT_CACHE_DIR`. TTL is supplied per call so heterogeneous feed
cadences (daily bars, weekly COT, annual fundamentals) share one
directory without collision.

### B) In-memory LRU cache

Fast but doesn't persist across Python sessions. Doesn't help CI runs
that start fresh.

### C) No caching

Rely on feeds' own caching (yfinance has some). Doesn't work for
FRED, CFTC, EIA which have no built-in cache.

## Decision

**Option A**.

## Consequences

1. `alphakit.data.cache` ships a `FeedCache` class and a
   `@cached_feed(ttl_seconds=N)` decorator that adapters apply to
   `fetch` / `fetch_chain`.
2. The cache is optional. Setting `ALPHAKIT_CACHE_DIR=/dev/null` (or
   `NUL` on Windows) disables it: every call hits the live feed.
   These two strings are *sentinels*, not paths — they never get
   `mkdir`'d.
3. Any other unwritable path is an error, not a sentinel.
   `FeedCache.put` raises `FeedError`; `FeedCache.get` warns once per
   path and returns `None` (a miss) so read breakage degrades
   gracefully.
4. Corrupt parquet files are removed on read and the call falls
   through to a live fetch. Next successful write repopulates.
5. CI can warm the cache as a GitHub Actions cache step, drastically
   reducing subsequent test runtime.
6. `docs/feeds/caching.md` (Session 2B) will document the model,
   key layout, and debugging steps.

## Related decisions

- ADR-003: multi-feed data architecture (the infrastructure caching
  plugs into).
- ADR-007: rate-limit coordination (the sibling defence against
  provider throttling).
