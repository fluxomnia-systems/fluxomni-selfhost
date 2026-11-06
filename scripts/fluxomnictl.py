#!/usr/bin/env python3
"""Fluxomni local admin tool for self-hosted installs.

One tool serves every install on this host. It finds the install folder by
itself, so it works from any directory.
"""

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

TARGETS = ("full", "media-node")
DEFAULT_FOLDERS = {"full": "fluxomni", "media-node": "fluxomni-media-node"}


class CtlError(Exception):
    """A safe, credential-free failure shown to the operator."""


class Install:
    """One existing install folder and its target."""

    def __init__(self, path, target):
        self.path = Path(path)
        self.target = target

    def __repr__(self):
        return f"{self.path} ({self.target})"


def service_pattern(name):
    return re.compile(r"^[ \t]*[\"']?" + re.escape(name) + r"[\"']?[ \t]*:", re.MULTILINE)


CONTROL_PLANE = service_pattern("control-plane")
MEDIA_NODE = service_pattern("media-node")


def compose_text(path):
    """Read every regular Compose file in an install folder, ignoring bad ones."""
    texts = []
    for item in sorted(path.glob("*.yml")):
        if not (item.name.startswith(("docker-compose", "compose"))):
            continue
        try:
            if item.is_file() and not item.is_symlink():
                texts.append(item.read_text(errors="replace"))
        except OSError:
            continue
    return "\n".join(texts)


def install_target(path):
    """Return the target of an install folder, or None when it is not one.

    Reads all Compose files because the installer splits them into release,
    defaults, and overlay files. Needs a media-node service in every install.
    """
    path = Path(path)
    try:
        if not (path / ".env").is_file():
            return None
        text = compose_text(path)
    except OSError:
        return None
    if not MEDIA_NODE.search(text):
        return None
    return "full" if CONTROL_PLANE.search(text) else "media-node"


def home_directory(environ):
    home = environ.get("HOME")
    return Path(home) if home else Path.home()


def candidate_folders(home, target):
    names = [target] if target else list(TARGETS)
    return [(home / DEFAULT_FOLDERS[name]) for name in names]


def describe(installs):
    return ", ".join(str(item.path) for item in installs)


