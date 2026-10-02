"""Execute the installer with local assets and a simulated Docker lifecycle.

Compose rendering uses the real CLI; no Docker daemon or network is needed.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def installation(tmp_path):
    assets = tmp_path / "assets"
    shutil.copytree(ROOT, assets, ignore=shutil.ignore_patterns(".git", "book", "__pycache__", ".pytest_cache"))
    commands = tmp_path / "bin"
    commands.mkdir()
    stub = commands / "stub"
    stub.write_text(f"#!{sys.executable}\n" + r'''
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

name, args = Path(sys.argv[0]).name, sys.argv[1:]
if name == "curl":
    url = next(arg for arg in args if arg.startswith("https://"))
    relative = "scripts/generated-version-map.sh" if url.endswith("generated-version-map.sh") else url.rsplit("/", 1)[1]
    shutil.copyfile(Path(os.environ["TEST_ASSETS"]) / relative, args[args.index("-o") + 1])
elif name == "hostname":
    print("127.0.0.1")
elif name == "nc":
    pass
elif name == "sudo":
    sys.exit(subprocess.run(args).returncode)
elif name in ("apt-get", "ufw", "firewall-cmd", "systemctl"):
    with open(Path(os.environ["TEST_ASSETS"]).parent / "firewall.jsonl", "a") as log:
        log.write(json.dumps([name, *args]) + "\n")
elif name == "docker":
    version_fixture = Path(os.environ["TEST_ASSETS"]) / "compose-version.txt"
    if args == ["compose", "version", "--short"] and version_fixture.exists():
        print(version_fixture.read_text())
        sys.exit(0)
    if args[:2] in (["compose", "config"], ["compose", "version"]):
        sys.exit(subprocess.run([os.environ["REAL_DOCKER"], *args]).returncode)
    if args == ["info"] or args[:2] == ["compose", "pull"]:
        pass
    elif args[:2] == ["compose", "up"]:
        rendered = subprocess.check_output([os.environ["REAL_DOCKER"], "compose", "config", "--format", "json"], text=True)
        Path("started.json").write_text(rendered)
    elif args[:2] == ["compose", "exec"]:
        assert args[2:6] == ["-T", "media-node", "sh", "-c"]
        # Run the real readiness predicate with the effective Compose soft limit.
        config = json.loads(Path("started.json").read_text())
        limit = config["services"]["media-node"]["ulimits"]["nofile"]["soft"]
        script = 'ulimit() { printf "%s\\n" "$TEST_LIMIT"; }; ' + args[6]
        sys.exit(subprocess.run(["sh", "-c", script], env={**os.environ, "TEST_LIMIT": str(limit)}).returncode)
    elif args[0] == "inspect":
        print("healthy")
    elif args[0] == "logs":
        print("Registered media node with control plane")
    else:
        raise AssertionError(args)
else:
    raise AssertionError(name)
''')
    stub.chmod(0o755)
    for name in ("docker", "curl", "hostname", "nc", "sudo", "apt-get", "ufw", "firewall-cmd", "systemctl"):
        (commands / name).symlink_to(stub)
    destination = tmp_path / "installation"
    env = {
        **{key: value for key, value in os.environ.items() if not key.startswith(("FLUXOMNI_", "COMPOSE_"))},
        "PATH": f"{commands}:{os.environ['PATH']}",
        "REAL_DOCKER": shutil.which("docker"),
        "TEST_ASSETS": str(assets),
        "FLUXOMNI_REPO_RAW": "https://assets.invalid/v26.3.2",
        "FLUXOMNI_DIR": str(destination),
        "FLUXOMNI_VERSION": "v26.3.2",
        "FLUXOMNI_CONTROL_PLANE_RPC_ENDPOINT": "http://127.0.0.1:50052",
        "FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN": "test-token",
        "FLUXOMNI_MEDIA_NODE_PUBLIC_HOST": "127.0.0.1",
        "FLUXOMNI_MEDIA_NODE_ID": "test-node",
        "FLUXOMNI_MEDIA_NODE_NAME": "Test Node",
        "WITH_INITIAL_UPGRADE": "0",
        "WITH_UFW": "0",
        "WITH_FIREWALLD": "0",
    }

    def run(target, overrides=None):
        return subprocess.run(["bash", str(ROOT / "install.sh"), target], cwd=tmp_path, env={**env, **(overrides or {})}, text=True, capture_output=True, timeout=30)

    return assets, destination, run


# @lat: [[installation#Installer regression coverage]]
@pytest.mark.parametrize("target,asset", [("full", "docker-compose.yml"), ("media-node", "docker-compose.media-node.yml")])
@pytest.mark.parametrize("limits", [None, {"nproc": 2048}, {"nofile": {"soft": 131072, "hard": 131072}}])
@pytest.mark.parametrize("mapping_style", ["block", "flow", "alias"])
def test_installs_and_reruns_preserve_data_and_supply_file_limits(installation, target, asset, limits, mapping_style):
    assets, destination, run = installation
    source = assets / asset
    config = yaml.safe_load(source.read_text())
    media = config["services"]["media-node"]
    if limits is None:
        media.pop("ulimits")  # Shape of the published v26.3.2 assets.
    else:
        media["ulimits"] = limits
    if mapping_style == "alias" and limits is not None:
        config = {"x-limits": limits, **config}
    source.write_text(yaml.safe_dump(config, sort_keys=False, default_flow_style=None if mapping_style == "flow" else False))
    original_assets = source.read_bytes()
    first = run(target)
    assert first.returncode == 0, first.stdout + first.stderr
    started = json.loads((destination / "started.json").read_text())
    expected = {"nofile": {"soft": 65536, "hard": 65536}, **(limits or {})}
    assert started["services"]["media-node"]["ulimits"] == expected
    assert ("control-plane" in started["services"]) == (target == "full")
    assert (destination / "compose.release.yml").read_bytes() == original_assets
    media_service = started["services"]["media-node"]
    assert media_service["image"].endswith(":v26.3.2")
    assert any(volume["type"] == "bind" and volume["source"] == str(destination / "data") for volume in media_service["volumes"])
    with (destination / ".env").open("a") as env_file:
        env_file.write("ENV_FILE_SENTINEL=loaded\n")
    env_before = (destination / ".env").read_text()
    (destination / "data/state.db").write_bytes(b"existing database sentinel")
    override = destination / "docker-compose.override.yml"
    override.write_text("services:\n  media-node:\n    environment:\n      OPERATOR_SETTING: retained\n")
    override_before = override.read_bytes()
    second = run(target)
    assert second.returncode == 0, second.stdout + second.stderr
    assert (destination / "data/state.db").read_bytes() == b"existing database sentinel"
    assert (destination / ".env").read_text() == env_before
    assert override.read_bytes() == override_before
    started = json.loads((destination / "started.json").read_text())
    assert started["services"]["media-node"]["ulimits"] == expected
    assert started["services"]["media-node"]["environment"]["OPERATOR_SETTING"] == "retained"
    assert started["services"]["media-node"]["environment"]["ENV_FILE_SENTINEL"] == "loaded"


# @lat: [[installation#Effective limit verification]]
@pytest.mark.parametrize("target", ["full", "media-node"])
def test_operator_override_with_insufficient_limit_fails_installation(installation, target):
    _, destination, run = installation
    destination.mkdir()
    override = destination / "docker-compose.override.yml"
    override.write_text("services:\n  media-node:\n    ulimits:\n      nofile:\n        soft: 1024\n        hard: 1024\n")
    result = run(target)
    assert result.returncode != 0
    assert "requires at least 1128 open files" in result.stderr
    assert "is ready" not in result.stdout
    assert "is connected" not in result.stdout


@pytest.mark.parametrize("asset", ["docker-compose.yml", "docker-compose.media-node.yml"])
def test_manual_deployment_assets_include_file_limits(asset):
    config = yaml.safe_load((ROOT / asset).read_text())
    assert config["services"]["media-node"]["ulimits"]["nofile"] == {"soft": 65536, "hard": 65536}


# @lat: [[installation#Compose version requirement]]
def test_unsupported_compose_leaves_existing_installation_untouched(installation):
    assets, destination, run = installation
    (assets / "compose-version.txt").write_text("v2.19.1")
    destination.mkdir()
    compose = destination / "docker-compose.yml"
    compose.write_text("existing compose sentinel")
    result = run("full")
    assert result.returncode != 0
    assert "Docker Compose 2.20.0 or newer" in result.stdout
    assert compose.read_text() == "existing compose sentinel"
    assert not (destination / "started.json").exists()


# @lat: [[installation#Publisher Port Regression Coverage]]
@pytest.mark.parametrize("target", ["full", "media-node"])
@pytest.mark.parametrize("firewall", ["WITH_UFW", "WITH_FIREWALLD"])
def test_publish_ports_preserve_mapping_advertisement_and_firewall(installation, target, firewall):
    assets, destination, run = installation
    result = run(target)
    assert result.returncode == 0, result.stdout + result.stderr
    media = json.loads((destination / "started.json").read_text())["services"]["media-node"]
    assert media["environment"]["FLUXOMNI_MEDIA_NODE_WHIP_PORT"] == "8003"
    assert media["environment"]["FLUXOMNI_SRS_RTC_PORT"] == "8000"
    assert any(p["target"] == 8003 and p["published"] == "8003" and p["protocol"] == "tcp" for p in media["ports"])
    custom = {
        "FLUXOMNI_MEDIA_NODE_RTMP_PORT": "21387",
        "FLUXOMNI_MEDIA_NODE_HLS_PORT": "22387",
        "FLUXOMNI_MEDIA_NODE_SRT_PORT": "25387",
        "FLUXOMNI_MEDIA_NODE_WHIP_PORT": "27387",
        "FLUXOMNI_SRS_RTC_PORT": "26387",
        "FLUXOMNI_SRS_CANDIDATE": "media.example.com",
        firewall: "1",
    }
    result = run(target, custom)
    assert result.returncode == 0, result.stdout + result.stderr
    # No overrides: saved port and candidate choices must survive reinstall.
    result = run(target, {firewall: "1"})
    assert result.returncode == 0, result.stdout + result.stderr
    media = json.loads((destination / "started.json").read_text())["services"]["media-node"]
    for name, value in custom.items():
        if name.startswith("FLUXOMNI_"):
            assert media["environment"][name] == value
    for host, container, protocol in [(21387, 1935, "tcp"), (22387, 8000, "tcp"), (25387, 10080, "udp"), (27387, 8003, "tcp"), (26387, 26387, "udp")]:
        assert any(p["target"] == container and p["published"] == str(host) and p["protocol"] == protocol for p in media["ports"])
    commands = [json.loads(line) for line in (assets.parent / "firewall.jsonl").read_text().splitlines()]
    for port, protocol in [(21387, "tcp"), (22387, "tcp"), (27387, "tcp"), (25387, "udp"), (26387, "udp")]:
        expected = ["ufw", "allow", f"{port}/{protocol}"] if firewall == "WITH_UFW" else ["firewall-cmd", "--zone=public", "--permanent", f"--add-port={port}/{protocol}"]
        assert commands.count(expected) == 2
