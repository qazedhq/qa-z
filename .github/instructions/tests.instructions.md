---
applyTo: "**/*.{test,spec}.*,tests/**,e2e/**"
---

Prefer targeted regression tests for the changed behavior.

Make the failing behavior observable before changing implementation when practical.

Keep assertions tied to user-visible or contract-visible behavior.

Do not delete assertions to make a check pass.

Do not skip tests to make a check pass.

Do not weaken expectations to make a check pass.
