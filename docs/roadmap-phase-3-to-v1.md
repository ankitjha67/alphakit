# alphakit roadmap — Phase 3 through v1.0

> Status as of `v0.2.2` (`659c64b`), Session 2L in flight.
> This document is the session-by-session plan for everything still
> outstanding. Each `### Session` block is self-contained and designed to be
> pasted directly into Claude Code as a kickoff.

---

## 0. Where things actually stand

**109 strategies shipped**, across two phases:

| Phase | Families | Count |
|---|---|---|
| Phase 1 | trend 15, meanrev 15, value 10, carry 10, volatility 10 | **60** |
| Phase 2 | rates 13, commodity 10, options 15, macro 11 | **49** |

**Real-feed coverage: 29/109 (26.6%).** The other 80 are `synthetic-fixture`:

| Block | Count | Substrate blocker |
|---|---|---|
| Phase-1 trend | 15 | none — yfinance ETF, ready to convert |
| Phase-1 meanrev | 15 | none — yfinance equities; pairs need a declared universe |
| Phase-1 volatility (non-proxy) | 5 | partial — VIX term structure needs futures curve |
| Phase-1 volatility (`_proxy`) | 5 | real option chains (Polygon) |
| Phase-1 value | 10 | **fundamentals feed — no adapter exists** |
| Phase-1 carry | 10 | **FX forwards / futures curves / crypto funding — ADR-001** |
| Phase-2 options | 15 | real option chains (Polygon) |
| Phase-2 commodity | 3 | back-month futures (2026-05-31 amendment) |
| Phase-2 rates | 2 | 10Y USD swap rate + JP CPI (2026-05-31 amendment) |

**Infrastructure state:**

- Feeds registered: `yfinance`, `yfinance-futures`, `fred`, `eia`, `cftc-cot`, `cftc-cot-wide`, `synthetic-options`, `polygon` (stub, ADR-004).
- Bridges: `vectorbt` (production), `backtrader` (working), `lean` (stub).
- 7 `_proxy` strategies carry Phase-1 naming debt (ADR-002): 2 value, 5 volatility.
- 16 strategies were **dropped** during Phase 2 — no citable systematic-strategy paper, or the substrate could not represent the mechanic. That filter is why the shipped set is not padding.

---

## 1. Read this before pasting anything

You asked for something you can paste once and have everything built. I'm giving you the complete plan, but I'm not going to pretend it collapses into one run, because the evidence in this repo says it doesn't:

- Phase 2 shipped 49 strategies across **12 sessions** (2A–2L).
- Every strategy carries `strategy.py`, `config.yaml`, `paper.md` with real DOIs, `known_failures.md` with regime analysis, `README.md`, unit + integration tests, and a `benchmark_results.json`.
- **16 candidate strategies were dropped** mid-phase because per-strategy literature research found no citable anchor. That research is exactly what a single mega-run would skip — and skipping it is how you get the shallow placeholder set you said you don't want.

So the plan below is chunked **because chunking is the mechanism that prevents shallowness**, not because of tooling limits. Paste one `### Session` block at a time. Section 2's Definition of Done is the anti-shallow contract; every session block references it.

---

## 2. Definition of Done — per strategy (the anti-placeholder contract)

**Paste this block into any session that creates or converts strategies.**

A strategy is not done until every item below is true. A strategy that cannot
satisfy items 1–3 must be **dropped with an amendment entry**, not shipped as a
stub.

1. **Citable anchor.** A named foundational paper *and* a primary methodology
   paper, each with a resolvable DOI, recorded in `paper.md`. "Folk wisdom",
   "widely known", or a blog link is grounds for a drop — see the Session 2E
   and 2F drop entries in `docs/phase-2-amendments.md` for the precedent.
2. **Mechanism differentiation.** `paper.md` states explicitly how this
   strategy differs from its nearest siblings by *signal type*, not by
   parameter value. Two strategies differing only in a lookback constant are
   one strategy.
