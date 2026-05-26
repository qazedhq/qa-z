from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WALKTHROUGH_PATH = ROOT / "docs" / "walkthroughs" / "verify-baseline-candidate.md"
REPAIR_VERIFY_PATH = ROOT / "docs" / "repair-verify-workflow.md"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_verify_baseline_candidate_walkthrough_exists() -> None:
    assert WALKTHROUGH_PATH.is_file()
    assert REPAIR_VERIFY_PATH.is_file()


def test_verify_baseline_candidate_walkthrough_pins_commands_and_artifacts() -> None:
    walkthrough = WALKTHROUGH_PATH.read_text(encoding="utf-8")

    for command in (
        "qa-z fast --output-dir .qa-z/runs/baseline",
        "qa-z deep --from-run .qa-z/runs/baseline",
        "qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex",
        "qa-z verify --from-run .qa-z/runs/baseline",
        "qa-z fast --output-dir .qa-z/runs/candidate",
        "qa-z deep --from-run .qa-z/runs/candidate",
        "qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate",
    ):
        assert command in walkthrough

    for artifact_path in (
        ".qa-z/runs/baseline/fast/summary.json",
        ".qa-z/runs/baseline/deep/summary.json",
        ".qa-z/runs/baseline/repair/codex.md",
        ".qa-z/runs/candidate/fast/summary.json",
        ".qa-z/runs/candidate/deep/summary.json",
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/compare.json",
        ".qa-z/runs/candidate/verify/report.md",
    ):
        assert artifact_path in walkthrough


def test_verify_baseline_candidate_walkthrough_explains_verdicts() -> None:
    walkthrough = WALKTHROUGH_PATH.read_text(encoding="utf-8")

    for expected_text in (
        "`improved` means the candidate reduced blockers without new regressions.",
        "`mixed` means some issues improved but new or remaining issues need review.",
        "`regressed` means the candidate is worse than the baseline.",
        "`unchanged` means the candidate did not materially improve the baseline.",
        "`verification_failed` means the comparison could not complete; rerun or inspect artifacts.",
        "deterministic and does not rely on LLM-only judgment",
    ):
        assert expected_text in walkthrough


def test_verify_baseline_candidate_walkthrough_pins_generated_artifact_policy() -> None:
    walkthrough = WALKTHROUGH_PATH.read_text(encoding="utf-8")

    for expected_text in (
        "Generated root `.qa-z/**` stays local",
        "Do not commit generated `.qa-z/**` runtime evidence",
        "intentionally frozen with context",
    ):
        assert expected_text in walkthrough


def test_docs_index_links_verify_baseline_candidate_walkthrough() -> None:
    docs_index = read("docs/README.md")

    assert (
        "[Verify baseline/candidate](walkthroughs/verify-baseline-candidate.md) | "
        "Compare repaired candidates against baseline QA-Z evidence"
    ) in docs_index
    assert (
        "[Repair -> verify workflow](repair-verify-workflow.md) | "
        "First-class loop from guard verdict to repair prompt to deterministic verification"
    ) in docs_index


def test_repair_verify_workflow_pins_short_loop_and_boundaries() -> None:
    workflow = REPAIR_VERIFY_PATH.read_text(encoding="utf-8")

    for expected in (
        "qa-z guard --from-run latest --adapter codex",
        "qa-z repair-prompt --from-run latest --adapter codex",
        "qa-z verify --from-run latest",
        "qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate",
        "worse (regressed)",
        "does not call live model APIs",
        "does not call live model APIs, run an external agent",
        "publish packages",
    ):
        assert expected in workflow
