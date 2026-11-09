"""Tests for scripts/auto-https.sh host classification and asset rendering."""

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "auto-https.sh"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def classify(host: str) -> str:
    result = run("classify", host)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_public_domains_classify_as_domain() -> None:
    for host in ["example.com", "stream.Example.COM", "a.b.example.org"]:
        assert classify(host) == "domain", host


def test_public_ipv4_addresses_classify_as_public_ip() -> None:
    for host in [
        "8.8.8.8",
        "1.1.1.1",
        "203.0.113.10".replace("203.0.113.10", "93.184.216.34"),
    ]:
        assert classify(host) == "public-ip", host


def test_private_and_special_ipv4_stay_local() -> None:
    for host in [
        "127.0.0.1",
        "10.0.0.1",
        "192.168.1.5",
        "172.16.5.4",
        "169.254.1.1",
        "100.64.1.1",
        "0.1.2.3",
        "203.0.113.10",
        "198.51.100.7",
        "198.18.0.1",
        "224.0.0.1",
    ]:
        assert classify(host) == "local", host


def test_public_ipv6_classifies_as_public_ip() -> None:
    assert classify("2606:4700:4700::1111") == "public-ip"


def test_special_ipv6_and_names_stay_local() -> None:
    for host in [
        "::1",
        "fe80::1",
        "fd00::1",
        "2001:db8::1",
        "2001:2::1",
        "3fff::1",
        "64:ff9b:1::1",
        "100::1",
        "localhost",
        "router.local",
        "printer.alt",
        "app.example",
        "home.arpa",
        "router.home.arpa",
    ]:
        assert classify(host) == "local", host


def test_invalid_hosts_are_rejected() -> None:
    for host in ["", "bad host", "example.com/path", "exa_mple.com"]:
        result = run("classify", host)
        assert result.returncode != 0, host


def test_render_caddyfile_domain_uses_plain_acme(tmp_path: Path) -> None:
    out = tmp_path / "Caddyfile"
    result = run("render-caddyfile", "stream.example.com", str(out))
    assert result.returncode == 0, result.stderr
    text = out.read_text()
    assert text.startswith("stream.example.com {")
    assert "shortlived" not in text
    assert "reverse_proxy frontend:80" in text


def test_render_caddyfile_public_ipv4_uses_shortlived_profile(tmp_path: Path) -> None:
    out = tmp_path / "Caddyfile"
    result = run("render-caddyfile", "8.8.8.8", str(out))
    assert result.returncode == 0, result.stderr
    text = out.read_text()
    assert 'default_sni "8.8.8.8"' in text
    assert "profile shortlived" in text
    assert "disable_tlsalpn_challenge" in text
    assert "8.8.8.8 {" in text


def test_render_caddyfile_public_ipv6_brackets_site_address(tmp_path: Path) -> None:
    out = tmp_path / "Caddyfile"
    result = run("render-caddyfile", "2606:4700:4700::1111", str(out))
    assert result.returncode == 0, result.stderr
    assert "[2606:4700:4700::1111] {" in out.read_text()


def test_render_caddyfile_refuses_private_host(tmp_path: Path) -> None:
    out = tmp_path / "Caddyfile"
    result = run("render-caddyfile", "192.168.1.5", str(out))
    assert result.returncode != 0
    assert not out.exists()


def test_compose_override_adds_caddy_service(tmp_path: Path) -> None:
    result = run("compose-override", str(tmp_path))
    assert result.returncode == 0, result.stderr
    text = (tmp_path / "docker-compose.https.yml").read_text()
    assert "caddy:" in text
    assert '"80:80"' in text and '"443:443"' in text
    assert "./Caddyfile.auto-https:/etc/caddy/Caddyfile:ro" in text
    assert "caddy_data" in text
