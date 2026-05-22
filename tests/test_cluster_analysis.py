"""Tests for the ``scripts/cluster_analysis.py`` ``--feed real`` path (Session 2I).

The default ``--feed synthetic`` 49x49 path is unchanged and slow (it runs every
Phase-2 strategy through the bridge), so it is not exercised here. These tests
cover the new real-feed regime cluster: the prerequisite fail-loud and the
predicted-vs-actual ρ reporting, with ``_regime_real_returns`` mocked so no
network/key is needed.

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


def test_real_regime_cluster_reports_predicted_vs_actual(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Five controlled return series (shared factor + idiosyncratic noise) so the
    # 5x5 correlation is finite and the predicted-vs-actual logic has data.
    idx = pd.date_range("2010-01-01", periods=500, freq="B")
    rng = np.random.default_rng(0)
    factor = rng.normal(0.0, 0.01, len(idx))
    series: dict[str, pd.Series] = {
        slug: pd.Series(0.6 * factor + 0.4 * rng.normal(0.0, 0.01, len(idx)), index=idx)
        for slug in cluster._REGIME_SLUGS
    }

    monkeypatch.setattr(cluster, "_require_fred_real", lambda: None)
    monkeypatch.setattr(cluster, "_regime_real_returns", lambda slug: series[slug].rename(slug))

    rc = cluster._real_regime_cluster()
    out = capsys.readouterr().out

    assert rc == 0
    assert "regime cluster" in out.lower()
    for slug in cluster._REGIME_SLUGS:
        assert slug in out
    assert "Predicted (Session 2G) vs actual" in out
    assert "within the Session 2G predicted range" in out
    assert "dedup-review bar" in out


def test_predicted_rho_covers_all_ten_pairs() -> None:
    # All 10 unordered regime pairs must have a documented prediction.
    pairs = {
        frozenset({a, b})
        for i, a in enumerate(cluster._REGIME_SLUGS)
        for b in cluster._REGIME_SLUGS[i + 1 :]
    }
    assert pairs == set(cluster._PREDICTED_RHO)