3. **Substrate honesty.** The data the methodology requires is actually
   obtainable on a feed the project has. If it isn't, the strategy is deferred
   with an amendment naming the missing substrate and the re-instatement path.
   Never fabricate a proxy series to make a strategy runnable.
4. **`generate_signals` implements the published rule** — not a simplified
   gesture at it. Input validation: DataFrame type, DatetimeIndex, column
   count/naming contract, strictly-positive prices where the bridge requires
   it. Warm-up periods return zero weights rather than NaN.
5. **`known_failures.md`** with: named regimes where the strategy loses money
   and why; a regime-performance reference table; and a §"Cluster correlation"
   section giving predicted ρ bands against named siblings, **written before
   any real-feed run**.
6. **Tests**: unit tests for the signal logic and every validation branch;
   an integration test through `vectorbt_bridge.run`. Match the conventions of
   the family's existing tests.
7. **`config.yaml`** with a real universe (actual tickers/series IDs), signal
   parameters, `rebalance` cadence, and a `meta` block carrying both DOIs.
8. **`benchmark_results.json`** produced by `BenchmarkRunner`, with a correct
   `data_source` stamp. Never hand-edit a benchmark file.
9. **Gates green**: `uv sync --extra dev` then `uv run ruff check .`,
   `uv run ruff format --check .`, `uv run mypy --strict packages/`,
   `uv run pytest` (**no path argument** — the root `tests/` directory is
   outside `packages/`; scoping the path let a breakage reach CI in S2K-4).

---

## 3. Standing discipline — prepend to every session

**Paste this block at the top of every session kickoff.**

- **Branch** `claude/<session-id>-<slug>`. Never push to `main`. Never
  `--force`. Never amend; always new commits.
- **Empirical verification before scope commitment.** Probe the real substrate
  before building against an assumption. Precedent: two of four CFTC market
  codes asserted in the S2K-1 kickoff were empirically wrong and would have
  shipped silently-wrong data.
- **Network-gated tests are mandatory pre-push** for any adapter or routing
  change: `ALPHAKIT_RUN_NETWORK_TESTS=1 uv run pytest -k real`.
- **Keyed runs are Ankit-side.** API keys never enter the sandbox, a commit, a
  doc, or chat. Claude builds against mocks; Ankit runs the keyed regen.
- **Clear `~/.alphakit/cache` between keyed runs.** The cache key has no
  code-version component, so it survives adapter changes (S2J §8(e)).
- **Honest deferral beats a fabricated proxy.** Deferring with an amendment is
  a successful outcome, not a failure.
- **Drafts for review before doc commits** — amendment, closeout, CHANGELOG.
- Silent build holds: no PyPI, no public announcement, until v1.0.

---

# Phase 3 — Real-feed completion & execution realism (`v0.3.x`)

**Goal:** take real-feed coverage from 29/109 to as close to 109/109 as the
free-and-open-source substrate allows, and make the deferred blocks either
shipped or formally closed. Two new adapters and one new bridge.

**Sessions 3A → 3K.** Order is chosen so that substrate-easy work banks
progress early and substrate-hard decisions come after the adapters that
unblock them exist.

### Session 3A — Phase-1 trend family real-feed (15 strategies)

- **Scope:** convert all 15 trend strategies from `synthetic-fixture` to
  `yfinance-real`. No new strategies.
- **Substrate:** `yfinance` only. Universes are already real ETF baskets
  (SPY/EFA/EEM/AGG/GLD/DBC and similar) — verify each `config.yaml` universe
  is complete-rows viable over 2005–2025 before regen.
- **First task:** extend `scripts/audit_etf_universe.py` to cover every ticker
  referenced across the 15 configs; report inception dates and the
  complete-rows intersection per strategy. Some universes will be
  inception-bound like the covariance trio was — establish that up front.
- **Wire** the trend family into `regenerate_benchmarks.py` as a new tier.
- **Deliverables:** 15 regenerated benchmarks, audit output in the closeout,
  amendment for any strategy whose universe cannot span the window.
- **Decision point:** for universes bound by a late-inception ticker, trim to
  the intersection or substitute the ticker? Precedent favours trimming.
