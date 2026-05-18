# Community Distribution Plan

QA-Z needs external discovery to reach 30k stars. This page keeps the launch queue concrete.

## Launch Channels

- Hacker News Show HN.
- Reddit: `r/programming`, `r/LocalLLaMA`, `r/ClaudeAI`, `r/cursor`.
- X thread.
- LinkedIn technical post.
- Dev.to or Hashnode article.

## Awesome List PR Targets

- AI coding tools lists.
- Testing tools lists.
- DevSecOps lists.
- Semgrep and SARIF ecosystem lists.

## Before/After Articles

1. AI auth bug caught by QA-Z.
2. Semgrep finding turned into repair prompt.
3. PR gate blocks unsafe generated code before merge.

## Community Example Submissions

Community examples should show how QA-Z turns an agent-produced or risky change into deterministic merge evidence.

Good community examples include:

- a small runnable repository or fixture;
- a clear before/after bug or risk;
- a `qa-z.yaml` configuration;
- commands that reproduce the baseline failure;
- commands that verify the fixed candidate;
- links to relevant QA-Z artifacts or expected artifact paths;
- a short explanation of what QA-Z caught and how the evidence should be reviewed.

Do not submit examples that require live model APIs, private services, production credentials, or hidden network dependencies.

## Required Evidence

A community example should include:

- scope: what the example proves;
- baseline command: how to reproduce the unsafe or failing state;
- candidate command: how to verify the fixed or improved state;
- expected verdict: for example `failed`, `do_not_merge`, `needs_review`, or `improved`;
- artifact paths: expected `.qa-z/runs/...` summaries, review packets, repair prompts, SARIF, or verification reports;
- validation commands: exact commands maintainers can run;
- non-goals: what the example does not prove;
- privacy note: confirmation that secrets, credentials, private paths, and personal data are not included.

Useful expected artifact paths include:

```text
.qa-z/runs/<run-id>/fast/summary.json
.qa-z/runs/<run-id>/deep/summary.json
.qa-z/runs/<run-id>/deep/results.sarif
.qa-z/runs/<run-id>/repair/codex.md
.qa-z/runs/<candidate-run-id>/verify/summary.json
.qa-z/runs/<candidate-run-id>/verify/report.md
```

## Acceptable Local Artifacts

Acceptable committed example material includes:

- source files for the minimal demo;
- tests that reproduce the risk;
- fixed candidate files when useful;
- `qa-z.yaml`;
- documentation explaining expected QA-Z artifact paths;
- small fixture-local `.qa-z/**` only under `benchmarks/fixtures/**/repo/.qa-z/**` when intentionally used as benchmark input.

Generated runtime evidence should normally be referenced by path, not committed.

## Do Not Commit

Do not commit:

- root `.qa-z/**`;
- `benchmarks/results/work/**`;
- `benchmarks/results/summary.json` or `benchmarks/results/report.md` unless intentionally frozen with context;
- `build/**`;
- `dist/**`;
- `src/qa_z.egg-info/**`;
- `.pytest_cache/**`;
- `.mypy_cache/**`;
- `.ruff_cache/**`;
- secrets, credentials, tokens, API keys, private repository contents, or customer data.

## Validation Commands

A community example PR should list the narrowest relevant validation commands.

Typical docs/example validation:

```bash
python -m pytest tests/test_launch_growth_package.py -q
python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public
git diff --check
```

Runnable example validation may include:

```bash
qa-z fast --path examples/<example> --output-dir .qa-z/runs/<example-baseline>
qa-z deep --path examples/<example> --output-dir .qa-z/runs/<example-deep>
qa-z repair-prompt --from-run .qa-z/runs/<example-baseline> --adapter codex
qa-z verify --baseline-run .qa-z/runs/<baseline> --candidate-run .qa-z/runs/<candidate>
```

If these commands generate `.qa-z/**`, keep those artifacts local unless the PR intentionally adds fixture-local benchmark evidence.

## Community Space

Start with GitHub Discussions because it stays close to issues, PRs, and examples. Add Discord only if discussion volume justifies real-time moderation.
