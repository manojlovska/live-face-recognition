from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_release_documentation_artifacts_exist() -> None:
    assert (DOCS / "pilot-readiness-checklist.md").exists()
    assert (DOCS / "operator-runbook.md").exists()
    assert (DOCS / "release-notes-rc1.md").exists()


def test_readme_and_docs_avoid_identity_verification_claims() -> None:
    readme = _read(ROOT / "README.md")
    release_readiness = _read(DOCS / "release-readiness.md")
    release_notes = _read(DOCS / "release-notes-rc1.md")
    current_state = _read(DOCS / "current-state.md")

    assert "What this is not" in readme
    combined = "\n".join([readme, release_readiness, release_notes, current_state]).lower()
    assert "not identity verification" in combined or "not identity proof" in combined
    assert "commercially ready" not in combined
    assert "bundled celeba" not in combined
    assert "bundled onnx" not in combined


def test_benchmark_results_remain_a_template() -> None:
    benchmark_results = _read(DOCS / "benchmark-results.md")

    assert "No authoritative benchmark results are recorded yet." in benchmark_results
    assert "Latency metric" in benchmark_results
    assert "5.0" not in benchmark_results
    assert "18.1" not in benchmark_results
    assert "0.84" not in benchmark_results


def test_handoff_points_to_next_work_order() -> None:
    handoff = _read(DOCS / "handoff.md")

    assert "Work Order 21: Run a full RC validation pass on a Docker-capable machine" in handoff