- **Estimate:** 4–6h + one keyed regen.

### Session 3B — Phase-1 meanrev family real-feed (15 strategies)

- **Scope:** convert the 15 meanrev strategies.
- **Substrate:** `yfinance`. Harder than 3A: `pairs_distance`,
  `pairs_engle_granger`, `pairs_johansen`, `pairs_kalman`, and `statarb_pca`
  need a *declared* equity universe, not just an ETF basket. `crypto_basis_perp`
  needs a crypto spot+perp substrate that does not exist yet — expect a defer.
- **First task:** per-strategy substrate triage. Classify each of the 15 as
  (i) ETF-ready, (ii) needs-declared-equity-universe, (iii) blocked.
- **Decision point:** for the pairs/statarb block, what is the canonical
  equity universe — S&P 100 constituents? A fixed sector basket? This choice
  is methodologically load-bearing and must be recorded in an amendment,
  because survivorship bias enters here. Constituent lists are themselves a
  substrate the project does not have; a fixed hand-declared basket with the
  bias documented is the honest v0.3 answer.
- **Estimate:** 5–7h + one keyed regen.

### Session 3C — Fundamentals adapter (new substrate)

- **Scope:** infrastructure only. No strategy conversions.
- **Why:** the 10 value strategies need P/B, P/E, EV/EBITDA, FCF yield,
  shareholder yield, and the Piotroski/Altman component inputs. No adapter
  serves these today. This is the single largest substrate gap in the project.
- **Feasibility audit FIRST, mirroring the S2K-2 pattern.** Candidates to
  probe, in order of licence-friendliness: SEC EDGAR company facts API
  (XBRL, free, no key, authoritative); Alpha Vantage `INCOME_STATEMENT` /
  `BALANCE_SHEET` / `COMPANY_OVERVIEW` (free tier, keyed, rate-limited);
  yfinance fundamentals (free, unofficial, known-unreliable).
  Measure: coverage depth in years, restatement handling, point-in-time
  availability, and **look-ahead safety** — a fundamentals feed that serves
  restated figures without an as-reported date will silently inject
  look-ahead bias into every value backtest.
- **PAUSE for substrate decision before building the adapter.**
- **Then:** build the chosen adapter to the `DataFeedProtocol` contract, with
  the shared adapter-contract test entry, cache TTL, rate limiting, offline
  behaviour, and network-gated substrate-boundary tests.
- **Deliverables:** `docs/feeds/<name>.md`, ADR for the fundamentals substrate
  choice, audit script, adapter + tests.
- **Estimate:** 6–8h. Highest-uncertainty session in Phase 3.

### Session 3D — Phase-1 value family real-feed (10 strategies)

- **Scope:** convert the 10 value strategies onto the Session 3C adapter.
- **Includes** the two `_proxy` strategies: `altman_zscore_proxy` and
  `piotroski_fscore_proxy` graduate to `altman_zscore` and `piotroski_fscore`
  once real fundamentals land — this is the ADR-002 suffix-removal path.
  Removing the suffix requires the full component inputs, not an approximation.
- **Point-in-time discipline is the whole session.** Every value signal must
  be computed from data available *as of* the rebalance date. Record the
  reporting-lag convention in an amendment.
- **Deliverables:** 10 regenerated benchmarks, 2 strategy renames with
  deprecation shims, amendment for the lag convention.
- **Estimate:** 6–8h + one keyed regen.

### Session 3E — Polygon integration (ADR-004 wire-up)

- **Scope:** infrastructure only. Replace the Polygon stub with a real
  options-chain adapter.
- **Why:** unblocks 15 Phase-2 options strategies + 5 Phase-1 volatility
  `_proxy` strategies = 20 strategies, the second-largest blocked block.
- **Cost gate:** Polygon options chains are a paid tier. **Decide before
  building** whether the project accepts a paid feed as an optional upgrade
  (ADR-004 anticipated this) or whether options stay synthetic through v1.0.
  If paid is rejected, this session becomes "formally close the options
  real-feed path with an amendment" and Phase 3 loses two sessions.
