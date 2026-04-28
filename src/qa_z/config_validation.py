"""Config validation for qa-z doctor."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

IssueLevel = Literal["error", "warning"]

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
            if not isinstance(checks.get(mode), list):
                errors.append(
                    issue(
                        "invalid_checks_type",
                        f"checks.{mode}",
                        f"checks.{mode} must be a list when present.",
                    )
                )


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
    if not isinstance(value, list):
        errors.append(issue("invalid_checks_type", path, f"{path} must be a list."))
        return
    for index, item in enumerate(value):
        validate_check_item(item, f"{path}[{index}]", errors)


def validate_check_item(
    item: Any,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate one check item."""
    if isinstance(item, str):
        return
    if not isinstance(item, dict):
        errors.append(
            issue("invalid_check_item", path, f"{path} must be a string or mapping.")
        )
        return
    check_id = item.get("id")
    if not isinstance(check_id, str) or not check_id.strip():
        errors.append(
            issue(
                "missing_check_id", f"{path}.id", "Check item requires a non-empty id."
            )
        )
    run = item.get("run")
    if run is not None and (
        not isinstance(run, list) or not all(isinstance(part, str) for part in run)
    ):
        errors.append(
            issue(
                "invalid_check_run",
                f"{path}.run",
                "Check run must be a list of strings.",
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
