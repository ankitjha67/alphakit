# alphakit Phase 2 Master Plan — v0.2.0

**Scope:** 65 new strategies across rates, commodity, options, and macro/GTAA families. Multi-feed data architecture. Real feed adapters for all free-and-open-source sources. Polygon adapter placeholder with graceful fallback. Phase 2 ships as **v0.2.0**, marked pre-release (silent build — no announcement until v1.0).

**Target duration:** 6–8 weeks across 8 Claude Code sessions.

**Baseline:** main @ `0fbc23a` (v0.1.1 tag), 60 strategies live, 928 tests passing, verify-install.yml CI green.

**Success criteria:** 125 total strategies live; 4 new free feed adapters functional; Polygon placeholder with upgrade path documented; real-feed-tested rates and commodity strategies; synthetic-chain options strategies; v0.2.0 tagged and verify-install green on the tag.

---

## Section 0 — Phase 1 Retrospective

Before planning Phase 2, an honest accounting of what shipped, what broke, and what changed as a result. This retrospective lives in the plan deliberately — Phase 2 sessions reference it to avoid repeating Phase 1 mistakes.

### What shipped successfully

60 paper-cited strategies across five families, each with the full per-strategy contract: strategy.py, config.yaml, paper.md with DOI, known_failures.md, README.md, tests/test_unit.py, tests/test_integration.py, benchmark_results.json. Nine-package uv workspace structure with alphakit-core, alphakit-bridges, alphakit-data, alphakit-bench, and five alphakit-strategies-{trend,meanrev,carry,value,volatility} sub-packages. Core infrastructure including DataFeedProtocol, StrategyProtocol, BacktestEngineProtocol, and BacktestResult with full @property accessor layer. Canonical data schemas (Bar, Tick, OptionChain, OrderBook) as immutable pydantic v2 models with strict validation. Instrument taxonomy covering equity, future, option, fx, and crypto. Two engine bridges (vectorbt as primary, backtrader as secondary). verify-install.yml CI matrix covering Python 3.10/3.11/3.12 × ubuntu-latest/macos-latest. benchmark.yml weekly scheduled runner.

### What broke in production and how we caught it

**v0.1.0 packaging disaster.** Root meta-package declared sub-packages as bare pip dependencies that couldn't resolve without PyPI. Every first-user install failed immediately with "Could not find a version that satisfies the requirement alphakit-bench". Caught within hours of release by local Windows PowerShell verification against the released tag. Result: v0.1.0 yanked, v0.1.1 shipped as install-path hotfix.

**alphakit-bench cross-package deps.** Bench package listed alphakit-strategies-carry, alphakit-strategies-trend, etc. as pip dependencies — same resolution failure as the root package. Fixed in the same v0.1.1 hotfix by removing those declarations (strategies are discovered at runtime, not installed as deps).

**README drift from code.** v0.1.0 README quickstart used `result.sharpe` and `result.max_dd` as attribute access, but BacktestResult's actual fields were `equity_curve`, `returns`, `weights`, `metrics`, `meta` — the Sharpe value lived inside `result.metrics["sharpe"]`. The quickstart copy-paste crashed on the first print statement. Caught by the same local verification.

**pip git-clone cache staleness.** During post-yank verification, pip kept resolving `git+...@main` to an older commit hash (e308529) even after main had advanced. The `main` → commit mapping was cached locally and stale. Resolution: aggressive cache busting with `pip cache purge` plus `--no-cache-dir` flag plus pinning to full commit SHA when in doubt.

### Patterns that worked

**Per-strategy contract enforcement.** Non-negotiable requirement that every strategy ship with paper.md (DOI citation), known_failures.md (honest limitations), config.yaml, unit + integration tests, and benchmark_results.json. No exceptions. This is the single most important discipline decision in the project. It forces honest accounting at the per-strategy level, which compounds across 60 strategies into genuine quality.

**Stacked feature branches per family.** Each family (trend → meanrev → carry → value → volatility) built on its own branch, merged into main only when the family was complete and tested. Kept main green throughout the 5-session build.

**verify-install.yml from day one.** Fresh-container install verification caught the v0.1.0 packaging bug before external users hit it. CI runs on every tag push, so every release is verified in a clean environment by default. This is permanent infrastructure worth defending.

**test_readme_api.py executable documentation.** Added in the v0.1.1 hotfix. Any public API claim in the README is now asserted in CI. Prevents future docs-vs-code drift automatically. Extend this pattern to Phase 2.

**ADR discipline.** Two ADRs (ADR-001 carry data gap, ADR-002 proxy suffix convention) documented in-repo at the moment of decision. When Phase 2 reconsiders ADR-001, the original context is preserved and the supersede path is clean.

### Patterns that didn't work

**Architecture-from-memory.** At multiple points during Phase 1 builds and especially at the Phase 2 planning stage, I (Claude, producing the plan) assumed architectural state that wasn't actually in the repo. DataFeedProtocol already existed; I was about to plan building it from scratch. Option chain schemas already existed; I assumed they needed designing. **Fix for Phase 2: every session starts with a grep/tree of the relevant part of the repo before writing any new code.** This is built into every session prompt.

**Proxy suffix proliferation risk.** Phase 1 ended with 7 `_proxy` suffixed strategies (piotroski_fscore_proxy, altman_zscore_proxy, 5 options strategies). That's tolerable for a Phase 1 build under ADR-001. But another 20+ proxy suffixes in Phase 2 would start to look like "proxies all the way down" and undermine the paper-grade positioning. Mitigation: Phase 2 strategies only ship with a `_proxy` suffix if the equivalent real-feed version is explicitly scoped for a named future phase. Otherwise the strategy waits.

**Context loss across sessions.** Phase 1 had multiple cases where a Claude Code session "completed" but didn't actually push all the way to origin/main. Fix commits landed on feature branches but weren't promoted. The v0.1.1 pre-mortem showed this clearly: the same commit hash appeared in verification run after verification run because pushes weren't happening. **Fix for Phase 2: every session handoff prompt requires explicit `git log origin/main -1` output in the session report to confirm push success, and the session is not marked done until origin/main shows the new commit hash.**

---

## Section 1 — Phase 2 Mission and Non-Goals

### Mission

Ship 65 new strategies across four new families (rates, commodity, options, macro/GTAA) backed by a real multi-feed data architecture. Free/open-source feeds are primary and fully implemented. Paid-feed adapters exist as placeholders with graceful fallback logic, ready for drop-in when the user chooses to wire them up.

At the end of Phase 2, someone clones alphakit, sets zero API keys, runs the quickstart, and sees a rates strategy backtested on real FRED treasury yields. No paid subscriptions required. No proxies where real data is freely available.

### In scope

65 new strategies: 15 rates, 15 commodity, 20 options, 15 macro/GTAA. Full per-strategy contract for each (paper.md, known_failures.md, tests, benchmark_results.json).

FeedRegistry with name-based adapter lookup. Disk-backed parquet caching with TTL. Rate-limit coordinator. Offline mode (ALPHAKIT_OFFLINE=1).

Four new free-feed adapters: FRED (treasury yields, CPI, Fed funds, 800K series), EIA (energy inventory), CFTC COT (weekly positioning), yfinance-futures-extension (front-month + continuous series for commodity futures).

Polygon placeholder adapter: proper interface matching DataFeedProtocol.fetch_chain, raises PolygonNotConfiguredError with clear message if POLYGON_API_KEY missing. No real API calls in Phase 2 — adapter shell ready for Phase 3 wire-up.

Synthetic options chain generator: Black-Scholes pricer with historical-vol-based IV estimator. Used as the default chain source for Phase 2 options strategies. OptionChain-typed output matches real feed output byte-for-byte, so strategies work identically against synthetic and real feeds.

DataFeedProtocol extension: add `fetch_chain(underlying, as_of) -> OptionChain` method, default-raising for feeds that don't support it.

ADR-003 (multi-feed architecture, supersedes ADR-001), ADR-004 (Polygon placeholder pattern), ADR-005 (synthetic options chain approach), ADR-006 (feed caching strategy), ADR-007 (rate-limit coordination).

test_readme_api.py pattern extended to cover Phase 2 public APIs.

v0.2.0 release tagged as pre-release (silent build continues).

### Out of scope

Real Polygon integration (Phase 3 or v1.0 polish). Phase 2 ships the adapter shell; the actual HTTP calls come later.

Retroactive upgrade of Phase 1 proxy strategies. The 7 _proxy strategies stay _proxy until a later phase explicitly scopes their upgrade. Phase 2 does not modify Phase 1 carry strategies.

C# LEAN bridge (Phase 3).

Alt-data integration — sentiment, news, satellite, etc. (Phase 4).

Portfolio construction overlays (risk parity weighting, Kelly sizing, HRP clustering). Some Phase 2 strategies use these as ingredients, but the portfolio-construction framework itself is Phase 4.

Live-trading scaffolding (Phase 5–6).

PyPI publishing. Silent build continues. Install remains via `git+https://github.com/...@v0.2.0`.

Any public announcement. LinkedIn, HN, Reddit, Twitter, Product Hunt all off-limits until v1.0 ships. Adjacent-topic posts (credit risk, Basel III, open-source discipline) remain allowed as long as they don't mention alphakit by name.

---

## Section 2 — Architecture Decisions (5 ADRs)

All five ADRs are drafted below in final form, ready to commit to `docs/adr/` in Session 2A. They are reproduced here in full so the plan stands alone as a self-contained specification.

### ADR-003: Multi-feed data architecture

**Status:** Proposed (to be Accepted in Session 2A).  
**Date:** Phase 2 Session 2A.  
**Deciders:** Project maintainers.  
**Supersedes:** ADR-001 (carry-family data gap).

**Context.** Phase 2 introduces four strategy families (rates, commodity, options, macro/GTAA) that fundamentally require data feeds beyond adjusted-close price panels. Rates strategies need Treasury yield curves from FRED. Commodity strategies need futures term structures, CFTC positioning, and EIA inventory data. Options strategies need option chains with strikes, expiries, IV, and greeks. Macro/GTAA strategies need economic indicators.

Phase 1 ADR-001 deferred the multi-feed extension to "Phase 4 when options chains, order books, and alt-data collectively justify a general-purpose protocol extension." Phase 2 brings that justification forward because three of its four families need non-price feeds.

The groundwork is already in place. Phase 1 shipped canonical data schemas (Bar, OptionChain, OrderBook, Tick) in alphakit-core.data. DataFeedProtocol exists but has only a single `fetch()` method returning `pd.DataFrame` — suitable for price panels, insufficient for OptionChain snapshots.

**Options considered.**

**Option A — Extend DataFeedProtocol with fetch_chain.** Add a second method to the protocol:

```python
def fetch_chain(self, underlying: str, as_of: datetime) -> OptionChain: ...
```

Feeds that don't provide options (FRED, basic yfinance) implement it to raise NotImplementedError. Feeds that do (Polygon, synthetic) implement it properly. Strategies that need chains call `feed.fetch_chain(...)`.

Pros: single protocol, single registry, single import path. Strategies can be feed-agnostic — switch from synthetic to Polygon by changing the registry lookup. Matches the DataFeedProtocol's existing design intent.

Cons: violates interface-segregation slightly — feeds advertise a method they don't support. Mitigation: runtime hasattr-check or a FeedCapability enum.

**Option B — Separate OptionFeedProtocol.** Second runtime-checkable protocol for options-only feeds. OptionFeedProtocol has fetch_chain; DataFeedProtocol has fetch.

Pros: cleaner ISP adherence. Each protocol is minimal.

Cons: strategies need to know which protocol to use. FeedRegistry becomes multi-typed. Crossover feeds (e.g., a hypothetical all-asset-class provider) must implement two protocols.

**Option C — Unified fetch with overload.** Single fetch method that returns pd.DataFrame or OptionChain depending on arguments.

Pros: one method to call.

Cons: type system fights it. Return type isn't stable. Strategy code becomes conditional. Reject.

**Decision.** Option A.

