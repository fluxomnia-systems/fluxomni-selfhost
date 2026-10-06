"""Capacity upgrade proofs over real SQLite and bounded service transitions."""

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "scripts/capacity-upgrade.py"
spec = importlib.util.spec_from_file_location("capacity_upgrade", MODULE)
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


def write_ledger(path, initialized=False, claims=None, enabled=False):
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS assignment_snapshots(assignment_snapshot_id TEXT, snapshot_key TEXT, payload TEXT)")
        connection.execute("CREATE TABLE IF NOT EXISTS restreams(payload TEXT)")
        connection.execute("DELETE FROM assignment_snapshots")
        snapshot = {"capacity_reservations": claims or []}
        if initialized is not None:
            snapshot["capacity_initialized"] = initialized
        connection.execute("INSERT INTO assignment_snapshots VALUES('current','current',?)", (json.dumps(snapshot),))
        connection.execute("DELETE FROM restreams")
        connection.execute("INSERT INTO restreams VALUES(?)", (json.dumps({"id": "saved-route", "enabled": enabled}),))


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "state.db"
    write_ledger(path)
    return path


# @lat: [[installation#Capacity marker classification tests]]
@pytest.mark.parametrize("initialized", [True, False, None])
@pytest.mark.parametrize("claims", [[], [{"reserved": "unknown"}]])
def test_initial_mode_never_reinitializes_an_initialized_ledger(database, initialized, claims):
    write_ledger(database, initialized, claims)
    before = database.read_bytes()
    if initialized:
        with pytest.raises(upgrade.UpgradeError, match="already initialized"):
            upgrade.require_mode(database, "initial")
    else:
        upgrade.require_mode(database, "initial")
    assert database.read_bytes() == before


# @lat: [[installation#Capacity drain proof tests]]
@pytest.mark.parametrize("initialized,claims,enabled", [(False, [], False), (True, [{"state": "retiring"}], False), (True, [], True)])
def test_later_upgrade_refuses_every_unproven_drain(database, initialized, claims, enabled):
    write_ledger(database, initialized, claims, enabled)
    with pytest.raises(upgrade.UpgradeError, match="zero reservations"):
        upgrade.require_mode(database, "drained")


# @lat: [[installation#Capacity empty ledger serialization tests]]
def test_initialized_empty_ledger_omits_claims_and_reads_committed_wal(database):
    with sqlite3.connect(database) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("UPDATE assignment_snapshots SET payload = ?", (json.dumps({"capacity_initialized": True}),))
        writer.commit()
        upgrade.require_mode(database, "drained")
        with pytest.raises(upgrade.UpgradeError):
            upgrade.require_mode(database, "initial")


@pytest.mark.parametrize("payload", ['null', '[]', '{bad', '{"capacity_initialized":"true"}', '{"capacity_reservations":{}}'])
def test_malformed_state_is_never_an_empty_ledger(database, payload):
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE assignment_snapshots SET payload=?", (payload,))
    with pytest.raises(upgrade.UpgradeError):
        upgrade.require_mode(database, "initial")


# @lat: [[installation#Capacity storage binding tests]]
def test_bind_resolution_refuses_ambiguous_or_custom_storage(tmp_path):
    service = {"environment": {"FLUXOMNI_APP_ROOT": "/data"}, "volumes": [{"type": "bind", "source": str(tmp_path), "target": "/data"}]}
    assert upgrade.database_path(service) == tmp_path / "state.db"
    for change in [
        {"command": ["--app-root", "/different"]},
        {"entrypoint": ["custom"]},
        {"volumes": [{"type": "volume", "source": "named", "target": "/data"}]},
        {"volumes": [*service["volumes"], {"type": "bind", "source": str(tmp_path), "target": "/data/state.db"}]},
        {"environment": {"FLUXOMNI_APP_ROOT": "./data"}},
        {"environment": {"FLUXOMNI_APP_ROOT": "/data", "FLUXOMNI_DB_URL": "sqlite://elsewhere"}},
    ]:
        with pytest.raises(upgrade.UpgradeError):
            upgrade.database_path({**service, **change})
    linked = tmp_path / "linked"
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(upgrade.UpgradeError):
        upgrade.database_path({**service, "volumes": [{"type": "bind", "source": str(linked), "target": "/data"}]})


class Lifecycle:
    def __init__(self, path, fail_api=False, fail_persist=False, grow_on_freeze=False):
        self.path = path
        self.events = []
        self.environment = {"FLUXOMNI_APP_ROOT": "/data"}
        self.fail_api = fail_api
        self.fail_persist = fail_persist
        self.grow_on_freeze = grow_on_freeze

    def config(self):
        return {"services": {"control-plane": {"environment": {"FLUXOMNI_APP_ROOT": "/data"}, "volumes": [{"type": "bind", "source": str(self.path.parent), "target": "/data"}]}, "media-node": {}, "frontend": {}, "watchtower": {}}}

    def owner(self):
        return self.path, self.environment

    def compose(self, *args, **kwargs):
        self.events.append(args)
        if args == ("stop", "--timeout", "30", "control-plane") and self.grow_on_freeze:
            write_ledger(self.path, True, enabled=True)
            self.grow_on_freeze = False

    def start_control_plane(self, config, acknowledgement=False):
        self.events.append(("candidate", acknowledgement))
        if acknowledgement:
            self.environment["FLUXOMNI_CAPACITY_UPGRADE_STOPPED"] = "true"
            if not self.fail_persist:
                write_ledger(self.path, True)
        else:
            self.environment.pop("FLUXOMNI_CAPACITY_UPGRADE_STOPPED", None)

    def api_ready(self):
        self.events.append(("api",))
        if self.fail_api:
            raise upgrade.UpgradeError("API not ready")

    def stopped(self, service):
        self.events.append(("stopped", service))


