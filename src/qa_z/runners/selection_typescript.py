"""TypeScript smart-selection planning."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from qa_z.diffing.models import ChangedFile, ChangeSet
from qa_z.runners.models import CheckPlan, CheckSpec
from qa_z.runners.selection_common import (
    command_with_targets,
    full_check_plan,
    skipped_check_plan,
    targeted_check_plan,
    unique_preserve_order,
)

TYPESCRIPT_BUILTIN_IDS = {"ts_lint", "ts_type", "ts_test"}
TYPESCRIPT_TEST_SUFFIXES = (".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx")


def build_typescript_check_plan(
    spec: CheckSpec,
    change_set: ChangeSet,
    repo_root: Path,
    high_risk_reasons: list[str],
) -> CheckPlan:
    """Build a smart selection plan for one built-in TypeScript check."""
    typescript_changed = [
        changed
        for changed in change_set.files
        if changed.language == "typescript" and changed.kind in {"source", "test"}
    ]
    changed_tests = [
        changed for changed in typescript_changed if changed.kind == "test"
    ]
    changed_sources = [
        changed for changed in typescript_changed if changed.kind == "source"
    ]

    if not typescript_changed:
        return skipped_check_plan(spec, "no typescript source/test changes")

    if spec.id == "ts_lint":
        targets = [changed.path for changed in typescript_changed]
        if targets:
            return targeted_check_plan(
                spec,
                command_with_targets(spec, targets, replace_roots={"."}),
                targets,
                "typescript source/test files changed",
                high_risk_reasons,
            )
    if spec.id == "ts_type":
        if typescript_changed:
            return full_check_plan(
                spec,
                "type checking remains full for typescript changes",
                high_risk_reasons,
            )
    if spec.id == "ts_test":
        if changed_tests:
            targets = [changed.path for changed in changed_tests]
            return targeted_check_plan(
                spec,
                command_with_targets(spec, targets),
                targets,
                "changed test files selected directly",
                high_risk_reasons,
            )
        if changed_sources:
            targets, reason = resolve_typescript_test_targets(
                changed_sources, repo_root
            )
            if targets:
                return targeted_check_plan(
                    spec,
                    command_with_targets(spec, targets),
                    targets,
                    reason or "mapped changed source files to candidate tests",
                    high_risk_reasons,
                )
            return full_check_plan(
                spec,
                "no candidate tests resolved; falling back to full",
                high_risk_reasons,
            )

    return full_check_plan(
        spec,
        "custom check has no targeted selector; falling back to full",
        high_risk_reasons,
    )


def resolve_typescript_test_targets(
    changed_files: list[ChangedFile],
    repo_root: Path,
) -> tuple[list[str], str | None]:
    """Map changed TypeScript source files to candidate Vitest files."""
    candidates: list[str] = []
    for changed in changed_files:
        for candidate in candidate_test_paths(changed.path):
            if (repo_root / candidate).is_file() and candidate not in candidates:
                candidates.append(candidate)
    if not candidates:
        return [], None
    return candidates, "mapped changed source files to candidate tests"


def candidate_test_paths(path: str) -> list[str]:
    """Return likely Vitest files for a TypeScript source path."""
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.name.endswith(TYPESCRIPT_TEST_SUFFIXES):
        return [normalized]

    module_parts = list(pure.with_suffix("").parts)
    if module_parts and module_parts[0] in {"src", "app", "lib"}:
        module_parts = module_parts[1:]
    module_dir = PurePosixPath(*module_parts[:-1]) if len(module_parts) > 1 else None
    stem = pure.stem
    same_dir = pure.parent

    test_names = [
        f"{stem}.test.ts",
        f"{stem}.spec.ts",
        f"{stem}.test.tsx",
        f"{stem}.spec.tsx",
    ]
    candidates: list[str] = []
    for test_name in test_names:
        if module_dir is not None:
            candidates.append(f"tests/{module_dir}/{test_name}")
        else:
            candidates.append(f"tests/{test_name}")
    for test_name in test_names:
        candidates.append(f"{same_dir}/{test_name}")
    for test_name in test_names:
        if module_dir is not None:
            candidates.append(f"__tests__/{module_dir}/{test_name}")
        else:
            candidates.append(f"__tests__/{test_name}")
    return unique_preserve_order(candidates)