**Consequences.** DataFeedProtocol gets a second method. Existing adapters (yfinance) get a default NotImplementedError implementation for fetch_chain. Phase 2 adapters (FRED, EIA, CFTC, yfinance-futures, synthetic-options, Polygon-placeholder) implement fetch, fetch_chain, or both as appropriate. Strategy code that needs chains documents it in the strategy's paper.md. A FeedRegistry (Session 2A) provides name-based lookup. ADR-001 is superseded — its "Phase 4 deferral" rationale is overtaken by Phase 2's needs. Carry-family proxies from Phase 1 remain as-is (ADR-002 proxy suffix convention still applies); Phase 2 does not retroactively upgrade them.

---

### ADR-004: Polygon placeholder adapter pattern

**Status:** Proposed.  
**Date:** Phase 2 Session 2C.  
**Deciders:** Project maintainers.

**Context.** Polygon.io is the primary paid data feed alphakit will support for options chains with greeks, IV, and institutional-grade data quality. Phase 2 commits to free/open-source feeds as the primary layer, with paid feeds as an optional upgrade. But Phase 2 also needs options strategies to ship with the Polygon integration shape ready, so that Phase 3 or later can drop in real Polygon calls without touching any strategy code.

The question is how to ship a "placeholder" adapter that exposes the right interface without making real API calls in Phase 2.

**Options considered.**

**Option A — Full stub.** Adapter class with the right name, `fetch_chain` method, raises PolygonNotConfiguredError with a clear message pointing to documentation. No real API logic. Strategies test against this stub and also against synthetic-chain fallback.

**Option B — Minimal real implementation.** Ship a minimal real Polygon adapter that works if POLYGON_API_KEY is set. Tests that exercise it are skipped in CI without the key. This is what most open-source libraries do.

**Option C — No adapter at all.** Don't ship any Polygon file in Phase 2. Add it in Phase 3.

**Decision.** Option A (full stub).

**Rationale.** Option B sounds cleaner but requires real API testing discipline that's premature for Phase 2. If we ship a real Polygon adapter now, we have to maintain it now — keeping it up to date with Polygon's API changes, handling their rate limits, debugging their edge cases. That's a commitment we don't want to take on until we're ready to make Polygon a first-class feed (Phase 3 at earliest).

Option C leaves a visible gap — anyone reading the codebase wonders "why isn't there an adapter for X?" Option A answers the question: "there is, it's a placeholder, here's the path to enabling it."

**Consequences.** packages/alphakit-data/alphakit/data/options/polygon_adapter.py ships as a stub. It implements DataFeedProtocol with name="polygon". fetch() raises NotImplementedError (Polygon does price data too, but we're only using it for chains in Phase 2). fetch_chain() checks for POLYGON_API_KEY env var; if missing, raises PolygonNotConfiguredError with a clear message including a link to docs/feeds/polygon.md explaining how to enable it; if present, raises NotImplementedError pointing to the Phase 3 roadmap. The adapter is registered with FeedRegistry under the name "polygon". Tests verify the error paths. No real HTTP calls occur in Phase 2.

A companion docs/feeds/polygon.md explains: what Polygon provides, current status (placeholder), what Phase 3 will add, how to enable it when the real integration ships.

---

### ADR-005: Synthetic options chain generator for Phase 2

**Status:** Proposed.  
**Date:** Phase 2 Session 2C.  
**Deciders:** Project maintainers.

**Context.** Phase 2 options family (20 strategies) needs an OptionChain source that works without paid feeds. Polygon is stubbed (ADR-004). Free alternatives exist (yfinance has some options data, CBOE has free end-of-day files) but are inconsistent, incomplete, and unreliable for systematic backtests.

The cleanest Phase 2 solution is to generate synthetic OptionChain snapshots from historical underlying prices using Black-Scholes pricing with an implied-volatility estimator derived from realized volatility.

**Options considered.**

**Option A — Synthetic chains via Black-Scholes + realized-vol IV proxy.** For each (underlying, as_of) pair, compute a realized-vol surface (trailing 30-day, 60-day, 90-day) and use it as the IV for Black-Scholes pricing. Generate quotes across a reasonable strike grid (0.8x to 1.2x spot, 5% increments) and expiry grid (weekly, monthly, quarterly, annual). Ship as alphakit-data/options/synthetic.py.

**Option B — yfinance options data.** Use yf.Ticker.option_chain(date). Free, but only available for current/recent dates, no historical chains, inconsistent coverage, and yfinance frequently rate-limits or changes the API.

**Option C — CBOE end-of-day files.** Free download of historical options data. Requires manual curation, large file sizes, licensing ambiguity.

**Option D — Require Polygon.** Don't ship Phase 2 options family at all until Phase 3's real Polygon integration.

**Decision.** Option A (synthetic chains).

**Rationale.** Systematic options strategies operate on strike relationships, expiry term structure, IV skew, and basic greek exposure. All of these can be backtested against synthetic chains produced by a reasonable pricing model. The backtest results are not production-accurate — they're approximations — but they demonstrate strategy logic correctness and produce benchmark numbers comparable to Phase 1's other synthetic-data strategies. This matches the honesty framework established by ADR-002: synthetic data is acceptable for signal-logic testing, provided it's documented prominently.

Users who want production-accurate backtests can wire up Polygon in a future phase and re-run the benchmark runner. The strategy code is feed-agnostic, so no strategy changes are needed.

**Consequences.** packages/alphakit-data/alphakit/data/options/synthetic.py ships with a SyntheticOptionsFeed class implementing DataFeedProtocol. Its fetch_chain method computes Black-Scholes prices across a strike/expiry grid with realized-vol-based IV. The feed is registered under the name "synthetic-options". All Phase 2 options strategies default to this feed in their integration tests. The feed produces OptionChain-typed output identical in shape to what a real Polygon adapter would produce. docs/feeds/synthetic-options.md documents the approach, its limitations (no real IV skew, no real volume/OI, no real greeks — only BS-computed), and the Phase 3 upgrade path. docs/deviations.md gets a "Synthetic Options Chains" section. All 20 options strategies' paper.md files include a "Data Fidelity" note explaining the synthetic-chain backtest caveat.

---

### ADR-006: Feed caching strategy

**Status:** Proposed.  
**Date:** Phase 2 Session 2A.  
**Deciders:** Project maintainers.

**Context.** Every Phase 2 integration test that hits a real feed (FRED, yfinance-futures, EIA, CFTC) has three failure modes: rate-limited by the provider, network-dependent in CI, slow. Without caching, running the full benchmark suite on 125 strategies against real feeds would take hours and likely trip rate limits multiple times.

**Options considered.**

**Option A — Disk-backed parquet cache with TTL.** Cache key: `hash(feed_name, symbols, start, end, frequency)`. Cache location: `~/.alphakit/cache/` (or `ALPHAKIT_CACHE_DIR` env var). TTL per feed type: daily bars cached 24 hours; weekly positioning data cached 7 days; annual historical data cached 90 days. Force-refresh via `ALPHAKIT_CACHE_REFRESH=1`. Cache hits are logged at DEBUG level.

**Option B — In-memory LRU cache.** Fast but doesn't persist across Python sessions. Doesn't help CI runs that start fresh.

**Option C — No caching.** Rely on feeds' own caching (yfinance has some). Doesn't work for FRED, CFTC, EIA which have no built-in cache.

**Decision.** Option A.

**Consequences.** alphakit-data gets a cache.py module implementing a `FeedCache` class. Feed adapters delegate to it via a decorator (`@cached_feed(ttl_seconds=86400)`) on their fetch/fetch_chain methods. The cache is optional — if `ALPHAKIT_CACHE_DIR` is set to `/dev/null` or similar, caching is disabled. Tests can opt out with a `disable_cache` context manager. CI sets up a warm cache as a GitHub Actions cache step, drastically reducing test runtime for subsequent runs. `docs/feeds/caching.md` explains the model, cache-key collisions risk (none, because keys include frequency and date range), and how to debug cache issues.

---

### ADR-007: Rate-limit coordination

**Status:** Proposed.  
**Date:** Phase 2 Session 2A.  
**Deciders:** Project maintainers.

**Context.** Free feeds have rate limits. FRED allows 120 requests/minute with an API key (free, unlimited series). yfinance has undocumented rate limits that vary by endpoint. CFTC COT is a weekly ZIP download with no formal limit but don't abuse. EIA has a 5000-request-per-hour limit with a free key.

If a benchmark runner parallelizes 50 strategies that all need FRED yield curves, each triggering its own FRED call without coordination, we can burn the minute's quota in a second.

**Options considered.**

**Option A — Global semaphore per feed.** Each feed adapter wraps its HTTP client in a rate-limit semaphore. The semaphore's capacity reflects the feed's limit (e.g., FRED has a 120-per-minute semaphore). Multiple strategies serialize through the semaphore transparently.

**Option B — Request-queue with worker pool.** More sophisticated but overkill for Phase 2.

**Option C — No coordination.** Rely on caching (ADR-006) to reduce real calls. Works for repeated backtests but fails on the first cold run.

**Decision.** Option A combined with aggressive caching from ADR-006.

**Consequences.** alphakit-data gets a `rate_limit.py` module implementing a per-feed token-bucket rate limiter. Feed adapters call `ratelimit.acquire("fred")` before each HTTP request. Limits are configurable via `ALPHAKIT_RATELIMIT_{FEED}_PER_MINUTE` env vars, with sensible defaults. In CI, limits are set low (e.g., 30/minute for FRED) to be conservative. Tests with mocked HTTP don't hit the rate limiter. `docs/feeds/rate-limits.md` documents the defaults per feed and the environment variables.

---

## Section 3 — Data Layer Design

### Module layout

After Session 2A and 2B, the packages/alphakit-data layout is:

```
packages/alphakit-data/
├── pyproject.toml                      # optional-deps cleaned up
├── README.md
└── alphakit/
    └── data/
        ├── __init__.py                 # public API exports
        ├── registry.py                 # FeedRegistry (NEW in 2A)
        ├── cache.py                    # FeedCache, @cached_feed (NEW in 2A)
        ├── rate_limit.py               # per-feed token bucket (NEW in 2A)
        ├── offline.py                  # ALPHAKIT_OFFLINE detection + fixture fallback (NEW in 2A)
        ├── errors.py                   # PolygonNotConfiguredError etc (NEW in 2A)
        ├── equities/
        │   ├── __init__.py
        │   └── yfinance_adapter.py     # existing, Phase 1
        ├── fixtures/
        │   ├── __init__.py
        │   └── generator.py            # existing, Phase 1
        ├── rates/                      # NEW in 2B
        │   ├── __init__.py
        │   └── fred_adapter.py
        ├── futures/                    # NEW in 2B
        │   ├── __init__.py
        │   ├── yfinance_futures_adapter.py
        │   └── eia_adapter.py
        ├── positioning/                # NEW in 2B
        │   ├── __init__.py
        │   └── cftc_cot_adapter.py
        └── options/                    # NEW in 2C
            ├── __init__.py
            ├── synthetic.py
            └── polygon_adapter.py      # placeholder stub
```

### FeedRegistry

```python
# alphakit/data/registry.py
from __future__ import annotations

from typing import ClassVar
from alphakit.core.protocols import DataFeedProtocol


class FeedRegistry:
    """Central registry for data feed adapters.

    Adapters register themselves by name at import time. Strategies and
    the benchmark runner look them up by name. This keeps strategy code
    feed-agnostic — swapping a synthetic options feed for a real Polygon
    feed is a registry change, not a strategy change.
    """

    _feeds: ClassVar[dict[str, DataFeedProtocol]] = {}

    @classmethod
    def register(cls, feed: DataFeedProtocol) -> None:
        if feed.name in cls._feeds:
            raise ValueError(f"Feed {feed.name!r} already registered")
        cls._feeds[feed.name] = feed

    @classmethod
    def get(cls, name: str) -> DataFeedProtocol:
        if name not in cls._feeds:
            raise KeyError(f"No feed registered under {name!r}. Registered: {sorted(cls._feeds)}")
        return cls._feeds[name]

    @classmethod
    def list(cls) -> list[str]:
        return sorted(cls._feeds)

    @classmethod
    def clear(cls) -> None:
        """Used in tests only."""
        cls._feeds.clear()
```

### Protocol extension

In Session 2A, alphakit/core/protocols.py gets DataFeedProtocol.fetch_chain added:

```python
@runtime_checkable
class DataFeedProtocol(Protocol):
    name: str

    def fetch(self, symbols, start, end, frequency="1d") -> pd.DataFrame: ...

    def fetch_chain(self, underlying: str, as_of: datetime) -> OptionChain:
        """Return an option chain snapshot.

        Feeds that don't support options raise NotImplementedError.
        """
        raise NotImplementedError(f"{self.name!r} does not support option chains")
```

The default-raising implementation keeps existing adapters (yfinance) compliant without code changes. Options-capable feeds (synthetic, polygon placeholder) override it.

### Public API

After Session 2A, alphakit/data/__init__.py exports:

```python
from alphakit.data.registry import FeedRegistry
from alphakit.data.cache import FeedCache, cached_feed
from alphakit.data.rate_limit import acquire as ratelimit_acquire
from alphakit.data.errors import (
    FeedError,
    FeedNotConfiguredError,
    PolygonNotConfiguredError,
    OfflineModeError,
)

__all__ = [
    "FeedRegistry",
    "FeedCache",
    "cached_feed",
    "ratelimit_acquire",
    "FeedError",
    "FeedNotConfiguredError",
    "PolygonNotConfiguredError",
    "OfflineModeError",
]
```

### pyproject.toml cleanup

The current file declares `[fred]` and `[ccxt]` optional-deps with no backing code. Session 2A either removes these or Session 2B adds the code. Session 2B chosen — FRED adapter is part of Phase 2 scope, and CCXT will be part of a later crypto-feed effort (Phase 3). So Session 2A trims to the ones that are real, Session 2B adds FRED back with real code.

---

## Section 4 — Session Handoffs

Eight Claude Code sessions. Each below includes: scope, dependencies, deliverables checklist, the exact prompt to paste into Claude Code, and adversarial review questions for the session closeout.

### Session 2A: Data architecture foundation

**Estimated duration:** One Claude Code session (3–4 hours of context, one PR).

**Scope.** Build the core data infrastructure: FeedRegistry, FeedCache, rate limiter, offline mode, errors module. Extend DataFeedProtocol with fetch_chain. Migrate the existing yfinance_adapter to register with the registry and use the cache/rate-limit decorators. Commit ADR-003, ADR-006, ADR-007. Clean up pyproject optional-deps (remove fred, ccxt — Session 2B will add fred back with real code).

**Dependencies.** None (first session of Phase 2). Baseline is v0.1.1 (commit 0fbc23a).

**Deliverables.**
- `packages/alphakit-core/alphakit/core/protocols.py` — DataFeedProtocol gets fetch_chain with default NotImplementedError
- `packages/alphakit-data/alphakit/data/registry.py` — FeedRegistry class
- `packages/alphakit-data/alphakit/data/cache.py` — FeedCache class and cached_feed decorator
- `packages/alphakit-data/alphakit/data/rate_limit.py` — per-feed token bucket
- `packages/alphakit-data/alphakit/data/offline.py` — ALPHAKIT_OFFLINE detection, fixture fallback wiring
- `packages/alphakit-data/alphakit/data/errors.py` — exception hierarchy
- `packages/alphakit-data/alphakit/data/__init__.py` — updated public API exports
- `packages/alphakit-data/alphakit/data/equities/yfinance_adapter.py` — migrated to register with FeedRegistry, use @cached_feed and ratelimit_acquire
- `packages/alphakit-data/pyproject.toml` — trim optional-deps to match code reality
- `docs/adr/003-multi-feed-architecture.md`
- `docs/adr/006-feed-caching-strategy.md`
- `docs/adr/007-rate-limit-coordination.md`
- `docs/adr/001-carry-data-deferred.md` — edit Status line to "Superseded by ADR-003 (2026-04-XX)"
- `packages/alphakit-data/tests/test_registry.py` — FeedRegistry unit tests
- `packages/alphakit-data/tests/test_cache.py` — cache read/write/TTL/invalidation tests
- `packages/alphakit-data/tests/test_rate_limit.py` — token bucket tests
- `packages/alphakit-data/tests/test_offline.py` — offline mode tests
- `packages/alphakit-core/tests/test_protocol_fetch_chain.py` — verify default NotImplementedError raise for feeds that don't implement it
- Full test suite still passes (existing 928 tests + ~40 new tests for Session 2A additions)
- verify-install.yml on main: 6/6 green

**Claude Code handoff prompt:**

Phase 2 Session 2A: Data architecture foundation.

Context: Phase 1 shipped DataFeedProtocol in packages/alphakit-core/alphakit/core/protocols.py with a single fetch method returning pd.DataFrame. Canonical schemas (Bar, OptionChain, OrderBook, Tick) already exist in alphakit.core.data. One adapter exists: packages/alphakit-data/alphakit/data/equities/yfinance_adapter.py. There is no registry, no caching, no rate limiting, no offline mode. This session builds that infrastructure.

Before writing any code, do these discovery steps and report back:

1. cat packages/alphakit-core/alphakit/core/protocols.py — confirm DataFeedProtocol current shape
2. cat packages/alphakit-data/alphakit/data/__init__.py — confirm current exports
3. cat packages/alphakit-data/alphakit/data/equities/yfinance_adapter.py — confirm current yfinance adapter implementation
4. cat packages/alphakit-data/pyproject.toml — confirm current optional-deps
5. ls docs/adr/ — confirm ADR-001 and ADR-002 file locations
6. git log --oneline -5 — confirm we're starting from 0fbc23a (v0.1.1)

Report the output. Do not write any code until I approve.

After discovery approval, implement:

A) Extend DataFeedProtocol with fetch_chain:

