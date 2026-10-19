# Backup & Restore

Back up runtime data and configuration, and preserve capacity ownership when stopping or moving an installation.

## What to back up

Keep `data/state.db`, `.env` and cached playlist files in `data/videos/`. Include configured external data binds. SQLite may also create `state.db-wal` and `state.db-shm`; retain them beside the database for live filesystem snapshots.

Also save standalone `node-secrets/` and the full installation's `control-secrets` and `local-node-secrets` Docker volumes. The data archive below does not include Docker volumes; back them up separately before restart.

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

## Preserve machine identities

Back up the full installation's `control-secrets` and `local-node-secrets` Docker volumes along with its database, files and configuration. Standalone nodes keep their credential, identity and trust files under `node-secrets/`. Protect these backups as secrets.

Restore the matching node credential and control-plane hash authority together. Enrollment cannot replace an existing node's credential. Do not delete identity files to force new enrollment or bypass reserved execution ownership.

## Rotate internal HTTP artifact access

`FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` is separate from machine admission. A full installation creates it for internal HTTP artifact access; standalone enrollment does not copy it into the node's `.env`.

Coordinate changes through the capacity maintenance procedure and verify artifact access after current control sessions reconnect. Machine credential rotation and recovery after permanent credential loss require a separate reviewed procedure.
