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
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

name, args = Path(sys.argv[0]).name, sys.argv[1:]
if name == "curl":
    url = next(arg for arg in args if arg.startswith("https://"))
    relative = "scripts/" + url.rsplit("/", 1)[1] if "/scripts/" in url else url.rsplit("/", 1)[1]
    shutil.copyfile(Path(os.environ["TEST_ASSETS"]) / relative, args[args.index("-o") + 1])
elif name == "python3":
    if len(args) > 1 and Path(args[0]).name == "preparation-cgroup.py" and args[1] in ("install", "disable"):
        with open(Path(os.environ["TEST_ASSETS"]).parent / "preparation.jsonl", "a") as log:
            log.write(json.dumps(args[1:]) + "\n")
        if os.environ.get("TEST_PROVISION_FAIL"):
            sys.exit(1)
        key = hashlib.sha256(str(Path(args[2]).resolve()).encode()).hexdigest()[:24]
        print("/sys/fs/cgroup/fluxomni-preparation-" + key)
    else:
        sys.exit(subprocess.run([sys.executable, *args]).returncode)
elif name == "uname":
    print(os.environ.get("TEST_HOST_OS", "Linux"))
elif name == "stat":
    print(os.environ.get("TEST_CGROUP_FS", "cgroup2fs"))
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
    elif args[:2] == ["info", "--format"]:
        print(os.environ.get("TEST_DOCKER_INFO", '2 ["name=seccomp"]'))
    elif args[:2] == ["context", "show"]:
        print("default")
    elif args[:2] == ["context", "inspect"]:
        print(os.environ.get("TEST_DOCKER_ENDPOINT", "unix:///var/run/docker.sock"))
    elif args[:2] == ["compose", "up"]:
        rendered = subprocess.check_output([os.environ["REAL_DOCKER"], "compose", "config", "--format", "json"], text=True)
        Path("started.json").write_text(rendered)
    elif args[:2] == ["compose", "exec"]:
        assert args[2:6] == ["-T", "media-node", "sh", "-c"]
        if "root=$FLUXOMNI_PREPARATION_CGROUP_ROOT" in args[6]:
            sys.exit(1 if os.environ.get("TEST_ENFORCEMENT_FAIL") else 0)
        # Run the real readiness predicate with the effective Compose soft limit.
        config = json.loads(Path("started.json").read_text())
        limit = config["services"]["media-node"]["ulimits"]["nofile"]["soft"]
        script = 'ulimit() { printf "%s\\n" "$TEST_LIMIT"; }; ' + args[6]
        sys.exit(subprocess.run(["sh", "-c", script], env={**os.environ, "TEST_LIMIT": str(limit)}).returncode)
    elif args[0] == "inspect":
        print("2026-10-04T00:00:00Z" if "StartedAt" in args[2] else "healthy")
    elif args[0] == "logs":
        print("Registered media node with control plane")
        if os.environ.get("TEST_ISOLATION_UNAVAILABLE"):
            print("Preparation isolation unavailable")
        elif not os.environ.get("TEST_UNSUPPORTED_IMAGE"):
            print("Preparation isolation enforced")
    else:
        raise AssertionError(args)
else:
    raise AssertionError(name)
