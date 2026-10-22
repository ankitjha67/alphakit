"""Tests for the ``scripts/cluster_analysis.py`` ``--feed real`` path.

The default ``--feed synthetic`` 49x49 path is unchanged and slow (it runs every
Phase-2 strategy through the bridge), so it is not exercised here. These tests
cover the real-feed **32x32** cluster (5 regime + 7 commodity + 11 rates + 9
macro, Session 2L expansion of Session 2K-4's 29x29): the prerequisite
fail-loud paths, the predicted-vs-actual ρ reporting for all four intra-family
blocks, and the cross-family descriptive blocks. The three returns helpers
(``_regime_real_returns``, ``_commodity_real_returns``,
``_yfinance_real_returns``) are mocked so no network/key is needed.

The script lives under ``scripts/`` (not an importable package), so it is loaded
by path via :mod:`importlib`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from alphakit.data.errors import FeedNotConfiguredError

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "cluster_analysis.py"
_spec = importlib.util.spec_from_file_location("cluster_analysis", _SCRIPT)
assert _spec is not None and _spec.loader is not None
cluster = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cluster)


def test_require_fred_real_without_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(FeedNotConfiguredError) as exc:
        cluster._require_fred_real()
    msg = str(exc.value)
    assert "FRED_API_KEY" in msg
    assert "export FRED_API_KEY" in msg
    assert "--feed real" in msg


def test_main_feed_real_without_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["cluster_analysis.py", "--feed", "real"])
    with pytest.raises(FeedNotConfiguredError):
        cluster.main()


def test_require_commodity_real_without_yfinance_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--feed real`` without yfinance importable fails loud (commodity portion)."""
    import builtins

    real_import = builtins.__import__

    def _fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "yfinance" or name.startswith("yfinance."):
            raise ImportError("simulated: no yfinance")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.delitem(sys.modules, "yfinance", raising=False)
    with pytest.raises(SystemExit) as exc:
        cluster._require_commodity_real()
    assert "yfinance" in str(exc.value)
    assert "--feed real" in str(exc.value)


