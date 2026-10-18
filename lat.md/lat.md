# Self-host deployment

Internal contracts for the public installer and deployment assets. Operator instructions live in `docs/src/`.

- [[installation]] — Container limits, installation behavior, and regression checks.

## Documentation language

Write public docs in simple English with short sentences, common words, and no idioms. Keep technical meaning, UI labels, commands, links, and release facts unchanged.

Apply this style to the repository README and the mdBook guides in `docs/src/`. Explain technical terms when needed. Prefer direct instructions over abstract interface or marketing terms. Keep headings stable so existing links still work.

Run `make lint.ci` after editing public docs. It builds the book, checks local Markdown links, and checks Markdown style.
