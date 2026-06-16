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

    combined = "\n".join([request, decision, comment, notes])

    assert "v0.1.0-rc1" in combined
    assert "release candidate, not a final release" in combined
    assert "not identity verification" in combined or "not verification" in combined
    assert "dataset/legal approval remains pending" in combined
    assert "approved with conditions" in combined
    assert "final release publication" in combined
    assert "commercial-ready" in combined
    assert ".env" in combined and "not committed" in combined
    assert "local-machine-specific" in combined
    assert "approvals are complete" not in combined
    assert "work order 29" in handoff
    assert "engineering" in notes
    assert "security/privacy" in notes
    assert "dataset/legal" in notes
    assert "pilot operator" in notes
    assert "final release approver" in notes
    assert "pending" in notes
    assert "do not change `pending` to `approved`" in notes
