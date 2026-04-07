# CLAUDE.md

## Project Overview

FluxOmni Self-Hosted — public installer, Docker Compose configs, and mdBook documentation for running FluxOmni. This repo does **not** contain application source code. FluxOmni is a multi-platform streaming tool with a split `control-plane` + `media-node` runtime.

## Repository Structure

```
install.sh          # Main installer script (curl-pipe-bash)
docker-compose.yml  # Single-host compose: control-plane + media-node + watchtower
docker-compose.media-node.yml  # Standalone media-node compose
.env.example        # Reference env vars for the compose stack
docs/               # mdBook documentation site (published to GitHub Pages)
  book.toml         # mdBook config
  src/              # Markdown source files
scripts/            # Helper scripts (e.g. check-md-links.sh)
screenshots/        # Playwright project for capturing user-guide screenshots
workers/install/    # Cloudflare Worker that serves install.fluxomni.io
```

## Common Commands

Node.js is managed via **mise**. Prefix shell commands with `eval "$(mise activate bash)"` when running outside an interactive shell (e.g. from Claude Code Bash tool).

```bash
# Build docs
make build

# Serve docs locally (default port 3000)
make serve

# Lint docs (build + link check + markdownlint if available)
make lint

# Strict CI lint (requires markdownlint-cli2)
make lint.ci

# Clean generated docs
make clean

# Capture user-guide screenshots (needs running FluxOmni instance)
make screenshots
# With custom target and auth:
# FLUXOMNI_URL=https://example.com FLUXOMNI_ADMIN_PASSWORD=secret make screenshots
```

## Prerequisites

- **mise**: runtime manager — provides Node.js (and optionally Rust/mdbook). Activate with `eval "$(mise activate bash)"` or use the shell hook.
- **mdbook**: `cargo install mdbook` (CI uses v0.5.2)
- **markdownlint-cli2**: `npm install -g markdownlint-cli2` (required for `make lint.ci`)
- **Node.js 20+**: managed via mise; used for screenshots (Playwright) and markdownlint
- **ripgrep**: used by `scripts/check-md-links.sh`

## CI/CD

GitHub Actions workflow (`.github/workflows/docs.yml`):
- **On PR/push** (docs paths): runs `make docs.lint.ci`
- **On push to main**: builds and deploys to GitHub Pages

## Docs Guidelines

- Markdown files live in `docs/src/`
- Book structure defined in `docs/src/SUMMARY.md`
- Markdownlint config: `.markdownlint-cli2.yaml` (MD003, MD013, MD033, MD041, MD050 disabled)
- Always run `make lint` before submitting doc changes
- Screenshots go in `docs/src/images/user-guide/`; regenerate with `make screenshots`

## Docker Stack

Two compose files:
- `docker-compose.yml` — single-host (control-plane + media-node + watchtower)
- `docker-compose.media-node.yml` — standalone media-node only

Images from `ghcr.io/fluxomnia-systems/fluxomni-{control-plane,media-node}`.
Config is env-driven via `.env` (see `.env.example`). Never commit `.env`.

## Key Ports (defaults)

| Service       | Port  | Protocol |
|---------------|-------|----------|
| HTTP (UI/API) | 80    | TCP      |
| gRPC (CP)     | 50052 | TCP      |
| RTMP          | 1935  | TCP      |
| HLS           | 8000  | TCP+UDP  |
| SRT           | 10080 | UDP      |
| SRS Callback  | 8081  | TCP (localhost only) |
