# Security Policy

QA-Z is an alpha project. Please report security issues privately when possible and include deterministic reproduction evidence.

## Supported Version

The current public alpha target is `v0.9.8-alpha`.

## Reporting

Preferred private path: open a GitHub Security Advisory for this repository if
that option is available to you. If advisories are unavailable, contact a
maintainer through an existing private channel before sharing exploit details.
Do not include live secrets in public issues.

When reporting a vulnerability, include:

- affected command or artifact surface
- exact command run
- observed output or artifact path
- expected safe behavior
- repository state or fixture needed to reproduce

Do not include live secrets in reports. If a fixture needs secret-like text, use synthetic values that cannot grant access to a real system.

## Project Boundaries

QA-Z local flows do not call live Codex, Claude, or other model APIs. Security fixes should preserve deterministic gates and should not replace executable checks with LLM-only judgments.
