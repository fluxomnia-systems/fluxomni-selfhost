"""Garage object-storage setup: credential generation, provisioning, Compose contract."""

import importlib.util
import json
import os
import shutil
import socket
import stat
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("object_storage", ROOT / "scripts/object-storage.py")
object_storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(object_storage)


def good_compose_config() -> dict:
    return {
        "services": {
            "garage": {
                "image": object_storage.GARAGE_IMAGE,
                "ports": [
                    {"host_ip": "127.0.0.1", "target": 3900, "published": "3900"},
                    {"host_ip": "127.0.0.1", "target": 3903, "published": "3903"},
                ],
                "environment": {"GARAGE_CONFIG_FILE": "/etc/garage.toml"},
            },
            "garage-init": {"image": "python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df"},
            "control-plane": {
                "environment": {
                    "FLUXOMNI_STORAGE_BACKEND": "id=object_storage,kind=s3,bucket=fluxomni-artifacts,endpoint_url=http://garage:3900,path_style=true,fetch_mode=presigned",
                    "AWS_ACCESS_KEY_ID": "GK" + "a" * 32,
                }
            },
        }
    }


class TestInit:
    def test_generates_secure_config_and_credentials(self, tmp_path):
        storage = object_storage.init(tmp_path, "fluxomni-artifacts", 1024, 10)
        assert stat.S_IMODE(storage.stat().st_mode) == 0o700
        config_path = storage / "config.toml"
        credentials_path = storage / "credentials.env"
        for path in (config_path, credentials_path):
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
        text = config_path.read_text()
        assert "replication_factor = 1" in text
        assert 'admin_token = "' in text
        assert "[s3_api]" in text and "[admin]" in text
        values = dict(line.split("=", 1) for line in credentials_path.read_text().splitlines() if "=" in line)
        assert object_storage.KEY_ID_PATTERN.fullmatch(values["FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY"])
        assert object_storage.SECRET_PATTERN.fullmatch(values["FLUXOMNI_OBJECT_STORAGE_SECRET_KEY"])
        assert values["FLUXOMNI_OBJECT_STORAGE_BUCKET"] == "fluxomni-artifacts"
        assert values["FLUXOMNI_OBJECT_STORAGE_QUOTA_SIZE"] == "1024"

    def test_init_is_idempotent_and_keeps_credentials(self, tmp_path):
        object_storage.init(tmp_path, "fluxomni-artifacts", 1024, 10)
        first = (tmp_path / "object-storage/credentials.env").read_text()
        object_storage.init(tmp_path, "fluxomni-artifacts", 1024, 10)
        assert (tmp_path / "object-storage/credentials.env").read_text() == first

    def test_init_force_rotates_credentials(self, tmp_path):
        object_storage.init(tmp_path, "fluxomni-artifacts", 1024, 10)
        first = (tmp_path / "object-storage/credentials.env").read_text()
        object_storage.init(tmp_path, "fluxomni-artifacts", 1024, 10, force=True)
        assert (tmp_path / "object-storage/credentials.env").read_text() != first

    def test_init_rerun_updates_quota_but_keeps_credentials(self, tmp_path):
        object_storage.init(tmp_path, "fluxomni-artifacts", 1024, 10)
        first = (tmp_path / "object-storage/credentials.env").read_text()
        object_storage.init(tmp_path, "fluxomni-artifacts", 2048, 20)
        second = (tmp_path / "object-storage/credentials.env").read_text()
        assert "FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY=" + first.split("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY=")[1].splitlines()[0] in second
        assert "FLUXOMNI_OBJECT_STORAGE_QUOTA_SIZE=2048" in second

    def test_init_rejects_invalid_bucket(self, tmp_path):
        with pytest.raises(SystemExit):
            object_storage.init(tmp_path, "Bad_Bucket", 1024, 10)

    def test_env_lines_round_trip(self, tmp_path):
        object_storage.init(tmp_path, "fluxomni-artifacts", 1024, 10)
        lines = object_storage.env_lines(tmp_path / "object-storage")
        keys = {line.split("=", 1)[0] for line in lines}
        assert "FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY" in keys
        assert "FLUXOMNI_OBJECT_STORAGE_SECRET_KEY" in keys


