"""Verify fluxomnictl finds the right install folder from any directory."""

import importlib.util
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
