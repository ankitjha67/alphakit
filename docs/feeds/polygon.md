# Polygon.io

**Status:** Placeholder (Phase 2) — real integration planned for Phase 3.
**Registered name:** `polygon`
**API key:** `POLYGON_API_KEY` (required for the Phase 3 wiring, not
usable in Phase 2).

## What Polygon provides

Polygon.io serves real-time and historical options chains with
greeks, implied vol, volume, and open interest, alongside equities
and futures tick data. It is the primary paid feed AlphaKit plans to
support for institutional-grade options data.

## Why a placeholder in Phase 2

ADR-004 documents the decision in full. In short: shipping a real
Polygon client now would lock us into maintaining it — keeping up
with API changes, handling their rate limits, debugging edge cases
— before we have a Phase 3 milestone to justify the investment. An
explicit stub answers the "where is Polygon?" question, advertises
the upgrade path, and keeps the `fetch_chain` interface consistent
across the registry.

## Behaviour today

```python
from alphakit.data.registry import FeedRegistry

feed = FeedRegistry.get("polygon")

feed.fetch(["SPY"], start, end)
# → NotImplementedError (placeholder; use yfinance for equities)

feed.fetch_chain("SPY", as_of)
# Without POLYGON_API_KEY:
# → PolygonNotConfiguredError
#   "POLYGON_API_KEY env var not set. Polygon is a placeholder in
#    Phase 2 — use 'synthetic-options' feed instead."
#
# With POLYGON_API_KEY set:
# → NotImplementedError
#   "Polygon adapter placeholder. Real integration scoped for Phase 3."
```

Both error paths are covered by tests in
`packages/alphakit-data/tests/test_polygon_adapter.py`.

## Using options data in Phase 2

Use the `synthetic-options` feed. All 20 Phase 2 options strategies
default to it; see `docs/feeds/synthetic-options.md` for methodology
and limitations.

```python
chain = FeedRegistry.get("synthetic-options").fetch_chain("SPY", as_of)
```

## Phase 3 upgrade path

When the real Polygon integration ships:

1. Install the Polygon client dependency (via a new optional-deps
   group on `alphakit-data`).
2. Set `POLYGON_API_KEY` in your environment.
3. Flip the configured feed name from `"synthetic-options"` to
   `"polygon"` at the `FeedRegistry.get(...)` call site. Strategies
   depend only on the `DataFeedProtocol` interface and the
   `OptionChain` schema — both feeds implement them identically, so
   no strategy logic or schema changes are required.
4. Re-run the benchmark runner to regenerate
   `benchmark_results_real.json` against live Polygon chains.

Strategies remain feed-agnostic throughout. The migration is a
registry-key rename plus an environment variable — no schema change,
no strategy rewrite.

## See also

* `docs/adr/004-polygon-placeholder-adapter.md` — decision record.
* `docs/feeds/synthetic-options.md` — the Phase 2 options substitute.
