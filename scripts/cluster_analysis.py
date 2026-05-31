#!/usr/bin/env python3
"""Phase 2 cluster analysis — pairwise equity-curve correlation (49 strategies).

Computes the 49 x 49 Pearson correlation matrix of strategy equity-curve
returns across the four Phase 2 families (rates, commodity, options, macro)
on a **common synthetic-fixture basis** (deterministic, seed=42), so that
strategies sharing tradable symbols see identical underlying price paths and
correlations are apples-to-apples.

Surfaces:
* the highest-correlated pairs (rho >= 0.70),
* any pair at or above the Phase 2 master-plan dedup-review bar (rho > 0.95),
* the documented deliberate-redundancy pairs for sanity.

Honest scope (v0.2.0 default, ``--feed synthetic``): regime-state strategies
(the 5 FRED-gated macro strategies) have informational columns that are generic
GBM on synthetic fixtures, so their *signal* is degenerate there and their
cluster correlations are NOT meaningfully captured.

Session 2I (``--feed real`` with FRED-gated regime): the 5 regime strategies are
run through the multi-feed ``BenchmarkRunner(strict_feed=True)`` against real
yfinance+FRED data, and their 5x5 pairwise ρ is reported against the Session 2G
``known_failures.md`` predictions.

Session 2J (``--feed real`` now 11x11): adds the 6 commodity real-feed strategies
(commodity_tsmom, crack_spread, crush_spread, grain_seasonality, metals_momentum,
wti_brent_spread) routed via yfinance-futures, with the anomaly filter
(``drop_nonpositive_tradable_bars=True``) enabled so the 2020-04-20 WTI -$37.63
settlement and Thanksgiving NaN bars are excluded — matching the configuration
used by ``regenerate_benchmarks.py commodity --feed real``. The cluster output
covers:

* 5x5 regime intra-family (predicted vs actual, Session 2G predictions);
* 6x6 commodity intra-family (predicted vs actual where documented, ``n/a``
  otherwise — 6 of 15 pairs have explicit predictions in known_failures.md);
* 5x6 cross-family (descriptive — predictions are sparse).

Requires ``FRED_API_KEY`` + ``fredapi`` (for the 5 regime strategies) and
``yfinance`` (for the 6 commodity strategies). The real curves are NOT pooled
with the 47 synthetic curves — different price bases are not apples-to-apples.

Usage:
    uv run --extra dev python scripts/cluster_analysis.py                # synthetic 49x49
    uv run --with fredapi --with yfinance --extra dev \
        python scripts/cluster_analysis.py --feed real                  # real 11x11
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from alphakit.bench import discovery  # noqa: E402
from alphakit.bench.runner import BenchmarkRunner  # noqa: E402
from alphakit.bridges import vectorbt_bridge  # noqa: E402
from alphakit.data.errors import FeedNotConfiguredError  # noqa: E402
from alphakit.data.fixtures.generator import generate_fixture_prices  # noqa: E402

_PHASE2_FAMILIES = ("rates", "commodity", "options", "macro")
_DATA_START = "2005-01-01"
_IN_SAMPLE_END = "2019-12-31"
_DATA_END = "2025-12-31"

# FRED-gated regime strategies whose signal is degenerate on generic fixtures.
_REGIME_STATE = {
    "recession_probability_rotation",
    "growth_inflation_regime_rotation",
    "yield_curve_regime_allocation",
    "fed_policy_tilt",
    "inflation_regime_allocation",
}

# Ordered for the --feed real 5x5 matrix (Commit 8-12 order).
_REGIME_SLUGS = [
    "recession_probability_rotation",
    "growth_inflation_regime_rotation",
    "yield_curve_regime_allocation",
    "fed_policy_tilt",
    "inflation_regime_allocation",
]

# Session 2G predicted pairwise ρ ranges (from each regime strategy's
# known_failures.md §"Cluster correlation with sibling strategies"). Keyed by
# unordered pair. The recession↔yield_curve pair is the deliberate-redundancy
# pair (highest band).
_PREDICTED_RHO: dict[frozenset[str], tuple[float, float]] = {
    frozenset({"recession_probability_rotation", "yield_curve_regime_allocation"}): (0.50, 0.70),
    frozenset({"recession_probability_rotation", "growth_inflation_regime_rotation"}): (0.40, 0.60),
    frozenset({"recession_probability_rotation", "fed_policy_tilt"}): (0.40, 0.60),
    frozenset({"recession_probability_rotation", "inflation_regime_allocation"}): (0.30, 0.50),
    frozenset({"growth_inflation_regime_rotation", "yield_curve_regime_allocation"}): (0.40, 0.60),
    frozenset({"growth_inflation_regime_rotation", "fed_policy_tilt"}): (0.40, 0.60),
    frozenset({"growth_inflation_regime_rotation", "inflation_regime_allocation"}): (0.40, 0.60),
    frozenset({"yield_curve_regime_allocation", "fed_policy_tilt"}): (0.40, 0.60),
    frozenset({"yield_curve_regime_allocation", "inflation_regime_allocation"}): (0.30, 0.50),
    frozenset({"fed_policy_tilt", "inflation_regime_allocation"}): (0.30, 0.50),
}

# Session 2J commodity real-feed slugs (6 front-month strategies; 3 yfinance
# second-month-blocked are amendment-deferred; cot_speculator_position is
# Session 2K-deferred — see docs/known-data-anomalies.md).
_COMMODITY_REAL_SLUGS = [
    "commodity_tsmom",
    "crack_spread",
    "crush_spread",
    "grain_seasonality",
    "metals_momentum",
    "wti_brent_spread",
]

# Session 2E commodity predicted pairwise ρ — only 6 of the 15 in-scope pairs
# carry explicit predictions in their §6 ``Cluster correlation`` sections; the
# other 9 are scored ``n/a`` in the output. The
# ``commodity_tsmom↔metals_momentum`` (0.75-0.90) pair is the documented
# deliberate-redundancy / borderline-cluster pair (Session 2E acknowledged).
_PREDICTED_COMMODITY_RHO: dict[frozenset[str], tuple[float, float]] = {
    frozenset({"commodity_tsmom", "metals_momentum"}): (0.75, 0.90),
    frozenset({"commodity_tsmom", "grain_seasonality"}): (0.20, 0.40),
    frozenset({"crack_spread", "crush_spread"}): (0.00, 0.10),
    frozenset({"crack_spread", "wti_brent_spread"}): (0.10, 0.30),
    frozenset({"crush_spread", "wti_brent_spread"}): (0.00, 0.10),
    frozenset({"crush_spread", "grain_seasonality"}): (0.10, 0.20),
}

# Documented deliberate-redundancy pairs to report explicitly (from known_failures.md).
_DELIBERATE_PAIRS = [
    ("risk_parity_erc_3asset", "permanent_portfolio"),
    ("recession_probability_rotation", "yield_curve_regime_allocation"),
    ("curve_steepener_2s10s", "curve_flattener_2s10s"),
]


def _equity_returns(family: str, slug: str) -> pd.Series | None:
    """Return the OOS daily-return series for one strategy on fixture data."""
    try:
        strategy = discovery.instantiate(family, slug)
        universe = list(discovery.load_config(family, slug)["universe"])
        prices = generate_fixture_prices(symbols=universe, start=_DATA_START, end=_DATA_END)
        result = vectorbt_bridge.run(strategy=strategy, prices=prices)
        return cast(pd.Series, result.returns.rename(slug))
    except Exception as exc:
        print(f"  WARN {family}/{slug}: {exc}")
        return None


def _require_fred_real() -> None:
    """Fail loud if the --feed real prerequisites (key + package) are missing."""
    if not os.environ.get("FRED_API_KEY"):
        raise FeedNotConfiguredError(
            "--feed real requires the FRED_API_KEY environment variable (not "
            "set). Get a free key at "
            "https://fred.stlouisfed.org/docs/api/api_key.html, then set it:\n"
            "  Linux/macOS:  export FRED_API_KEY=your_key_here\n"
            "  Windows (PowerShell, persistent):  "
            "[Environment]::SetEnvironmentVariable('FRED_API_KEY','your_key_here','User')\n"
            "Then re-run:  uv run --with fredapi --with yfinance --extra dev "
            "python scripts/cluster_analysis.py --feed real"
        )
    try:
        import fredapi  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "ERROR: --feed real requires the fredapi package, which is not "
            "importable. Re-run with it, e.g.:\n"
            "    uv run --with fredapi --with yfinance --extra dev "
            "python scripts/cluster_analysis.py --feed real\n"
            f"(import error: {exc})"
        ) from exc


def _require_commodity_real() -> None:
    """Fail loud if commodity ``--feed real`` prerequisites are missing.

    Only yfinance is checked — yfinance-futures uses the same library, and the
    cftc-cot adapter is not exercised by the 6 in-scope commodity strategies
    (cot_speculator_position is Session 2K-deferred). Anomaly filter handling
    of the 2020-04-20 WTI negative bar is the runner's responsibility.
    """
    try:
        import yfinance  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "ERROR: --feed real (commodity portion) requires the yfinance "
            "package, which is not importable. Re-run with it, e.g.:\n"
            "    uv run --with fredapi --with yfinance --extra dev "
            "python scripts/cluster_analysis.py --feed real\n"
            f"(import error: {exc})"
        ) from exc


def _regime_real_returns(slug: str) -> pd.Series | None:
    """Daily-return series for one regime strategy on real yfinance+FRED data.

    Routes through the multi-feed ``BenchmarkRunner(strict_feed=True)`` fetch
    (tradable columns from yfinance, informational FRED columns from FRED), so
    the regime signal is driven by real macro data rather than degenerate GBM.
    Matches the configuration used by ``regenerate_benchmarks.py tier2
    --feed real`` so the cluster correlations are comparable to the committed
    v0.2.1 benchmark JSONs.
    """
    try:
        strategy = discovery.instantiate("macro", slug)
        universe = list(discovery.load_config("macro", slug)["universe"])
        runner = BenchmarkRunner(
            data_start=_DATA_START,
            in_sample_end=_IN_SAMPLE_END,
            out_of_sample_end=_DATA_END,
            strict_feed=True,
        )
        prices = runner._fetch_prices(universe, strategy=strategy)
        result = vectorbt_bridge.run(strategy=strategy, prices=prices)
        return cast(pd.Series, result.returns.rename(slug))
    except Exception as exc:
        print(f"  WARN macro/{slug} (real feed): {exc}")
        return None


def _commodity_real_returns(slug: str) -> pd.Series | None:
    """Daily-return series for one commodity strategy on real yfinance-futures.

    Routes through the per-role feed router (``=F`` → yfinance-futures) with the
    anomaly filter ON (``drop_nonpositive_tradable_bars=True``) so the
    2020-04-20 WTI -$37.63 settlement and Thanksgiving NaN gaps are excluded —
    matches the configuration used by ``regenerate_benchmarks.py commodity
    --feed real`` so the cluster correlations are comparable to the committed
    v0.2.2 commodity benchmark JSONs.
    """
    try:
        strategy = discovery.instantiate("commodity", slug)
        universe = list(discovery.load_config("commodity", slug)["universe"])
        runner = BenchmarkRunner(
            data_start=_DATA_START,
            in_sample_end=_IN_SAMPLE_END,
            out_of_sample_end=_DATA_END,
            strict_feed=True,
            drop_nonpositive_tradable_bars=True,
        )
        prices = runner._fetch_prices(universe, strategy=strategy)
        result = vectorbt_bridge.run(strategy=strategy, prices=prices)
        return cast(pd.Series, result.returns.rename(slug))
    except Exception as exc:
        print(f"  WARN commodity/{slug} (real feed): {exc}")
        return None


def _report_intra_family(
    corr: pd.DataFrame,
    slugs: list[str],
    predictions: dict[frozenset[str], tuple[float, float]],
    label: str,
) -> tuple[int, int]:
    """Print a sorted predicted-vs-actual table for one intra-family block.

    Returns ``(in_range_count, documented_pair_count)`` — i.e. how many pairs
    with documented predictions land inside their predicted band, out of the
    pairs that have a prediction at all (``n/a`` pairs are excluded from both
    numerator and denominator).
    """
    print(f"\n{label} — predicted vs actual ρ:")
    rows: list[tuple[float, str]] = []
    in_range = 0
    documented = 0
    for i in range(len(slugs)):
        for j in range(i + 1, len(slugs)):
            a, b = slugs[i], slugs[j]
            rho = float(corr.loc[a, b])
            pred = predictions.get(frozenset({a, b}))
            if pred is None:
                rows.append((rho, f"  [?? ] {rho:+.3f}  pred  n/a       {a} <-> {b}"))
                continue
            lo, hi = pred
            documented += 1
            ok = lo <= rho <= hi
            in_range += int(ok)
            flag = "OK " if ok else "OUT"
            rows.append((rho, f"  [{flag}] {rho:+.3f}  pred {lo:.2f}-{hi:.2f}  {a} <-> {b}"))
    for _, row in sorted(rows, reverse=True):
        print(row)
    if documented:
        print(f"\n{in_range}/{documented} documented pairs within predicted range.")
    return in_range, documented


def _report_cross_family(
    corr: pd.DataFrame, group_a: list[str], group_b: list[str], label: str
) -> None:
    """Print the cross-family ``len(a) × len(b)`` pairs, sorted descending by ρ.

    Cross-family predictions are sparse to non-existent — this block is
    descriptive only (no OK/OUT flags), surfacing the strongest cross-family
    co-movements for narrative discussion in the closeout.
    """
    print(f"\n{label} — descriptive (no formal prediction baseline):")
    rows: list[tuple[float, str]] = []
    for a in group_a:
        for b in group_b:
            rho = float(corr.loc[a, b])
            rows.append((rho, f"  {rho:+.3f}  {a} <-> {b}"))
    for _, row in sorted(rows, reverse=True):
        print(row)


def _real_cluster() -> int:
    """Compute and report the 11x11 real-feed cluster (5 regime + 6 commodity).

    Single combined correlation matrix; output split into regime-intra,
    commodity-intra, and regime×commodity cross-family blocks.
    """
    _require_fred_real()
    _require_commodity_real()

    series: dict[str, pd.Series] = {}
    for slug in _REGIME_SLUGS:
        ret = _regime_real_returns(slug)
        if ret is not None:
            series[slug] = ret
    for slug in _COMMODITY_REAL_SLUGS:
        ret = _commodity_real_returns(slug)
        if ret is not None:
            series[slug] = ret
    if len(series) < 2:
        print("ERROR: fewer than 2 real curves computed; cannot correlate.")
        return 1

    rets = pd.DataFrame(series).dropna(how="all")
    corr = rets.corr()
    print(
        f"\nReal-feed (yfinance+fred + yfinance-futures) cluster — "
        f"{len(corr)}x{len(corr)} ρ ({len(rets)} aligned bars).\n"
    )
    print(corr.round(3).to_string())

    regime_in_corr = [s for s in _REGIME_SLUGS if s in corr.columns]
    commodity_in_corr = [s for s in _COMMODITY_REAL_SLUGS if s in corr.columns]

    regime_in_range, regime_documented = _report_intra_family(
        corr, regime_in_corr, _PREDICTED_RHO, "Regime intra-family (Session 2G predictions)"
    )
    commodity_in_range, commodity_documented = _report_intra_family(
        corr,
        commodity_in_corr,
        _PREDICTED_COMMODITY_RHO,
        "Commodity intra-family (Session 2E predictions)",
    )
    if regime_in_corr and commodity_in_corr:
        _report_cross_family(
            corr, regime_in_corr, commodity_in_corr, "Cross-family (regime × commodity)"
        )

    tri = corr.to_numpy()[np.triu_indices(len(corr), 1)]
    max_rho = float(np.nanmax(tri))
    total_documented = regime_documented + commodity_documented
    total_in_range = regime_in_range + commodity_in_range
    print(
        f"\nOverall: {total_in_range}/{total_documented} documented pairs in range "
        f"(regime {regime_in_range}/{regime_documented}, "
        f"commodity {commodity_in_range}/{commodity_documented})."
    )
    print(
        f"Mean |ρ|: {np.nanmean(np.abs(tri)):.3f}   Max ρ: {max_rho:+.3f}   "
        f"dedup-review bar (ρ > 0.95): {'BREACHED' if max_rho > 0.95 else 'clear'}"
    )
    return 0


def _synthetic_cluster() -> int:
    series: dict[str, pd.Series] = {}
    fam_of: dict[str, str] = {}
    for family in _PHASE2_FAMILIES:
        for slug in discovery.discover_slugs(family):
            ret = _equity_returns(family, slug)
            if ret is not None:
                series[slug] = ret
                fam_of[slug] = family

    rets = pd.DataFrame(series).dropna(how="all")
    corr = rets.corr()
    n = len(corr)
    print(f"\nComputed {n} x {n} correlation matrix ({len(rets)} aligned bars).\n")

    # Upper-triangle pairwise list
    pairs: list[tuple[float, str, str]] = []
    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            rho = corr.iloc[i, j]
            if np.isfinite(rho):
                pairs.append((float(rho), cols[i], cols[j]))
    pairs.sort(reverse=True)

    above_bar = [(r, a, b) for r, a, b in pairs if r > 0.95]
    high = [(r, a, b) for r, a, b in pairs if 0.70 <= r <= 0.95]

    print(f"Pairs with rho > 0.95 (dedup-review bar): {len(above_bar)}")
    for r, a, b in above_bar:
        print(f"  {r:+.3f}  {a} <-> {b}  [{fam_of[a]}/{fam_of[b]}]")
    print(f"\nPairs with 0.70 <= rho <= 0.95: {len(high)}")
    for r, a, b in high[:25]:
        print(f"  {r:+.3f}  {a} <-> {b}  [{fam_of[a]}/{fam_of[b]}]")

    print("\nDocumented deliberate-redundancy pairs (fixture-basis rho):")
    for a, b in _DELIBERATE_PAIRS:
        if a in corr.columns and b in corr.columns:
            note = (
                " (regime-degenerate on fixtures)"
                if (a in _REGIME_STATE or b in _REGIME_STATE)
                else ""
            )
            print(f"  {corr.loc[a, b]:+.3f}  {a} <-> {b}{note}")

    print(
        f"\nMean |rho| (off-diagonal): {np.nanmean(np.abs(corr.values[np.triu_indices(n, 1)])):.3f}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 cluster analysis")
    parser.add_argument(
        "--feed",
        choices=["synthetic", "real"],
        default="synthetic",
        help="'synthetic' (default): 49x49 fixture-basis matrix. 'real': 11x11 "
        "real-feed cluster (5 regime via yfinance+FRED + 6 commodity via "
        "yfinance-futures) with intra-family OK/OUT vs Session 2G/2E "
        "predictions and a regime×commodity cross-family block. Needs "
        "FRED_API_KEY + fredapi + yfinance.",
    )
    args = parser.parse_args()
    if args.feed == "real":
        return _real_cluster()
    return _synthetic_cluster()


if __name__ == "__main__":
    sys.exit(main())
