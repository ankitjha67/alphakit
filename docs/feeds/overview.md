# Data feeds — overview

All AlphaKit strategies fetch data via the feed registry. Adapters
register themselves at module import time under a stable name;
strategies and the benchmark runner look them up via
`FeedRegistry.get(name)`. This page summarises every registered feed
at the current phase.

## Registered feeds

| Name                | Status      | API Key            | Rate Limit (default) | Offline behaviour                     | Phase added |
|---------------------|-------------|--------------------|----------------------|---------------------------------------|-------------|
| `yfinance`          | real        | —                  | 60 req/min           | routes to fixture (close-price panel) | 1 / 2A      |
| `yfinance-futures`  | real        | —                  | 60 req/min           | routes to fixture (close-price panel) | 2B          |
| `fred`              | real        | `FRED_API_KEY`     | 120 req/min          | raises `OfflineModeError`             | 2B          |
| `eia`               | real        | `EIA_API_KEY`      | 80 req/min           | raises `OfflineModeError`             | 2B          |
| `cftc-cot`          | real        | —                  | 10 req/min           | raises `OfflineModeError`             | 2B          |
| `polygon`           | placeholder | `POLYGON_API_KEY`* | —                    | raises `PolygonNotConfiguredError`    | 2C          |
| `synthetic-options` | synthetic   | —                  | —                    | works fully offline (chain-only)      | 2C          |

\* `POLYGON_API_KEY` is documented for the Phase 3 upgrade path. In
Phase 2 the adapter is a stub: with the key set, `fetch_chain` still
raises `NotImplementedError`; without the key it raises
`PolygonNotConfiguredError` directing callers to `synthetic-options`.

Planned (later sessions):

| Name                | Status      | Notes                                                  | Phase |
|---------------------|-------------|--------------------------------------------------------|-------|
| `ccxt`              | planned     | Crypto exchange data                                   | 3     |

## First-run experience (no keys configured)

Two of the five 2B adapters work out of the box: `yfinance`,
`yfinance-futures`, and `cftc-cot` need no credentials. A new user who
runs the Phase 2 equity/trend backtests end-to-end never has to touch
an API-key prompt.

Adding FRED or EIA costs ~30 seconds each:

- FRED key: <https://fred.stlouisfed.org/docs/api/api_key.html>
- EIA key: <https://www.eia.gov/opendata/register.php>

`FeedNotConfiguredError` is raised only when `fetch` is called without
the key — imports and registration succeed unconditionally, so a
partially-configured environment never breaks module loading.

## Offline mode (`ALPHAKIT_OFFLINE=1`)

Each adapter documents its offline behaviour in its per-feed page.
The shared contract test
(`packages/alphakit-data/tests/test_adapter_contract.py`) parametrises
over every registered adapter and verifies the documented behaviour
— fabric fixture or `OfflineModeError` — at the boundary.

## Cache directory

All adapters share a single parquet cache at
`${ALPHAKIT_CACHE_DIR:-~/.alphakit/cache}`. Set the directory to
`/dev/null` (POSIX) or `NUL` (Windows) to disable caching entirely —
useful for integration tests or freshness-sensitive workflows.

## Per-feed rate-limit override

Every default is overridable via environment variable. The variable
name derives from the feed name: upper-case, `-` replaced with `_`:

```bash
ALPHAKIT_RATELIMIT_FRED_PER_MINUTE=60           # half the FRED default
ALPHAKIT_RATELIMIT_YFINANCE_FUTURES_PER_MINUTE=30
ALPHAKIT_RATELIMIT_CFTC_COT_PER_MINUTE=5
```

Values must be positive integers; invalid values raise `ValueError`
the first time the bucket is used.

## Adding a new feed

1. Create the adapter under
   `packages/alphakit-data/alphakit/data/<subdir>/<name>_adapter.py`.
2. Implement `DataFeedProtocol`: `name`, `fetch`, `fetch_chain`.
3. Decorate `fetch` with `@cached_feed(ttl_seconds=...)` and call
   `ratelimit_acquire(self.name)` before any outbound HTTP.
4. Call `is_offline()` inside `fetch` and either return fixture data
   or raise `OfflineModeError`.
5. Register at module import time:
   `with contextlib.suppress(ValueError): FeedRegistry.register(MyAdapter())`.
6. Add the module to the adapter-imports block at the top of
   `packages/alphakit-data/tests/test_adapter_contract.py` and add a
   `HARNESSES` entry so the parametrised contract tests cover it.
7. Add a `docs/feeds/<name>.md` page and a row in this overview.
