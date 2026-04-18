# P20 Dry-Run Current-Truth Design

## Goal

Lock the landed dry-run publish and residue behavior into current-truth docs so README, artifact schema, and regression tests describe the same surfaces the code now emits.

## Scope

Included:

- README updates for publish/session dry-run residue
- artifact-schema updates for repair-session summary dry-run fields
- roadmap/status notes for P18 through P20
- current-truth regression coverage

Excluded:

- new commands
- remote publishing
- non-deterministic doc generation

## Design

P18 and P19 add real behavior to repair-session summaries, `outcome.md`, and
GitHub-style publish output. P20 keeps those changes honest by updating the
public README, the artifact schema reference, and the milestone status notes,
then pinning the new wording with a small current-truth regression test.
