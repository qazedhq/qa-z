from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def package_version_from_pyproject() -> str:
    pyproject = read("pyproject.toml")
    match = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_beta_readiness_report_keeps_release_execution_blocked() -> None:
    report = read("docs/reports/v0.10.0-beta-readiness.md")

    assert "Audit type: release-candidate gap report, not release execution." in report
    assert "`v0.10.0-beta` is\nplanned, not released" in report
    assert "Open GitHub issues: `0`" in report
    assert "Open GitHub pull requests: `0`" in report
    assert "issue #4 is closed as completed, and PR #59" in report
    assert "Current public alpha: `v0.9.9-alpha` GitHub prerelease." in report
    assert f"Package metadata version: `{package_version_from_pyproject()}`" in report
    assert "registry_upload_executed=false" in report
    assert "`RELEASE_EXECUTION_APPROVED=true`" in report
    assert "`PACKAGE_PUBLISH_ALLOWED=true`" in report
    assert "Recommendation: `NO-GO` for v0.10.0-beta release execution today." in (
        report
    )

    for forbidden in (
        "registry_upload_executed=true",
        "v0.10.0-beta is released",
        "PyPI publish completed",
        "TestPyPI publish completed",
    ):
        assert forbidden not in report


def test_public_install_docs_do_not_claim_live_pypi_install() -> None:
    readme = read("README.md")
    quickstart = read("docs/quickstart.md")
    package_plan = read("docs/package-publish-plan.md")
    report = read("docs/reports/v0.10.0-beta-readiness.md")

    for public_install_surface in (readme, quickstart):
        assert "pipx install qa-z" not in public_install_surface
        assert "uv tool install qa-z" not in public_install_surface
        assert "git+https://github.com/qazedhq/qa-z.git" in public_install_surface

    beta_section = package_plan.split("## v0.10.0-beta", 1)[1]
    assert "pipx install qa-z" in beta_section
    assert "uv tool install qa-z" in beta_section
    assert "future `v0.10.0-beta` planning" in report
    assert "A successful rehearsal proves only local package readiness." in (
        package_plan
    )


def test_beta_readiness_report_records_validation_and_cleanup_contract() -> None:
    report = read("docs/reports/v0.10.0-beta-readiness.md")

    for status in ("`PASS`", "`NOT RUN`", "`BLOCKED`"):
        assert status in report

    for command in (
        "python -m pytest -q",
        "python -m ruff check .",
        "python -m ruff format --check .",
        "python -m mypy src tests",
        "python -m build --sdist --wheel",
        "python scripts/alpha_release_artifact_smoke.py --json",
        "python -m qa_z benchmark --results-dir benchmarks/results-ci --json",
        "git diff --check",
    ):
        assert command in report

    for evidence in (
        "`1804 passed",
        "`54/54 fixtures`",
        "`overall_rate=1.0`",
        "`qa_z-0.9.8a0.tar.gz`",
        "`qa_z-0.9.8a0-py3-none-any.whl`",
        "`No module named twine`",
        "`2` moderate advisories",
        "`GHSA-qx2v-qp2m-jg93`",
        "`CVE-2026-41305`",
        "`next@15.5.18`",
        "`postcss@8.4.31`",
        "`8.5.10`",
        "`next@latest`",
    ):
        assert evidence in report

    assert "a blind Next.js major bump does not prove closure" in report
    assert "does not run `npm audit fix --force`" in report
    assert "does not downgrade or override Next.js" in report
    assert "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md" in report
    assert "release execution `NO-GO` remains unchanged" in " ".join(report.split())

    for artifact in (
        "`build/`",
        "`dist/`",
        "`src/qa_z.egg-info/`",
        "`.qa-z/`",
        "`benchmarks/results-ci/`",
        "`examples/**/node_modules/`",
        "`examples/**/qa/contracts/`",
    ):
        assert artifact in report


def test_beta_readiness_report_keeps_hosted_demo_static() -> None:
    hosted_demo = read("docs/hosted-demo.md")
    docs_site = read("docs/docs-site.md")
    report = read("docs/reports/v0.10.0-beta-readiness.md")

    for text in (hosted_demo, docs_site, report):
        assert "QA-Z Cloud" in text

    assert "The hosted demo is a static docs page, not QA-Z Cloud." in hosted_demo
    assert "static/local replay, not QA-Z Cloud" in report
    assert "live-agent execution" in hosted_demo
    assert "uploaded source-code analysis" in hosted_demo
