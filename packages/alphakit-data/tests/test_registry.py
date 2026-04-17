"""Tests for alphakit.data.registry.FeedRegistry."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

import pandas as pd
import pytest
from alphakit.core.data import OptionChain
from alphakit.core.protocols import raise_chain_not_supported
from alphakit.data.registry import FeedRegistry


class _StubFeed:
    """Minimal DataFeedProtocol implementation used as a registry fixture."""

    def __init__(self, name: str) -> None:
        self.name = name

    def fetch(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        frequency: str = "1d",
    ) -> pd.DataFrame:
        return pd.DataFrame({s: [1.0] for s in symbols})

    def fetch_chain(self, underlying: str, as_of: datetime) -> OptionChain:
        raise_chain_not_supported(self.name)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    """Reset the FeedRegistry before and after every test."""
    FeedRegistry.clear()
    yield
    FeedRegistry.clear()


def test_register_and_get_roundtrip() -> None:
    feed = _StubFeed("alpha")
    FeedRegistry.register(feed)
    assert FeedRegistry.get("alpha") is feed


def test_register_duplicate_raises_value_error() -> None:
    FeedRegistry.register(_StubFeed("alpha"))
    with pytest.raises(ValueError, match=r"'alpha' already registered"):
        FeedRegistry.register(_StubFeed("alpha"))


def test_get_unknown_key_lists_registered_feeds() -> None:
    FeedRegistry.register(_StubFeed("beta"))
    FeedRegistry.register(_StubFeed("alpha"))
    with pytest.raises(KeyError) as exc:
        FeedRegistry.get("ghost")
    msg = str(exc.value)
    assert "'ghost'" in msg
    # Message lists registered feeds sorted alphabetically.
    assert "alpha" in msg and "beta" in msg
    assert msg.index("alpha") < msg.index("beta")


def test_list_returns_sorted_names() -> None:
    FeedRegistry.register(_StubFeed("gamma"))
    FeedRegistry.register(_StubFeed("alpha"))
    FeedRegistry.register(_StubFeed("beta"))
    assert FeedRegistry.list() == ["alpha", "beta", "gamma"]


def test_clear_removes_all() -> None:
    FeedRegistry.register(_StubFeed("alpha"))
    FeedRegistry.register(_StubFeed("beta"))
    FeedRegistry.clear()
    assert FeedRegistry.list() == []


def test_register_independent_instances_same_name_still_rejected() -> None:
    """Two separate instances sharing a name must still raise."""
    FeedRegistry.register(_StubFeed("alpha"))
    second = _StubFeed("alpha")
    with pytest.raises(ValueError):
        FeedRegistry.register(second)


def test_get_returns_same_instance_across_calls() -> None:
    feed = _StubFeed("alpha")
    FeedRegistry.register(feed)
    assert FeedRegistry.get("alpha") is FeedRegistry.get("alpha")
