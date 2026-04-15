---
name: New strategy proposal
about: Propose a new paper-cited strategy to add to AlphaKit
title: "[strategy] <family>/<slug>: <short description>"
labels: ["strategy", "needs-triage"]
assignees: []
---

<!--
Thank you for proposing a new strategy!

Please fill out every field. AlphaKit does not accept strategies
without paper citations and expected-metric ranges — see CONTRIBUTING.md
for the non-negotiable rules.
-->

## Strategy name (slug)

<!-- e.g. `xs_momentum_jt`, `merger_arb_cash`, `vol_carry_vrp` -->

## Family

<!-- trend | meanrev | carry | value | volatility | options | rates |
commodity | macro | ml | rl | event_driven | microstructure | altdata |
crypto_native | behavioral | factor | portfolio | execution | risk | quality -->

## Paper citation

- **Title:**
- **Authors:**
- **Venue (journal / conference / book):**
- **Year:**
- **DOI or arXiv link:**

## Asset classes

<!-- Which of AlphaKit's 14 asset classes does this strategy apply to?
Check all that apply.

- [ ] equity
- [ ] future
- [ ] option
- [ ] bond
- [ ] rates
- [ ] fx
- [ ] commodity
- [ ] crypto
- [ ] index
- [ ] etf
- [ ] credit
- [ ] volatility
- [ ] structured
- [ ] alternative
-->

## Key parameters (from the paper)

| Parameter | Paper value | Notes |
|---|---|---|
|  |  |  |

## Rebalance frequency

<!-- daily | weekly | monthly | quarterly | event-driven | intraday -->

## Expected metrics (from paper or known replications)

- **Sharpe range:**
- **Max drawdown:**
- **Annualised return:**
- **Annualised vol:**
- **Turnover (annual):**

## Known failure regimes

<!-- What regimes is this strategy known to underperform in? Please
cite evidence where you can — published CTA index years, academic
follow-ups, practitioner write-ups. -->

## Data requirements

<!-- What data does this strategy need? (daily OHLCV, tick data,
fundamentals, options chains, alt data, ...) Which existing AlphaKit
adapter can provide it, or will a new adapter be needed? -->

## Known replications

<!-- Any public replications, open-source implementations, or
follow-up papers we should be aware of? -->

## Implementation complexity

- [ ] Simple — pure NumPy/pandas from daily prices
- [ ] Medium — needs fundamentals, options chain, or calendar logic
- [ ] Complex — needs tick data, custom execution model, or ML pipeline

## Willing to implement?

- [ ] Yes, I will open a PR
- [ ] No, I'm proposing this for someone else to pick up