''')
    stub.chmod(0o755)
    for name in ("docker", "curl", "hostname", "nc", "sudo", "apt-get", "ufw", "firewall-cmd", "systemctl", "python3", "uname", "stat"):
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


PREPARATION = {
    'FLUXOMNI_PREPARATION_CGROUP_ENABLED': '1',
    'FLUXOMNI_PREPARATION_CPU_MILLICORES': '500',
    'FLUXOMNI_PREPARATION_MEMORY_MIB': '1024',
    'FLUXOMNI_PREPARATION_TASKS': '64',
}


def started_node(destination):
    return json.loads((destination / 'started.json').read_text())['services']['media-node']


# @lat: [[installation#Preparation installer regression coverage]]
@pytest.mark.parametrize('target', ['full', 'media-node'])
def test_preparation_enable_preserve_update_disable_reenable(installation, target):
    assets, destination, run = installation
    assert run(target).returncode == 0
    assert 'cgroup' not in started_node(destination)
    assert not any(k in started_node(destination)['environment'] for k in PREPARATION if k != 'FLUXOMNI_PREPARATION_CGROUP_ENABLED')
    first = run(target, PREPARATION)
    assert first.returncode == 0, first.stdout + first.stderr
    node = started_node(destination)
    assert node['cgroup'] == 'host' and node['user'] == '0:0'
    mount = next(v for v in node['volumes'] if v['target'] == '/preparation-cgroup')
    assert mount['source'].startswith('/sys/fs/cgroup/fluxomni-preparation-')
    assert mount['type'] == 'bind' and not mount.get('read_only')
    assert mount['bind']['create_host_path'] is False
    assert node['environment']['FLUXOMNI_PREPARATION_CGROUP_ROOT'] == '/preparation-cgroup'
    for key, value in PREPARATION.items():
        assert node['environment'][key] == value
    saved = (destination / '.env').read_bytes()
    assert run(target).returncode == 0
    assert (destination / '.env').read_bytes() == saved
    result = run(target, {'FLUXOMNI_PREPARATION_CPU_MILLICORES': '750'})
    assert result.returncode == 0, result.stdout + result.stderr
    assert started_node(destination)['environment']['FLUXOMNI_PREPARATION_CPU_MILLICORES'] == '750'
    disabled = run(target, {'FLUXOMNI_PREPARATION_CGROUP_ENABLED': '0'})
    assert disabled.returncode == 0, disabled.stdout + disabled.stderr
    node = started_node(destination)
    assert 'cgroup' not in node
    assert not any(k in node['environment'] for k in PREPARATION if k != 'FLUXOMNI_PREPARATION_CGROUP_ENABLED')
    assert not any(v['target'] == '/preparation-cgroup' for v in node['volumes'])
    operations = [json.loads(line) for line in (assets.parent / 'preparation.jsonl').read_text().splitlines()]
    assert operations[-1][0] == 'disable'
    assert run(target).returncode == 0
    reenabled = run(target, {'FLUXOMNI_PREPARATION_CGROUP_ENABLED': '1'})
    assert reenabled.returncode == 0, reenabled.stdout + reenabled.stderr
    assert started_node(destination)['environment']['FLUXOMNI_PREPARATION_CPU_MILLICORES'] == '750'
    assert started_node(destination)['environment']['FLUXOMNI_PREPARATION_MEMORY_MIB'] == '1024'


@pytest.mark.parametrize('value', ['0', '-1', '1.5', 'abc', '9999999999999999999999999999', '01', '1\nPRIVILEGED=true'])
@pytest.mark.parametrize('key', ['FLUXOMNI_PREPARATION_CPU_MILLICORES', 'FLUXOMNI_PREPARATION_MEMORY_MIB', 'FLUXOMNI_PREPARATION_TASKS'])
def test_invalid_preparation_budget_does_not_mutate_existing_install(installation, key, value):
    _, destination, run = installation
    assert run('full').returncode == 0
    before = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()}
    result = run('full', {**PREPARATION, key: value})
    assert result.returncode != 0
    assert {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()} == before


@pytest.mark.parametrize('target', ['full', 'media-node'])
def test_partial_preparation_configuration_rejected(installation, target):
    _, destination, run = installation
    result = run(target, {'FLUXOMNI_PREPARATION_CGROUP_ENABLED': '1', 'FLUXOMNI_PREPARATION_CPU_MILLICORES': '500'})
    assert result.returncode != 0
    assert not destination.exists()


# @lat: [[installation#Preparation host prerequisites]]
@pytest.mark.parametrize('override', [
    {'TEST_HOST_OS': 'Darwin'}, {'TEST_CGROUP_FS': 'tmpfs'},
    {'TEST_DOCKER_INFO': '1 []'}, {'TEST_DOCKER_INFO': '2 ["name=rootless"]'},
    {'TEST_DOCKER_INFO': '2 ["name=userns"]'},
    {'TEST_DOCKER_ENDPOINT': 'ssh://other-host'}, {'DOCKER_HOST': 'tcp://other-host:2375'},
])
def test_preparation_host_preflight_rejects_unsupported_install(installation, override):
    _, destination, run = installation
    result = run('full', {**PREPARATION, **override})
    assert result.returncode != 0
    assert not destination.exists()


@pytest.mark.parametrize('change', [
    {'user': '1000:1000'}, {'cgroup': 'private'}, {'privileged': True},
    {'environment': {'FLUXOMNI_PREPARATION_CPU_MILLICORES': '2000'}},
    {'volumes': [{'type': 'bind', 'source': '/sys/fs/cgroup', 'target': '/preparation-cgroup', 'read_only': True}]},
])
def test_preparation_effective_override_rejected_and_configuration_restored(installation, change):
    _, destination, run = installation
    assert run('full').returncode == 0
    override = destination / 'docker-compose.override.yml'
    override.write_text(yaml.safe_dump({'services': {'media-node': change}}))
    before = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()}
    result = run('full', PREPARATION)
    assert result.returncode != 0
    assert 'unsafe preparation Compose' in result.stderr
    assert {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()} == before


@pytest.mark.parametrize('failure', ['TEST_PROVISION_FAIL', 'TEST_ENFORCEMENT_FAIL', 'TEST_ISOLATION_UNAVAILABLE'])
def test_preparation_failure_does_not_report_installation_ready(installation, failure):
    _, destination, run = installation
    assert run('full').returncode == 0
    saved = (destination / '.env').read_bytes()
    result = run('full', {**PREPARATION, failure: '1'})
    assert result.returncode != 0
    assert 'is ready' not in result.stdout
    if failure == 'TEST_PROVISION_FAIL':
        assert (destination / '.env').read_bytes() == saved


def test_preparation_supported_to_unsupported_image_rerun_cannot_reuse_old_limit_proof(installation):
    _, destination, run = installation
    supported = run('full', PREPARATION)
    assert supported.returncode == 0, supported.stdout + supported.stderr
    # The Docker stub still reports matching root limits; only positive current
    # startup evidence disappears, as with an older image ignoring these envs.
    unsupported = run('full', {'TEST_UNSUPPORTED_IMAGE': '1'})
    assert unsupported.returncode != 0
    assert 'did not confirm preparation enforcement' in unsupported.stderr
    assert 'is ready' not in unsupported.stdout
    assert started_node(destination)['environment']['FLUXOMNI_PREPARATION_CPU_MILLICORES'] == '500'
