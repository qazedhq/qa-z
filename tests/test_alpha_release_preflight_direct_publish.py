from __future__ import annotations

from tests.alpha_release_preflight_test_support import (
    FakeRunner,
    base_responses,
    load_preflight_module,
    public_release_branch_metadata,
)


def test_preflight_direct_publish_guidance_uses_repository_default_branch(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        "",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_release_branch_metadata,
    )
    payload = module.result_payload(
        result, repository_url="https://github.com/qazedhq/qa-z.git"
    )

    assert payload["publish_checklist"] == [
        (
            'Verify the approved release SHA with `test "$(git rev-parse HEAD)" = '
            '"<approved-sha>"`, then push the validated release baseline to release '
            "with `git push origin <approved-sha>:release`."
        ),
        "Wait for remote CI: `test`, `Build package artifacts`, `Smoke test built package artifacts`, and `qa-z` must pass.",
        "Create and verify `v0.9.8-alpha` from the validated default branch, then `git push origin v0.9.8-alpha`.",
    ]
    assert payload["next_actions"] == [
        (
            "Remote is empty and ready for direct publish; push the release "
            "baseline to release, wait for remote CI, and tag only after the "
            "validated default branch is green."
        )
    ]
    assert payload["next_commands"] == [
        'test "$(git rev-parse HEAD)" = "<approved-sha>"',
        "git push origin <approved-sha>:release",
    ]
