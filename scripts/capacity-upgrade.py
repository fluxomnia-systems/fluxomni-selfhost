#!/usr/bin/env python3
"""Verify and execute an explicit local capacity-ledger maintenance window.

SQLite is read through its normal WAL-aware connection, never edited. External
execution shutdown is an operator assertion, not inferred from liveness.
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path, PurePosixPath


class UpgradeError(Exception):
    """A safe, credential-free maintenance failure."""


def document(raw):
    try:
        value = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise UpgradeError("Invalid JSON in maintenance evidence") from error
    if not isinstance(value, dict):
        raise UpgradeError("Maintenance evidence must be an object")
    return value


def database_path(service):
    """Resolve only the supported unambiguous local SQLite bind."""
    if service.get("command") or service.get("entrypoint"):
        raise UpgradeError("Custom control-plane command/entrypoint requires manual maintenance")
    environment = service.get("environment", {})
    if not isinstance(environment, dict) or any(k.startswith("FLUXOMNI_DB_") for k in environment):
        raise UpgradeError("Unsupported control-plane database configuration")
    root = environment.get("FLUXOMNI_APP_ROOT")
    if not isinstance(root, str) or not root.startswith("/") or ".." in PurePosixPath(root).parts:
        raise UpgradeError("An absolute control-plane app root is required")
    target = PurePosixPath(root) / "state.db"
    covering = []
    for mount in service.get("volumes", []):
        destination = mount.get("target", "")
        if not destination or ".." in PurePosixPath(destination).parts:
            raise UpgradeError("Invalid control-plane mount")
        destination = PurePosixPath(destination)
        if target == destination or destination in target.parents:
            covering.append(mount)
    if len(covering) != 1 or covering[0].get("type") != "bind":
        raise UpgradeError("One local directory bind must own control-plane SQLite")
    mount = covering[0]
    source = Path(mount.get("source", ""))
    if not source.is_absolute() or mount.get("read_only"):
        raise UpgradeError("A local writable control-plane data bind is required")
    path = source / str(target.relative_to(PurePosixPath(mount["target"])))
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise UpgradeError("Symlinked control-plane storage requires manual maintenance")
    return path


# @lat: [[installation#Capacity ledger evidence]]
def read_ledger(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise UpgradeError("Existing control-plane SQLite database is required")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:
            connection.execute("BEGIN")
            rows = connection.execute(
                "SELECT payload FROM assignment_snapshots "
                "WHERE assignment_snapshot_id = 'current' AND snapshot_key = 'current'"
            ).fetchall()
            if len(rows) != 1:
                raise UpgradeError("Exactly one current assignment snapshot is required")
            snapshot = document(rows[0][0])
            routes = [document(row[0]) for row in connection.execute("SELECT payload FROM restreams")]
    except sqlite3.Error as error:
        raise UpgradeError("Unable to read the control-plane capacity ledger") from error
    initialized = snapshot.get("capacity_initialized", False)
    if not isinstance(initialized, bool):
        raise UpgradeError("Invalid capacity initialization marker")
    claims = snapshot.get("capacity_reservations", [])
    if not isinstance(claims, list) or any(not isinstance(claim, dict) for claim in claims):
        raise UpgradeError("Invalid capacity reservation ledger")
    # For a stopped/drained boundary require no claims at all. Do not reinterpret
    # unknown claim schemas as empty demand.
    for route in routes:
        if not isinstance(route.get("enabled"), bool):
            raise UpgradeError("Unknown persisted route enabled state")
    return initialized, claims, routes


def require_mode(path, mode):
    initialized, claims, routes = read_ledger(path)
    if mode == "initial":
        if initialized:
            raise UpgradeError("Ledger is already initialized; use a drained upgrade")
    elif not initialized or claims or any(route["enabled"] for route in routes):
        raise UpgradeError("Disable all routes and wait for zero reservations before a drained upgrade")


class Docker:
    def __init__(self, prefix, timeout):
        self.prefix = prefix
        self.timeout = timeout

    def run(self, *args, timeout=60):
        try:
            result = subprocess.run(
                [*self.prefix, *args], capture_output=True, text=True, timeout=timeout, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise UpgradeError("Docker maintenance operation unavailable or timed out") from error
        if result.returncode:
            # Raw Docker output can include rendered environment secrets.
            raise UpgradeError("Docker maintenance operation failed: " + " ".join(args[:2]))
        return result.stdout

    def compose(self, *args, timeout=60):
        # Make inactive automatic updaters visible for inspection and stopping.
        # Every start below names services explicitly and excludes Watchtower.
        return self.run("compose", "--profile", "auto-update", *args, timeout=timeout)

    def config(self):
        return document(self.compose("config", "--format", "json"))

    def owner(self):
        ids = self.compose("ps", "--all", "--quiet", "control-plane").split()
        if len(ids) != 1:
            raise UpgradeError("Exactly one existing control-plane container is required")
        try:
            owners = json.loads(self.run("inspect", ids[0]))
            owner = owners[0]
        except (ValueError, IndexError, TypeError) as error:
            raise UpgradeError("Invalid control-plane inspection") from error
        if len(owners) != 1:
            raise UpgradeError("Ambiguous control-plane owner")
        environment = dict(item.split("=", 1) for item in owner["Config"]["Env"] if "=" in item)
        if "--app-root" in " ".join(owner["Config"].get("Cmd") or []):
            raise UpgradeError("Custom app-root argument requires manual maintenance")
        mounts = [
            {"type": m["Type"], "source": m["Source"], "target": m["Destination"], "read_only": not m["RW"]}
            for m in owner["Mounts"]
        ]
        return database_path({"environment": environment, "volumes": mounts}), environment

    def api_ready(self):
        payload = json.dumps({"query": "query { fleet { mediaNodes { admissionCapacity { committedRoutes startingRoutes retiringRoutes committedOutputs startingOutputs retiringOutputs } } } }"})
        script = '''curl --fail --silent --max-time 5 \
-H "Authorization: Bearer $FLUXOMNI_CONTROL_PLANE_INTERNAL_AUTH_TOKEN" \
-H 'Content-Type: application/json' --data-binary "$1" http://127.0.0.1:80/api'''
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                response = document(self.compose("exec", "-T", "control-plane", "sh", "-ec", script, "capacity-upgrade", payload, timeout=10))
                nodes = response.get("data", {}).get("fleet", {}).get("mediaNodes")
                if response.get("errors") or not isinstance(nodes, list):
                    raise UpgradeError("Candidate does not expose the admission API")
                for node in nodes:
                    counts = node.get("admissionCapacity", {})
                    if len(counts) != 6 or any(type(v) is not int or v < 0 for v in counts.values()):
                        raise UpgradeError("Invalid admission API response")
                return
            except (UpgradeError, AttributeError, TypeError):
                if time.monotonic() >= deadline:
                    raise UpgradeError("Control-plane admission API did not become ready") from None
                time.sleep(min(1, max(0, deadline - time.monotonic())))

    def start_control_plane(self, config, acknowledgement=False):
        if not acknowledgement:
            self.compose("up", "-d", "--no-deps", "--force-recreate", "control-plane")
            return
        # Rendered JSON binds project identity and all operator overrides. The
        # acknowledgement lives only in this private temporary Compose input.
        config = json.loads(json.dumps(config))
        config["services"]["control-plane"]["environment"]["FLUXOMNI_CAPACITY_UPGRADE_STOPPED"] = "true"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix=".capacity-upgrade-", dir=".") as temporary:
            json.dump(config, temporary)
            temporary.flush()
            self.run("compose", "-f", temporary.name, "up", "-d", "--no-deps", "--force-recreate", "control-plane")

    def stopped(self, service):
        ids = self.compose("ps", "--all", "--quiet", service).split()
        for container_id in ids:
            values = json.loads(self.run("inspect", container_id))
            if not isinstance(values, list) or len(values) != 1 or not isinstance(values[0], dict):
                raise UpgradeError("Invalid execution container inspection")
            if values[0].get("State", {}).get("Running") is not False:
                raise UpgradeError("Execution container has not stopped")


# @lat: [[installation#Capacity upgrade service ordering]]
def maintenance(docker, mode, expected_path):
    config = docker.config()
    services = config.get("services", {})
    path = database_path(services.get("control-plane", {}))
    actual_path, environment = docker.owner()
    if path != actual_path or str(path) != expected_path:
        raise UpgradeError("Control-plane storage changed; explicit manual migration is required")
    if mode != "initial" and "FLUXOMNI_CAPACITY_UPGRADE_STOPPED" in environment:
        raise UpgradeError("Remove the raw runtime acknowledgement before maintenance")
    require_mode(path, mode)
    controllers = [s for s in ("watchtower", "frontend") if s in services]
    if controllers:
        docker.compose("stop", "--timeout", "30", *controllers)
    execution_stopped = False
    control_plane_stopped = False
    temporary_control_plane = False
    try:
        if mode == "drained":
            docker.compose("stop", "--timeout", "30", "control-plane")
            control_plane_stopped = True
            # Freeze durable writes, then confirm there was no growth after the
            # online preflight. Keep old execution available for proof on refusal.
            require_mode(path, mode)
        docker.compose("stop", "--timeout", "30", "media-node")
        execution_stopped = True
        docker.stopped("media-node")
        if not control_plane_stopped:
            docker.compose("stop", "--timeout", "30", "control-plane")
            control_plane_stopped = True
            require_mode(path, mode)
        temporary_control_plane = mode == "initial"
        docker.start_control_plane(config, acknowledgement=temporary_control_plane)
        docker.api_ready()
        actual_path, _ = docker.owner()
        if actual_path != path:
            raise UpgradeError("Candidate control-plane storage differs from the previous owner")
        docker.compose("stop", "--timeout", "30", "control-plane")
        temporary_control_plane = False
        if not read_ledger(path)[0]:
            raise UpgradeError("Candidate did not persist capacity initialization")
        docker.start_control_plane(config)
        docker.api_ready()
        actual_path, environment = docker.owner()
        if actual_path != path or "FLUXOMNI_CAPACITY_UPGRADE_STOPPED" in environment:
            raise UpgradeError("Candidate retains the acknowledgement or uses different storage")
        docker.compose("up", "-d", "--no-deps", "media-node", *[s for s in controllers if s != "watchtower"], timeout=120)
    except (UpgradeError, KeyError, TypeError, ValueError, OSError):
        if temporary_control_plane:
            try:
                docker.compose("stop", "--timeout", "30", "control-plane")
                docker.stopped("control-plane")
            except UpgradeError as error:
                raise UpgradeError("Unable to stop the temporary control plane; stop it manually before retry") from error
        if not execution_stopped and control_plane_stopped:
            # No candidate has started and execution remains available to drain.
            docker.compose("start", "control-plane")
        raise


def local_config(docker):
    if os.environ.get("DOCKER_HOST") or os.environ.get("COMPOSE_FILE") or os.environ.get("COMPOSE_PROFILES"):
        raise UpgradeError("Maintenance requires the local default Compose bundle")
    context = docker.run("context", "show").strip()
    endpoint = docker.run("context", "inspect", context, "--format", "{{.Endpoints.docker.Host}}").strip()
    if not endpoint.startswith("unix://"):
        raise UpgradeError("Maintenance requires a local Docker daemon")
    return docker.config()


def preflight(docker, mode):
    config = local_config(docker)
    service = config.get("services", {}).get("control-plane", {})
    if "FLUXOMNI_CAPACITY_UPGRADE_STOPPED" in service.get("environment", {}):
        raise UpgradeError("Remove the raw runtime acknowledgement from .env/Compose")
    path = database_path(service)
    actual_path, environment = docker.owner()
    if path != actual_path or (mode != "initial" and "FLUXOMNI_CAPACITY_UPGRADE_STOPPED" in environment):
        raise UpgradeError("Rendered storage/acknowledgement differs from the actual control plane")
    require_mode(path, mode)
    return path



# @lat: [[installation#Incomplete fresh installation retries]]
def fresh_preflight(docker, target):
    config = local_config(docker)
    if docker.compose("ps", "--all", "--quiet").split():
        raise UpgradeError("Fresh retry has runtime containers; use maintenance or manual recovery")
    services = config.get("services", {})
    required = ["media-node"] if target == "media-node" else ["control-plane", "media-node"]
    for name in required:
        path = database_path(services.get(name, {}))
        if (path.exists() and (not path.is_file() or path.stat().st_size)) or any(
            Path(str(path) + suffix).exists() or Path(str(path) + suffix).is_symlink() for suffix in ("-wal", "-shm")
        ):
            raise UpgradeError("Fresh retry has durable state; use maintenance or manual recovery")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "run", "fresh-preflight"])
    parser.add_argument("--mode", choices=["initial", "drained"])
    parser.add_argument("--target", choices=["full", "media-node"])
    parser.add_argument("--database")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--docker", nargs="+", default=["docker"])
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("timeout must be 1–300 seconds")
    prefix = args.docker
    docker = Docker(prefix or ["docker"], args.timeout)
    try:
        if args.action == "fresh-preflight":
            if not args.target:
                parser.error("fresh-preflight requires --target")
            fresh_preflight(docker, args.target)
        elif not args.mode:
            parser.error("maintenance requires --mode")
        elif args.action == "preflight":
            print(preflight(docker, args.mode))
        else:
            if not args.database:
                parser.error("run requires --database")
            maintenance(docker, args.mode, args.database)
    except (UpgradeError, KeyError, TypeError, ValueError, OSError) as error:
        message = str(error) if isinstance(error, UpgradeError) else "Invalid maintenance evidence"
        print("Error: " + message + ". Execution is not automatically restored; retain data and follow the upgrade guide.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
