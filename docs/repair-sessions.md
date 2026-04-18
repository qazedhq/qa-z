# QA-Z Repair Sessions

Repair sessions package a failed baseline run into a named local workspace under `.qa-z/sessions/`. The workflow keeps handoff evidence, executor guidance, candidate verification, and the final outcome together without calling live models or mutating remote systems.

## Start A Session

```bash
python -m qa_z repair-session start --baseline-run .qa-z/runs/baseline
python -m qa_z repair-session start --baseline-run latest --session-id session-one --json
```

The start command writes:

- `session.json`
- `executor_guide.md`
- `handoff/packet.json`
- `handoff/prompt.md`
- `handoff/handoff.json`
- `handoff/codex.md`
- `handoff/claude.md`

The handoff directory is derived from the same deterministic evidence used by `repair-prompt`.

## Check Status

```bash
python -m qa_z repair-session status --session session-one
python -m qa_z repair-session status --session .qa-z/sessions/session-one/session.json --json
```

Status reads the local manifest and does not rerun checks.

## Verify The Candidate

```bash
python -m qa_z repair-session verify --session session-one --candidate-run .qa-z/runs/candidate
python -m qa_z github-summary --from-session session-one
```

Verification compares the session baseline with the returned candidate run, writes nested `verify/` artifacts, updates `session.json`, and writes session-level `summary.json` plus `outcome.md`.

## Executor Bridge

```bash
python -m qa_z executor-bridge --from-session session-one
python -m qa_z executor-bridge --from-loop loop-one
```

The bridge copies the session manifest and handoff JSON into `.qa-z/executor/<bridge-id>/inputs/`, then writes `bridge.json`, `executor_guide.md`, `codex.md`, and `claude.md`. When created from a loop outcome that already contains a `repair_session` action, it also copies that loop outcome into the bridge inputs.

The bridge is still local packaging. Its return contract points back to:

```bash
python -m qa_z repair-session verify --session .qa-z/sessions/<session-id> --candidate-run <candidate-run>
```

The exit code follows the deterministic verification verdict:

- `0` for `improved`
- `1` for comparable but not improved outcomes
- `2` for verification errors

## Boundaries

Repair sessions are local artifact organizers. They do not dispatch remote work, call Codex or Claude, create GitHub comments, or decide success from LLM-only judgment. The merge signal comes from deterministic QA-Z run and verification artifacts.
