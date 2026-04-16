# ADR-002: `_proxy` suffix for severe-deviation strategies

- **Status**: Accepted
- **Date**: 2026-04-16
- **Deciders**: Project maintainers

## Context

Some Phase 1 strategies deviate so severely from the referenced paper
that the price-derived proxy signal is fundamentally different from the
original. In these cases, using the canonical slug (e.g., `piotroski_fscore`)
would mislead researchers into thinking the strategy implements the paper's
methodology.

The first instances are:
- **Piotroski F-Score**: The paper's 9-point score is computed entirely
  from accounting data (profitability, leverage, operating efficiency).
  The Phase 1 proxy replaces all 9 signals with price-derived indicators
  (momentum, low-vol, trend). This is NOT the F-Score.
- **Altman Z-Score**: The paper's formula uses working capital, retained
  earnings, EBIT, market cap / book value of liabilities, and sales —
  all accounting data. The Phase 1 proxy uses drawdown, volatility, and
  trend signals. This is NOT the Z-Score.

Both strategies are still valuable as standalone price-based composites,
but they must not be confused with the academic originals.

## Decision

Strategies with severe deviations (signal class fundamentally different
from the paper) use a `_proxy` suffix on the slug:

- `piotroski_fscore_proxy` — Phase 1 price-based composite
- `altman_zscore_proxy` — Phase 1 price-based distress proxy
- Reserved: `piotroski_fscore` — Phase 4 with real accounting data
- Reserved: `altman_zscore` — Phase 4 with real accounting data

## Naming convention

| Deviation severity | Slug convention | Example |
|---|---|---|
| Mild (price proxy for yield/rate) | Canonical slug | `fx_carry_g10` |
| Moderate (momentum for carry) | Canonical slug + paper.md note | `equity_carry` |
| Severe (signal class change) | `_proxy` suffix | `piotroski_fscore_proxy` |

## Criteria for `_proxy` suffix

Apply the suffix when ALL of these are true:
1. The paper's signal uses a fundamentally different data source
   (accounting, options, order book) than the proxy (price-only)
2. The proxy cannot be justified as a known academic approximation
3. The correlation between proxy and true signal is expected to be low

## Consequences

1. Canonical slugs (`piotroski_fscore`, `altman_zscore`) are reserved
   for Phase 4 implementations with proper data feeds.
2. The `_proxy` convention may apply to future families (e.g.,
   alt-data strategies without alt-data, options strategies without
   options data).
3. `docs/deviations.md` explicitly flags `_proxy` strategies.
