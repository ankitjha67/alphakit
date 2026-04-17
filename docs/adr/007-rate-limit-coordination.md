# ADR-007: Rate-limit coordination

- **Status**: Accepted
- **Date**: 2026-04-17
- **Deciders**: Project maintainers

## Context

Free feeds have quotas. FRED allows 120 requests/minute with an API
key (free, unlimited series). yfinance has undocumented rate limits
that vary by endpoint. CFTC COT is a weekly ZIP download with no
formal limit but it should not be abused. EIA permits 5000 requests
per hour with a free key.

If a benchmark runner parallelises 50 strategies that all need FRED
yield curves, each triggering its own FRED call without coordination,
the minute's quota burns in seconds.

## Options considered

### A) Per-feed semaphore (token bucket)

Each feed adapter calls a module-level `ratelimit.acquire("fred")`
before every outbound HTTP request. The module keeps a token bucket
per feed; capacity and refill rate reflect the feed's quota.
Callers serialise transparently — no adapter has to understand
concurrency.

### B) Request-queue with worker pool

More sophisticated (async, back-pressure) but overkill for Phase 2
where backtests run single-process.

### C) No coordination

Rely on caching (ADR-006) to reduce real calls. Works for repeated
backtests but fails on the first cold run and on any benchmark that
asks for a broader symbol set than what the cache holds.

## Decision

**Option A**, combined with the aggressive caching from ADR-006.

## Consequences

1. `alphakit.data.rate_limit` ships a process-global dict of
   `_TokenBucket` instances keyed by feed name, plus an
   `acquire(feed_name)` function.
2. Limits are configurable via
   `ALPHAKIT_RATELIMIT_{FEED}_PER_MINUTE` env vars (e.g.
   `ALPHAKIT_RATELIMIT_FRED_PER_MINUTE=60`). Defaults: FRED 120,
   yfinance 60, EIA 80, CFTC 10.
3. CI can set conservative low limits so it never hammers a provider
   even if a test forgets to mock HTTP.
4. Tests that mock HTTP don't hit the limiter — acquisition is cheap
   when the bucket starts full.
5. **Single-process only for Phase 2.** Multi-process and distributed
   coordination (live trading, cloud benchmark runners) require
   shared-memory or external coordination; that work is deferred to
   Phase 5 and will revisit this ADR then.
6. `docs/feeds/rate-limits.md` (Session 2B) will document the
   defaults per feed and the relevant env vars.

## Related decisions

- ADR-003: multi-feed data architecture.
- ADR-006: feed caching strategy (the sibling defence against
  provider throttling).
