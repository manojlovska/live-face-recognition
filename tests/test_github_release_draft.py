from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_github_release_draft_exists() -> None:
    assert (DOCS / "github-release-draft-v0.1.0-rc1.md").exists()
    assert (DOCS / "internal-rc1-announcement.md").exists()


def test_github_release_draft_stays_candidate_only() -> None:
    draft = _read(DOCS / "github-release-draft-v0.1.0-rc1.md").lower()
    announcement = _read(DOCS / "internal-rc1-announcement.md").lower()
    handoff = _read(DOCS / "handoff.md").lower()

    assert "v0.1.0-rc1 — release candidate 1" in draft
    assert "release candidate, not a final release" in draft
    assert "not a final release" in draft
    assert "not identity verification" in draft or "not identity proof" in draft
    assert "legal/dataset review remains pending" in draft
    assert "local-machine-specific" in draft
    assert "92.756" in draft
    assert "94.117" in draft
    assert "104.155" in draft
    assert "v0.1.0-rc1" in draft
    assert ".env" not in draft
    assert "base64" not in draft
    assert "api key" not in draft

    assert "v0.1.0-rc1" in announcement
    assert "github release is not published yet" in announcement
    assert "legal/dataset approval remains pending" in announcement
    assert "security/privacy signoff remains pending" in announcement

    assert "work order 32" in handoff
