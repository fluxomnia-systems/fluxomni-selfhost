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

## Publisher Port Configuration

Installations expose and advertise independent RTMP, HLS, SRT, WHIP signaling, and RTC media ports in both full-stack and standalone modes.

WHIP defaults to TCP 8003 and RTC media to UDP 8000. The RTC host mapping equals its SRS listener port; changing HLS never changes RTC. ICE candidates default to the public media-node host. Installer reruns preserve saved values unless explicit environment overrides are supplied, and firewall configuration runs after resolving those values.

## Publisher Port Regression Coverage

Installer tests verify default and customized publish port bindings, advertised ports, ICE candidates, rerun preservation, explicit override precedence, and firewall rules in both install modes.

The tests use local assets and simulated commands with real Compose rendering so no real deployment or firewall mutation is needed.

## Preparation installation configuration

Full and standalone installs support an opt-in preparation budget with explicit CPU, memory and thread limits, persisted per installation.

`FLUXOMNI_PREPARATION_CGROUP_ENABLED=1` requires all three positive integer budgets. Requests override saved values; absent overrides preserve them. Disabled budgets become comments so `env_file` never injects partial runtime options. Enable/disable requires installer regeneration of the include. Validation/provisioning failures restore only installer-managed files, never operator overrides or runtime data.

## Preparation host prerequisites

Preparation provisioning requires a local rootful Linux cgroup-v2 Docker daemon, systemd, Python 3 and already enabled host controllers.

Docker Desktop, remote contexts, rootless daemons and user namespace remapping fail before configuration changes. The helper never enables host-wide controllers. CPU, memory and pids limits remain exclusively owned by the runtime.

## Preparation group lifecycle

Each canonical install directory has a hash-named group, root-owned ownership marker, helper and boot unit, supporting safe reruns and reboot recreation.

Preflight requires executable `/usr/bin/python3`, matching the installed boot helper interpreter.

The marker binds schema, canonical directory and exact group path. A host lock serializes operations. Unmarked roots are refused. Busy runtime directory locks permit immutable read-only checks without enumerating changing attempts. Idle roots accept only UUID attempt leaves. Provisioning preserves all limits and descendants. The boot unit orders before Docker service/socket; disabling retains the group and saved budgets. Cleanup requires the runtime lock and validates every child before killing any.

## Preparation Compose enforcement

The effective rendered Compose must retain host UID 0, host cgroup namespace, complete budgets and one exact writable preparation bind without path creation.

Compose v2 omits false booleans from rendered JSON; an existing bind-options object with an omitted `create_host_path` means false. An absent bind-options object or explicit true is rejected.

Installer overrides that weaken these properties fail before container recreation. After startup, runtime-written CPU/memory/swap/thread limits, a positive enforcement signal from the current start and isolation warnings are checked before reporting success. Retained policy files cannot prove an older image supports isolation. Fleet's enforced state remains the operator confirmation of actual runtime attachment.

## Preparation installer regression coverage

Installer tests cover both targets, enable/update/disable/re-enable, persisted budgets, unsupported hosts, bad overrides, failed provisioning and runtime rejection.

The tests use real Compose rendering and simulated host mutation. Invalid budgets and pre-start failures retain the existing configuration and data. [[tests/test_install.py#test_preparation_enable_preserve_update_disable_reenable]] exercises the complete lifecycle.

## Preparation provisioning regression coverage

Provisioning tests verify ownership, root separation, live-owner reruns, reboot recreation, malformed roots and missing controllers without touching real host groups.

[[tests/test_preparation_cgroup.py#test_owned_rerun_and_reboot_recreation_preserve_runtime_limits]] verifies the ownership marker and unit ordering. Real Linux validation additionally exercises the helper on a dedicated disposable subtree and checks the generated unit with systemd tooling.
