---
name: release-gate-triage
description: Use when release readiness, deploy, approval, production, public launch, app release, or source-release claims are involved.
---

# Release Gate Triage

1. List each gate as `PASS`, `FAIL`, `BLOCKED`, `PARTIAL`, `NO-GO`, or `NOT CHECKED`.
2. Separate local-fixable failures from external or human blockers.
3. Never convert `BLOCKED` into `PASS` without real evidence.
4. For each blocked item, name the next safe local improvement.
5. Update release docs only after command, runtime, or manual evidence changes.
