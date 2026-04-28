"""CLI-facing tests for the alpha release gate runtime wrapper."""

from __future__ import annotations

import json

from tests.alpha_release_gate_test_support import load_gate_module


def test_alpha_release_gate_cli_can_emit_json_and_write_output(
    monkeypatch, tmp_path, capsys
):
    module = load_gate_module()
    output_path = tmp_path / "evidence.json"

    def fake_run_alpha_release_gate(_repo_root, **kwargs):
        assert kwargs["with_deps"] is True
        assert kwargs["allow_dirty"] is True
        assert kwargs["include_remote"] is True
        assert kwargs["repository_url"] == "https://github.com/qazedhq/qa-z.git"
        assert kwargs["expected_origin_url"] == "https://github.com/qazedhq/qa-z.git"
        assert kwargs["allow_existing_refs"] is True
        assert kwargs["preflight_output"] == output_path.with_suffix(".preflight.json")
        assert kwargs["worktree_plan_output"] == output_path.with_suffix(
            ".worktree-plan.json"
        )
        return module.AlphaReleaseGateResult(
            summary="alpha release gate passed",
            exit_code=0,
            commands=[],
            payload={
                "summary": "alpha release gate passed",
                "exit_code": 0,
                "checks": [],
            },
        )

    monkeypatch.setattr(module, "run_alpha_release_gate", fake_run_alpha_release_gate)

    exit_code = module.main(
        [
            "--with-deps",
            "--allow-dirty",
            "--include-remote",
            "--repository-url",
            "https://github.com/qazedhq/qa-z.git",
            "--expected-origin-url",
            "https://github.com/qazedhq/qa-z.git",
            "--allow-existing-refs",
            "--json",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["summary"] == "alpha release gate passed"
    assert json.loads(output_path.read_text()) == payload


def test_alpha_release_gate_cli_prints_next_actions(monkeypatch, capsys):
    module = load_gate_module()

    def fake_run_alpha_release_gate(_repo_root, **_kwargs):
        return module.AlphaReleaseGateResult(
            summary="alpha release gate failed",
            exit_code=1,
            commands=[],
            payload={
                "summary": "alpha release gate failed",
                "exit_code": 1,
                "checks": [
                    {
                        "name": "local_preflight",
                        "label": "python scripts/alpha_release_preflight.py --json",
                        "status": "failed",
                        "stderr_tail": "",
                        "stdout_tail": "release preflight failed",
                    }
                ],
                "next_actions": [
                    (
                        "Create or expose the public GitHub repository qazedhq/qa-z, "
                        "then rerun remote preflight."
                    )
                ],
                "next_commands": [
                    (
                        "python scripts/alpha_release_preflight.py --repository-url "
                        "https://github.com/qazedhq/qa-z.git --json"
                    )
                ],
            },
        )

    monkeypatch.setattr(module, "run_alpha_release_gate", fake_run_alpha_release_gate)

    exit_code = module.main([])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Next actions:" in captured.out
    assert (
        "- Create or expose the public GitHub repository qazedhq/qa-z, "
        "then rerun remote preflight."
    ) in captured.out
    assert "Next commands:" in captured.out
    assert (
        "- python scripts/alpha_release_preflight.py --repository-url "
        "https://github.com/qazedhq/qa-z.git --json"
    ) in captured.out
