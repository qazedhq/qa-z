"""Post-repair verification comparison and artifacts."""

from __future__ import annotations

from qa_z.verification_artifacts import (
    load_verification_run,
    render_verification_report,
    write_verification_artifacts,
)
from qa_z.verification_compare import (
    compare_deep_findings,
    compare_fast_checks,
    compare_verification_runs,
)
from qa_z.verification_finding_support import (
    blocking_severities,
    extract_deep_findings,
    find_matching_candidate,
    normalize_active_finding,
    normalize_grouped_finding,
)
from qa_z.verification_findings import (
    compare_deep_findings_impl as _compare_deep_findings_impl,
)
from qa_z.verification_models import (
    VerificationArtifactPaths,
    VerificationComparison,
    VerificationFindingDelta,
    VerificationRun,
    VerificationVerdict,
)
from qa_z.verification_outcome import (
    comparison_json,
    verification_summary_dict,
    verify_exit_code,
)
from qa_z.verification_status import (
    build_comparison_summary,
    count_blocking_checks,
    count_blocking_deep_findings,
    count_deep_findings,
    derive_verdict,
)

VERIFY_COMPARE_KIND = "qa_z.verify_compare"
VERIFY_SUMMARY_KIND = "qa_z.verify_summary"
VERIFY_SCHEMA_VERSION = 1

__all__ = [
    "VERIFY_COMPARE_KIND",
    "VERIFY_SUMMARY_KIND",
    "VERIFY_SCHEMA_VERSION",
    "VerificationArtifactPaths",
    "VerificationComparison",
    "VerificationFindingDelta",
    "VerificationRun",
    "VerificationVerdict",
    "_compare_deep_findings_impl",
    "blocking_severities",
    "build_comparison_summary",
    "compare_deep_findings",
    "compare_fast_checks",
    "compare_verification_runs",
    "comparison_json",
    "count_blocking_checks",
    "count_blocking_deep_findings",
    "count_deep_findings",
    "derive_verdict",
    "extract_deep_findings",
    "find_matching_candidate",
    "load_verification_run",
    "normalize_active_finding",
    "normalize_grouped_finding",
    "render_verification_report",
    "verification_summary_dict",
    "verify_exit_code",
    "write_verification_artifacts",
]
