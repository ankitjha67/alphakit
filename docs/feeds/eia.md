# EIA (U.S. Energy Information Administration) adapter

**Status:** real · **Phase added:** 2B · **API key:** required

Fetches energy inventory, production, and price series from the
[EIA v2 API](https://www.eia.gov/opendata/documentation.php) via
`requests`. No third-party SDK is required; the API is a simple
REST+JSON surface.

## What it provides

Weekly / monthly series covering:

- Crude oil stocks (`PET.WCESTUS1.W`, `PET.WCRFPUS2.W`)
- Natural-gas storage (`NG.NW2_EPG0_SWO_R48_BCF.W`)
- WTI and Brent spot prices (`PET.WTISPLC.W`, `PET.RBRTE.D`)
- Refinery utilization, gasoline / diesel stocks, crude imports/exports

Symbols passed to `fetch()` are EIA v2 series IDs. `frequency` is
ignored — each series has its own publication cadence.

## Strategies that use it

- Commodity mean-reversion signals built on inventory surprises
- Energy-spread strategies (crack spreads, regional basis)

## API key

Register for a free key at
<https://www.eia.gov/opendata/register.php>. Export it:

```bash
export EIA_API_KEY='your-key-here'
```

Missing key raises `FeedNotConfiguredError` at call time.

## Rate limit

Default 80 requests/minute (below EIA's published 5000 requests/hour ≈
83 req/min limit, so we leave a small safety margin). Override with
`ALPHAKIT_RATELIMIT_EIA_PER_MINUTE`.

## Cache TTL

24 hours.

## Example

```python
from datetime import datetime

from alphakit.data.registry import FeedRegistry

import alphakit.data.futures.eia_adapter  # noqa: F401

eia = FeedRegistry.get("eia")
df = eia.fetch(
    ["PET.WCESTUS1.W", "NG.NW2_EPG0_SWO_R48_BCF.W"],
    start=datetime(2023, 1, 1),
    end=datetime(2024, 12, 31),
)
```

## Offline mode

`ALPHAKIT_OFFLINE=1` raises `OfflineModeError`. Physical inventory and
spot series have no reasonable synthetic analogue — fabricating weekly
storage numbers would mislead backtests. Tests must mock
`requests.get` (see
`packages/alphakit-data/tests/test_eia_adapter.py`).

## Known limitations

- One HTTP per symbol (EIA v2 does not provide a batch series
  endpoint).
- EIA occasionally revises historical values in place. The 24-hour
  cache will serve the pre-revision value until the next fetch; set
  `ALPHAKIT_CACHE_DIR=/dev/null` to force a live fetch when a known
  revision has shipped.
