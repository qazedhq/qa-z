from __future__ import annotations

import json
from pathlib import Path

import qa_z.benchmark_executor_loop_context as loop_context_module


def test_write_benchmark_loop_context_writes_self_inspect_and_outcome(
    tmp_path: Path,
) -> None:
    loop_context_module.write_benchmark_loop_context(
        workspace=tmp_path,
        loop_id="loop-7",
        session_id="session-one",
        fixed_now="2026-04-16T00:00:00Z",
        context_paths=["docs/spec.md"],
    )

    self_inspect = json.loads(
        (tmp_path / ".qa-z" / "loops" / "loop-7" / "self_inspect.json").read_text(
            encoding="utf-8"
        )
    )
    outcome = json.loads(
        (tmp_path / ".qa-z" / "loops" / "loop-7" / "outcome.json").read_text(
            encoding="utf-8"
        )
    )

    assert self_inspect["loop_id"] == "loop-7"
    assert outcome["actions_prepared"][0]["session_id"] == "session-one"
    assert outcome["actions_prepared"][0]["context_paths"] == ["docs/spec.md"]
    assert outcome["artifacts"]["outcome"] == ".qa-z/loops/loop-7/outcome.json"
