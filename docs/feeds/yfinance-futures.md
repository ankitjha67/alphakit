# yfinance-futures adapter

**Status:** real · **Phase added:** 2B · **API key:** not required

Fetches continuous-contract futures OHLCV bars via
[`yfinance`](https://pypi.org/project/yfinance/). Registered separately
from the equities yfinance adapter so the rate-limit bucket is
independent — a futures-heavy workload will not starve equity fetches.

## What it provides

Daily (or intraday, if `frequency` supports) OHLCV bars for Yahoo's
continuous-contract symbols with the `=F` suffix:

| Symbol | Instrument                |
|--------|---------------------------|
| `CL=F` | WTI crude oil (front-month continuous) |
| `GC=F` | Gold                      |
| `NG=F` | Natural gas               |
| `SI=F` | Silver                    |
| `HG=F` | Copper                    |
| `ZC=F` | Corn                      |
| `ZS=F` | Soybeans                  |
| `ES=F` | E-mini S&P 500            |
| `NQ=F` | E-mini Nasdaq 100         |

The `=F` suffix is passed through to `yfinance.download` unchanged.
Single-symbol requests return a flat-column OHLCV frame; multi-symbol
requests return a MultiIndex-columned frame (symbol × field), matching
yfinance's native output.

## Strategies that use it

- Trend-following across commodities (Phase 2 trend family, commodity
  subset)
- Commodity-carry strategies that use front-month continuous pricing

## API key

None.

## Rate limit

Default 60 requests/minute under the `yfinance-futures` bucket
(separate from the equities `yfinance` bucket). Override with
`ALPHAKIT_RATELIMIT_YFINANCE_FUTURES_PER_MINUTE`.

## Cache TTL

24 hours.

## Example

```python
from datetime import datetime

from alphakit.data.registry import FeedRegistry

import alphakit.data.futures.yfinance_futures_adapter  # noqa: F401

futures = FeedRegistry.get("yfinance-futures")
df = futures.fetch(
    ["CL=F", "GC=F", "NG=F"],
    start=datetime(2023, 1, 1),
    end=datetime(2024, 12, 31),
)
```

## Offline mode

`ALPHAKIT_OFFLINE=1` routes to
`alphakit.data.offline.offline_fixture` and returns the shared
deterministic close-price panel (one column per symbol, daily business
days). This is a close-only panel — callers that need true OHLCV
offline must supply their own fixture.

## Known limitations

- Yahoo occasionally changes the `=F` continuous-contract methodology.
  Backtests that span a methodology change show a visible discontinuity.
  Production use should prefer a dedicated futures vendor (Phase 3+).
- Yahoo rate-limiting is undocumented and varies by endpoint; the
  60 req/min default is conservative.
