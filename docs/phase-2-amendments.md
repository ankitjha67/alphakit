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

---

## 2026-04-27 — Session 2E: drop energy_weather_premium (no citable systematic-strategy paper)

Context: The Session 2E commodity manifest listed
`energy_weather_premium` — long WTI ahead of winter on the basis of
a "winter pre-positioning" premium.

Honesty-check failure: There is no citable academic paper that
specifies a tradable systematic rule for a WTI pre-winter premium.
The phenomenon exists in commodity-trading folklore (and there is
related literature on natural-gas weather risk, e.g. Considine
2000), but applying a systematic long-WTI-into-Q4 rule with a
specific entry/exit logic is not anchored in a peer-reviewed paper
that this implementation could replicate verbatim.

Options considered:
- Substitute a generic "seasonal commodity premium" anchor (e.g.
  Sørensen 2002 on agricultural seasonality). Rejected: WTI is not
  agricultural and the seasonality mechanism (heating-demand
  premium) is materially different from grain-harvest seasonality.
- Use weather-derivative literature (Boyd/Mercer 2010, etc.).
  Rejected: that literature trades weather contracts, not WTI
  futures, and the bridge to WTI prices is not specified by any
  single paper.

Decision: Drop. Phase 2 ships without a WTI-pre-winter strategy.
Re-instatement would require a peer-reviewed paper specifying both
the entry rule and the empirical evidence — not currently
available.

Manifest impact: commodity family ships 14 strategies after this
drop; further drops in this session reduce that further (see
subsequent entries).

---

## 2026-04-27 — Session 2E: drop henry_hub_ttf_spread (no European nat gas data feed + thin systematic-strategy citation)

Context: The Session 2E commodity manifest listed
`henry_hub_ttf_spread` — mean-reversion on the US-EU natural gas
spread (Henry Hub vs Title Transfer Facility).

Honesty-check failure (two independent reasons):

1. **No European nat gas data feed wired up.** The `eia` adapter
   (Session 2B) covers US Energy Information Administration series
   only — it does not carry European TTF settlements. There is no
   ICE or Bloomberg adapter on the Phase 2 roadmap. Without TTF
   prices, the spread cannot be computed.
2. **Thin systematic-strategy citation.** Cross-region nat gas
   pricing has structural reasons (LNG arbitrage capacity, pipeline
   constraints) and there is descriptive literature on natural-gas
   market integration (Asche, Osmundsen & Sandsmark 2012), but a
   peer-reviewed paper specifying a tradable systematic strategy on
   the HH-TTF spread is not in evidence.

Decision: Drop. Phase 2 ships without an HH-TTF strategy.
Re-instatement would require both (a) a European nat gas data
adapter and (b) a peer-reviewed strategy paper; neither is on the
Phase 2 roadmap.

Manifest impact: commodity family ships 13 strategies after this
drop.

---

## 2026-04-27 — Session 2E: drop inventory_surprise (no consensus-expectations data)

Context: The Session 2E commodity manifest listed
`inventory_surprise` — trade WTI on the EIA weekly inventory report
versus consensus expectations, anchored on Linn & Zhu 2004 "Natural
gas prices and the gas storage report" (Journal of Futures Markets).

Honesty-check failure: Linn & Zhu (2004) construct the "surprise"
as **realised inventory − Bloomberg consensus forecast**. The
`eia` adapter carries the realised inventory series but **no
consensus-expectations data**. Bloomberg / Reuters survey data is
not in scope for any Phase 2 feed.

This is the same failure mode as `fed_funds_surprise` in Session
2D (Kuttner 2001 surprise required CME fed-funds-futures-implied
expectations, not on FRED). The honesty-bar precedent: drop rather
than substitute a synthetic-expectations methodology that would
materially change both the citation and the strategy's economic
content.

Options considered:
- Substitute an AR(1) or seasonal-average forecast as the
  "expected" inventory. Rejected: changes the methodology; would
  need its own peer-reviewed citation that specifies the
  forecast rule. Not on the Phase 2 roadmap.

Decision: Drop. Phase 2 ships without an inventory-surprise
strategy. Re-instatement requires a Bloomberg / Reuters consensus
data feed, which is a separate session-scale data-engineering
effort.

Manifest impact: commodity family ships 12 strategies after this
drop.

---

## 2026-04-27 — Session 2E: drop calendar_spread_corn (folk wisdom, not a citable systematic strategy)

Context: The Session 2E commodity manifest listed
`calendar_spread_corn` — corn calendar spread (March-July).

Honesty-check failure: Calendar-spread mechanics are well-
documented (Working 1949 "Theory of Inverse Carrying Charges"), but
the specific Mar-Jul corn spread as a *systematic strategy* with a
citable entry rule is folk wisdom from commodity-trading practice.
There is some practitioner literature (CME Group educational
material) but no peer-reviewed paper specifies a tradable rule.

Options considered:
- Generalise to a multi-commodity `ag_calendar_spread` with
  Sørensen 2002 (agricultural seasonality) and Working 1949 (calendar
  spread theory) as anchors. Rejected: that universe overlaps
  `grain_seasonality` (which is shipping in this session) and the
  differentiation gets thin — both would trade similar seasonal
  patterns on similar ag commodities.

Decision: Drop. The calendar-spread mechanic is captured implicitly
in `grain_seasonality` which trades outright seasonal positions on
corn / soybeans / wheat with a citable academic anchor. A separate
calendar-spread strategy without its own citation is redundant.

Manifest impact: commodity family ships 11 strategies after this
drop.

---

## 2026-04-27 — Session 2E: drop coffee_weather_asymmetry (folk wisdom, no academic anchor)

Context: The Session 2E commodity manifest listed
`coffee_weather_asymmetry` — long coffee during Brazilian winter
(June-August in the southern hemisphere) on the basis of frost-risk
asymmetry.

Honesty-check failure: The "Brazilian-winter coffee long" is folk
wisdom in commodity trading. Agronomic literature on frost
protection in coffee (Goetz 2000) is descriptive, not financial.
Letson/McCullough 2001 examines coffee weather impacts but does
not specify a tradable systematic rule. There is no peer-reviewed
academic paper that this implementation could replicate as a
systematic strategy.

Options considered:
- Retitle as `coffee_weather_volatility` and anchor on a generic
  weather-derivatives paper (e.g. Boyd & Mercer 2010). Rejected:
  weather-derivatives literature trades weather contracts, not
  coffee futures, and the bridge to coffee prices is not specified.

Decision: Drop. Phase 2 ships without a coffee strategy.
Re-instatement would require a peer-reviewed paper that
specifies both the weather-conditional entry rule and the
empirical evidence on coffee futures specifically — not currently
available.

Manifest impact: commodity family ships **10 strategies** after
this drop. Total Phase 2 strategy count revised: was 63 after
Session 2D drops, **now 58** after Session 2E's 5 drops.

---

## 2026-04-30 — Session 2E: signal-output semantics for multi-asset strategies

Context: Session 2D's `bond_tsmom_12_1` returned discrete
`{-1, 0, +1}` signals because it's single-asset; vol-scaling was
deferred to a portfolio overlay. Session 2E's multi-asset
cross-sectional strategies (`commodity_tsmom`, `metals_momentum`,
`commodity_curve_carry`, `cot_speculator_position`,
`wti_backwardation_carry`, `ng_contango_short`, `grain_seasonality`)
return vol-scaled weights at the strategy level, consistent with
Asness, Moskowitz & Pedersen (2013) §V methodology for
cross-instrument panels. Multi-leg spread strategies
(`crack_spread`, `crush_spread`, `wti_brent_spread`) return discrete
spread direction with leg ratios encoded as fixed parameters in the
strategy class.

Pattern:

* **Single-asset strategies** — return discrete signal; vol-scaling
  deferred to portfolio layer.
* **Multi-asset cross-sectional strategies** — return vol-scaled
  weights; cross-instrument scaling IS the methodology.
* **Multi-leg spread trades** (crack, crush, pairs) — return
  discrete spread direction; leg ratios encoded as fixed
  parameters.

Phase 1 trend family's `tsmom_12_1` (multi-asset cross-sectional)
also uses vol-scaled weights. `commodity_tsmom` is consistent with
this precedent.

No protocol change. No scope change. The `StrategyProtocol`
`generate_signals` method returns `DataFrame` in both cases — only
the values differ between discrete and continuous semantics.

