# Phase 2 — remaining session kickoffs (2L → 2N, then Phase 2 CLOSED)

> Every placeholder resolved. Each `## Session` block below is pasteable
> as-is. Prepend §3 Standing Discipline from
> [`docs/roadmap-phase-3-to-v1.md`](../roadmap-phase-3-to-v1.md) to each;
> prepend §2 Definition of Done only to 2L (the only remaining session that
> creates strategies).

**Remaining Phase 2 arc:**

| Session | Scope | Tag | Strategy count |
|---|---|---|---|
| **2L** *(in flight, paused at S2L-0)* | Macro covariance universe expansion | `v0.2.3` | 109 → 112 |
| **2M** | Supply-chain pinning + tooling hygiene | `v0.2.4` | 112 |
| **2N** | Prediction recalibration + Phase 2 retrospective + Phase 3 master plan | `v0.2.5` | 112 |

After 2N, Phase 2 is closed and Session 3A opens Phase 3.

---

## Session 2L — status: IN FLIGHT, paused

Kicked off already. Currently paused at the end of S2L-0 awaiting:

1. The output of `uv run --with yfinance python scripts/audit_etf_universe.py`
2. Your universe decision: **(a)** 10-asset incl. DBC, or **(b)** 9-asset ex-DBC
3. If (b), confirmation that the naming suffix is `_9asset`

Landed so far on `claude/2l-covariance-universe-expansion`:

- `db782f7` — carry-in verification (v0.2.2 verify-install 6/6 green,
  per-cell) + `scripts/audit_etf_universe.py`
- `1a82657` — the Phase 3 → v1.0 roadmap

S2L-1 through S2L-4 are specified in the original 2L kickoff and do not need
restating. **Nothing below starts until 2L tags `v0.2.3`.**

---

## Session 2M kickoff

