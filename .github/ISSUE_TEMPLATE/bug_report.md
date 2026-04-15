---
name: Bug report
about: Report a bug or unexpected behaviour in AlphaKit
title: "[bug] <package>: <short description>"
labels: ["bug", "needs-triage"]
assignees: []
---

## Package affected

<!-- Which AlphaKit package does this bug live in? Tick all that apply.

- [ ] alphakit-core
- [ ] alphakit-bridges
- [ ] alphakit-data
- [ ] alphakit-strategies-trend
- [ ] alphakit-strategies-meanrev
- [ ] alphakit-strategies-carry
- [ ] alphakit-strategies-value
- [ ] alphakit-strategies-volatility
- [ ] alphakit-strategies-options
- [ ] alphakit-strategies-rates
- [ ] alphakit-strategies-commodity
- [ ] alphakit-strategies-macro
- [ ] alphakit-strategies-ml
- [ ] alphakit-strategies-rl
- [ ] other (please specify below)
-->

## Environment

- **AlphaKit version:** <!-- output of: python -c "import alphakit; print(alphakit.__version__)" -->
- **Python version:** <!-- output of: python --version -->
- **OS and architecture:** <!-- e.g. Ubuntu 22.04 x86_64, macOS 14.4 arm64 -->
- **Installed extras:** <!-- e.g. dev, vectorbt, backtrader -->
- **Install method:** <!-- uv sync / pip install / editable clone -->

## Minimal reproduction

<!-- Please provide the smallest possible script that reproduces the
bug. A failing ~20-line example is far more actionable than a 2000-line
notebook. Use synthetic data where possible so maintainers can run it
without your private data feed. -->

```python
# paste minimal repro here
```

## Expected behaviour

<!-- What did you expect to happen? -->

## Actual behaviour

<!-- What actually happened? Include the full traceback if any. -->

```
# paste traceback here
```

## Have you checked the known failure modes?

<!-- Every AlphaKit strategy documents its known failure regimes in
`known_failures.md`. If this bug might be one of those regimes rather
than a code bug, please say so — it's still worth reporting but will
get a different triage. -->

- [ ] Yes, and this is not a documented failure mode
- [ ] Not applicable (core / bridge / data bug)

## Anything else?

<!-- Screenshots, profiler output, benchmark regressions, anything you
think is relevant. -->