```python
from datetime import datetime
from alphakit.core.data import OptionChain

class DataFeedProtocol(Protocol):
    name: str
    def fetch(self, symbols, start, end, frequency="1d") -> pd.DataFrame: ...
    def fetch_chain(self, underlying: str, as_of: datetime) -> OptionChain:
        raise NotImplementedError(f"{self.name!r} does not support option chains")
```

The default-raising implementation means existing adapters stay compliant. Test: test_protocol_fetch_chain.py verifies a feed without fetch_chain raises NotImplementedError when called.

B) FeedRegistry in packages/alphakit-data/alphakit/data/registry.py (spec in phase-2-master-plan.md section 3). Supports register, get, list, clear (test-only). ClassVar dict _feeds. Raises ValueError on duplicate name, KeyError on missing name with helpful message listing registered feeds.

C) FeedCache in packages/alphakit-data/alphakit/data/cache.py. Disk-backed parquet. Cache key: sha256 of (feed_name, symbols_tuple, start_iso, end_iso, frequency). Default cache dir: ~/.alphakit/cache/. Override via ALPHAKIT_CACHE_DIR env var. TTL per call. Expired entries deleted lazily on next miss. @cached_feed(ttl_seconds=N) decorator wraps fetch methods. Disable cache by setting ALPHAKIT_CACHE_DIR to "/dev/null" (or raises if write fails). Tests: test_cache.py covers put/get, TTL expiry, key collision isolation, disabled mode, corrupt-file recovery.

D) Rate limiter in packages/alphakit-data/alphakit/data/rate_limit.py. Token bucket per feed. Module-level acquire(feed_name: str) -> None blocks until a token is available. Limits configured via ALPHAKIT_RATELIMIT_{FEED}_PER_MINUTE with defaults (FRED=120, YFINANCE=60, EIA=80, CFTC=10). Tests: test_rate_limit.py covers token acquisition, blocking behavior with mocked time, per-feed isolation.

E) Offline mode in packages/alphakit-data/alphakit/data/offline.py. If ALPHAKIT_OFFLINE=1, feed adapters route to fixture-generator fallback instead of making HTTP calls. is_offline() -> bool helper. offline_fallback context manager. Tests: test_offline.py verifies OFFLINE=1 routes to fixtures, OFFLINE=0 hits real code path (mocked).

F) errors.py with exception hierarchy: FeedError → FeedNotConfiguredError, PolygonNotConfiguredError (inherits FeedNotConfiguredError), OfflineModeError. Each includes a docstring explaining when it's raised.

G) Update packages/alphakit-data/alphakit/data/__init__.py with public API exports (see spec).

H) Migrate yfinance_adapter.py: (a) register itself with FeedRegistry at import time, (b) wrap fetch with @cached_feed(ttl_seconds=86400) and ratelimit_acquire("yfinance"). Its test should still pass.

I) Clean pyproject.toml optional-deps. Remove [fred] and [ccxt] — they'll be re-added by Session 2B (fred) and a later phase (ccxt) with real backing code. Leave [yfinance].

J) ADRs. Write three new ones from the spec in phase-2-master-plan.md section 2 (ADR-003, ADR-006, ADR-007). Update ADR-001 header: add "Superseded by: ADR-003 (YYYY-MM-DD)" line right after "Status".

K) Run all the checks:

```
uv run pytest packages/ -x
uv run ruff check .
uv run mypy --strict packages/alphakit-core/ packages/alphakit-data/
```

All green. Any failures, fix before proceeding.

L) Commit with message: "feat(data): multi-feed architecture foundation (FeedRegistry, cache, rate-limit, offline mode). Adds ADR-003, ADR-006, ADR-007. Supersedes ADR-001. Extends DataFeedProtocol with fetch_chain."

M) Push to main. Verify with: git log origin/main -1. Confirm hash is NOT 0fbc23a.

N) Re-trigger verify-install.yml via workflow_dispatch on main. Wait for all 6 matrix jobs green.

Session closeout report:

- New commit hash on origin/main
- Test count before and after (expect +~40 tests)
- Ruff + mypy both clean
- CI result: 6/6 green
- Files changed summary

Do not mark done until origin/main shows new commit AND CI is green on that commit.

