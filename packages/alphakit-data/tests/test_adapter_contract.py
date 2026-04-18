"""Shared contract test for every ``DataFeedProtocol`` adapter.

Per ``docs/phase-2-amendments.md`` 2026-04-17 entry #3, every adapter
registered with :class:`alphakit.data.registry.FeedRegistry` must satisfy
a uniform contract: discoverable, offline-compliant, cached, rate-limited,
and chain-aware. This module exercises that contract with a single
parametrised test suite so future sessions cannot add an adapter that
silently drops one of the guarantees.

Adapters register with ``FeedRegistry`` at import time via module-level
``FeedRegistry.register()`` calls. Python doesn't auto-import
sub-packages, so every adapter must be imported explicitly in this
file to populate the registry before the parametrised contract tests
collect. Add the import and a ``HARNESSES`` entry together whenever a
new adapter lands. Failure to register shows up as
``test_adapter_is_in_harness_table`` or a missing parametrisation.

Update this list when adding adapters in Sessions 2C and beyond.
"""

from __future__ import annotations

import contextlib
import sys
import types
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

# Adapter modules — each ``from ... import`` below loads the adapter
# module, which triggers its module-level ``FeedRegistry.register()``
# call. Python doesn't auto-import sub-packages, so every adapter must
# be referenced explicitly here to populate the registry before the
# contract tests run. When a new adapter lands, add it to this block.
from alphakit.data.equities.yfinance_adapter import YFinanceAdapter
from alphakit.data.errors import OfflineModeError
from alphakit.data.futures.eia_adapter import EIAAdapter
from alphakit.data.futures.yfinance_futures_adapter import YFinanceFuturesAdapter
from alphakit.data.positioning.cftc_cot_adapter import CFTCCOTAdapter
from alphakit.data.rates.fred_adapter import FREDAdapter
from alphakit.data.registry import FeedRegistry


@dataclass(frozen=True)
class Harness:
    """Per-adapter test hooks keyed by the registered feed name."""

    module_path: str
    """Dotted path to the adapter's defining module. Used to
    monkeypatch ``ratelimit_acquire`` inside the adapter's namespace."""

    offline_behavior: str
    """``"fixture"`` (adapter.fetch returns a fixture DataFrame) or
    ``"raise"`` (adapter.fetch raises OfflineModeError)."""

    fetch_args: tuple[list[str], datetime, datetime]
    """Positional args passed as ``adapter.fetch(symbols, start, end)``."""

    install_http_mock: Callable[[pytest.MonkeyPatch, list[str], int], None]
    """Install a mock HTTP boundary for the adapter. Each outbound call
    appends ``"http"`` to the call log. ``payload_variant`` selects a
    canned response so the caching behavioural test can distinguish
    the first vs second fetch payload."""

    extra_env: dict[str, str] = field(default_factory=dict)
    """Extra environment variables to set before online-scenario tests.
    Adapters that require an API key (e.g. ``FRED_API_KEY``,
    ``EIA_API_KEY``) list a dummy value here so Scenario B can exercise
    the full fetch pipeline without raising ``FeedNotConfiguredError``."""

    implements_fetch: bool = True
    """``True`` if ``fetch`` returns a price panel; ``False`` if it
    raises ``NotImplementedError`` (e.g. Polygon placeholder,
    synthetic-options which is chain-only). Adapters with
    ``implements_fetch=False`` opt out of the offline/caching/rate-limit
    scenarios, which all assume a working ``fetch``."""

    implements_chain: bool = False
    """``True`` if ``fetch_chain`` returns an ``OptionChain``; ``False``
    if it raises. Session 2C's synthetic-options feed flips this on so
    the chain-return + determinism contract tests run against it."""

    fetch_error_type: type[BaseException] = NotImplementedError
    """Exception type raised by ``fetch`` when ``implements_fetch`` is
    ``False``. Used by :func:`test_adapter_fetch_raises_when_unsupported`."""

    chain_error_type: type[BaseException] = NotImplementedError
    """Exception type raised by ``fetch_chain`` when ``implements_chain``
    is ``False``. Polygon uses ``PolygonNotConfiguredError``; every other
    non-options adapter uses the default ``NotImplementedError`` via
    :func:`raise_chain_not_supported`."""

    chain_error_match: str | None = None
    """Regex matched against the ``fetch_chain`` error message. ``None``
    skips the match (Polygon's configuration-error message is
    stylistically different from the ``f"{name!r}"`` pattern that
    ``raise_chain_not_supported`` emits)."""


