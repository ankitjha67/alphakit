"""Unit tests for :mod:`alphakit.data.futures.yfinance_futures_adapter`.

Cross-cutting guarantees live in ``test_adapter_contract.py``. This
module covers adapter-specific behaviour: ``=F``-suffix passthrough,
offline-fixture routing, and the missing-library error path.
"""

from __future__ import annotations

import sys
import types
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from alphakit.data.futures.yfinance_futures_adapter import YFinanceFuturesAdapter


def test_fetch_passes_f_suffix_symbols_through_to_yfinance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Continuous-contract ``=F`` suffixes reach ``yf.download`` unchanged."""
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        "alphakit.data.futures.yfinance_futures_adapter.ratelimit_acquire",
        lambda _n: None,
    )

    received_tickers: list[Any] = []
    fake = types.ModuleType("yfinance")

    def fake_download(**kwargs: Any) -> pd.DataFrame:
        received_tickers.append(kwargs.get("tickers"))
        return pd.DataFrame(
            {"Close": [70.0, 71.0]},
            index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"]),
        )

    fake.download = fake_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "yfinance", fake)

    adapter = YFinanceFuturesAdapter()
    adapter.fetch(["CL=F", "GC=F"], datetime(2024, 1, 2), datetime(2024, 1, 10))

    assert received_tickers == [["CL=F", "GC=F"]]


def test_fetch_returns_offline_fixture_when_offline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Offline mode returns the shared fixture without importing yfinance."""
    monkeypatch.setenv("ALPHAKIT_OFFLINE", "1")
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    # Breaking the yfinance import proves the offline path was taken.
    monkeypatch.setitem(sys.modules, "yfinance", None)

    adapter = YFinanceFuturesAdapter()
    df = adapter.fetch(["CL=F"], datetime(2024, 1, 2), datetime(2024, 1, 10))

    assert isinstance(df, pd.DataFrame)
    assert "CL=F" in df.columns
    assert not df.empty


def test_fetch_missing_yfinance_library_raises_import_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        "alphakit.data.futures.yfinance_futures_adapter.ratelimit_acquire",
        lambda _n: None,
    )
    monkeypatch.setitem(sys.modules, "yfinance", None)

    adapter = YFinanceFuturesAdapter()
    with pytest.raises(ImportError, match="yfinance"):
        adapter.fetch(["CL=F"], datetime(2024, 1, 2), datetime(2024, 1, 10))
