from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_post_publication_artifacts_exist() -> None:
    assert (DOCS / "rc1-post-publication-verification.md").exists()
    assert (DOCS / "pilot-operator-onboarding.md").exists()


def test_post_publication_and_onboarding_docs_cover_release_ops() -> None:
    verification = _read(DOCS / "rc1-post-publication-verification.md").lower()
    onboarding = _read(DOCS / "pilot-operator-onboarding.md").lower()
    handoff = _read(DOCS / "handoff.md").lower()
    current_state = _read(DOCS / "current-state.md").lower()

    assert "v0.1.0-rc1" in verification
    assert "release candidate" in verification
    assert "not a final release" in verification
    assert (
        "https://github.com/manojlovska/live-face-recognition/releases/tag/v0.1.0-rc1"
        in verification
    )
    assert "no release assets are attached" in verification
    assert "local-machine-specific" in verification
    assert "v0.1.0-rc1" in onboarding
    assert "not identity verification" in onboarding
    assert "operators must supply authorized model and gallery assets locally" in onboarding
    assert "/healthz" in onboarding
    assert "/readyz" in onboarding
    assert "/demo" in onboarding
    assert "change-me-local-dev-key" in onboarding
    assert "pilot-operator onboarding documentation exists" in current_state
    assert "work order 32" in handoff
