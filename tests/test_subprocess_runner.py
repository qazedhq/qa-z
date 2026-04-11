"""Tests for deterministic subprocess check execution."""

from __future__ import annotations

import sys

from qa_z.runners.models import CheckSpec
from qa_z.runners.subprocess import run_check


def test_run_check_decodes_utf8_output_on_non_utf8_windows_locales(tmp_path) -> None:
    spec = CheckSpec(
        id="utf8_failure",
        command=[
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stderr.buffer.write('허용되지 않음\\n'.encode('utf-8')); "
                "sys.exit(1)"
            ),
        ],
        kind="test",
    )

    result = run_check(spec, cwd=tmp_path)

    assert result.status == "failed"
    assert result.exit_code == 1
    assert "허용되지 않음" in result.stderr_tail
