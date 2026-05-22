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

Honest scope (v0.2.0): regime-state strategies (the 5 FRED-gated macro
strategies) have informational columns that are generic GBM on synthetic
fixtures, so their *signal* is degenerate here and their cluster
correlations are NOT meaningfully captured. The authoritative cluster
predictions for those remain the per-strategy known_failures.md rho ranges,
pending the v0.2.1 real-feed cluster pass (needs FRED_API_KEY + the runner
FRED-merge enhancement). This is labeled in the output.

Usage:
    uv run --extra dev python scripts/cluster_analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from alphakit.bench import discovery  # noqa: E402
from alphakit.bridges import vectorbt_bridge  # noqa: E402
from alphakit.data.fixtures.generator import generate_fixture_prices  # noqa: E402

_PHASE2_FAMILIES = ("rates", "commodity", "options", "macro")
_DATA_START = "2005-01-01"
_DATA_END = "2025-12-31"

# FRED-gated regime strategies whose signal is degenerate on generic fixtures.
_REGIME_STATE = {
    "recession_probability_rotation",
    "growth_inflation_regime_rotation",
    "yield_curve_regime_allocation",
    "fed_policy_tilt",
    "inflation_regime_allocation",
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


def main() -> int:
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


if __name__ == "__main__":
    sys.exit(main())
