"""CFTC Commitments of Traders (COT) weekly positioning adapter.

Downloads the CFTC legacy COT weekly report as a year-sized ZIP from
``https://www.cftc.gov/dea/newcot/``, extracts the embedded CSV, filters
by market code and date range, and reshapes into a long-format frame
suitable for strategies that trade off speculator / commercial
positioning.

* :func:`alphakit.data.cache.cached_feed` — 7-day parquet cache (COT
  publishes weekly every Friday for data as of the previous Tuesday;
  a shorter TTL would cause pointless refetches).
* :func:`alphakit.data.rate_limit.acquire` — per-feed token bucket
  under the ``"cftc-cot"`` bucket (default 10 req/min, generous
  headroom against CFTC's anti-bot guidance).
* :func:`alphakit.data.offline.is_offline` — CFTC inventories are
  integers tied to real dealer positions; there is no synthetic
  analogue, so offline mode raises :class:`OfflineModeError`.

No API key is required.

Output schema (long format)
---------------------------
``date`` (datetime64) · ``market_code`` (str) · ``long_positions`` ·
``short_positions`` · ``net_positions`` · ``commercial_long`` ·
``commercial_short`` · ``speculative_long`` · ``speculative_short``.

Registers at import time under ``name="cftc-cot"``.
"""

from __future__ import annotations

import contextlib
import io
import zipfile
from datetime import datetime
from urllib.request import urlopen

import pandas as pd
from alphakit.core.data import OptionChain
from alphakit.core.protocols import raise_chain_not_supported
from alphakit.data.cache import cached_feed
from alphakit.data.errors import OfflineModeError
from alphakit.data.offline import is_offline
from alphakit.data.rate_limit import acquire as ratelimit_acquire
from alphakit.data.registry import FeedRegistry

_CACHE_TTL_SECONDS = 604_800  # 7 days — COT is weekly
_COT_URL_TEMPLATE = "https://www.cftc.gov/dea/newcot/deacot{year}.zip"
_URLOPEN_TIMEOUT_SECONDS = 60.0

# Legacy COT column headers. These names are stable across reports
# going back many years.
_COL_DATE = "Report_Date_as_YYYY-MM-DD"
_COL_MARKET = "CFTC_Contract_Market_Code"
_COL_NC_LONG = "NonComm_Positions_Long_All"
_COL_NC_SHORT = "NonComm_Positions_Short_All"
_COL_COMM_LONG = "Comm_Positions_Long_All"
_COL_COMM_SHORT = "Comm_Positions_Short_All"


class CFTCCOTAdapter:
    """Fetch CFTC COT weekly positioning via ``urllib``.

    COT is not an options feed; ``fetch_chain`` raises via the shared
    helper.
    """

    name: str = "cftc-cot"

    @cached_feed(ttl_seconds=_CACHE_TTL_SECONDS)
    def fetch(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        frequency: str = "1d",
    ) -> pd.DataFrame:
        """Return a long-format DataFrame of COT positioning.

        ``symbols`` are CFTC market codes as zero-padded strings, e.g.
        ``"067651"`` for E-mini S&P 500 futures or ``"023391"`` for
        WTI crude oil. ``frequency`` is ignored — COT publishes weekly.

        Offline mode (``ALPHAKIT_OFFLINE=1``) raises
        :class:`OfflineModeError`: CFTC positioning is intrinsically
        real data and has no synthetic analogue.
        """
        if is_offline():
            raise OfflineModeError(
                f"{self.name!r} has no offline fixture; set ALPHAKIT_OFFLINE=0 "
                "or mock the adapter in tests."
            )

        frames: list[pd.DataFrame] = []
        for year in range(start.year, end.year + 1):
            ratelimit_acquire(self.name)
            url = _COT_URL_TEMPLATE.format(year=year)
            with urlopen(url, timeout=_URLOPEN_TIMEOUT_SECONDS) as response:
                zip_bytes: bytes = response.read()
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                inner_name = zf.namelist()[0]
                with zf.open(inner_name) as handle:
                    frames.append(pd.read_csv(handle, dtype={_COL_MARKET: str}))

        combined = pd.concat(frames, ignore_index=True)
        combined[_COL_DATE] = pd.to_datetime(combined[_COL_DATE], format="%Y-%m-%d")
        combined = combined[combined[_COL_MARKET].isin(symbols)]
        mask = (combined[_COL_DATE] >= pd.Timestamp(start)) & (
            combined[_COL_DATE] <= pd.Timestamp(end)
        )
        combined = combined.loc[mask]

        nc_long = combined[_COL_NC_LONG].astype(int)
        nc_short = combined[_COL_NC_SHORT].astype(int)
        comm_long = combined[_COL_COMM_LONG].astype(int)
        comm_short = combined[_COL_COMM_SHORT].astype(int)

        result = pd.DataFrame(
            {
                "date": combined[_COL_DATE].to_numpy(),
                "market_code": combined[_COL_MARKET].astype(str).to_numpy(),
                "long_positions": (nc_long + comm_long).to_numpy(),
                "short_positions": (nc_short + comm_short).to_numpy(),
                "net_positions": (nc_long + comm_long - nc_short - comm_short).to_numpy(),
                "commercial_long": comm_long.to_numpy(),
                "commercial_short": comm_short.to_numpy(),
                "speculative_long": nc_long.to_numpy(),
                "speculative_short": nc_short.to_numpy(),
            }
        )
        return pd.DataFrame(result.reset_index(drop=True))

    def fetch_chain(self, underlying: str, as_of: datetime) -> OptionChain:
        """CFTC COT has no option chain surface."""
        raise_chain_not_supported(self.name)


with contextlib.suppress(ValueError):
    FeedRegistry.register(CFTCCOTAdapter())
