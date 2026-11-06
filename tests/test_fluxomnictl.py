"""Verify fluxomnictl finds the right install folder from any directory."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fluxomnictl", ROOT / "scripts/fluxomnictl.py")
ctl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ctl)


def make_install(path, target):
    path.mkdir(parents=True)
    (path / ".env").write_text("FLUXOMNI_VERSION=26.4.0\n")
    services = "services:\n  media-node:\n    image: x\n"
    if target == "full":
        services += "  control-plane:\n    image: y\n"
    (path / "docker-compose.yml").write_text(services)
    return path


@pytest.fixture
def home(tmp_path):
    folder = tmp_path / "home"
    folder.mkdir()
    return folder


def select(home, **options):
    environ = {"HOME": str(home), **options.pop("environ", {})}
    return ctl.select_install(environ=environ, cwd=options.pop("cwd", home), **options)


def test_no_install_lists_checked_folders(home):
    with pytest.raises(ctl.CtlError, match="Checked: .*fluxomni, .*fluxomni-media-node"):
        select(home)


def test_one_install_is_selected_without_flags(home):
    make_install(home / "fluxomni", "full")
    found = select(home)
    assert (found.path, found.target) == (home / "fluxomni", "full")


def test_two_installs_fail_with_both_paths_without_terminal(home):
    make_install(home / "fluxomni", "full")
    make_install(home / "fluxomni-media-node", "media-node")
    with pytest.raises(ctl.CtlError) as error:
        select(home)
    assert str(home / "fluxomni") in str(error.value)
    assert str(home / "fluxomni-media-node") in str(error.value)


def test_two_installs_prompt_on_a_terminal(home):
    make_install(home / "fluxomni", "full")
    make_install(home / "fluxomni-media-node", "media-node")
    found = select(home, interactive=True, ask=lambda _: "2")
    assert found.target == "media-node"
    with pytest.raises(ctl.CtlError, match="no install selected"):
        select(home, interactive=True, ask=lambda _: "9")


def test_target_filters_candidates(home):
    make_install(home / "fluxomni", "full")
    make_install(home / "fluxomni-media-node", "media-node")
    assert select(home, target="full").target == "full"
    assert select(home, target="media-node").path == home / "fluxomni-media-node"


def test_order_dir_then_environment_then_current_folder_then_defaults(home, tmp_path):
    default = make_install(home / "fluxomni", "full")
    here = make_install(tmp_path / "here", "media-node")
    chosen = make_install(tmp_path / "chosen", "full")
    env = make_install(tmp_path / "env", "full")
    assert select(home, cwd=here).path == here
    assert select(home, cwd=here, environ={"FLUXOMNI_DIR": str(env)}).path == env
    assert select(home, cwd=here, directory=str(chosen), environ={"FLUXOMNI_DIR": str(env)}).path == chosen
    assert select(home, cwd=tmp_path).path == default


def test_explicit_folder_must_be_an_install_of_the_requested_target(home, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(ctl.CtlError, match="not a Fluxomni install folder"):
        select(home, directory=str(plain))
    node = make_install(tmp_path / "node", "media-node")
    with pytest.raises(ctl.CtlError, match="media-node install, not full"):
        select(home, directory=str(node), target="full")


def test_where_prints_folder_and_target(home, capsys):
    make_install(home / "fluxomni", "full")
    assert ctl.main(["where"], environ={"HOME": str(home)}, cwd=home, interactive=False) == 0
    assert capsys.readouterr().out.strip() == f"{home / 'fluxomni'} full"
    assert ctl.main(["where"], environ={"HOME": str(home / "none")}, cwd=home, interactive=False) == 1


def test_real_installer_layout_with_include_wrapper_and_overlays(home):
    node = make_install(home / "fluxomni-media-node", "media-node")
    (node / "docker-compose.yml").write_text("include:\n  - path:\n      - compose.defaults.yml\n      - compose.release.yml\n")
    (node / "compose.defaults.yml").write_text("services:\n  media-node:\n    ulimits: {}\n")
    (node / "compose.release.yml").write_text("services:\n  media-node:\n    image: x\n")
    assert select(home).target == "media-node"
    full = make_install(home / "fluxomni", "full")
    (full / "docker-compose.yml").write_text("include:\n  - path: compose.release.yml\n")
    (full / "compose.release.yml").write_text('services:\n    "control-plane":\n        image: y\n    media-node:\n        image: x\n')
    assert select(home, target="full").target == "full"


def test_comment_does_not_make_a_full_install_and_media_node_is_required(home):
    node = make_install(home / "fluxomni-media-node", "media-node")
    (node / "docker-compose.yml").write_text("services:\n  media-node: {}\n#  control-plane:\n")
    assert select(home).target == "media-node"
    (node / "docker-compose.yml").write_text("services:\n  other: {}\n")
    with pytest.raises(ctl.CtlError, match="no Fluxomni install found"):
        select(home)


def test_unreadable_or_broken_folders_are_skipped(home):
    broken = make_install(home / "fluxomni", "full")
    (broken / "docker-compose.yml").unlink()
    (broken / "docker-compose.yml").mkdir()
    make_install(home / "fluxomni-media-node", "media-node")
    assert select(home).target == "media-node"


def test_symlinked_default_folders_to_one_install_are_not_ambiguous(home):
    real = make_install(home / "real", "full")
    (home / "fluxomni").symlink_to(real)
    (home / "fluxomni-media-node").symlink_to(real)
    assert select(home).path == real.resolve()


def test_wrong_target_in_current_folder_falls_through_to_defaults(home, tmp_path):
    here = make_install(tmp_path / "here", "media-node")
    make_install(home / "fluxomni", "full")
    assert select(home, cwd=here, target="full").path == home / "fluxomni"


def test_empty_and_home_relative_explicit_folders(home, tmp_path):
    with pytest.raises(ctl.CtlError, match="--dir is empty"):
        select(home, directory="")
    with pytest.raises(ctl.CtlError, match="FLUXOMNI_DIR is empty"):
        select(home, environ={"FLUXOMNI_DIR": " "})
    make_install(home / "x", "full")
    assert select(home, directory="~/x", environ={"HOME": str(home)}).path == (home / "x").resolve()


def test_prompt_end_of_input_is_a_clean_failure(home):
    make_install(home / "fluxomni", "full")
    make_install(home / "fluxomni-media-node", "media-node")

    def closed(_):
        raise EOFError

    with pytest.raises(ctl.CtlError, match="no install selected"):
        select(home, interactive=True, ask=closed)


class FakeHost(ctl.Host):
    """Scriptable host: a file map and a command table."""

    def __init__(self, files=None, commands=None, system="Linux", euid=0, tools=("docker", "systemctl", "sudo", "stat"), cpus=8, mem=16384):
        self.files = dict(files or {})
        self.commands = dict(commands or {})
        self._system, self._euid, self.tools = system, euid, set(tools)
        self.ran, self._cpus, self._mem, self.python, self.written = [], cpus, mem, True, []

    def system(self):
        return self._system

    def euid(self):
        return self._euid

    def which(self, name):
        return name if name in self.tools else None

    def executable(self, path):
        return self.python

    def read(self, path):
        try:
            return self.files[str(path)]
        except KeyError:
            raise FileNotFoundError(path) from None

    def write(self, path, text):
        self.written.append(str(path))
        self.files[str(path)] = text

    def run(self, args, timeout=30, cwd=None):
        self.ran.append(list(args))
        handler = self.commands.get(args[0] + (" " + args[1] if len(args) > 1 else ""), self.commands.get(args[0]))
        return handler(args) if callable(handler) else (handler or (0, ""))

    def cpus(self):
        return self._cpus

    def memory_mib(self):
        return self._mem


GOOD_COMMANDS = {
    "systemctl show-environment": (0, ""),
    "docker context": lambda args: (0, "default") if args[2] == "show" else (0, "unix:///var/run/docker.sock"),
    "docker info": (0, '2 ["name=seccomp,profile=builtin","name=cgroupns"]'),
    "stat": (0, "cgroup2fs"),
}


def good_host(enabled="cpu memory pids", **options):
    files = {
        "/sys/fs/cgroup/cgroup.controllers": "cpuset cpu io memory pids",
        "/sys/fs/cgroup/cgroup.subtree_control": enabled,
    }
    return FakeHost(files=files, commands=dict(GOOD_COMMANDS), **options)


def test_good_host_passes_every_check(monkeypatch):
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    results = ctl.preparation_checks(good_host(), {})
    assert all(item.ok for item in results), [(i.label, i.detail) for i in results if not i.ok]
    assert len(results) == 8


def test_all_failures_are_reported_together_with_fixes(monkeypatch, capsys):
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    host = FakeHost(system="Darwin", euid=1000, tools=(), commands={})
    host.python = False
    results = ctl.preparation_checks(host, {})
    failed = [item.label for item in results if not item.ok]
    assert {"Linux host", "Root or sudo", "/usr/bin/python3", "systemd", "Docker", "Host cgroup v2"} <= set(failed)
    assert ctl.print_checks(results) is False
    output = capsys.readouterr().out
    assert output.count("fix:") == len(failed)
    assert "checks passed" in output


def test_rootless_userns_and_remote_docker_are_refused(monkeypatch):
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    for info in ('2 ["name=rootless"]', '2 ["name=userns"]', '1 ["name=seccomp"]'):
        host = good_host()
        host.commands["docker info"] = (0, info)
        assert not next(i for i in ctl.preparation_checks(host, {}) if i.label.startswith("Docker uses")).ok
    remote = {"DOCKER_HOST": "tcp://remote:2375"}
    assert not next(i for i in ctl.preparation_checks(good_host(), remote) if i.label == "Local Docker socket").ok
    named = good_host()
    named.commands["docker context"] = lambda args: (0, "ssh://box") if args[2] == "inspect" else (0, "default")
    assert not next(i for i in ctl.preparation_checks(named, {}) if i.label == "Local Docker socket").ok
    pinned = {"DOCKER_CONTEXT": "local"}
    assert next(i for i in ctl.preparation_checks(good_host(), pinned) if i.label == "Local Docker socket").ok
    failing = good_host()
    failing.commands["docker context"] = (1, "boom")
    result = next(i for i in ctl.preparation_checks(failing, {}) if i.label == "Local Docker socket")
    assert not result.ok and result.detail == "docker context failed"


def test_missing_controllers_name_the_fix(monkeypatch):
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    item = next(i for i in ctl.preparation_checks(good_host(enabled="cpuset"), {}) if "controllers" in i.label)
    assert not item.ok and "--enable-controllers" in item.fix and item.detail == "not enabled: cpu, memory, pids"


def test_enable_controllers_needs_confirmation_and_never_writes_cgroup_files():
    host = good_host(enabled="cpuset")
    with pytest.raises(ctl.CtlError, match="not confirmed"):
        ctl.enable_controllers(host, lambda _: False)
    assert str(ctl.SYSTEMD_DROPIN) not in host.files and not host.ran

    def reexec(args):
        host.files["/sys/fs/cgroup/cgroup.subtree_control"] = "cpuset cpu memory pids"
        return 0, ""

    host.commands["systemctl daemon-reexec"] = reexec
    ctl.enable_controllers(host, lambda _: True)
    assert host.files[str(ctl.SYSTEMD_DROPIN)] == ctl.DROPIN_TEXT
    assert ["systemctl", "daemon-reexec"] in host.ran
    assert host.written == [str(ctl.SYSTEMD_DROPIN)]


def test_enable_controllers_says_reboot_when_systemd_does_not_apply_it():
    host = good_host(enabled="cpuset")
    with pytest.raises(ctl.CtlError, match="Reboot the host"):
        ctl.enable_controllers(host, lambda _: True)
    assert str(ctl.SYSTEMD_DROPIN) in host.files


def test_enable_controllers_refuses_kernel_gaps_and_skips_when_enabled(capsys):
    host = good_host()
    host.files["/sys/fs/cgroup/cgroup.controllers"] = "cpu memory"
    host.files["/sys/fs/cgroup/cgroup.subtree_control"] = ""
    with pytest.raises(ctl.CtlError, match="kernel does not offer: pids"):
        ctl.enable_controllers(host, lambda _: True)
    ctl.enable_controllers(good_host(), lambda _: pytest.fail("must not ask"))
    assert "already enabled" in capsys.readouterr().out


def test_check_command_exit_codes_and_noninteractive_confirmation(monkeypatch, capsys):
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    assert ctl.main(["preparation", "check"], host=good_host(), interactive=False) == 0
    assert ctl.main(["preparation", "check"], host=good_host(enabled=""), interactive=False) == 1
    assert ctl.main(["preparation", "check", "--enable-controllers"], host=good_host(enabled=""), interactive=False) == 1
    assert "use --yes to confirm" in capsys.readouterr().err


def test_budget_validation_matches_the_installer_bounds():
    assert ctl.validate_budget("CPU", "500") == 500
    for label, bad in [("CPU", "0"), ("CPU", "49"), ("CPU", "256001"), ("CPU", "1e3"), ("CPU", "$(id)"), ("MEMORY", "255"), ("TASKS", "-1"), ("TASKS", "")]:
        with pytest.raises(ctl.CtlError):
            ctl.validate_budget(label, bad)


def test_suggested_budgets_have_a_floor_and_a_ceiling():
    assert ctl.suggest_budgets(8, 16384) == {"CPU": 2000, "MEMORY": 4096, "TASKS": 256}
    assert ctl.suggest_budgets(1, 512) == {"CPU": 250, "MEMORY": 512, "TASKS": 256}
    huge = ctl.suggest_budgets(1024, 8 * 1024 * 1024)
    assert huge["CPU"] == 64000 and huge["MEMORY"] == 262144
    for label, value in huge.items():
        assert ctl.validate_budget(label, value) == value


def test_enable_controllers_needs_root_and_maps_write_errors(tmp_path):
    with pytest.raises(ctl.CtlError, match="needs root"):
        ctl.enable_controllers(good_host(enabled="cpuset", euid=1000), lambda _: True)
    host = good_host(enabled="cpuset")

    def refuse(path, text):
        raise PermissionError("denied")

    host.write = refuse
    with pytest.raises(ctl.CtlError, match="cannot write"):
        ctl.enable_controllers(host, lambda _: True)
    assert not host.ran
    host = good_host(enabled="cpuset")
    host.commands["systemctl daemon-reexec"] = (1, "failed")
    with pytest.raises(ctl.CtlError, match="daemon-reexec failed"):
        ctl.enable_controllers(host, lambda _: True)


def test_yes_confirms_without_a_terminal(monkeypatch):
    host = good_host(enabled="cpuset")
    host.commands["systemctl daemon-reexec"] = lambda args: (host.files.update({"/sys/fs/cgroup/cgroup.subtree_control": "cpu memory pids"}), (0, ""))[1]
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    assert ctl.main(["preparation", "check", "--enable-controllers", "--yes"], host=host, interactive=False) == 0


def test_real_host_write_is_atomic_and_refuses_symlinks(tmp_path):
    target = tmp_path / "conf.d" / "x.conf"
    ctl.Host().write(target, "one\n")
    ctl.Host().write(target, "two\n")
    assert target.read_text() == "two\n" and oct(target.stat().st_mode & 0o777) == "0o644"
    assert not list(target.parent.glob("*.tmp"))
    link = tmp_path / "link.conf"
    link.symlink_to(target)
    with pytest.raises(OSError, match="symlink"):
        ctl.Host().write(link, "x")


def doctor_host(**options):
    host = good_host(**options)
    host.commands.update({
        "docker version": (0, "28.0.1"),
        "docker compose": lambda args: (0, "2.40.0") if args[2] == "version" else (
            (0, '{"Name":"x"}') if args[2] == "ps" and "--format" in args and args[-1] == "json" else
            (0, "frontend\ncontrol-plane\nmedia-node") if args[2] == "config" else (0, "running (healthy)")),
        "hostname": (0, "10.0.0.5 172.17.0.1"),
        "lsof": (1, ""),
    })
    host.tools |= {"docker"}
    host.disk_free = lambda path: "40.0 GiB"
    return host


def doctor_install(tmp_path, target="full", extra_env=""):
    folder = make_install(tmp_path / "inst", target)
    (folder / ".env").write_text("FLUXOMNI_VERSION=26.4.0\nFLUXOMNI_PUBLIC_HOST=10.0.0.5\n" + extra_env)
    (folder / "data").mkdir()
    (folder / "data" / "state.db").write_text("x")
    return ctl.Install(folder, target)


def test_doctor_passes_on_a_healthy_full_install(tmp_path, capsys):
    install = doctor_install(tmp_path, extra_env="FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=t\n")
    assert ctl.doctor(install, doctor_host(), environ={}) == 0
    output = capsys.readouterr().out
    assert "Internal Auth Token configured" in output and "control-plane container" in output
    assert "Port 80 (Web UI) available" in output and "looks good" in output


def test_doctor_reports_failures_and_exit_code(tmp_path, capsys):
    install = doctor_install(tmp_path)
    host = doctor_host()
    host.commands["docker compose"] = lambda args: (0, "2.40.0") if args[2] == "version" else (
        (0, "{}") if args[-1] == "json" else (0, "frontend\nmedia-node") if args[2] == "config" else (0, "exited (1)"))
    assert ctl.doctor(install, host, environ={}) == 1
    output = capsys.readouterr().out
    assert "Internal Auth Token MISSING" in output and "frontend container NOT running" in output
    assert "Some issues were detected" in output


def test_doctor_standalone_node_credential_and_private_node(tmp_path, capsys):
    folder = make_install(tmp_path / "node", "media-node")
    (folder / ".env").write_text("FLUXOMNI_VERSION=26.4.0\nFLUXOMNI_NODE_CREDENTIAL_FILE=node-secrets/credential\n")
    install = ctl.Install(folder, "media-node")
    assert ctl.doctor(install, doctor_host(), environ={}) == 1
    assert "Node credential missing" in capsys.readouterr().out
    (folder / "node-secrets").mkdir()
    (folder / "node-secrets" / "credential").write_text("secret")
    assert ctl.doctor(install, doctor_host(), environ={}) == 0
    output = capsys.readouterr().out
    assert "Private node" in output and "Web UI" not in output and "RTMP" not in output


def test_doctor_warns_on_unknown_public_host_and_busy_port(tmp_path, capsys):
    install = doctor_install(tmp_path)
    (install.path / ".env").write_text("FLUXOMNI_VERSION=26.4.0\nFLUXOMNI_PUBLIC_HOST=192.0.2.9\nFLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=t\n")
    host = doctor_host()
    host.commands["lsof"] = (0, "COMMAND PID\nnginx 12 root")
    ctl.doctor(install, host, environ={})
    output = capsys.readouterr().out
    assert "NOT found in host IPs" in output and "in use by another process" in output


def test_doctor_command_uses_the_selected_install(tmp_path, capsys):
    install = doctor_install(tmp_path, extra_env="FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=t\n")
    assert ctl.main(["--dir", str(install.path), "doctor"], host=doctor_host(), interactive=False, environ={"HOME": str(tmp_path)}) == 0
    assert str(install.path.resolve()) in capsys.readouterr().out


@pytest.mark.parametrize("version,supported", [
    ("26.4.0", True), ("v26.4.1", True), ("v27.0.0", True), ("v26.10.0", True), ("latest", True), ("edge", True), ("", True),
    ("v26.3.2", False), ("26.3.9", False), ("v25.12.0", False), ("garbage", False),
])
def test_version_support(version, supported):
    assert ctl.version_supported(version) is supported


def test_check_support_refuses_old_installs_with_an_upgrade_hint(tmp_path, capsys):
    folder = make_install(tmp_path / "old", "full")
    (folder / ".env").write_text("FLUXOMNI_VERSION=v26.3.2\n")
    assert ctl.main(["--dir", str(folder), "check-support"], environ={"HOME": str(tmp_path)}, interactive=False) == 1
    assert "supports v26.4.0 and newer" in capsys.readouterr().err
    (folder / ".env").write_text("FLUXOMNI_VERSION=26.4.0\n")
    assert ctl.main(["--dir", str(folder), "check-support"], environ={"HOME": str(tmp_path)}, interactive=False) == 0


def test_doctor_wrapper_calls_the_tool_by_absolute_path_with_its_own_folder(tmp_path):
    folder = tmp_path / "install"
    folder.mkdir()
    wrapper = folder / "doctor.sh"
    wrapper.write_text((ROOT / "doctor.sh").read_text())
    tool = tmp_path / "ctl"
    tool.write_text("#!/bin/sh\necho \"called: $*\"\n")
    tool.chmod(0o755)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path / "nohome")}
    done = subprocess.run(["bash", str(wrapper)], env={**env, "FLUXOMNICTL": str(tool)}, capture_output=True, text=True)
    assert done.returncode == 0 and done.stdout.strip() == f"called: --dir {folder.resolve()} doctor"
    missing = subprocess.run(["bash", str(wrapper)], env=env, capture_output=True, text=True)
    assert missing.returncode == 1 and "bash install.sh tools" in missing.stderr


def test_version_edge_cases_and_last_line_wins(tmp_path):
    for odd in ("26.4.0abc", "v26.4", "stable", "26.4.0-rc1x y"):
        assert ctl.version_supported(odd) is False
    assert ctl.version_supported("v26.5.0-rc.1") is True
    env = tmp_path / ".env"
    env.write_text("FLUXOMNI_VERSION=v26.3.2\nFLUXOMNI_VERSION=26.4.0\n")
    assert ctl.read_env_value(env, "FLUXOMNI_VERSION") == "26.4.0"


def test_doctor_reads_addresses_on_macos_and_survives_disk_errors(tmp_path, capsys):
    host = doctor_host()
    host.commands["hostname"] = (1, "")
    host.commands["ip"] = (127, "")
    host.commands["ifconfig"] = (0, "lo0: inet 127.0.0.1\nen0: inet 192.168.1.9 netmask 0xffffff00")
    assert ctl.host_addresses(host) == ["192.168.1.9"]

    def broken(path):
        raise OSError("gone")

    host.disk_free = broken
    install = doctor_install(tmp_path, extra_env="FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN=t\n")
    ctl.doctor(install, host, environ={})
    assert "cannot read" in capsys.readouterr().out