```
Session 2M kickoff. Scope: supply-chain action pinning + three tooling-debt
items carried from the 2K closeout §10 backlog. No strategy changes.
Branch: claude/2m-supply-chain-and-tooling

[Paste §3 Standing Discipline from docs/roadmap-phase-3-to-v1.md]
(Definition of Done not needed — this session creates no strategies.)

Context: v0.2.3 shipped 3 new covariance variants. This session clears the
non-strategy debt so Phase 2 closes without carrying tooling rot into
Phase 3. Four items, all independently landable.

S2M-0: Carry-in + action-pin audit
- Verify v0.2.3's verify-install is 6/6 green via GitHub MCP
  (mcp__github__actions_list, method=list_workflow_jobs on the tag's run).
  If red, STOP and report before any 2M work.
- Write scripts/audit_action_pins.py. Not a data-substrate probe, so it
  mirrors audit_fred_rates_series.py in SHAPE rather than mechanism:
  per-candidate probe, machine-checkable classifier, summary table,
  fail-loud on error. For each `uses:` ref across .github/workflows/*:
    * current ref and its class: floating-major / floating-minor /
      immutable-tag / full-SHA
    * whether the publisher still publishes floating majors (setup-uv
      stopped at v8 — that is the whole reason this session exists)
    * latest available release, via the GitHub releases API
    * the resolved commit SHA for the current ref, so a SHA pin is one
      copy-paste away
    * first-party (actions/*, astral-sh/*) vs third-party — third-party
      carries materially higher supply-chain risk
  Known inventory to classify (6 refs, all currently floating):
    actions/checkout@v5, actions/setup-python@v6,
    actions/upload-artifact@v4, actions/github-script@v7,
    astral-sh/setup-uv@v7, peaceiris/actions-gh-pages@v4
- I run it locally and paste output.
- PAUSE for my pinning-policy decision. Options:
    (a) Full commit-SHA pins everywhere. Strongest guarantee; requires
        Dependabot or the pins rot silently and invisibly.
    (b) Immutable release tags where the publisher offers them, floating
        elsewhere. Lighter; weaker guarantee; inconsistent by construction.
    (c) SHA-pin third-party only (peaceiris), immutable/floating for
        first-party. Risk-weighted middle.
  Do not start S2M-1 until I confirm.

S2M-1: setup-uv v8 + pinning policy applied
- Bump astral-sh/setup-uv@v7 -> @v8.x (immutable — v8 stopped publishing
  floating majors, which is why 2K held at v7).
- Apply the chosen policy across all 6 refs in all 5 workflow files.
- Write docs/adr/008-github-action-pinning-policy.md recording the decision,
  the rationale, and the rot-mitigation (Dependabot config if SHAs chosen).
- If SHAs: add .github/dependabot.yml for the github-actions ecosystem, or
  the pins go stale and the policy becomes worse than floating.
- Gates: uv sync --extra dev && uv run pytest (NO path arg).
- CI must go green on the bump before S2M-2 starts — a broken workflow
  blocks every later session.

S2M-2: Doc-consistency linter
- Closes the 2K closeout §8(g) finding: CodeRabbit caught prose referencing
  renamed identifiers 7 times across PRs #22/#23.
- Implement as a pytest test in tests/, NOT a standalone tool — then it
  rides the existing gate and cannot be forgotten.
- Deliberately narrow scope, catching only the observed bug class:
    * every feed name appearing in docs/**/*.md and in package docstrings
      must exist in FeedRegistry.list()
    * every strategy slug appearing in docs/**/*.md must exist in the
      discovered manifest
  Extract candidates by regex against the known name-shapes (feed names are
  lowercase-hyphenated and appear in backticks; slugs are
  lowercase_underscored). False positives are the failure mode — if prose
  triggers noise, NARROW the pattern rather than adding heuristics.
- Seed it by confirming it would have caught the S2K-1 "cftc-cot" drift:
  temporarily reintroduce one stale ref, watch the test fail, revert.

S2M-3: Code-aware cache keys
- Closes the S2J §8(e) finding: ~/.alphakit/cache survived uv sync
  --reinstall and silently overrode the S2J-2.5 adapter fix on a keyed run.
  Cache key is (feed_name, symbols, start, end, frequency) — no code
  component, so it does NOT invalidate when adapter code changes.
- Design constraint that makes this non-trivial: the key must change when
  the ADAPTER's parsing/normalisation logic changes, and must NOT change on
  unrelated repo edits, or every commit nukes every user's cache.
- Evaluate at least: (i) hash of the adapter module's source via
  inspect.getsource, (ii) an explicit _CACHE_SCHEMA_VERSION constant per
  adapter bumped by hand, (iii) hash of the installed alphakit-data version.
  (i) is automatic but churns on comment edits; (ii) is stable but relies on
  discipline; (iii) is coarse. Recommend with reasoning, then build.
- Migration: existing cache entries must not crash on read. Old-format keys
  simply miss and repopulate.
- Tests: same-code repeated fetch hits cache; simulated adapter-code change
  misses; corrupt/legacy entry degrades to a miss, not a crash.

S2M-4: Windows CI leg — ONLY IF 2L deferred it
- If 2L's S2L-3 stretch landed windows-latest, skip this entirely.
- If deferred: add windows-latest + py3.12 to test.yml's matrix (one Python
  version to bound job count).
- Institutionalises the S2K-3.5 lesson — the cache-sentinel bug existed
  precisely because CI never ran Windows. The now-fixed cross-platform cache
  tests are the first validation.
- Expected failure classes: path separators, line endings, tempfile
  semantics, Path() normalisation.
- TIME-BOX: >3 distinct failure classes or >3h, STOP, document in the
  closeout, defer. verify-install stays Linux+macOS this session.

S2M-5: Docs + closeout + v0.2.4 tag
- Amendment only if a convention changed (the pinning policy is an ADR, not
  an amendment; a cache-key format change IS an amendment).
- CHANGELOG [0.2.4]; docs/sessions/2m-closeout.md mirroring 2k structure.
- Drafts for my review BEFORE the docs commit.
- PR review -> squash-merge -> v0.2.4 tag on squash SHA.
  Tag SHA == CI-target SHA (Session 2H §7 footgun guard).
  Tag push is Ankit-side — sandbox gets HTTP 403 on tag refs.

Reporting cadence: after each S2M-n, plus a pause at the S2M-0 decision.
Estimate: 5-7h, +2-3h if S2M-4 activates.
```

---

## Session 2N kickoff

