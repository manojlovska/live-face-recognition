from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_rc1_signoff_artifacts_exist() -> None:
    assert (DOCS / "rc1-signoff-request.md").exists()
    assert (DOCS / "rc1-approval-decision-template.md").exists()
    assert (DOCS / "rc1-review-comment-template.md").exists()


def test_rc1_signoff_docs_cover_expected_gates() -> None:
    request = _read(DOCS / "rc1-signoff-request.md").lower()
    decision = _read(DOCS / "rc1-approval-decision-template.md").lower()
    comment = _read(DOCS / "rc1-review-comment-template.md").lower()
    notes = _read(DOCS / "rc1-human-approval-notes.md").lower()
    handoff = _read(DOCS / "handoff.md").lower()
    current_state = _read(DOCS / "current-state.md").lower()
    release_readiness = _read(DOCS / "release-readiness.md").lower()

    combined = "\n".join([request, decision, comment, notes])

    assert "v0.1.0-rc1" in combined
    assert "release candidate, not a final release" in combined
    assert "not identity verification" in combined or "not verification" in combined
    assert "approved for internal controlled-pilot rc publication" in combined
    assert "permission to publish github release: yes" in combined
    assert "final release publication" in combined
    assert "commercial-ready" in combined
    assert ".env" in combined and "not committed" in combined
    assert "local-machine-specific" in combined
    assert "work order 31" in handoff
    assert "engineering | anastasija manojlovska | approved | 2026-06-16" in notes
    assert "security/privacy | anastasija manojlovska | approved | 2026-06-16" in notes
    assert "dataset/legal | anastasija manojlovska | approved | 2026-06-16" in notes
    assert "pilot operator | anastasija manojlovska | approved | 2026-06-16" in notes
    assert "final release approver | anastasija manojlovska | approved | 2026-06-16" in notes
    assert "permission to publish github release: yes" in notes
    assert "human sign-offs for v0.1.0-rc1 have been recorded" in current_state
    assert "approved for internal controlled-pilot rc publication" in release_readiness
    assert "| tbd | pending | tbd |" not in notes
