#!/usr/bin/env python3
"""Replace one node credential using a saved candidate and a Fleet grant."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import ssl
import stat
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_private(path: Path, value: str) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write(value)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def read_secret(path: Path) -> str:
    value = path.read_text().strip()
    if not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError("Saved credential is damaged; keep it for recovery")
    return value


# @lat: [[installation#Credential replacement]]
def replace(root: Path, node: str, endpoint: str, mode: str, complete: bool = False) -> None:
    directory = root / "node-secrets"
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Use the original node installation directory")
    if directory.stat().st_uid != os.getuid():
        raise ValueError("Node secrets must belong to the current installer user")
    os.chmod(directory, 0o700)
    names = ("credential", "credential.next", ".credential-operation", ".credential-lock", "identity", "enrolled", "enrollment-ca.crt")
    for name in names:
        path = directory / name
        if path.is_symlink() or (path.exists() and (not stat.S_ISREG(path.stat().st_mode) or path.stat().st_uid != os.getuid())):
            raise ValueError("Node credential files must be owned regular files")
    with (directory / ".credential-lock").open("a") as lock:
        os.chmod(lock.name, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("Another credential replacement is running; retry the same command") from error
        candidate = directory / "credential.next"
        operation_file = directory / ".credential-operation"
        current = directory / "credential"
        identity = f"{node}\n{endpoint}"
        if (directory / "identity").read_text().strip() != identity:
            raise ValueError("Keep the original node and control endpoint identity")
        if complete:
            if not operation_file.exists() or not candidate.exists() or read_secret(candidate) != read_secret(current):
                raise ValueError("Replacement completion files do not match the active credential")
            binding = json.loads(operation_file.read_text())
            if binding.get("node") != node or binding.get("endpoint") != endpoint or binding.get("mode") != mode or binding.get("candidateHash") != sha(read_secret(current)):
                raise ValueError("Replacement completion identity does not match")
            candidate.unlink()
            operation_file.unlink()
            return
        url = os.environ.get("FLUXOMNI_CREDENTIAL_URL", "")
        code = os.environ.get("FLUXOMNI_CREDENTIAL_CODE", "")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("Credential replacement requires a verified HTTPS URL")
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", code) or mode not in ("ROTATE", "RECOVER"):
            raise ValueError("Use a fresh Fleet rotation or recovery command")
        binding = {"grant": sha(code), "node": node, "endpoint": endpoint, "mode": mode, "url": parsed.geturl()}
        if operation_file.exists():
            saved = json.loads(operation_file.read_text())
            stable = ("node", "endpoint", "url")
            if any(saved.get(key) != binding[key] for key in stable) or (saved.get("grant") == binding["grant"] and saved.get("mode") != mode):
                raise ValueError("A saved candidate belongs to another identity or URL; keep the original installation")
            # A fresh Admin grant can retry a cancelled/expired operation with
            # the same candidate. The server still compares its generation.

            if "candidateHash" in saved:
                binding["candidateHash"] = saved["candidateHash"]
        else:
            if candidate.exists():
                raise ValueError("A saved candidate has no command binding; preserve it and inspect the interrupted operation")
            # Save the binding first. A crash before candidate creation can retry safely.
            write_private(operation_file, json.dumps(binding))
        if not candidate.exists():
            if "candidateHash" in binding:
                # Cleanup may have removed the candidate just before a crash.
                secret = read_secret(current)
                if sha(secret) != binding["candidateHash"] or (directory / "enrolled").read_text().strip() != sha(secret):
                    raise ValueError("Missing candidate cannot be reconstructed from the committed receipt")
                write_private(candidate, secret + "\n")
            else:
                write_private(candidate, secrets.token_hex(32) + "\n")
        secret = read_secret(candidate)
        if "candidateHash" in binding and binding["candidateHash"] != sha(secret):
            raise ValueError("Saved candidate does not match its operation")
        binding["candidateHash"] = sha(secret)
        write_private(operation_file, json.dumps(binding))
        payload = {"nodeId": node, "code": code, "credentialHash": sha(secret)}
        if mode == "ROTATE":
            payload["currentCredential"] = read_secret(current)
        trust = directory / "enrollment-ca.crt"
        arguments = ["curl", "--silent", "--show-error", "--proto", "=https", "--tlsv1.2", "--connect-timeout", "10", "--max-time", "30", "--request", "POST", "--header", "Content-Type: application/json", "--data-binary", "@-", "--write-out", "\n%{http_code}"]
        if trust.exists():
            # Validate trust before sending a code or proof. curl verifies hostnames too.
            ssl.create_default_context(cafile=str(trust))
            arguments.extend(["--cacert", str(trust)])
        arguments.append(url)
        result = subprocess.run(arguments, input=json.dumps(payload), text=True, capture_output=True, check=False)
        body, _, status = result.stdout.rpartition("\n")
        try:
            confirmed = result.returncode == 0 and status == "200" and json.loads(body).get("replaced") is True
        except (ValueError, AttributeError):
            confirmed = False
        if not confirmed:
            raise ValueError("Replacement is unconfirmed. Keep the saved candidate and retry the same command; check Fleet for blockers")
        write_private(current, secret + "\n")
        write_private(directory / "enrolled", sha(secret) + "\n")
        print("Credential replacement committed. Starting the node with its saved credential.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    try:
        replace(Path(os.environ["FLUXOMNI_DIR"]), args.node, args.endpoint, os.environ.get("FLUXOMNI_CREDENTIAL_MODE", ""), args.complete)
    except (ValueError, OSError, KeyError):
        # Never echo request contents, curl stderr, saved secrets or untrusted errors.
        print("Error: credential replacement was not confirmed. Keep the saved candidate and retry the original command. Check Fleet status, maintenance and execution blockers.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
