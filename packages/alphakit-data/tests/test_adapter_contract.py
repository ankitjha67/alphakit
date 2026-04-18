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


HARNESSES: dict[str, Harness] = {
    "yfinance": Harness(
        module_path="alphakit.data.equities.yfinance_adapter",
        offline_behavior="fixture",
        fetch_args=(["SPY"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_yfinance_mock,
    ),
    "yfinance-futures": Harness(
        module_path="alphakit.data.futures.yfinance_futures_adapter",
        offline_behavior="fixture",
        fetch_args=(["CL=F"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_yfinance_futures_mock,
    ),
    "fred": Harness(
        module_path="alphakit.data.rates.fred_adapter",
        offline_behavior="raise",
        fetch_args=(["DGS10"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_fred_mock,
        extra_env={"FRED_API_KEY": "test-key-not-real"},
    ),
    "eia": Harness(
        module_path="alphakit.data.futures.eia_adapter",
        offline_behavior="raise",
        fetch_args=(["PET.WTISPLC.W"], datetime(2024, 1, 2), datetime(2024, 1, 10)),
        install_http_mock=_install_eia_mock,
        extra_env={"EIA_API_KEY": "test-key-not-real"},
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
    """``fetch_chain`` must either raise or return an OptionChain.

    All Phase 2B free-feed adapters raise via
    ``raise_chain_not_supported``. When Session 2C adds options-capable
    adapters (synthetic, Polygon), extend the harness with an
    ``implements_chain`` flag and branch here.
    """
    adapter = FeedRegistry.get(name)
    with pytest.raises(NotImplementedError, match=f"{name!r}"):
        adapter.fetch_chain("SPY", datetime(2024, 1, 2))
