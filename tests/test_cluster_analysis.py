"""Tests for the ``scripts/cluster_analysis.py`` ``--feed real`` path.

The default ``--feed synthetic`` 49x49 path is unchanged and slow (it runs every
Phase-2 strategy through the bridge), so it is not exercised here. These tests
cover the real-feed 11x11 cluster (5 regime + 6 commodity, Session 2J expansion
of Session 2I's 5x5): the prerequisite fail-loud paths, the predicted-vs-actual
ρ reporting for both intra-family blocks, and the descriptive cross-family
block. ``_regime_real_returns`` and ``_commodity_real_returns`` are mocked so
no network/key is needed.

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
    """The 11x11 combined cluster prints regime + commodity intra-family
    predicted-vs-actual tables, the regime×commodity cross-family descriptive
    block, and an overall summary line. All slugs (regime + commodity) appear
    in the output and the dedup-bar line is emitted.
    """
    idx = pd.date_range("2010-01-01", periods=500, freq="B")
    rng = np.random.default_rng(0)
    factor = rng.normal(0.0, 0.01, len(idx))
    all_slugs = list(cluster._REGIME_SLUGS) + list(cluster._COMMODITY_REAL_SLUGS)
    series: dict[str, pd.Series] = {
        slug: pd.Series(0.6 * factor + 0.4 * rng.normal(0.0, 0.01, len(idx)), index=idx)
        for slug in all_slugs
    }

    monkeypatch.setattr(cluster, "_require_fred_real", lambda: None)
    monkeypatch.setattr(cluster, "_require_commodity_real", lambda: None)
    monkeypatch.setattr(cluster, "_regime_real_returns", lambda slug: series[slug].rename(slug))
    monkeypatch.setattr(cluster, "_commodity_real_returns", lambda slug: series[slug].rename(slug))

    rc = cluster._real_cluster()
    out = capsys.readouterr().out

    assert rc == 0
    # Both intra-family headers
    assert "Regime intra-family" in out
    assert "Commodity intra-family" in out
    # Cross-family descriptive block
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
    """The 6 documented commodity pairs from known_failures.md §6 are in the dict.

    The other 9 in-scope pairs out of 15 total intentionally lack predictions —
    the cluster output shows them as ``n/a`` rather than scoring them.
    """
    expected_documented = {
        frozenset({"commodity_tsmom", "metals_momentum"}),
        frozenset({"commodity_tsmom", "grain_seasonality"}),
        frozenset({"crack_spread", "crush_spread"}),
        frozenset({"crack_spread", "wti_brent_spread"}),
        frozenset({"crush_spread", "wti_brent_spread"}),
        frozenset({"crush_spread", "grain_seasonality"}),
    }
    assert expected_documented == set(cluster._PREDICTED_COMMODITY_RHO)
    # Every prediction key must be a pair of in-scope commodity slugs.
    commodity_set = set(cluster._COMMODITY_REAL_SLUGS)
    for pair in cluster._PREDICTED_COMMODITY_RHO:
        assert pair.issubset(commodity_set)