---

## 2026-05-01 — Session 2F: drop diagonal_spread (no peer-reviewed systematic-strategy paper)

Context: The Session 2F options manifest listed `diagonal_spread`
— long ITM call / short OTM call with different expiries — as
strategy #11 of 20.

Honesty-check failure: The diagonal-spread mechanic is documented
in practitioner literature (McMillan 2002 "Options as a Strategic
Investment", CBOE educational material) as a directional-with-
theta-tilt structure, but no peer-reviewed paper specifies a
systematic entry / exit rule for diagonal spreads. The closest
academic literature on multi-expiry call structures
(Goyal/Saretto 2009 on calendar spreads) is already covered by
`calendar_spread_atm` shipping in this session. Adding a diagonal
without a distinct citation would duplicate the calendar trade
with an arbitrary strike-offset rule.

Options considered:
- Anchor on McMillan 2002 as a textbook reference. Rejected:
  practitioner textbooks fall below the Phase 2 honesty bar
  (peer-reviewed paper specifying both the rule and empirical
  evidence) — same standard that dropped `calendar_spread_corn`
  and `coffee_weather_asymmetry` in Session 2E.

Decision: Drop. Phase 2 ships without a diagonal-spread strategy.
Re-instatement would require a peer-reviewed paper specifying the
systematic rule.

Manifest impact: options family ships 19 strategies after this
drop; further drops in this session reduce that further (see
subsequent entries).

---

## 2026-05-01 — Session 2F: drop pin_risk_capture (substrate cannot represent pinning microstructure)

Context: The Session 2F options manifest listed `pin_risk_capture`
— write an ATM straddle on monthly expiry Friday and capture the
"pin" effect where index closes are statistically clustered at
round strikes — as strategy #13 of 20.

Honesty-check failure (two independent reasons):

1. **No systematic-strategy citation.** Ni, Pearson & Poteshman
   (2005) "Stock price clustering on option expiration dates"
   (Journal of Financial Economics, DOI 10.1016/j.jfineco.2004.09.005)
   *documents* the pinning phenomenon descriptively but does not
   specify a tradable systematic capture rule. The literature
   that follows (Pearson, Poteshman & White 2009; Avellaneda &
   Lipkin 2003) explores mechanism, not strategy.
2. **Synthetic chain has no microstructure.** Pinning is an
   intraday expiry-day microstructure effect driven by delta-hedging
   flows from market-makers near expiration. The synthetic-options
   adapter (ADR-005) has no bid-ask spread, no order book, and no
   intraday flow modelling — the substrate cannot represent the
   thing the strategy is meant to capture. P&L of an ATM straddle
   held into expiry on synthetic chains depends purely on terminal-
   day price moves under the realized-vol-derived diffusion.

Decision: Drop. Phase 2 ships without a pin-risk-capture strategy.
Re-instatement would require both (a) a peer-reviewed strategy
citation and (b) an intraday microstructure-modelling option chain
adapter; neither is on the Phase 2 roadmap.

Manifest impact: options family ships 18 strategies after this
drop.

---

## 2026-05-01 — Session 2F: drop earnings_vol_crush (synthetic chain has no earnings-vol structure)

Context: The Session 2F options manifest listed `earnings_vol_crush`
— long straddle 5 days before earnings, close after announcement
— as strategy #15 of 20. The plan's adversarial-review answer
proposed a "1.5x multiplier on trailing 90-day vol pre-earnings,
collapse post-earnings" workaround.

Honesty-check failure (two independent reasons):

1. **Synthetic chain has no earnings structure.** The
   synthetic-options adapter (ADR-005) prices every quote off a
   single realized-vol number per expiry-DTE bucket; there is no
   per-underlying earnings calendar, no IV-term-structure jump
   ahead of announcements, and no post-announcement vol collapse.
   Documented at `docs/feeds/synthetic-options.md` under "When it
   is inaccurate": *Earnings-vol strategies without a layered
   earnings-multiplier adjustment.*
2. **The "1.5x multiplier" workaround is fabricated.** The plan's
   own adversarial-review answer acknowledged the substrate gap
   and proposed multiplying trailing-90-day vol by 1.5 pre-earnings
   and collapsing it post — but that multiplier has no academic
   source. The empirical magnitude of pre-earnings IV expansion
   varies materially by ticker, market cap, and announcement
   recency (Patell/Wolfson 1981; Dubinsky/Johannes/Kaeck/Seeger
   2018). Hardcoding 1.5x would be a methodology fabrication, not
   an implementation of any peer-reviewed paper.

Decision: Drop. Phase 2 ships without an earnings-vol-crush strategy.
Re-instatement requires either (a) a real options chain adapter
that captures pre-earnings IV expansion empirically (Polygon, ADR-
004 stub) or (b) per-ticker earnings-calendar + IV-multiplier data
sourced from a peer-reviewed paper specifying the multipliers.
Neither is on the Phase 2 roadmap.

Manifest impact: options family ships 17 strategies after this
drop.

---

## 2026-05-01 — Session 2F: drop ratio_spread_put (folklore mechanic, overlaps put_skew_premium)

Context: The Session 2F options manifest listed `ratio_spread_put`
— long 1× ATM put, short 2× OTM put — as strategy #19 of 20. The
trade is sometimes called a "front-spread" or "1-by-2 put spread"
in practitioner literature.

Honesty-check failure (two independent reasons):

1. **No peer-reviewed systematic-strategy citation.** The 1-by-2
   put ratio is documented in practitioner texts (Natenberg 1994
   "Option Volatility and Pricing"; McMillan 2002) as a directional-
   with-skew-tilt structure but no peer-reviewed paper specifies a
   systematic entry / exit rule.
2. **Overlaps put_skew_premium.** The ratio's economic content is
   net short OTM puts (sells more skew than the long ATM put buys
   back). That is the same exposure as `put_skew_premium`
   (strategy #9, anchored on Bakshi/Kapadia/Madan 2003 +
   Garleanu/Pedersen/Poteshman 2009). Two strategies with
   substantially identical skew exposure would be a Phase 2 cluster
   under the cluster-detection methodology in master plan §6.

Decision: Drop. The skew-premium exposure is captured by
`put_skew_premium` shipping in this session. A separate ratio-
spread strategy without its own citation and with overlapping
economic content is redundant.

Manifest impact: options family ships 16 strategies after this
drop.

---

## 2026-05-01 — Session 2F: drop dispersion_trade_proxy (no individual-stock chains)

Context: The Session 2F options manifest listed
`dispersion_trade_proxy` — long index straddle, short basket-of-
constituents straddles — as strategy #20 of 20. The dispersion
trade monetises the spread between index implied correlation and
average single-name implied vol.

Honesty-check failure: The synthetic-options adapter (ADR-005) is
chain-only at the **index level** — `fetch_chain(underlying,
as_of)` builds a Black-Scholes chain from the underlying's price
history. To run a dispersion trade, the strategy needs simultaneous
chains on the index AND every constituent (typically S&P 500: 500
single-name chains). Building 500 synthetic chains at every
rebalance is mechanically possible but the approach has no
defensible substrate: synthetic chains have no skew (`docs/feeds/
synthetic-options.md`), and dispersion is fundamentally a
correlation-of-skew trade. Without real per-name skew, the strategy
cannot test what it claims to test.

Options considered:
- Generate 500 single-name synthetic chains and run the trade
  anyway. Rejected: P&L would reflect realized-vol-of-vol across
  the constituent universe, which is a different economic content
  from the dispersion trade described in Driessen/Maenhout/Vilkov
  2009 "The Price of Correlation Risk".
- Use real S&P constituent chains via Polygon. Rejected: ADR-004
  Polygon adapter is a stub for Phase 2; real chain data is
  Phase 3+.

Decision: Drop. Phase 2 ships without a dispersion-trade strategy.
Re-instatement requires real per-name option chains (Polygon, ADR-
004 promotion to active in Phase 3+).

Manifest impact: options family ships **15 strategies** after this
drop. Total Phase 2 strategy count revised: was 58 after Session 2E's
5 drops, **now 53** after Session 2F's 5 drops.

---

## 2026-05-01 — Session 2F: reframe wheel_strategy → bxmp_overlay (Whaley 2002 + Israelov/Nielsen 2014 + CBOE BXMP)

Context: The Session 2F options manifest listed `wheel_strategy`
(strategy #3 of 20) — the practitioner "wheel": sell cash-secured
put → if assigned, sell covered call → if assigned again, restart.

Honesty-check finding: The "wheel" is folklore, not academic
literature. There is no peer-reviewed paper that specifies the
wheel's entry / exit / roll logic as a systematic strategy.
However, the wheel's economic content — alternating short-put
and short-call exposure on the same underlying — is captured by
the **CBOE BXMP index** (BuyWrite-PutWrite combination), which has
a documented methodology and is anchored academically by Whaley
(2002) on BXM construction and Israelov/Nielsen (2014) on the
covered-call / cash-secured-put put-call-parity equivalence.

Resolution: Reframe `wheel_strategy` → `bxmp_overlay`. The slug
references the BXMP index directly, slots alongside
`bxm_replication` for clean naming differentiation in this session,
and carries an academic-anchored methodology rather than folklore.
The economic content is identical (alternating short-put / short-
call writes on a single underlying); only the citation and the
implementation-rule source change.

`paper.md` for `bxmp_overlay` cites:
- **Foundational:** Whaley (2002) "Risk and Return of the CBOE
  BuyWrite Monthly Index" (J of Derivatives Vol 10 No 2, Winter 2002,
  DOI 10.3905/jod.2002.319188).
- **Primary:** Israelov & Nielsen (2014) "Covered Call Strategies:
  One Fact and Eight Myths" (Financial Analysts Journal Vol 70
  No 6, DOI 10.2469/faj.v70.n6.5) plus the CBOE BXMP index
  methodology document.