**Adversarial review questions for Session 2A closeout:**
- Does FeedRegistry have any global-state side-effects that could cause test pollution? (The clear() method exists for this — are tests actually using it?)
- What happens if two adapters try to register under the same name due to a typo? (ValueError, confirmed.)
- If ALPHAKIT_CACHE_DIR points to a read-only location, does the cache silently succeed or raise? (Should raise on put, warn-once on get.)
- Does the rate limiter work correctly when multiple threads/processes share a process? (Phase 2 is single-process for now — document this; revisit in Phase 5 when live-trading shows up.)
- Does ALPHAKIT_OFFLINE=1 actually cover all Phase 2 adapters? (Session 2B and 2C adapters must also respect it — codify this as a contract test.)
- ADR-001 supersede wording: does the file's original content remain intact, just with the status banner updated? (Yes — don't rewrite history; add a banner.)
- After this session, does the verify-install matrix job do anything new (install the new registry/cache code) or is it just verifying the same surface? (Same surface — but the next session's adapters will exercise the new infrastructure.)

---

### Session 2B: Free-feed adapters

**Estimated duration:** One Claude Code session.

**Scope.** Implement four free-feed adapters: FRED (treasury yields, CPI, Fed funds), yfinance-futures extension (front-month + continuous commodity futures), EIA (energy inventory), CFTC COT (weekly positioning). Each adapter registers with FeedRegistry, uses @cached_feed with appropriate TTL, and calls ratelimit_acquire.

**Dependencies.** Session 2A delivered: FeedRegistry, FeedCache, rate limiter, DataFeedProtocol.fetch_chain extension.

**Deliverables.**
- `packages/alphakit-data/alphakit/data/rates/fred_adapter.py` — FRED adapter via fredapi library
- `packages/alphakit-data/alphakit/data/futures/yfinance_futures_adapter.py` — futures-specific yfinance wrapper (handles continuous contracts like `CL=F`, `GC=F`)
- `packages/alphakit-data/alphakit/data/futures/eia_adapter.py` — EIA v2 API adapter for inventory data
- `packages/alphakit-data/alphakit/data/positioning/cftc_cot_adapter.py` — CFTC COT weekly ZIP download adapter
- `packages/alphakit-data/pyproject.toml` — re-add `[fred]` optional-dep with fredapi>=0.5; add `[eia]` with requests; existing yfinance covers futures
- Per-adapter tests with mocked HTTP (never call real APIs in CI without a flag)
- `docs/feeds/fred.md`, `docs/feeds/yfinance-futures.md`, `docs/feeds/eia.md`, `docs/feeds/cftc.md` — each documents: what the feed provides, which strategies use it, how to get an API key (if needed), default rate limits, example code
- `docs/feeds/overview.md` — one-page summary listing all feeds with status (real, placeholder, planned)
- All new tests pass. Existing tests still pass.

**Claude Code handoff prompt:**

Phase 2 Session 2B: Free-feed adapters.

Context: Session 2A built FeedRegistry, FeedCache, rate_limit, offline mode, extended DataFeedProtocol with fetch_chain. This session implements four real free-feed adapters: FRED, yfinance-futures, EIA, CFTC COT.

Before writing any code, discovery:

1. ls packages/alphakit-data/alphakit/data/ — confirm Session 2A's additions are present
2. cat packages/alphakit-data/alphakit/data/registry.py — confirm FeedRegistry API
3. cat packages/alphakit-data/alphakit/data/cache.py — confirm @cached_feed decorator signature
4. cat packages/alphakit-data/alphakit/data/rate_limit.py — confirm acquire() signature
5. cat packages/alphakit-data/pyproject.toml — confirm current optional-deps
6. git log --oneline -5 — confirm Session 2A landed on origin/main

Report the output. Do not write code until I approve.

After discovery approval, implement each adapter as a separate commit on the same branch. Branch name: claude/2b-free-feeds.

Adapter 1: FRED.

- File: packages/alphakit-data/alphakit/data/rates/fred_adapter.py
- Class: FREDAdapter, name="fred"
- Uses fredapi library (re-added to [fred] optional-dep in pyproject)
- API key: FRED_API_KEY env var. If missing, raise FeedNotConfiguredError with a message pointing to https://fred.stlouisfed.org/docs/api/api_key.html
- Implements fetch(symbols, start, end, frequency): symbols are FRED series IDs (e.g., "DGS10" for 10-year treasury). Returns wide DataFrame (date x series).
- fetch_chain: raises NotImplementedError (FRED has no options)
- @cached_feed(ttl_seconds=86400) on fetch; ratelimit_acquire("fred") before each fredapi call
- Registers at import time via FeedRegistry.register(FREDAdapter())
- Tests: mock fredapi.Fred, verify fetch returns expected DataFrame shape, missing API key raises correct error, cache hit on second call.

Adapter 2: yfinance-futures extension.

- File: packages/alphakit-data/alphakit/data/futures/yfinance_futures_adapter.py
- Class: YFinanceFuturesAdapter, name="yfinance-futures"
- Extends the existing equities yfinance_adapter with handling for continuous contract symbols (=F suffix)
- Implements fetch(symbols, start, end, frequency): expects symbols like ["CL=F", "GC=F", "NG=F"]. Returns OHLCV wide DataFrame.
- @cached_feed(ttl_seconds=86400); ratelimit_acquire("yfinance")
- Tests: mock yf.download, verify =F symbols are recognized and passed through correctly.

Adapter 3: EIA.

- File: packages/alphakit-data/alphakit/data/futures/eia_adapter.py
- Class: EIAAdapter, name="eia"
- Uses requests library directly (EIA v2 API is simple JSON)
- API key: EIA_API_KEY env var. Missing → FeedNotConfiguredError with https://www.eia.gov/opendata/register.php link
- Implements fetch(symbols, start, end, frequency): symbols are EIA series IDs. Returns DataFrame (date x series).
- fetch_chain: NotImplementedError
- @cached_feed(ttl_seconds=86400); ratelimit_acquire("eia")
- Tests: mock requests.get, verify correct URL construction, verify response parsing.

Adapter 4: CFTC COT.

- File: packages/alphakit-data/alphakit/data/positioning/cftc_cot_adapter.py
- Class: CFTCCOTAdapter, name="cftc-cot"
- Uses urllib to download weekly ZIPs from https://www.cftc.gov/dea/newcot/
- No API key needed
- fetch(symbols, start, end, frequency): symbols are CFTC market codes (e.g., "067651" for S&P 500 futures). Returns long-format DataFrame with columns: date, market_code, long_positions, short_positions, net_positions, commercial_long, commercial_short, speculative_long, speculative_short
- fetch_chain: NotImplementedError
- @cached_feed(ttl_seconds=604800) — 7 days, since COT is weekly
- ratelimit_acquire("cftc")
- Tests: mock urllib.request.urlopen with canned ZIP bytes, verify parsing.

For each adapter, also create docs/feeds/<name>.md explaining: what it provides, strategies that use it, API key instructions, default rate limit, example usage, known issues.

Also create docs/feeds/overview.md: single-page listing all feeds with columns: Name, Status (Real/Placeholder/Planned), API Key Required (Y/N), Rate Limit, Phase Added.

Update packages/alphakit-data/pyproject.toml optional-deps:

```
[project.optional-dependencies]
yfinance = ["yfinance>=0.2"]
fred = ["fredapi>=0.5"]
eia = ["requests>=2.31"]
all-free-feeds = ["yfinance>=0.2", "fredapi>=0.5", "requests>=2.31"]
```

(CCXT stays out until Phase 3.)

After all four adapters:

```
uv run pytest packages/ -x
uv run ruff check .
uv run mypy --strict packages/alphakit-data/
```

All green.

Commit strategy: four commits on the branch, one per adapter, each with tests. Then a fifth commit for docs. Then PR to main. Reviewer (you, reading the PR diff before approving it) should verify: no real HTTP calls in tests, no hard-coded API keys, all adapters register correctly at import time.

Merge the PR. Verify origin/main advances. Re-trigger verify-install.yml; expect 6/6 green.

Session closeout report:

- New commit hash on origin/main
- Test count (expect +~60 tests for four adapters)
- Ruff + mypy clean
- CI result
- Feed registry now shows: yfinance, yfinance-futures, fred, eia, cftc-cot (5 feeds)

Do not mark done until origin/main shows new commit AND CI is green.

**Adversarial review for 2B:**
- Do any tests accidentally hit real APIs? (Grep for `real` or `integration_test` markers; verify CI runs with mocks only.)
- Do adapters gracefully handle malformed responses from the real APIs? (Add parametrized tests with sample corrupted payloads.)
- Is FeedRegistry.list() output in a predictable order? (Sort it.)
- What's the actual first-run experience for someone without any API keys? FRED requires a key (free signup, 30 seconds). EIA requires a key. yfinance and CFTC don't. Document this clearly in docs/feeds/overview.md.
- Cache behavior when date ranges overlap: e.g., cache(2020-2023) then request 2020-2024. Does it make one call for the missing year, or refetch everything? Phase 2 MVP: refetch everything. Note this as a known limitation, optimize in Phase 3 if it matters.

---

### Session 2C: Polygon placeholder and synthetic options chains

**Estimated duration:** One Claude Code session.

**Scope.** Ship Polygon adapter as a placeholder stub (per ADR-004). Ship synthetic options chain generator (per ADR-005). Both register with FeedRegistry. Commit ADR-004 and ADR-005.

**Dependencies.** Session 2A delivered protocol + registry. Session 2B proved the adapter pattern works. This session builds on both.

**Deliverables.**
- `packages/alphakit-data/alphakit/data/options/polygon_adapter.py` — stub, raises PolygonNotConfiguredError
- `packages/alphakit-data/alphakit/data/options/synthetic.py` — Black-Scholes + realized-vol synthetic chain generator
- `packages/alphakit-data/alphakit/data/options/__init__.py` — registers both adapters
- `packages/alphakit-data/alphakit/data/options/bs.py` — small Black-Scholes helpers (d1/d2, call/put price, greeks)
- `docs/feeds/polygon.md` — current status (placeholder), Phase 3 upgrade plan
- `docs/feeds/synthetic-options.md` — methodology, limitations, upgrade path
- `docs/adr/004-polygon-placeholder-adapter.md`
- `docs/adr/005-synthetic-options-chain.md`
- Tests covering Polygon-placeholder error paths, synthetic chain generation (strike grid, expiry grid, IV surface, BS pricing correctness)
- Update `docs/deviations.md` with a "Synthetic Options Chains" section

**Claude Code handoff prompt:**

Phase 2 Session 2C: Polygon placeholder + synthetic options chains.

Context: Sessions 2A and 2B are complete. FeedRegistry works, four free-feed adapters registered. This session adds Polygon as a placeholder (no real API) and synthetic options chains as the Phase 2 default options data source.

Discovery first:

1. cat packages/alphakit-core/alphakit/core/data/option_chain.py — confirm OptionChain, OptionQuote, OptionRight schemas
2. cat packages/alphakit-data/alphakit/data/errors.py — confirm PolygonNotConfiguredError exists (Session 2A)
3. cat packages/alphakit-data/alphakit/data/registry.py — confirm registration pattern
4. git log --oneline -5 — confirm 2B landed on origin/main

Report. Wait for approval.

Implementation:

A) Black-Scholes helpers in packages/alphakit-data/alphakit/data/options/bs.py:
- d1(S, K, T, r, sigma), d2(...)
- call_price(S, K, T, r, sigma), put_price(...)
- delta, gamma, vega, theta for calls and puts
- implied_vol via Brent's method bracketing [0.001, 5.0]

All pure numpy/scipy, no dependencies beyond what's already there.

Tests: verify against Hull textbook reference values for at least 5 strike/expiry/vol triples.

B) Synthetic adapter in packages/alphakit-data/alphakit/data/options/synthetic.py:
- Class: SyntheticOptionsFeed, name="synthetic-options"
- Constructor accepts an underlying_feed (DataFeedProtocol) for fetching spot-price history
- fetch: raises NotImplementedError (we're options-only)
- fetch_chain(underlying, as_of):
  * fetch 252 bars of underlying prices ending at as_of using the underlying_feed
  * compute realized vol over trailing 30/60/90 days
  * select appropriate vol for each expiry (30-day rvol for <45d to expiry, 60-day for 45-120d, 90-day for >120d)
  * strike grid: 0.8x, 0.85x, 0.9x, 0.95x, 1.0x, 1.05x, 1.1x, 1.15x, 1.2x spot
  * expiry grid: next 4 weekly, next 6 monthly, next 4 quarterly (14 expiries total)
  * for each (strike, expiry, right) combo, compute BS price and greeks
  * assemble as OptionQuote tuple, return OptionChain
- No real IV skew (flat vol across strikes — documented limitation)
- No bid-ask spread (bid=ask=mid=price)
- Registers at import time

Tests: verify chain has expected number of quotes, verify greeks are in plausible ranges, verify round-trip against OptionChain's filter() and strikes() methods.

C) Polygon placeholder in packages/alphakit-data/alphakit/data/options/polygon_adapter.py:
- Class: PolygonAdapter, name="polygon"
- Constructor takes no args
- fetch: raises NotImplementedError ("Polygon adapter is a placeholder; use Phase 3+ for real integration")
- fetch_chain(underlying, as_of):
  * Check POLYGON_API_KEY env var
  * If missing: raise PolygonNotConfiguredError("POLYGON_API_KEY env var not set. Polygon is a placeholder in Phase 2 — use 'synthetic-options' feed instead. See docs/feeds/polygon.md.")
  * If present: raise NotImplementedError("Polygon adapter placeholder. Real integration scoped for Phase 3. See docs/adr/004-polygon-placeholder-adapter.md.")
- Registers at import time

Tests: both error paths covered.

D) __init__.py in options/: imports both adapters to trigger registration.

E) docs/feeds/polygon.md:

```
# Polygon.io
Status: Placeholder (Phase 2) — real integration planned Phase 3
Provides: Real-time and historical options chains with greeks, IV, volume, OI.
Cost: $29/mo for options tier.
Why placeholder in Phase 2: [explanation from ADR-004]
How to use today: You cannot, directly. Use 'synthetic-options' feed instead.
Phase 3 upgrade: Set POLYGON_API_KEY, switch FeedRegistry.get("polygon") calls as documented.
```

F) docs/feeds/synthetic-options.md:

