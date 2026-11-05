#!/usr/bin/env python3
"""Prepare the local Connect gateway configuration for a fresh installation."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from uuid import UUID, uuid4


def prepare(root, origin, key_id, public_key):
    url = urlsplit(origin)
    if (
        url.scheme != "https"
        or not url.hostname
        or not re.fullmatch(r"[a-z0-9.-]+", url.hostname)
        or origin != f"https://{url.hostname}"
    ):
        raise ValueError("Use a canonical HTTPS hostname without a path or port")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", key_id):
        raise ValueError("Invalid gateway key ID")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", public_key):
        raise ValueError("Expected a 32-byte Ed25519 public key in unpadded base64url")
    decoded = base64.urlsafe_b64decode(public_key + "=")
    if base64.urlsafe_b64encode(decoded).decode().rstrip("=") != public_key:
        raise ValueError("Expected canonical base64url")

    path = root / "gateway.json"
    settings = {
        "origin": origin,
        "initialGatewayKey": {"keyId": key_id, "publicKey": public_key},
    }
    with tempfile.NamedTemporaryFile(mode="w", dir=root) as temporary:
        json.dump({**settings, "installationId": str(uuid4())}, temporary, indent=2)
        temporary.write("\n")
        temporary.flush()
        os.fsync(temporary.fileno())
        try:
            os.link(temporary.name, path)
        except FileExistsError:
            if path.is_symlink() or not path.is_file():
                raise ValueError("Existing gateway.json must be a regular file")
            saved = json.loads(path.read_text())
            if not isinstance(saved, dict) or any(
                saved.get(name) != value for name, value in settings.items()
            ):
                raise ValueError("Existing gateway.json differs. Use explicit recovery or migration.")
            identifier = saved.get("installationId")
            if not isinstance(identifier, str) or str(UUID(identifier)) != identifier:
                raise ValueError("Existing gateway.json has an invalid Installation ID")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin")
    parser.add_argument("key_id")
    parser.add_argument("public_key")
    args = parser.parse_args()
    try:
        prepare(Path.cwd(), args.origin, args.key_id, args.public_key)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")
    print("gateway.json is ready")


if __name__ == "__main__":
    main()
