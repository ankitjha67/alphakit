# ADR-001: Carry-family data gap handled via price-derived proxies

- **Status**: Accepted
- **Date**: 2026-04-16
- **Deciders**: Project maintainers

## Context

Carry strategies (FX, equity, bond, vol, crypto) need yield/rate feeds
that the close-only `StrategyProtocol` doesn't provide. The protocol's
`generate_signals(prices: pd.DataFrame) -> pd.DataFrame` contract
accepts a single price panel (timestamp index, symbol columns, adjusted
close values). Carry-family strategies fundamentally depend on auxiliary
data — interest-rate differentials, dividend yields, repo rates, funding
rates, implied volatility — that cannot be derived from close prices
alone without approximation.

This is the third instance of a data-gap pattern in Phase 1:

- `overnight_intraday` needed open prices (close-only protocol)
- `crypto_basis_perp` needed separate perp/spot price feeds
- `residual_momentum` needed Fama-French 3-factor returns

## Options considered

### A) Extend StrategyProtocol with optional `carry_feed`

Add an optional keyword argument or a second protocol method for
auxiliary data feeds:

```python
def generate_signals(
    self,
    prices: pd.DataFrame,
    *,
    carry_feed: pd.DataFrame | None = None,
) -> pd.DataFrame: ...
```

**Pros**: Cleaner long-term architecture, type-safe, explicit.
**Cons**: Requires changes to `alphakit-core` and all 30 existing
strategies (even if just to accept and ignore the kwarg). Breaks
the simplicity of the current protocol. Premature — we don't yet
know the full shape of auxiliary data needs (options chains, order
books, alt-data will emerge in later phases).

### B) Price-derived proxies with honest documentation

Synthesize carry from price-derived proxies (e.g., implied from
futures basis for FX carry, trailing dividend yield from price
returns for equity carry). Document each proxy choice honestly in
the strategy's `paper.md` and aggregate all simplifications in
`docs/deviations.md`.

**Pros**: Consistent with the precedent set by `overnight_intraday`,
`crypto_basis_perp`, and `residual_momentum`. Ships Phase 1 on pace.
No core protocol changes needed.
**Cons**: Proxies are approximations. Backtest results will differ
from production implementations that use actual carry data.

## Decision

**Option B** for Phase 1. Proper multi-feed architecture revisited
in Phase 2 or Phase 4 when options chains, order books, and alt-data
will collectively justify a general-purpose protocol extension.

## Consequences

1. Carry strategies ship with `paper.md` documenting each proxy
   choice and its limitations vs. the ideal data feed.
2. `docs/deviations.md` aggregates all documented simplifications
   across all Phase 1 families (trend, meanrev, carry).
3. Phase 4 ticket created: **"Unified multi-feed StrategyProtocol
   extension"** with scope covering carry feeds, options chains,
   order books, and alt-data.
4. Each carry strategy's `known_failures.md` includes a section on
   proxy-vs-actual data discrepancies.

## Related decisions

- `overnight_intraday`: close-only protocol, no open prices →
  approximated via cross-sectional residuals
- `crypto_basis_perp`: no separate perp/spot feeds → used fast/slow
  MA spread as basis proxy
- `residual_momentum`: no Fama-French factor feed → used market
  return as single factor
