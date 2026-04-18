# CFTC COT (Commitments of Traders) adapter

**Status:** real · **Phase added:** 2B · **API key:** not required

Fetches the CFTC's weekly
[Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)
legacy report directly from `https://www.cftc.gov/dea/newcot/` via
`urllib`. Each yearly ZIP is downloaded once per calendar year in the
requested range.

## What it provides

Weekly speculator-vs-commercial positioning for every CFTC-regulated
futures market, reshaped into a long-format DataFrame:

| Column             | Description                                                  |
|--------------------|--------------------------------------------------------------|
| `date`             | Report date (Tuesday of the reported week)                   |
| `market_code`      | CFTC contract market code (zero-padded string)               |
| `long_positions`   | Total reportable long positions (commercial + non-commercial) |
| `short_positions`  | Total reportable short positions                             |
| `net_positions`    | `long_positions` − `short_positions`                         |
| `commercial_long`  | Commercial (hedger) long positions                           |
| `commercial_short` | Commercial (hedger) short positions                          |
| `speculative_long` | Non-commercial (large speculator) long positions             |
| `speculative_short`| Non-commercial (large speculator) short positions            |

Symbols passed to `fetch()` are CFTC market codes (e.g. `"067651"` for
E-mini S&P 500 futures, `"023391"` for WTI crude oil). `frequency` is
ignored — COT publishes weekly, every Friday, for data as of the
previous Tuesday.

## Strategies that use it

- Positioning-extreme mean-reversion signals (shorts when speculators
  are max long, longs when max short)
- Commodity carry overlays gated on commercial-hedger accumulation

## API key

None.

## Rate limit

Default 10 requests/minute under the `cftc-cot` bucket — generous
headroom against CFTC's anti-bot guidance. Override with
`ALPHAKIT_RATELIMIT_CFTC_COT_PER_MINUTE`.

## Cache TTL

7 days. COT publishes weekly; a shorter TTL would cause pointless
refetches.

## Example

```python
from datetime import datetime

from alphakit.data.registry import FeedRegistry

import alphakit.data.positioning.cftc_cot_adapter  # noqa: F401

cot = FeedRegistry.get("cftc-cot")
df = cot.fetch(
    ["067651"],  # E-mini S&P 500
    start=datetime(2023, 1, 1),
    end=datetime(2024, 12, 31),
)
```

## Offline mode

`ALPHAKIT_OFFLINE=1` raises `OfflineModeError`. CFTC positioning is
intrinsically real data — fabricating dealer positions would be
misleading. Tests should mock the adapter's `urlopen` (see
`packages/alphakit-data/tests/test_cftc_cot_adapter.py`).

## Known limitations

- The adapter downloads one ZIP per calendar year spanned by the
  request, even if only a single week is needed. For multi-year ranges
  this is efficient; for a single-week fetch it is wasteful.
- Columns are derived from the Legacy COT report; Traders in Financial
  Futures (TFF) and Disaggregated COT layouts are not wired up yet.
