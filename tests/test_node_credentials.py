"""Candidate-secret durability and exact replacement retries."""
import fcntl
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
from test_install import installation  # noqa: F401

SPEC = importlib.util.spec_from_file_location("node_credentials", Path(__file__).parents[1] / "scripts/node-credentials.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)
OLD = "a" * 64


@pytest.fixture
def identity(tmp_path, monkeypatch):
    directory = tmp_path / "node-secrets"
    directory.mkdir(mode=0o700)
    (directory / "credential").write_text(OLD + "\n")
    (directory / "identity").write_text("node\nhttps://control.invalid:50052\n")
    monkeypatch.setenv("FLUXOMNI_CREDENTIAL_CODE", "grant.code")
    monkeypatch.setenv("FLUXOMNI_CREDENTIAL_URL", "https://control.invalid/api/node-credentials/redeem")
    return tmp_path, directory


# @lat: [[installation#Credential retry coverage]]
def test_lost_response_retains_candidate_and_retries_same_hash(identity, monkeypatch):
    root, directory = identity
    requests = []

    def post(args, **kwargs):
        payload = json.loads(kwargs["input"])
        requests.append(payload)
        assert payload["credentialHash"] == hashlib.sha256((directory / "credential.next").read_bytes().strip()).hexdigest()
        assert payload["currentCredential"] == OLD
        assert OLD not in " ".join(args)
        assert "--insecure" not in args
        return subprocess.CompletedProcess(args, 28 if len(requests) == 1 else 0, "" if len(requests) == 1 else '{"replaced":true}\n200', "")

    monkeypatch.setattr(subprocess, "run", post)
    with pytest.raises(ValueError):
        helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    candidate = (directory / "credential.next").read_bytes()
    assert (directory / "credential").read_text().strip() == OLD
    helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    assert requests[0]["credentialHash"] == requests[1]["credentialHash"]
    assert (directory / "credential").read_bytes() == candidate
    assert (directory / "credential.next").stat().st_mode & 0o077 == 0
    helper.replace(root, "node", "https://control.invalid:50052", "ROTATE", complete=True)
    assert not (directory / "credential.next").exists()
    assert not (directory / ".credential-operation").exists()


@pytest.mark.parametrize("change", ["node", "endpoint", "mode", "http", "https_origin"])
def test_changed_operation_cannot_reuse_a_saved_candidate(identity, monkeypatch, change):
    root, directory = identity
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: calls.append(args) or subprocess.CompletedProcess(args, 0, '{}\n409', ""))
    with pytest.raises(ValueError):
        helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    candidate = (directory / "credential.next").read_bytes()
    if change == "code":
        monkeypatch.setenv("FLUXOMNI_CREDENTIAL_CODE", "another.code")
    if change == "http":
        monkeypatch.setenv("FLUXOMNI_CREDENTIAL_URL", "http://control.invalid/redeem")
    if change == "https_origin":
        monkeypatch.setenv("FLUXOMNI_CREDENTIAL_URL", "https://another.invalid/redeem")
    with pytest.raises(ValueError):
        helper.replace(root, "other" if change == "node" else "node", "https://other.invalid:50052" if change == "endpoint" else "https://control.invalid:50052", "RECOVER" if change == "mode" else "ROTATE")
    assert len(calls) == 1
    assert (directory / "credential.next").read_bytes() == candidate
    assert (directory / "credential").read_text().strip() == OLD


def test_recovery_does_not_require_a_lost_old_secret(identity, monkeypatch):
    root, directory = identity
    (directory / "credential").unlink()
    def post(args, **kwargs):
        assert "currentCredential" not in json.loads(kwargs["input"])
        return subprocess.CompletedProcess(args, 0, '{"replaced":true}\n200', "")
    monkeypatch.setattr(subprocess, "run", post)
    helper.replace(root, "node", "https://control.invalid:50052", "RECOVER")
    assert len((directory / "credential").read_text().strip()) == 64


def test_concurrent_invocation_and_symlink_cannot_change_saved_secret(identity):
    root, directory = identity
    with (directory / ".credential-lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError):
            helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    (directory / "credential.next").symlink_to(directory / "credential")
    with pytest.raises(ValueError):
        helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    assert (directory / "credential").read_text().strip() == OLD


def test_public_installer_rotation_keeps_identity_and_candidate_across_lost_ack(installation):  # noqa: F811
    assets, directory, run = installation
    first = run("media-node")
    assert first.returncode == 0, first.stdout + first.stderr
    old = (directory / "node-secrets/credential").read_bytes()
    change = {"FLUXOMNI_CREDENTIAL_MODE": "ROTATE", "FLUXOMNI_CREDENTIAL_CODE": "replacement.code", "FLUXOMNI_CREDENTIAL_URL": "https://control.invalid/api/node-credentials/redeem"}
    failed = run("media-node", {**change, "TEST_ENROLLMENT_LOST_RESPONSE": "1"})
    assert failed.returncode != 0
    assert (directory / "node-secrets/credential").read_bytes() == old
    candidate = (directory / "node-secrets/credential.next").read_bytes()
    retry = run("media-node", change, arguments=["--capacity-upgrade", "node", "--confirm-control-plane-ready"])
    assert retry.returncode == 0, retry.stdout + retry.stderr
    assert (directory / "node-secrets/credential").read_bytes() == candidate
    assert candidate != old
    assert not (directory / "node-secrets/credential.next").exists()
    assert not (directory / "node-secrets/.credential-operation").exists()
    assert candidate.decode().strip() not in retry.stdout + retry.stderr + (directory / ".env").read_text()
    requests = [json.loads(line) for line in (assets.parent / "enrollment.jsonl").read_text().splitlines()]
    assert requests[-1]["credentialHash"] == requests[-2]["credentialHash"]


def test_completion_rejects_missing_or_mismatched_candidate(identity):
    root, directory = identity
    with pytest.raises(ValueError):
        helper.replace(root, "node", "https://control.invalid:50052", "ROTATE", complete=True)
    (directory / ".credential-operation").write_text("{}")
    (directory / "credential.next").write_text("b" * 64)
    with pytest.raises(ValueError):
        helper.replace(root, "node", "https://control.invalid:50052", "ROTATE", complete=True)
    assert (directory / ".credential-operation").exists()
    assert (directory / "credential.next").exists()


def test_retry_after_interrupted_cleanup_reuses_the_committed_secret(identity, monkeypatch):
    root, directory = identity
    hashes = []
    def post(args, **kwargs):
        hashes.append(json.loads(kwargs["input"])["credentialHash"])
        return subprocess.CompletedProcess(args, 0, '{"replaced":true}\n200', "")
    monkeypatch.setattr(subprocess, "run", post)
    helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    committed = (directory / "credential").read_bytes()
    (directory / "credential.next").unlink()
    helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    assert hashes[0] == hashes[1]
    assert (directory / "credential").read_bytes() == committed


def test_new_grant_reuses_candidate_after_cancelled_or_expired_redemption(identity, monkeypatch):
    root, _directory = identity
    hashes = []
    def post(args, **kwargs):
        hashes.append(json.loads(kwargs["input"])["credentialHash"])
        return subprocess.CompletedProcess(args, 0, '{}\n409' if len(hashes) == 1 else '{"replaced":true}\n200', "")
    monkeypatch.setattr(subprocess, "run", post)
    with pytest.raises(ValueError):
        helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    monkeypatch.setenv("FLUXOMNI_CREDENTIAL_CODE", "new.admin.grant")
    helper.replace(root, "node", "https://control.invalid:50052", "ROTATE")
    assert hashes[0] == hashes[1]