- **If proceeding:** real `fetch_chain` returning `OptionChain`, greeks and IV
  from the provider rather than Black-Scholes-recomputed, historical chain
  support for backtests, plus the contract-test entry and network-gated tests.
- **Deliverables:** adapter, updated ADR-004, `docs/feeds/polygon.md` rewrite.
- **Estimate:** 6–8h, or 1h if the cost gate closes it.

### Session 3F — Options family real-feed (15 strategies)

- **Depends on 3E proceeding.**
- **Scope:** convert the 15 options strategies from `synthetic-options` to
  real chains.
- **Expect drops.** Several options strategies were sized to what the
  synthetic chain could represent. Against real chains with real skew, real
  OI, and real bid-ask, some will show that the synthetic benchmark was
  measuring an artifact. Treat a large benchmark delta as a finding to
  document, not a bug to suppress.
- **Estimate:** 6–8h + one keyed regen.

### Session 3G — Volatility family real-feed + `_proxy` graduation (10)

- **Depends on 3E for the 5 `_proxy` strategies.**
- **Scope:** 5 non-proxy (`vix_roll_short`, `vix_term_structure`,
  `vol_targeting`, `vrp_harvest`, `leveraged_etf_decay`) + 5 `_proxy`
  graduations (`covered_call`, `cash_secured_put`, `short_strangle`,
  `iron_condor_systematic`, `wheel_strategy` → note the 2026-05-01 amendment
  already reframed wheel to `bxmp_overlay`).
- **Substrate note:** `vix_term_structure` needs a VIX futures curve. The
  Session 2F amendment already established that back-month VIX is not on
  yfinance. Check whether the 3E provider serves it; if not, this one defers.
- **Estimate:** 5–7h + one keyed regen.

### Session 3H — Carry family: ADR-001 resolution (10 strategies)

- **Scope:** decide and act on the oldest open architectural debt in the repo.
  ADR-001 deferred carry data to "Phase 2 or Phase 4"; Phase 2 came and went.
- **Substrate triage** — the 10 split into genuinely different problems:
  - `dividend_yield`, `equity_carry`, `vol_carry_vrp` — probably reachable on
    existing feeds.
  - `bond_carry_roll`, `swap_spread_carry` — hit the same 10Y swap-rate gap
    that blocked `swap_spread_mean_rev` (2026-05-31 rates amendment).
  - `fx_carry_g10`, `fx_carry_em` — need FX forward points or interest-rate
    differentials. FRED has some policy rates; forwards are paid.
  - `repo_carry` — repo rates; FRED has SOFR but not term repo.
  - `crypto_funding_carry` — needs a crypto perp funding-rate feed (CCXT was
    named as a Phase 3 candidate in the master plan).
  - `cross_asset_carry` — composite; depends on the others.
- **Audit first, build second.** Expect this session to ship 3–5 and defer the
  rest with a superseding ADR that finally closes ADR-001.
- **Estimate:** 6–8h.

### Session 3I — Deferred-5 re-instatement attempt

- **Scope:** the 5 strategies deferred by the two 2026-05-31 amendments.
  - 3 commodity (`commodity_curve_carry`, `ng_contango_short`,
    `wti_backwardation_carry`) — need continuous second-month futures.
    Probe: CME direct, Nasdaq Data Link, whether the 3E provider serves
    futures chains.
  - 2 rates (`swap_spread_mean_rev`, `global_inflation_momentum`) — need a
    post-2016 10Y USD swap rate and a JP CPI level series with 2025 coverage.
    Probe: BIS statistics, OECD direct, Japan Statistics Bureau.
- **Honest outcome is acceptable.** If the substrates remain unavailable,
  this session re-affirms the deferrals with updated evidence and closes them
  as permanent-until-paid rather than leaving them open indefinitely.
- **Estimate:** 4–6h, audit-heavy.

### Session 3J — LEAN bridge

