# Troubleshooting

## Container Does Not Start

```bash
cd ~/fluxomni
docker compose logs -f control-plane media-node
```

Common causes:

- Docker daemon is not running.
- The selected image tag does not exist.
- `FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN` is missing from `.env` after a manual install.
- Port 80, 1935, 8000/tcp, 8000/udp, or 10080/udp is already in use.

## Check Running State

```bash
cd ~/fluxomni
docker compose ps
```

## Clean Restart

```bash
cd ~/fluxomni
docker compose down
docker compose up -d
```
