# Installation

Installer contracts for full stacks and standalone media nodes.

## One-time node enrollment

Fleet issues a fifteen-minute code for one fresh node. The installer saves its random machine credential before exchanging the code and credential hash over verified HTTPS.

Owner-only `node-secrets/` contains the credential, public CA files, bound identity and enrollment receipt. The directory is mounted read-only into the node. Codes and plaintext credentials never enter `.env` or diagnostic output. Ambiguous responses are confirmed through this boot's outbound Hello/Welcome. Interrupted installs can retry admission with the saved credential without another code. A saved receipt skips redemption on later starts.

The node opens its outbound TLS Hello/Welcome connection after redemption. Private nodes publish no ports. Public ingest/playback and HTTP media relay settings each enable only their own media ports. A full installation bootstraps its colocated node through the same credential authority before the control plane starts.

## Enrollment recovery coverage

Installer tests verify owner-only credential storage, exact retries after response loss, reuse without a new code, bound identity, HTTPS trust and optional public media ports.

The simulated redemption endpoint records only node IDs and credential hashes. Real Docker acceptance uses the current control-plane redemption service and existing outbound admission.

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

## Capacity maintenance selection

Existing installations require an explicit initial, drained or standalone-node maintenance mode; fresh installation entry points remain unchanged.

The initial mode is full-stack only and requires an external-execution-stopped assertion. Standalone updates assert that the upgraded control plane has verified the initial boundary, or the node drained before stopping. Raw acknowledgement environment/Compose overrides are rejected. See the public capacity upgrade guide for operator ordering.

## Capacity ledger evidence

The helper reads the actual control-plane bind-mounted SQLite through a WAL-aware read-only transaction and verifies its current assignment marker and persisted route state.

[[scripts/capacity-upgrade.py#read_ledger]] never edits SQLite. Initialized ledgers always reject initial mode. Drained mode requires disabled routes and no capacity reservations. Storage resolution compares candidate Compose and actual owner mounts; custom commands, ambiguous mounts, symlinks and remote Docker fail closed.

The runtime serializer omits `capacity_reservations` when empty, even with `capacity_initialized: true`. The helper follows that persisted schema: an omitted field means empty; a present malformed value or any retained claim is rejected.

## Capacity upgrade service ordering

Maintenance stops local automatic updates before replacing assets or pulling candidates. Full-stack upgrades verify control-plane initialization before restarting execution.

[[scripts/capacity-upgrade.py#maintenance]] freezes writers and rechecks later drains before stopping nodes. Initial mode starts only the control plane with a private temporary Compose acknowledgement, verifies authenticated admission API readiness and persisted initialization, then recreates and verifies without acknowledgement. Watchtower stays stopped, including containers from an inactive profile. Failure stops the temporary acknowledged control plane and retains data and selected assets; no predecessor rollback occurs after state may have changed.

## Capacity marker classification tests

Initial upgrades accept legacy missing markers and reject initialized ledgers regardless of demand, without modifying SQLite.

The tests also read uncheckpointed WAL changes and reject malformed ledger evidence.

## Capacity drain proof tests

Later upgrades reject uninitialized state, reserved claims and enabled routes instead of treating desired absence or liveness as shutdown proof.

## Capacity empty ledger serialization tests

Initialized empty snapshots omit the reservation field under the runtime serialization contract; committed WAL evidence still accepts drained mode and rejects initial mode.

## Capacity storage binding tests

Maintenance refuses custom app-root commands, unsupported database knobs, named volumes, shadowed binds and symlinked storage.

## Capacity initialization ordering tests

Initial cutover proves API readiness and durable initialization and removes the active acknowledgement before starting media.

## Capacity initialization failure tests

An unavailable candidate API, wrong candidate storage or missing durable marker never restarts execution or rewinds the database. The temporary acknowledged control plane is stopped before returning.

## Capacity frozen drain tests

Demand arriving before writers stop refuses node shutdown and restores only the old control plane so withdrawal proofs can continue.

## Capacity maintenance selection tests

Existing installer runs and initial cutovers fail before service mutation when maintenance selection or the external shutdown assertion is missing.

## Capacity raw acknowledgement tests

An ambient or persisted runtime acknowledgement cannot bypass the explicit maintenance flow or mutate installation state.

## Capacity real Compose upgrade tests

Real Compose-rendered initial upgrades remove temporary acknowledgement inputs, retain the selected database, keep Watchtower stopped and support later drained restart.


## Incomplete fresh installation retries

An installer-owned version/target marker permits retrying an incomplete bootstrap only with absent project containers and empty rendered runtime storage, without WAL or SHM sidecars.

[[scripts/capacity-upgrade.py#fresh_preflight]] never treats the marker as shutdown proof or resets state. Runtime evidence requires explicit maintenance or manual recovery. The marker participates in configuration rollback and is removed only after complete readiness, including successful explicit maintenance.

## Incomplete fresh installation retry tests

Failed pulls and startup attempts before resource creation can retry; mismatched markers and runtime or durable-state evidence cannot bypass maintenance.

## Independent HTTP relay selection

An empty HTTP relay host stays empty even when public ingest is configured. The installer preserves that choice in the saved environment and does not publish port 8004 on retries.

Legacy shared-token nodes use fresh enrollment after capacity maintenance; no shared-token import or old control protocol is preserved.

## HTTPS control preflight defaults

The connectivity preflight uses port 443 for HTTPS endpoints without an explicit port, including bracketed IPv6 hosts. Explicit endpoint ports stay unchanged.

## Public release selection

The public launcher selects installer code and Compose assets from one release before changing installation files.

Explicit version values override the saved installation version; otherwise the default is latest. Latest resolves to the generated stable ref while retaining the latest image channel. Historical releases declare their root installer in release metadata. New releases and edge use scripts/install-runtime.sh. Missing files fail without falling back to main. Stable historical code owns its release's admission and update contract; the new runtime adds no legacy protocol adapter.

Current stable v26.3.2 uses bundle f4a0b3b0c72da80dd889ef4a51f637537dd89406. Its installer and all helper/assets downloads share that SHA, retaining the file-limit, media-port and preparation fixes without requiring the newer capacity API. The image channel stays latest or the requested version. The manual installation example uses the same corrected asset SHA with the v26.3.2 image pin.

Release sync preserves declared historical installer paths and same-release bundle overrides and assigns the current path to new releases. Custom asset roots require the current runtime installer. Caller working directories never supply executable version maps. Enrollment commands cannot be sent to historical installers.

## Public release selection tests

Launcher tests verify stable and edge selection, saved versions, explicit overrides, argument and exit propagation, missing-bundle safety and generated release paths.

Real release acceptance additionally runs downloaded stable installers with their published Compose bundles using a simulated Docker lifecycle and real Compose rendering. Matching-runtime Docker acceptance verifies the new enrollment protocol separately.

## Versioned public installer URLs

The install proxy serves the release-aware launcher for versioned URLs and passes the URL version explicitly to prevent latest-channel drift.

The launcher then resolves the same corrected stable bundle used by environment pins. Historical alias fallback passes the core image tag as well as the core asset ref to installers that predate public tag normalization. Proxy responses stream the launcher after the version prefix; missing upstream launchers fail without a moving-version fallback.

## Public proxy pin tests

Worker tests execute returned scripts to verify URL pins, corrected-bundle launcher selection, unchanged default dispatch and failure responses.