- **Scope:** replace the `lean_bridge.py` stub with a working integration.
- **Why it matters:** LEAN is event-driven and handles options, futures, and
  discrete-traded legs that the vectorised bridges approximate. The 2026-05-01
  amendment on "bridge architecture extension for discrete-traded legs" is the
  standing evidence that `vectorbt` is being stretched.
- **Deliverables:** bridge implementing the same `run(strategy, prices, ...)`
  surface as `vectorbt_bridge`; a cross-bridge consistency test proving both
  bridges produce materially the same equity curve for a strategy both can
  represent; docs on when to choose which.
- **Estimate:** 8–10h. Largest single-session build in Phase 3.

### Session 3K — Phase 3 closeout + `v0.3.0`

- Full-repo cluster at whatever N real-feed coverage reaches.
- Phase 3 retrospective in the Section 0 style of the Phase 2 master plan.
- Amendment consolidation; CHANGELOG `[0.3.0]`; closeout; tag.
- **Write `docs/phase-4-master-plan.md`** before closing.
- **Estimate:** 4–6h.

---

# Phase 4 — Portfolio construction & alt-data (`v0.4.x`)

**Goal:** stop shipping 109 independent signals and start shipping a way to
*combine* them. This is the phase where the library becomes a system.

### Session 4A — Portfolio construction framework

- Extract the covariance primitive (`_covariance.py`, currently private to the
  macro family) into a first-class public module.
- Implement: inverse-vol, ERC/risk-parity, HRP (Lopez de Prado 2016), Kelly
  and fractional-Kelly sizing, mean-variance with shrinkage.
- Each allocator needs the same Definition-of-Done rigour as a strategy:
  citable anchor, known-failure modes, tests.
- **Estimate:** 8–10h.

### Session 4B — Multi-strategy portfolio API

- Compose N strategies into one portfolio with an allocator, correlation-aware
  weighting, and a rebalance cadence.
- This is where the 29×29 → N×N cluster work finally pays off: the correlation
  matrix becomes an input to allocation, not just a diagnostic.
- **Estimate:** 6–8h.

### Session 4C — Risk overlays

- Vol targeting at portfolio level, drawdown control, regime-conditional
  de-risking, position limits, turnover budgeting.
- **Estimate:** 6–8h.

### Session 4D — Transaction-cost & capacity modelling

- Replace flat `commission_bps` with a real cost model: spread, market impact
  (square-root law), borrow costs for shorts, and the funding asymmetry that
  `swap_spread_mean_rev`'s `known_failures.md` §4 already flags as unmodelled.
- Capacity estimates per strategy grounded in ADV.
- **Estimate:** 6–8h.

### Session 4E — Alt-data substrate audit

- Audit-only session, S2K-2 pattern. Candidates: news sentiment, Google
  Trends, SEC filing text, short interest, retail-flow proxies.
- **PAUSE for scope decision.** Alt-data is where research projects go to
  die; the audit exists to make a small, defensible selection or none at all.
- **Estimate:** 4–6h.

### Session 4F — Phase 4 closeout + `v0.4.0`

- Portfolio-level benchmarks; Phase 5 master plan; tag.
- **Estimate:** 4–6h.

---

# Phase 5 — Execution realism (`v0.5.x`)

**Goal:** close the gap between backtest and what an order actually does.

- **5A — Order/execution model.** Limit vs market, partial fills, latency,
  queue position. Slippage as a distribution, not a constant.
- **5B — Broker abstraction.** A protocol over Alpaca / IBKR / CCXT with a
  paper-trading implementation. No live keys, no live orders.
- **5C — Live-shaped data path.** Streaming/incremental updates against the
  same adapter contract, so a strategy runs unchanged on batch or stream.
- **5D — State & reconciliation.** Position persistence, restart safety,
  broker-vs-internal reconciliation.
- **5E — Phase 5 closeout + `v0.5.0`.**

Each 6–10h. Detail these into full session specs at the Phase 5 master plan,
not now — writing them in detail before Phase 4 lands would be planning
fiction.

---

# Phase 6 — Paper trading (`v0.6.x`)

