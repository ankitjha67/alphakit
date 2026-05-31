# Phase 2 Session 2J closeout — v0.2.2 pt 1: commodity real-feed

## 1. Summary

* **Branch:** `claude/2j-commodity-real-feed`
* **PR:** [#22](https://github.com/ankitjha67/alphakit/pull/22)
* **Merge commit:** _to be filled after squash-merge_
* **Merge type:** squash (per Session 2D–2I precedent)
* **Scope:** v0.2.2 **pt 1 of 2** — feed-router primitive + anomaly filter +
  6 commodity strategies real-feed (yfinance-futures); CFTC adapter
  foundations laid for Session 2K's cot wiring. **Not a new strategy
  family.** **v0.2.2 tag waits for Session 2K** (cot CFTC wiring + rates
  real-feed + setup-uv bump + broader cluster).
* **Strategy count unchanged:** 109 on `main`.
* **PR CI:** _to be filled — 13/13 expected_.

## 2. Commits

| # | Hash | Summary |
|---|---|---|
| S2J-1   | `cb63907` | per-role feed router + cot Session-2G declaration |
| S2J-1.5 | `8b708c6` | FeedRegistry population (Codex P1) + KeyError surfacing + cot finiteness ordering + 4 CodeRabbit review fixes |
| S2J-2   | `fc6b232` | `commodity --feed real` (7 slugs) in `regenerate_benchmarks.py` |
| S2J-2.5 | `b0f40cf` | yfinance-futures MultiIndex flatten + CFTC `urllib → requests` |
| S2J-2.6 | `1f627c9` | CFTC URL fix + anomaly filter (`drop_nonpositive_tradable_bars`) |
| S2J-2.7 | `f5d9d0e` | PR #22 review pass — `last_anomaly_filter` reset + adapter `reindex` + test hygiene |
| S2J-2.8 | `e58d1f8` | CFTC archive column rename + `cot_speculator_position` deferred to Session 2K |
| S2J-3   | `5d4e3d1` | `cluster_analysis.py --feed real` broadened 5×5 → 11×11 |
| S2J-3   | `96bd51a` | CHANGELOG v0.2.2 pt 1 section |
| S2J-3   | _this_    | 2026-05-31 amendment + this closeout + 11×11 cluster findings |

## 3. What 2J delivered

* **Feed-router primitive** in `BenchmarkRunner._fetch_prices` — per-role
  ticker-pattern dispatch via `FeedRegistry` (`=F` → yfinance-futures,
  `*_NET_SPEC` → cftc-cot; defaults to yfinance / fred). Replaces the
  pre-S2J hardcoded yfinance + FRED dispatch; unblocks any future adapter
  without more runner edits.
* **Anomaly filter** — opt-in `drop_nonpositive_tradable_bars=True` drops
  mid-panel rows with NaN or `<= 0` tradable values before the bridge sees
  them, classifying each as "missing data" / "negative price" / "mixed" in
  the log and recording the audit trail in `result["anomaly_filter"]`.
* **6 commodity real-feed benchmarks** —
  `commodity_tsmom`, `crack_spread`, `crush_spread`, `grain_seasonality`,
  `metals_momentum`, `wti_brent_spread`. `data_source="yfinance-futures-real"`.
* **CFTC adapter cleanup** — `urllib → requests` (Windows SSL fix), URL
  moved from retired `/dea/newcot/` archive to `/files/dea/history/`, and
  6 column constants renamed to the new schema. Session 2K's cot wiring
  now needs only symbol-mapping + long-to-wide, not adapter plumbing.
* **Network-gated substrate-boundary tests** —
  `ALPHAKIT_RUN_NETWORK_TESTS=1` opt-in, skipped by default in CI. Three
  guards: real yfinance multi-ticker fetch, real CFTC ZIP download, real
  CFTC archive schema. **Mandatory pre-push gate for adapter changes.**
* **`docs/known-data-anomalies.md`** — new top-level doc for substrate
  observations (per-ticker known anomalies, filter contract, JSON audit
  format, "Deferred to Session 2K" for cot).
* **11×11 real-feed cluster** in `cluster_analysis.py --feed real` —
  regime-intra + commodity-intra (predicted vs actual) + cross-family
  descriptive block.
* **CHANGELOG v0.2.2 pt 1** + this closeout + 2026-05-31 amendment.

## 4. Real-feed coverage update

`data_source` split on `main` after merge:
**17 yfinance-real + 5 yfinance+fred-real + 6 yfinance-futures-real + 81
synthetic-fixture** = 109 total. Real-feed coverage **22/109 → 28/109
(25.7%)**.

Deferrals:
* **Session 2K (v0.2.2 pt 2)**: `cot_speculator_position` (CFTC adapter
  symbol-mapping + long-to-wide pivot), `swap_spread_mean_rev`,
  `global_inflation_momentum`, broader cluster.
* **Phase 3**: 3 yfinance-second-month-blocked commodity strategies
  (`commodity_curve_carry`, `ng_contango_short`, `wti_backwardation_carry`)
  per 2026-05-31 amendment; options (15) remain synthetic-options by
  design.

## 5. 11×11 cluster findings (real-feed basis)

Full output from `cluster_analysis.py --feed real` (5,288 aligned bars,
2005-2025). All 11 strategies pairwise distinct — **no pair breaches the
ρ > 0.95 dedup-review bar** (max ρ = +0.794). Mean |ρ| = 0.149 across the
55 unique pairs.

### Headline: `commodity_tsmom ↔ metals_momentum` resolves "keep both"

The pair Session 2E flagged as the deliberate-redundancy candidate
(metals being a strict subset of `commodity_tsmom`'s 8-asset universe)
came in at **+0.565, well below the 0.75–0.90 predicted band**. The two
strategies are genuinely distinct enough to ship separately. Three
interpretations explain the gap:

* The non-metals legs (CL/NG/ZC/ZS/ZW) carry enough independent signal
  to dilute the metals overlap.
* Risk-parity weighting differences between the 8-asset and 4-asset
  portfolios matter more than universe overlap alone.
* Session 2E over-anchored the prediction on universe overlap without
  accounting for parity-weighting dilution.

**Implication for Session 2K:** the pair is **NOT a dedup candidate**.
Session 2E's flag for potential consolidation resolves to "keep both" —
both ship in v0.2.2.

### Regime intra-family (5/10 in predicted range — same pattern as Session 2I)

Synthetic predictions UNDERSTATED real co-movement; the diffuse macro-wide
common-factor framing from Session 2I holds. The four overshoots are all
FRED-input-sharing pairs:

| Pair | Actual | Predicted | Note |
|---|---|---|---|
| `yield_curve_regime_allocation` ↔ `fed_policy_tilt` | **+0.794** | 0.40–0.60 | significant overshoot — largest ρ in matrix |
| `growth_inflation_regime_rotation` ↔ `inflation_regime_allocation` | **+0.779** | 0.40–0.60 | CPI shared input |
| `yield_curve_regime_allocation` ↔ `inflation_regime_allocation` | +0.672 | 0.30–0.50 | |
| `fed_policy_tilt` ↔ `inflation_regime_allocation` | +0.637 | 0.30–0.50 | |
| `recession_probability_rotation` ↔ `yield_curve_regime_allocation` | +0.495 | 0.50–0.70 | narrowly below the deliberate-redundancy band — essentially as predicted |

### Commodity intra-family (1/6 in predicted range — opposite asymmetry)

Commodity predictions OVERSTATED co-movement (in contrast to regime).
The metals pair (above) is the headline; the other 5 documented pairs
all land at or below their predicted floors:

| Pair | Actual | Predicted | In range |
|---|---|---|---|
| `commodity_tsmom` ↔ `metals_momentum` | +0.565 | 0.75–0.90 | OUT (low) — see headline above |
| `crack_spread` ↔ `wti_brent_spread` | +0.188 | 0.10–0.30 | ✓ |
| `crush_spread` ↔ `grain_seasonality` | +0.081 | 0.10–0.20 | OUT (narrowly below) |
| `crack_spread` ↔ `crush_spread` | −0.022 | 0.00–0.10 | OUT (just below) |
| `crush_spread` ↔ `wti_brent_spread` | −0.017 | 0.00–0.10 | OUT (just below) |
| `commodity_tsmom` ↔ `grain_seasonality` | −0.020 | 0.20–0.40 | OUT (well below) |

The other 9 in-scope commodity pairs (out of 15) carry no documented
prediction; their actual ρ are uniformly small (`|ρ| < 0.10` across all
9), consistent with their universes being genuinely independent.

### Cross-family (5 regime × 6 commodity — descriptive)

`commodity_tsmom ↔ growth_inflation_regime_rotation = +0.154` is the
strongest cross-family pair; all other regime×commodity ρ are
`|ρ| ≤ 0.108`. The 5 regime and 6 commodity strategies sit in
**genuinely independent factor spaces** — a clean diversification finding
for the project. No cross-family pair approaches the 0.95 dedup bar
(max +0.154 is half an order of magnitude below).

### Anomaly filter audit (from the keyed-run logs)

Per-strategy bars dropped by the S2J-2.6 filter:

| Strategy | Bars dropped | Dominant cause |
|---|---|---|
| `metals_momentum` | 570 | `PL=F` early-years gaps (2005–2009) |
| `wti_brent_spread` | 55 | `BZ=F` early-years gaps (2008–2014) |
| `commodity_tsmom` | 19 | holiday NaN + 2020-04-20 WTI |
| `crack_spread` | 6 | holiday NaN |
| `grain_seasonality` | 2 | holiday NaN |
| `crush_spread` | 0 | clean ag data |

The `metals_momentum` 570-bar drop confirms `PL=F` inception is materially
later than the 2005-01-01 nominal start; the silent leading-trim portion
of the filter handles those gaps cleanly. The single negative-price drop
(2020-04-20 WTI) lands as a single mid-panel line in
`commodity_tsmom`'s / `crack_spread`'s / `wti_brent_spread`'s audit
trails.

### Summary

| Metric | Value |
|---|---|
| Aligned bars | 5,288 (2005–2025) |
| Mean \|ρ\| (off-diagonal, 55 pairs) | 0.149 |
| Max ρ | +0.794 (`yield_curve_regime_allocation` ↔ `fed_policy_tilt`) |
| Documented pairs in predicted range | **6 of 16** (regime 5/10, commodity 1/6) |
| `ρ > 0.95` (dedup bar) | **0** — all 11 strategies pairwise distinct |

## 6. Architectural changes

* **Feed router** (S2J-1) — pattern-based, role-separated, zero strategy
  code changes for 9 of the 10 in-scope strategies; only
  `cot_speculator_position` needed the Session 2G alias declaration.
* **Anomaly filter** (S2J-2.6) — value-pattern, not hardcoded date list.
  Handles 2020-04-20 WTI generically; future negative-price events
  (any commodity) are handled identically. Audit trail in JSON.
* **CFTC adapter** (S2J-2.5 + S2J-2.6 + S2J-2.8) — `requests`, current
  archive URL, new schema column names. Foundation for Session 2K cot
  wiring.
* **Network-gated test pattern** (S2J-2.5+) — `ALPHAKIT_RUN_NETWORK_TESTS=1`
  env gate; institutionalised as the pre-push gate for adapter changes.

## 7. v0.2.2 tag plan — _waits for Session 2K_

Per scope constraint, **v0.2.2 tag is not in this session**. Session 2K
completes the v0.2.2 backlog (§10), and the tag publishes against the
post-2K merged-main SHA. The Session 2H §7 tag-plan conventions apply
unchanged (no pre-release flag, verify tag SHA == CI-target SHA, fresh-venv
keyed reproduce).

## 8. Process lessons

### (a) Multi-layer verification scorecard

**13 bug-catches across Sessions 2I + 2J**, distributed across layers:

| Session | Layer | Count |
|---|---|---|
| 2I-1.5  | substrate-boundary (real data + real OS) | 3 |
| 2J-1.5  | cross-cutting (Codex P1 + CodeRabbit Majors + Minors) | 5 |
| 2J-2.5  | substrate-boundary (real yfinance MultiIndex + real Windows SSL) | 2 |
| 2J-2.6  | substrate-boundary (URL drift, WTI negative, holiday NaN — keyed retry round) | 3 |
| 2J-2.7  | cross-cutting (CodeRabbit pass after S2J-2.6) | 5 |
| 2J-2.8  | architectural-depth (investigation surfaced cot adapter layers 2 + 3) — deferral, not fix | — |

**Three categories of bugs single-layer testing misses:**

1. *Structural correctness* (routing, validation, alignment) — caught by
   mock-based integration tests.
2. *Cross-cutting concerns* (import-time side effects, error-handling
   paths, doc drift, dead branches) — caught by automated code review
   (Codex + CodeRabbit).
3. *Substrate-boundary* (adapter ↔ real-data quirks, OS-specific,
   network/SSL config, schema drift) — caught only by real-environment
   execution against the actual substrate.

Single-layer testing catches at most one of these three. **Pre-release
verification requires three layers:** mocked integration suite, automated
review pass, network-gated real-environment smoke test. Mocks alone
would have shipped all 13.

### (b) Network-gated tests are mandatory pre-push for adapter changes

Sessions 2J-2.5 and 2J-2.6 each missed this gate and each cost one keyed
regen round-trip. Session 2J-2.8 hit the gate correctly (URL fix + column
rename verified together against the real CFTC archive) and avoided a
third round-trip. S2J-2.7 was a pure code-review pass (no adapter or
routing changes), so the network-gate question didn't apply. The
discipline is `ALPHAKIT_RUN_NETWORK_TESTS=1 uv run pytest
packages/alphakit-data/tests/ -v -k real` before any adapter or routing
push.

### (c) Prediction methodology calibration — sign asymmetry between sessions

The 11×11 cluster surfaced a clean sign asymmetry in prediction misses
between Sessions 2E (commodity) and 2G (regime):

* **Session 2G regime predictions UNDERSTATED real co-movement.** 4 of
  the 5 OUT pairs land *above* their predicted band — the diffuse
  macro-wide common factor that synthetic fixtures couldn't reproduce
  (first observed in Session 2I, replicated in Session 2J).
* **Session 2E commodity predictions OVERSTATED real co-movement.** 5
  of the 5 OUT pairs land *below* their predicted band; the headline
  `commodity_tsmom ↔ metals_momentum` came in at 0.565 vs predicted
  0.75–0.90 (universe-overlap intuition didn't account for risk-parity
  weighting dilution).

This isn't an artifact of one bad prediction in either session — the sign
is consistent across all OUT pairs in each session. The two sessions
used different methodologies for predicting ρ ranges, and both
miscalibrated in opposite directions on real data.

**Forward recommendation for Session 2K:** before publishing cluster
predictions for rates (`swap_spread_mean_rev` ↔ `bond_carry_*`, etc.) or
for the cot wiring, review the prediction-methodology calibration
explicitly. The empirical pattern from 2I + 2J suggests:

* Predictions anchored on *signal-input overlap* (FRED series sharing in
  regime) **underestimate** — real signals are noisier than synthetic
  and correlate via shared input even when strategy rules differ.
* Predictions anchored on *universe overlap* (`commodity_tsmom` ⊃
  `metals_momentum`) **overestimate** — different weighting / sizing
  rules dilute overlap more than intuition allows for.

Documenting the calibration adjustment up front, rather than discovering
the bias post-hoc, would make cluster predictions more useful as actual
guides rather than as ground-truth-revealing baselines.

### (d) Feasibility audits precede scope commitment

Three Session 2J feasibility gaps the Session 2I closeout backlog missed:

* yfinance has no continuous second-month series (3 commodity strategies
  blocked → 2026-05-31 amendment).
* No clean free foreign-bond proxy for `global_inflation_momentum`
  (partial feasibility — Session 2K still has the gap).
* `EIA_API_KEY` unblocks no current strategy (no shipping strategy
  consumes EIA series).

**Plus Session 2J-2.8's architectural-depth gap:** the v0.2.0 → v0.2.1 →
v0.2.2 audit identified `cot_speculator_position` as "needs CFTC routing
wiring" — *correct* about the surface symptom, *incomplete* about depth.
Three independent architectural mismatches (column-rename layer 1 +
symbol-mapping layer 2 + long-to-wide pivot layer 3) only surfaced when
the keyed S2J-2.7 regen hit the first layer and S2J-2.8 investigation
peeled the others. **Going forward:** when an audit identifies a
strategy as needing "just routing wiring," verify the adapter contract
end-to-end against real substrate data **before** scope commitment, not
just symbol/feed mapping at the API surface. A `requests.get` + manual
schema inspection takes 15 minutes and prevents multi-hour
misadventures.

### (e) Persistent caches must be invalidated when code changes

`~/.alphakit/cache/` (24h-TTL parquet) survived `uv sync --reinstall` and
silently overrode the S2J-2.5 multi-level flatten fix on Ankit's first
re-run. Cache-key is `(feed_name, symbols, start, end, frequency)` — no
code-version component. The cache **does not** invalidate when adapter
code changes. Documented in `docs/known-data-anomalies.md`. Phase 3
candidate: code-aware cache keys (e.g. hash of the adapter module's
source).

### (f) Honest deferral is a positive outcome

`cot_speculator_position` → Session 2K, 3 commodity → Phase 3 amendment.
Both demonstrate the project's discipline of *not* shipping architecture
for capabilities that aren't actually deliverable on the chosen
substrate — same pattern as Session 2F `vix_front_back_spread` and
Session 2D's `fed_funds_surprise` / `fra_ois_spread`. The single S2J-2.8
deferral decision avoided a 4–6h Session 2J build with material
silent-wrong-data risk (CFTC publishes multiple contracts per commodity
name; misidentifying the right market code would produce wrong
positioning data and bad benchmarks).

## 9. Pacing

Session 2J ran **10 commits** (S2J-1 → S2J-3 + this docs commit) versus
Session 2I's 7. The added rounds were S2J-1.5 (Codex + CodeRabbit P1 + 4
review items), S2J-2.5 (substrate-boundary retry round 1), S2J-2.6
(substrate-boundary retry round 2 — anomaly filter + CFTC URL), S2J-2.7
(review pass), S2J-2.8 (CFTC schema rename + cot deferral). Each round
genuinely surfaced an architectural class — not churn — and the
multi-layer verification scorecard above is the empirical justification
for the discipline. Network-gated tests became a session deliverable in
their own right.

## 10. v0.2.2 pt 2 backlog (Session 2K scope)

* **`cot_speculator_position` CFTC wiring.** Layer 2: symbol →
  market-code mapping (on the strategy, since the multi-market case needs
  disambiguation per commodity — e.g. WTI is `067411` NYMEX or `06765A`
  ICE Europe). Layer 3: long-to-wide pivot wrapper or adapter mode that
  produces `columns = requested symbols` indexed by date, so the runner's
  multi-feed merge consumes it like every other adapter.
* **Rates real-feed.** `swap_spread_mean_rev` FRED ICE-swap-rate series
  construction (continuous availability through 2025 needs verifying —
  `DSWP10` was discontinued ~2016). `global_inflation_momentum`
  international CPI series (`CPIAUCSL`, `CPHPTT01DEM659N`,
  `CPALTT01JPM659N` identified) and BOND_DE / BOND_JP proxies (open
  question — no clean free Bund/JGB total-return ETF).
* **`setup-uv` bump** to confirmed-stable v5/v6 (held at v4 since v0.2.0).
* **Broader real-feed cluster** — once Session 2K real-feed strategies
  land: 5 regime + 6 commodity + 1 cot + 2 rates = 14, plus the existing
  17 yfinance-real ETFs could be folded in for a 31×31 if methodology
  permits. **Note from Session 2J cluster:** the metals dedup question is
  already resolved (keep both); 2K cluster need not re-litigate it. The
  prediction-calibration recalibration from §8(c) should inform new
  predictions for the 2K-added pairs.
* **v0.2.2 tag** after Session 2K closes the backlog.