```
Session 2N kickoff. Scope: mechanism-derived prediction recalibration across
all four real-feed families, Phase 2 retrospective, and the Phase 3 master
plan. Final Phase 2 session. Branch: claude/2n-recalibration-and-phase2-close

[Paste §3 Standing Discipline from docs/roadmap-phase-3-to-v1.md]
(Definition of Done not needed — this session creates no strategies.)

Context: the 32x32 cluster from 2L scored roughly 9-12 of ~40 documented
pairs inside their predicted bands. The 2K closeout §8(h) established that
the four families miss in four DIFFERENT directions for four DIFFERENT
mechanisms. This session acts on that, then closes Phase 2.

S2N-0: Carry-in + prediction inventory
- Verify v0.2.4's verify-install is 6/6 green via GitHub MCP. If red, STOP.
- No substrate audit — this is doc work. Instead write
  scripts/audit_predictions.py: for every in-cluster pair, emit
  (family, strategy_a, strategy_b, a_priori_band, observed_rho,
  in_range, miss_direction, source_file, source_line).
  Machine-checkable classifier: miss_direction in
  {IN_RANGE, OVER, UNDER, WRONG_SIGN}. Reads the committed cluster output
  plus the _PREDICTED_*_RHO tables; no network, so it runs in-sandbox.
- Scope boundary, stated explicitly and NOT exceeded: only the in-cluster
  pairs (~40 of the 202 rho-prediction lines across 49 known_failures.md
  files). The other ~160 cover strategies with no real-feed coverage and
  stay a priori until their substrate lands in Phase 3.
- PAUSE for my review of the inventory before any file is edited.

S2N-1: Mechanism-derived recalibration
- METHODOLOGICAL GUARDRAIL — this is the entire point of the session.
  Setting each prediction to its observed rho would score ~40/40 and mean
  NOTHING. That is curve-fitting the hypothesis to the answer. Per OUT pair:
    1. Identify the MECHANISM explaining the observed value. Several are
       already derived in 2k-closeout §5: TLT-duration dominance across
       rates, small-N solver convergence in macro, binary-tail mutual
       exclusion in steepener/flattener, risk-parity weighting dilution in
       commodity.
    2. Re-derive the band FROM THE MECHANISM, not from the number. If the
       mechanism implies 0.6-0.8 and observed is 0.88, write 0.6-0.8.
    3. Where no mechanism explains the gap, write
       "observed rho = X, mechanism unexplained". An honest unknown beats
       an invented rationalisation.
- New two-tier doc convention, needs an amendment: each known_failures.md §6
  entry splits into A PRIORI (preserved verbatim — deleting it destroys the
  record of what we got wrong) and CALIBRATED (post-cluster, mechanism
  cited). Auditability is the whole reason to keep both.
- Update the _PREDICTED_*_RHO tables in cluster_analysis.py to the
  calibrated bands.
- SUCCESS CRITERION IS NOT "40/40 in range". It is: every OUT pair has
  either a mechanism-derived band or an explicit unexplained marker. Expect
  the post-recalibration score to land well short of 40/40 — that is
  correct, and a score near 40/40 is evidence the guardrail was violated.

S2N-2: Cluster re-run to score the recalibration
- Extend cluster_analysis.py AND tests/test_cluster_analysis.py in the SAME
  commit — the prediction-coverage test pins cluster scope and broke CI in
  S2K-4 (753d388).
- I run the keyed cluster:
  uv run --with fredapi --with yfinance --extra dev python scripts/cluster_analysis.py --feed real
  (cache-clear + uv sync --reinstall first)
- Evaluate honestly: did mechanism-derived bands beat the a priori hit rate?
  Report BOTH numbers. If they did not improve, that is a finding about the
  mechanisms being wrong, and it goes in the closeout as such.

S2N-3: Phase 2 retrospective + Phase 3 master plan
- docs/phase-3-master-plan.md, mirroring the structure of
  phase-2-master-plan.md: mission/non-goals, ADRs for the new substrates,
  data-layer design, per-session handoffs (3A-3K from
  docs/roadmap-phase-3-to-v1.md, expanded to full session specs), strategy
  manifest, benchmark plan, silent-build discipline.
- Phase 2 retrospective in the Section 0 style: what shipped, what broke and
  how we caught it, patterns that worked, patterns that didn't. Draw on the
  full amendment history (44 entries) and every session closeout 2A-2N.
- Resolve the three plan-changing decisions flagged in the roadmap §5, or
  record explicitly that they are deferred to 3A/3C/3E:
    1. fundamentals substrate (gates 12 strategies)
    2. paid-feed policy (gates 20 strategies)
    3. ADR-001 carry resolution (deferred since Phase 1)

S2N-4: Docs + closeout + v0.2.5 tag + Phase 2 CLOSED
- Amendment: the two-tier prediction convention from S2N-1.
- CHANGELOG [0.2.5].
- docs/sessions/2n-closeout.md — and because this closes the phase, it also
  carries the Phase 2 final scorecard: 112 strategies, real-feed coverage,
  families shipped, strategies dropped with reasons, amendments issued,
  substrate blockers documented.
- Drafts for my review BEFORE the docs commit.
- PR review -> squash-merge -> v0.2.5 tag on squash SHA.
  Tag SHA == CI-target SHA. Tag push is Ankit-side.

Reporting cadence: after each S2N-n, plus a pause at S2N-0.
Estimate: 7-9h. The retrospective is the long pole, not the recalibration.
```

---

## What "Phase 2 complete" means

At `v0.2.5`, all of the following are true:

- **112 strategies** across 9 families, every one carrying real citations,
  known-failure analysis, tests, and a runner-produced benchmark.
- **Real-feed coverage 32/112 (28.6%)**, with every one of the remaining 80
  attributed to a *named substrate blocker* and a documented Phase 3
  re-instatement path — not to unfinished work.
- **Cluster analysis at 32×32** with mechanism-derived predictions and an
  honest scorecard of where the predictions still miss.
- **Supply-chain posture decided** and recorded in an ADR.
- **Three tooling-debt items closed**: doc-consistency linting, code-aware
  cache keys, Windows CI.
- **`docs/phase-3-master-plan.md` written**, so Session 3A opens against a
  plan rather than a blank page.

The honest caveat worth stating plainly at close: **28.6% real-feed means 71%
of the catalogue is still validated only against synthetic fixtures.** Phase 2
built the machinery to fix that and proved it on four families. Phase 3 is
where the number moves.