```
# Synthetic Options Chains
Status: Primary Phase 2 options feed.
Methodology: Black-Scholes pricing with realized-volatility-based IV.
Limitations:
- Flat vol across strikes (no IV skew)
- No bid-ask spread modeling
- No realistic volume or open interest
- Greeks are BS-computed, not market-implied
When accurate: Signal-logic validation, systematic strategy backtest plausibility checks.
When inaccurate: Absolute strategy returns (backtest will overstate/understate depending on skew direction of the underlying). Vol-arb strategies that depend on skew. Anything depending on microstructure.
Upgrade path: Swap "synthetic-options" → "polygon" in FeedRegistry.get() once Phase 3 real integration ships.
```

G) docs/adr/004-polygon-placeholder-adapter.md — full text from section 2 above.
   docs/adr/005-synthetic-options-chain.md — full text from section 2 above.

H) Update docs/deviations.md with a new section: "Synthetic Options Chains (Phase 2)" — 2-3 paragraphs explaining that all 20 Phase 2 options strategies backtested on synthetic chains, with an upgrade path.

I) Run checks:

```
uv run pytest packages/ -x
uv run ruff check .
uv run mypy --strict packages/alphakit-data/
```

J) Commit: branch claude/2c-options-feeds. Two commits: "feat(data-options): Polygon placeholder adapter" and "feat(data-options): synthetic option chain generator (Black-Scholes + realized-vol IV)". Then docs commit. PR to main. Merge. Confirm origin/main advances. CI green.

Session closeout:

- New commit hash
- Tests added: ~30-40 (BS helpers + synthetic chain + Polygon stub)
- Feed registry now lists: yfinance, yfinance-futures, fred, eia, cftc-cot, synthetic-options, polygon (7 feeds)
- All green.

Do not mark done until origin/main shows new commit AND CI green.

