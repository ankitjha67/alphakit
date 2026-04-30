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

---

## 2026-04-18 — Session 2C: macOS verify-install transient network flake

Context: First dispatch of verify-install.yml against main after
Session 2C merge (run #10) failed on the macos-latest/3.11 leg only.
Failure was a TCP connect timeout to github.com:443 during git clone
inside pip install — the install step never reached the wheel build,
let alone tests. Other 5 matrix legs passed in 50-80s.

Re-run of failed jobs (run #11) was 6/6 green against the same
commit. No code change needed.

Pattern: macOS GitHub Actions runners occasionally exhibit transient
network failures during pip install from git sources. Diagnosis
heuristic: if exactly one matrix leg fails on a network operation
that other legs completed, suspect runner flake before assuming
code regression.

Action: Re-run failed jobs first; only investigate code if the same
leg fails on re-run with a different error.

No scope change.

---

## 2026-04-18 — Session 2C: GitHub Actions Node.js 20 deprecation warning

Context: verify-install.yml run #11 surfaced a deprecation warning:
actions/checkout@v4 and actions/setup-python@v5 run on Node.js 20.
GitHub will force Node.js 24 by June 2 2026 and remove Node.js 20
on Sept 16 2026.

Decision: Defer fix to a Phase 2 housekeeping pass. Workflows still
run correctly today; the warning is informational, not blocking.
Available bumps: actions/checkout@v5 (or pin to a v4 tag that
explicitly supports Node 24) and actions/setup-python@v6.

Trigger: bump actions before Session 2H if the deprecation banner
becomes more aggressive, otherwise bundle into Session 2H's CI
cleanup.

Phase 2 housekeeping ticket added (informally tracked here, not
filed as GitHub issue per silent-build discipline).

---

## 2026-04-26 — Session 2D: drop fed_funds_surprise (no fed-funds-futures data on FRED)

Context: The Session 2D rates manifest listed `fed_funds_surprise` —
position bond exposure after FOMC rate decisions versus market
expectations, anchored on Kuttner (2001) "Monetary Policy Surprises
and Interest Rates" (Journal of Monetary Economics, 47(3), 523-544,
DOI 10.1016/S0304-3932(01)00055-1).

Honesty-check failure: Kuttner's surprise is constructed from
**CME 30-day federal funds futures**: surprise = realised target-rate
change − futures-implied expected change on the day of the FOMC
release. FRED carries the **realised** effective fed funds rate
(`DFF`) and the target range (`DFEDTARU`/`DFEDTARL`) but **does not
carry CME futures-implied expectations**. We have no other rates
feed wired up that supplies them.

Substituting a survey-consensus proxy (e.g. Blue Chip, Reuters poll)
would change both the methodology and the citation; reporting the
strategy as "Kuttner 2001" while using a different signal would
fail the honesty bar codified in Phase 2 master plan Section 10.

Decision: Drop. Phase 2 ships without a fed-funds-surprise strategy.
Candidate for re-instatement once CME fed-funds-futures data is
wired (own session, not Session 2H).

Manifest impact: rates family ships 14 strategies after this drop.

---

## 2026-04-26 — Session 2D: drop fra_ois_spread (no clean strategy paper + no FRA data)

Context: The Session 2D rates manifest listed `fra_ois_spread` —
position on the FRA-OIS spread, anchored on McAndrews, Sarkar &
Wang (2008) "The Effect of the Term Auction Facility on the
London Inter-Bank Offered Rate" (FRBNY Staff Report 335).

Honesty-check failure (two independent reasons):

1. **Paper does not describe a tradable systematic strategy.**
   McAndrews/Sarkar/Wang frames LIBOR-OIS (precursor to FRA-OIS)
   as a **funding-stress indicator** measuring inter-bank
   dysfunction during the 2007-2008 crisis. The paper studies
   the response of the spread to TAF interventions; it does not
   prescribe entry/exit rules, position sizing, or holding
   periods that would constitute a systematic strategy.

2. **No data feed for FRA quotes.** FRAs are over-the-counter
   derivative instruments. FRED carries SOFR (`SOFR`) and some
   OIS-related curves but not 3-month FRA quotes. We have no
   alternative rates feed wired up.

The reviewer flagged this exact concern in the Session 2D kickoff
brief. Both failure modes were borne out under audit.

Decision: Drop. Phase 2 ships without an FRA-OIS strategy.
Re-instatement would require both (a) a different anchor paper
that prescribes a systematic rule on a stress indicator, and (b)
a derivatives data feed; neither is on the Phase 2 roadmap.

Manifest impact: rates family ships 13 strategies after both
Session 2D drops. Total Phase 2 strategy count drops from 65 to 63.

---

## 2026-04-26 — Session 2D: signal-contract clarifications across rates strategies

Context: implementing 13 rates strategies surfaced several
contract-level conventions that go beyond the bare
`StrategyProtocol.generate_signals(prices: DataFrame) -> DataFrame`
shape documented in `alphakit.core.protocols`. These are not
deviations from the protocol — they are *extensions* that downstream
families (commodity, options, macro) should follow for consistency.

### 1. Discrete vs vol-scaled signals on single-asset trades

`bond_tsmom_12_1` was originally specified in the Session 2D brief
to return ``pd.Series of {-1, 0, +1}``, but the protocol requires
``pd.DataFrame``. Resolution: return a *single-column DataFrame*
on the discrete ``{-1.0, 0.0, +1.0}`` grid. This preserves both:

* the protocol contract (DataFrame return), and
* the discrete-signal economic content (no vol-targeting on a
  single asset; vol-targeting is deferred to a portfolio overlay).

This pattern applies to single-asset momentum/sign strategies
generally. Phase 1 `tsmom_12_1` (trend) returns vol-scaled weights
because it operates on a multi-asset panel and applies cross-asset
vol-scaling internally; the rates-family analogue does not, by
design.

### 2. Column-naming conventions for multi-leg strategies

Several rates strategies require structured multi-column inputs
that exceed "free-form list of asset symbols":

* **2-column ordered** (steepener / flattener / carry-rolldown /
  swap-spread): first column is "short-end / Treasury", second
  column is "long-end / target / swap". Validated at runtime via
  ``prices.shape[1] == 2`` plus column-order semantics in the
  docstring.
* **3-column ordered** (curve-butterfly): ``[short, belly, long]``.
* **N-column with per-column duration mapping**
  (duration-targeted-momentum, g10-bond-carry): a
  ``durations: dict[str, float]`` map validates that every input
  column has a configured duration.
* **2K-column with prefix-pairing** (global-inflation-momentum):
  ``CPI_<country>`` paired with ``BOND_<country>``. Validated by
  splitting columns into two sets and requiring exact match.
* **N>=4 free-named panel** (yield-curve-pca-trade): requires
  ``n_pcs < n_assets``; column names are flexible because PCA
  works on the covariance regardless.

Each strategy raises ``ValueError`` with a descriptive message on
contract violation. Future families (commodity, options, macro)
should follow the same pattern: validate column count and naming
at the top of `generate_signals`, raise descriptive errors, document
the convention in the strategy docstring AND in the README.

### 3. Strategies that take informational columns with zero weight

`bond_carry_rolldown` and `global_inflation_momentum` accept
columns that are *informational only* and always carry zero weight
in the output:

* `bond_carry_rolldown`: the short-end column is informational
  (used to compute the slope proxy); only the target-bond column
  ever carries non-zero weight.
* `global_inflation_momentum`: `CPI_<country>` columns are
  informational (used to compute inflation momentum); only
  `BOND_<country>` columns carry non-zero weight.

This is a legitimate pattern: the strategy needs the auxiliary data
to compute the signal but does not take a position on it. The
protocol still preserves shape (output DataFrame columns match
input), with informational columns explicitly zero. Future
strategies that need exogenous signal inputs (e.g. macro state
variables) should follow this pattern rather than introducing a
side-channel constructor parameter.

### 4. Methodology bug caught and fixed mid-session

The initial `curve_steepener_2s10s` draft inverted the steepener
mechanic — the position is **long short-end / short long-end**,
not the reverse. The error was caught during code-review of the
strategy.py docstring before commit and fixed in-place. The fix
was confirmed across the four downstream strategies that share the
mean-reversion-on-log-spread mechanic (flattener, butterfly,
swap-spread mean-rev, breakeven rotation) — each was derived from
the corrected sign convention.

Action item for Phase 2 housekeeping: file a one-page "fixed-income
trade-direction reference" under `docs/` summarising the
steepener/flattener/butterfly/carry/basis directions of trade so
that future implementations can cross-reference rather than
re-derive. Bundled into Session 2H cleanup.

### Impact

These are extensions, not deviations. No changes to
`alphakit.core.protocols.StrategyProtocol`. Contract-level patterns
documented here for downstream families to follow.
