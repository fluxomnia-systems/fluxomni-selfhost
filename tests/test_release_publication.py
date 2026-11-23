import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/check-release-publication.py"
spec = importlib.util.spec_from_file_location("release_publication", MODULE)
assert spec is not None and spec.loader is not None
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)

MANIFEST = {
    "latestStable": "v26.4.1",
    "releases": {
        "v26.4.1": {"selfhostRef": "v26.4.1"},
        "v26.3.2": {"selfhostRef": "v26.3.2", "installerBundleRef": "a" * 40, "installerPath": "install.sh"},
    },
}


def test_all_stable_tags_and_matching_assets_are_required():
    calls = []

    def available(ref, path):
        calls.append((ref, path))
        return True

    assert publication.publication_errors(MANIFEST, {"v26.4.1", "v26.3.2"}, available) == []
    assert calls == [("v26.4.1", "scripts/install-runtime.sh"), ("a" * 40, "install.sh")]
    errors = publication.publication_errors(MANIFEST, set(), available)
    assert any("latestStable v26.4.1 has no published" in error for error in errors)
    assert any("selfhostRef v26.3.2 has no published" in error for error in errors)


def test_a_published_tag_without_its_installer_does_not_pass():
    errors = publication.publication_errors(MANIFEST, {"v26.4.1", "v26.3.2"}, lambda ref, _: ref != "v26.4.1")
    assert len(errors) == 1
    assert "v26.4.1/scripts/install-runtime.sh did not return HTTP 200" in errors[0]
