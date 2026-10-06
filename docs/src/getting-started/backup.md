# Backup & Restore

Back up runtime data and configuration, and preserve capacity ownership when stopping or moving an installation.

## What to back up

Keep `data/state.db`, `.env` and cached playlist files in `data/videos/`. Include configured external data binds. SQLite may also create `state.db-wal` and `state.db-shm`; retain them beside the database for live filesystem snapshots.

DVR recordings in `data/dvr/` are optional backup data. Generated `data/srs-http/` media can be recreated.

## Create a backup

For capacity-ledger builds, record enabled route IDs, disable all routes and wait for every node's committed, starting and retiring counts to reach zero while old reporters are alive. Follow [Capacity Ledger Upgrades](capacity-upgrades.md) before stopping execution.

Then stop the full-stack installation, retaining its containers for storage verification:

```bash
cd ~/fluxomni
docker compose --profile auto-update stop --timeout 30
tar czf ~/fluxomni-backup-$(date +%Y%m%d).tar.gz data/ .env
```

Restart the same tested build with the drained installer mode from the upgrade guide. Verify Fleet and playback, then restore the recorded enabled routes. Keep automatic updates stopped.

For a live SQLite backup, use SQLite's backup command instead of copying only `state.db`:

```bash
cd ~/fluxomni
sqlite3 data/state.db ".backup '$HOME/fluxomni-state-backup.db'"
cp .env ~/fluxomni-env-backup
```

A live backup can contain exposed reservations. It is evidence and backup data; restoring it does not release ownership or prove predecessor execution stopped.

## Restore from backup

Restore matching database, files, configuration and images through a separately reviewed recovery procedure. Stop all predecessor execution and deployment automation before restoring. Preserve the original backup and current runtime data until recovery is verified.

Do not delete the capacity ledger, reset initialized state, or use the initial acknowledgement to discard reservations from a restored initialized database. Missing shutdown proof can keep ownership reserved and requires separate recovery work. The installer does not automate data rollback.

## Migrate between hosts

Drain the source cluster while reporters are alive, take a stopped backup, and keep source execution stopped throughout migration. Transfer the matching data and configuration, preserve node identities deliberately, and update public hostnames and shared video paths before startup.

Changed storage roots or a different host require a separately reviewed manual procedure. Verify the initialized ledger, acknowledgement absence and Fleet registration before enabling the recorded routes. Never run source and destination against copied ownership concurrently.

## Rotate the auth token

Drain all routes with the old credentials still valid, following [Capacity Ledger Upgrades](capacity-upgrades.md). Stop execution and automatic updates on every host, then stop the control plane.

Generate a new token with `openssl rand -hex 24` and update `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` in `.env` on the full-stack and every standalone-node host. Restart the full stack with drained mode, then update standalone nodes with `--capacity-upgrade node --confirm-control-plane-ready`. Verify registration before restoring enabled routes.

All services must use the same token. A mismatch prevents node registration and shutdown reporting.
