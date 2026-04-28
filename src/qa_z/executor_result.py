"""Public surface for executor-result contracts and artifact helpers."""

from __future__ import annotations

from qa_z.executor_result_models import (
    EXECUTOR_RESULT_INGEST_KIND,
    EXECUTOR_RESULT_KIND,
    EXECUTOR_RESULT_SCHEMA_VERSION,
    ExecutorChangedFile,
    ExecutorResult,
    ExecutorResultStatus,
    ExecutorValidation,
    ExecutorValidationResult,
    ExecutorValidationStatus,
    ExecutorVerificationHint,
    PLACEHOLDER_SUMMARY,
)
from qa_z.executor_result_artifacts import (
    executor_result_template,
    load_bridge_manifest,
    load_executor_result,
    resolve_bridge_manifest_path,
    store_executor_result,
)
from qa_z.executor_result_io import read_json_object, write_json
from qa_z.executor_result_parsing import (
    list_of_string_lists,
    optional_int,
    optional_string,
    required_string,
    string_list,
)
from qa_z.executor_result_summary import (
    ingest_summary_dict,
    next_recommendation_for_result,
)

__all__ = [
    "EXECUTOR_RESULT_INGEST_KIND",
    "EXECUTOR_RESULT_KIND",
    "EXECUTOR_RESULT_SCHEMA_VERSION",
    "ExecutorChangedFile",
    "ExecutorResult",
    "ExecutorResultStatus",
    "ExecutorValidation",
    "ExecutorValidationResult",
    "ExecutorValidationStatus",
    "ExecutorVerificationHint",
    "PLACEHOLDER_SUMMARY",
    "executor_result_template",
    "load_executor_result",
    "resolve_bridge_manifest_path",
    "load_bridge_manifest",
    "store_executor_result",
    "ingest_summary_dict",
    "next_recommendation_for_result",
    "write_json",
    "read_json_object",
    "required_string",
    "optional_string",
    "optional_int",
    "string_list",
    "list_of_string_lists",
]