**Adversarial review for 2C:**
- Black-Scholes implementation: tested against known textbook values? Put-call parity verified?
- Synthetic chain: does it respect the OptionChain immutability contract? (Tuple, not list.)
- What happens if underlying_feed.fetch returns NaN or insufficient history for the realized-vol window? (Raise clearly, don't silently produce garbage chains.)
- Is the synthetic chain deterministic? (Given same underlying + same as_of, should produce identical chain. Test this.)
- Does Polygon error message correctly direct users to synthetic-options? (Yes, per spec.)
- Does the test suite verify both error paths of Polygon adapter (key-missing and key-present-but-placeholder)? (Yes.)

---

### Session 2D: Rates family (15 strategies)

**Estimated duration:** One Claude Code session (possibly 1.5 if full DOI research is needed mid-session).

**Scope.** 15 rates strategies using real FRED yield curve data.

**Strategy list (provisional — Session 2D starts by confirming each has a citable paper):**

1. bond_tsmom_12_1 — Time-series momentum on 10Y treasury returns. [Moskowitz/Ooi/Pedersen 2012 applied to bonds — Asness et al "Value and Momentum Everywhere" 2013.]
2. curve_steepener_2s10s — Short 2Y / long 10Y when 2s10s spread is narrow. [Litterman/Scheinkman "Common Factors Affecting Bond Returns" 1991.]
3. curve_flattener_2s10s — Reverse of above when spread is wide.
4. curve_butterfly_2s5s10s — Long wings, short belly when 2-5-10Y PCA signals mispricing.
5. bond_carry_rolldown — Carry-and-rolldown on forward bond yields. [Fama 1984 "Forward Rates as Predictors of Future Spot Rates."]
6. duration_targeted_momentum — Momentum on duration-adjusted bond returns. [Durham 2015.]
7. breakeven_inflation_rotation — Long TIPS vs nominals when breakeven spreads compress. [Campbell/Shiller 1996.]
8. real_yield_momentum — Momentum on real yields (TIPS). [Pflueger/Viceira 2011.]
9. yield_curve_pca_trade — Trade deviations from the first three PCs. [Litterman/Scheinkman 1991.]
10. fed_funds_surprise — Position bonds after FOMC rate decision vs expectations. [Kuttner 2001.]
11. g10_bond_carry — Rank G10 sovereigns by short-rate carry. [Asness/Moskowitz/Pedersen 2013.]
12. credit_spread_momentum — Momentum on IG corporate credit spreads. [Jostova et al 2013.]
13. swap_spread_mean_rev — Mean-reversion on swap spread to risk-free rate. [Liu/Longstaff/Mandell 2006.]
14. fra_ois_spread — Position on FRA-OIS spread (funding stress indicator). [McAndrews/Sarkar/Wang 2008.]
15. global_inflation_momentum — Rank countries by inflation momentum, tilt bond exposure. [Ilmanen 2011 "Expected Returns" Ch 12.]

**Dependencies.** FRED adapter (Session 2B) fully functional. OptionChain not needed for this family.

**Deliverables.**
- 15 strategy folders under `packages/alphakit-strategies-rates/alphakit/strategies/rates/`, each with full per-strategy contract
- `packages/alphakit-strategies-rates/pyproject.toml` — new sub-package, depends on alphakit-core, alphakit-data[fred]
- 15 benchmark_results.json (first against synthetic data from fixtures, second against real FRED data)
- Integration test per strategy that runs against mocked FRED data
- Update `packages/alphakit-bench/alphakit/bench/discovery.py` — should auto-discover the new rates family (no manual wiring needed if discovery is pattern-based)
- Verify all 60 Phase 1 + 15 Phase 2 rates = 75 total strategies discoverable
- verify-install.yml updated to include alphakit-strategies-rates in the install matrix

**Claude Code handoff prompt pattern (customized per session at start):** Discovery-first (git log, ls packages/, confirm 2B landed, confirm FRED adapter imports correctly), then per-strategy commits on branch `claude/2d-rates`, full contract each (strategy.py, config.yaml, paper.md with DOI, known_failures.md, README.md, tests/test_unit.py, tests/test_integration.py, benchmark_results.json), final commit adds alphakit-strategies-rates to install_from_git scripts and verify-install.yml matrix, PR to main, merge, confirm origin/main advances, CI green.

**Adversarial review for 2D:**
- Does each strategy actually need FRED, or is it secretly using price data that was already available in Phase 1? (If yes, it belongs in a different family.)
- Benchmark_results.json: both synthetic and real-FRED versions saved?
- Are any two rates strategies producing correlation > 0.95? (Cluster flag.)
- Is the FRED cache being used, or does the benchmark runner make 15 × N calls each time? (Should hit cache after first run.)
- Does any strategy's paper.md cite a DOI that doesn't resolve? (Spot-check 3 at random.)

---

### Session 2E: Commodity family (15 strategies)

**Estimated duration:** One Claude Code session.

**Strategy list:**

1. wti_backwardation_carry — Long front-month vs deferred when in backwardation.
2. ng_contango_short — Short natural gas when in contango (rolling negative carry).
3. grain_seasonality — Corn/soybean/wheat seasonality overlay.
4. energy_weather_premium — WTI pre-winter premium.
5. cot_speculator_position — Position based on CFTC speculator net long/short.
6. crack_spread — Long crack spread (RBOB-heating oil vs WTI).
7. crush_spread — Soybean-meal-oil crush spread.
8. metals_momentum — Gold/silver/copper/platinum momentum.
9. commodity_curve_carry — Cross-commodity carry (roll yield).
10. wti_brent_spread — Mean-reversion on WTI-Brent.
11. henry_hub_ttf_spread — Mean-reversion on US-EU nat gas.
12. inventory_surprise — Trade oil on EIA inventory report vs consensus.
13. calendar_spread_corn — Corn calendar spread (March-July).
14. coffee_weather_asymmetry — Coffee long exposure during Brazilian winter.
15. commodity_tsmom — Cross-commodity time-series momentum.

**Dependencies.** yfinance-futures (Session 2B), EIA (Session 2B), CFTC COT (Session 2B).

**Deliverables.** Same pattern as 2D: new `packages/alphakit-strategies-commodity/` sub-package, 15 strategy folders with full contract, integration tests with mocked feeds, benchmark results (synthetic + real), verify-install.yml matrix updated.

**Adversarial review for 2E:**
- Seasonality strategies: is the seasonality statistically significant or curve-fit? (Expose in known_failures.md honestly.)
- COT positioning lag: weekly data is released Friday for Tuesday — is the strategy respecting this 3-day lag?
- Crack/crush spreads: are the ratios (3-2-1 for crack, 1-1.5-0.8 for crush) hardcoded correctly?
- WTI-Brent and Henry Hub-TTF: are the pairs actually cointegrated over the test period? (Johansen test in the strategy or in paper.md.)

---

### Session 2F: Options family (20 strategies)

**Estimated duration:** One Claude Code session. Possibly the largest session in Phase 2.

**Strategy list (all backtest on synthetic chains per ADR-005):**

1. covered_call_systematic — Write 1-month 2% OTM call on SPY monthly.
2. cash_secured_put_systematic — Write 1-month 5% OTM put on SPY.
3. wheel_strategy — CSP assignment → covered call → roll.
4. iron_condor_monthly — Sell 1-month ATM±5% call + put.
5. short_strangle_monthly — Sell 1-month ATM±10% call + put.
6. delta_hedged_straddle — Long straddle with daily delta hedge.
7. vix_term_structure_roll — Long VXX when VIX<VIX6M, short when above.
8. vix_front_back_spread — Trade the slope of VIX futures curve.
9. put_skew_premium — Short OTM puts / long OTM calls.
10. calendar_spread_atm — Long back-month / short front-month ATM call.
11. diagonal_spread — ITM long call / OTM short call.
12. bxm_replication — Replicate the CBOE BXM index.
13. pin_risk_capture — Write ATM straddle on monthly expiry Friday.
14. weekly_theta_harvest — 7-day OTM put/call write.
15. earnings_vol_crush — Long straddle 5 days before earnings, close after.
16. variance_risk_premium_synthetic — Short variance swap replication via straddles.
17. gamma_scalping_daily — Long straddle, delta-hedge daily.
18. skew_reversal — When put-skew >1.5 sigma, short puts.
19. ratio_spread_put — Long 1x ATM put, short 2x OTM put.
20. dispersion_trade_proxy — Long index straddle, short basket straddles.

**Dependencies.** synthetic-options feed (Session 2C).

**Deliverables.** Same pattern: new `packages/alphakit-strategies-options/` sub-package, 20 strategy folders, full contracts, each paper.md includes the "Data Fidelity" note about synthetic chains, verify-install.yml matrix updated.

**Adversarial review for 2F:**
- Does the covered call strategy model assignment risk correctly? (If spot goes above strike, the call is assigned — do we account for this?)
- Iron condor: are both wings sized correctly to cap max loss?
- VIX strategies: VXX has negative roll yield — is the backtest accounting for it?
- Earnings vol crush: synthetic chains have no earnings-vol structure. How is this backtested? (Answer: compute trailing-90-day vol, assume 1.5x multiplier pre-earnings, collapse post. Document clearly in paper.md.)
- Put-call parity check: are any strategies accidentally arbitraging the synthetic chain due to a BS parameter mismatch? (Run parity test on generated chains.)

---

### Session 2G: Macro/GTAA family (15 strategies)

**Estimated duration:** One Claude Code session.

**Strategy list:**

1. permanent_portfolio — 25/25/25/25 stocks/LTBonds/gold/cash. [Harry Browne 1981.]
2. risk_parity_3asset — Equal risk contribution across stocks, bonds, commodities. [Bridgewater All-Weather.]
3. min_variance_gtaa — Minimum variance weighting across 9 asset ETFs.
4. max_diversification — Max diversification ratio weighting. [Choueifaty/Coignard 2008.]
5. economic_regime_rotation — Rotate based on CPI/GDP growth regimes.
6. cape_country_rotation — Rank countries by CAPE, long cheapest 25%. [Shiller/Siegel 1998.]
7. dollar_strength_tilt — Short EM when DXY rising.
8. yield_curve_regime_asset_allocation — Steep curve → equities; flat → bonds.
9. recession_probability_rotation — Rotate to bonds when recession prob > 30% (Cleveland Fed indicator).
10. fed_policy_tilt — Risk-on when Fed cutting; risk-off when hiking.
11. inflation_regime_allocation — Stocks/bonds/commodities/gold based on inflation regime.
12. global_macro_momentum — 12-1 momentum across 24 asset class ETFs.
13. dual_momentum_gtaa — Absolute + relative momentum overlay. [Antonacci 2015.]
14. 5_asset_tactical — Vigilant asset allocation on 5 ETFs. [Keller/Keuning 2014.]
15. commodity_overlay_gtaa — Base 60/40 plus commodity tilt when inflation rising.

**Dependencies.** FRED (Session 2B), yfinance (Phase 1).

**Deliverables.** Same pattern: new `packages/alphakit-strategies-macro/` sub-package, 15 strategy folders, full contracts, verify-install.yml matrix updated.

**Adversarial review for 2G:**
- Permanent Portfolio: is the rebalance frequency (annual) preserved faithfully?
- Risk parity: is the vol target configurable, or hard-coded to 10%?
- CAPE rotation: which data source for historical CAPE by country? (Shiller's website is US-only; other countries require alternative sources — document honestly.)
- Economic regime strategies: regime definitions are subjective. Is the paper.md clear about which paper's regime definition is used?
- Recession probability: Cleveland Fed updates its model — is the strategy using the most current version or an old snapshot? (Document the model version.)

---

### Session 2H: Phase 2 closeout

**Estimated duration:** One Claude Code session plus manual release steps.

**Scope.** Benchmark runner extended, cluster analysis, CHANGELOG, README update, verify-install extension, v0.2.0 release.

**Deliverables.**
- benchmark runner regenerates all 125 strategies' benchmark_results.json (synthetic + real-feed where applicable)
- Cluster analysis report: `docs/benchmark_notes.md` updated with Phase 2 clusters
- `docs/deviations.md` — Phase 2 section covering all synthetic-data deviations
- `CHANGELOG.md` — full v0.2.0 section
- `README.md` — new leaderboard, install instructions remain the same (script-based from git)
- `docs/phase-2-master-plan.md` — mark completed tasks, add retrospective
- `verify-install.yml` — matrix now includes alphakit-strategies-rates, -commodity, -options, -macro
- v0.2.0 tagged via GitHub UI (pre-release)
- Full manual verification against v0.2.0 tag: fresh PowerShell venv, install all packages, run 4-test suite, confirm all pass
- CI on the tag: 6/6 green

**Claude Code handoff prompt:** Generated at session start based on actual state — ensures the closeout reflects reality, not assumptions.

**Adversarial review for 2H:**
- Did all 65 Phase 2 strategies actually ship with the full per-strategy contract? (Spot-check 10.)
- Any _proxy suffixes that snuck in without being scoped for a future phase? (Should be zero in Phase 2 — per ADR-002.)
- Is the verify-install matrix actually installing the 4 new family packages? (Check the YAML.)
- Does the v0.2.0 release notes template honestly acknowledge synthetic options chains as the default options feed?
- Is origin/main's commit hash on v0.2.0 tag the same as the v0.2.0 CI run's target? (Common v0.1.0 mistake.)

---

## Section 5 — 65-Strategy Manifest

Per-strategy manifest tables are produced and committed during Sessions 2D-2G as each family lands. The canonical table form is in `docs/papers/phase-2.md` (human-readable) and `docs/papers/phase-2.bib` (BibTeX format).

Each manifest row contains:

- **Slug** (e.g., `bond_tsmom_12_1`)
- **Family** (rates, commodity, options, macro)
- **Paper** (first-author surname + year)
- **DOI** (or arxiv.org link; ISBN for books)
- **Feed required** (fred, yfinance-futures, cftc-cot, synthetic-options, macro-composite)
- **Real-data compatible** (y/n — is a real feed available, or is this synthetic-only in Phase 2)
- **Expected Sharpe range** (on synthetic fixture data, so fresh clones see the same range as CI)
- **Known failures** (one-line summary pointing to the strategy's known_failures.md)

The manifest tables are reserved here — not populated in this master plan — because populating them before implementation would encode assumptions about each strategy's exact behavior. Populate during Sessions 2D-2G with real numbers from actual benchmark runs, not projections.

**Cross-reference.** When a strategy in Sessions 2D-2G ships, its row gets added to `docs/papers/phase-2.md` in the same commit. No strategy is considered complete until its manifest row is committed. This is a hard contract.

**Session 2H final audit.** The first task in Session 2H is to diff the manifest against the actually-shipped strategies:

```bash
# Expected: 65 rows in docs/papers/phase-2.md matching 65 strategy folders
wc -l docs/papers/phase-2.md
find packages/alphakit-strategies-rates packages/alphakit-strategies-commodity \
     packages/alphakit-strategies-options packages/alphakit-strategies-macro \
     -maxdepth 4 -name "strategy.py" | wc -l
```

Mismatches get resolved before v0.2.0 tag. The manifest is ground truth for the release notes.

---

## Section 6 — Benchmark and Validation Plan

### Phase 2 benchmark execution

After each family session (2D-2G), the benchmark runner regenerates that family's `benchmark_results.json` files. Two variants per strategy, saved side-by-side:

- `benchmark_results_synthetic.json` — against synthetic fixtures (Phase 1 pattern, keeps CI offline-safe)
- `benchmark_results_real.json` — against real feeds where available (FRED for rates, yfinance-futures + CFTC + EIA for commodity, synthetic-options for options, FRED + yfinance for macro)

**Why both.** Synthetic results feed the README leaderboard because they're deterministic across fresh clones (no API key, no cache) and stable across CI runs. Real-feed results feed `docs/benchmark_notes.md` with honest commentary about how the strategy behaves on production-like data. Users comparing the two can see immediately which strategies are robust and which are fixture-sensitive.

**Benchmark runner updates needed in Session 2H.** The existing runner (`packages/alphakit-bench/alphakit/bench/runner.py`) needs two extensions:

1. A `--feed-mode={synthetic|real|both}` flag. Default `synthetic` (preserves Phase 1 behavior). CI uses `synthetic` to stay offline-safe; manual runs can use `real` or `both`.
2. Two distinct output paths per strategy so synthetic and real results don't overwrite each other.

### Cluster detection

Phase 1 shipped with 6 volatility strategies producing identical Sharpe ratios on synthetic data. Phase 2 has a genuine risk of more clusters — e.g., the 4 grain-related commodity strategies may all produce similar signals on generic commodity fixtures, or the 3 VIX-based options strategies may collapse into near-identical behavior without real VIX term structure data.

**The cluster-detection procedure runs at Session 2H:**

1. For each Phase 2 strategy, compute the equity curve under synthetic fixtures.
2. Compute pairwise Pearson correlation of equity curves across all Phase 2 strategies (65 × 65 matrix).
3. Flag any pair with `|ρ| > 0.95` as a suspected cluster.
4. Human review each flagged pair: are they legitimately similar (e.g., bond_tsmom and global_inflation_momentum both trading rates momentum), or is one an accidental duplicate?
5. Legitimate pairs get documented in `docs/benchmark_notes.md` under "Known Phase 2 clusters."
6. Accidental duplicates get refactored (tweak parameters, change rebalance frequency) or one drops.

A script `scripts/cluster_analysis.py` implements this. It runs in Session 2H and is committed so future phases can reuse it.

### Pretend-you're-a-user verification template

A reusable PowerShell script, committed to `scripts/verify_release_windows.ps1`, reproduces the fresh-user install experience. Template code (same pattern that caught v0.1.0's install bug):

```powershell
# scripts/verify_release_windows.ps1
# Usage: .\verify_release_windows.ps1 -Tag v0.2.0

param(
    [Parameter(Mandatory=$true)]
    [string]$Tag
)

$testDir = "$env:TEMP\alphakit-$Tag-verify"
Remove-Item -Recurse -Force $testDir -ErrorAction SilentlyContinue
pip cache purge
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\pip\Cache" -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Path $testDir | Out-Null
Set-Location $testDir
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

$REPO = "https://github.com/ankitjha67/alphakit.git"

# Install all sub-packages
$packages = @(
    "alphakit-core",
    "alphakit-bridges",
    "alphakit-data",
    "alphakit-bench",
    "alphakit-strategies-trend",
    "alphakit-strategies-meanrev",
    "alphakit-strategies-carry",
    "alphakit-strategies-value",
    "alphakit-strategies-volatility",
    "alphakit-strategies-rates",       # NEW in v0.2.0
    "alphakit-strategies-commodity",   # NEW in v0.2.0
    "alphakit-strategies-options",     # NEW in v0.2.0
    "alphakit-strategies-macro"        # NEW in v0.2.0
)

foreach ($pkg in $packages) {
    pip install --no-cache-dir "$pkg @ git+$REPO@$Tag#subdirectory=packages/$pkg"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install $pkg"
        exit 1
    }
}

# Four-test verification
Write-Host "=== Test 1: basic import ===" -ForegroundColor Cyan
python -c "from alphakit.strategies.rates.bond_tsmom_12_1 import BondTSMOM12m1m; print('Test 1 OK')"

Write-Host "=== Test 2: all 9 families import ===" -ForegroundColor Cyan
python -c @"
from alphakit.strategies.trend.tsmom_12_1 import TimeSeriesMomentum12m1m
from alphakit.strategies.meanrev.bollinger_reversion import BollingerReversion
from alphakit.strategies.carry.fx_carry_g10 import FXCarryG10
from alphakit.strategies.value.pb_value import PBValue
from alphakit.strategies.volatility.vol_targeting import VolTargeting
from alphakit.strategies.rates.bond_tsmom_12_1 import BondTSMOM12m1m
from alphakit.strategies.commodity.wti_backwardation_carry import WTIBackwardationCarry
from alphakit.strategies.options.covered_call_systematic import CoveredCallSystematic
from alphakit.strategies.macro.permanent_portfolio import PermanentPortfolio
print('Test 2 OK — all 9 families import')
"@

Write-Host "=== Test 3: discovery returns 125 strategies ===" -ForegroundColor Cyan
python -c @"
from alphakit.bench.discovery import discover_slugs
slugs = discover_slugs()
assert len(slugs) == 125, f'Expected 125, got {len(slugs)}'
print(f'Test 3 OK — {len(slugs)} strategies')
"@

Write-Host "=== Test 4: end-to-end rates backtest ===" -ForegroundColor Cyan
python -c @"
import os
os.environ['ALPHAKIT_OFFLINE'] = '1'  # Use fixtures, no real FRED call
from alphakit.strategies.rates.bond_tsmom_12_1 import BondTSMOM12m1m
from alphakit.bridges.vectorbt_bridge import run
from alphakit.data.fixtures.generator import synthetic_bond_panel

data = synthetic_bond_panel(n_days=1000, n_bonds=5)
strategy = BondTSMOM12m1m()
result = run(strategy, data)
print(f'Sharpe: {result.sharpe:.2f}')
print(f'Max DD: {result.max_dd:.2%}')
print('Test 4 OK — end-to-end rates backtest')
"@

Write-Host "All 4 tests passed for $Tag" -ForegroundColor Green
```

This script is run manually before every tag. It reproduces the Windows experience that caught v0.1.0's bug in hours. Running it is non-negotiable before creating any release tag — same discipline as Phase 1.

### CI matrix extension

After Session 2H, verify-install.yml's install step iterates over 13 sub-packages (9 from Phase 1 + 4 from Phase 2). The matrix remains 3 Python × 2 OS = 6 jobs per tag push. Total job count: 6 jobs × 13 packages × per-Python cache = manageable runtime.

**Offline-mode enforcement.** CI sets `ALPHAKIT_OFFLINE=1` environment variable in verify-install.yml. This guarantees that CI never makes real API calls (no FRED_API_KEY, no EIA_API_KEY, no Polygon checks). All adapter tests must respect this. Session 2A's adversarial review question #5 enforces this as a contract.

### Weekly scheduled benchmark runs

The existing `benchmark.yml` weekly runner gets updated in Session 2H to cover Phase 2 strategies. Two matrix modes:

- **Synthetic weekly run** (always-on): regenerates `benchmark_results_synthetic.json` for all 125 strategies. Runs Sunday 00:00 UTC. ~10 minutes.
- **Real-data monthly run** (opt-in, manual workflow_dispatch): pulls FRED, CFTC, EIA and regenerates `benchmark_results_real.json`. Requires FRED_API_KEY and EIA_API_KEY as GitHub secrets. Skipped if keys missing.

The monthly real-data run serves as a drift detector. If `benchmark_results_real.json` for `bond_tsmom_12_1` shifts materially between runs, that's either real market change (interesting) or data-feed change (concerning). Either way, it surfaces in the monthly diff.

---

## Section 7 — Silent-Build Discipline Framework

Silent build foregoes the external pressure that normally shapes open-source development: user bug reports, feedback on design choices, reality-checks from critics. Without that pressure, three failure modes emerge: quality drift (standards relax because nobody's watching), scope drift (features creep in without external justification), and motivation drift (8 weeks of shipping into the void is psychologically hard). This section names mechanisms that substitute for external pressure.

### Per-session adversarial review

Every session's closeout includes the adversarial review questions listed in Section 4. These are not optional. They're answered in writing, committed to the session's PR description, and the PR cannot merge until every question has an answer — even if the answer is "we deliberately deferred this to Phase 3."

The Claude Code session running the implementation work is the implementer. The review is conducted by the same Claude Code session, immediately before declaring the session done. The adversarial review is a structured self-critique, not a rubber-stamp. If the implementer's answer is "yes it works" for every question, the review is failing — at least one question should surface something worth fixing or documenting.

**Concrete discipline:** during Session 2A's closeout report, one adversarial question must produce a non-trivial response. If all seven produce "yes, confirmed" with no caveats, pause and probe again — there's something missed.

### Monthly architecture audit

At weeks 2, 4, 6, 8 of Phase 2, pause implementation for a two-hour architectural audit. Produce `docs/audits/phase-2-week-N.md`.

**Week 2 audit (after Sessions 2A-2B):**
- Is the 9-package structure (now 11 with rates + commodity + options + macro incoming) still the right shape, or should we consolidate?
- Are the free-feed adapters all following the same pattern (register at import, @cached_feed, ratelimit_acquire)? Any drift?
- Is ADR-003's fetch_chain extension holding up, or are strategies finding it awkward?
- Are pyproject optional-deps tracking code reality, or is drift starting?
- Has any strategy shipped without full per-strategy contract? (Spot-check all shipped so far.)

**Week 4 audit (after Sessions 2C-2D):**
- How's the synthetic options chain holding up under 20 strategies? Is it flexible enough, or are strategies working around its limitations?
- Do the rates strategies cluster badly? (Run cluster_analysis.py on Phase 2 rates.)
- Is the benchmark runner still scaling, or is it slow enough to discourage regeneration?
- Are any ADRs from Phase 1 or early Phase 2 proving wrong? Time to supersede?

**Week 6 audit (after Sessions 2E-2F):**
- Final integration check: do rates + commodity + options all coexist cleanly, or are there import ordering issues?
- Are Phase 2 strategies' papers actually citing real papers, or are we sliding toward "inspired by" without hard citations?
- Honest scope check: are we on track for 65 strategies, or did some fall out along the way?

**Week 8 audit (after Session 2G, before 2H):**
- Final drift check. Does the repo match the plan?
- Are the Phase 3 handoff notes accurate — what really picks up where Phase 2 stops?
- What lessons go into the Phase 2 retrospective that opens the Phase 3 plan?

Audits are committed to the repo. They're ugly, honest, and short. Two pages of bullets per audit, not a formal document. The goal is to force a pause, not to produce more artifacts.

### Private trusted-reviewer channel (optional, at v0.3.0)

Phase 2 is silent. Phase 3 can optionally open a private reviewer channel — invite 2-3 trusted quant friends (not public, just GitHub repo collaborator access) to review Phases 2-3 work. They see what's been built, give honest feedback, code gets better.

**Why not earlier:** Phase 2 is architectural; the decisions are opinionated and we want to commit to them before soliciting debate. Phase 3 outputs (real Polygon data, more strategies, LEAN bridge) are more straightforwardly reviewable.

**Candidate reviewers to consider:** anyone from your 28K LinkedIn quant-network who's actually built systematic strategies (not just posts about them). Avoid pure academics — they'll over-index on paper-grade rigor and under-index on engineering tradeoffs. Prefer practitioners who've shipped production systems.

**Not a commitment.** Reevaluate at v0.2.0 tag. If silent-build momentum is strong, keep it silent. If you're feeling the lack of feedback, open the channel.

### Motivation-risk mitigations

Shipping into the void for 6-8 weeks is genuinely hard. Three mechanisms reduce burnout risk:

**Weekly mini-merges.** Each session is its own merge-to-main moment. Every merged PR is a small win. Phase 2's 8 sessions mean 8 such wins across the 6-8 weeks. Not daily, but frequent enough to sustain momentum.

**Adjacent-topic LinkedIn posts.** Your LinkedIn presence (28K followers, quant/risk content) stays active throughout Phase 2 on adjacent topics: Basel III regulatory changes, credit risk model governance, open-source engineering discipline, prompt engineering for technical work, Claude Skills architecture. None of these reveal alphakit. All of them keep your voice in the market and satisfy the "ship and show" instinct without breaking silent-build.

**Honest pace tracking.** If week 4 audit shows you're at 25% of Phase 2 work instead of 50%, don't panic and don't compress quality. Adjust the timeline. Shipping 125 rigorous strategies in 12 weeks is infinitely better than shipping 200 sloppy ones in 8. The v1.0 target (500+ strategies) has 8+ more phases to absorb pace changes.

**Intentional rest.** Phase 1 was sprinted. Phase 2 is a marathon. Build in non-coding days. EY work, family, health, sleep. A tired builder makes architectural mistakes that compound into weeks of rework. The project's competitive moat is quality; quality requires a rested builder.

### Drift detection mechanisms

Five automatic checks running across Phase 2:

1. **pyproject-vs-code drift.** Script that fails CI if any `optional-dependencies` entry has no corresponding code using the package. Prevents Phase 1's fred/ccxt problem from recurring.

2. **README-vs-code drift.** `test_readme_api.py` pattern extended: every public API claim in README, strategy READMEs, and docs/ gets an assertion. Added per family in Sessions 2D-2G.

3. **Manifest-vs-code drift.** Session 2H audit (Section 5) compares `docs/papers/phase-2.md` row count to `packages/alphakit-strategies-*/` strategy folder count. Must match 65.

4. **ADR-vs-code drift.** Grep for references to superseded ADRs in new code. ADR-001 is superseded by ADR-003; any new code citing ADR-001 as live is a drift signal.

5. **Known-failures-vs-tests drift.** Every strategy's `known_failures.md` section called "Failure modes that are tested" must correspond to actual tests in `tests/test_unit.py` or `tests/test_integration.py`. Drift means either the docs lie or the tests don't catch what they claim.

All five run in CI (or session-end scripts). Drift breaks the build, not a comment thread.

---

## Section 8 — Risks and Mitigations

Phase 2's major risks, probability × impact, and the mitigation committed to.

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|------------|
| 1 | Real FRED / EIA rate-limiting trips during benchmark runs | Medium | Medium | Caching (ADR-006) plus rate-limit coordinator (ADR-007). CI uses warm cache via GitHub Actions cache step. Weekly benchmark respects ALPHAKIT_OFFLINE=1 for baseline. |
| 2 | Synthetic options chains produce implausible backtest numbers | Medium | Low-Medium | Honest `docs/deviations.md` section for every options strategy. Spot-check 3 strategies' synthetic backtest vs published academic backtests; if off by >1 order of magnitude, refine BS IV parameters. If still off, flag the strategy in known_failures.md. |
| 3 | Cluster of near-duplicate strategies ships undetected | Medium | Low | Session 2H cluster analysis with ρ=0.95 flag. Script committed as `scripts/cluster_analysis.py` so future phases reuse. |
| 4 | Session context loss (push didn't happen, fix never landed) | Low-Medium (happened in Phase 1 multiple times) | High | Every session closeout requires explicit `git log origin/main -1` output showing the new commit hash, not the baseline. This is a hard session-done criterion. |
| 5 | Burnout during 6-8 week silent build | Medium | High | Weekly audits, weekly mini-merges, adjacent-topic posts, intentional rest days. See Section 7 mitigations. |
| 6 | ADR drift — new decision contradicts prior ADR without formal supersede | Low | Medium | ADR discipline: every decision gets an ADR, ADRs reference each other explicitly, superseded ADRs get a banner (not rewritten). |
| 7 | Strategy fails the paper-citation test (no citable paper exists) | Low-Medium | Medium | Drop the strategy from Phase 2 manifest rather than ship without citation. Keep honesty bar. If <65 strategies ship, the v0.2.0 release notes say 60-65, not "target 65". |
| 8 | pip cache staleness breaks local verification (repeat of v0.1.1 issue) | High | Low | `scripts/verify_release_windows.ps1` uses `--no-cache-dir` and `pip cache purge` in every run. Template committed to repo. |
| 9 | verify-install matrix grows unwieldy as sub-packages multiply | Medium | Low | Matrix capped at 13 sub-packages × 3 Python × 2 OS = 78 jobs. Still manageable. When Phase 3 adds more, re-evaluate parallelism. |
| 10 | A Phase 2 strategy requires an API that Phase 2 doesn't have | Low | Low | Ship it in a later phase; don't hack around it. Better to ship 60 rigorous strategies than 65 that need an apology. |
| 11 | Silent build produces a structural architecture mistake that can't be caught without user feedback | Medium | High | Per-session adversarial review. Monthly audits. Optional trusted-reviewer channel at v0.3.0. This is the biggest risk — no single mitigation fully addresses it. |
| 12 | Free feed APIs break or get rate-limited more aggressively mid-Phase 2 | Low-Medium | Medium | Each adapter has a fixture fallback via ALPHAKIT_OFFLINE=1. If FRED deprecates their v1 API mid-build, we switch to v2 and flag as a Phase 2 amendment in `docs/phase-2-amendments.md`. |
| 13 | A Phase 2 session runs longer than one Claude Code context window | Medium | Low-Medium | Each session scoped carefully. If overrun happens, split the session at a natural boundary (e.g., Session 2F splits options into 2F-1 and 2F-2). Document in amendments. |
| 14 | Phase 2 timeline drifts from 6-8 weeks to 12+ weeks | Medium | Low | Not a failure mode — the plan flexes. Document honestly in amendments. v1.0 target date moves, quality bar doesn't. |
| 15 | A paid-feed contributor opens a PR adding real Polygon integration | Low | Low-Medium | Triage per ADR-004: real Polygon is Phase 3 or later. A well-written PR could accelerate Phase 3's start, but don't let someone else's enthusiasm derail Phase 2 scope. Thank, label `phase-3`, merge later. |

### Early-warning signals per risk

Risks 1-3 surface in weekly audits (check cache hit rate, review synthetic vs real-feed deviation, run cluster analysis).

Risk 4 surfaces immediately — every session closeout report includes the commit hash; if it doesn't, the session is blocking merge.

Risk 5 surfaces in human awareness. Pay attention. If you're dreading Claude Code sessions by week 3, something's wrong.

Risks 6-7 surface in PR review. Every PR gets a once-over for ADR references and paper citations.

Risks 8-14 surface through CI, manual verification scripts, and the amendments log.

Risk 15 is a contingency — respond when it arrives.

### Rollback plans per session

Each session is a PR. Each PR can be reverted. If Session 2A's multi-feed infrastructure turns out to be the wrong design after Session 2B tries to use it, the rollback is: revert 2A's merge commit, re-design, re-implement.

The more expensive rollback is strategy-session-level: if Session 2D ships 15 rates strategies and review later shows the rates architecture was wrong, the strategies themselves may be reusable but the wiring needs redo. Mitigation: per-session adversarial review catches this before merge.

The most expensive rollback is Phase-level: Phase 2 is the wrong scope, drop back to Phase 1 and re-plan Phase 2. Unlikely given the groundwork, but named as a possibility.

---

## Section 9 — Phase 2 → Phase 3 Transition

### Phase 2 exit criteria

Phase 2 is "done" when all of these are true:

- 125 strategies merged to main (60 Phase 1 + 65 Phase 2)
- Each new strategy has the full per-strategy contract (strategy.py, config.yaml, paper.md with DOI, known_failures.md, README.md, tests/test_unit.py, tests/test_integration.py, benchmark_results_synthetic.json, benchmark_results_real.json where applicable)
- v0.2.0 tagged via GitHub UI, marked pre-release
- verify-install.yml green on the v0.2.0 tag (all 6 matrix jobs)
- Local PowerShell verification (cache-busted, via `scripts/verify_release_windows.ps1`) green on v0.2.0 tag
- CHANGELOG.md reflects v0.1.1 → v0.2.0 delta honestly, including any strategies dropped from the original 65 manifest
- docs/ updated: phase-2-master-plan.md marked complete with session-status table, deviations.md current with Phase 2 synthetic-data sections, benchmark_notes.md current with Phase 2 cluster analysis, 5 new ADRs committed and numbered 003-007
- Monthly audits (weeks 2, 4, 6, 8) completed and filed under `docs/audits/`
- `docs/phase-2-amendments.md` exists and captures any in-flight scope changes honestly
- The cluster analysis from Session 2H has been reviewed; any suspected duplicates either documented or resolved

If any of these is missing, Phase 2 is not done. Don't tag v0.2.0 until all apply.

### What Phase 3 picks up

Phase 3 is scoped at a high level here — the full Phase 3 master plan will be produced at the start of Phase 3, after Phase 2's retrospective reveals what changed under contact with reality.

**Real Polygon integration.** Wire up the placeholder adapter from ADR-004. Polygon API key needed for development; tests mocked for CI. All 20 Phase 2 options strategies get re-benchmarked against real chains; diffs from synthetic-only get documented in `docs/benchmark_notes.md`.

**C# LEAN bridge.** The fourth engine, joining internal, vectorbt, and backtrader. Targets `alphakit-bridges`. Enables users to run alphakit strategies on LEAN's infrastructure for live paper trading.

**Strategy count push to ~200 total.** 75 new strategies across: more rates (curve trades, credit, sovereign CDS), more commodity (softs, energy term structure, metal spreads), more options (real Polygon-based strategies that couldn't work with synthetic chains), crypto strategies (CCXT adapter goes from deferred to shipped).

**Alt-data exploration.** News sentiment (NewsAPI, Tiingo), macro surprise indices (Citi Economic Surprise), Google Trends signals. May slip to Phase 4 depending on Phase 3 scope pressure.

**Portfolio construction layer.** HRP clustering, risk parity weighting, Kelly sizing, minimum-volatility optimization as cross-cutting utilities that any strategy can opt into. Lives in `alphakit-core/portfolio/` with tests.

### Handoff artifacts produced at Phase 2 closeout

Session 2H's final commits include three artifacts that Phase 3 will need:

1. **Phase 2 retrospective section** in the Phase 3 master plan. Not written in Phase 2; the Phase 3 plan's Section 0 will mirror this plan's Section 0, with Phase 2 replacing Phase 1. Captures what shipped, what broke, what changed.

2. **Open questions document** (`docs/phase-2-open-questions.md`). During Phase 2 implementation, edge cases will arise that don't block shipping but deserve an answer in Phase 3: how do we handle daylight-saving transitions in options expiry dates, what's the right cache TTL for intraday data, should alphakit-strategies-* sub-packages consolidate into one package, etc. List them as they come up.

3. **Phase 3 scope ticket** — a single GitHub issue titled "Phase 3 scope" that aggregates the "Out of scope" commitments from Phase 2, the Phase 2 amendments, and the open questions. Serves as the seed document for Phase 3's master plan.

### v0.2.0 release notes template

The v0.2.0 release ships silently — tagged, release notes written, but no LinkedIn / HN / Reddit / Twitter announcement. The release notes sit on GitHub as the authoritative record of what shipped. When v1.0 lands, the v0.2.0 notes are part of the "what we built along the way" narrative.

Template below. Fill in concrete numbers at Session 2H.

````markdown
## v0.2.0 — Multi-feed architecture + 65 new strategies

**Silent pre-release.** Part of the quiet build toward v1.0 (500+ strategies, all asset classes, production-grade).

### New families

- **Rates (15):** Real FRED yield curves. Bond TSMOM, curve trades (2s10s, 2s5s10s butterfly), carry-and-roll, breakeven inflation, yield curve PCA, Fed funds surprise, G10 bond carry, credit spread momentum, swap spread, FRA-OIS, global inflation momentum.
- **Commodity (15):** Real yfinance futures + CFTC COT + EIA inventory. Backwardation carry, contango short, seasonality, weather premium, speculator positioning, crack/crush spreads, metals momentum, cross-commodity carry, WTI-Brent, Henry Hub-TTF, inventory surprise, calendar spreads, coffee weather, cross-commodity TSMOM.
- **Options (20):** Synthetic Black-Scholes chains (see docs/feeds/synthetic-options.md). Covered call, CSP, wheel, iron condor, strangle, delta-hedged straddle, VIX term structure, put skew premium, calendar/diagonal spreads, BXM replication, pin risk, weekly theta, earnings vol crush, VRP synthetic, gamma scalping, skew reversal, ratio spread, dispersion proxy.
- **Macro/GTAA (15):** Real FRED economic data + multi-asset ETFs. Permanent portfolio, risk parity, min-variance, max diversification, economic regime, CAPE country rotation, dollar strength, yield curve regime, recession probability, Fed policy, inflation regime, global macro momentum, dual momentum GTAA, 5-asset tactical, commodity overlay.

### New architecture

- **Multi-feed data layer** (ADR-003): FeedRegistry with name-based lookup, DataFeedProtocol.fetch_chain extension for options feeds.
- **Free-feed adapters:** FRED (treasury yields, CPI, Fed funds), yfinance-futures (continuous commodity contracts), EIA (energy inventory), CFTC COT (weekly positioning).
- **Polygon placeholder** (ADR-004): Adapter shell ready for Phase 3 real integration.
- **Synthetic options chains** (ADR-005): Black-Scholes + realized-vol IV. Default for Phase 2 options strategies.
- **Disk-backed feed cache** (ADR-006): parquet with TTL.
- **Rate-limit coordinator** (ADR-007): per-feed token bucket.

### Deprecated / superseded

- ADR-001 (carry-family data gap) is superseded by ADR-003.
- Phase 1 carry-family proxy strategies remain as-is; their upgrade is out-of-scope for Phase 2.

### Known limitations

See `docs/deviations.md` for full honest accounting. Highlights:
- All 20 options strategies backtest on synthetic Black-Scholes chains, not real market data. Upgrade path via Polygon adapter in Phase 3.
- FRED requires free API key; EIA requires free API key. yfinance and CFTC are keyless.
- Synthetic chains have no IV skew and no bid-ask spread. Strategies dependent on skew (put_skew_premium, skew_reversal, dispersion_trade_proxy) backtest against approximations.
- Any Phase 2 strategies that clustered at ρ>0.95 on synthetic data are documented in `docs/benchmark_notes.md` under "Known Phase 2 clusters."

### Install

Same script-based install from git tag as v0.1.1:

```bash
curl -sSL https://raw.githubusercontent.com/ankitjha67/alphakit/v0.2.0/scripts/install_from_git.sh | bash
```

Or per-package (now 13 sub-packages). See README.md.

### Roadmap

v0.3.0 (Phase 3): Real Polygon integration, C# LEAN bridge, CCXT crypto feed, ~200 total strategies.
v1.0.0 target: 500+ strategies, all asset classes, full production grade.
````

---

## Section 10 — Papers Referenced in Phase 2

Appendix. 65 citations, DOI-linked where available, grouped by family. This appendix is produced in full during Sessions 2D-2G as each family is implemented. The canonical files are:

- `docs/papers/phase-2.bib` — BibTeX format, machine-readable, suitable for academic citation tools
- `docs/papers/phase-2.md` — Human-readable table, one row per strategy: slug | paper | DOI | feed | notes

**Quality bar.** Every Phase 2 strategy's paper.md must cite a real, resolvable paper. Acceptable citation types, in order of preference:

1. **Peer-reviewed journal article with DOI.** E.g., Moskowitz/Ooi/Pedersen "Time Series Momentum" (Journal of Financial Economics, 2012), DOI 10.1016/j.jfineco.2011.11.003.
2. **arXiv preprint with stable arxiv URL.** E.g., https://arxiv.org/abs/2201.12345.
3. **Working paper from a recognized institution with stable URL.** E.g., NBER working paper, SSRN with DOI.
4. **Book chapter with ISBN and page range.** E.g., Ilmanen "Expected Returns" 2011, ISBN 978-1-119-99072-7, Ch 12.
5. **Industry whitepaper from a named author at a recognized firm.** E.g., AQR Capital Management whitepaper authored and dated.

**Unacceptable:**
- Blog posts without peer review
- Podcasts, YouTube videos, conference talks without companion paper
- "Personal communication" or undocumented claims
- Strategies described only in trading forums or social media

If a strategy's only source is unacceptable-category, drop the strategy from Phase 2 rather than ship without citation. The honesty bar is load-bearing for alphakit's competitive positioning.

**Verification procedure.** Session 2H includes a step to spot-check 10 random strategies' citations. For each: resolve the DOI, verify the paper exists, verify the paper actually describes the strategy. If 2 or more of 10 fail this check, audit all 65 before tagging.

---

## Plan ownership and revision

**Author (initial):** Claude, coordinating with Ankit Jha.

**Owner during execution:** Ankit Jha. Final decisions on ADRs, scope cuts, timeline adjustments. Claude Code sessions implement; Ankit approves merges, tags releases, and writes the amendments log.

**Plan lives at:** `docs/phase-2-master-plan.md` in the alphakit repo. Committed atomically as the first action of Phase 2 (before Session 2A starts).

**Amendments log:** `docs/phase-2-amendments.md`. Track every scope change, timeline shift, strategy substitution, or decision reversal with date and rationale. Silent build demands explicit records because external discussion doesn't exist to self-correct. Template for an amendment entry:

````markdown
## 2026-04-28 — Dropped strategy fra_ois_spread from rates manifest

Context: No citable paper found for FRA-OIS spread as a systematic strategy at the level of rigor alphakit requires. McAndrews/Sarkar/Wang 2008 describes FRA-OIS as a stress indicator but doesn't formalize it as a tradable strategy.

Options:
- Drop from Phase 2 manifest (chosen)
- Substitute: sonia_ois_mean_rev (UK instead of US, same concept, better paper trail)
- Keep but downgrade to `_proxy` suffix

Decision: Drop. Rates family ships with 14 strategies, not 15. Total Phase 2 count becomes 64, not 65. Release notes update accordingly.

Impact: No ADR change needed. Phase 2 exit criteria updated to "64 strategies" instead of "65".
````

**Status tracking table:** A table at the top of this file (to be added when Session 2A lands) tracks each session's status:

| Session | Target date | Status | Commit hash on main | PR | Notes |
|---------|-------------|--------|---------------------|-----|-------|
| 2A | Week 1 | Not started | — | — | Data architecture foundation |
| 2B | Week 2 | Not started | — | — | Four free-feed adapters |
| 2C | Week 3 | Not started | — | — | Polygon placeholder + synthetic chains |
| 2D | Week 4 | Not started | — | — | Rates family (15) |
| 2E | Week 5 | Not started | — | — | Commodity family (15) |
| 2F | Week 6 | Not started | — | — | Options family (20) |
| 2G | Week 7 | Not started | — | — | Macro/GTAA family (15) |
| 2H | Week 8 | Not started | — | — | Closeout + v0.2.0 release |

Each session's closeout updates its row. By Session 2H, every row has a green Status and a commit hash.

**Scope freeze.** This master plan is the scope of Phase 2. Changes to scope require an amendment entry in `docs/phase-2-amendments.md`. No scope changes land silently.

---

**End of Phase 2 Master Plan.**
