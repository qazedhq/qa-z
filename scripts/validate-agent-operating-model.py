from pathlib import Path
import re
import sys

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # Python 3.10 compatibility

ROOT = Path.cwd()

REQUIRED = [
    "AGENTS.md",
    ".codex/config.toml",
    ".codex/agents/product-flow-auditor.toml",
    ".codex/agents/implementation-surgeon.toml",
    ".codex/agents/verification-runner.toml",
    ".codex/agents/docs-truth-syncer.toml",
    ".agents/skills/project-improvement-loop/SKILL.md",
    ".agents/skills/product-code-slice/SKILL.md",
    ".agents/skills/release-gate-triage/SKILL.md",
    ".agents/skills/md-truth-sync/SKILL.md",
    ".github/copilot-instructions.md",
    "docs/agent/workflow-acceptance.md",
    "docs/agent/next-real-slices.md",
]

MOJIBAKE_PATTERNS = ["諛", "怨", "洹", "鍮", "�", "?곸", "?댁", "?꾩"]
DANGEROUS_CONFIG = [
    r'(?m)^\s*approval_policy\s*=\s*"never"',
    r'(?m)^\s*sandbox_mode\s*=\s*"danger-full-access"',
]


def fail(message: str) -> None:
    print(message)
    sys.exit(1)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


missing = [path for path in REQUIRED if not (ROOT / path).exists()]
if missing:
    fail("Missing required workflow files:\n- " + "\n- ".join(missing))

# TOML parse and required custom-agent fields.
try:
    tomllib.loads(read(ROOT / ".codex/config.toml"))
except Exception as exc:
    fail(f".codex/config.toml: invalid TOML: {exc}")

config_text = read(ROOT / ".codex/config.toml")
for pattern in DANGEROUS_CONFIG:
    if re.search(pattern, config_text):
        fail(".codex/config.toml: do not hard-code approval_policy=never or sandbox_mode=danger-full-access in repo config")

for path in sorted((ROOT / ".codex/agents").glob("*.toml")):
    try:
        data = tomllib.loads(read(path))
    except Exception as exc:
        fail(f"{path}: invalid TOML: {exc}")
    for key in ("name", "description", "developer_instructions"):
        if not data.get(key):
            fail(f"{path}: missing {key}")

# Skills metadata and handoff coverage.
for path in sorted((ROOT / ".agents/skills").glob("*/SKILL.md")):
    text = read(path)
    if not text.startswith("---"):
        fail(f"{path}: missing frontmatter")
    head = text.split("---", 2)[1]
    if "name:" not in head or "description:" not in head:
        fail(f"{path}: missing name or description frontmatter")

loop_text = read(ROOT / ".agents/skills/project-improvement-loop/SKILL.md")
if "product-code-slice" not in loop_text or "next-real-slices.md" not in loop_text:
    fail("project-improvement-loop skill must hand off to product-code-slice and next-real-slices.md")

# Roster must point to Codex, not Claude, as installed source of truth.
roster = ROOT / "docs/agent/subagent-roster.md"
if roster.exists():
    text = read(roster)
    if "Use these role files under `.claude/agents/`" in text:
        fail(f"{roster}: roster incorrectly treats .claude/agents as source of truth")
    for match in re.findall(r"`([a-z0-9-]+)`", text):
        candidate = ROOT / ".codex/agents" / f"{match}.toml"
        if not candidate.exists() and match not in {
            "product-flow-auditor",
            "implementation-surgeon",
            "verification-runner",
            "docs-truth-syncer",
        }:
            fail(f"{roster}: listed specialist `{match}` has no {candidate}")

# Next real slices should be actionable, not another scaffold queue.
next_slices = read(ROOT / "docs/agent/next-real-slices.md")
for required_phrase in ("Discovery commands", "Validation candidates", "Stop rule"):
    if required_phrase not in next_slices:
        fail(f"docs/agent/next-real-slices.md: missing {required_phrase}")
if next_slices.count("## Slice ") < 2:
    fail("docs/agent/next-real-slices.md: expected multiple executable product slices")

# Workflow acceptance should include already-present operating model case.
acceptance = read(ROOT / "docs/agent/workflow-acceptance.md")
if "Scenario 4: operating model already exists" not in acceptance:
    fail("workflow-acceptance.md: missing scenario 4 for post-scaffold improvement")

# Catch common mojibake in durable instruction files.
for path in [ROOT / "AGENTS.md", ROOT / ".github/copilot-instructions.md"] + list((ROOT / "docs/agent").glob("*.md")):
    if not path.exists():
        continue
    text = read(path)
    for token in MOJIBAKE_PATTERNS:
        if token in text:
            fail(f"{path}: possible mojibake token {token!r}")

print("agent operating model: OK")