class TestVerifyCompose:
    def test_accepts_secure_rendered_config(self, monkeypatch):
        monkeypatch.setenv("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY", "GK" + "a" * 32)
        object_storage.verify_compose(good_compose_config())

    def test_rejects_unpinned_image(self, monkeypatch):
        monkeypatch.setenv("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY", "GK" + "a" * 32)
        config = good_compose_config()
        config["services"]["garage"]["image"] = "dxflrs/garage:latest"
        with pytest.raises(ValueError, match="pinned"):
            object_storage.verify_compose(config)

    def test_rejects_public_port(self, monkeypatch):
        monkeypatch.setenv("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY", "GK" + "a" * 32)
        config = good_compose_config()
        config["services"]["garage"]["ports"].append({"host_ip": "0.0.0.0", "target": 3900, "published": "3900"})
        with pytest.raises(ValueError, match="loopback"):
            object_storage.verify_compose(config)

    def test_rejects_non_presigned_backend(self, monkeypatch):
        monkeypatch.setenv("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY", "GK" + "a" * 32)
        config = good_compose_config()
        config["services"]["control-plane"]["environment"]["FLUXOMNI_STORAGE_BACKEND"] = (
            "id=object_storage,kind=s3,endpoint_url=http://garage:3900,fetch_mode=public"
        )
        with pytest.raises(ValueError, match="presigned"):
            object_storage.verify_compose(config)

    def test_rejects_default_bucket_bootstrap(self, monkeypatch):
        monkeypatch.setenv("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY", "GK" + "a" * 32)
        config = good_compose_config()
        config["services"]["garage"]["environment"]["GARAGE_DEFAULT_BUCKET"] = "fluxomni-artifacts"
        with pytest.raises(ValueError, match="default-bucket"):
            object_storage.verify_compose(config)

    def test_rejects_ambient_key_mismatch(self, monkeypatch):
        monkeypatch.setenv("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY", "GK" + "b" * 32)
        with pytest.raises(ValueError, match="scoped"):
            object_storage.verify_compose(good_compose_config())


class FakeGarage:
    """Minimal in-process admin API + S3 endpoint for provision tests."""

    def __init__(self):
        self.admin_calls = []
        self.objects = {}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _json(self, code, payload):
                body = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.startswith("/v2/ListKeysInfo"):
                    self._json(200, [{"accessKeyId": "GK" + "c" * 32, "name": "fluxomni"}, {"accessKeyId": creds_key, "name": "fluxomni"}])
                elif self.path.startswith("/v2/GetBucketInfo"):
                    self._json(200, {"id": "bucket-id-1", "globalAliases": ["fluxomni-artifacts"]})
                elif self.path.startswith("/s3/"):
                    key = self.path[len("/s3/") :]
                    if key in outer.objects:
                        body = outer.objects[key]
                        self.send_response(200)
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                    else:
                        self.send_response(404)
                        self.end_headers()
                else:
                    self._json(404, {"error": "not found"})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                operation = self.path.rsplit("/", 1)[-1].split("?")[0]
                outer.admin_calls.append((operation, body, self.path))
                self._json(200, {"ok": True, "id": "bucket-id-1"})

            def do_PUT(self):
                if self.path.startswith("/s3/"):
                    length = int(self.headers.get("Content-Length", 0))
                    outer.objects[self.path[len("/s3/") :]] = self.rfile.read(length)
                    self.send_response(200)
                    self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_DELETE(self):
                if self.path.startswith("/s3/"):
                    outer.objects.pop(self.path[len("/s3/") :], None)
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        self.server.shutdown()
        self.thread.join()


@pytest.fixture
def garage(tmp_path):
    object_storage.init(tmp_path, "fluxomni-artifacts", 4096, 50)
    global creds_key
    creds_key = (tmp_path / "object-storage/credentials.env").read_text().split("FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY=")[1].splitlines()[0]
    fake = FakeGarage()
    yield fake, tmp_path / "object-storage/config.toml"
    fake.stop()


creds_key = ""


class TestProvision:
    def test_provision_scopes_key_and_verifies_checksum(self, garage):
        fake, config_path = garage
        creds = dict(line.split("=", 1) for line in (config_path.parent / "credentials.env").read_text().splitlines() if "=" in line)
        # The fake serves both admin and S3 on one port; provision uses two URLs.
        object_storage.provision(
            config_path,
            admin_url=fake.url,
            s3_url=f"{fake.url}/s3",
            bucket="fluxomni-artifacts",
            access_key=creds["FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY"],
            secret_key=creds["FLUXOMNI_OBJECT_STORAGE_SECRET_KEY"],
            quota_size=4096,
            quota_objects=50,
        )
        operations = [op for op, *_ in fake.admin_calls]
        assert "ImportKey" in operations and "CreateBucket" in operations
        # The stale rotated key is revoked, the current key is kept.
        deletes = [path for op, _, path in fake.admin_calls if op == "DeleteKey"]
        assert deletes == [f"/v2/DeleteKey?id=GK{'c' * 32}"]
        allow = next(body for op, body, _ in fake.admin_calls if op == "AllowBucketKey")
        assert allow["permissions"] == {"read": True, "write": True, "owner": False}
        quota = next(body for op, body, _ in fake.admin_calls if op == "UpdateBucket")
        assert quota["quotas"] == {"maxSize": 4096, "maxObjects": 50}
        # The probe object was written, read back, and deleted.
        assert not fake.objects

    def test_provision_rejects_malformed_credentials(self, garage):
        _, config_path = garage
        with pytest.raises(SystemExit, match="format"):
            object_storage.provision(config_path, "http://127.0.0.1:1", "http://127.0.0.1:1", "b", "short", "short", 1, 1)


class TestSigV4:
    def test_signature_is_deterministic_and_well_formed(self):
        headers = object_storage.sign_v4(
            "PUT",
            "http://garage:3900/bucket/key",
            "GK" + "a" * 32,
            "b" * 64,
            "us-east-1",
            b"payload",
            {"x-amz-date": "20260101T000000Z"},
        )
        auth = headers["Authorization"]
        assert auth.startswith("AWS4-HMAC-SHA256 Credential=GK")
        assert "SignedHeaders=host;x-amz-content-sha256;x-amz-date" in auth
        again = object_storage.sign_v4(
            "PUT", "http://garage:3900/bucket/key", "GK" + "a" * 32, "b" * 64, "us-east-1", b"payload",
            {"x-amz-date": "20260101T000000Z"},
        )
        assert again["Authorization"] == auth


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.mark.skipif(shutil.which("docker") is None, reason="requires a Docker daemon")
def test_live_garage_provision_round_trip(tmp_path):
    """Contract check against a real Garage container: scoped key, quota, checksums."""
    if subprocess.run(["docker", "info"], capture_output=True, check=False).returncode != 0:
        pytest.skip("Docker daemon not reachable")
    object_storage.init(tmp_path, "fluxomni-artifacts", 4096, 50)
    (tmp_path / "scripts").mkdir()
    shutil.copy(ROOT / "scripts/object-storage.py", tmp_path / "scripts/object-storage.py")
    # The overlay merges into the base stack; the test only starts garage.
    (tmp_path / "docker-compose.yml").write_text("services:\n  control-plane:\n    image: alpine:3.22\n")
    creds = dict(line.split("=", 1) for line in (tmp_path / "object-storage/credentials.env").read_text().splitlines() if "=" in line)
    env = dict(os.environ)
    env.update(
        {
            "FLUXOMNI_OBJECT_STORAGE_BUCKET": "fluxomni-artifacts",
            "FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY": creds["FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY"],
            "FLUXOMNI_OBJECT_STORAGE_SECRET_KEY": creds["FLUXOMNI_OBJECT_STORAGE_SECRET_KEY"],
            "FLUXOMNI_OBJECT_STORAGE_DATA_DIR": str(tmp_path / "garage-data"),
            "FLUXOMNI_OBJECT_STORAGE_API_PORT": str(free_port()),
            "FLUXOMNI_GARAGE_ADMIN_PORT": str(free_port()),
        }
    )
    compose = [
        "docker", "compose",
        "-f", str(tmp_path / "docker-compose.yml"),
        "-f", str(ROOT / "docker-compose.object-storage.yml"),
        "-p", "fluxomni-os-test",
    ]
    try:
        subprocess.run([*compose, "up", "-d", "--wait", "garage"], check=True, env=env, cwd=tmp_path, capture_output=True)
        object_storage.provision(
            tmp_path / "object-storage/config.toml",
            admin_url=f"http://127.0.0.1:{env['FLUXOMNI_GARAGE_ADMIN_PORT']}",
            s3_url=f"http://127.0.0.1:{env['FLUXOMNI_OBJECT_STORAGE_API_PORT']}",
            bucket="fluxomni-artifacts",
            access_key=creds["FLUXOMNI_OBJECT_STORAGE_ACCESS_KEY"],
            secret_key=creds["FLUXOMNI_OBJECT_STORAGE_SECRET_KEY"],
            quota_size=4096,
            quota_objects=50,
        )
    finally:
        subprocess.run([*compose, "down", "-v"], check=False, env=env, cwd=tmp_path, capture_output=True)
