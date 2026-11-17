# Object Storage (Garage)

Fluxomni can store durable artifacts in S3-compatible object storage instead of only on the local disk. Self-hosted full installs use [Garage](https://garagehq.deuxfleurs.fr/), a small single-node object store, behind a Compose overlay.

Object storage is enabled by default on full (single-host) installs. To disable it, set `FLUXOMNI_OBJECT_STORAGE_ENABLED=0` in `.env` and rerun `install.sh full`. Standalone media-node installs never include it.

When enabled, the installer:

1. Downloads `docker-compose.object-storage.yml` and includes it in the Compose stack.
2. Generates `object-storage/config.toml` and `object-storage/credentials.env` with `0600` permissions. The credentials are a dedicated Garage access key; they are written to `.env` like the internal auth token and are never printed in logs.
3. Starts `garage` and a one-shot `garage-init` container that provisions the bucket.

## Security properties

- **Isolated credentials**: the control plane receives only the generated access key. The Garage admin token stays in `object-storage/config.toml`, readable only by the provisioner.
- **Bounded uploads**: the key is allowed read and write on exactly one bucket (`FLUXOMNI_OBJECT_STORAGE_BUCKET`, default `fluxomni-artifacts`). It cannot create buckets and is not a bucket owner. The bucket has a size and object quota (`FLUXOMNI_OBJECT_STORAGE_QUOTA_SIZE`, default 10 GiB; `FLUXOMNI_OBJECT_STORAGE_QUOTA_OBJECTS`, default 100000).
- **No public buckets**: no bucket alias or website is ever created; anonymous requests are rejected.
- **Private endpoints**: the S3 and admin APIs publish on `127.0.0.1` only (`FLUXOMNI_OBJECT_STORAGE_API_PORT`, `FLUXOMNI_GARAGE_ADMIN_PORT`). The control plane reaches Garage over the private Compose network at `http://garage:3900`. Never bind these ports to `0.0.0.0`.
- **Verified checksums**: provisioning writes a probe object, reads it back, and compares SHA-256 checksums before reporting success. Garage also verifies block checksums internally on every write.
- **Pinned image**: Garage runs from `dxflrs/garage:v2.5.0` pinned by digest.

## Manual setup

Without the installer, in the installation directory:

```bash
python3 scripts/object-storage.py init --dir .
# add docker-compose.object-storage.yml to COMPOSE_FILE, set the
# FLUXOMNI_OBJECT_STORAGE_* variables from the generated credentials, then:
docker compose up -d
```

## Operating

- Data lives in `FLUXOMNI_OBJECT_STORAGE_DATA_DIR` (default `./data/garage`). Back it up with your regular data backup; see [Backup & Restore](backup.md).
- The control plane fetches artifacts with short-lived presigned URLs; no public URL is ever generated.
- To inspect the bucket: `docker exec fluxomni-garage /garage bucket info fluxomni-artifacts`.
