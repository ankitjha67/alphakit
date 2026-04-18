# FRED (St. Louis Fed) adapter

**Status:** real · **Phase added:** 2B · **API key:** required

Fetches macroeconomic time-series from the St. Louis Fed's
[FRED](https://fred.stlouisfed.org/) database via the
[`fredapi`](https://pypi.org/project/fredapi/) wrapper.

## What it provides

Thousands of daily, weekly, monthly, and quarterly series covering:

- Treasury yields (`DGS3MO`, `DGS2`, `DGS10`, `DGS30`, ...)
- Fed funds rate (`DFF`, `FEDFUNDS`)
- CPI and inflation (`CPIAUCSL`, `CPILFESL`)
- Unemployment (`UNRATE`, `U6RATE`)
- Industrial production, retail sales, housing starts, and hundreds more

Symbols passed to `fetch()` are FRED series IDs. `frequency` is accepted
for signature parity but ignored — FRED returns whatever cadence each
series publishes.

## Strategies that use it

- Phase 2 rates-family strategies (treasury term-structure signals,
  carry-of-the-curve)
- Macro regime gates across every family (e.g. CPI-surprise overlays)

## API key

Register for a free key at
<https://fred.stlouisfed.org/docs/api/api_key.html>. Export it:

```bash
export FRED_API_KEY='your-key-here'
```

Missing key raises `FeedNotConfiguredError` at call time — the adapter
can still be imported and registered without a key.

## Rate limit

Default 120 requests/minute (matches FRED's published limit). Override
with `ALPHAKIT_RATELIMIT_FRED_PER_MINUTE`.

## Cache TTL

24 hours. FRED series update on their publication schedule (often
monthly), so same-day repeats are always safe cache hits.

## Example

```python
from datetime import datetime

from alphakit.data.registry import FeedRegistry

# Importing the module triggers registration.
import alphakit.data.rates.fred_adapter  # noqa: F401

fred = FeedRegistry.get("fred")
df = fred.fetch(
    ["DGS10", "DGS2"],
    start=datetime(2020, 1, 1),
    end=datetime(2024, 12, 31),
)
# df is a wide DataFrame indexed by date with DGS10 and DGS2 columns.
```

## Offline mode

`ALPHAKIT_OFFLINE=1` raises `OfflineModeError`. There is no synthetic
substitute for macro series — a fake yield curve is worse than no
yield curve. Tests that need to exercise FRED code paths must mock
`fredapi.Fred` directly (see
`packages/alphakit-data/tests/test_fred_adapter.py`).

## Known limitations

- The adapter issues one `fredapi.get_series` call per symbol. A batch
  endpoint would reduce round-trips but does not exist in the public
  API.
- Cached responses are keyed on `(symbols, start, end, frequency)`;
  overlapping date ranges do not share cache entries (Phase 3 may add
  range-merging).
