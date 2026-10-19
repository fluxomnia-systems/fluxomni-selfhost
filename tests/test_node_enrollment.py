"""One-command node provisioning through the public installer entry point."""

import base64
import hashlib
import json
import subprocess

from test_install import installation  # noqa: F401


# @lat: [[installation#Enrollment recovery coverage]]
def test_private_enrollment_saves_secret_and_reuses_it_without_another_code(installation):
    assets, destination, run = installation
    result = run("media-node", {"FLUXOMNI_MEDIA_NODE_PUBLIC_HOST": "", "FLUXOMNI_MEDIA_NODE_HTTP_HOST": ""})
    assert result.returncode == 0, result.stdout + result.stderr
    secret = (destination / "node-secrets/credential").read_bytes()
    assert len(secret.strip()) == 64
    assert (destination / "node-secrets").stat().st_mode & 0o077 == 0
    assert (destination / "node-secrets/credential").stat().st_mode & 0o077 == 0
    env = (destination / ".env").read_text()
    assert secret.decode().strip() not in env + result.stdout + result.stderr
    assert "FLUXOMNI_ENROLLMENT_CODE" not in env
    assert "FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" not in env
    config = json.loads((destination / "started.json").read_text())["services"]["media-node"]
    assert not config.get("ports")
    assert any(volume["target"] == "/run/fluxomni-node" and volume["read_only"] for volume in config["volumes"])
    retry = run("media-node", {"FLUXOMNI_MEDIA_NODE_PUBLIC_HOST": "", "FLUXOMNI_ENROLLMENT_CODE": "", "FLUXOMNI_ENROLLMENT_URL": ""})
    assert retry.returncode == 0, retry.stdout + retry.stderr
    assert (destination / "node-secrets/credential").read_bytes() == secret
    requests = (assets.parent / "enrollment.jsonl").read_text().splitlines()
    assert len(requests) == 1
    request = json.loads(requests[0])
    assert request["credentialHash"] == hashlib.sha256(secret.strip()).hexdigest()
    assert request["nodeId"] == "test-node"
    assert "--insecure" not in request["tls"]
    assert request["tls"][request["tls"].index("--proto") + 1] == "=https"


def test_lost_response_reuses_the_saved_credential_and_repeats_only_its_hash(installation):
    assets, destination, run = installation
    failed = run("media-node", {"TEST_ENROLLMENT_LOST_RESPONSE": "1"})
    assert failed.returncode == 0, failed.stdout + failed.stderr
    secret = (destination / "node-secrets/credential").read_bytes()
    assert (destination / "node-secrets/enrolled").exists()
    (destination / "node-secrets/enrolled").unlink()
    retry = run("media-node", {"FLUXOMNI_ENROLLMENT_CODE": "", "FLUXOMNI_ENROLLMENT_URL": ""})
    assert retry.returncode == 0, retry.stdout + retry.stderr
    assert (destination / "node-secrets/credential").read_bytes() == secret
    requests = [json.loads(line) for line in (assets.parent / "enrollment.jsonl").read_text().splitlines()]
    assert len(requests) == 1
    assert requests[0]["credentialHash"] == hashlib.sha256(secret.strip()).hexdigest()


def test_rejected_code_keeps_identity_for_a_new_code(installation):
    _, destination, run = installation
    failed = run("media-node", {"TEST_ENROLLMENT_FAIL": "1"})
    assert failed.returncode != 0
    secret = (destination / "node-secrets/credential").read_bytes()
    retried = run("media-node", {"FLUXOMNI_ENROLLMENT_CODE": "fresh-code"})
    assert retried.returncode == 0, retried.stdout + retried.stderr
    assert (destination / "node-secrets/credential").read_bytes() == secret


def test_existing_identity_rejects_another_node(installation):
    assets, destination, run = installation
    assert run("media-node").returncode == 0
    secret = (destination / "node-secrets/credential").read_bytes()
    changed = run("media-node", {"FLUXOMNI_MEDIA_NODE_ID": "another-node"})
    assert changed.returncode != 0
    assert (destination / "node-secrets/credential").read_bytes() == secret
    assert len((assets.parent / "enrollment.jsonl").read_text().splitlines()) == 1


