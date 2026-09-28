# Installation

The self-host installer manages Compose assets and environment settings for full stacks and standalone media nodes. Runtime defaults must work independently of Docker daemon defaults.

## Media-node file limits

Both public Compose templates set soft and hard `nofile` limits to 65,536. The installer supplies missing file limits in downloaded release assets before starting containers, including assets pinned to v26.3.2.

Normalization follows the two-space service indentation of published templates and preserves explicit limits and separate operator override files. Compose applies configuration changes through `up -d`, recreating changed containers while retaining mounted data.

## Effective limit verification

After Compose starts containers, the installer checks the media-node process soft limit before announcing success. SRS requires at least 1,128 descriptors: 1,000 configured connections plus 128 reserved descriptors.

An operator override can lower the effective limit. The installer fails with remediation instructions rather than reporting success while SRS restarts. Tests exercise this failure in both installation modes.

## Installer regression coverage

Pytest runs the complete installer with local download fixtures and a simulated Docker lifecycle. The real Compose CLI renders configuration, so tests require Compose but do not use a Docker daemon or external network.

Coverage includes missing limits in pinned assets, unrelated existing limits, higher explicit limits, full and standalone services, reruns preserving environment and database contents, and custom Compose overrides. Public templates also carry limits for manual deployment.

Run `uv run --no-project --with-requirements scripts/requirements-test.txt pytest -q tests`. The Installer workflow runs these checks for relevant pull requests and main changes.
