# Worktree Area Evidence Summary Design

## Purpose

QA-Z already promotes a dirty-worktree backlog item when the local integration
branch becomes too large. The current evidence summary gives counts and a small
path sample, but it does not explain which repository areas dominate the dirty
surface.

This pass adds a deterministic area summary to the same `git_status` evidence so
operators can split the alpha closure worktree into safer batches without
opening the full `git status` output first.

## Scope

- Add a small path classifier for dirty worktree paths.
- Render area counts inside the existing dirty-worktree evidence summary.
- Keep the candidate id, recommendation, scoring, JSON artifact shape, and live
  execution boundary unchanged.
- Document that this is an operator-facing evidence summary improvement.

## Area Buckets

The classifier uses stable repository path prefixes:

- `.github/workflows/` -> `workflow`
- `src/` -> `source`
- `tests/` -> `tests`
- `docs/` and `README.md` -> `docs`
- `benchmarks/` or `benchmark/` -> `benchmark`
- `examples/` -> `examples`
- `templates/` -> `templates`
- root config files such as `.gitignore`, `pyproject.toml`, and
  `qa-z.yaml.example` -> `config`
- root `.qa-z/` or `benchmarks/results/` -> `runtime_artifact`
- everything else -> `other`

The summary sorts buckets by descending count and then by bucket name. It renders
at most five buckets to keep stdout and backlog evidence concise.

## Output Shape

Existing summary:

```text
modified=12; untracked=24; staged=0; sample=README.md, docs/report.md, src/qa_z/cli.py
```

New summary:

```text
modified=12; untracked=24; staged=0; areas=docs:2, source:2; sample=README.md, docs/report.md, src/qa_z/cli.py
```

If no dirty paths are present, no `areas=` segment is rendered.

## Non-Goals

- Do not add a new CLI command.
- Do not mutate, delete, stage, commit, or reorder files.
- Do not change backlog candidate ids, scores, or recommendation mapping.
- Do not add network, live executor, or model behavior.

## Test Strategy

- Unit-test the area summary through the existing dirty-worktree self-inspection
  path.
- Unit-test the path classifier with representative repository areas.
- Keep existing worktree-risk tests passing by preserving the original count
  text.

## Documentation

Update README, artifact schema, and current report/roadmap language to say the
dirty-worktree evidence now includes deterministic area counts for operator
triage.
