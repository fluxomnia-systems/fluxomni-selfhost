# Installation

Installer contracts for full stacks and standalone media nodes.

## Media-node file limits

Both Compose templates set soft/hard `nofile` to 65,536. The installer fills missing limits in downloaded assets, including v26.3.2.

The installer saves downloaded YAML as `compose.release.yml` and includes it after `compose.defaults.yml` through `docker-compose.yml`. Compose 2.20+ merges defaults beneath explicit limits, including flow mappings and aliases, without rewriting templates. Keep these files together. Operator overrides still apply; `up -d` recreates changed containers while retaining mounted data.

## Effective limit verification

Before reporting success, the installer verifies at least 1,128 descriptors: 1,000 connections plus 128 reserved by SRS. Insufficient limits, including operator overrides, fail with recovery instructions.

## Compose version requirement

Compose 2.20+ is required for native includes. Older versions fail before deployment files are overwritten or containers are started.

## Installer regression coverage

Pytest runs the installer with local assets, real Compose rendering, and a simulated Docker lifecycle. No Docker daemon or network is required.

Tests cover both modes, block/flow/alias mappings, missing/existing limits, low-limit overrides, manual templates, and reruns preserving templates, bind mounts, settings, and data.

Run `uv run --no-project --with-requirements scripts/requirements-test.txt pytest -q tests`; Installer CI runs the same checks.
