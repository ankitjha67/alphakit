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