def test_plain_http_cannot_receive_the_enrollment_code(installation):
    assets, _, run = installation
    failed = run("media-node", {"FLUXOMNI_ENROLLMENT_URL": "http://control.invalid/enroll"})
    assert failed.returncode != 0
    assert not (assets.parent / "enrollment.jsonl").exists()


def test_public_ca_is_saved_and_used_for_verified_redemption(installation, tmp_path):
    assets, destination, run = installation
    certificate = tmp_path / "ca.crt"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1", "-subj", "/CN=Installer test", "-keyout", str(tmp_path / "ca.key"), "-out", str(certificate)], check=True, capture_output=True)
    encoded = base64.b64encode(certificate.read_bytes()).decode()
    result = run("media-node", {"FLUXOMNI_ENROLLMENT_TLS_CA_PEM_BASE64": encoded, "FLUXOMNI_CONTROL_TLS_CA_PEM_BASE64": encoded})
    assert result.returncode == 0, result.stdout + result.stderr
    assert (destination / "node-secrets/ca.crt").read_bytes() == certificate.read_bytes()
    request = json.loads((assets.parent / "enrollment.jsonl").read_text().splitlines()[0])
    assert "--cacert" in request["tls"]
    assert "FLUXOMNI_CONTROL_TLS_CA=/run/fluxomni-node/ca.crt" in (destination / ".env").read_text()


def test_http_relay_opens_only_its_media_port(installation):
    _, destination, run = installation
    result = run("media-node", {"FLUXOMNI_MEDIA_NODE_PUBLIC_HOST": "", "FLUXOMNI_MEDIA_NODE_HTTP_HOST": "node.internal"})
    assert result.returncode == 0, result.stdout + result.stderr
    node = json.loads((destination / "started.json").read_text())["services"]["media-node"]
    assert [(port["target"], port["published"]) for port in node["ports"]] == [(8004, "8004")]


def test_missing_committed_credential_requires_backup_restore(installation):
    _, destination, run = installation
    assert run("media-node").returncode == 0
    (destination / "node-secrets/credential").unlink()
    failed = run("media-node")
    assert failed.returncode != 0
    assert not (destination / "node-secrets/credential").exists()


def test_invalid_ca_does_not_bind_an_unprovisioned_identity(installation):
    _, destination, run = installation
    failed = run("media-node", {"FLUXOMNI_MEDIA_NODE_ID": "wrong-node", "FLUXOMNI_CONTROL_TLS_CA_PEM_BASE64": "invalid"})
    assert failed.returncode != 0
    assert not (destination / "node-secrets/identity").exists()
    assert not (destination / "node-secrets/credential").exists()
    assert run("media-node").returncode == 0


def test_public_ingest_can_disable_the_http_relay_and_keep_it_disabled_on_retry(installation):
    _, destination, run = installation
    result = run("media-node", {"FLUXOMNI_MEDIA_NODE_PUBLIC_HOST": "media.example.com", "FLUXOMNI_MEDIA_NODE_HTTP_HOST": ""})
    assert result.returncode == 0, result.stdout + result.stderr
    first = json.loads((destination / "started.json").read_text())["services"]["media-node"]
    assert 1935 in {port["target"] for port in first["ports"]}
    assert 8004 not in {port["target"] for port in first["ports"]}
    assert first["environment"]["FLUXOMNI_MEDIA_NODE_HTTP_HOST"] == ""
    retry = run("media-node", {"FLUXOMNI_ENROLLMENT_CODE": "", "FLUXOMNI_ENROLLMENT_URL": ""})
    assert retry.returncode == 0, retry.stdout + retry.stderr
    second = json.loads((destination / "started.json").read_text())["services"]["media-node"]
    assert 8004 not in {port["target"] for port in second["ports"]}
