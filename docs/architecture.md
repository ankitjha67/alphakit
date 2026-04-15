# Architecture

AlphaKit is organised as a **thin core** with **independent
sub-packages** for each strategy family, engine bridge and data
adapter. This page explains why, and how the pieces plug into each
other.

## Layers

```
┌────────────────────────────────────────────────────────────┐
│                    User code / notebook                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────────┐
          │  alphakit.strategies.<family>     │   ← 23+ family sub-packages
          │     (trend, meanrev, carry, …)    │
          └────────────────┬──────────────────┘
                           │     implements StrategyProtocol
                           ▼
          ┌───────────────────────────────────┐
          │         alphakit.bridges          │   ← vectorbt / backtrader / LEAN
          │       run(strategy, prices)       │
          └────────────────┬──────────────────┘
                           │     returns BacktestResult
                           ▼
          ┌───────────────────────────────────┐
          │           alphakit.core           │   ← protocols, data, metrics
          │   StrategyProtocol | BacktestResult
          │   Bar | Instrument | Portfolio    │
          └────────────────┬──────────────────┘
                           │     consumes DataFrame panels
                           ▼
          ┌───────────────────────────────────┐
          │          alphakit.data            │   ← yfinance / CCXT / FRED / …
          │    DataFeedProtocol.fetch(...)    │
          └───────────────────────────────────┘
```

The critical design rule is that **dependencies point inward**: family
packages depend on core, but core never depends on any family. Adding
a new strategy, bridge or data adapter is a pure extension — it does
not touch a single line of core code.

## The three protocols

Everything in AlphaKit plugs into one of three `runtime_checkable`
protocols, all defined in
[`alphakit.core.protocols`](https://github.com/ankitjha67/alphakit/blob/main/packages/alphakit-core/alphakit/core/protocols.py).

### `StrategyProtocol`

A strategy is a **pure function of a price panel**: given OHLCV data,
produce a weights DataFrame. The framework handles sizing, execution,
commissions and bookkeeping.

```python
class StrategyProtocol(Protocol):
    name: str                      # unique slug, e.g. "tsmom_12_1"
    family: str                    # "trend", "meanrev", ...
    asset_classes: list[str]       # ["equity", "future", "fx", ...]
    paper_doi: str                 # DOI / arXiv / ISBN — never blank
    rebalance_frequency: str       # "daily" | "weekly" | "monthly" | ...

    def generate_signals(self, prices: pd.DataFrame) -> pd.DataFrame:
        """prices → target weights, aligned to the same index."""
```

Key properties:

- **Pure**: same input ⇒ same output. No hidden RNG, no file I/O, no
  network. Deterministic tests rely on this.
- **Vectorised**: strategies see the full price panel at once, not
  bar-by-bar. This is how we compile down to vectorbt.
- **Engine-agnostic**: a strategy does not know or care which bridge
  will run it.

### `BacktestEngineProtocol`

The single entrypoint every engine bridge exposes:

```python
class BacktestEngineProtocol(Protocol):
    name: str
    def run(
        self,
        strategy: StrategyProtocol,
        prices: pd.DataFrame,
        *,
        initial_cash: float = 100_000.0,
        commission_bps: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> BacktestResult: ...
```

Because every bridge returns the same `BacktestResult`, swapping
engines is a one-line change in user code.

### `DataFeedProtocol`

```python
class DataFeedProtocol(Protocol):
    name: str
    def fetch(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        frequency: str = "1d",
    ) -> pd.DataFrame: ...
```

Each adapter (`yfinance`, `ccxt`, `fred`, ...) implements this
interface. Adapters live in `alphakit.data` and are installed by
opt-in extras so that a crypto user does not pay for an equities
dependency tree.

## `BacktestResult`

Every engine bridge normalises its native output into this pydantic
v2 model:

```python
class BacktestResult(BaseModel):
    equity_curve: pd.Series
    returns: pd.Series
    weights: pd.DataFrame
    metrics: dict[str, float]
    meta: dict[str, Any]
```

`metrics` contains the headline Sharpe / Sortino / Calmar / max-DD /
final-equity set, computed by **AlphaKit's own** metric functions
(from `alphakit.core.metrics`) rather than the engine's native ones.
This guarantees that the same strategy, run on vectorbt vs. backtrader
vs. LEAN, produces numerically comparable metrics.

## Engine bridges

Phase 0 ships three bridges:

| Bridge | Engine | Best for |
|---|---|---|
| `vectorbt_bridge` | [vectorbt](https://vectorbt.dev) | daily-ish strategies, large universes, fast iteration |
| `backtrader_bridge` | [backtrader](https://www.backtrader.com) | event-driven logic, custom execution models, small universes |
| `lean_bridge` | [LEAN](https://www.lean.io) | **Phase 2+** — options, futures, live trading (currently a typed stub) |

All three are thin wrappers over the native engine API. The bridge
code lives in
[`packages/alphakit-bridges/alphakit/bridges/`](https://github.com/ankitjha67/alphakit/tree/main/packages/alphakit-bridges/alphakit/bridges).

## Data adapter pattern

Data adapters are expected to be **boring and auditable**:

1. Take a list of symbols, a date range, and a frequency.
2. Hit the upstream source (file, API, database).
3. Return a pandas DataFrame with a `DatetimeIndex` and one column per
   symbol containing adjusted close prices.

Adapters that expose full OHLCV return a `MultiIndex` on columns
(`symbol`, `field`). Caching, rate-limiting, credential management
and retry logic are all the adapter's responsibility — strategies
should never see them.

## Per-strategy contract

Every strategy ships a directory that looks like this:

```
packages/alphakit-strategies-<family>/alphakit/strategies/<family>/<slug>/
├── __init__.py
├── strategy.py              # Implements StrategyProtocol
├── config.yaml              # Default parameters and universe
├── paper.md                 # Citation, abstract, parameter rationale
├── benchmark_results.json   # OOS statistics (Appendix C schema)
├── known_failures.md        # Regimes where it underperforms
├── README.md                # 1-page user guide
└── tests/
    ├── __init__.py
    ├── test_unit.py
    └── test_integration.py
```

See [strategy contract](strategy_contract.md) for the full spec and
the reference implementation in
[`tsmom_12_1`](https://github.com/ankitjha67/alphakit/tree/main/packages/alphakit-strategies-trend/alphakit/strategies/trend/tsmom_12_1)
for a working example.

## Modular install

AlphaKit uses pip extras to keep installs minimal:

```bash
pip install alphakit                # core + bridges + trend reference
pip install alphakit[crypto]        # adds CCXT
pip install alphakit[ml]            # adds sklearn, xgboost, lightgbm
pip install alphakit[all]           # everything, including torch + CUDA
```

Installing an extra never activates another extra — a crypto user is
not forced to download pandas-stubs or PyTorch.
