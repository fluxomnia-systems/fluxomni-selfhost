# Self-host deployment

Internal contracts for the public installer and deployment assets. Operator instructions live in `docs/src/`.

- [[installation]] — Container limits, installation behavior, and regression checks.

## Documentation language

Write public docs in simple English with short sentences, common words, and no idioms. Keep technical meaning, UI labels, commands, links, and release facts unchanged.

Apply this style to the repository README and the mdBook guides in `docs/src/`. Explain technical terms when needed. Prefer direct instructions over abstract interface or marketing terms. Keep headings stable so existing links still work.

Run `make lint.ci` after editing public docs. It builds the book, checks local Markdown links, and checks Markdown style.

## Capacity planning

The public sizing guide presents a measured relay workload and explicit planning extrapolations, with matching examples in the operator scenarios.

[[docs/src/getting-started/sizing.md|The sizing guide]] shows the one-hour four-route, 48-output measurement beside 2×, 4×, and 8× estimates. The estimates scale media-container budgets, active routes, outputs, and payload under stated workload and CPU assumptions. Whole-host overhead and physical network limits remain separate.

[[docs/src/scenarios/multistream-agency.md|The agency scenario]] applies the same budgets to client routes. [[docs/src/scenarios/power-creator.md|The creator scenario]] calculates outgoing payload from bitrate and destinations. [[docs/src/scenarios/distributed-fleet.md|The fleet scenario]] marks its combined-node example as an estimate.
