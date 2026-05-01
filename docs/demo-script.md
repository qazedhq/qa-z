# QA-Z Demo Script

Demo title:

```text
AI wrote a bad auth change. QA-Z caught it.
```

This script uses real CLI commands and local artifacts. It does not depend on screenshots, GIFs, generated media, or live model APIs.

## Setup

From the repository root:

```bash
python -m pip install -e .[dev]
python -m qa_z --help
cd examples/agent-auth-bug
```

If `qa-z` is on PATH, use the shorter command form below. Otherwise replace `qa-z` with `python -m qa_z`.

## Baseline: Agent Change Is Unsafe

```bash
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected result:

```text
Before:
- Agent changed auth logic.
- Tests failed.
- QA-Z produced a repair prompt.

QA-Z:
- Generated a QA contract.
- Captured deterministic evidence.
- Produced a repair prompt for Codex.
- Preserved the run artifacts under .qa-z/runs/baseline.
```

## Optional Deep Check

Install Semgrep and run the local auth rule:

```bash
python -m pip install semgrep
qa-z deep --from-run .qa-z/runs/baseline
```

Expected result: the local Semgrep rule flags the risky signed-in-user shortcut in `app/auth.py`.

## Candidate Repair

Apply the included fixed implementation:

```bash
cp app/auth.fixed.py app/auth.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

PowerShell:

```powershell
Copy-Item app\auth.fixed.py app\auth.py -Force
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

## Expected Artifact Surfaces

```text
.qa-z/runs/baseline/fast/summary.json
.qa-z/runs/baseline/review/
.qa-z/runs/baseline/repair/
.qa-z/runs/baseline/deep/results.sarif
.qa-z/runs/candidate/fast/summary.json
```

Use this as the short recorded terminal demo. Keep the message simple:

```text
AI-generated code -> QA-Z -> deterministic merge evidence
```
