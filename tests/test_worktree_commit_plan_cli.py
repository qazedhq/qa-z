"""CLI and compact-payload tests for the worktree commit plan helper."""

from __future__ import annotations

import json

from tests.worktree_commit_plan_test_support import (
    commit_tracked_file,
    init_git_repository,
    load_plan_module,
    run_plan_cli,
)


def test_commit_plan_can_write_json_output_file(tmp_path) -> None:
    module = load_plan_module()
    payload = module.analyze_status_lines([" M src/qa_z/benchmark.py"])
    output_path = tmp_path / "evidence" / "worktree-commit-plan.json"

    module.write_json_output(payload, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8"))["kind"] == (
        "qa_z.worktree_commit_plan"
    )
    assert output_path.read_text(encoding="utf-8").endswith("\n")


def test_commit_plan_compact_payload_omits_full_batch_path_lists() -> None:
    module = load_plan_module()
    payload = module.analyze_status_lines(
        [
            " M README.md",
            " M src/qa_z/benchmark.py",
            "?? benchmarks/results-l2-full/summary.json",
        ],
        fail_on_cross_cutting=True,
    )

    compact = module.compact_payload(payload)

    assert "batches" not in compact
    assert compact["summary"] == payload["summary"]
    assert compact["attention_reasons"] == ["cross_cutting_paths_present"]
    assert compact["generated_artifact_paths"] == ["benchmarks/results-l2-full/"]
    assert compact["cross_cutting_paths"] == ["README.md"]
    assert compact["cross_cutting_groups"] == [
        {
            "id": "public_docs_contract",
            "title": "Public docs and schema contract",
            "path_count": 1,
            "paths": ["README.md"],
            "patch_command": ["git", "add", "--patch", "--", "README.md"],
            "patch_command_text": "git add --patch -- README.md",
        }
    ]
    assert compact["changed_batches"] == [
        {
            "id": "benchmark_coverage",
            "title": "Benchmark coverage",
            "message": "Keep benchmark runtime, fixtures, and regression evidence together.",
            "changed_count": 1,
            "staging_plan": {
                "include_path_count": 1,
                "include_paths": ["src/qa_z/benchmark.py"],
                "git_add_command": ["git", "add", "--", "src/qa_z/benchmark.py"],
                "git_add_command_text": "git add -- src/qa_z/benchmark.py",
            },
            "validation_commands": [
                "python -m pytest tests/test_benchmark.py -q",
                "python -m qa_z benchmark --results-dir .qa-z/tmp/benchmark-results --json",
            ],
        }
    ]


def test_commit_plan_compact_payload_reports_truncated_previews() -> None:
    module = load_plan_module()
    payload = {
        "kind": "qa_z.worktree_commit_plan",
        "schema_version": 1,
        "generated_at": "2026-04-23T00:00:00Z",
        "status": "attention_required",
        "strict_mode": {},
        "summary": {},
        "attention_reasons": [],
        "next_actions": [],
        "cross_cutting_paths": [f"README-{index}.md" for index in range(25)],
        "cross_cutting_groups": [
            {
                "id": f"group-{index}",
                "path_count": 25,
                "paths": [f"path-{item}.md" for item in range(25)],
                "patch_command": [
                    "git",
                    "add",
                    "--patch",
                    "--",
                    *[f"path-{item}.md" for item in range(25)],
                ],
            }
            for index in range(25)
        ],
        "batches": [],
    }

    compact = module.compact_payload(payload)

    assert len(compact["cross_cutting_paths"]) == 20
    assert compact["cross_cutting_paths_truncated_count"] == 5
    assert len(compact["cross_cutting_groups"]) == 20
    assert compact["cross_cutting_groups_truncated_count"] == 5
    assert compact["cross_cutting_groups"][0]["paths"] == [
        f"path-{item}.md" for item in range(20)
    ]
    assert compact["cross_cutting_groups"][0]["paths_truncated_count"] == 5
    assert compact["cross_cutting_groups"][0]["patch_command"] == [
        "git",
        "add",
        "--patch",
        "--",
        *[f"path-{item}.md" for item in range(25)],
    ]
    assert compact["cross_cutting_groups"][0]["patch_command_text"].startswith(
        "git add --patch -- path-0.md"
    )


