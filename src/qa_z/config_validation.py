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
MAPPING_SECTIONS = tuple(sorted(KNOWN_TOP_LEVEL_KEYS))
VALID_SELECTION_MODES = {"full", "smart"}
VALID_NO_TESTS_POLICIES = {"warn", "fail"}
KNOWN_SEMGREP_POLICY_KEYS = {
    "config",
    "fail_on_severity",
    "ignore_rules",
    "exclude_paths",
}
VALID_SEMGREP_SEVERITIES = {"ERROR", "WARNING", "WARN", "INFO"}


def validate_config(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Validate a loaded QA-Z config and return a JSON-safe report."""
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    suggestions: list[str] = []

    validate_top_level_keys(config, warnings)
    validate_section_shapes(config, errors)
    validate_project_section(config, errors)
    validate_contracts_section(config, errors)
    validate_runner_options(config, errors)
    validate_checks_shape(config, errors, warnings)
    validate_adapters(root, config, errors, warnings, suggestions)

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


def validate_section_shapes(
    config: dict[str, Any], errors: list[dict[str, str]]
) -> None:
    """Validate known top-level sections before reading nested options."""
    for section_name in MAPPING_SECTIONS:
        validate_mapping_section(config, section_name, errors)


def validate_project_section(
    config: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """Validate optional project metadata used in reports and examples."""
    project = config.get("project")
    if not isinstance(project, dict):
        return
    if "name" in project and not is_non_empty_string(project.get("name")):
        errors.append(
            issue(
                "invalid_project_name",
                "project.name",
                "project.name must be a non-empty string when present.",
            )
        )
    validate_string_list_option(config, ("project", "languages"), errors)
    validate_string_list_option(config, ("project", "roots"), errors)
    validate_string_list_option(config, ("project", "critical_paths"), errors)


def validate_contracts_section(
    config: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """Validate contract output settings consumed by artifact path helpers."""
    contracts = config.get("contracts")
    if not isinstance(contracts, dict):
        return
    if "output_dir" in contracts and not is_non_empty_string(
        contracts.get("output_dir")
    ):
        errors.append(
            issue(
                "invalid_contracts_output_dir",
                "contracts.output_dir",
                "contracts.output_dir must be a non-empty string when present.",
            )
        )
    validate_string_list_option(config, ("contracts", "sources"), errors)
    validate_string_list_option(config, ("contracts", "required_sections"), errors)


def validate_checks_shape(
    config: dict[str, Any],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate fast/deep check lists and legacy paths."""
    validate_check_list(config, "fast", "checks", errors, warnings)
    validate_check_list(config, "deep", "checks", errors, warnings)

    checks = config.get("checks")
    if not isinstance(checks, dict):
        return
    validate_legacy_checks_selection(checks, warnings)
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
                validate_check_items(
                    checks.get(mode),
                    mode,
                    f"checks.{mode}",
                    errors,
                    warnings,
                )


def validate_legacy_checks_selection(
    checks: dict[str, Any],
    warnings: list[dict[str, str]],
) -> None:
    """Warn when legacy selection metadata is present but ignored."""
    selection = checks.get("selection")
    if not isinstance(selection, dict) or "mode" not in selection:
        return
    warnings.append(
        issue(
            "legacy_checks_selection_mode",
            "checks.selection.mode",
            (
                "checks.selection.mode is ignored; use "
                "fast.selection.default_mode or deep.selection.default_mode."
            ),
        )
    )


def validate_runner_options(
    config: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """Validate scalar options consumed by fast/deep runners."""
    validate_string_option(config, ("fast", "default_contract"), errors)
    validate_string_option(config, ("fast", "output_dir"), errors)
    validate_mapping_option(config, ("fast", "selection"), errors)
    validate_mapping_option(config, ("deep", "selection"), errors)
    validate_mapping_option(config, ("checks", "selection"), errors)
    validate_selection_mode(config, "fast", errors)
    validate_selection_mode(config, "deep", errors)
    validate_non_negative_int_option(
        config, ("fast", "selection", "full_run_threshold"), errors
    )
    validate_non_negative_int_option(
        config, ("deep", "selection", "full_run_threshold"), errors
    )
    validate_non_negative_int_option(
        config, ("checks", "selection", "max_changed_files"), errors
    )
    validate_string_list_option(
        config, ("fast", "selection", "high_risk_paths"), errors
    )
    validate_string_list_option(
        config, ("deep", "selection", "high_risk_paths"), errors
    )
    validate_string_list_option(config, ("deep", "selection", "exclude_paths"), errors)
    validate_string_list_option(config, ("gates", "escalate_on"), errors)
    validate_string_list_option(config, ("gates", "block_on"), errors)
    validate_boolean_option(config, "fast", "strict_no_tests", errors)
    validate_boolean_option(config, "fast", "fail_on_missing_tool", errors)
    validate_boolean_option(config, "deep", "fail_on_missing_tool", errors)
    validate_boolean_option(config, "gates", "require_human_review", errors)
    validate_boolean_option(config, "reporters", "markdown", errors)
    validate_boolean_option(config, "reporters", "json", errors)
    validate_boolean_option(config, "reporters", "sarif", errors)
    validate_boolean_option(config, "reporters", "github_annotations", errors)
    validate_boolean_option(config, "reporters", "repair_packet", errors)


def validate_mapping_section(
    config: dict[str, Any],
    section_name: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate that a configured section is a mapping."""
    if section_name not in config or isinstance(config.get(section_name), dict):
        return
    errors.append(
        issue(
            f"invalid_{section_name}_type",
            section_name,
            f"{section_name} must be a mapping when present.",
        )
    )


def validate_mapping_option(
    config: dict[str, Any],
    path: tuple[str, ...],
    errors: list[dict[str, str]],
) -> None:
    """Validate that a nested option is a mapping when present."""
    present, value = get_nested_value(config, path)
    if not present or isinstance(value, dict):
        return
    path_text = ".".join(path)
    errors.append(
        issue(
            f"invalid_{'_'.join(path)}",
            path_text,
            f"{path_text} must be a mapping when present.",
        )
    )


def validate_boolean_option(
    config: dict[str, Any],
    section_name: str,
    option_name: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate a boolean option when it is present."""
    section = config.get(section_name)
    if not isinstance(section, dict) or option_name not in section:
        return
    if isinstance(section.get(option_name), bool):
        return
    path = f"{section_name}.{option_name}"
    errors.append(
        issue(
            f"invalid_{section_name}_{option_name}",
            path,
            f"{path} must be a boolean when present.",
        )
    )


def validate_string_option(
    config: dict[str, Any],
    path: tuple[str, ...],
    errors: list[dict[str, str]],
) -> None:
    """Validate a non-empty string option when it is present."""
    present, value = get_nested_value(config, path)
    if not present or is_non_empty_string(value):
        return
    path_text = ".".join(path)
    errors.append(
        issue(
            f"invalid_{'_'.join(path)}",
            path_text,
            f"{path_text} must be a non-empty string when present.",
        )
    )


def validate_string_list_option(
    config: dict[str, Any],
    path: tuple[str, ...],
    errors: list[dict[str, str]],
) -> None:
    """Validate a list of non-empty strings when it is present."""
    present, value = get_nested_value(config, path)
    if not present:
        return
    if isinstance(value, list) and all(is_non_empty_string(item) for item in value):
        return
    path_text = ".".join(path)
    errors.append(
        issue(
            f"invalid_{'_'.join(path)}",
            path_text,
            f"{path_text} must be a list of non-empty strings when present.",
        )
    )


def validate_non_negative_int_option(
    config: dict[str, Any],
    path: tuple[str, ...],
    errors: list[dict[str, str]],
) -> None:
    """Validate a non-negative integer option when it is present."""
    present, value = get_nested_value(config, path)
    if not present or coerce_non_negative_int(value) is not None:
        return
    path_text = ".".join(path)
    errors.append(
        issue(
            f"invalid_{'_'.join(path)}",
            path_text,
            f"{path_text} must be a non-negative integer when present.",
        )
    )


def validate_selection_mode(
    config: dict[str, Any],
    section_name: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate smart/full selection mode defaults before runners fall back."""
    path = (section_name, "selection", "default_mode")
    present, value = get_nested_value(config, path)
    if not present or (isinstance(value, str) and value in VALID_SELECTION_MODES):
        return
    path_text = ".".join(path)
    errors.append(
        issue(
            f"invalid_{'_'.join(path)}",
            path_text,
            f"{path_text} must be one of: full, smart.",
        )
    )


def get_nested_value(config: dict[str, Any], path: tuple[str, ...]) -> tuple[bool, Any]:
    """Return whether a nested value exists and the value when parents are mappings."""
    current: Any = config
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def modern_check_list_exists(config: dict[str, Any], section_name: str) -> bool:
    """Return whether a modern section shadows its legacy check list."""
    section = config.get(section_name)
    return isinstance(section, dict) and "checks" in section


def validate_check_list(
    config: dict[str, Any],
    section_name: str,
    key: str,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate one configured check list."""
    section = config.get(section_name)
    if not isinstance(section, dict) or key not in section:
        return
    value = section.get(key)
    path = f"{section_name}.{key}"
    validate_check_items(value, section_name, path, errors, warnings)


def validate_check_items(
    value: Any,
    section_name: str,
    path: str,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate one configured check item list."""
    if not isinstance(value, list):
        errors.append(issue("invalid_checks_type", path, f"{path} must be a list."))
        return
    seen_ids: set[str] = set()
    for index, item in enumerate(value):
        check_id = validate_check_item(
            item,
            section_name,
            f"{path}[{index}]",
            errors,
            warnings,
        )
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
    warnings: list[dict[str, str]],
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
    default = default_spec_for_section(section_name, check_id)
    run = item.get("run")
    enabled = item.get("enabled", True)
    if "enabled" in item and not isinstance(enabled, bool):
        errors.append(
            issue(
                "invalid_check_enabled",
                f"{path}.enabled",
                "enabled must be a boolean when present.",
            )
        )
    if "no_tests" in item and not is_valid_no_tests_policy(item.get("no_tests")):
        errors.append(
            issue(
                "invalid_check_no_tests",
                f"{path}.no_tests",
                "no_tests must be either 'warn' or 'fail' when present.",
            )
        )
    if "kind" in item and not is_non_empty_string(item.get("kind")):
        errors.append(
            issue(
                "invalid_check_kind",
                f"{path}.kind",
                "kind must be a non-empty string when present.",
            )
        )
    validate_semgrep_policy(
        item,
        section_name=section_name,
        check_id=check_id,
        default_id=default.id if default is not None else None,
        path=path,
        errors=errors,
        warnings=warnings,
    )
    disabled = enabled is False
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


def validate_semgrep_policy(
    item: dict[str, Any],
    *,
    section_name: str,
    check_id: str,
    default_id: str | None,
    path: str,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate optional Semgrep policy fields before deep runs normalize them."""
    if "semgrep" not in item:
        return
    semgrep = item.get("semgrep")
    semgrep_path = f"{path}.semgrep"
    if not isinstance(semgrep, dict):
        errors.append(
            issue(
                "invalid_semgrep_policy",
                semgrep_path,
                "semgrep must be a mapping when present.",
            )
        )
        return
    if section_name != "deep" or (default_id or check_id) != "sg_scan":
        warnings.append(
            issue(
                "ignored_semgrep_policy",
                semgrep_path,
                "semgrep policy is only applied to the built-in sg_scan deep check.",
            )
        )
    for key in sorted(semgrep):
        if key not in KNOWN_SEMGREP_POLICY_KEYS:
            errors.append(
                issue(
                    "unknown_semgrep_policy_key",
                    f"{semgrep_path}.{key}",
                    f"Unknown Semgrep policy key: {key}",
                )
            )
    if "config" in semgrep and not is_non_empty_string(semgrep.get("config")):
        errors.append(
            issue(
                "invalid_semgrep_config",
                f"{semgrep_path}.config",
                "semgrep.config must be a non-empty string when present.",
            )
        )
    for field in ("fail_on_severity", "ignore_rules", "exclude_paths"):
        if field not in semgrep:
            continue
        value = semgrep.get(field)
        field_path = f"{semgrep_path}.{field}"
        if not is_string_list(value):
            errors.append(
                issue(
                    f"invalid_semgrep_{field}",
                    field_path,
                    f"semgrep.{field} must be a list of non-empty strings when present.",
                )
            )
            continue
        if field == "fail_on_severity":
            validate_semgrep_severities(value, field_path, errors)


def validate_semgrep_severities(
    values: Any,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate configured Semgrep severities used for blocking thresholds."""
    if not isinstance(values, list):
        return
    for index, value in enumerate(values):
        severity = str(value).strip().upper()
        if severity not in VALID_SEMGREP_SEVERITIES:
            errors.append(
                issue(
                    "invalid_semgrep_fail_on_severity",
                    f"{path}[{index}]",
                    "semgrep.fail_on_severity must contain INFO, WARNING, WARN, or ERROR.",
                )
            )


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


def is_valid_no_tests_policy(value: Any) -> bool:
    """Return whether a no-tests policy is supported by fast check normalization."""
    return isinstance(value, str) and value.lower() in VALID_NO_TESTS_POLICIES


def is_string_list(value: Any) -> bool:
    """Return whether a value is a list of non-empty strings."""
    return isinstance(value, list) and all(is_non_empty_string(item) for item in value)


def is_non_empty_string(value: Any) -> bool:
    """Return whether a config value is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def validate_adapters(
    root: Path,
    config: dict[str, Any],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
    suggestions: list[str],
) -> None:
    """Validate adapter instruction file references."""
    adapters = config.get("adapters")
    if not isinstance(adapters, dict):
        return
    for name, adapter in sorted(adapters.items()):
        if not isinstance(adapter, dict):
            errors.append(
                issue(
                    "invalid_adapter_type",
                    f"adapters.{name}",
                    f"adapters.{name} must be a mapping.",
                )
            )
            continue
        if adapter.get("enabled") is False:
            continue
        if "enabled" in adapter and not isinstance(adapter.get("enabled"), bool):
            errors.append(
                issue(
                    "invalid_adapter_enabled",
                    f"adapters.{name}.enabled",
                    f"adapters.{name}.enabled must be a boolean when present.",
                )
            )
            continue
        if "instructions_file" not in adapter:
            continue
        instructions_file = adapter.get("instructions_file")
        if not isinstance(instructions_file, str) or not instructions_file.strip():
            errors.append(
                issue(
                    "invalid_adapter_instructions_file",
                    f"adapters.{name}.instructions_file",
                    f"adapters.{name}.instructions_file must be a non-empty string when present.",
                )
            )
            continue
        target = Path(instructions_file).expanduser()
        if not target.is_absolute():
            target = root / target
        if target.is_file():
            continue
        if target.exists():
            warnings.append(
                issue(
                    "adapter_instruction_file_not_file",
                    f"adapters.{name}.instructions_file",
                    f"Instruction file path is not a file: {instructions_file}",
                )
            )
            suggestions.append("qa-z init --with-agent-templates")
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
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def coerce_non_negative_int(value: Any) -> int | None:
    """Return a non-negative integer when possible."""
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def unique_strings(values: list[str]) -> list[str]:
    """Return unique strings in first-seen order."""
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique
