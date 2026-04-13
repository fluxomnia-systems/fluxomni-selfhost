# Backup & Restore

FluxOmni stores all persistent state in the `data/` directory inside
your install path (default `~/fluxomni`). Backing up this directory
preserves your entire configuration: routes, settings, user accounts,
and cached playlist files.

## What to back up

| Path | Contents | Priority |
| ---- | -------- | -------- |
| `data/state.db` | Embedded SQLite state for routes, settings, and user accounts | Critical |
| `data/videos/` | Cached playlist files | Recommended |
| `.env` | Environment variables and auth token | Critical |

While the stack is running, SQLite may also create `data/state.db-wal`
and `data/state.db-shm`. Keep those files beside `state.db` whenever
you take live filesystem snapshots.

The `data/dvr/` and `data/srs-http/` directories contain transient
media data and can be regenerated. Back them up only if you need to
preserve DVR recordings.

## Create a backup

Stop the stack first to ensure a consistent snapshot:

```bash
cd ~/fluxomni
docker compose down
tar czf ~/fluxomni-backup-$(date +%Y%m%d).tar.gz data/ .env
docker compose up -d
```

If you need a live SQLite backup and have `sqlite3` available on the
host, use SQLite's backup command instead of copying only `state.db`
with `cp`:

```bash
cd ~/fluxomni
sqlite3 data/state.db ".backup '$HOME/fluxomni-state-backup.db'"
cp .env ~/fluxomni-env-backup
```

If `sqlite3` is not available, prefer the stopped-stack backup above or
a storage-level snapshot of the full `data/` directory.

## Restore from backup

To restore on the same or a new host:

```bash
cd ~/fluxomni
docker compose down
tar xzf ~/fluxomni-backup-20260408.tar.gz
docker compose up -d
```

If restoring to a different server, update `FLUXOMNI_PUBLIC_HOST` and
`FLUXOMNI_MEDIA_NODE_PUBLIC_HOST` in `.env` to reflect the new
hostname or IP before starting the stack.

## Migrate between hosts

1. Back up the `data/` directory and `.env` on the source host.
2. Run the installer on the destination host (or set up the compose
   stack manually).
3. Stop the stack on the destination host.
4. Copy `data/` and `.env` from the source to the destination install
   directory.
5. Update hostnames in `.env` if the public address has changed.
6. Start the stack on the destination host.

```bash
# On source
cd ~/fluxomni && tar czf /tmp/fluxomni-migrate.tar.gz data/ .env

# Transfer to destination
scp /tmp/fluxomni-migrate.tar.gz user@new-host:/tmp/

# On destination
cd ~/fluxomni
docker compose down
tar xzf /tmp/fluxomni-migrate.tar.gz
# Edit .env if hostname changed
docker compose up -d
```

## Rotate the auth token

If you need to rotate `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN`:

1. Generate a new token: `openssl rand -hex 24`
2. Update the token in `.env` on the control-plane host.
3. Update the same token in `.env` on every standalone media-node host.
4. Restart all services:

```bash
# On each host
docker compose down && docker compose up -d
```

All services must use the same token value. A mismatch causes media
nodes to fail registration.
