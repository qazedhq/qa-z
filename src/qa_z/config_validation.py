"""Config validation for qa-z doctor."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from qa_z.runners.checks import default_spec_for_name as default_fast_spec_for_name
from qa_z.runners.semgrep import default_semgrep_spec_for_name

IssueLevel = Literal["error", "warning"]

CHECK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

KNOWN_TOP_LEVEL_KEYS = {
    "project",
    "contracts",
    "fast",
    "deep",
    "checks",
    "gates",
    "reporters",
    "adapters",
}


def validate_config(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Validate a loaded QA-Z config and return a JSON-safe report."""
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    suggestions: list[str] = []

    validate_top_level_keys(config, warnings)
    validate_checks_shape(config, errors, warnings)
    validate_adapters(root, config, warnings, suggestions)

    status = "passed"
    if errors:
        status = "failed"
    elif warnings:
        status = "warning"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "suggestions": unique_strings(suggestions),
    }


def validate_top_level_keys(
    config: dict[str, Any],
    warnings: list[dict[str, str]],
) -> None:
    """Warn about top-level keys that doctor does not understand."""
    for key in sorted(config):
        if key not in KNOWN_TOP_LEVEL_KEYS:
            warnings.append(
                issue(
                    "unknown_top_level_key",
                    key,
                    f"Unknown top-level config key: {key}",
                )
            )


def validate_checks_shape(
    config: dict[str, Any],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate fast/deep check lists and legacy paths."""
    validate_check_list(config, "fast", "checks", errors)
    validate_check_list(config, "deep", "checks", errors)

    checks = config.get("checks")
    if not isinstance(checks, dict):
        return
    for mode in ("fast", "deep"):
        if mode in checks:
            warnings.append(
                issue(
                    f"legacy_checks_{mode}",
                    f"checks.{mode}",
                    f"Use {mode}.checks instead of legacy checks.{mode}.",
                )
            )
            if modern_check_list_exists(config, mode):
                continue
            if not isinstance(checks.get(mode), list):
                errors.append(
                    issue(
                        "invalid_checks_type",
                        f"checks.{mode}",
                        f"checks.{mode} must be a list when present.",
                    )
                )
            else:
                validate_check_items(checks.get(mode), mode, f"checks.{mode}", errors)


def modern_check_list_exists(config: dict[str, Any], section_name: str) -> bool:
    """Return whether a modern section shadows its legacy check list."""
    section = config.get(section_name)
    return isinstance(section, dict) and "checks" in section


def validate_check_list(
    config: dict[str, Any],
    section_name: str,
    key: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate one configured check list."""
    section = config.get(section_name)
    if not isinstance(section, dict) or key not in section:
        return
    value = section.get(key)
    path = f"{section_name}.{key}"
    validate_check_items(value, section_name, path, errors)


def validate_check_items(
    value: Any,
    section_name: str,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate one configured check item list."""
    if not isinstance(value, list):
        errors.append(issue("invalid_checks_type", path, f"{path} must be a list."))
        return
    seen_ids: set[str] = set()
    for index, item in enumerate(value):
        check_id = validate_check_item(item, section_name, f"{path}[{index}]", errors)
        if check_id is None:
            continue
        if check_id in seen_ids:
            errors.append(
                issue(
                    "duplicate_check_id",
                    f"{path}[{index}].id",
                    f"Duplicate check id in {path}: {check_id}",
                )
            )
        else:
            seen_ids.add(check_id)


def validate_check_item(
    item: Any,
    section_name: str,
    path: str,
    errors: list[dict[str, str]],
) -> str | None:
    """Validate one check item."""
    if isinstance(item, str):
        check_id = item.strip()
        if not check_id:
            errors.append(issue("missing_check_id", path, "Check id cannot be empty."))
            return None
        if not is_safe_check_id(check_id):
            errors.append(
                issue(
                    "invalid_check_id",
                    path,
                    "Check id must use letters, numbers, dots, underscores, or hyphens.",
                )
            )
            return None
        default = default_spec_for_section(section_name, check_id)
        if default is None:
            errors.append(
                issue(
                    "unknown_check_id",
                    path,
                    f"Unknown built-in check id or alias: {check_id}",
                )
            )
            return None
        return default.id
    if not isinstance(item, dict):
        errors.append(
            issue("invalid_check_item", path, f"{path} must be a string or mapping.")
        )
        return None
    raw_check_id = item.get("id")
    if not isinstance(raw_check_id, str) or not raw_check_id.strip():
        errors.append(
            issue(
                "missing_check_id", f"{path}.id", "Check item requires a non-empty id."
            )
        )
        return None
    check_id = raw_check_id.strip()
    if not is_safe_check_id(check_id):
        errors.append(
            issue(
                "invalid_check_id",
                f"{path}.id",
                "Check id must use letters, numbers, dots, underscores, or hyphens.",
            )
        )
        return None
    run = item.get("run")
    enabled = item.get("enabled", True)
    disabled = enabled is False
    default = default_spec_for_section(section_name, check_id)
    if run is None and default is None and not disabled:
        errors.append(
            issue(
                "missing_check_run",
                f"{path}.run",
                "Custom checks require a run command.",
            )
        )
    elif run is not None and not is_valid_run_command(run):
        errors.append(
            issue(
                "invalid_check_run",
                f"{path}.run",
                "Check run must be a non-empty list of strings with a non-empty executable.",
            )
        )
    if (
        "timeout_seconds" in item
        and coerce_positive_int(item.get("timeout_seconds")) is None
    ):
        errors.append(
            issue(
                "invalid_timeout",
                f"{path}.timeout_seconds",
                "timeout_seconds must be a positive integer.",
            )
        )
    return default.id if default is not None else check_id


def default_spec_for_section(section_name: str, check_id: str) -> Any:
    """Return the built-in check spec for a fast or deep section."""
    if section_name == "fast":
        return default_fast_spec_for_name(check_id)
    if section_name == "deep":
        return default_semgrep_spec_for_name(check_id)
    return None


def is_safe_check_id(check_id: str) -> bool:
    """Return whether a check id is safe for per-check artifact filenames."""
    return bool(CHECK_ID_RE.fullmatch(check_id))


def is_valid_run_command(run: Any) -> bool:
    """Return whether a configured command can be passed to subprocess safely."""
    return (
        isinstance(run, list)
        and bool(run)
        and all(isinstance(part, str) for part in run)
        and bool(run[0].strip())
    )


def validate_adapters(
    root: Path,
    config: dict[str, Any],
    warnings: list[dict[str, str]],
    suggestions: list[str],
) -> None:
    """Validate adapter instruction file references."""
    adapters = config.get("adapters")
    if not isinstance(adapters, dict):
        return
    for name, adapter in sorted(adapters.items()):
        if not isinstance(adapter, dict) or adapter.get("enabled") is False:
            continue
        instructions_file = adapter.get("instructions_file")
        if not isinstance(instructions_file, str) or not instructions_file.strip():
            continue
        target = Path(instructions_file).expanduser()
        if not target.is_absolute():
            target = root / target
        if target.exists():
            continue
        warnings.append(
            issue(
                "missing_instruction_file",
                f"adapters.{name}.instructions_file",
                f"Instruction file does not exist: {instructions_file}",
            )
        )
        suggestions.append("qa-z init --with-agent-templates")


def issue(code: str, path: str, message: str) -> dict[str, str]:
    """Return a normalized validation issue."""
    return {"code": code, "path": path, "message": message}


def coerce_positive_int(value: Any) -> int | None:
    """Return a positive integer when possible."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def unique_strings(values: list[str]) -> list[str]:
    """Return unique strings in first-seen order."""
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique
