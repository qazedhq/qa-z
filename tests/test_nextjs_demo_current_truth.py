from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "nextjs-demo"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_nextjs_demo_has_runnable_project_files() -> None:
    required_paths = [
        "package.json",
        "tsconfig.json",
        "eslint.config.js",
        "vitest.config.ts",
        "next-env.d.ts",
        "app/layout.tsx",
        "app/page.tsx",
        "scripts/npm-run.mjs",
        "src/invoice-access.ts",
        "tests/invoice-access.test.ts",
        "qa-z.yaml",
        "README.md",
        "issue.md",
        "spec.md",
    ]

    missing = [path for path in required_paths if not (DEMO / path).is_file()]

    assert missing == []


def test_nextjs_demo_package_scripts_and_publish_boundary() -> None:
    package_json = json.loads((DEMO / "package.json").read_text(encoding="utf-8"))

    assert package_json["private"] is True
    assert package_json["scripts"]["lint"] == "eslint ."
    assert package_json["scripts"]["typecheck"] == "tsc --noEmit"
    assert package_json["scripts"]["test"] == "vitest run"
    assert "publishConfig" not in package_json
    assert "files" not in package_json


def test_nextjs_demo_qaz_config_wires_typescript_fast_gate() -> None:
    config = yaml.safe_load((DEMO / "qa-z.yaml").read_text(encoding="utf-8"))

    assert config["project"]["name"] == "qa-z-nextjs-demo"
    assert config["project"]["languages"] == ["typescript"]
    assert config["project"]["roots"] == ["app", "src", "tests"]
    assert config["fast"]["selection"]["default_mode"] == "smart"
    assert [check["id"] for check in config["fast"]["checks"]] == [
        "ts_lint",
        "ts_type",
        "ts_test",
    ]
    assert [check["run"][0:2] for check in config["fast"]["checks"]] == [
        ["node", "scripts/npm-run.mjs"],
        ["node", "scripts/npm-run.mjs"],
        ["node", "scripts/npm-run.mjs"],
    ]
    assert [check["run"][2] for check in config["fast"]["checks"]] == [
        "lint",
        "typecheck",
        "test",
    ]
    assert config["deep"]["checks"] == []


def test_nextjs_demo_docs_are_runnable_and_live_free() -> None:
    demo_readme = (DEMO / "README.md").read_text(encoding="utf-8")
    examples_index = read("examples/README.md")
    docs_index = read("docs/README.md")

    for command in (
        "npm install",
        "npm run lint",
        "npm run typecheck",
        "npm test",
        'python -m qa_z plan --path . --title "Protect Next.js invoice access" --issue issue.md --spec spec.md',
        "python -m qa_z fast --path . --selection smart",
    ):
        assert command in demo_readme

    for text in (
        ".qa-z/runs/latest",
        "fast/summary.json",
        "Generated `.qa-z/**` evidence remains local and must not be committed",
        "no live agents",
        "no hosted services",
        "no package publish",
        "no executor-bridge/result behavior",
        "QA-Z invokes those same package scripts through `scripts/npm-run.mjs`",
    ):
        assert text in demo_readme

    assert "placeholder-only" not in demo_readme.lower()
    assert "| [nextjs-demo](nextjs-demo/) | Runnable |" in examples_index
    assert "## Next.js Placeholder" not in examples_index
    assert "Placeholder-only | Planned future Next.js" not in examples_index
    assert "Runnable Next.js" in docs_index
