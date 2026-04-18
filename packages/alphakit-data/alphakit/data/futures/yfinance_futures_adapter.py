"""yfinance futures adapter for continuous commodity contracts.

Fetches OHLCV bars for continuous-contract futures symbols (``"CL=F"``
for front-month WTI crude, ``"GC=F"`` for gold, ``"NG=F"`` for natural
gas, etc.) via ``yfinance``. The adapter is deliberately thin: yfinance
already returns a sensible OHLCV DataFrame for ``=F``-suffixed symbols,
so this adapter's job is just to plug into the shared infrastructure
(registry, cache, rate-limit, offline mode) with a distinct feed name.

Cross-cutting concerns wired via decorators and guard calls:

* :func:`alphakit.data.cache.cached_feed` — 24-hour parquet cache.
* :func:`alphakit.data.rate_limit.acquire` — per-feed token bucket
  under the ``"yfinance-futures"`` bucket (separate from the equities
  bucket so a futures-heavy workload doesn't starve equity fetches).
* :func:`alphakit.data.offline.is_offline` +
  :func:`alphakit.data.offline.offline_fixture` — route to the shared
  fixture generator when ``ALPHAKIT_OFFLINE=1``. The fixture returns a
  close-price panel only; consumers that need true OHLCV offline should
  supply their own fixture rather than relying on this fallback.

Registers at import time under ``name="yfinance-futures"``.
"""

from __future__ import annotations

import contextlib
from datetime import datetime

import pandas as pd
from alphakit.core.data import OptionChain
from alphakit.core.protocols import raise_chain_not_supported
from alphakit.data.cache import cached_feed
from alphakit.data.offline import is_offline, offline_fixture
from alphakit.data.rate_limit import acquire as ratelimit_acquire
from alphakit.data.registry import FeedRegistry

_CACHE_TTL_SECONDS = 86_400  # 24 hours


class YFinanceFuturesAdapter:
    """Fetch continuous-contract futures via yfinance.

    Options on futures are out of scope — ``fetch_chain`` raises via
    the shared helper.
    """

    name: str = "yfinance-futures"

    @cached_feed(ttl_seconds=_CACHE_TTL_SECONDS)
    def fetch(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        frequency: str = "1d",
    ) -> pd.DataFrame:
        """Return an OHLCV DataFrame for continuous-contract symbols.

        ``symbols`` should carry the ``=F`` suffix yfinance uses for
        continuous contracts (``"CL=F"``, ``"GC=F"``, ``"NG=F"``, ...).
        The suffix is passed through unchanged.

        Offline mode (``ALPHAKIT_OFFLINE=1``) returns a deterministic
        close-price panel from
        :func:`alphakit.data.offline.offline_fixture` instead of hitting
        the network. Callers that need true OHLCV columns offline must
        substitute their own fixture.
        """
        if is_offline():
            return offline_fixture(symbols, start, end, frequency)

        ratelimit_acquire(self.name)

        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError(
                "yfinance is required. Install with: pip install 'alphakit-data[yfinance]'"
            ) from exc

        data = yf.download(
            tickers=symbols,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=frequency,
            auto_adjust=True,
            progress=False,
        )

        data = data.dropna(how="all")
        data.index = pd.DatetimeIndex(data.index)
        data.index.name = None
        return pd.DataFrame(data)

    def fetch_chain(self, underlying: str, as_of: datetime) -> OptionChain:
        """Options on futures are out of scope for this adapter."""
        raise_chain_not_supported(self.name)


with contextlib.suppress(ValueError):
    FeedRegistry.register(YFinanceFuturesAdapter())
