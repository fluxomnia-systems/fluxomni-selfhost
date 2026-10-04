#!/usr/bin/env python3
"""Reject rendered Compose overrides that weaken the requested preparation budget."""

# @lat: [[installation#Preparation Compose enforcement]]
import json
import sys


def verify(config, root, cpu, memory, tasks):
    node = config["services"]["media-node"]
    if node.get("user") not in ("0", "0:0") or node.get("cgroup") != "host":
        raise ValueError("media-node must use UID 0 and the host cgroup namespace")
    expected = {
        "FLUXOMNI_PREPARATION_CGROUP_ROOT": "/preparation-cgroup",
        "FLUXOMNI_PREPARATION_CPU_MILLICORES": cpu,
        "FLUXOMNI_PREPARATION_MEMORY_MIB": memory,
        "FLUXOMNI_PREPARATION_TASKS": tasks,
    }
    if any(
        str(node.get("environment", {}).get(key)) != value
        for key, value in expected.items()
    ):
        raise ValueError(
            "media-node preparation budget differs from the requested settings"
        )
    volumes = [
        volume
        for volume in node.get("volumes", [])
        if volume["target"] == "/preparation-cgroup"
    ]
    if (
        len(volumes) != 1
        or volumes[0].get("type") != "bind"
        or volumes[0].get("source") != root
        or volumes[0].get("read_only", False)
        or not isinstance(volumes[0].get("bind"), dict)
        # Compose v2 omits false booleans in its rendered JSON.
        or volumes[0]["bind"].get("create_host_path", False)
    ):
        raise ValueError(
            "media-node needs the exact owned writable cgroup bind with create_host_path=false"
        )
    if node.get("privileged") or node.get("userns_mode") not in (None, "", "host"):
        raise ValueError(
            "preparation isolation does not support privileged or remapped media nodes"
        )


if __name__ == "__main__":
    try:
        verify(json.load(sys.stdin), *sys.argv[1:])
    except (ValueError, KeyError, TypeError) as exc:
        print(
            "Error: unsafe preparation Compose configuration: " + str(exc),
            file=sys.stderr,
        )
        sys.exit(1)