def _install_yfinance_mock(
    monkeypatch: pytest.MonkeyPatch,
    call_log: list[str],
    payload_variant: int,
) -> None:
    """Install a fake ``yfinance`` module so ``import yfinance`` picks it up."""
    fake = types.ModuleType("yfinance")

    def fake_download(**_kwargs: Any) -> pd.DataFrame:
        call_log.append("http")
        return pd.DataFrame(
            {"Close": [100.0 + payload_variant, 101.0 + payload_variant]},
            index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"]),
        )

    fake.download = fake_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "yfinance", fake)


def _install_yfinance_futures_mock(
    monkeypatch: pytest.MonkeyPatch,
    call_log: list[str],
    payload_variant: int,
) -> None:
    """Install a fake ``yfinance`` module returning OHLCV bars.

    The fake lives in ``sys.modules["yfinance"]`` just like the equities
    adapter's fake; whichever adapter's ``fetch`` runs next will pick up
    whichever fake was installed most recently, which is fine because
    contract tests monkeypatch the module per-test.
    """
    fake = types.ModuleType("yfinance")

    def fake_download(**_kwargs: Any) -> pd.DataFrame:
        call_log.append("http")
        return pd.DataFrame(
            {
                "Open": [70.0 + payload_variant, 71.0 + payload_variant],
                "High": [72.0 + payload_variant, 73.0 + payload_variant],
                "Low": [69.0 + payload_variant, 70.0 + payload_variant],
                "Close": [71.0 + payload_variant, 72.0 + payload_variant],
                "Volume": [1000, 2000],
            },
            index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"]),
        )

    fake.download = fake_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "yfinance", fake)


def _install_fred_mock(
    monkeypatch: pytest.MonkeyPatch,
    call_log: list[str],
    payload_variant: int,
) -> None:
    """Install a fake ``fredapi`` module exposing a ``Fred`` class."""
    fake = types.ModuleType("fredapi")

    class FakeFred:
        def __init__(self, api_key: str | None = None) -> None:
            self._api_key = api_key

        def get_series(self, series_id: str, **_kwargs: Any) -> pd.Series:
            call_log.append("http")
            return pd.Series(
                [100.0 + payload_variant, 101.0 + payload_variant],
                index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"]),
                name=series_id,
            )

    fake.Fred = FakeFred  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fredapi", fake)


def _install_eia_mock(
    monkeypatch: pytest.MonkeyPatch,
    call_log: list[str],
    payload_variant: int,
) -> None:
    """Install a fake ``requests`` module with a ``get`` returning EIA v2 JSON."""
    fake = types.ModuleType("requests")

    class FakeResponse:
        def __init__(self, data: dict[str, Any]) -> None:
            self._data = data

        def json(self) -> dict[str, Any]:
            return self._data

        def raise_for_status(self) -> None:
            return None

    def fake_get(_url: str, params: dict[str, Any] | None = None, **_kwargs: Any) -> FakeResponse:
        call_log.append("http")
        return FakeResponse(
            {
                "response": {
                    "data": [
                        {"period": "2024-01-02", "value": str(100.0 + payload_variant)},
                        {"period": "2024-01-03", "value": str(101.0 + payload_variant)},
                    ]
                }
            }
        )

    fake.get = fake_get  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "requests", fake)