Manifest impact: options family ship count unchanged (15). Slug
list updated: `wheel_strategy` is not a Phase 2 slug;
`bxmp_overlay` ships in its place.

---

## 2026-05-01 — Session 2F: reframe vix_front_back_spread → vix_3m_basis (substrate constraint: no back-month VIX futures)

Context: The Session 2F options manifest listed
`vix_front_back_spread` (strategy #8 of 20) — trade the slope of
the VIX futures curve via a long-front / short-back (or vice
versa) calendar spread on VIX futures.

Honesty-check failure: The yfinance-futures adapter (Phase 2
Session 2B) exposes a single continuous-front-month VIX symbol
(`VIX=F`) — Yahoo handles the roll. **Back-month VIX futures
contracts (e.g. specific maturities like `VXM26`, `VXJ26`) are not
available via yfinance.** Without a back-month leg, the front-back
calendar spread cannot be constructed.

Options considered:
- Add a Polygon-based VIX-futures-by-maturity adapter. Rejected:
  ADR-004 stub for Phase 2; real per-maturity futures are Phase 3+.
- Add a CME-direct adapter for VIX futures. Rejected: not on the
  Phase 2 free-and-open-source feed roadmap.

Resolution: Reframe `vix_front_back_spread` → `vix_3m_basis`. The
substrate that *does* exist via yfinance equity passthrough is the
spot VIX index `^VIX` and the 3-month constant-maturity VIX index
`^VIX3M` (CBOE-published). The basis between these two is well-
studied in Alexander, Korovilas & Kapraun (2015) "Diversification
with Volatility Products" — the academic anchor for the term-
structure trade on real (not realized-vol-proxied) VIX data.

`paper.md` for `vix_3m_basis` cites:
- **Foundational:** Whaley (2009) "Understanding VIX" (J of
  Portfolio Management, DOI 10.3905/JPM.2009.35.2.014).
- **Primary:** Alexander, Korovilas & Kapraun (2015)
  "Diversification with Volatility Products" (J of International
  Money and Finance, DOI 10.1016/j.jimonfin.2015.10.005 or
  pre-print equivalent).

Differentiated from `vix_term_structure_roll` shipping in the same
session, which trades `^VIX` (spot) vs `VIX=F` (front-month future)
per Simon & Campasano (2014). Two distinct term-structure trades:
spot-vs-front-future (Simon/Campasano) vs spot-vs-3M-constant-
maturity (Alexander et al.). No cluster overlap; the two basis
measures move on different schedules.

Manifest impact: options family ship count unchanged (15). Slug
list updated: `vix_front_back_spread` is not a Phase 2 slug;
`vix_3m_basis` ships in its place.

`known_failures.md` for both `vix_term_structure_roll` and
`vix_3m_basis` will document the yfinance ^-prefix passthrough
assumption: real-data shape verification is deferred to Session 2H
(Phase 2 closeout) when the benchmark runner exercises real feeds.
Integration tests mock the OHLCV response shape.

---

## 2026-05-01 — Session 2F: reframe weekly_theta_harvest → weekly_short_volatility (Carr-Wu 2009 + Bondarenko 2003/2014)

Context: The Session 2F options manifest listed
`weekly_theta_harvest` (strategy #14 of 20) — a 7-day OTM put/call
write to "harvest theta" on weekly expiries.

Honesty-check finding: "Theta harvesting" is practitioner
terminology, not an academic concept. The economic content is
**short volatility on a weekly horizon** — the strategy collects
the variance risk premium over a 7-day window. The cleaner
academic framing anchors the trade in the variance-risk-premium
literature (Carr/Wu 2009, Bondarenko 2003/2014), which establishes
that systematic short-vol writes earn a positive risk premium
across most horizons including weekly.

Resolution: Reframe `weekly_theta_harvest` →
`weekly_short_volatility`. The descriptive slug "weekly" indicates
the differentiating parameter from monthly siblings (`#1
covered_call_systematic`, `#2 cash_secured_put_systematic`,
`#4 iron_condor_monthly`, `#5 short_strangle_monthly`); "short
volatility" replaces the practitioner "theta harvest" with the
academic framing. Avoids slug ambiguity with `#16
variance_risk_premium_synthetic` (variance-swap-replication-via-
straddle, monthly) by emphasising the weekly horizon and the
short-volatility-write mechanic (rather than variance-swap
replication).

`paper.md` for `weekly_short_volatility` cites:
- **Foundational:** Carr & Wu (2009) "Variance Risk Premia"
  (Review of Financial Studies Vol 22 No 3, DOI
  10.1093/rfs/hhn038) — establishes the cross-horizon magnitude
  of the variance risk premium.
- **Primary:** Bondarenko (2003/2014) "Why Are Put Options So
  Expensive?" (Quarterly Journal of Finance Vol 4 No 1, DOI
  10.1142/S2010139214500050) — short-volatility writes earn the
  premium systematically.

Manifest impact: options family ship count unchanged (15). Slug
list updated: `weekly_theta_harvest` is not a Phase 2 slug;
`weekly_short_volatility` ships in its place.

---

## 2026-05-01 — Session 2F: vix_term_structure_roll citations refined (foundational + primary pair)

Context: The Session 2F options manifest listed
`vix_term_structure_roll` (strategy #7 of 20) — long VXX when
spot VIX < VIX6M, short when above. The original session brief
suggested Whaley (2009) "Understanding VIX" + Alexander, Korovilas
& Kapraun (2015) as paired anchors.

Refinement: For Phase 2 implementation purposes, the cleaner
foundational + primary citation pair is **Whaley 2009 (foundational
on VIX construction and futures pricing) + Simon & Campasano 2014
(primary on the spot-vs-front-month-future basis trade)**. Simon
& Campasano explicitly study the basis between the spot VIX index
and the front-month VIX future — which is exactly what
`vix_term_structure_roll` trades using `^VIX` (yfinance) vs
`VIX=F` (yfinance-futures). Alexander et al. (2015) is reserved
for `vix_3m_basis` (the spot-vs-3M-constant-maturity trade), per
the previous reframe entry.

This is also a **differentiation** entry: Phase 1's
`vix_term_structure` strategy (volatility family, Simon/Campasano
2014 anchored) uses **realized vol of SPY as a VIX proxy** because
Phase 1 had no real VIX feed. Phase 2's `vix_term_structure_roll`
consumes **real `^VIX` and `VIX=F` data** via the equity and futures
yfinance passthroughs. The two slugs co-exist on main: Phase 1's
slug stays for the realized-vol-proxy methodology (Phase 1
honesty-frame, ADR-002 mild-deviation canonical slug); Phase 2's
new slug ships the real-data variant.

`paper.md` for `vix_term_structure_roll` will:
1. Cite Whaley 2009 as the foundational VIX-construction paper.
2. Cite Simon & Campasano 2014 as the primary methodology anchor.
3. Cross-reference Phase 1's `vix_term_structure` and explicitly
   document the data-source upgrade (realized-vol proxy →
   real `^VIX` / `VIX=F`).
4. Document the yfinance ^-prefix passthrough assumption in
   `known_failures.md`, deferring real-data shape verification to
   Session 2H.

Manifest impact: options family ship count unchanged (15). Slug
unchanged. Citation pair refined; differentiation from Phase 1
counterpart documented.

---

## 2026-05-01 — Session 2F: bridge architecture extension for discrete-traded legs

Context: Session 2F's first strategy
(`covered_call_systematic`, Commit 2 reverted before push)
exposed an architectural mismatch in the
`StrategyProtocol → vectorbt_bridge` contract. The bridge interpreted
*every* output column under continuous-rebalance
`SizeType.TargetPercent` semantics — correct for the 83 strategies
through Session 2E (TSMOM, mean-reversion, carry, value, volatility,
rates, commodity, all expressing continuous-exposure positions) but
**fundamentally wrong for discretely-traded option legs whose price
legitimately decays from premium → 0 across a monthly cycle**.

Diagnostic evidence (captured during Session 2F bridge investigation):

* On a synthetic 21-bar panel with SPY flat at $400 and a call leg
  decaying linearly $8.00 → $0.01, a static `weight = -1.0` on the
  call leg every bar caused the bridge to sell ever-more contracts
  to maintain the −100 % dollar target. The cumulative short P&L
  scaled with the price ratio, producing a 9× nonsense gain on a
  trade whose analytic covered-call P&L is +$7.99.
* `vectorbt` fails fast on zero-price bars (`order.price must be
  finite and greater than 0`); `backtrader_bridge` survives zero
  prices (it has a `if price <= 0: continue` guard) but produces
  the same continuous-rebalance nonsense P&L silently.
* The `lean_bridge` is the canonical Phase 3 path for options
  (per its own module docstring) but is currently a stub.
* Empirically: vectorbt's `SizeType.Amount` with weights non-zero
  only on the write bar reproduces the analytic +$7.99 P&L
  exactly. The bridge primitive exists; the dispatch was missing.

Resolution: Extend `StrategyProtocol` with an **optional**
`discrete_legs: tuple[str, ...]` metadata attribute. Strategies
with write-and-hold legs declare them; `vectorbt_bridge` dispatches
to `SizeType.Amount` for those columns and `SizeType.TargetPercent`
for the rest using vectorbt's per-column `size_type` array
parameter (no two-portfolio merge needed).

The attribute is documented in the Protocol *docstring* but **not
declared on the Protocol class body**. Reason: Python's
`@runtime_checkable Protocol` enforces strict attribute-existence
on `isinstance()` checks regardless of declared defaults — adding
`discrete_legs` to the body would break `isinstance(strategy,
StrategyProtocol)` for every strategy that does not redeclare the
attribute (verified empirically). Instead, a centralised helper
`alphakit.core.protocols.get_discrete_legs(strategy)` performs
`getattr(strategy, "discrete_legs", ())` with type validation, and
`vectorbt_bridge` calls the helper to fetch the dispatch metadata.

Scope:

* `packages/alphakit-core/alphakit/core/protocols.py` —
  `StrategyProtocol` docstring extended with the Optional
  class-level metadata section; new `get_discrete_legs(strategy)`
  helper with type validation.
* `packages/alphakit-bridges/alphakit/bridges/vectorbt_bridge.py` —
  refactored to compute a per-column `size_type` array from
  `get_discrete_legs(strategy)`. Continuous-only path
  (no `discrete_legs`) is byte-identical to the pre-fix behaviour.
* `packages/alphakit-bridges/tests/test_vectorbt_bridge.py` —
  new test file with bridge-contract tests covering: continuous-
  only path (backwards compatibility), legacy-class-without-the-
  attribute path, discrete-only Amount semantics matching analytic
  premium minus intrinsic, mixed continuous + discrete covered-
  call P&L matching analytic, validation paths (non-tuple,
  non-string entries, missing-column).
* `backtrader_bridge.py` update: **deferred**. backtrader has the
  same continuous-rebalance architectural mismatch but is not
  blocking Session 2F (vectorbt is the primary engine for Session
  2F backtests). A follow-up amendment will track the backtrader
  fix when an options strategy exercises that bridge.
* `lean_bridge.py`: still a stub; remains Phase 3.

No protocol breaking change for existing strategies. The 83
strategies through Session 2E do not declare `discrete_legs` and
are routed through the unchanged `TargetPercent` code path.
`isinstance(strategy, StrategyProtocol)` continues to pass for all
of them.

Unblocks Session 2F: 14 of 15 options strategies have write-and-
hold legs and need this metadata to produce meaningful backtest
P&L through the bridge. `covered_call_systematic` (re-implementing
in Commit 2 after this fix lands) declares
`discrete_legs = (call_leg_symbol,)` and exercises the new dispatch
path through its integration tests.

---

## 2026-05-13 — Session 2F: `delta_hedged_straddle` trailing-cycle flush

**Context.** Codex AI review on PR #16 flagged a latent correctness
bug in `delta_hedged_straddle`'s stateful coupling. The `cycles`
list was only appended inside the close-at-expiry branch of
`make_legs_prices`, so truncated windows (window ending mid-cycle)
emitted zero hedge weights on the underlying for trailing bars
while the option-leg lifecycle detection correctly fired — the
final straddle was held unhedged end-to-end, producing directional
P&L bias.

**Resolution.** Flush the trailing open cycle on the last bar of
the window before assigning `self._cycles`. The cycle is treated as
closing on the last bar of the window:

    if current_expiry is not None and current_write_idx is not None:
        cycles.append(
            _CycleMetadata(
                write_idx=current_write_idx,
                close_idx=len(idx) - 1,
                expiry=current_expiry,
                strike=cast(float, current_strike),
                sigma=cast(float, current_sigma),
            )
        )
    self._cycles = cycles

`gamma_scalping_daily` inherits the fix via composition.

**Severity.** Latent on the existing year-aligned test windows
(panels run to/past final expiry). Would surface on Phase 3
rolling / walk-forward harnesses, mid-month start dates, or
portfolio construction that doesn't honour monthly expiry cycle
boundaries.

**Scope.**

* `packages/alphakit-strategies-options/alphakit/strategies/
  options/delta_hedged_straddle/strategy.py` — added trailing-cycle
  flush block at end of `make_legs_prices` (immediately before
  `self._cycles = cycles`).
* `packages/alphakit-strategies-options/alphakit/strategies/
  options/delta_hedged_straddle/tests/test_unit.py` — added
  `test_truncated_window_emits_trailing_hedge_weights` regression
  test asserting the trailing cycle is flushed and produces
  non-zero hedge weights on the underlying in the final 10 bars.
* `packages/alphakit-strategies-options/alphakit/strategies/
  options/delta_hedged_straddle/known_failures.md` — added §11
  documenting the trailing-cycle-flush invariant.

**Lessons learned.** Gate 3 review focused on
`covered_call_systematic` (no trailing-cycle issue — single-leg
short-vol with `discrete_legs` lifecycle handled entirely by
bridge-side lifecycle detection). Gate 4 spot check chose other
novel patterns. Future gate-3 selections should include any
strategy that introduces a NEW state primitive.
`delta_hedged_straddle` introduced cycle metadata as a state
primitive (the first strategy to maintain stateful coupling
between `make_legs_prices` and `generate_signals` via
`self._cycles`) but wasn't selected for either gate review.

External AI code review (Codex) caught what human review missed.
The process loop is: gate review identifies architectural novelty
+ spot-check exercises substrate edge cases + AI review catches
state-machine completeness. All three are valid catches.

---

## 2026-05-15 — Session 2G: drop cape_country_rotation (cluster duplicate of Phase 1 country_cape_rotation)

Context: The Session 2G macro/GTAA manifest listed
`cape_country_rotation` (strategy #6 of 15) — rank countries by CAPE
(cyclically-adjusted P/E), long the cheapest 25%, attributed in the
master plan to "Shiller/Siegel 1998".

Honesty-check failure: Two compounding problems.

1. **Cluster duplicate.** Phase 1 already ships
   `packages/alphakit-strategies-value/alphakit/strategies/value/country_cape_rotation/`
   citing Faber (2014) "Global Value: Building Trading Models with the
   10 Year CAPE" (SSRN DOI 10.2139/ssrn.2129474). The Phase 1 mechanic
   is "rank countries by 10-year CAPE, rotate into the cheapest
   quartile, rebalance monthly". This is exactly the master-plan
   description of `cape_country_rotation` (rank countries by CAPE,
   long cheapest 25%). Same paper-anchor genre, same universe (country
   equity indices), same cross-sectional ranking, same rebalance
   cadence — no methodological differentiation available.
2. **Citation does not match the strategy.** The master plan attributes
   the strategy to "Shiller/Siegel 1998". Campbell & Shiller (1998)
   "Valuation Ratios and the Long-Run Stock Market Outlook" (J of
   Portfolio Management) is about *US-only* long-horizon return
   prediction from CAPE — not a country-rotation strategy. Siegel's
   contemporaneous work (*Stocks for the Long Run*, 1998) is a
   long-only buy-and-hold treatise, not a country-rotation rule.
   Faber (2014) is the canonical country-CAPE-rotation paper, and
   Phase 1 already cites it.

Options considered:
- Ship a "real-CAPE" variant using actual country CAPE data
  (StarCapital, Barclays). Rejected: those datasets are licensed and
  not in the Phase 2 free-and-open-source feed set. The FRED adapter
  carries US-only macro series. yfinance carries price data, not
  earnings-smoothed valuation ratios.
- Ship a quarterly-rebalance variant with a different cheap-quartile
  threshold. Rejected: parameterisation differences are not
  methodological differentiation. Cluster-analysis would flag the two
  strategies as ρ ≈ 0.95-1.0 redundant.

Decision: Drop. Phase 2 ships without a second country-CAPE rotation
strategy. Phase 1 `country_cape_rotation` (Faber 2014) covers the
mechanic.

Manifest impact: macro family ships 14 strategies after this drop;
further Session 2G drops reduce the count further (see subsequent
entries).

---

## 2026-05-15 — Session 2G: drop dollar_strength_tilt (no peer-reviewed anchor for "DXY momentum → EM equity short")

Context: The Session 2G macro/GTAA manifest listed
`dollar_strength_tilt` (strategy #7 of 15) — "short EM when DXY
rising". The master plan provided no peer-reviewed citation.

Honesty-check failure: The "short EM equity when dollar strengthening"
signal is a Bloomberg-tape / sell-side-research narrative, not a
published systematic strategy. Two adjacent literatures exist but
neither anchors the specific signal proposed:

- **FX-carry literature.** Lustig, Roussanov & Verdelhan (2014)
  "Countercyclical Currency Risk Premia" (JFE, DOI
  10.1016/j.jfineco.2013.10.009) and the prior Lustig-Roussanov-
  Verdelhan (2011) "Common Risk Factors in Currency Markets" (RFS,
  DOI 10.1093/rfs/hhr068) document a dollar-as-risk-factor premium
  *in currency carry returns*, not in EM equity returns. Phase 1
  `fx_carry_em` already exercises this literature on the EM-currency
  side directly.
- **Equity-vs-currency literature.** Cenedese, Sarno & Tsiakas (2014)
  "Foreign Exchange Risk and the Predictability of Carry Trade
  Returns" (J of Banking & Finance, DOI 10.1016/j.jbankfin.2014.01.008)
  and Dahlquist & Hasseltoft (2013) "International Bond Risk Premia"
  (J of International Economics) treat the dollar as a global-factor
  exposure, not a stand-alone EM-equity signal. Neither paper
  specifies a "long-DXY-momentum, short-EEM" rule with the entry /
  exit / sizing logic this implementation would replicate verbatim.

Options considered:
- Reframe as "dollar-as-global-factor regime tilt" anchored on
  Verdelhan (2018) "The Share of Systematic Variation in Bilateral
  Exchange Rates" (J of Finance, DOI 10.1111/jofi.12587). Rejected:
  Verdelhan's "dollar factor" is a *currency-portfolio* risk factor,
  not a tradable equity-allocation signal. The bridge from
  "dollar-factor exposure" to "short EM equity allocation" is a
  practitioner inference not supported by the paper itself.
- Ship the signal as folklore with a paper.md disclaimer. Rejected:
  Phase 2 honesty-check explicitly disallows folklore strategies
  without peer-reviewed citations. The Session 2E precedent
  (`coffee_weather_asymmetry`, `calendar_spread_corn`) and Session 2F
  precedent (`diagonal_spread`, `ratio_spread_put`) both dropped
  similar folklore signals.

Decision: Drop. Phase 2 ships without a stand-alone DXY-momentum-EM-
equity signal. FX-side dollar premia are covered by Phase 1
`fx_carry_em` and `fx_carry_g10`; cross-asset regime allocators in
this session (`growth_inflation_regime_rotation`,
`yield_curve_regime_allocation`, `recession_probability_rotation`,
`fed_policy_tilt`, `inflation_regime_allocation`) use peer-reviewed
state variables.

Manifest impact: macro family ships 13 strategies after this drop.

---

## 2026-05-15 — Session 2G: drop dual_momentum_gtaa (cluster duplicate of Phase 1 dual_momentum_gem)

Context: The Session 2G macro/GTAA manifest listed
`dual_momentum_gtaa` (strategy #13 of 15) — "absolute + relative
momentum overlay", attributed to "Antonacci 2015".

Honesty-check failure: Hard cluster duplicate of Phase 1
`packages/alphakit-strategies-trend/alphakit/strategies/trend/dual_momentum_gem/`.
Both implement Antonacci's Global Equities Momentum:

1. **Same paper.** Phase 1 `dual_momentum_gem` cites Antonacci (2014)
   *Dual Momentum Investing* (McGraw-Hill, ISBN 978-0071849449) plus
   the working-paper version Antonacci (2012) "Risk Premia Harvesting
   Through Dual Momentum" (SSRN 2042750, DOI 10.2139/ssrn.2042750).
   The master plan's "Antonacci 2015" citation appears to be a typo —
   there is no 2015 Antonacci paper that establishes a separate dual-
   momentum framework. The book is 2014; the working paper is 2012.
2. **Same mechanic.** Both strategies compute (i) absolute momentum
   (asset vs risk-free 12-month return) for the regime gate, then
   (ii) relative momentum (US vs International equity) for the asset
   selection, then (iii) bond fallback when the absolute filter fails.
3. **Same universe template.** Both strategies operate on a three-leg
   universe of US equity + International equity + bonds with a cash /
   short-Treasury fallback (Phase 1 default tickers: SPY, VEU, AGG,
   SHY).

Options considered:
- Ship a "5-asset dual momentum" variant. Rejected: that variant is
  already shipping as `vigilant_asset_allocation_5` in this session
  (Keller-Keuning 2017 VAA), which extends the dual-momentum logic
  with breadth-momentum aggregation and canary-asset fallback — a
  materially different mechanic.
- Ship a "monthly dual momentum on commodity-asset universe". Rejected:
  Antonacci does not specify this; would be folklore extension of his
  framework rather than a separate published strategy.

Decision: Drop. Phase 2 ships without a second dual-momentum
strategy. Phase 1 `dual_momentum_gem` covers the mechanic faithfully.

Manifest impact: macro family ships 12 strategies after this drop.

---

## 2026-05-15 — Session 2G: drop inflation_tilt_60_40_overlay (borderline cluster duplicate of inflation_regime_allocation)

Context: The Session 2G macro/GTAA manifest listed
`commodity_overlay_gtaa` (strategy #15 of 15) — "base 60/40 plus
commodity tilt when inflation rising". The pre-flight honesty check
proposed reframing the slug to `inflation_tilt_60_40_overlay` anchored
on Erb/Harvey (2006) + Greer (2000).

Honesty-check finding: The reframed slug would still ship alongside
`inflation_regime_allocation` (strategy #11) in the same session.
Both strategies:

- Read the same FRED CPI series (`CPIAUCSL` or `CPILFESL`) as the
  driving state variable.
- Trigger on the same "inflation rising" regime classification.
- Tilt allocation toward commodities (GSCI, DBC, GLD) when the
  regime fires.

The mechanical differences (full 4-asset rotation vs overlay on a 60/40
base; 4-cell regime vs 2-cell rising/falling) are parameterisation
choices over the same underlying signal driver, not methodologically
distinct strategies. Cluster analysis would flag them as ρ ≈ 0.80-0.95
redundant.

Precedent: Session 2F shipped 3 deliberate-redundancy pairs
(`covered_call_systematic` + `bxm_replication` on Whaley 2002;
`cash_secured_put_systematic` as the put-call-parity sibling;
`delta_hedged_straddle` + `gamma_scalping_daily` on Carr-Wu 2009).
Each pair has a *distinct* citation anchor or implementation framing.
Adding a fourth pair to v0.2.0 cluster analysis with the *same*
citation candidates (Erb/Harvey 2006, Neville 2021) and the *same*
signal driver would dilute the cluster-analysis signal without
adding methodological information.

Options considered:
- Ship both with a deliberate-redundancy paper.md note. Rejected:
  the redundancy is not parity-driven (like CSP↔CC) or framing-driven
  (like delta-hedged-straddle vs gamma-scalping) — it is the same
  paper applied with different parameterisations. That fails the
  Session 2F "deliberate-pair" bar.
- Ship as a single combined strategy. Rejected: would force a choice
  between the rotation mechanic (Neville 2021 4-cell) and the overlay
  mechanic; better to ship the rotation faithfully and defer overlay
  variants to Phase 3.

Decision: Drop `commodity_overlay_gtaa` / `inflation_tilt_60_40_overlay`.
`inflation_regime_allocation` covers the CPI-driven commodity tilt
faithfully under Neville et al. (2021) + Erb/Harvey (2006).

Manifest impact: macro family ships 11 strategies after this drop —
the final Session 2G ship count.

---

## 2026-05-15 — Session 2G: reframe risk_parity_3asset → risk_parity_erc_3asset (Maillard-Roncalli-Teiletche 2010 + Asness-Frazzini-Pedersen 2012)

Context: The Session 2G macro/GTAA manifest listed `risk_parity_3asset`
(strategy #2 of 15) — equal-risk-contribution weighting across stocks,
bonds, commodities, attributed in the master plan to "Bridgewater
All-Weather".

Honesty-check finding: "Bridgewater All-Weather" is a fund-marketing
attribution, not a peer-reviewed paper. Bridgewater's All-Weather
methodology has never been published in detail; the public-domain
documents are marketing summaries. The peer-reviewed literature for
the equal-risk-contribution (ERC) construction does exist and is
specific enough to replicate verbatim.

Resolution: Reframe `risk_parity_3asset` → `risk_parity_erc_3asset`
(slug clarifies the ERC construction explicitly, distinguishing it
from naive risk parity / volatility-parity variants). Cite:

- **Foundational:** Maillard, S., Roncalli, T. & Teiletche, J. (2010)
  "The Properties of Equally Weighted Risk Contribution Portfolios"
  (Journal of Portfolio Management Vol 36 No 4, DOI
  10.3905/jpm.2010.36.4.060). The canonical paper on ERC: defines
  the fixed-point iteration that produces equal-marginal-risk-
  contribution weights from a covariance matrix.
- **Primary:** Asness, C. S., Frazzini, A. & Pedersen, L. H. (2012)
  "Leverage Aversion and Risk Parity" (Financial Analysts Journal
  Vol 68 No 1, DOI 10.2469/faj.v68.n1.1). Provides the risk-premium
  justification for ERC weighting and the empirical evidence across
  stock-bond-commodity multi-asset panels.

The covariance estimation, ERC solver, and rolling-window logic are
shared across `risk_parity_erc_3asset`, `min_variance_gtaa`, and
`max_diversification` via the `alphakit.strategies.macro._covariance`
helper module (Commit 1.5 in the Session 2G ship order; gate-3
reviewed before the first dependent strategy ships).

Manifest impact: macro family ship count unchanged at this stage.
Slug list updated: `risk_parity_3asset` is not a Phase 2 slug;
`risk_parity_erc_3asset` ships in its place.

---

## 2026-05-15 — Session 2G: reframe economic_regime_rotation → growth_inflation_regime_rotation (Ilmanen-Maloney-Ross 2014)

Context: The Session 2G macro/GTAA manifest listed
`economic_regime_rotation` (strategy #5 of 15) — "rotate based on
CPI/GDP growth regimes". The master plan provided no citation.

Honesty-check finding: "CPI/GDP regime rotation" without a paper-
anchor is folklore. The All-Weather conceptual framing of "four
regimes from the cross of growth and inflation expectations" has been
formalised in the peer-reviewed literature by Ilmanen, Maloney & Ross
(2014).

Resolution: Reframe `economic_regime_rotation` →
`growth_inflation_regime_rotation` (slug specifies the regime
dimensions explicitly). Cite as sole primary anchor:

- **Primary:** Ilmanen, A., Maloney, T. & Ross, A. (2014) "Exploring
  Macroeconomic Sensitivities: How Investments Respond to Different
  Economic Environments" (Journal of Portfolio Management Vol 40 No 3,
  DOI 10.3905/jpm.2014.40.3.087). Specifies the 4-cell growth ×
  inflation regime taxonomy (rising-growth / falling-growth crossed
  with rising-inflation / falling-inflation) and the empirical asset-
  class sensitivities (equities long rising-growth; bonds long
  falling-growth; commodities long rising-inflation; cash long
  falling-inflation) that drive the regime-conditional allocation.

The single-paper citation pattern matches Session 2F precedent of
`calendar_spread_atm` citing Goyal/Saretto (2009) as the sole anchor —
when a paper specifies *both* the regime taxonomy and the empirical
asset-class sensitivities, a foundational separate citation is not
needed.

Architectural note: this is the most complex of the regime allocators
shipping in Session 2G (4-cell regime requires both growth and
inflation series, vs single-series regime classifiers like
`yield_curve_regime_allocation` or `recession_probability_rotation`).
The regime-state primitive uses the Session 2D "informational columns
with zero weight" pattern (`docs/phase-2-amendments.md` §2D
sub-section 3): FRED growth and inflation series enter
`generate_signals` as input DataFrame columns and carry zero weight;
tradable assets (equities, bonds, commodities, cash) carry the
regime-conditional allocation.

Manifest impact: macro family ship count unchanged at this stage.
Slug list updated: `economic_regime_rotation` is not a Phase 2 slug;
`growth_inflation_regime_rotation` ships in its place.

---

## 2026-05-15 — Session 2G: reframe yield_curve_regime_asset_allocation → yield_curve_regime_allocation (Estrella-Hardouvelis 1991 + Ang-Piazzesi-Wei 2006)

Context: The Session 2G macro/GTAA manifest listed
`yield_curve_regime_asset_allocation` (strategy #8 of 15) — "steep
curve → equities; flat → bonds". The master plan provided no
citation.

Honesty-check finding: The slug is unnecessarily long. The mechanic
itself is academically well-anchored — the yield-curve term spread
as a state variable for equity-vs-bond allocation has been studied
since Estrella & Hardouvelis (1991) and extended through the modern
predictive-regression literature.

Resolution: Reframe `yield_curve_regime_asset_allocation` →
`yield_curve_regime_allocation` (shorter slug, same mechanic). Cite:

- **Foundational:** Estrella, A. & Hardouvelis, G. A. (1991) "The Term
  Structure as a Predictor of Real Economic Activity" (J of Finance
  Vol 46 No 2, DOI 10.1111/j.1540-6261.1991.tb03747.x). The seminal
  result that the slope of the Treasury yield curve forecasts
  economic activity 1–4 quarters out, providing the macroeconomic
  rationale for using the slope as an equity-vs-bond allocation
  signal.
- **Primary:** Ang, A., Piazzesi, M. & Wei, M. (2006) "What Does the
  Yield Curve Tell Us About GDP Growth?" (J of Econometrics Vol 131
  No 1-2, DOI 10.1016/j.jeconom.2005.01.032). Documents the predictive
  power of the 3-month / 10-year yield-curve slope (`T10Y3M` on FRED)
  for subsequent GDP growth — and via the standard equity-vs-bond
  cyclical-allocation logic, for equity-vs-bond return differentials.
  The empirical regime thresholds (positive-slope / flat / inverted)
  drive the strategy's allocation switches.

Differentiated from `recession_probability_rotation` (also in this
session) which uses the Cleveland Fed's recession-probability series
(`RECPROUSM156N`) — a derived probability output rather than the raw
slope — and from `breakeven_inflation_rotation` (Phase 2 Session 2D)
which trades TIPS-vs-nominal breakeven, not equity-vs-bond. No
cluster overlap with either.

Manifest impact: macro family ship count unchanged. Slug list updated:
`yield_curve_regime_asset_allocation` is not a Phase 2 slug;
`yield_curve_regime_allocation` ships in its place.

---

## 2026-05-15 — Session 2G: reframe global_macro_momentum → gtaa_cross_asset_momentum (AMP 2013 + Hurst-Ooi-Pedersen 2017)

Context: The Session 2G macro/GTAA manifest listed
`global_macro_momentum` (strategy #12 of 15) — "12-1 momentum across
24 asset class ETFs". The master plan provided no citation.

Honesty-check finding: A 12-1 multi-asset momentum strategy needs to
clearly differentiate from two cluster anchors already shipping in
AlphaKit:

1. Phase 1 `tsmom_12_1` (Moskowitz/Ooi/Pedersen 2012) trades time-
   series momentum across *commodity-, currency-, equity-index-, and
   bond-* **futures** (58 instruments in MOP). Futures universe, not
   ETF universe.
2. Phase 1 `dual_momentum_gem` (Antonacci 2014) trades a 3-leg
   absolute + relative momentum on US / international / bonds.

The Session 2G strategy must (a) cite a paper that supports a
multi-asset *ETF* universe specifically, and (b) be tractably
differentiated from both Phase 1 anchors by universe breadth and
ranking mechanic.

Resolution: Reframe `global_macro_momentum` → `gtaa_cross_asset_momentum`
(slug references the GTAA — global tactical asset allocation —
framing explicitly and the cross-asset universe). Cite:

- **Foundational:** Hurst, B., Ooi, Y. H. & Pedersen, L. H. (2017)
  "A Century of Evidence on Trend-Following Investing" (J of Portfolio
  Management Vol 44 No 1, DOI 10.3905/jpm.2017.44.1.015). Extends
  MOP 2012's time-series momentum result to a century of data across
  multiple asset classes — establishes the long-horizon evidence for
  cross-asset momentum.
- **Primary:** Asness, C. S., Moskowitz, T. J. & Pedersen, L. H.
  (2013) "Value and Momentum Everywhere" (J of Finance Vol 68 No 3,
  DOI 10.1111/jofi.12021). Provides the implementation anchor for
  cross-sectional and time-series momentum across 8 asset classes
  (US/UK/Continental/Japanese equity, government bonds, currencies,
  commodities — directly mappable to the GTAA ETF universe) plus the
  empirical Sharpe and correlation properties of the combined
  strategy. This is the same primary anchor used by Phase 1
  `dual_momentum_gem` and the rates-family `bond_tsmom_12_1` /
  `real_yield_momentum`, but applied to a *broader* universe of
  multi-asset ETFs spanning equities, bonds, commodities, real estate,
  currency, and inflation-protection instruments.

Universe differentiation from Phase 1:
- `tsmom_12_1` (trend): futures universe, time-series-only ranking.
- `dual_momentum_gem` (trend): 3-asset universe (US equity / intl
  equity / bonds), absolute + relative momentum overlay.
- `gtaa_cross_asset_momentum` (macro): 8–24 ETF universe spanning
  multi-asset classes, cross-sectional + time-series ranking via the
  AMP 2013 mechanic.

Manifest impact: macro family ship count unchanged. Slug list updated:
`global_macro_momentum` is not a Phase 2 slug;
`gtaa_cross_asset_momentum` ships in its place.

---

## 2026-05-15 — Session 2G: reframe 5_asset_tactical → vigilant_asset_allocation_5 (Keller-Keuning 2017 + 2014)

Context: The Session 2G macro/GTAA manifest listed `5_asset_tactical`
(strategy #14 of 15) — "Vigilant Asset Allocation on 5 ETFs",
attributed in the master plan to "Keller/Keuning 2014".

Honesty-check finding: Two corrections required.

1. **Slug.** Python identifiers cannot begin with a digit. The slug
   `5_asset_tactical` cannot be imported as
   `alphakit.strategies.macro.5_asset_tactical`. The slug must be
   re-cast.
2. **Citation date.** Vigilant Asset Allocation (VAA) is Keller &
   Keuning (2017), not 2014. The 2014 Keller-Keuning paper is *Elastic
   Asset Allocation* (EAA), which precedes VAA and uses a momentum-
   score formulation that VAA refines with breadth-momentum and the
   canary-asset cash-bucket fallback. Both papers are SSRN working
   papers.

Resolution: Reframe `5_asset_tactical` → `vigilant_asset_allocation_5`
(slug references VAA explicitly and the 5-asset universe; valid
Python identifier). Cite:

- **Foundational:** Keller, W. J. & Keuning, J. W. (2014) "A Century
  of Generalized Momentum: From Flexible Asset Allocations (FAA) to
  Elastic Asset Allocation (EAA)" (SSRN Working Paper 2543979, DOI
  10.2139/ssrn.2543979). The momentum-score foundation that VAA
  builds on.
- **Primary:** Keller, W. J. & Keuning, J. W. (2017) "Breadth
  Momentum and Vigilant Asset Allocation: Winning More by Losing
  Less" (SSRN Working Paper 3002624, DOI 10.2139/ssrn.3002624). The
  canonical VAA paper: specifies the 13612W momentum-score (weighted
  1/3/6/12-month returns) on 4 offensive assets (SPY, EFA, EEM, AGG)
  + 1 defensive bucket switch on canary-asset breadth, plus the
  cash-bucket fallback when canary momentum is negative.

Architectural note: VAA's momentum-score with canary-fallback
introduces a non-trivial signal-aggregation mechanic, but does not
introduce a new state primitive. The strategy is stateless per the
StrategyProtocol contract — each `generate_signals` call recomputes
the 13612W score and the canary check from scratch. No gate-3
review tier required (mild novelty per the pre-flight assessment).

Manifest impact: macro family ship count unchanged. Slug list updated:
`5_asset_tactical` is not a Phase 2 slug; `vigilant_asset_allocation_5`
ships in its place.

---

## 2026-05-15 — Session 2G: covariance-primitive shared helper module

Context: Session 2G ships three covariance-based portfolio-
construction strategies (`risk_parity_erc_3asset`, `min_variance_gtaa`,
`max_diversification`) that all require joint covariance estimation
followed by numerical weight optimisation. Implementing covariance +
shrinkage + solvers in each strategy independently would (1) duplicate
~200 lines of code three times and (2) risk inconsistent shrinkage
approaches across strategies, breaking the integrity of cluster
predictions — cluster ρ values across the three siblings are only
meaningful if they share the same covariance estimator and only differ
in the weight-construction step.

Resolution: Shared helper module at
`packages/alphakit-strategies-macro/alphakit/strategies/macro/_covariance.py`
with stateless functional design (leading underscore in the module
name signals "package-private" — strategies in the same sub-package
may import it; downstream consumers should not depend on its API
across releases). The helper exposes:

- `rolling_covariance(returns, window, shrinkage)` — rolling
  covariance estimator with three shrinkage methods (`"none"`,
  `"ledoit_wolf"` [default], `"constant"`). Returns a DataFrame
  indexed by `MultiIndex(date, asset_i)` with `asset_j` columns;
  `df.loc[date]` is the (N, N) covariance matrix at that date.
- `_ledoit_wolf_shrinkage(returns_demeaned)` — Ledoit & Wolf (2004)
  "Honey, I Shrunk the Sample Covariance Matrix" (J Portfolio Mgmt
  Vol 30 No 4, DOI 10.3905/jpm.2004.110) constant-correlation-
  target shrinkage with analytic optimal intensity. Translated from
  the authors' published MATLAB reference (`shrinkage_corr.m`).
- `solve_erc_weights(cov, max_iters, tol)` — Equal-risk-contribution
  weights via the Spinu (2013) convex reformulation of the
  Maillard-Roncalli-Teiletche (2010) ERC problem. Uses SciPy
  L-BFGS-B with positive box bounds.
- `solve_min_variance_weights(cov, long_only, max_weight)` —
  Long-only or long-short minimum-variance weights via SciPy SLSQP
  with sum-to-1 equality and box constraints.
- `solve_max_diversification_weights(cov, long_only, max_weight)` —
  Maximum-diversification weights per Choueifaty & Coignard (2008)
  via SciPy SLSQP minimising the negative diversification ratio.
- `diversification_ratio(weights, cov)` — Choueifaty-Coignard
  diversification ratio helper. Scale-invariant in weights.

Numerical guards documented in the module docstring:

- `N == 1` (single asset): all solvers return `[1.0]`.
- `T_eff < N` (more assets than effective observations in a window):
  the sample covariance is singular; `rolling_covariance` falls back
  to `np.cov` with `ddof=1` rather than producing a rank-deficient
  shrinkage estimate.
- Zero/negative sample variance in any asset: raises `ValueError`
  rather than producing weights that allocate to a non-stochastic
  asset.
- ERC iteration with degenerate marginal risks (negative `(Σw)_i`,
  possible with strong negative correlations): the convex
  reformulation avoids the pathology entirely — the log-barrier
  objective is bounded below only for positive `w`, so the
  L-BFGS-B box-bound enforcement is sufficient.

Scope: This commit adds the helper module plus comprehensive tests
(`packages/alphakit-strategies-macro/tests/test_covariance.py`, 39
tests). No strategy code uses the helper yet; subsequent commits 5,
6, 7 (`risk_parity_erc_3asset`, `min_variance_gtaa`,
`max_diversification`) are the first consumers. Backwards
compatibility: trivial (new module, no existing code touched). A new
hard dependency on `scipy>=1.11` is declared in
`packages/alphakit-strategies-macro/pyproject.toml` — scipy was
already pulled in transitively by pandas / vectorbt, so adding the
explicit declaration carries no install-cost change.

Architecture: this is a within-family helper, not a workspace-level
extension like Session 2F's `discrete_legs` metadata or Session 2A's
`raise_chain_not_supported`. The pattern is "shared utility module"
not "architectural protocol extension". The leading-underscore
module name is a deliberate signal that the API is package-private —
strategies in `alphakit.strategies.macro` may import from it, but
downstream consumers (Phase 3 alpha discovery, external user code)
should not depend on it across releases.

Test coverage (39 tests):

- 11 tests for `rolling_covariance`: shape, indexing, symmetry,
  known-variance recovery, NaN handling, majority-NaN omission,
  default Ledoit-Wolf shrinkage, constant shrinkage smoke, invalid-
  window error, invalid-shrinkage-method error, single-asset error.
- 5 tests for `_ledoit_wolf_shrinkage`: α-in-[0,1] invariant, small-
  sample-pushes-α-higher invariant, symmetric-positive-definite
  output, single-asset error, singular-covariance fallback via
  rolling.
- 7 tests for `solve_erc_weights`: analytic inverse-vol case (3
  uncorrelated assets with vols 10%/20%/30% → weights inversely
  proportional to vol), sums-to-1 invariant, all-positive invariant,
  equal-risk-contribution invariant (`w_i * (Σw)_i` constant across
  `i`), N=1 case, zero-variance error, non-square error.
- 7 tests for `solve_min_variance_weights`: 2-asset uncorrelated
  Markowitz closed form (`w_1 = σ_2² / (σ_1² + σ_2²)`), 2-asset
  correlated Markowitz closed form, sums-to-1 invariant, long-only-
  constraint-binds invariant, long-short-allows-negatives
  contrast, N=1 case, invalid-max-weight error.
- 3 tests for `diversification_ratio`: single-asset (DR=1.0), 2-
  asset hand-checked case (DR = 0.1/sqrt(0.0075) for equal-weight 2
  assets with σ=0.1, ρ=0.5), zero-variance edge case.
- 5 tests for `solve_max_diversification_weights`: equal-correlation
  + equal-vol → equal weight, mixed-universe DR > equal-weight DR,
  sums-to-1, long-only non-negative, N=1 case.
- 1 test for N=10 cross-solver convergence: random PSD covariance,
  all three solvers produce valid weight vectors.

Gate-3 review surface: the analytic-known-result tests (ERC inverse-
vol; min-var 2-asset Markowitz; max-div equal-correlation equal-vol)
are the integrity check on the architectural primitive. Any future
modification to the solvers must preserve these analytic invariants
within the documented tolerances.

---

## 2026-05-15 — Session 2G: alphakit-wide rebalance-cadence convention (clarification)

Context: During Session 2G's Commit 2 gate-3 review of
`permanent_portfolio`, investigation surfaced that the vectorbt
bridge's `SizeType.TargetPercent` semantics combined with the
project-wide signal convention (monthly weights forward-filled
daily) produces daily drift-correction trades rather than discrete
monthly rebalance events. The reviewer flagged this as a possible
methodological inconsistency in `permanent_portfolio`'s "monthly
rebalance" claim.

Investigation findings:

- `vectorbt.Portfolio.from_orders(..., size_type=TargetPercent)`
  re-evaluates the target weight on every bar and rebalances on any
  drift, however small. There is no built-in "rebalance only when
  target changes" gate.
- Empirical test on a 63-bar permanent_portfolio panel: the
  strategy emitted 25/25/25/25 target signals on 3 month-end bars,
  but the bridge fired **156 orders across 41 distinct dates**
  (4 legs × 39 drift-correction events post-warm-up + 4 initial
  buys). Realised trade-event rate: ~63 events per asset per year,
  not ~12.
- This is the implemented behavior across **all 99 strategies on
  `origin/main`** (60 Phase 1 + 13 rates + 10 commodity + 15 options
  + 1 macro pending). The pattern was established in Phase 1
  `dual_momentum_gem` (line 130:
  `monthly_weights.reindex(prices.index).ffill().fillna(0.0)`) and
  applied uniformly across Sessions 2D, 2E, 2F. No strategy on
  main produces a true discrete monthly-rebalance trade pattern.
- vectorbt **can** interpret `NaN` size as "do not rebalance this
  bar" — verified empirically (10-bar manual test: NaN-preserved
  weights produced 4 orders vs 17 with the project's ffill+fillna(0)
  pattern). The opt-in path exists but requires a bridge change to
  preserve NaN instead of `weights.reindex_like(prices).fillna(0.0)`
  at `vectorbt_bridge.py:96`.

Resolution: Document the convention explicitly. Strategy docstrings
and per-strategy `paper.md` files should describe the cadence as
"monthly target signal + bridge-side daily drift correction toward
target" rather than "monthly rebalance". The economic exposure
matches a true monthly rebalance within friction-cost noise —
total dollar turnover is comparable because each daily drift-
correction trade rebalances only the drift accumulated since the
previous bar (typically 0.05–0.5% of position value), not the full
target notional. Only the trade-event distribution differs (~63
small events per year vs ~12 discrete events).

The `rebalance_frequency` class attribute on every strategy keeps
its existing semantics: it describes the **signal cadence**, not
the bridge-event cadence. Clarification, not a change.

Phase 3 candidate: A sparse-rebalance protocol extension —
analogous to Session 2F's `discrete_legs` opt-in attribute — would
let strategies declare `sparse_rebalance: bool = False` (defaulting
to today's behavior) and have the bridge preserve `NaN` for opt-in
strategies. Strategies that wanted the discrete-monthly-rebalance
trade pattern would emit weights on rebalance bars only (`NaN`
elsewhere) and opt in via the new attribute. Out of scope for
Session 2G; tracked for Phase 3 bridge-architecture work because:

- Blast radius is large (99 existing strategies need a
  `sparse_rebalance: bool = False` default added).
- vectorbt-bridge tests must be extended to cover both dispatch
  paths.
- Existing benchmark numbers under the daily-drift-correction
  convention would need to be re-run against the sparse-rebalance
  bridge path to confirm Sharpe-equivalence (expected: yes within
  noise, but must be verified).
- Backtrader bridge dispatch would also need to be audited for
  consistent NaN handling.

Scope: **Documentation only.** No code changes to any existing
strategy. Permanent_portfolio (Commit 2) ships with updated
strategy.py docstring + paper.md "Implementation deviations" +
known_failures.md item 4 reflecting the project-wide convention.
Future Session 2G strategies (Commits 3–12) inherit the clarified
convention; explicit docstring framing prevents future reviewer
confusion.

Process lesson: Gate-3 review for a first-strategy-in-family
should verify the bridge integration semantics match the stated
cadence. The Session 2F precedent (covered_call_systematic
gate-3 surfaced the discrete-leg dispatch requirement) had its
analog here — permanent_portfolio gate-3 surfaced the
rebalance-cadence convention. Both are caught by reviewing the
bridge dispatch path on the simplest strategy in the family
before the architecturally-novel strategies (covariance-based
Commits 5-7, regime-state Commits 8-12) layer on top.
