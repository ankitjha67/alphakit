# Phase 2 amendments

This log records deliberate deviations from `docs/phase-2-master-plan.md`
discovered during implementation. The plan remains the canonical
specification; entries here explain *why* a session diverged and
document the runtime/contract-preserving resolution, so future sessions
and reviewers can reconcile code with the plan.

Each entry is dated and tagged with the originating session.

---

## 2026-04-17 — Session 2A: `raise_chain_not_supported` helper instead of Protocol default body

**Context.** The plan's Section 3 shows `DataFeedProtocol.fetch_chain`
with a default-raising body (`raise NotImplementedError`). Under
`mypy --strict`, this pattern causes every `DataFeedProtocol`
implementer to be flagged as abstract, forcing explicit overrides in
every adapter.

**Resolution.** The raise moved from the Protocol body into an
exported helper
`raise_chain_not_supported(feed_name: str) -> NoReturn` in
`alphakit.core.protocols`. Adapters that don't support chains call
this helper in their `fetch_chain` implementation. Runtime behaviour
is identical to the plan; mypy strict is now clean.

ADR-003 updated inline to document the helper pattern.

**Impact.** No scope change. No exit criteria change. Slight syntactic
shift from "inherit the raise" to "call the raise helper."

---

## 2026-04-17 — Issue #1 scope expanded: benchmark runner mutates tracked JSON files

Context: During Phase 2 Session 2A's working-tree cleanup, pytest
was observed modifying packages/alphakit-strategies-*/alphakit/
strategies/*/*/benchmark_results.json in-place. These files are
tracked in git; running the test suite leaves git status dirty.
Earlier Issue #1 (filed pre-v0.1.1) identified .json.bak pollution;
the scope is broader — the real benchmark_results.json files
themselves get touched.

Current workaround: don't commit the modified files. Tests don't
fail on the dirty state since the modifications preserve valid
JSON and benchmark content.

Impact on Phase 2: every session will observe dirty trees after
running pytest. Each session must explicitly git-stash or git-restore
these files before commit to avoid accidentally polluting PRs with
benchmark regeneration noise.

Proper fix deferred: benchmark runner should accept a benchmark_root
parameter (default=the strategy dir for production runs, a tmp_path
in tests). Scoped to Session 2H as part of the benchmark runner
refactor.

No scope change to Session 2A or any intermediate session. Annotation
only.

---

## 2026-04-17 — Follow-up: shared adapter contract test for offline/rate-limit/cache

Context: Session 2A's infrastructure (FeedRegistry, FeedCache,
rate_limit, offline) is verified in isolation and exercised by
the migrated yfinance adapter. But every future feed adapter must
independently implement the same contract (register at import,
respect ALPHAKIT_OFFLINE, use @cached_feed + ratelimit_acquire).

Risk: drift. Session 2B adds 4 adapters; one could forget to check
ALPHAKIT_OFFLINE and nobody would notice until a user without
network access tried to run tests.

Resolution: Session 2B will add a shared parametrized contract
test in packages/alphakit-data/tests/test_adapter_contract.py.
For each registered adapter, the test verifies:
  - Adapter is discoverable via FeedRegistry.get(name)
  - Adapter.fetch respects ALPHAKIT_OFFLINE=1 (routes to fixtures
    or raises OfflineModeError)
  - Adapter.fetch uses @cached_feed (verified by inspecting method
    attributes)
  - Adapter.fetch calls ratelimit_acquire (verified via
    monkeypatch assertion)
  - Adapter.fetch_chain either implements or calls
    raise_chain_not_supported

Impact: adds ~10-15 tests (parametrized across all registered
adapters). No scope change; architectural gap filled as part of
2B's implementation.

---

## 2026-04-17 — Session 2B: mypy overrides landed per-adapter, not bulk

Context: Session 2B's plan called for a single pyproject.toml update
in Commit 7 to add fredapi and requests to mypy's
ignore_missing_imports list. In practice each mypy override was added
in the commit that introduced the adapter using it (fredapi in the
FRED commit, requests in the EIA commit), because mypy --strict must
pass in isolation on every intermediate commit, not just the tip of
the branch.

No scope change. Commit 7 still covers the remaining pyproject work
(optional-deps for alphakit-data, types-requests for dev).

Pattern to continue: mypy overrides land in the commit that introduces
them, not in a trailing "enables" commit.

---

## 2026-04-17 — Session 2B: malformed-response regression tests deferred

Context: Session 2B's adversarial review question (b) identified that
while all four adapters (FRED, yfinance-futures, EIA, CFTC COT)
correctly propagate exceptions from malformed upstream responses
(HTML-for-JSON, HTTP 500, corrupt ZIP, empty DataFrame), parametrized
regression tests with known-bad payloads do not exist.

Decision: Defer to Phase 3.

Rationale:
- Current behavior is correct — errors propagate with library-native
  messages, do not get swallowed or silently coerced.
- Explicit empty-data handling IS tested (EIA empty response
  test_fetch_handles_empty_response_data, CFTC market-code filter
  test_fetch_filters_by_market_code).
- Phase 3 scope naturally includes real Polygon integration plus
  broader adapter hardening.
- Blocking Session 2C on a ~20-test addition costs roughly half a
  day without proportional risk reduction.

Phase 3 scope addition: parametrized regression tests across all
registered adapters covering:
- HTML-for-JSON returns (FRED via fredapi, EIA via requests)
- HTTP error codes including 429, 500, 503 (EIA via requests)
- Corrupt ZIP payloads (CFTC COT via urllib + zipfile)
- Empty upstream responses (yfinance, yfinance-futures)
- Schema mismatches (adapter expects column X, upstream returns Y)

No Phase 2 scope change. Session 2C unblocked.