- **6A** — Paper-trading harness running the full stack against live data with
  simulated fills.
- **6B** — Monitoring, alerting, daily reconciliation reports.
- **6C** — 30-day continuous paper-trading soak. Calendar time, not work time.
- **6D** — Live-vs-backtest divergence analysis. This is the session that
  tells you whether any of it was real.
- **6E** — Phase 6 closeout + `v0.6.0`.

---

# v1.0 — Publish

- **V1A — Documentation site.** API reference, strategy catalogue, the full
  amendment history as a first-class artifact.
- **V1B — Packaging.** PyPI publish, versioning policy, deprecation policy,
  contribution guide.
- **V1C — Security & licence review.** Dependency audit, licence compatibility
  across every feed's terms of service, secrets policy.
- **V1D — Reproducibility pass.** Every benchmark reproducible from a clean
  clone. This is the claim the whole project rests on.
- **V1E — `v1.0.0` + the end of the silent build.** First public announcement.

---

## 4. Session kickoff template

Copy this, fill the bracketed fields, prepend §3 Standing Discipline and — for
any session touching strategies — §2 Definition of Done.

```
Session [ID] kickoff. Scope: [one line]. Branch: claude/[id]-[slug].

[Paste §3 Standing Discipline]
[Paste §2 Definition of Done — if strategies are created or converted]

S[ID]-0: Carry-in + feasibility audit
- Verify previous tag's verify-install is green via GitHub MCP. If red, STOP.
- Write scripts/audit_[substrate].py mirroring audit_fred_rates_series.py:
  per-candidate probe, machine-checkable classifier, summary table,
  fail-loud on offline mode, cache disabled via null sentinel.
- I run it locally and paste output.
- PAUSE for my substrate decision. Do not start S[ID]-1 until I confirm.

S[ID]-1: [Build]
- [Specific deliverables]
- Predictions in known_failures.md §6 written BEFORE any keyed run.
- Gates: uv sync --extra dev && uv run pytest (NO path arg).
- Give me the exact regen command.

S[ID]-2: Cluster extension
- Extend cluster_analysis.py AND tests/test_cluster_analysis.py in the SAME
  commit — the prediction-coverage test pins cluster scope and broke CI in
  S2K-4.
- I run the keyed cluster.

S[ID]-3: Docs + closeout + tag
- Amendment for any deferral/drop/convention change.
- CHANGELOG section; docs/sessions/[id]-closeout.md mirroring 2k structure.
- Drafts for my review BEFORE the docs commit.
- PR review → squash-merge → tag on squash SHA. Tag SHA == CI-target SHA.

Reporting cadence: after each S[ID]-n, plus a pause at every decision point.
```

---

## 5. Honest totals

| Phase | Sessions | Rough effort |
|---|---|---|
| Phase 3 | 11 (3A–3K) | 60–80h |
| Phase 4 | 6 (4A–4F) | 35–45h |
| Phase 5 | 5 (5A–5E) | 35–50h |
| Phase 6 | 5 (6A–6E) | 30–40h + 30 days calendar |
| v1.0 | 5 (V1A–V1E) | 25–35h |
| **Total** | **32 sessions** | **185–250h** |

Phase 2 ran 12 sessions for 49 strategies plus the data layer. Thirty-two more
sessions to a defensible v1.0 is consistent with that observed rate, not a
pessimistic padding of it.

**The three decisions that most change this plan**, all of which should be
made early rather than discovered late:

1. **Session 3C fundamentals substrate** — gates 10 value strategies and both
   value `_proxy` graduations.
2. **Session 3E paid-feed policy** — gates 20 strategies. If paid feeds are
   permanently rejected, Phase 3 drops to 9 sessions and options/vol-proxy
   stay synthetic through v1.0, which is a legitimate outcome that should then
   be stated plainly in the README rather than left implicit.
3. **Session 3H ADR-001 resolution** — the carry family has been deferred
   since Phase 1. Either it gets a substrate in Phase 3 or ADR-001 gets
   superseded by an ADR that says "these 10 ship synthetic, permanently,
   here's why."
