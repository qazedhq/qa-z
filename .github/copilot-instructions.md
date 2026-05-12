# GitHub Copilot Instructions

Use root `AGENTS.md` for repository-wide operating rules.

Prioritize the critical user-facing flows listed there. Do not weaken tests, gates, auth, security, image, approval, deploy, or release checks. Do not claim production readiness without command, runtime, manual, or release evidence.

For broad changes, prefer one small Flow, Contract, Evidence, or Cleanup Slice. Report changed files, validation result, user impact, remaining blockers, and next safe slice.

When the operating model already exists, use `docs/agent/next-real-slices.md` to choose one product code/test/runtime/evidence slice; avoid scaffold-only changes unless the workflow validator fails.