def _install_cftc_cot_mock(
    monkeypatch: pytest.MonkeyPatch,
    call_log: list[str],
    payload_variant: int,
) -> None:
    """Replace ``cftc_cot_adapter.urlopen`` with a fake returning a COT-shaped ZIP."""
    import io
    import zipfile

    def fake_urlopen(_url: str, timeout: float | None = None) -> io.BytesIO:
        call_log.append("http")
        csv = (
            "Report_Date_as_YYYY-MM-DD,CFTC_Contract_Market_Code,"
            "NonComm_Positions_Long_All,NonComm_Positions_Short_All,"
            "Comm_Positions_Long_All,Comm_Positions_Short_All\n"
            f"2024-01-02,067651,{100 + payload_variant},{200 + payload_variant},"
            f"{300 + payload_variant},{400 + payload_variant}\n"
            f"2024-01-09,067651,{110 + payload_variant},{210 + payload_variant},"
            f"{310 + payload_variant},{410 + payload_variant}\n"
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("deacot2024.txt", csv)
        buf.seek(0)
        return buf

    monkeypatch.setattr("alphakit.data.positioning.cftc_cot_adapter.urlopen", fake_urlopen)


HARNESSES: dict[str, Harness] = {
    "yfinance": Harness(
        module_path="alphakit.data.equities.yfinance_adapter",
        offline_behavior="fixture",
        fetch_args=(["SPY"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_yfinance_mock,
        implements_fetch=True,
        implements_chain=False,
    ),
    "yfinance-futures": Harness(
        module_path="alphakit.data.futures.yfinance_futures_adapter",
        offline_behavior="fixture",
        fetch_args=(["CL=F"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_yfinance_futures_mock,
        implements_fetch=True,
        implements_chain=False,
    ),
    "fred": Harness(
        module_path="alphakit.data.rates.fred_adapter",
        offline_behavior="raise",
        fetch_args=(["DGS10"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_fred_mock,
        extra_env={"FRED_API_KEY": "test-key-not-real"},
        implements_fetch=True,
        implements_chain=False,
    ),
    "eia": Harness(
        module_path="alphakit.data.futures.eia_adapter",
        offline_behavior="raise",
        fetch_args=(["PET.WTISPLC.W"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_eia_mock,
        extra_env={"EIA_API_KEY": "test-key-not-real"},
        implements_fetch=True,
        implements_chain=False,
    ),
    "cftc-cot": Harness(
        module_path="alphakit.data.positioning.cftc_cot_adapter",
        offline_behavior="raise",
        fetch_args=(["067651"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_cftc_cot_mock,
        implements_fetch=True,
        implements_chain=False,
    ),
}


def _registered_names() -> list[str]:
    """Snapshot ``FeedRegistry.list()`` at collection time.

    ``@pytest.mark.parametrize`` evaluates its argument when the test
    module is imported, which is also when the adapter imports above
    register their feeds. That ordering makes this snapshot safe.
    """
    return FeedRegistry.list()


@pytest.fixture(autouse=True)
def _ensure_adapters_registered() -> Iterator[None]:
    """Guarantee the registry is populated even if a prior test cleared it.

    ``tests/test_registry.py`` defines an autouse ``FeedRegistry.clear()``
    fixture scoped to its own module; if pytest ever reorders test files
    so that module runs first, its teardown would wipe the registry and
    every contract test here would then fail to find its adapter. This
    fixture re-registers the adapters cheaply on every test call.
    """
    with contextlib.suppress(ValueError):
        FeedRegistry.register(YFinanceAdapter())
    with contextlib.suppress(ValueError):
        FeedRegistry.register(YFinanceFuturesAdapter())
    with contextlib.suppress(ValueError):
        FeedRegistry.register(FREDAdapter())
    with contextlib.suppress(ValueError):
        FeedRegistry.register(EIAAdapter())
    with contextlib.suppress(ValueError):
        FeedRegistry.register(CFTCCOTAdapter())
    yield


_REGISTERED = _registered_names()


@pytest.mark.parametrize("name", _REGISTERED)
def test_adapter_is_in_harness_table(name: str) -> None:
    """Every registered adapter must have a harness entry.

    If this fails after adding a new adapter, update ``HARNESSES`` above.
    """
    assert name in HARNESSES, (
        f"No test harness for registered adapter {name!r}. Add an entry to HARNESSES in {__file__}."
    )


@pytest.mark.parametrize("name", _REGISTERED)
def test_adapter_discoverable_via_registry(name: str) -> None:
    adapter = FeedRegistry.get(name)
    assert adapter.name == name


@pytest.mark.parametrize("name", _REGISTERED)
def test_adapter_offline_behavior(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Scenario A: ``ALPHAKIT_OFFLINE=1`` routes to fixture or raises."""
    harness = HARNESSES[name]
    if not harness.implements_fetch:
        pytest.skip(f"{name!r} does not implement fetch; offline behaviour N/A")
    monkeypatch.setenv("ALPHAKIT_OFFLINE", "1")
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    # Belt-and-suspenders: break the HTTP stack so any accidental
    # fallthrough to the network path raises ImportError instead of
    # silently hitting a real API.
    monkeypatch.setitem(sys.modules, "yfinance", None)

    adapter = FeedRegistry.get(name)
    symbols, start, end = harness.fetch_args

    if harness.offline_behavior == "fixture":
        df = adapter.fetch(symbols, start, end)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
    elif harness.offline_behavior == "raise":
        with pytest.raises(OfflineModeError):
            adapter.fetch(symbols, start, end)
    else:
        pytest.fail(f"Unknown offline_behavior {harness.offline_behavior!r} for {name!r}")


@pytest.mark.parametrize("name", _REGISTERED)
def test_adapter_online_calls_ratelimit_before_http(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Scenario B: online fetch calls ``ratelimit_acquire(name)`` before HTTP."""
    harness = HARNESSES[name]
    if not harness.implements_fetch:
        pytest.skip(f"{name!r} does not implement fetch; rate-limit path N/A")
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    for env_key, env_value in harness.extra_env.items():
        monkeypatch.setenv(env_key, env_value)

    call_log: list[str] = []

    def recording_ratelimit(feed_name: str) -> None:
        call_log.append(f"ratelimit:{feed_name}")

    monkeypatch.setattr(f"{harness.module_path}.ratelimit_acquire", recording_ratelimit)
    harness.install_http_mock(monkeypatch, call_log, 0)

    adapter = FeedRegistry.get(name)
    symbols, start, end = harness.fetch_args
    adapter.fetch(symbols, start, end)

    expected = f"ratelimit:{name}"
    assert expected in call_log, (
        f"{name!r} did not call ratelimit_acquire({name!r}); log={call_log}"
    )
    assert "http" in call_log, f"HTTP mock never triggered for {name!r}"
    assert call_log.index(expected) < call_log.index("http"), (
        f"{name!r} must call ratelimit_acquire BEFORE the HTTP call; log={call_log}"
    )


@pytest.mark.parametrize("name", _REGISTERED)
def test_adapter_fetch_has_cached_feed_marker(name: str) -> None:
    """F3a: ``@cached_feed`` wraps fetch → ``__wrapped__`` attribute present."""
    harness = HARNESSES[name]
    if not harness.implements_fetch:
        pytest.skip(f"{name!r} does not implement fetch; cache marker N/A")
    adapter = FeedRegistry.get(name)
    assert hasattr(adapter.fetch, "__wrapped__"), (
        f"{name!r} adapter.fetch missing __wrapped__; is @cached_feed applied?"
    )


@pytest.mark.parametrize("name", _REGISTERED)
def test_adapter_caches_fetch_results(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """F3b: second fetch with same args returns cached payload.

    Populate the cache with payload A, replace the HTTP mock to return
    payload B, fetch again with the same args. A cache-bypassing
    implementation would return B; a correctly cached implementation
    returns A and never triggers the second mock.
    """
    harness = HARNESSES[name]
    if not harness.implements_fetch:
        pytest.skip(f"{name!r} does not implement fetch; caching N/A")
    monkeypatch.delenv("ALPHAKIT_OFFLINE", raising=False)
    monkeypatch.setenv("ALPHAKIT_CACHE_DIR", str(tmp_path))
    for env_key, env_value in harness.extra_env.items():
        monkeypatch.setenv(env_key, env_value)
    monkeypatch.setattr(f"{harness.module_path}.ratelimit_acquire", lambda _n: None)

    adapter = FeedRegistry.get(name)
    symbols, start, end = harness.fetch_args

    call_log_first: list[str] = []
    harness.install_http_mock(monkeypatch, call_log_first, 0)
    df_first = adapter.fetch(symbols, start, end)
    assert "http" in call_log_first

    call_log_second: list[str] = []
    harness.install_http_mock(monkeypatch, call_log_second, 1)
    df_second = adapter.fetch(symbols, start, end)
    assert call_log_second == [], (
        f"{name!r} second fetch should be a cache hit; call_log_second={call_log_second}"
    )
    pd.testing.assert_frame_equal(df_first, df_second)


@pytest.mark.parametrize("name", _REGISTERED)
def test_adapter_fetch_chain_raises_when_unsupported(name: str) -> None:
    """``fetch_chain`` must raise when ``implements_chain`` is ``False``.

    Most Phase 2B free-feed adapters raise via
    ``raise_chain_not_supported`` (a ``NotImplementedError`` whose
    message contains ``f"{name!r}"``). Session 2C's Polygon placeholder
    raises ``PolygonNotConfiguredError`` with a differently-formatted
    message — hence the optional ``chain_error_match``.
    """
    harness = HARNESSES[name]
    if harness.implements_chain:
        pytest.skip(f"{name!r} implements fetch_chain; covered by the returns-OptionChain test")
    adapter = FeedRegistry.get(name)
    if harness.chain_error_match is None:
        with pytest.raises(harness.chain_error_type):
            adapter.fetch_chain("SPY", datetime(2024, 1, 2))
    else:
        with pytest.raises(harness.chain_error_type, match=harness.chain_error_match):
            adapter.fetch_chain("SPY", datetime(2024, 1, 2))
