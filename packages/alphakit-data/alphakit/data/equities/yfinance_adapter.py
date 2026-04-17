"""YFinance data adapter with local parquet cache.

Fetches daily adjusted close prices via yfinance, caches to
~/.alphakit/cache/ as parquet files with 7-day TTL.

Security note: yfinance makes HTTPS requests to Yahoo Finance API.
No credentials are required. Cache files are stored locally.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from pathlib import Path

import pandas as pd


class YFinanceAdapter:
    """Fetch equity/ETF prices via yfinance with parquet cache.

    Parameters
    ----------
    cache_dir
        Directory for parquet cache files.
    ttl_days
        Cache time-to-live in days. Default 7.
    """

    name: str = "yfinance"

    def __init__(
        self,
        *,
        cache_dir: str | Path | None = None,
        ttl_days: int = 7,
    ) -> None:
        if cache_dir is None:
            self.cache_dir = Path.home() / ".alphakit" / "cache" / "yfinance"
        else:
            self.cache_dir = Path(cache_dir)
        self.ttl_days = ttl_days

    def fetch(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        frequency: str = "1d",
    ) -> pd.DataFrame:
        """Fetch adjusted close prices for symbols.

        Returns a DataFrame indexed by date with one column per symbol.
        Uses parquet cache when available and fresh.
        """
        cache_key = self._cache_key(symbols, start, end, frequency)
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        # Import yfinance lazily
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError(
                "yfinance is required. Install with: pip install 'alphakit-data[yfinance]'"
            ) from exc

        # Batch download
        data = yf.download(
            tickers=symbols,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=frequency,
            auto_adjust=True,
            progress=False,
        )

        # Extract adjusted close prices
        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"]
        else:
            prices = data[["Close"]]
            prices.columns = symbols

        prices = prices.dropna(how="all")
        prices.index = pd.DatetimeIndex(prices.index)
        prices.index.name = None

        self._save_cache(cache_key, prices)
        return pd.DataFrame(prices)

    def _cache_key(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        frequency: str,
    ) -> str:
        raw = f"{sorted(symbols)}|{start}|{end}|{frequency}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _load_cache(self, key: str) -> pd.DataFrame | None:
        path = self.cache_dir / f"{key}.parquet"
        if not path.exists():
            return None
        age_days = (time.time() - path.stat().st_mtime) / 86400
        if age_days > self.ttl_days:
            path.unlink()
            return None
        return pd.read_parquet(path)

    def _save_cache(self, key: str, df: pd.DataFrame) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{key}.parquet"
        df.to_parquet(path, engine="pyarrow")
