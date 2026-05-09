# Actions Runtime Maintenance

The 2026-05-08 `main` runs emitted GitHub Actions annotations for Node.js 20
action runtimes:

- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/setup-node@v4`
- `actions/upload-artifact@v4`

The maintenance path is to use the current Node.js 24-compatible major versions
for repository workflows, reusable workflow templates, and composite actions:

- `actions/checkout@v6`
- `actions/setup-python@v6`
- `actions/setup-node@v6`
- `actions/upload-artifact@v6`

`github/codeql-action/upload-sarif@v4` is intentionally unchanged because the
latest warning annotations did not identify it as a Node.js 20 runtime action.

Validation:

```bash
python -m pytest -q tests/test_github_workflow.py
```
