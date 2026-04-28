"""Tests for fast-runner smart check selection."""

from __future__ import annotations

import json
from textwrap import dedent

import yaml

from qa_z.cli import main
from qa_z.diffing.models import ChangedFile, ChangeSet
from qa_z.runners.models import CheckSpec
from qa_z.runners.selection import build_fast_selection


def python_checks() -> list[CheckSpec]:
    return [
        CheckSpec(id="py_lint", command=["ruff", "check", "."], kind="lint"),
        CheckSpec(
            id="py_format",
            command=["ruff", "format", "--check", "."],
            kind="format",
        ),
        CheckSpec(id="py_type", command=["mypy", "src", "tests"], kind="typecheck"),
        CheckSpec(id="py_test", command=["pytest", "-q"], kind="test"),
    ]


def typescript_checks() -> list[CheckSpec]:
    return [
        CheckSpec(id="ts_lint", command=["eslint", "."], kind="lint"),
        CheckSpec(id="ts_type", command=["tsc", "--noEmit"], kind="typecheck"),
        CheckSpec(id="ts_test", command=["vitest", "run"], kind="test"),
    ]


def changed(
    path: str,
    *,
    status: str = "modified",
    language: str = "python",
    kind: str = "source",
) -> ChangedFile:
    return ChangedFile(
        path=path,
        old_path=path if status != "added" else None,
        status=status,  # type: ignore[arg-type]
        additions=1,
        deletions=1,
        language=language,  # type: ignore[arg-type]
        kind=kind,  # type: ignore[arg-type]
    )


def test_typescript_source_change_targets_lint_and_mapped_tests(tmp_path) -> None:
    test_path = tmp_path / "tests" / "foo" / "bar.test.ts"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("import { test } from 'vitest';\n", encoding="utf-8")

    plans, selection = build_fast_selection(
        check_specs=typescript_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed(
                    "src/foo/bar.ts",
                    language="typescript",
                    kind="source",
                )
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    by_id = {plan.id: plan for plan in plans}
    assert by_id["ts_lint"].execution_mode == "targeted"
    assert by_id["ts_lint"].resolved_command == ["eslint", "src/foo/bar.ts"]
    assert by_id["ts_type"].execution_mode == "full"
    assert by_id["ts_type"].resolved_command == ["tsc", "--noEmit"]
    assert by_id["ts_test"].execution_mode == "targeted"
    assert by_id["ts_test"].resolved_command == [
        "vitest",
        "run",
        "tests/foo/bar.test.ts",
    ]
    assert selection.targeted_checks == ["ts_lint", "ts_test"]
    assert selection.full_checks == ["ts_type"]


def test_typescript_test_only_change_selects_test_file_directly(tmp_path) -> None:
    plans, _selection = build_fast_selection(
        check_specs=typescript_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed(
                    "src/foo/bar.spec.ts",
                    language="typescript",
                    kind="test",
                )
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    by_id = {plan.id: plan for plan in plans}
    assert by_id["ts_lint"].execution_mode == "targeted"
    assert by_id["ts_test"].execution_mode == "targeted"
    assert by_id["ts_test"].resolved_command == [
        "vitest",
        "run",
        "src/foo/bar.spec.ts",
    ]


def test_typescript_source_without_candidate_tests_falls_back_to_full_tests(
    tmp_path,
) -> None:
    plans, _selection = build_fast_selection(
        check_specs=typescript_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed(
                    "src/foo/missing.ts",
                    language="typescript",
                    kind="source",
                )
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    ts_test = {plan.id: plan for plan in plans}["ts_test"]
    assert ts_test.execution_mode == "full"
    assert ts_test.resolved_command == ["vitest", "run"]
    assert (
        ts_test.selection_reason == "no candidate tests resolved; falling back to full"
    )


def test_typescript_config_change_forces_all_typescript_checks_full(tmp_path) -> None:
    plans, selection = build_fast_selection(
        check_specs=typescript_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed(
                    "tsconfig.json",
                    language="json",
                    kind="config",
                )
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=["tsconfig.json"],
    )

    assert all(plan.execution_mode == "full" for plan in plans)
    assert selection.full_checks == ["ts_lint", "ts_type", "ts_test"]
    assert "high-risk path changed: tsconfig.json" in selection.high_risk_reasons
    assert "config files changed" in selection.high_risk_reasons


def test_mixed_python_and_typescript_changes_keep_language_check_plans(
    tmp_path,
) -> None:
    (tmp_path / "tests" / "test_cli.py").parent.mkdir(parents=True)
    (tmp_path / "tests" / "test_cli.py").write_text(
        "def test_cli():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "ui" / "button.test.ts").parent.mkdir(parents=True)
    (tmp_path / "tests" / "ui" / "button.test.ts").write_text(
        "import { test } from 'vitest';\n", encoding="utf-8"
    )

    plans, selection = build_fast_selection(
        check_specs=[*python_checks(), *typescript_checks()],
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed("src/qa_z/cli.py"),
                changed(
                    "src/ui/button.ts",
                    language="typescript",
                    kind="source",
                ),
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    by_id = {plan.id: plan for plan in plans}
    assert by_id["py_lint"].resolved_command == ["ruff", "check", "src/qa_z/cli.py"]
    assert by_id["py_test"].resolved_command == ["pytest", "-q", "tests/test_cli.py"]
    assert by_id["ts_lint"].resolved_command == ["eslint", "src/ui/button.ts"]
    assert by_id["ts_test"].resolved_command == [
        "vitest",
        "run",
        "tests/ui/button.test.ts",
    ]
    assert selection.targeted_checks == [
        "py_lint",
        "py_format",
        "py_test",
        "ts_lint",
        "ts_test",
    ]
    assert selection.full_checks == ["py_type", "ts_type"]


def test_typescript_only_change_skips_python_builtin_checks(tmp_path) -> None:
    (tmp_path / "tests" / "ui" / "button.test.ts").parent.mkdir(parents=True)
    (tmp_path / "tests" / "ui" / "button.test.ts").write_text(
        "import { test } from 'vitest';\n", encoding="utf-8"
    )

    plans, selection = build_fast_selection(
        check_specs=[*python_checks(), *typescript_checks()],
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed(
                    "src/ui/button.ts",
                    language="typescript",
                    kind="source",
                )
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    by_id = {plan.id: plan for plan in plans}
    assert by_id["py_lint"].execution_mode == "skipped"
    assert by_id["py_format"].execution_mode == "skipped"
    assert by_id["py_type"].execution_mode == "skipped"
    assert by_id["py_test"].execution_mode == "skipped"
    assert by_id["ts_lint"].execution_mode == "targeted"
    assert by_id["ts_type"].execution_mode == "full"
    assert by_id["ts_test"].execution_mode == "targeted"
    assert selection.skipped_checks == ["py_lint", "py_format", "py_type", "py_test"]


def test_python_only_change_skips_typescript_builtin_checks(tmp_path) -> None:
    (tmp_path / "tests" / "test_cli.py").parent.mkdir(parents=True)
    (tmp_path / "tests" / "test_cli.py").write_text(
        "def test_cli():\n    assert True\n", encoding="utf-8"
    )

    plans, selection = build_fast_selection(
        check_specs=[*python_checks(), *typescript_checks()],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/qa_z/cli.py")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    by_id = {plan.id: plan for plan in plans}
    assert by_id["py_lint"].execution_mode == "targeted"
    assert by_id["py_format"].execution_mode == "targeted"
    assert by_id["py_type"].execution_mode == "full"
    assert by_id["py_test"].execution_mode == "targeted"
    assert by_id["ts_lint"].execution_mode == "skipped"
    assert by_id["ts_type"].execution_mode == "skipped"
    assert by_id["ts_test"].execution_mode == "skipped"
    assert selection.skipped_checks == ["ts_lint", "ts_type", "ts_test"]


def test_docs_only_changes_skip_python_checks(tmp_path) -> None:
    plans, selection = build_fast_selection(
        check_specs=python_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed("docs/readme.md", language="markdown", kind="docs"),
                changed("README.md", language="markdown", kind="docs"),
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    assert {plan.id: plan.execution_mode for plan in plans} == {
        "py_lint": "skipped",
        "py_format": "skipped",
        "py_type": "skipped",
        "py_test": "skipped",
    }
    assert selection.mode == "smart"
    assert selection.input_source == "cli_diff"
    assert selection.skipped_checks == ["py_lint", "py_format", "py_type", "py_test"]
    assert all(plan.selection_reason == "docs-only change" for plan in plans)


def test_python_source_change_targets_lint_format_and_mapped_tests(tmp_path) -> None:
    test_path = tmp_path / "tests" / "test_cli.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_cli():\n    assert True\n", encoding="utf-8")

    plans, selection = build_fast_selection(
        check_specs=python_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/qa_z/cli.py")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    by_id = {plan.id: plan for plan in plans}
    assert by_id["py_lint"].execution_mode == "targeted"
    assert by_id["py_lint"].resolved_command == ["ruff", "check", "src/qa_z/cli.py"]
    assert by_id["py_format"].execution_mode == "targeted"
    assert by_id["py_type"].execution_mode == "full"
    assert by_id["py_test"].execution_mode == "targeted"
    assert by_id["py_test"].resolved_command == ["pytest", "-q", "tests/test_cli.py"]
    assert selection.targeted_checks == ["py_lint", "py_format", "py_test"]
    assert selection.full_checks == ["py_type"]


def test_python_source_without_candidate_tests_falls_back_to_full_tests(
    tmp_path,
) -> None:
    plans, _selection = build_fast_selection(
        check_specs=python_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/qa_z/runners/fast.py")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    py_test = {plan.id: plan for plan in plans}["py_test"]
    assert py_test.execution_mode == "full"
    assert py_test.resolved_command == ["pytest", "-q"]
    assert (
        py_test.selection_reason == "no candidate tests resolved; falling back to full"
    )


def test_deleted_renamed_config_and_too_many_files_force_full(tmp_path) -> None:
    change_set = ChangeSet(
        source="cli_diff",
        files=[
            changed("src/qa_z/old.py", status="deleted"),
            changed("src/qa_z/new_name.py", status="renamed"),
            changed("qa-z.yaml", language="yaml", kind="config"),
            changed("src/qa_z/extra.py"),
        ],
    )

    plans, selection = build_fast_selection(
        check_specs=python_checks(),
        change_set=change_set,
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=3,
        high_risk_paths=["qa-z.yaml"],
    )

    assert all(plan.execution_mode == "full" for plan in plans)
    assert selection.full_checks == ["py_lint", "py_format", "py_type", "py_test"]
    assert "deleted files changed" in selection.high_risk_reasons
    assert "renamed files changed" in selection.high_risk_reasons
    assert "high-risk path changed: qa-z.yaml" in selection.high_risk_reasons
    assert "changed file count 4 exceeds threshold 3" in selection.high_risk_reasons


def test_deleted_docs_file_still_forces_full(tmp_path) -> None:
    plans, selection = build_fast_selection(
        check_specs=python_checks(),
        change_set=ChangeSet(
            source="cli_diff",
            files=[
                changed(
                    "docs/removed.md",
                    status="deleted",
                    language="markdown",
                    kind="docs",
                )
            ],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    assert all(plan.execution_mode == "full" for plan in plans)
    assert selection.full_checks == ["py_lint", "py_format", "py_type", "py_test"]
    assert selection.high_risk_reasons == ["deleted files changed"]


def test_custom_check_falls_back_to_full_for_non_docs_change(tmp_path) -> None:
    plans, selection = build_fast_selection(
        check_specs=[
            *python_checks(),
            CheckSpec(id="custom_gate", command=["custom-gate"], kind="custom"),
        ],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/qa_z/cli.py")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    custom = {plan.id: plan for plan in plans}["custom_gate"]
    assert custom.execution_mode == "full"
    assert (
        custom.selection_reason
        == "custom check has no targeted selector; falling back to full"
    )
    assert "custom_gate" in selection.full_checks


def test_fast_smart_with_docs_diff_persists_v2_selection_and_skipped_checks(
    tmp_path, capsys
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(
            {
                "project": {"name": "qa-z", "languages": ["python"]},
                "contracts": {"output_dir": "qa/contracts"},
                "fast": {
                    "output_dir": ".qa-z/runs",
                    "checks": [
                        {
                            "id": "py_lint",
                            "enabled": True,
                            "run": ["ruff", "check", "."],
                            "kind": "lint",
                        }
                    ],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    contract_dir = tmp_path / "qa" / "contracts"
    contract_dir.mkdir(parents=True)
    (contract_dir / "docs.md").write_text("# QA Contract: Docs\n", encoding="utf-8")
    diff_path = tmp_path / "docs.diff"
    diff_path.write_text(
        dedent(
            """\
            diff --git a/docs/readme.md b/docs/readme.md
            index 1111111..2222222 100644
            --- a/docs/readme.md
            +++ b/docs/readme.md
            @@ -1 +1,2 @@
             old
            +new
            """
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--selection",
            "smart",
            "--diff",
            str(diff_path),
            "--output-dir",
            str(tmp_path / "runs"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["schema_version"] == 2
    assert output["selection"]["mode"] == "smart"
    assert output["selection"]["skipped_checks"] == ["py_lint"]
    assert output["checks"][0]["status"] == "skipped"
    assert output["checks"][0]["execution_mode"] == "skipped"
    assert output["checks"][0]["selection_reason"] == "docs-only change"


def test_fast_uses_configured_smart_selection_default(tmp_path, capsys) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(
            {
                "project": {"name": "qa-z", "languages": ["python"]},
                "contracts": {"output_dir": "qa/contracts"},
                "fast": {
                    "output_dir": ".qa-z/runs",
                    "selection": {"default_mode": "smart"},
                    "checks": [
                        {
                            "id": "py_lint",
                            "enabled": True,
                            "run": ["ruff", "check", "."],
                            "kind": "lint",
                        }
                    ],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    contract_dir = tmp_path / "qa" / "contracts"
    contract_dir.mkdir(parents=True)
    (contract_dir / "docs.md").write_text("# QA Contract: Docs\n", encoding="utf-8")
    diff_path = tmp_path / "docs.diff"
    diff_path.write_text(
        dedent(
            """\
            diff --git a/docs/readme.md b/docs/readme.md
            index 1111111..2222222 100644
            --- a/docs/readme.md
            +++ b/docs/readme.md
            @@ -1 +1,2 @@
             old
            +new
            """
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "fast",
            "--path",
            str(tmp_path),
            "--diff",
            str(diff_path),
            "--output-dir",
            str(tmp_path / "runs"),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["selection"]["mode"] == "smart"
    assert output["selection"]["skipped_checks"] == ["py_lint"]


def test_python_test_smart_selection_preserves_configured_pytest_command(
    tmp_path,
) -> None:
    test_path = tmp_path / "tests" / "test_app.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_app():\n    assert True\n", encoding="utf-8")

    plans, _selection = build_fast_selection(
        check_specs=[
            CheckSpec(
                id="py_test",
                command=["python", "-m", "pytest", "-q"],
                kind="test",
            )
        ],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/app.py")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    assert plans[0].resolved_command == [
        "python",
        "-m",
        "pytest",
        "-q",
        "tests/test_app.py",
    ]


def test_python_lint_smart_selection_replaces_configured_root_with_targets(
    tmp_path,
) -> None:
    plans, _selection = build_fast_selection(
        check_specs=[
            CheckSpec(
                id="py_lint",
                command=["uv", "run", "ruff", "check", "."],
                kind="lint",
            )
        ],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/app.py")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    assert plans[0].resolved_command == [
        "uv",
        "run",
        "ruff",
        "check",
        "src/app.py",
    ]


def test_typescript_lint_preserves_pnpm_eslint_command(tmp_path) -> None:
    plans, _selection = build_fast_selection(
        check_specs=[
            CheckSpec(
                id="ts_lint",
                command=["pnpm", "exec", "eslint", "."],
                kind="lint",
            )
        ],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/ui/button.ts", language="typescript", kind="source")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    assert plans[0].resolved_command == [
        "pnpm",
        "exec",
        "eslint",
        "src/ui/button.ts",
    ]


def test_typescript_test_preserves_configured_vitest_command(tmp_path) -> None:
    test_path = tmp_path / "tests" / "ui" / "button.test.ts"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("import { test } from 'vitest';\n", encoding="utf-8")

    plans, _selection = build_fast_selection(
        check_specs=[
            CheckSpec(
                id="ts_test",
                command=["pnpm", "vitest", "run"],
                kind="test",
            )
        ],
        change_set=ChangeSet(
            source="cli_diff",
            files=[changed("src/ui/button.ts", language="typescript", kind="source")],
        ),
        repo_root=tmp_path,
        selection_mode="smart",
        full_run_threshold=40,
        high_risk_paths=[],
    )

    assert plans[0].resolved_command == [
        "pnpm",
        "vitest",
        "run",
        "tests/ui/button.test.ts",
    ]
