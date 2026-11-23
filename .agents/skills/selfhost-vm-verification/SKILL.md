---
name: selfhost-vm-verification
description: Verify Fluxomni self-host installer and upgrade changes on a disposable Ubuntu VM. Use for real Docker acceptance of fresh installs, guarded maintenance, and Garage or HTTPS toggles.
---

# Self-host VM verification

## Isolate the run

- Record the commit and any local diff. Copy the candidate installer, helpers, and Compose assets together. Do not substitute released assets for changed files. Record the pinned image tags and actual digests separately.
- Prefer a disposable local Ubuntu cloud-image VM on QEMU/KVM. Check tooling, disk space and KVM access. Get approval before installing host packages or provisioning billable infrastructure. Attach the cloud-init seed ISO as a virtual CD-ROM.
- Use a per-VM SSH key, a dedicated known-hosts file, and SSH forwarding bound to loopback. Confirm the guest hostname before each mutating operation. Run Docker and the installer only in the guest, never on the host or an existing installation.
- If using a guest-only HTTP asset server, bind it to loopback. Report that testing the runtime directly does not verify the published launcher or CLI delegation. Do not bypass production release checks to claim a launcher pass.

## Run the matrix

1. Fresh full-stack install: confirm the control plane and media node are healthy, the node registers, the frontend answers an HTTP request, and the expected persistent mounts exist.
2. Guarded upgrade: keep the old stack running while disabling routes via the supported API if needed. Wait for zero reservations. Keep Watchtower stopped. Exercise the documented maintenance mode and check that the same database and credentials are retained without printing secrets.
3. Garage: start with Garage off. Enable it, verify health and the provisioning helper's checksummed S3 round-trip, then omit the option and check that Garage still works. Disable it and check the saved flag, rendered service list, stopped old container and reachable frontend. Preserve the bucket data and volumes.
4. HTTPS: enable it, make a certificate-verified request through Caddy, and repeat after an upgrade with the flag omitted. Then disable it; check that Caddy stopped, port 443 is free, the frontend answers on its previous bind, and the previous public URL and proxy settings were restored. Unset and empty environment values are not interchangeable.
5. For local TLS, use a guest-only hostname and Caddy's local CA. Make the copied public root certificate readable by the test user and verify with `curl --cacert` and `--resolve`, not `-k`. Report public ACME as untested unless actually verified on a reachable hostname.

## Capture evidence and clean up

- Run long checks as background jobs. Upload the test script first and then run it by path with installer stdin redirected from `/dev/null` for unattended steps. Otherwise a subprocess can consume commands streamed over SSH. Require a pass marker per checkpoint; a job exit code alone is insufficient.
- Use distinct container names and nonconflicting ports for multiple installs in one guest, or use separate guests. Stopped containers still reserve their names.
- On failure, capture Compose status and relevant service logs. Check one-shot services explicitly: a healthy Garage container does not prove the bucket provisioner ran, and a removed overlay does not prove its old container stopped. Never use broad orphan cleanup as a substitute for checking which containers the installer owns.
- Report what passed, what failed, and what was not exercised. Redact credentials and do not dump `.env` or rendered environment values. Shut down the disposable VM after collecting evidence; retain its disk only if needed for follow-up, and delete only the resources created by this run.
