from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_rc1_release_package_documents_exist() -> None:
    assert (DOCS / "rc1-human-approval-notes.md").exists()
    assert (DOCS / "rc1-release-checklist.md").exists()
    assert (DOCS / "rc1-release-manifest.md").exists()


def test_rc1_release_package_stays_candidate_only() -> None:
    readme = _read(ROOT / "README.md").lower()
    release_notes = _read(DOCS / "release-notes-rc1.md").lower()
    approval_notes = _read(DOCS / "rc1-human-approval-notes.md").lower()
    checklist = _read(DOCS / "rc1-release-checklist.md").lower()
    manifest = _read(DOCS / "rc1-release-manifest.md").lower()
    release_readiness = _read(DOCS / "release-readiness.md").lower()
    handoff = _read(DOCS / "handoff.md").lower()

    assert "rc1 release package" in readme
    assert "does not imply a final release" in readme
    assert "release-candidate draft, not a final release" in release_notes
    assert "v0.1.0-rc1" in release_notes
    assert "approved for internal controlled-pilot rc publication" in release_notes
    assert "legal/dataset review remains pending" in release_notes
    assert "does not claim commercial readiness" in release_notes
    assert "not identity verification" in approval_notes
    assert "human legal/dataset approval remains required" in approval_notes
    assert "gallery artifacts were generated locally and are not committed" in approval_notes
    assert "raw benchmark reports are not committed" in approval_notes
    assert "api keys are not committed" in approval_notes
    assert ".env" in approval_notes and "not committed" in approval_notes
    assert "git tag -a v0.1.0-rc1" in checklist
    assert "run the tag commands only after human approval" in checklist
    assert "v0.1.0-rc1" in manifest
    assert "excluded artifacts" in manifest
    assert "approved for internal controlled-pilot rc publication" in release_readiness
    assert "work order 32" in handoff
