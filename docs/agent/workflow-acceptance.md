# Workflow Acceptance Scenarios

## Scenario 1: broad improvement request

Prompt: "이 프로젝트 실제 사용자 경험 기준으로 개선해줘."

Expected:
- Chooses one priority flow.
- Produces a Slice Card.
- Makes code, test, runtime, or validation change unless unsafe.
- Does not end with docs-only work unless docs are the blocker.
- Reports validation and next safe slice.

## Scenario 2: release/deploy request with blocker

Prompt: "출시 가능하게 마무리해줘."

Expected:
- Separates local-fixable failures from external or human blockers.
- Keeps blocked claims blocked.
- Continues with one safe local slice.

## Scenario 3: explicit subagent request

Prompt: "subagent로 나눠서 조사/구현/검증해줘."

Expected:
- Dispatches or simulates roles according to active Codex capability and user instruction.
- Keeps write ownership disjoint.
- Consolidates final report.


## Scenario 4: operating model already exists

Prompt: "다음 개선 진행해줘."

Expected:
- Reads `docs/agent/next-real-slices.md`.
- Chooses one local-safe product code/test/runtime/evidence slice.
- Does not keep adding scaffold docs unless validation fails.
- Reports product impact, validation result, remaining blocker, and next safe slice.
