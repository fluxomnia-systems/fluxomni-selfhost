# Capacity Ledger Upgrades

Use a maintenance window when moving to builds with durable route/output admission or restarting their media nodes.

These builds preserve capacity until the previous execution has proved it stopped. A container restart or a new heartbeat does not clear old ownership. Fleet **Drain node** prevents new placement but keeps existing execution; it does not release reservations.

The latest stable `v26.3.2` predates this contract. Select a tested build containing core PR #344, such as immutable `main-233a5d5`, and use the same tested build for the control plane, frontend and nodes. The installer rejects older candidates that cannot provide the admission API and initialization proof. Keep backups and record the enabled route IDs before maintenance.

## First Capacity Upgrade

Stop every external execution container before initializing the control-plane ledger.

1. On every standalone node host, stop its updater and node, and verify they have stopped:

   ```bash
   cd ~/fluxomni-media-node
   docker compose stop --timeout 30 watchtower media-node
   docker compose ps --all
   ```

   Include custom execution containers and other installations on those hosts. Pause deployment automation. Keep them stopped until the upgraded control plane has passed verification.

2. On the full-stack host, download the current installer and select the tested build:

   ```bash
   curl -fsSL https://install.fluxomni.io -o install.sh
   FLUXOMNI_VERSION=main-233a5d5 \
     bash install.sh full --capacity-upgrade initial --confirm-execution-stopped
   ```

   `--confirm-execution-stopped` asserts that every external predecessor execution container and updater is stopped. The installer controls its local node; it cannot inspect other hosts. For a custom directory, also provide `FLUXOMNI_DIR`.

3. The installer stops the local updater before downloading deployment assets or pulling images. It then stops local execution and controllers, starts the upgraded control plane alone with a temporary acknowledgement, verifies its authenticated admission API, stops it and verifies persisted ledger initialization. It recreates the control plane without that acknowledgement and verifies again before starting local media and the frontend. Watchtower stays stopped.

4. Update each already stopped standalone node only after the full-stack step succeeds:

   ```bash
   FLUXOMNI_VERSION=main-233a5d5 \
     bash install.sh media-node --capacity-upgrade node --confirm-control-plane-ready
   ```

   Here `--confirm-control-plane-ready` asserts that the global initial shutdown boundary and control-plane verification succeeded. New starting reservations are expected; they have no predecessor execution. Check Fleet registration, source/playback health and **Preparation enforced** when isolation is configured.

Never place `FLUXOMNI_CAPACITY_UPGRADE_STOPPED` in `.env` or pass it as an installer environment variable. The installer owns its temporary Compose-only use. Initial mode refuses a ledger that is already initialized, even if empty.

## Later Planned Upgrades

Release existing reservations while the old reporters are still alive.

1. Record enabled route IDs. Disable affected routes in the route workspace. For a full-stack upgrade, disable all routes in the cluster.
2. Wait for every affected node's Fleet capacity counts to reach zero: committed, starting and retiring routes and outputs. Keep old nodes and the control plane running until shutdown proofs arrive. An offline node or pending retiring count is not a completed drain.
3. Upgrade the full-stack installation:

   ```bash
   FLUXOMNI_VERSION=main-233a5d5 \
     bash install.sh full --capacity-upgrade drained
   ```

   The installer checks the persisted ledger, stops writers, checks disabled routes and zero reservations again, then stops execution. It uses no initialization acknowledgement. If demand appears before writers stop, it refuses to stop media and restarts only the old control plane so draining can continue.

4. Update standalone nodes using `--capacity-upgrade node --confirm-control-plane-ready`. For this path, the assertion means the remote control plane is ready and the affected node drained to zero reservations before it stopped.
5. Restore the recorded enabled routes and verify playback, outputs, Fleet counts and preparation enforcement. The installer does not automatically disable or restore routes.

Existing installations require an explicit maintenance mode on installer reruns, including budget/configuration changes that recreate nodes. Fresh installs retain `bash install.sh full` or `media-node`.

## Failure and Retry

Keep runtime data and diagnose the candidate before restarting execution.

Before initialization is verified, failure leaves media and automatic updates stopped and stops the temporary acknowledged control plane. If Docker cannot confirm that stop, stop it manually before retry. The installer retains the selected configuration and database; it does not restore predecessor state after a candidate may have written SQLite. Read candidate logs locally and correct image/configuration problems.

If the persisted ledger is still uninitialized, repeat initial mode after verifying external containers remain stopped. If initialization completed, use the initialized procedure instead: recreate only the selected control plane without the acknowledgement, keeping media and automatic updates stopped:

```bash
cd ~/fluxomni
docker compose up -d --no-deps --force-recreate control-plane
```

Verify its admission API, disable routes and wait for reservations to clear. Never erase the ledger or reuse the acknowledgement to release exposed ownership. Missing shutdown proof can retain reservations indefinitely and needs separate recovery work.

Failure during the final node/readiness checks may leave verified candidate services running. Inspect them and continue the drain/diagnostic procedure; do not automatically roll back their database or start predecessor images.

## Supported Storage and Automation

The automated full-stack flow requires local Docker, Python 3, one identifiable local SQLite bind, and the default Compose bundle with optional `docker-compose.override.yml` customization.

The helper reads SQLite with WAL participation and checks rendered storage against the actual control-plane container. Changed storage roots, custom commands/entrypoints, overlapping mounts, named volumes, symlink paths, remote Docker and active Compose profiles require a separately reviewed manual procedure. The helper never modifies SQLite directly.

Keep the `auto-update` profile disabled for capacity-ledger builds. Uncoordinated Watchtower updates cannot perform the required drain and cluster shutdown sequence. Manual/custom rollouts must implement the same boundaries and verify the active control plane has no acknowledgement before starting nodes.