def test_commit_plan_compact_payload_truncates_large_changed_batch_staging() -> None:
    module = load_plan_module()
    payload = {
        "kind": "qa_z.worktree_commit_plan",
        "schema_version": 1,
        "generated_at": "2026-04-23T00:00:00Z",
        "status": "ready",
        "strict_mode": {},
        "summary": {},
        "attention_reasons": [],
        "next_actions": [],
        "batches": [
            {
                "id": "large-batch",
                "title": "Large batch",
                "message": "Large staging surface.",
                "changed_count": 25,
                "changed_paths": [f"src/file_{index}.py" for index in range(25)],
                "validation_commands": ["python -m pytest -q"],
                "staging_plan": {
                    "include_paths": [f"src/file_{index}.py" for index in range(25)],
                    "git_add_command": [
                        "git",
                        "add",
                        "--",
                        *[f"src/file_{index}.py" for index in range(25)],
                    ],
                },
            }
        ],
    }

    compact = module.compact_payload(payload)
    staging_plan = compact["changed_batches"][0]["staging_plan"]

    assert staging_plan["include_path_count"] == 25
    assert staging_plan["include_paths"] == [
        f"src/file_{index}.py" for index in range(20)
    ]
    assert staging_plan["include_paths_truncated_count"] == 5
    assert "git_add_command" not in staging_plan
    assert "git_add_command_text" not in staging_plan


def test_commit_plan_compact_payload_quotes_command_text_paths_with_spaces() -> None:
    module = load_plan_module()
    payload = module.analyze_status_lines(
        [
            ' M "benchmarks/fixtures/path with space/expected.json"',
            ' M "docs/reports/path with space.md"',
        ],
        fail_on_cross_cutting=True,
    )

    compact = module.compact_payload(payload)

    assert (
        compact["changed_batches"][0]["staging_plan"]["git_add_command_text"]
        == 'git add -- "benchmarks/fixtures/path with space/expected.json"'
    )
    assert compact["cross_cutting_groups"][0]["patch_command_text"] == (
        'git add --patch -- "docs/reports/path with space.md"'
    )


