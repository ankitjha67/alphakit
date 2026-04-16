# Quickstart

This page walks you through installing AlphaKit and running the Phase 0
reference strategy (`tsmom_12_1`) end-to-end in about 30 seconds.

## Install

AlphaKit targets Python 3.10 and later. We recommend
[`uv`](https://docs.astral.sh/uv/) for managing the project — it is
the same tool the maintainers and CI use.

=== "uv (recommended)"

    ```bash
    uv add alphakit
    ```

=== "pip"

    ```bash
    pip install alphakit
    ```

The base install pulls in `alphakit-core`, `alphakit-bridges` (which
transitively installs `vectorbt` and `backtrader`) and the
`alphakit-strategies-trend` family that contains the reference
strategy.

If you want to hack on AlphaKit itself, clone the repository and use
the uv workspace layout:

```bash
git clone https://github.com/ankitjha67/alphakit.git
cd alphakit
uv sync --extra dev
```

## Run the reference strategy

The reference strategy is a faithful implementation of
**Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum*, JFE**. We
use the vectorbt bridge to backtest it on a synthetic 6-asset panel so
the example is reproducible without any network calls.

```python
import numpy as np
import pandas as pd

from alphakit.bridges import vectorbt_bridge
from alphakit.strategies.trend import TimeSeriesMomentum12m1m

# 1. A deterministic 5-year, 6-asset synthetic panel (swap in real
#    prices from yfinance, Stooq, Polygon, CCXT, ... for production).
rng = np.random.default_rng(42)
index = pd.date_range("2020-01-01", periods=5 * 252, freq="B")
prices = pd.DataFrame(
    {sym: 100.0 * np.exp(np.cumsum(rng.normal(drift, vol, len(index))))
     for sym, (drift, vol) in {
         "SPY": (0.0006, 0.010),
         "EFA": (0.0002, 0.011),
         "EEM": (0.0003, 0.014),
         "AGG": (0.00005, 0.003),
         "GLD": (0.0004, 0.009),
         "DBC": (0.0002, 0.013),
     }.items()},
    index=index,
)

# 2. Instantiate the strategy with the Moskowitz-Ooi-Pedersen defaults.
strategy = TimeSeriesMomentum12m1m()

# 3. Run a vectorbt backtest with realistic frictions.
result = vectorbt_bridge.run(
    strategy=strategy,
    prices=prices,
    initial_cash=100_000.0,
    commission_bps=2.0,
    slippage_bps=1.0,
)

# 4. Inspect the headline metrics.
print(f"Sharpe:        {result.sharpe:.2f}")
print(f"Sortino:       {result.sortino:.2f}")
print(f"Calmar:        {result.calmar:.2f}")
print(f"Max DD:        {result.max_dd:.1%}")
print(f"Final equity:  {result.final_equity:.0f}")
```

## What just happened?

1. `TimeSeriesMomentum12m1m` is an ordinary Python class that satisfies
   [`StrategyProtocol`](architecture.md#strategyprotocol) — it exposes
   `name`, `family`, `asset_classes`, `paper_doi`,
   `rebalance_frequency` and a `generate_signals` method.
2. `vectorbt_bridge.run` translates the weights panel produced by
   `generate_signals` into a vectorbt `Portfolio.from_orders` call and
   normalises the native vectorbt output into a
   [`BacktestResult`](architecture.md#backtestresult).
3. Every engine bridge (vectorbt, backtrader, LEAN in Phase 2+)
   produces the **same** `BacktestResult` shape — so you can swap
   engines without rewriting strategy code.

## Next steps

- Read the [architecture](architecture.md) page to understand how the
  pieces fit together.
- Read the [strategy contract](strategy_contract.md) if you want to
  add a new strategy of your own.
- Browse the [full strategy list](https://github.com/ankitjha67/alphakit/tree/main/packages)
  in the repository.

## Troubleshooting

??? question "I installed alphakit but `from alphakit.strategies.trend import ...` fails"

    Check that you are using Python 3.10 or later. AlphaKit uses PEP 420
    namespace packages to spread sub-packages across wheels, and older
    Python versions do not resolve them reliably.

??? question "`vectorbt` fails to import with a Numba error"

    The `vectorbt` → Numba → llvmlite toolchain is sensitive to NumPy
    ABI changes. Re-running `uv sync --extra dev --reinstall-package vectorbt`
    usually fixes it. If you are on macOS arm64 you may need to install
    llvmlite via Homebrew first.

??? question "The backtrader bridge is slow on large universes"

    That is expected — backtrader is event-driven and does not
    vectorise. For universes bigger than ~50 symbols prefer the
    vectorbt bridge.
