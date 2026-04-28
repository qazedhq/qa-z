"""Tests for the runtime artifact cleanup helper."""

from __future__ import annotations

import json
from pathlib import Path

from tests.runtime_artifact_cleanup_test_support import FakeRunner, load_cleanup_module


def write_file(path: Path, text: str = "artifact") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cleanup_runner(
    status_lines: list[str], *responses: tuple[tuple[str, ...], tuple[int, str, str]]
) -> FakeRunner:
    return FakeRunner(
        {
            (
                "git",
                "status",
                "--short",
                "--ignored",
                "--untracked-files=all",
            ): (0, "\n".join(status_lines), ""),
            **{command: result for command, result in responses},
        }
    )


def test_cleanup_plan_collects_helper_derived_policy_roots_for_review(
    tmp_path: Path,
) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json", "{}")
    write_file(tmp_path / ".pytest_cache" / "v" / "cache" / "nodeids", "[]")
    write_file(tmp_path / ".mypy_cache_safe" / "3.10" / "cache.db", "{}")
    write_file(tmp_path / "src" / "qa_z" / "__pycache__" / "models.pyc")
    write_file(tmp_path / "benchmarks" / "results" / "work" / "repo" / "stdout.txt")
    write_file(tmp_path / "benchmarks" / "results-analysis" / "report.md")
    write_file(tmp_path / "benchmarks" / "results" / "summary.json")
    runner = cleanup_runner(
        [
            "!! .pytest_cache/v/cache/nodeids",
            "?? .mypy_cache_safe/3.10/cache.db",
            "?? .qa-z/loops/latest/self_inspect.json",
            "!! benchmarks/results/work/repo/stdout.txt",
            "?? benchmarks/results/summary.json",
            "?? benchmarks/results-analysis/report.md",
            "!! src/qa_z/__pycache__/models.pyc",
        ],
        (("git", "ls-files", "--", ".pytest_cache"), (0, "", "")),
        (("git", "ls-files", "--", ".mypy_cache_safe"), (0, "", "")),
        (("git", "ls-files", "--", ".qa-z"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/results/work"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/results"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/results-analysis"), (0, "", "")),
        (("git", "ls-files", "--", "src/qa_z/__pycache__"), (0, "", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    candidates = {item["path"]: item for item in payload["candidates"]}

    assert payload["counts"] == {
        "planned": 5,
        "review_local_by_default": 2,
        "skipped_tracked": 0,
        "deleted": 0,
    }
    assert candidates[".pytest_cache"]["policy_bucket"] == "local_only"
    assert candidates[".pytest_cache"]["status"] == "planned"
    assert candidates[".mypy_cache_safe"]["policy_bucket"] == "local_only"
    assert candidates[".mypy_cache_safe"]["status"] == "planned"
    assert candidates[".qa-z"]["policy_bucket"] == "local_only"
    assert candidates[".qa-z"]["status"] == "planned"
    assert candidates["src/qa_z/__pycache__"]["policy_bucket"] == "local_only"
    assert candidates["src/qa_z/__pycache__"]["status"] == "planned"
    assert candidates["benchmarks/results/work"]["policy_bucket"] == "local_only"
    assert candidates["benchmarks/results/work"]["status"] == "planned"
    assert candidates["benchmarks/results-analysis"]["policy_bucket"] == (
        "local_by_default"
    )
    assert candidates["benchmarks/results-analysis"]["status"] == (
        "review_local_by_default"
    )
    assert candidates["benchmarks/results"]["policy_bucket"] == "local_by_default"
    assert candidates["benchmarks/results"]["status"] == "review_local_by_default"
    assert candidates["benchmarks/results"]["tracked_paths"] == []


def test_cleanup_collects_literal_percent_temp_benchmark_output_as_local_only(
    tmp_path: Path,
) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / "%TEMP%" / "qa-z-l27-full-benchmark" / "summary.json", "{}")
    runner = cleanup_runner(
        [
            "?? %TEMP%/qa-z-l27-full-benchmark/summary.json",
            "?? %TEMP%/qa-z-l27-full-benchmark/report.md",
        ],
        (("git", "ls-files", "--", "%TEMP%"), (0, "", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    candidates = {item["path"]: item for item in payload["candidates"]}

    assert candidates["%TEMP%"]["policy_bucket"] == "local_only"
    assert candidates["%TEMP%"]["status"] == "planned"
    assert payload["counts"] == {
        "planned": 1,
        "review_local_by_default": 0,
        "skipped_tracked": 0,
        "deleted": 0,
    }


def test_cleanup_collects_root_tmp_scratch_outputs_as_local_only(
    tmp_path: Path,
) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / "tmp_mypy_smoke.py", "x: int = 1")
    write_file(tmp_path / "tmp_mypy_cache" / "3.10" / "cache.db", "{}")
    write_file(tmp_path / "tmp_rmtree_probe" / "x.txt", "x")
    runner = cleanup_runner(
        [
            "?? tmp_mypy_smoke.py",
            "?? tmp_mypy_cache/3.10/cache.db",
            "?? tmp_rmtree_probe/x.txt",
        ],
        (("git", "ls-files", "--", "tmp_mypy_smoke.py"), (0, "", "")),
        (("git", "ls-files", "--", "tmp_mypy_cache"), (0, "", "")),
        (("git", "ls-files", "--", "tmp_rmtree_probe"), (0, "", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    candidates = {item["path"]: item for item in payload["candidates"]}

    assert candidates["tmp_mypy_smoke.py"]["policy_bucket"] == "local_only"
    assert candidates["tmp_mypy_cache"]["policy_bucket"] == "local_only"
    assert candidates["tmp_rmtree_probe"]["policy_bucket"] == "local_only"
    assert payload["counts"] == {
        "planned": 3,
        "review_local_by_default": 0,
        "skipped_tracked": 0,
        "deleted": 0,
    }


def test_cleanup_collects_benchmark_minlock_probe_outputs_as_local_only(
    tmp_path: Path,
) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / "benchmarks" / "minlock-plain.txt", "x")
    write_file(tmp_path / "benchmarks" / "minlock-repro" / ".benchmark.lock", "pid=1")
    write_file(tmp_path / "benchmarks" / "minlock-x.txt", "x")
    runner = cleanup_runner(
        [
            "?? benchmarks/minlock-plain.txt",
            "?? benchmarks/minlock-repro/.benchmark.lock",
            "?? benchmarks/minlock-x.txt",
        ],
        (("git", "ls-files", "--", "benchmarks/minlock-plain.txt"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/minlock-repro"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/minlock-x.txt"), (0, "", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    candidates = {item["path"]: item for item in payload["candidates"]}

    assert candidates["benchmarks/minlock-plain.txt"]["policy_bucket"] == "local_only"
    assert candidates["benchmarks/minlock-repro"]["policy_bucket"] == "local_only"
    assert candidates["benchmarks/minlock-x.txt"]["policy_bucket"] == "local_only"
    assert payload["counts"] == {
        "planned": 3,
        "review_local_by_default": 0,
        "skipped_tracked": 0,
        "deleted": 0,
    }


def test_cleanup_apply_does_not_delete_local_by_default_benchmark_roots(
    tmp_path: Path,
) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / ".qa-z" / "runs" / "latest" / "summary.json", "{}")
    write_file(
        tmp_path / "benchmarks" / "results" / "work" / "repo" / "stdout.txt", "{}"
    )
    write_file(tmp_path / "benchmarks" / "results-l2-full" / "summary.json", "{}")
    write_file(tmp_path / "benchmarks" / "results" / "summary.json", "{}")
    runner = cleanup_runner(
        [
            "?? .qa-z/runs/latest/summary.json",
            "!! benchmarks/results/work/repo/stdout.txt",
            "?? benchmarks/results/summary.json",
            "?? benchmarks/results-l2-full/summary.json",
        ],
        (("git", "ls-files", "--", ".qa-z"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/results/work"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/results"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/results-l2-full"), (0, "", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner, apply=True)
    candidates = {item["path"]: item for item in payload["candidates"]}

    assert candidates[".qa-z"]["kind"] == "directory"
    assert candidates[".qa-z"]["status"] == "deleted"
    assert candidates["benchmarks/results/work"]["kind"] == "directory"
    assert candidates["benchmarks/results/work"]["status"] == "deleted"
    assert candidates["benchmarks/results-l2-full"]["status"] == (
        "review_local_by_default"
    )
    assert (
        candidates["benchmarks/results-l2-full"]["reason"]
        == "local-by-default benchmark evidence requires operator review"
    )
    assert candidates["benchmarks/results"]["status"] == "review_local_by_default"
    assert (
        candidates["benchmarks/results"]["reason"]
        == "local-by-default benchmark evidence requires operator review"
    )
    assert payload["counts"] == {
        "planned": 0,
        "review_local_by_default": 2,
        "skipped_tracked": 0,
        "deleted": 2,
    }
    assert not (tmp_path / ".qa-z").exists()
    assert not (tmp_path / "benchmarks" / "results" / "work").exists()
    assert (tmp_path / "benchmarks" / "results-l2-full").exists()
    assert (tmp_path / "benchmarks" / "results").exists()


def test_cleanup_human_output_reports_review_and_skip_counts(tmp_path: Path) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / ".qa-z" / "runs" / "latest" / "summary.json", "{}")
    write_file(tmp_path / "benchmarks" / "results" / "summary.json", "{}")
    runner = cleanup_runner(
        [
            "?? .qa-z/runs/latest/summary.json",
            "?? benchmarks/results/summary.json",
        ],
        (("git", "ls-files", "--", ".qa-z"), (0, "", "")),
        (("git", "ls-files", "--", "benchmarks/results"), (0, "", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    output = module.render_human(payload)

    assert "Mode: dry-run" in output
    assert "Planned deletions: 1" in output
    assert "Review-only local-by-default roots: 1" in output
    assert "Skipped tracked roots: 0" in output
    assert "- planned: .qa-z" in output
    assert "- review_local_by_default: benchmarks/results" in output
    assert "operator review" in output


def test_cleanup_skips_tracked_local_only_roots(tmp_path: Path) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / "dist" / "bundle.js")
    runner = cleanup_runner(
        [" M dist/bundle.js"],
        (("git", "ls-files", "--", "dist"), (0, "dist/bundle.js\n", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    candidates = {item["path"]: item for item in payload["candidates"]}

    assert candidates["dist"]["policy_bucket"] == "local_only"
    assert candidates["dist"]["status"] == "skipped_tracked"
    assert (
        candidates["dist"]["reason"]
        == "tracked paths present; cleanup will not delete this root"
    )
    assert candidates["dist"]["tracked_paths"] == ["dist/bundle.js"]
    assert payload["counts"] == {
        "planned": 0,
        "review_local_by_default": 0,
        "skipped_tracked": 1,
        "deleted": 0,
    }


def test_cleanup_apply_skips_tracked_local_only_roots_with_reason(
    tmp_path: Path,
) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / "tmp_keep" / "artifact.json", "{}")
    runner = cleanup_runner(
        [" M tmp_keep/artifact.json"],
        (("git", "ls-files", "--", "tmp_keep"), (0, "tmp_keep/artifact.json\n", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner, apply=True)
    candidates = {item["path"]: item for item in payload["candidates"]}
    output = module.render_human(payload)

    assert candidates["tmp_keep"]["policy_bucket"] == "local_only"
    assert candidates["tmp_keep"]["status"] == "skipped_tracked"
    assert candidates["tmp_keep"]["reason"] == (
        "tracked paths present; cleanup will not delete this root"
    )
    assert (tmp_path / "tmp_keep").exists()
    assert "- skipped_tracked: tmp_keep" in output
    assert "cleanup will not delete this root" in output
    assert payload["counts"] == {
        "planned": 0,
        "review_local_by_default": 0,
        "skipped_tracked": 1,
        "deleted": 0,
    }


def test_cleanup_ignores_fixture_local_seeded_runtime_inputs(tmp_path: Path) -> None:
    module = load_cleanup_module()
    write_file(
        tmp_path
        / "benchmarks"
        / "fixtures"
        / "seeded_case"
        / "repo"
        / ".qa-z"
        / "runs"
        / "baseline"
        / "summary.json",
        "{}",
    )
    write_file(tmp_path / "benchmarks" / "results" / "summary.json", "{}")
    runner = cleanup_runner(
        [
            "?? benchmarks/fixtures/seeded_case/repo/.qa-z/runs/baseline/summary.json",
            "?? benchmarks/results/summary.json",
        ],
        (("git", "ls-files", "--", "benchmarks/results"), (0, "", "")),
    )

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    candidate_paths = [item["path"] for item in payload["candidates"]]

    assert "benchmarks/fixtures/seeded_case/repo/.qa-z" not in candidate_paths
    assert candidate_paths == ["benchmarks/results"]
    assert payload["counts"] == {
        "planned": 0,
        "review_local_by_default": 1,
        "skipped_tracked": 0,
        "deleted": 0,
    }


def test_cleanup_main_prints_json_payload(monkeypatch, tmp_path: Path, capsys) -> None:
    module = load_cleanup_module()
    write_file(tmp_path / ".qa-z" / "runs" / "latest" / "summary.json", "{}")
    monkeypatch.chdir(tmp_path)

    runner = cleanup_runner(
        ["?? .qa-z/runs/latest/summary.json"],
        (("git", "ls-files", "--", ".qa-z"), (0, "", "")),
    )
    monkeypatch.setattr(module, "subprocess_runner", runner)

    exit_code = module.main(["--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["counts"] == {
        "planned": 1,
        "review_local_by_default": 0,
        "skipped_tracked": 0,
        "deleted": 0,
    }
    assert output["candidates"][0]["path"] == ".qa-z"