def test_commit_plan_cli_output_file_preserves_strict_artifact_fields(
    monkeypatch, tmp_path, capsys
) -> None:
    module = load_plan_module()
    output_path = tmp_path / "evidence" / "worktree-commit-plan.json"

    monkeypatch.setattr(
        module,
        "git_status_lines",
        lambda *_args, **_kwargs: [
            "?? dist/alpha-release-gate.json",
            " M README.md",
        ],
    )
    monkeypatch.setattr(
        module,
        "repository_context",
        lambda *_args, **_kwargs: {"branch": "codex/qa-z-bootstrap", "head": "abc123"},
    )

    exit_code = module.main(
        [
            "--output",
            str(output_path),
            "--fail-on-generated",
            "--fail-on-cross-cutting",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out)
    written_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert stdout_payload == written_payload
    assert written_payload["output_path"] == str(output_path)
    assert written_payload["strict_mode"] == {
        "fail_on_generated": True,
        "fail_on_cross_cutting": True,
    }
    assert written_payload["summary"]["attention_reason_count"] == 2
    assert written_payload["attention_reasons"] == [
        "generated_artifacts_present",
        "cross_cutting_paths_present",
    ]


def test_commit_plan_cli_summary_only_json_writes_compact_payload(
    monkeypatch, tmp_path, capsys
) -> None:
    module = load_plan_module()
    output_path = tmp_path / "evidence" / "compact-worktree-plan.json"

    monkeypatch.setattr(
        module,
        "git_status_lines",
        lambda *_args, **_kwargs: [
            " M README.md",
            " M src/qa_z/benchmark.py",
        ],
    )
    monkeypatch.setattr(
        module,
        "repository_context",
        lambda *_args, **_kwargs: {"branch": "codex/qa-z-bootstrap", "head": "abc123"},
    )

    exit_code = module.main(
        [
            "--summary-only",
            "--output",
            str(output_path),
            "--fail-on-cross-cutting",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out)
    written_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert stdout_payload == written_payload
    assert "batches" not in written_payload
    assert written_payload["output_path"] == str(output_path)
    assert written_payload["repository"] == {
        "branch": "codex/qa-z-bootstrap",
        "head": "abc123",
    }
    assert written_payload["changed_batches"] == [
        {
            "id": "benchmark_coverage",
            "title": "Benchmark coverage",
            "message": "Keep benchmark runtime, fixtures, and regression evidence together.",
            "changed_count": 1,
            "staging_plan": {
                "include_path_count": 1,
                "include_paths": ["src/qa_z/benchmark.py"],
                "git_add_command": ["git", "add", "--", "src/qa_z/benchmark.py"],
                "git_add_command_text": "git add -- src/qa_z/benchmark.py",
            },
            "validation_commands": [
                "python -m pytest tests/test_benchmark.py -q",
                "python -m qa_z benchmark --results-dir .qa-z/tmp/benchmark-results --json",
            ],
        }
    ]


def test_commit_plan_cli_reports_output_write_failure(monkeypatch, tmp_path, capsys):
    module = load_plan_module()

    monkeypatch.setattr(
        module,
        "git_status_lines",
        lambda *_args, **_kwargs: [" M src/qa_z/benchmark.py"],
    )
    monkeypatch.setattr(
        module,
        "repository_context",
        lambda *_args, **_kwargs: {"branch": "codex/qa-z-bootstrap", "head": "abc123"},
    )

    def fail_write_json_output(_payload, _output_path):
        raise OSError("permission denied")

    monkeypatch.setattr(module, "write_json_output", fail_write_json_output)

    exit_code = module.main(["--output", str(tmp_path / "blocked.json")])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "worktree commit plan failed: could not write output" in captured.err
    assert str(tmp_path / "blocked.json") in captured.err
    assert "permission denied" in captured.err


def test_commit_plan_can_fail_when_generated_artifacts_are_present() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.json",
            " M src/qa_z/benchmark.py",
        ],
        fail_on_generated=True,
    )

    assert result["status"] == "attention_required"
    assert result["strict_mode"] == {
        "fail_on_generated": True,
        "fail_on_cross_cutting": False,
    }
    assert result["summary"]["attention_reason_count"] == 1
    assert result["generated_artifact_paths"] == ["dist/"]
    assert "generated_artifacts_present" in result["attention_reasons"]


def test_commit_plan_can_fail_when_cross_cutting_paths_need_patch_add() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M README.md",
            " M src/qa_z/benchmark.py",
        ],
        fail_on_cross_cutting=True,
    )

    assert result["status"] == "attention_required"
    assert result["strict_mode"] == {
        "fail_on_generated": False,
        "fail_on_cross_cutting": True,
    }
    assert result["summary"]["attention_reason_count"] == 1
    assert result["cross_cutting_paths"] == ["README.md"]
    assert "cross_cutting_paths_present" in result["attention_reasons"]


def test_commit_plan_can_fail_when_report_paths_need_patch_add() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M docs/reports/current-state-analysis.md",
            " M src/qa_z/benchmark.py",
        ],
        fail_on_cross_cutting=True,
    )

    assert result["status"] == "attention_required"
    assert result["strict_mode"] == {
        "fail_on_generated": False,
        "fail_on_cross_cutting": True,
    }
    assert result["summary"]["attention_reason_count"] == 1
    assert result["report_paths"] == ["docs/reports/current-state-analysis.md"]
    assert result["cross_cutting_paths"] == []
    assert result["cross_cutting_groups"][0]["id"] == "status_reports"
    assert "cross_cutting_paths_present" in result["attention_reasons"]