def select_install(directory=None, target=None, cwd=None, environ=None, interactive=False, ask=input):
    """Pick one install by explicit folder, current folder, or default folders.

    Order: --dir, FLUXOMNI_DIR, current folder, then the default folders.
    Two matches ask on a terminal and fail with both paths otherwise.
    """
    environ = os.environ if environ is None else environ
    cwd = Path(cwd or os.getcwd())
    source = "--dir" if directory is not None else "FLUXOMNI_DIR"
    explicit = directory if directory is not None else environ.get("FLUXOMNI_DIR")
    if explicit is not None and not explicit.strip():
        raise CtlError(f"{source} is empty")
    if explicit:
        if explicit == "~" or explicit.startswith("~/"):
            explicit = str(home_directory(environ) / explicit[2:])
        explicit = str(Path(explicit).resolve())
        found = install_target(explicit)
        if found is None:
            raise CtlError(f"{explicit} (from {source}) is not a Fluxomni install folder: it needs .env and Compose files with a media-node service")
        if target and found != target:
            raise CtlError(f"{explicit} is a {found} install, not {target}")
        return Install(explicit, found)
    found = install_target(cwd.resolve())
    if found and (not target or found == target):
        return Install(cwd.resolve(), found)
    home = home_directory(environ)
    installs = []
    seen = set()
    for folder in candidate_folders(home, target):
        real = folder.resolve()
        kind = install_target(real)
        if kind and (not target or kind == target) and real not in seen:
            seen.add(real)
            installs.append(Install(real, kind))
    if not installs:
        checked = ", ".join(str(folder) for folder in candidate_folders(home, target))
        raise CtlError(f"no Fluxomni install found. Checked: {checked}. Use --dir to select one")
    if len(installs) == 1:
        return installs[0]
    if not interactive:
        raise CtlError(f"more than one install found: {describe(installs)}. Use --dir or --target to select one")
    for number, item in enumerate(installs, 1):
        print(f"  {number}) {item.path} ({item.target})", file=sys.stderr)
    try:
        answer = ask(f"Select an install [1-{len(installs)}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise CtlError("no install selected") from None
    if not answer.isdigit() or not 1 <= int(answer) <= len(installs):
        raise CtlError("no install selected")
    return installs[int(answer) - 1]


CONTROLLERS = ("cpu", "memory", "pids")
CGROUP_ROOT = Path("/sys/fs/cgroup")
SYSTEMD_DROPIN = Path("/etc/systemd/system.conf.d/fluxomni-preparation.conf")
DROPIN_TEXT = (
    "# Written by fluxomnictl for Fluxomni offline preparation limits.\n"
    "[Manager]\nDefaultCPUAccounting=yes\nDefaultMemoryAccounting=yes\nDefaultTasksAccounting=yes\n"
)
BUDGET_LIMITS = {"CPU": (50, 256000), "MEMORY": (256, 1048576), "TASKS": (64, 4194304)}


class Host:
    """The real host. Tests replace it with a fake."""

    def system(self):
        return platform.system()

    def euid(self):
        return os.geteuid()

    def which(self, name):
        return shutil.which(name)

    def executable(self, path):
        return os.access(path, os.X_OK)

    def read(self, path):
        return Path(path).read_text()

    def write(self, path, text):
        """Replace the file atomically with mode 0644; refuse symlinked targets."""
        path = Path(path)
        if path.is_symlink() or path.parent.is_symlink():
            raise OSError(f"refusing to write through a symlink: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(text)
        temporary.chmod(0o644)
        os.replace(temporary, path)

    def run(self, args, timeout=30):
        """Return (status, output); 127 when the command does not exist."""
        try:
            done = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            return 127, ""
        except subprocess.TimeoutExpired:
            return 124, ""
        return done.returncode, (done.stdout + done.stderr).strip()

    def cpus(self):
        return os.cpu_count() or 1

    def memory_mib(self):
        try:
            for line in self.read("/proc/meminfo").splitlines():
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) // 1024
        except (OSError, ValueError):
            pass
        return 0


class Check:
    """One host requirement result with the command that fixes it."""

    def __init__(self, label, ok, detail="", fix=""):
        self.label, self.ok, self.detail, self.fix = label, ok, detail, fix


def check_controllers(host):
    """Report which of cpu, memory, pids are missing from the root subtree."""
    try:
        available = set(host.read(CGROUP_ROOT / "cgroup.controllers").split())
        enabled = set(host.read(CGROUP_ROOT / "cgroup.subtree_control").split())
    except OSError:
        return None, None
    return [c for c in CONTROLLERS if c not in available], [c for c in CONTROLLERS if c not in enabled]


def preparation_checks(host, environ=None):
    """Run every host requirement and return all results, never stopping early."""
    environ = os.environ if environ is None else environ
    results = []
    linux = host.system() == "Linux"
    results.append(Check("Linux host", linux, host.system(), "Offline preparation limits need a Linux host."))
    results.append(Check("Root or sudo", host.euid() == 0 or bool(host.which("sudo")), "",
                         "Run as root, or install sudo and use it."))
    results.append(Check("/usr/bin/python3", host.executable("/usr/bin/python3"), "",
                         "Install python3 so that /usr/bin/python3 exists (for example: apt-get install python3)."))
    systemd = bool(host.which("systemctl")) and host.run(["systemctl", "show-environment"])[0] == 0
    results.append(Check("systemd", systemd, "", "The boot setup for the cgroup needs systemd (systemctl)."))
    if not host.which("docker"):
        results.append(Check("Docker", False, "", "Install Docker Engine, then run the install again."))
    else:
        # Same order as the installer: DOCKER_CONTEXT, then DOCKER_HOST, then the current context.
        status, context, endpoint = 0, environ.get("DOCKER_CONTEXT", ""), environ.get("DOCKER_HOST", "")
        if not context and not endpoint:
            status, context = host.run(["docker", "context", "show"])
        if status == 0 and not endpoint:
            status, endpoint = host.run(["docker", "context", "inspect", context, "--format", "{{.Endpoints.docker.Host}}"])
        if status != 0:
            endpoint = "docker context failed"
        results.append(Check("Local Docker socket", status == 0 and endpoint.startswith("unix://"), endpoint,
                             "Use the local Docker daemon (docker context use default) and unset DOCKER_HOST."))
        status, info = host.run(["docker", "info", "--format", "{{.CgroupVersion}} {{json .SecurityOptions}}"])
        rootful = status == 0 and info.startswith("2 ") and "rootless" not in info and "userns" not in info
        results.append(Check("Docker uses cgroup v2, rootful, no userns remap", rootful, info if status == 0 else "docker info failed",
                             "Docker must be rootful on cgroup v2 without user namespace remapping. See the Fluxomni preparation guide."))
    cgroup2 = False
    if linux:
        status, kind = host.run(["stat", "-fc", "%T", str(CGROUP_ROOT)])
        cgroup2 = status == 0 and kind == "cgroup2fs"
    results.append(Check("Host cgroup v2", cgroup2, "", "Boot with cgroup v2 (systemd.unified_cgroup_hierarchy=1) and reboot."))
    missing, disabled = check_controllers(host) if cgroup2 else (None, None)
    if missing is None:
        results.append(Check("cpu, memory, pids controllers", False, "unreadable", "Fix the cgroup v2 check above first."))
    elif missing:
        results.append(Check("cpu, memory, pids controllers", False, "not offered by the kernel: " + ", ".join(missing),
                             "The kernel must offer cpu, memory, and pids (boot with cgroup_enable=memory if needed) and reboot."))
    elif disabled:
        results.append(Check("cpu, memory, pids controllers", False, "not enabled: " + ", ".join(disabled),
                             "Run: fluxomnictl preparation check --enable-controllers"))
    else:
        results.append(Check("cpu, memory, pids controllers", True))
    return results


def print_checks(results, out=None):
    out = out or sys.stdout
    for item in results:
        mark = "ok  " if item.ok else "FAIL"
        suffix = f" ({item.detail})" if item.detail and not item.ok else ""
        print(f"  [{mark}] {item.label}{suffix}", file=out)
        if not item.ok and item.fix:
            print(f"         fix: {item.fix}", file=out)
    failed = [item for item in results if not item.ok]
    print(f"{len(results) - len(failed)} of {len(results)} checks passed.", file=out)
    return not failed


def enable_controllers(host, confirm):
    """Persist cpu/memory/pids accounting in systemd, only after confirmation.

    Never writes cgroup files directly. If systemd does not offer the
    controllers after a re-exec, the host needs a reboot; say so and stop.
    """
    if host.euid() != 0:
        raise CtlError("changing the host needs root. Run: sudo fluxomnictl preparation check --enable-controllers")
    missing, disabled = check_controllers(host)
    if missing is None:
        raise CtlError("cgroup v2 is not readable on this host")
    if missing:
        raise CtlError("the kernel does not offer: " + ", ".join(missing) + ". Enable them at boot, then reboot")
    if not disabled:
        print("The cpu, memory, and pids controllers are already enabled.")
        return
    print(f"This will write {SYSTEMD_DROPIN} (CPU, memory, and tasks accounting)")
    print("and run: systemctl daemon-reexec. This is a host-wide setting. It is never removed automatically.")
    if not confirm("Apply this change? [y/N] "):
        raise CtlError("not changed: the change was not confirmed")
    try:
        host.write(SYSTEMD_DROPIN, DROPIN_TEXT)
    except OSError as error:
        raise CtlError(f"cannot write {SYSTEMD_DROPIN}: {error}") from None
    status, output = host.run(["systemctl", "daemon-reexec"])
    if status != 0:
        raise CtlError("systemctl daemon-reexec failed: " + output)
    missing, disabled = check_controllers(host)
    if disabled:
        raise CtlError(
            "the setting is saved but not active yet (" + ", ".join(disabled) + "). Reboot the host, then run the check again")
    print("The cpu, memory, and pids controllers are enabled.")


def validate_budget(label, value):
    """Same bounds as the installer: a plain positive integer in range."""
    low, high = BUDGET_LIMITS[label]
    text = str(value)
    if not re.fullmatch(r"[1-9][0-9]{0,6}", text) or not low <= int(text) <= high:
        raise CtlError(f"preparation {label.lower()} must be a whole number from {low} to {high}")
    return int(text)


def suggest_budgets(cpus, memory_mib):
    """About 25% of CPU and RAM with a floor and a ceiling, and 256 tasks."""
    cpu = int(cpus * 1000 * 0.25) // 50 * 50
    memory = int(memory_mib * 0.25)
    return {
        "CPU": min(max(cpu, 250), 64000),
        "MEMORY": min(max(memory, 512), 262144),
        "TASKS": 256,
    }


def run_check(args, host, interactive, ask, environ=None):
    """Run the host checks, optionally enabling controllers first."""
    if args.enable_controllers:
        def confirm(question):
            if args.yes:
                return True
            if not interactive:
                raise CtlError("confirmation needs a terminal; use --yes to confirm")
            return ask(question).strip().lower() in ("y", "yes")
        enable_controllers(host, confirm)
    return 0 if print_checks(preparation_checks(host, environ)) else 1


def build_parser():
    parser = argparse.ArgumentParser(prog="fluxomnictl", description=__doc__)
    parser.add_argument("--dir", help="install folder (default: find it automatically)")
    parser.add_argument("--target", choices=TARGETS, help="only consider installs of this target")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    commands.add_parser("where", help="print the selected install folder and target")
    preparation = commands.add_parser("preparation", help="offline preparation limits")
    actions = preparation.add_subparsers(dest="action", metavar="ACTION", required=True)
    check = actions.add_parser("check", help="check every host requirement and list all problems")
    check.add_argument("--enable-controllers", action="store_true", help="enable missing cpu/memory/pids controllers after confirmation")
    check.add_argument("--yes", action="store_true", help="confirm without asking")
    return parser


def main(argv=None, environ=None, cwd=None, interactive=None, host=None, ask=input):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    interactive = sys.stdin.isatty() and sys.stderr.isatty() if interactive is None else interactive
    host = host or Host()
    try:
        if args.command == "preparation" and args.action == "check":
            return run_check(args, host, interactive, ask, environ)
        install = select_install(args.dir, args.target, cwd, environ, interactive, ask)
        if args.command == "where":
            print(f"{install.path} {install.target}")
    except CtlError as error:
        print(f"Error: {error}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