# @lat: [[installation#Capacity initialization ordering tests]]
def test_initial_upgrade_proves_persistence_and_removes_ack_before_execution(database):
    docker = Lifecycle(database)
    upgrade.maintenance(docker, "initial", str(database))
    assert docker.events == [
        ("stop", "--timeout", "30", "watchtower", "frontend"),
        ("stop", "--timeout", "30", "media-node"),
        ("stopped", "media-node"),
        ("stop", "--timeout", "30", "control-plane"),
        ("candidate", True), ("api",),
        ("stop", "--timeout", "30", "control-plane"),
        ("candidate", False), ("api",),
        ("up", "-d", "--no-deps", "media-node", "frontend"),
    ]
    assert "FLUXOMNI_CAPACITY_UPGRADE_STOPPED" not in docker.environment
    assert upgrade.read_ledger(database)[0] is True


# @lat: [[installation#Capacity initialization failure tests]]
@pytest.mark.parametrize("failure", ["fail_api", "fail_persist"])
def test_failed_initialization_never_starts_execution_or_rolls_back_data(database, failure):
    docker = Lifecycle(database, **{failure: True})
    with pytest.raises(upgrade.UpgradeError):
        upgrade.maintenance(docker, "initial", str(database))
    assert not any(event[0] in ("up", "start") for event in docker.events)
    assert database.exists()
    assert ("stop", "--timeout", "30", "control-plane") == docker.events[-2 if failure == "fail_api" else -1]
    if failure == "fail_api":
        assert docker.events[-1] == ("stopped", "control-plane")


# @lat: [[installation#Capacity frozen drain tests]]
def test_demand_arriving_before_writer_stop_keeps_old_execution_available(database):
    write_ledger(database, True)
    docker = Lifecycle(database, grow_on_freeze=True)
    with pytest.raises(upgrade.UpgradeError, match="zero reservations"):
        upgrade.maintenance(docker, "drained", str(database))
    assert ("stop", "--timeout", "30", "media-node") not in docker.events
    assert docker.events[-1] == ("start", "control-plane")


def test_candidate_mount_change_is_rejected_before_any_stop(database, tmp_path):
    write_ledger(database, True)
    docker = Lifecycle(database)
    docker.owner = lambda: (tmp_path / "wrong.db", docker.environment)
    with pytest.raises(upgrade.UpgradeError):
        upgrade.maintenance(docker, "drained", str(database))
    assert docker.events == []


def test_failed_candidate_mount_check_stops_acknowledged_control_plane(database, tmp_path):
    docker = Lifecycle(database)
    observations = iter([database, tmp_path / "wrong.db"])
    docker.owner = lambda: (next(observations), docker.environment)
    with pytest.raises(upgrade.UpgradeError):
        upgrade.maintenance(docker, "initial", str(database))
    assert docker.events[-2:] == [("stop", "--timeout", "30", "control-plane"), ("stopped", "control-plane")]
    assert not any(event[0] in ("up", "start") for event in docker.events)


class FreshProbe:
    def __init__(self, root, containers=''):
        self.root = root
        self.containers = containers

    def run(self, *args):
        return 'default' if args == ('context', 'show') else 'unix:///var/run/docker.sock'

    def config(self):
        service = {'environment': {'FLUXOMNI_APP_ROOT': '/data'}, 'volumes': [
            {'type': 'bind', 'source': str(self.root), 'target': '/data'},
        ]}
        return {'services': {'control-plane': service, 'media-node': service}}

    def compose(self, *args):
        assert args == ('ps', '--all', '--quiet')
        return self.containers


def test_fresh_retry_requires_absent_containers_and_empty_storage(tmp_path):
    docker = FreshProbe(tmp_path)
    upgrade.fresh_preflight(docker, 'full')
    path = tmp_path / 'state.db'
    path.touch()
    upgrade.fresh_preflight(docker, 'full')
    for suffix in ['-wal', '-shm']:
        sidecar = tmp_path / ('state.db' + suffix)
        sidecar.touch()
        with pytest.raises(upgrade.UpgradeError):
            upgrade.fresh_preflight(docker, 'full')
        sidecar.unlink()
    for payload in [b'unknown database', b'{"capacity_initialized":true}']:
        path.write_bytes(payload)
        with pytest.raises(upgrade.UpgradeError):
            upgrade.fresh_preflight(docker, 'full')
    path.write_bytes(b'')
    docker.containers = 'created-or-established-container'
    with pytest.raises(upgrade.UpgradeError):
        upgrade.fresh_preflight(docker, 'full')
