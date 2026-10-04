"""Exercise preparation provisioning ownership and reboot/rerun contracts."""

import fcntl
import importlib.util
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def host(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "preparation", ROOT / "scripts/preparation-cgroup.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("CGROUPS", "OWNERS", "HELPERS", "UNITS"):
        path = tmp_path / name.lower()
        path.mkdir()
        monkeypatch.setattr(module, name, path)
    monkeypatch.setattr(module, "ROOT_UID", os.getuid())
    monkeypatch.setattr(module, "check_host", lambda: None)
    calls = []
    monkeypatch.setattr(module, "systemctl", lambda *args: calls.append(args))

    def create(root):
        root.mkdir()
        for name, value in {
            "cgroup.procs": "",
            "cgroup.controllers": "cpu memory pids",
            "cgroup.subtree_control": "cpu memory pids",
            "cpu.max": "max 100000",
            "memory.max": "max",
            "pids.max": "max",
        }.items():
            (root / name).write_text(value)

    monkeypatch.setattr(module, "create_root", create)
    install = tmp_path / "install"
    install.mkdir()
    return module, install, calls


# @lat: [[installation#Preparation provisioning regression coverage]]
def test_owned_rerun_and_reboot_recreation_preserve_runtime_limits(host):
    module, install, calls = host
    root = module.perform("install", str(install))
    key, owner = module.identity(install)
    marker = module.OWNERS / key / "owner.json"
    assert json.loads(marker.read_text()) == owner
    assert marker.stat().st_mode & 0o777 == 0o600
    unit = (module.UNITS / f"fluxomni-preparation-{key}.service").read_text()
    assert "Before=docker.service docker.socket" in unit
    assert "After=local-fs.target" in unit
    assert "ExecStop=" not in unit
    assert f"ExecStart={module.HELPERS / key / 'prepare.py'} ensure {key}" in unit
    assert ("enable", f"fluxomni-preparation-{key}.service") in calls
    (root / "cpu.max").write_text("50000 100000")
    module.perform("install", str(install))
    assert (root / "cpu.max").read_text() == "50000 100000"
    module.perform("disable", str(install))
    assert root.exists() and marker.exists()
    assert ("disable", f"fluxomni-preparation-{key}.service") in calls
    for path in root.iterdir():
        path.unlink()
    root.rmdir()
    assert module.perform("ensure", key).exists()
    assert (root / "cpu.max").read_text() == "max 100000"


def test_live_runtime_rerun_does_not_enumerate_attempts_or_change_limits(
    host, monkeypatch
):
    module, install, _ = host
    root = module.perform("install", str(install))
    with module.open_directory(root) as fd:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        monkeypatch.setattr(
            module,
            "children",
            lambda _: pytest.fail("must not enumerate a live runtime"),
        )
        assert module.perform("install", str(install)) == root
        key, _ = module.identity(install)
        with pytest.raises(RuntimeError, match="stop the media node"):
            module.perform("cleanup", key)
    assert (root / "cpu.max").read_text() == "max 100000"


@pytest.mark.parametrize(
    "kind",
    [
        "unmarked",
        "symlink",
        "unexpected-child",
        "direct-process",
        "missing-controller",
        "marker-mismatch",
    ],
)
def test_refuses_foreign_or_corrupt_group_without_touching_limits(host, kind):
    module, install, _ = host
    key, owner = module.identity(install)
    root = Path(owner["root"])
    if kind == "unmarked":
        module.create_root(root)
    else:
        module.perform("install", str(install))
        if kind == "symlink":
            alternate = root.with_name("foreign")
            root.rename(alternate)
            root.symlink_to(alternate, target_is_directory=True)
        elif kind == "unexpected-child":
            (root / "foreign-child").mkdir()
        elif kind == "direct-process":
            (root / "cgroup.procs").write_text("1234")
        elif kind == "missing-controller":
            (root / "cgroup.controllers").write_text("cpu memory")
        elif kind == "marker-mismatch":
            marker = module.OWNERS / key / "owner.json"
            value = json.loads(marker.read_text())
            value["root"] = "/sys/fs/cgroup/foreign"
            marker.write_text(json.dumps(value))
    with pytest.raises(RuntimeError):
        module.perform("install", str(install))
    assert (root / "cpu.max").read_text() == "max 100000"


def test_different_install_directories_have_independent_budgets(host):
    module, install, _ = host
    other = install.parent / "other-install"
    other.mkdir()
    first = module.perform("install", str(install))
    second = module.perform("install", str(other))
    assert first != second
    assert module.identity(install / ".." / "install") == module.identity(install)


def test_failed_first_provision_does_not_claim_foreign_group(host, monkeypatch):
    module, install, _ = host

    def fail(_):
        raise OSError("provisioning failed")

    monkeypatch.setattr(module, "create_root", fail)
    with pytest.raises(OSError):
        module.perform("install", str(install))
    key, _ = module.identity(install)
    assert not (module.OWNERS / key / "owner.json").exists()


def test_marker_symlink_is_not_followed(host):
    module, install, _ = host
    module.perform("install", str(install))
    key, _ = module.identity(install)
    marker = module.OWNERS / key / "owner.json"
    foreign = marker.with_name("foreign.json")
    marker.rename(foreign)
    marker.symlink_to(foreign)
    with pytest.raises(RuntimeError, match="unsafe preparation ownership marker"):
        module.perform("install", str(install))
