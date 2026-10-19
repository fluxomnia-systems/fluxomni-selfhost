"""Verify public commands select one release before installation starts."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = "https://raw.githubusercontent.com/fluxomnia-systems/fluxomni-selfhost"
STABLE_BUNDLE = "f4a0b3b0c72da80dd889ef4a51f637537dd89406"


@pytest.fixture
def launch(tmp_path):
    routes = {f"{RAW}/main/scripts/generated-version-map.sh": (ROOT / "scripts/generated-version-map.sh").read_text()}
    stub = tmp_path / "curl"
    stub.write_text(f"#!{sys.executable}\n" + '''
import json, os, pathlib, sys
args = sys.argv[1:]
url = next(arg for arg in args if arg.startswith("https://"))
with open(os.environ["TEST_REQUESTS"], "a") as f:
    f.write(url + "\\n")
body = json.loads(pathlib.Path(os.environ["TEST_ROUTES"]).read_text()).get(url)
if body is None:
    if "-fsSL" in args:
        sys.exit(22)
    print("404", end="")
else:
    pathlib.Path(args[args.index("-o") + 1]).write_text(body)
    if "--write-out" in args:
        print("200", end="")
''')
    stub.chmod(0o755)
    destination = tmp_path / "install"
    route_file = tmp_path / "routes.json"
    requests = tmp_path / "requests.log"
    env = {key: value for key, value in os.environ.items() if not key.startswith(("FLUXOMNI_", "COMPOSE_"))}
    env.update(PATH=f"{tmp_path}:{env['PATH']}", HOME=str(tmp_path), TEST_ROUTES=str(route_file), TEST_REQUESTS=str(requests))

    def run(args=(), values=None):
        route_file.write_text(json.dumps(routes))
        return subprocess.run(["bash", str(ROOT / "install.sh"), *args], cwd=tmp_path,
                              env={**env, "FLUXOMNI_DIR": str(destination), **(values or {})},
                              capture_output=True, text=True, timeout=10)

    return routes, destination, requests, run


def child_script():
    return f'''#!/bin/bash
{sys.executable} - "$@" <<'PY'
import json, os, sys
print(json.dumps({{"version": os.environ["FLUXOMNI_VERSION"], "ref": os.environ.get("FLUXOMNI_SELFHOST_REF"), "args": sys.argv[1:]}}))
sys.exit(int(os.environ.get("TEST_CHILD_STATUS", "0")))
PY
'''


# @lat: [[installation#Public release selection tests]]
def test_default_and_saved_latest_use_the_stable_installer_and_preserve_channel(launch):
    routes, destination, _, run = launch
    routes[f"{RAW}/{STABLE_BUNDLE}/install.sh"] = child_script()
    first = run()
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout) == {"version": "latest", "ref": STABLE_BUNDLE, "args": []}
    destination.mkdir()
    (destination / ".env").write_text("FLUXOMNI_VERSION=latest\n")
    routes[f"{RAW}/main/scripts/generated-version-map.sh"] = routes[f"{RAW}/main/scripts/generated-version-map.sh"].replace("'v26.3.2'", "'v26.4.0'", 1)
    routes[f"{RAW}/v26.4.0/scripts/install-runtime.sh"] = child_script()
    rerun = run()
    assert rerun.returncode == 0, rerun.stderr
    assert json.loads(rerun.stdout)["ref"] == "v26.4.0"


@pytest.mark.parametrize("target", ["full", "media-node"])
def test_saved_stable_pins_keep_historical_installer_for_fresh_and_repeat_runs(launch, target):
    routes, destination, _, run = launch
    routes[f"{RAW}/{STABLE_BUNDLE}/install.sh"] = child_script()
    first = run([target], {"FLUXOMNI_VERSION": "v26.3.2"})
    assert first.returncode == 0, first.stderr
    destination.mkdir()
    (destination / ".env").write_text("FLUXOMNI_VERSION=v26.3.2\n")
    repeated = run([target])
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout) == {"version": "v26.3.2", "ref": STABLE_BUNDLE, "args": [target]}


@pytest.mark.parametrize("version,ref", [("edge", "main"), ("main", "main"), ("v26.4.0", "v26.4.0")])
def test_new_releases_forward_arguments_and_child_failure(launch, version, ref):
    routes, _, _, run = launch
    routes[f"{RAW}/{ref}/scripts/install-runtime.sh"] = child_script()
    args = ["--install-target", "full", "--capacity-upgrade", "drained"]
    result = run(args, {"FLUXOMNI_VERSION": version, "TEST_CHILD_STATUS": "7"})
    assert result.returncode == 7, result.stderr
    assert json.loads(result.stdout) == {"version": version, "ref": ref, "args": args}


def test_explicit_version_overrides_saved_pin_and_custom_ref_keeps_code_and_assets_together(launch):
    routes, destination, _, run = launch
    destination.mkdir()
    (destination / ".env").write_text("FLUXOMNI_VERSION=v26.3.2\n")
    routes[f"{RAW}/candidate/scripts/install-runtime.sh"] = child_script()
    result = run(["media-node"], {"FLUXOMNI_VERSION": "edge", "FLUXOMNI_SELFHOST_REF": "candidate"})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["ref"] == "candidate"
    assert json.loads(result.stdout)["version"] == "edge"


@pytest.mark.parametrize("version", ["v26.3.2", "edge", "v26.4.0"])
def test_missing_installer_never_falls_back_to_main_or_changes_installation(launch, version):
    routes, destination, requests, run = launch
    routes[f"{RAW}/main/install.sh"] = child_script()
    result = run(values={"FLUXOMNI_VERSION": version})
    assert result.returncode != 0
    assert not destination.exists()
    assert f"{RAW}/main/install.sh" not in requests.read_text().splitlines()


def test_alias_uses_the_same_historical_release_bundle(launch):
    routes, _, _, run = launch
    routes[f"{RAW}/v0.13.0/install.sh"] = child_script()
    result = run(values={"FLUXOMNI_VERSION": "v26.2.4"})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["ref"] == "v0.13.0"


def test_custom_asset_root_requires_current_installer_without_version_map(launch):
    routes, _, requests, run = launch
    routes["https://assets.invalid/scripts/install-runtime.sh"] = child_script()
    result = run(values={"FLUXOMNI_REPO_RAW": "https://assets.invalid", "FLUXOMNI_SELFHOST_REF": "candidate"})
    assert result.returncode == 0, result.stderr
    assert requests.read_text().splitlines() == ["https://assets.invalid/scripts/install-runtime.sh"]


def test_help_needs_no_network_and_legacy_release_rejects_new_enrollment_before_mutation(launch):
    routes, destination, requests, run = launch
    assert run(["--help"]).returncode == 0
    assert not requests.exists()
    routes[f"{RAW}/{STABLE_BUNDLE}/install.sh"] = child_script()
    result = run(["media-node"], {"FLUXOMNI_ENROLLMENT_CODE": "test-code"})
    assert result.returncode != 0
    assert not destination.exists()


def test_release_sync_preserves_old_installer_paths_and_new_releases_use_current_path():
    spec = importlib.util.spec_from_file_location("release_sync", ROOT / "scripts/sync-release-from-fluxomni.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    existing = json.loads((ROOT / "docs/src/release-manifest.json").read_text())
    merged = module.merge_manifest(existing, {"latestStable": "v26.4.0", "releases": {
        "v26.3.2": {"coreVersion": "v26.3.2"}, "v26.4.0": {"coreVersion": "v26.4.0"}}})
    assert merged["releases"]["v26.3.2"]["installerPath"] == "install.sh"
    assert merged["releases"]["v26.3.2"]["installerBundleRef"] == STABLE_BUNDLE
    assert "installerBundleRef" not in merged["releases"]["v26.4.0"]
    assert merged["releases"]["v26.4.0"]["installerPath"] == "scripts/install-runtime.sh"
    assert module.render_version_map(existing) == (ROOT / "scripts/generated-version-map.sh").read_text()
