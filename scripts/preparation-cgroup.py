#!/usr/bin/python3
"""Provision one installation-owned preparation cgroup without changing live limits."""

# @lat: [[installation#Preparation group lifecycle]]
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

CGROUPS = Path("/sys/fs/cgroup")
OWNERS = Path("/var/lib/fluxomni-preparation")
HELPERS = Path("/usr/local/libexec/fluxomni-preparation")
UNITS = Path("/etc/systemd/system")
ROOT_UID = 0
CONTROLLERS = {"cpu", "memory", "pids"}
ATTEMPT = re.compile(
    r"attempt-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)


def identity(installation):
    installation = str(Path(installation).resolve(strict=True))
    key = hashlib.sha256(installation.encode()).hexdigest()[:24]
    return key, {
        "schema": 1,
        "installation": installation,
        "root": str(CGROUPS / ("fluxomni-preparation-" + key)),
    }


def private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if (
        path.is_symlink()
        or path.stat().st_uid != ROOT_UID
        or path.stat().st_mode & 0o022
    ):
        raise RuntimeError("unsafe ownership directory: " + str(path))


def atomic_write(path, contents, mode):
    if path.is_symlink():
        raise RuntimeError("refusing symlink: " + str(path))
    fd, temp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            os.fchmod(stream.fileno(), mode)
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def read_owner(key):
    marker = OWNERS / key / "owner.json"
    if (
        marker.is_symlink()
        or marker.stat().st_uid != ROOT_UID
        or marker.stat().st_mode & 0o077
    ):
        raise RuntimeError("unsafe preparation ownership marker")
    owner = json.loads(marker.read_text())
    installation = owner["installation"]
    if not isinstance(installation, str) or not Path(installation).is_absolute():
        raise RuntimeError("invalid preparation installation identity")
    expected_key = hashlib.sha256(installation.encode()).hexdigest()[:24]
    expected = {
        "schema": 1,
        "installation": installation,
        "root": str(CGROUPS / ("fluxomni-preparation-" + expected_key)),
    }
    if key != expected_key or owner != expected:
        raise RuntimeError("preparation ownership marker does not match installation")
    return owner


def check_host():
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("preparation provisioning requires host Linux root")
    filesystem = subprocess.check_output(
        ["stat", "-fc", "%T", str(CGROUPS)], text=True
    ).strip()
    if filesystem != "cgroup2fs":
        raise RuntimeError("preparation provisioning requires cgroup v2")
    if not CONTROLLERS <= set((CGROUPS / "cgroup.subtree_control").read_text().split()):
        raise RuntimeError("host must already enable cpu, memory and pids controllers")


def validate_root(root):
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("owned preparation root is missing or a symlink")
    if (root / "cgroup.procs").read_text().strip():
        raise RuntimeError("unexpected direct processes in preparation root")
    if not CONTROLLERS <= set((root / "cgroup.controllers").read_text().split()):
        raise RuntimeError("preparation controllers unavailable")
    if not CONTROLLERS <= set((root / "cgroup.subtree_control").read_text().split()):
        raise RuntimeError("preparation subtree controllers unavailable")


def children(root):
    leaves = [entry for entry in root.iterdir() if entry.is_dir() or entry.is_symlink()]
    if any(entry.is_symlink() or not ATTEMPT.fullmatch(entry.name) for entry in leaves):
        raise RuntimeError("unexpected child in preparation root")
    return leaves


def create_root(root):
    root.mkdir()
    try:
        (root / "cgroup.subtree_control").write_text("+cpu +memory +pids")
    except BaseException:
        root.rmdir()
        raise


@contextmanager
def open_directory(root):
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        yield fd
    finally:
        os.close(fd)


def ensure_root(key, owner, new=False):
    root = Path(owner["root"])
    if root.exists() or root.is_symlink():
        if new:
            raise RuntimeError("refusing existing unowned preparation subtree")
        validate_root(root)
        # The runtime has exclusive ownership. A busy lock permits read-only
        # reruns, without enumerating leaves that it may concurrently delete.
        with open_directory(root) as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return root
            children(root)
    else:
        create_root(root)
    return root


def unit_text(key):
    helper = HELPERS / key / "prepare.py"
    return f"""[Unit]
Description=Fluxomni preparation cgroup {key}
DefaultDependencies=no
RequiresMountsFor={HELPERS / key} {OWNERS / key}
After=local-fs.target
Before=docker.service docker.socket

[Service]
Type=oneshot
ExecStart={helper} ensure {key}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""


def systemctl(*args):
    subprocess.run(["systemctl", *args], check=True, stdout=subprocess.DEVNULL)


def perform(action, argument):
    check_host()
    if action in ("install", "disable"):
        key, expected = identity(argument)
    else:
        key = argument
        expected = None
    if not re.fullmatch("[0-9a-f]{24}", key):
        raise RuntimeError("invalid preparation installation identity")
    private_directory(OWNERS)
    private_directory(OWNERS / key)
    lock_path = OWNERS / key / "operation.lock"
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, "wb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = OWNERS / key / "owner.json"
        new = not marker.exists() and not marker.is_symlink()
        if new and action != "install":
            raise RuntimeError("preparation ownership marker missing")
        owner = expected if new else read_owner(key)
        if expected is not None and owner != expected:
            raise RuntimeError("installation already has a different preparation owner")
        unit = UNITS / f"fluxomni-preparation-{key}.service"
        helper_dir = HELPERS / key
        if new and (
            unit.exists()
            or unit.is_symlink()
            or helper_dir.exists()
            or helper_dir.is_symlink()
        ):
            raise RuntimeError("refusing existing unowned preparation unit/helper")
        if action == "install":
            root = ensure_root(key, owner, new=new)
            if new:
                try:
                    atomic_write(marker, (json.dumps(owner) + "\n").encode(), 0o600)
                except BaseException:
                    root.rmdir()
                    raise
            private_directory(HELPERS)
            private_directory(helper_dir)
            atomic_write(helper_dir / "prepare.py", Path(__file__).read_bytes(), 0o755)
            atomic_write(unit, unit_text(key).encode(), 0o644)
            systemctl("daemon-reload")
            systemctl("enable", unit.name)
            # ensure was already run under this operation lock; starting a unit
            # while holding it would deadlock its second ensure invocation.
        elif action == "ensure":
            root = ensure_root(key, owner)
        elif action == "disable":
            systemctl("disable", unit.name)
            root = Path(owner["root"])
        elif action == "cleanup":
            root = Path(owner["root"])
            validate_root(root)
            with open_directory(root) as directory:
                try:
                    fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise RuntimeError("stop the media node before cleanup") from exc
                leaves = children(root)
                systemctl("disable", unit.name)
                for leaf in leaves:
                    (leaf / "cgroup.kill").write_text("1")
                    deadline = time.monotonic() + 5
                    while "populated 0" not in (leaf / "cgroup.events").read_text():
                        if time.monotonic() >= deadline:
                            raise RuntimeError("preparation descendants did not drain")
                        time.sleep(0.02)
                    leaf.rmdir()
                root.rmdir()
        else:
            raise RuntimeError("expected install, ensure, disable or cleanup")
    if action == "install":
        systemctl("start", unit.name)
    return root


def main():
    try:
        if len(sys.argv) != 3:
            raise RuntimeError(
                "usage: preparation-cgroup.py install|disable INSTALL_DIR; ensure|cleanup INSTALL_HASH"
            )
        print(perform(*sys.argv[1:]))
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
