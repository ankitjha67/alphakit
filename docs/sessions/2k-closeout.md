# Phase 2 Session 2K closeout — v0.2.2 pt 2: cot CFTC wiring + rates feasibility + tag

## 1. Summary

* **Branch:** `claude/2k-rates-cot-real-feed`
* **PR:** [#23](https://github.com/ankitjha67/alphakit/pull/23)
* **Merge commit:** _to be filled after squash-merge_
* **Merge type:** squash (per Session 2D–2J precedent)
* **Scope:** v0.2.2 **pt 2 of 2** — closes the v0.2.2 backlog inherited
  from Session 2J. Ships the cot wiring (the 3-layer architectural fix
  Session 2J-2.8 deferred), the cache-portability fix (Windows /dev/null
  recognition), and the setup-uv v4 → v7 bump. Two rates strategies
  (`swap_spread_mean_rev`, `global_inflation_momentum`) deferred to Phase 3
  after an empirical FRED audit found the substrate gaps. **v0.2.2 tag
  publishes against the post-2K merged-main SHA.**
* **Strategy count unchanged:** 109.
* **PR CI:** _to be filled — 13/13 expected_.

## 2. Commits

| # | Hash | Summary |
|---|---|---|
| S2K-0   | `c19349e` | 2 PR #22 post-merge CodeRabbit cleanups (CFTC test offline-leak + regen messages restored) |
| S2K-1   | `09c1256` | cot 3-layer fix — strategy `cftc_market_codes` mapping + `CFTCCOTWideAdapter` + runner routing |
| S2K-1   | `69fd056` | cot routing edge-case tests (partial mapping / absent code / skipped-week ffill) |
| S2K-1   | `3c7997b` | 2 PR #23 CodeRabbit findings (3 stale `cftc-cot` refs + multi-year wide-adapter test) |
| _regen_ | `3f0615d` | 7-strategy commodity regen — `cot_speculator_position` stamped `yfinance+cftc-real` (Ankit-side keyed) |
| S2K-2   | `954de57` | rates feasibility audit doc + FRED probe script (primary) |
| S2K-2   | `3af36f1` | secondary FRED probe — corrected suffixes + `fred.search()` hunt |
| S2K-2   | `0b5c63c` | 2026-05-31 amendment + final deferral verdict for 2 rates strategies |
| S2K-3   | `530fb75` | `setup-uv@v4 → @v7` across 4 workflows |
| S2K-3   | `68c3812` | PR #23 CodeRabbit fix — audit script `probe_one` all-NaN crash guard |
| S2K-3.5 | `1f080d2` | cross-platform cache sentinel (raw-string check before `Path()` normalisation) |
| S2K-4   | `983bcf6` | cluster_analysis 11×11 → 29×29 (5 regime + 7 commodity + 11 rates + 6 macro) |
| S2K-4   | _this_    | 29×29 cluster findings + CHANGELOG v0.2.2 final + this closeout |

## 3. What 2K delivered

* **`cot_speculator_position` real-feed via cftc-cot-wide** — the
  S2J-2.8-deferred 3-layer fix lands: strategy declares
  `cftc_market_codes` mapping, new `CFTCCOTWideAdapter` returns
  OI-normalised wide-format positioning (`(NC_long − NC_short) / OI` ∈
  [-1, +1]), runner routes `*_NET_SPEC` symbols and translates
  NET_SPEC ↔ market_code at the adapter boundary so the adapter contract
  stays strategy-agnostic. Commodity family now ships **7 of 10**
  real-feed in v0.2.2 (up from 6 in v0.2.2 pt 1); 3 remain
  yfinance-second-month-blocked per the 2026-05-31 commodity amendment.
* **2 rates strategies deferred to Phase 3** — the S2K-2 empirical FRED
  audit (`scripts/audit_fred_rates_series.py`) found `DSWP10`
  discontinued 2016-10 with no continuous replacement (`fred.search()`
  exhausted 4 queries) and the Japan CPI level series
  (`JPNCPIALLMINMEI`) stops at 2021-06 leaving a 4-year gap against the
  2025-12 OOS window. 2026-05-31 rates amendment documents both
  deferrals with Phase 3 re-instatement paths.
* **Cross-platform cache sentinel** — `FeedCache._is_disabled` now
  compares the raw user input before `Path()` normalisation, so
  `/dev/null` works on Windows (where `str(Path("/dev/null"))` mangles to
  `\dev\null`) and `NUL` works on Linux. Case-insensitive Windows
  variants (`NUL`, `nul`, `NUL:`, `\\?\NUL`) all recognised. The fix
  was masquerading as test failures — investigation revealed a real
  silent cache-enable bug on Windows.
* **setup-uv @v4 → @v7** across all 4 workflows (test, lint, docs,
  benchmark). Floating-tag bump; v8 stops publishing floating major
  tags so that's the next pinning-model decision (Phase 3 backlog).
* **29×29 real-feed cluster** in `cluster_analysis.py --feed real` —
  expanded from S2J's 11×11 by adding S2K-1 cot + the 17 Session 2H
  yfinance-real ETF strategies (11 rates + 6 macro). Four intra-family
  blocks + 3 cross-family descriptive blocks.
* **2026-05-31 rates amendment** + S2K-1 / S2K-2 / S2K-3.5 process
  lessons + this closeout.

## 4. Real-feed coverage update

`data_source` split on `main` after merge:
**17 yfinance-real + 5 yfinance+fred-real + 6 yfinance-futures-real
+ 1 yfinance+cftc-real (cot) + 80 synthetic-fixture** = 109 total.
Real-feed coverage **28/109 (25.7%) → 29/109 (26.6%)**.

Deferrals:
* **Phase 3 — substrate / API blockers:**
  * 3 yfinance-second-month-blocked commodity strategies
    (`commodity_curve_carry`, `ng_contango_short`,
    `wti_backwardation_carry`) per the 2026-05-31 commodity amendment.
  * 2 rates strategies (`swap_spread_mean_rev`,
    `global_inflation_momentum`) per the 2026-05-31 rates amendment
    (DSWP10 / ICE swap rate / JP CPI 2021-06 gap).
* **Design choice:** options (15) remain synthetic-options.

## 5. 29×29 cluster findings (real-feed basis)

_To be filled with the actual keyed-run output after Ankit's_
_`uv run --with fredapi --with yfinance --extra dev python
scripts/cluster_analysis.py --feed real` reports back._

Structure of the findings section (mirrored on the S2J 11×11 template):

* Headline: max ρ across all 406 pairs; any ρ > 0.95 dedup-bar
  breaches (cot↔commodity_tsmom predicted NEGATIVE — worth a sub-
  headline if the prediction holds).
* Regime intra-family (5×5, carry-over from S2I/S2J — should reproduce).
* Commodity intra-family (7×7 — was 6×6; the cot↔commodity_tsmom
  prediction (-0.20 to 0.00, mildly NEGATIVE) is the only new in-scope
  cot pair).
* Rates intra-family (11×11 NEW) — 11 documented predictions in
  `_PREDICTED_RATES_RHO`; the steepener↔flattener mirror image
  (≈-1.0) is the headline deliberate-redundancy pair.
* Macro intra-family (6×6 NEW) — 7 documented predictions in
  `_PREDICTED_MACRO_RHO`; covariance-primitive trio
  (ERC / MV / max-div) the headline.
* Cross-family blocks (regime×commodity carry-over + rates×commodity
  + rates×macro NEW) — descriptive only.
* Per-family OK/documented summary + overall mean |ρ| + dedup-bar
  status.

## 6. Architectural changes

* **3-layer cot fix** (S2K-1) — the depth that S2J-2.8 investigation
  surfaced: strategy-side `cftc_market_codes` mapping + new
  `CFTCCOTWideAdapter` (long-format `CFTCCOTAdapter` unchanged for
  ad-hoc analysis, zero rewrites of its 4 unit tests or contract
  harness) + runner-side NET_SPEC ↔ market_code translation. The
  adapter contract (`fetch(symbols, start, end, frequency) ->
  pd.DataFrame`) stays strategy-agnostic — adapter speaks market
  codes, runner does the cot-specific translation.
* **Cross-platform cache sentinel** (S2K-3.5) — raw-string check
  before `Path()` normalisation. Same logical contract on every host
  OS for `/dev/null` and `NUL`. Env-var path consolidated through the
  same resolver.
* **S2K-2 audit framework** — `audit_fred_rates_series.py` pattern
  (multi-candidate probe + `looks_like_level` classifier +
  `fred.search()` negative-evidence trail + 1.5s inter-call sleep)
  generalises to any future FRED-substrate feasibility question.

## 7. v0.2.2 tag plan

Per Session 2H §7 tag conventions: **no pre-release flag**, this is
the `.2` release. Sequence after PR #23 squash-merge:

1. Capture squash SHA from the merge commit on `main`.
2. Tag `v0.2.2` on the squash SHA.
3. Verify **tag SHA == CI-target SHA** (Session 2H footgun guard).
4. Wait for `verify-install` workflow on the tag — **6/6 green
   required**.
5. Fresh-venv keyed reproduce check (Ankit-side) on the tag SHA.

## 8. Process lessons

### (a) S2K-1 empirical market-code verification

Session 2J-2.8 closeout's deferral note documented two CFTC market
codes for the cot wiring — **2 of the 4 were empirically wrong**.
A 15-minute probe of the real 2024 archive (`requests.get` + pandas
inspection of `Market and Exchange Names` column) revealed:

* `067411` documented for WTI → actually ICE Europe; the NYMEX PHYSICAL
  WTI code is `067651`.
* `023655` documented for NG → actually E-mini; the standard
  Henry Hub Natural Gas code is `03565B`.

Both would have silently shipped wrong positioning data and bad
benchmarks. The fix was institutionally cheap (a one-off probe before
scope commitment) and concretely confirmed the S2J-2.8 lesson:
"verify adapter contract end-to-end against real substrate data
BEFORE scope commitment." This is the first concrete example of
that lesson preventing a silent-wrong-data outcome.

### (b) S2K-2 audit framework — negative-evidence trail

The rates feasibility audit institutionalised three primitives:

1. **Multi-candidate per-series probe** — list every plausible series
   ID, probe each, report coverage + range + gaps. Surfaces the
   exact ID that works, not just "FRED has CPI somewhere".
2. **`looks_like_level` classifier** (`min >= 0 AND max > 50`) — turns
   "is this a LEVEL series?" from an eyeball check into a boolean.
   Surfaced that OECD-MEI suffixes `M657N` and `M659N` both return
   RATE-OF-CHANGE for DE and JP CPI despite naming convention
   suggesting they should differ; the LEVEL series live at the
   BIS-OECD alternative names (`DEUCPIALLMINMEI`,
   `JPNCPIALLMINMEI`). Prevented shipping silently-wrong
   inflation calculations.
3. **`fred.search()` negative-evidence trail** — before declaring a
   strategy blocked, exhaust the search space and document what FRED
   *does* have under the relevant queries. Four queries for the swap
   rate hunt (`10-year swap rate USD`, `ICE swap rate`,
   `USD interest rate swap`, `SOFR swap rate 10`) returned no usable
   continuous post-2016 series; the defensible verdict is "no
   continuous swap rate exists on FRED post-DSWP10".

This framework generalises directly to future feasibility questions
(international yields, alternative inflation series, commodity
back-month replacements).

### (c) S2K-3 conservative pinning vs floating-tag migration

`setup-uv@v4 → @v7` is a clean bump (none of our inputs are affected
by v5/v6/v7 breaking changes). v8.0.0 stopped publishing floating
major tags — `@v8` no longer resolves, only immutable patch tags
like `@v8.0.0` work. That's a pinning-model change (security:
immutable releases prevent supply-chain attacks) which is out of
v0.2.2 scope. **Phase 3 candidate:** review every action pin in
`.github/workflows/*` for immutable-reference compliance before
moving to setup-uv@v8.