def test_real_cluster_reports_intra_and_cross_family_blocks(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The 32x32 combined cluster prints all four intra-family
    predicted-vs-actual tables (regime / commodity / rates / macro), the
    cross-family descriptive blocks, and an overall summary line. Every slug
    appears in the output and the dedup-bar line is emitted.
    """
    idx = pd.date_range("2010-01-01", periods=500, freq="B")
    rng = np.random.default_rng(0)
    factor = rng.normal(0.0, 0.01, len(idx))
    all_slugs = (
        list(cluster._REGIME_SLUGS)
        + list(cluster._COMMODITY_REAL_SLUGS)
        + list(cluster._RATES_REAL_SLUGS)
        + list(cluster._MACRO_REAL_SLUGS)
    )
    series: dict[str, pd.Series] = {
        slug: pd.Series(0.6 * factor + 0.4 * rng.normal(0.0, 0.01, len(idx)), index=idx)
        for slug in all_slugs
    }

    monkeypatch.setattr(cluster, "_require_fred_real", lambda: None)
    monkeypatch.setattr(cluster, "_require_commodity_real", lambda: None)
    monkeypatch.setattr(cluster, "_regime_real_returns", lambda slug: series[slug].rename(slug))
    monkeypatch.setattr(cluster, "_commodity_real_returns", lambda slug: series[slug].rename(slug))
    monkeypatch.setattr(
        cluster, "_yfinance_real_returns", lambda _family, slug: series[slug].rename(slug)
    )

    rc = cluster._real_cluster()
    out = capsys.readouterr().out

    assert rc == 0
    # All four intra-family headers
    assert "Regime intra-family" in out
    assert "Commodity intra-family" in out
    assert "Rates intra-family" in out
    assert "Macro intra-family" in out
    # At least one cross-family descriptive block
    assert "Cross-family" in out
    # Every slug surfaces (sanity check the matrix render + tables)
    for slug in all_slugs:
        assert slug in out
    # Overall summary + dedup bar
    assert "Overall:" in out
    assert "documented pairs in range" in out
    assert "dedup-review bar" in out


def test_predicted_rho_covers_all_ten_regime_pairs() -> None:
    """All 10 unordered regime pairs must have a documented prediction."""
    pairs = {
        frozenset({a, b})
        for i, a in enumerate(cluster._REGIME_SLUGS)
        for b in cluster._REGIME_SLUGS[i + 1 :]
    }
    assert pairs == set(cluster._PREDICTED_RHO)


def test_predicted_commodity_rho_covers_documented_pairs() -> None:
    """The 6 Session 2E commodity pairs + the 1 Session 2K-1 cot pair
    (``cot_speculator_position↔commodity_tsmom``, mildly NEGATIVE by
    construction) are in the dict. The other 14 in-scope pairs out of 21
    total intentionally lack predictions — the cluster output shows them
    as ``n/a`` rather than scoring them.
    """
    expected_documented = {
        # Session 2E commodity intra-family.
        frozenset({"commodity_tsmom", "metals_momentum"}),
        frozenset({"commodity_tsmom", "grain_seasonality"}),
        frozenset({"crack_spread", "crush_spread"}),
        frozenset({"crack_spread", "wti_brent_spread"}),
        frozenset({"crush_spread", "wti_brent_spread"}),
        frozenset({"crush_spread", "grain_seasonality"}),
        # Session 2K-1 cot addition (single in-scope pair from cot
        # known_failures.md §6).
        frozenset({"cot_speculator_position", "commodity_tsmom"}),
    }
    assert expected_documented == set(cluster._PREDICTED_COMMODITY_RHO)
    # Every prediction key must be a pair of in-scope commodity slugs.
    commodity_set = set(cluster._COMMODITY_REAL_SLUGS)
    for pair in cluster._PREDICTED_COMMODITY_RHO:
        assert pair.issubset(commodity_set)


def test_predicted_rates_rho_keys_are_in_scope_pairs() -> None:
    """Every ``_PREDICTED_RATES_RHO`` key is a pair of two distinct
    in-scope rates slugs. Curated subset of the 55 total rates pairs
    (Session 2H predictions extracted from rates ``known_failures.md``);
    the cluster output shows undocumented pairs as ``n/a``."""
    assert len(cluster._PREDICTED_RATES_RHO) > 0
    rates_set = set(cluster._RATES_REAL_SLUGS)
    for pair in cluster._PREDICTED_RATES_RHO:
        assert len(pair) == 2, f"prediction key {pair} must be a 2-set"
        assert pair.issubset(rates_set), f"{pair} contains an out-of-scope rates slug"


def test_predicted_macro_rho_keys_are_in_scope_pairs() -> None:
    """Every ``_PREDICTED_MACRO_RHO`` key is a pair of two distinct
    in-scope macro slugs. Curated subset of the 36 total macro pairs at
    N=9."""
    assert len(cluster._PREDICTED_MACRO_RHO) > 0
    macro_set = set(cluster._MACRO_REAL_SLUGS)
    for pair in cluster._PREDICTED_MACRO_RHO:
        assert len(pair) == 2, f"prediction key {pair} must be a 2-set"
        assert pair.issubset(macro_set), f"{pair} contains an out-of-scope macro slug"


def test_session_2l_macro_variants_are_in_cluster_scope() -> None:
    """The three Session 2L 10-asset variants are in the macro cluster block,
    alongside the preserved 3-asset originals.

    The other macro tests read ``_MACRO_REAL_SLUGS`` live and so auto-adapt to
    any membership change, which means they would not notice the variants
    being dropped. This test pins the Session 2L scope explicitly. Both
    cardinalities must be present: the comparison the session exists to make
    is 3-asset versus 10-asset on the same three solver objectives, and
    removing either side destroys it.
    """
    macro = list(cluster._MACRO_REAL_SLUGS)

    originals = ["risk_parity_erc_3asset", "min_variance_gtaa", "max_diversification"]
    variants = [
        "risk_parity_erc_10asset",
        "min_variance_gtaa_10asset",
        "max_diversification_10asset",
    ]
    for slug in originals + variants:
        assert slug in macro, f"{slug} missing from the macro cluster block"

    assert len(macro) == 9, f"expected 9 macro slugs, got {len(macro)}: {macro}"
    assert len(set(macro)) == len(macro), "macro cluster block has duplicates"


def test_session_2l_variant_predictions_are_present_and_ordered() -> None:
    """Every Session 2L pair carries a band, and every band is well-formed.

    Bands for these pairs are measurement-derived rather than blind
    predictions; see the comment above ``_PREDICTED_MACRO_RHO``. This test
    checks structural validity, not accuracy: lower bound below upper bound,
    both inside [-1, 1].
    """
    variants = [
        "risk_parity_erc_10asset",
        "min_variance_gtaa_10asset",
        "max_diversification_10asset",
    ]
    table = cluster._PREDICTED_MACRO_RHO

    # Each variant pairs with the other two variants, its same-solver
    # 3-asset original, permanent_portfolio, and gtaa_cross_asset_momentum.
    expected_pairs = [
        frozenset({"risk_parity_erc_10asset", "min_variance_gtaa_10asset"}),
        frozenset({"risk_parity_erc_10asset", "max_diversification_10asset"}),
        frozenset({"min_variance_gtaa_10asset", "max_diversification_10asset"}),
        frozenset({"risk_parity_erc_10asset", "risk_parity_erc_3asset"}),
        frozenset({"min_variance_gtaa_10asset", "min_variance_gtaa"}),
        frozenset({"max_diversification_10asset", "max_diversification"}),
    ]
    for pair in expected_pairs:
        assert pair in table, f"missing Session 2L band for {sorted(pair)}"

    for variant in variants:
        for comparator in ("permanent_portfolio", "gtaa_cross_asset_momentum"):
            pair = frozenset({variant, comparator})
            assert pair in table, f"missing band for {sorted(pair)}"

    for pair, (lo, hi) in table.items():
        assert lo < hi, f"band for {sorted(pair)} is inverted: ({lo}, {hi})"
        assert -1.0 <= lo <= 1.0, f"band lower bound out of range for {sorted(pair)}"
        assert -1.0 <= hi <= 1.0, f"band upper bound out of range for {sorted(pair)}"


def test_erc_to_maxdiv_10asset_band_straddles_the_dedup_bar() -> None:
    """The near-breach pair's band must reach above 0.95.

    Measured at +0.9480, the ``risk_parity_erc_10asset`` to
    ``max_diversification_10asset`` pair sits 0.0020 below the dedup-review
    bar. A band that stopped short of 0.95 would score a genuine breach as
    OUT-high and bury the single most important risk in this variant group.
    """
    pair = frozenset({"risk_parity_erc_10asset", "max_diversification_10asset"})
    lo, hi = cluster._PREDICTED_MACRO_RHO[pair]
    assert lo < 0.95 < hi, (
        f"band ({lo}, {hi}) must straddle the 0.95 dedup bar so a breach is "
        "visible rather than scored as a band miss"
    )
