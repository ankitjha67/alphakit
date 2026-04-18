"""Unit tests for :mod:`alphakit.data.positioning.cftc_cot_adapter`.

Cross-cutting guarantees live in ``test_adapter_contract.py``. This
module covers CFTC-specific behaviour: URL year-range expansion, ZIP
parsing, output-schema correctness, market-code filtering, and
date-range filtering.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from alphakit.data.errors import OfflineModeError
from alphakit.data.positioning.cftc_cot_adapter import CFTCCOTAdapter


def _build_cot_zip(rows: list[tuple[str, str, int, int, int, int]]) -> io.BytesIO:
    """Return a ``BytesIO`` holding a ZIP containing a minimal COT CSV.

    Each row: (date, market_code, nc_long, nc_short, comm_long, comm_short).
    """
    header = (
        "Report_Date_as_YYYY-MM-DD,CFTC_Contract_Market_Code,"
        "NonComm_Positions_Long_All,NonComm_Positions_Short_All,"
        "Comm_Positions_Long_All,Comm_Positions_Short_All\n"
    )
    body = "\n".join(f"{d},{m},{nl},{ns},{cl},{cs}" for d, m, nl, ns, cl, cs in rows)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("deacot.txt", header + body + "\n")
    buf.seek(0)
    return buf


def test_fetch_raises_offline_mode_error_when_offline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ALPHAKIT_OFFLINE", "1")
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))

    adapter = CFTCCOTAdapter()
    with pytest.raises(OfflineModeError, match="cftc-cot"):
        adapter.fetch(["067651"], datetime(2024, 1, 2), datetime(2024, 1, 10))


def test_fetch_returns_long_format_with_expected_columns(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        "alphakit.data.positioning.cftc_cot_adapter.ratelimit_acquire", lambda _n: None
    )

    def fake_urlopen(_url: str, timeout: float | None = None) -> io.BytesIO:
        return _build_cot_zip(
            [("2024-01-02", "067651", 100, 200, 300, 400)],
        )

    monkeypatch.setattr("alphakit.data.positioning.cftc_cot_adapter.urlopen", fake_urlopen)

    adapter = CFTCCOTAdapter()
    df = adapter.fetch(["067651"], datetime(2024, 1, 2), datetime(2024, 1, 10))

    expected_columns = {
        "date",
        "market_code",
        "long_positions",
        "short_positions",
        "net_positions",
        "commercial_long",
        "commercial_short",
        "speculative_long",
        "speculative_short",
    }
    assert set(df.columns) == expected_columns
    assert len(df) == 1
    row = df.iloc[0]
    assert row["market_code"] == "067651"
    assert int(row["speculative_long"]) == 100
    assert int(row["speculative_short"]) == 200
    assert int(row["commercial_long"]) == 300
    assert int(row["commercial_short"]) == 400
    assert int(row["long_positions"]) == 400  # 100 + 300
    assert int(row["short_positions"]) == 600  # 200 + 400
    assert int(row["net_positions"]) == -200  # 400 - 600


def test_fetch_filters_by_market_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        "alphakit.data.positioning.cftc_cot_adapter.ratelimit_acquire", lambda _n: None
    )

    def fake_urlopen(_url: str, timeout: float | None = None) -> io.BytesIO:
        return _build_cot_zip(
            [
                ("2024-01-02", "067651", 100, 200, 300, 400),
                ("2024-01-02", "023391", 50, 60, 70, 80),  # WTI — should be excluded
            ],
        )

    monkeypatch.setattr("alphakit.data.positioning.cftc_cot_adapter.urlopen", fake_urlopen)

    adapter = CFTCCOTAdapter()
    df = adapter.fetch(["067651"], datetime(2024, 1, 2), datetime(2024, 1, 10))

    assert len(df) == 1
    assert df.iloc[0]["market_code"] == "067651"


def test_fetch_filters_by_date_range(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        "alphakit.data.positioning.cftc_cot_adapter.ratelimit_acquire", lambda _n: None
    )

    def fake_urlopen(_url: str, timeout: float | None = None) -> io.BytesIO:
        return _build_cot_zip(
            [
                ("2023-12-26", "067651", 50, 60, 70, 80),  # out of range
                ("2024-01-02", "067651", 100, 200, 300, 400),
                ("2024-01-09", "067651", 110, 210, 310, 410),
                ("2024-01-16", "067651", 120, 220, 320, 420),  # out of range
            ],
        )

    monkeypatch.setattr("alphakit.data.positioning.cftc_cot_adapter.urlopen", fake_urlopen)

    adapter = CFTCCOTAdapter()
    df = adapter.fetch(["067651"], datetime(2024, 1, 2), datetime(2024, 1, 10))

    assert len(df) == 2
    dates = sorted(pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d").tolist())
    assert dates == ["2024-01-02", "2024-01-09"]


def test_fetch_spans_multiple_years(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(
        "alphakit.data.positioning.cftc_cot_adapter.ratelimit_acquire", lambda _n: None
    )

    fetched_urls: list[str] = []

    def fake_urlopen(url: str, timeout: float | None = None) -> io.BytesIO:
        fetched_urls.append(url)
        year = url.rsplit("deacot", 1)[-1].rstrip(".zip")
        return _build_cot_zip(
            [(f"{year}-06-15", "067651", 100, 200, 300, 400)],
        )

    monkeypatch.setattr("alphakit.data.positioning.cftc_cot_adapter.urlopen", fake_urlopen)

    adapter = CFTCCOTAdapter()
    df = adapter.fetch(["067651"], datetime(2023, 6, 1), datetime(2024, 7, 1))

    assert len(fetched_urls) == 2
    assert "deacot2023" in fetched_urls[0]
    assert "deacot2024" in fetched_urls[1]
    assert len(df) == 2
