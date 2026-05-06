# Semgrep For AI-Generated Code

Use Semgrep-backed QA-Z deep checks when changes touch:

- authentication or authorization
- secrets, tokens, crypto, or deserialization
- database schema, migrations, or data retention
- API behavior or routing
- infrastructure and CI/CD

QA-Z normalizes Semgrep findings into deep summary artifacts and SARIF. Missing Semgrep should be reported honestly as missing optional evidence unless the project config marks it required.