### (d) S2K-3.5 substrate behavior bug masquerading as test failure

Two pre-existing test failures on Windows were initially framed as
"pre-existing Windows portability issues" worth a quick platform-aware
skip. Investigation revealed they were correctly detecting a **real
cache behaviour bug**: `Path()` normalisation on Windows mangled
`/dev/null` to `\dev\null`, the sentinel set didn't match the
normalised string, and the cache was silently ENABLED on Windows
when developers expected it disabled. Any Windows developer or
Windows CI run using `/dev/null` as the cache-disable sentinel got
actual caching, not disabled caching. Treating the failures as
test-skip candidates would have left a silent-wrong-behaviour bug
in production. Connects to S2J §8(a) multi-layer verification:
**empirical verification on the real environment surfaces what
synthetic testing misses**.

### (e) Honest deferral pattern at scale

Session 2K's deferral arithmetic: **1 resolved** (cot from S2J's
deferral list) + **2 deferred** (rates, this session) + **3 carried**
(commodity from S2J's 2026-05-31 amendment). The net is +1 to
real-feed coverage with two new amendments documenting Phase 3
re-instatement paths for the 5 deferred strategies. Same
substrate-or-architecture-blocker pattern as Sessions 2D / 2F / 2J;
the consistency of the pattern across 4 sessions is itself the
forward signal — **substrate constraints surface empirically, not
in advance, and the only sustainable response is to ship what
works and document the rest**.

### (f) CodeRabbit consistently catches doc-drift after rename

Across PRs #22 and #23, CodeRabbit's findings clustered on
**docstring / help-text drift after architectural rename** — refs
to old names left in docstrings, argparse help, module-level
comments. The pattern is reliable across 4 commits (S2K-0, S2K-1,
S2K-1 follow-up, S2K-3 follow-up). **Phase 3 candidate:** pre-push
doc-consistency linter (e.g. enforce that names referenced in
docstrings exist in the codebase, or that recent rename PRs leave
no stale references).

## 9. Pacing

Session 2K ran **11 commits** (S2K-0 through S2K-4 + this docs commit)
versus Session 2J's 10. Pacing breakdown:

* S2K-0 / S2K-1 / S2K-1 follow-ups (4 commits): cot delivery, the
  substantive new feature.
* S2K-2 audit phase (3 commits): empirical FRED probe, no build.
* S2K-3 / S2K-3.5 (3 commits): setup-uv bump + cross-platform cache
  fix.
* S2K-4 (this commit + cluster code): closeout, CHANGELOG, cluster
  broadening.

The audit-only phase (S2K-2) is new — Session 2K is the first
session where a substantial chunk was explicit "no build until
empirical verdict". The audit framework cost ~1h and prevented
multi-hour misadventures on two blocked strategies. Same pacing
discipline as S2J's network-gate retries: rounds that surface
architectural classes rather than churn.

## 10. v0.2.3 backlog (forward-looking)

Per Session 2H §7 / S2J §10 forward-planning pattern. v0.2.3 candidates
identified during Session 2K:

* **setup-uv@v7 → @v8** with immutable-tag pinning review for every
  action in `.github/workflows/*` (S2K-3 lesson).
* **Pre-push doc-consistency linter** (S2K-4 §8(f) lesson).
* **Phase 3 re-instatement candidates** documented in the 2026-05-31
  rates amendment (BIS swap rate, JP CPI alternative) and the
  2026-05-31 commodity amendment (CME second-month adapter).
* **Code-aware cache keys** (S2J §8(e) lesson, still open).
* **Real-feed cluster expansion to 47×47** — once additional
  Phase 3 substrates land. The 29×29 cluster's mean |ρ| + per-family
  prediction calibration carries over.