def test_commit_plan_cli_batch_preserves_strict_cross_cutting_exit(
    monkeypatch, capsys
) -> None:
    module = load_plan_module()

    monkeypatch.setattr(
        module,
        "git_status_lines",
        lambda *_args, **_kwargs: [
            " M README.md",
            " M src/qa_z/benchmark.py",
        ],
    )
    monkeypatch.setattr(
        module,
        "repository_context",
        lambda *_args, **_kwargs: {"branch": "codex/qa-z-bootstrap", "head": "abc123"},
    )

    exit_code = module.main(
        ["--batch", "benchmark_coverage", "--fail-on-cross-cutting", "--json"]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["status"] == "attention_required"
    assert payload["strict_mode"] == {
        "fail_on_generated": False,
        "fail_on_cross_cutting": True,
    }
    assert payload["attention_reasons"] == ["cross_cutting_paths_present"]
    assert payload["global_attention_reason_count"] == 1
    assert payload["selected_batch_summary"]["status"] == "ready"
    assert payload["selected_batch_summary"]["attention_reason_count"] == 1


def test_commit_plan_compact_selected_batch_staging_keeps_patch_add_command() -> None:
    module = load_plan_module()
    payload = module.analyze_status_lines(
        [
            " M README.md",
            " M src/qa_z/benchmark.py",
        ],
        fail_on_cross_cutting=True,
    )
    filtered = module.filter_payload_for_batch(payload, "benchmark_coverage")

    compact = module.compact_payload(filtered)
    staging_plan = compact["changed_batches"][0]["staging_plan"]

    assert staging_plan["candidate_patch_add_count"] == 1
    assert staging_plan["candidate_patch_add_paths"] == ["README.md"]
    assert staging_plan["git_add_patch_command"] == [
        "git",
        "add",
        "--patch",
        "--",
        "README.md",
    ]
    assert staging_plan["git_add_patch_command_text"] == (
        "git add --patch -- README.md"
    )


def test_commit_plan_script_entrypoint_prints_json_payload(tmp_path) -> None:
    init_git_repository(tmp_path)
    benchmark_path = commit_tracked_file(
        tmp_path,
        "src/qa_z/benchmark.py",
        "print('baseline benchmark')\n",
    )
    benchmark_path.write_text("print('updated benchmark')\n", encoding="utf-8")

    result = run_plan_cli(tmp_path, "--json")

    payload = json.loads(result.stdout)
    batches = {batch["id"]: batch for batch in payload["batches"]}
    assert result.returncode == 0
    assert result.stderr == ""
    assert payload["kind"] == "qa_z.worktree_commit_plan"
    assert batches["benchmark_coverage"]["changed_paths"] == ["src/qa_z/benchmark.py"]
    assert payload["status"] == "ready"


def test_commit_plan_script_entrypoint_writes_output_in_strict_mode(tmp_path) -> None:
    init_git_repository(tmp_path)
    generated_path = tmp_path / "dist" / "alpha-release-gate.json"
    generated_path.parent.mkdir(parents=True, exist_ok=True)
    generated_path.write_text("{}", encoding="utf-8")
    output_path = tmp_path / "evidence" / "worktree-commit-plan.json"

    result = run_plan_cli(
        tmp_path,
        "--json",
        "--fail-on-generated",
        "--output",
        str(output_path),
    )

    stdout_payload = json.loads(result.stdout)
    written_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert result.stderr == ""
    assert stdout_payload == written_payload
    assert written_payload["status"] == "attention_required"
    assert written_payload["attention_reasons"] == ["generated_artifacts_present"]
    assert written_payload["output_path"] == str(output_path)
