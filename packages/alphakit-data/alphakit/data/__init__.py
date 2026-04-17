"""AlphaKit data adapters.

Public API for the Phase 2 multi-feed architecture:

* :class:`FeedRegistry` — name-keyed registry of data-feed adapters.
* :class:`FeedCache` and :func:`cached_feed` — disk-backed parquet cache.
* :func:`ratelimit_acquire` — per-feed token-bucket rate limiter.
* :func:`is_offline`, :func:`offline_fixture`, :func:`offline_fallback`
  — offline-mode helpers that route to fixture data when
  ``ALPHAKIT_OFFLINE=1``.
* Exception hierarchy rooted at :class:`FeedError`.
"""

from __future__ import annotations

from alphakit.data.cache import FeedCache, cached_feed
from alphakit.data.errors import (
    FeedError,
    FeedNotConfiguredError,
    OfflineModeError,
    PolygonNotConfiguredError,
)
from alphakit.data.offline import is_offline, offline_fallback, offline_fixture
from alphakit.data.rate_limit import acquire as ratelimit_acquire
from alphakit.data.registry import FeedRegistry

__all__ = [
    "FeedCache",
    "FeedError",
    "FeedNotConfiguredError",
    "FeedRegistry",
    "OfflineModeError",
    "PolygonNotConfiguredError",
    "cached_feed",
    "is_offline",
    "offline_fallback",
    "offline_fixture",
    "ratelimit_acquire",
]
