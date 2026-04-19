# ADR-004: Polygon placeholder adapter pattern

**Status:** Accepted.
**Date:** Phase 2 Session 2C (2026-04-19).
**Deciders:** Project maintainers.

## Context

Polygon.io is the primary paid data feed AlphaKit will support for
options chains with greeks, IV, and institutional-grade data
quality. Phase 2 commits to free/open-source feeds as the primary
layer, with paid feeds as an optional upgrade. But Phase 2 also
needs options strategies to ship with the Polygon integration shape
ready, so that Phase 3 or later can drop in real Polygon calls
without touching any strategy code.

The question is how to ship a "placeholder" adapter that exposes the
right interface without making real API calls in Phase 2.

## Options considered

**Option A — Full stub.** Adapter class with the right name,
`fetch_chain` method, raises `PolygonNotConfiguredError` with a clear
message pointing to documentation. No real API logic. Strategies test
against this stub and also against synthetic-chain fallback.

**Option B — Minimal real implementation.** Ship a minimal real
Polygon adapter that works if `POLYGON_API_KEY` is set. Tests that
exercise it are skipped in CI without the key. This is what most
open-source libraries do.

**Option C — No adapter at all.** Don't ship any Polygon file in
Phase 2. Add it in Phase 3.

## Decision

Option A (full stub).

## Rationale

Option B sounds cleaner but requires real-API testing discipline that
is premature for Phase 2. If we ship a real Polygon adapter now, we
have to maintain it now — keeping it up to date with Polygon's API
changes, handling their rate limits, debugging their edge cases.
That's a commitment we don't want to take on until we're ready to
make Polygon a first-class feed (Phase 3 at earliest).

Option C leaves a visible gap — anyone reading the codebase wonders
"why isn't there an adapter for X?" Option A answers the question:
"there is, it's a placeholder, here's the path to enabling it."

## Consequences

`packages/alphakit-data/alphakit/data/options/polygon_adapter.py`
ships as a stub. It implements `DataFeedProtocol` with `name="polygon"`.

* `fetch` raises `NotImplementedError` unconditionally. (Polygon does
  price data too, but Phase 2 uses `yfinance` / `yfinance-futures`
  for equities and futures; Polygon is only of interest for chains.)
* `fetch_chain` checks the `POLYGON_API_KEY` environment variable:
    * **Missing**: raises `PolygonNotConfiguredError` with a clear
      message that points at `docs/feeds/polygon.md` and tells the
      caller to use `synthetic-options` instead.
    * **Present**: raises `NotImplementedError` pointing at this ADR
      and noting that real integration is scoped for Phase 3.

The adapter registers with `FeedRegistry` under `name="polygon"` at
import time. Both error paths are covered by direct tests in
`tests/test_polygon_adapter.py`; the shared contract test verifies
the adapter's harness entry (`implements_fetch=False`,
`implements_chain=False`, `chain_error_type=PolygonNotConfiguredError`).

A companion `docs/feeds/polygon.md` explains what Polygon provides,
the current placeholder status, what Phase 3 will add, and how to
enable it when the real integration ships.

## See also

* `docs/feeds/polygon.md` — user-facing documentation.
* `docs/adr/005-synthetic-options-chain.md` — the Phase 2 substitute.
* `packages/alphakit-data/alphakit/data/options/polygon_adapter.py` — implementation.
