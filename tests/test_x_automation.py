from __future__ import annotations

import json
import importlib.util
import socket
import threading
import time
import urllib.request
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "marketing" / "x" / "scripts"
SPEC = importlib.util.spec_from_file_location("qaz_x", SCRIPT_DIR / "qaz_x.py")
assert SPEC is not None
assert SPEC.loader is not None
qaz_x: Any = importlib.util.module_from_spec(SPEC)
sys.modules["qaz_x"] = qaz_x
SPEC.loader.exec_module(qaz_x)


def test_auth_url_writes_pkce_state_without_secrets(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("X_CLIENT_ID", "client-id")
    state_file = tmp_path / "oauth-state.json"

    assert (
        qaz_x.auth_url_command(
            redirect_uri="http://127.0.0.1:8080/callback",
            state_file=state_file,
            scopes=("tweet.read", "tweet.write", "users.read", "offline.access"),
        )
        == 0
    )

    output = capsys.readouterr().out
    state_payload = json.loads(state_file.read_text(encoding="utf-8"))

    assert "AUTHORIZATION_URL=" in output
    assert "https://x.com/i/oauth2/authorize?" in output
    assert "code_challenge_method=S256" in output
    assert "client_secret" not in state_payload
    assert "access_token" not in state_payload
    assert "refresh_token" not in state_payload
    assert len(state_payload["code_verifier"]) >= 43


def test_exchange_code_uses_confidential_client_auth_and_redacts_tokens(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("X_CLIENT_ID", "client-id")
    monkeypatch.setenv("X_CLIENT_SECRET", "client-secret")
    state_file = tmp_path / "oauth-state.json"
    token_file = tmp_path / "tokens.json"
    state_file.write_text(
        json.dumps(
            {
                "code_verifier": "verifier",
                "redirect_uri": "http://127.0.0.1:8080/callback",
                "scopes": ["tweet.read", "tweet.write", "users.read"],
            }
        ),
        encoding="utf-8",
    )
    response_payload = {
        "token_type": "bearer",
        "expires_in": 7200,
        "access_token": "example-access-token",
        "refresh_token": "example-refresh-token",
    }
    fake_response = mock.Mock()
    fake_response.__enter__ = lambda self: self
    fake_response.__exit__ = lambda self, *args: None
    fake_response.read.return_value = json.dumps(response_payload).encode("utf-8")

    with mock.patch("urllib.request.urlopen", return_value=fake_response) as urlopen:
        assert qaz_x.exchange_code_command("abc123", state_file, token_file) == 0

    request = urlopen.call_args.args[0]
    output = capsys.readouterr().out
    saved_payload = json.loads(token_file.read_text(encoding="utf-8"))

    assert request.full_url == "https://api.x.com/2/oauth2/token"
    assert request.headers["Authorization"].startswith("Basic ")
    assert saved_payload["access_token"] == "example-access-token"
    assert "example-access-token" not in output
    assert "example-refresh-token" not in output
    assert '"access_token": "<redacted>"' in output


def test_post_command_reads_enabled_token_file_and_updates_queue(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "x"
    (workspace / "content" / "posts").mkdir(parents=True)
    (workspace / ".state").mkdir()
    (workspace / "config.example.json").write_text(
        json.dumps(
            {
                "github_url": "https://github.com/qazedhq/qa-z",
                "max_post_chars": 260,
                "max_mentions_per_post": 1,
                "posting_enabled_env": "QA_Z_X_POST_ENABLE",
                "token_env": "X_USER_ACCESS_TOKEN",
                "token_file": ".state/x_tokens.json",
            }
        ),
        encoding="utf-8",
    )
    (workspace / "queue.json").write_text(
        json.dumps(
            {
                "posts": [
                    {
                        "id": "launch",
                        "file": "content/posts/launch.md",
                        "status": "approved",
                        "posted_id": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (workspace / "content" / "posts" / "launch.md").write_text(
        "# Launch\n\n## Post\n\nQA-Z launch https://github.com/qazedhq/qa-z\n",
        encoding="utf-8",
    )
    (workspace / ".state" / "x_tokens.json").write_text(
        json.dumps({"access_token": "file-token"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("QA_Z_X_POST_ENABLE", "1")
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)
    fake_response = mock.Mock()
    fake_response.__enter__ = lambda self: self
    fake_response.__exit__ = lambda self, *args: None
    fake_response.read.return_value = json.dumps({"data": {"id": "12345"}}).encode(
        "utf-8"
    )

    with mock.patch.object(qaz_x, "ROOT", workspace):
        with mock.patch(
            "urllib.request.urlopen", return_value=fake_response
        ) as urlopen:
            assert qaz_x.post_command(execute=True) == 0

    request = urlopen.call_args.args[0]
    queue_payload = json.loads((workspace / "queue.json").read_text(encoding="utf-8"))

    assert request.headers["Authorization"] == "Bearer file-token"
    assert queue_payload["posts"][0]["status"] == "posted"
    assert queue_payload["posts"][0]["posted_id"] == "12345"


def test_post_command_reports_api_block_without_marking_queue_posted(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    workspace = tmp_path / "x"
    (workspace / "content" / "posts").mkdir(parents=True)
    (workspace / ".state").mkdir()
    (workspace / "config.example.json").write_text(
        json.dumps(
            {
                "github_url": "https://github.com/qazedhq/qa-z",
                "max_post_chars": 260,
                "max_mentions_per_post": 1,
                "posting_enabled_env": "QA_Z_X_POST_ENABLE",
                "token_env": "X_USER_ACCESS_TOKEN",
                "token_file": ".state/x_tokens.json",
            }
        ),
        encoding="utf-8",
    )
    (workspace / "queue.json").write_text(
        json.dumps(
            {
                "posts": [
                    {
                        "id": "launch",
                        "file": "content/posts/launch.md",
                        "status": "approved",
                        "posted_id": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (workspace / "content" / "posts" / "launch.md").write_text(
        "# Launch\n\n## Post\n\nQA-Z launch https://github.com/qazedhq/qa-z\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("QA_Z_X_POST_ENABLE", "1")

    with mock.patch.object(qaz_x, "ROOT", workspace):
        with mock.patch.object(
            qaz_x,
            "post_to_x",
            side_effect=RuntimeError("X API rejected post: HTTP 402: CreditsDepleted"),
        ):
            assert qaz_x.post_command(execute=True) == 1

    output = capsys.readouterr().out
    queue_payload = json.loads((workspace / "queue.json").read_text(encoding="utf-8"))

    assert "POST_BLOCKED" in output
    assert "CreditsDepleted" in output
    assert queue_payload["posts"][0]["status"] == "approved"
    assert queue_payload["posts"][0]["posted_id"] is None


def test_reply_drafts_supports_semgrep_topic_alias(capsys) -> None:
    assert qaz_x.reply_drafts("semgrep") == 0

    output = capsys.readouterr().out

    assert "## Semgrep / AppSec" in output
    assert "AI coding makes shift-left security more important" in output
    assert "No matching topic" not in output


def test_login_rejects_non_local_redirect_uri(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("X_CLIENT_ID", "client-id")

    with pytest.raises(RuntimeError, match="local HTTP redirect"):
        qaz_x.login_command(
            redirect_uri="https://example.com/callback",
            state_file=tmp_path / "state.json",
            token_file=tmp_path / "tokens.json",
            open_browser=False,
            timeout_seconds=0.1,
        )


def test_login_accepts_local_callback_and_exchanges_code(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("X_CLIENT_ID", "client-id")
    state_file = tmp_path / "state.json"
    token_file = tmp_path / "tokens.json"
    exchange_calls: list[tuple[str, Path, Path, str | None]] = []
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    def fake_exchange(
        code: str,
        exchange_state_file: Path,
        exchange_token_file: Path,
        returned_state: str | None = None,
    ) -> int:
        exchange_calls.append(
            (code, exchange_state_file, exchange_token_file, returned_state)
        )
        exchange_token_file.write_text(
            json.dumps({"access_token": "example-access-token"}),
            encoding="utf-8",
        )
        return 0

    with mock.patch.object(qaz_x, "exchange_code_command", side_effect=fake_exchange):
        thread = threading.Thread(
            target=qaz_x.login_command,
            kwargs={
                "redirect_uri": f"http://127.0.0.1:{port}/callback",
                "state_file": state_file,
                "token_file": token_file,
                "open_browser": False,
                "timeout_seconds": 5,
            },
        )
        thread.start()
        deadline = time.time() + 3
        while not state_file.exists() and time.time() < deadline:
            time.sleep(0.01)
        state_payload = json.loads(state_file.read_text(encoding="utf-8"))

        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/callback?code=abc123&state={state_payload['state']}",
            timeout=3,
        ) as response:
            assert response.status == 200

        thread.join(timeout=3)

    assert not thread.is_alive()
    assert exchange_calls == [
        ("abc123", state_file, token_file, state_payload["state"])
    ]


def test_doctor_reports_missing_token_without_printing_secrets(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("X_CLIENT_ID", "client-id")
    monkeypatch.setenv("X_CLIENT_SECRET", "client-secret")
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    assert (
        qaz_x.doctor_command(token_file=tmp_path / "missing.json", json_output=True)
        == 1
    )

    payload = json.loads(capsys.readouterr().out)

    assert payload["ready_to_post"] is False
    assert payload["checks"]["client_id_env"] == "present"
    assert payload["checks"]["client_secret_env"] == "present"
    assert payload["checks"]["access_token"] == "missing"
    assert "oauth-diagnose" in payload["next_action"]
    assert "client-secret" not in json.dumps(payload)


def test_doctor_reports_ready_with_token_file(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    token_file = tmp_path / "tokens.json"
    token_file.write_text(json.dumps({"access_token": "file-token"}), encoding="utf-8")
    monkeypatch.setenv("X_CLIENT_ID", "client-id")
    monkeypatch.setenv("X_CLIENT_SECRET", "client-secret")
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    assert qaz_x.doctor_command(token_file=token_file, json_output=True) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["ready_to_post"] is True
    assert payload["checks"]["access_token"] == "present"


def test_doctor_cli_default_token_file_resolves_under_x_root(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    workspace = tmp_path / "x"
    (workspace / "content" / "posts").mkdir(parents=True)
    (workspace / ".state").mkdir()
    (workspace / "config.example.json").write_text(
        json.dumps(
            {
                "github_url": "https://github.com/qazedhq/qa-z",
                "max_post_chars": 260,
                "max_mentions_per_post": 1,
                "posting_enabled_env": "QA_Z_X_POST_ENABLE",
                "token_env": "X_USER_ACCESS_TOKEN",
                "token_file": ".state/x_tokens.json",
            }
        ),
        encoding="utf-8",
    )
    (workspace / "queue.json").write_text(
        json.dumps(
            {
                "posts": [
                    {
                        "id": "launch",
                        "file": "content/posts/launch.md",
                        "status": "approved",
                        "posted_id": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (workspace / "content" / "posts" / "launch.md").write_text(
        "# Launch\n\n## Post\n\nQA-Z launch https://github.com/qazedhq/qa-z\n",
        encoding="utf-8",
    )
    (workspace / ".state" / "x_tokens.json").write_text(
        json.dumps({"access_token": "file-token"}),
        encoding="utf-8",
    )
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    with mock.patch.object(qaz_x, "ROOT", workspace):
        assert qaz_x.main(["doctor", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["ready_to_post"] is True
    assert payload["checks"]["access_token"] == "present"
    assert payload["token_file"] == str(workspace / ".state" / "x_tokens.json")


def test_oauth_diagnose_json_prints_app_settings_checklist_without_secrets(
    monkeypatch, capsys
) -> None:
    monkeypatch.setenv("X_CLIENT_ID", "client-id")
    monkeypatch.setenv("X_CLIENT_SECRET", "client-secret")

    assert (
        qaz_x.main(
            [
                "oauth-diagnose",
                "--redirect-uri",
                "http://127.0.0.1:8080/callback",
                "--json",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["status"] == "manual_x_developer_portal_check_required"
    assert payload["redirect_uri"] == "http://127.0.0.1:8080/callback"
    assert payload["local_redirect_uri_valid"] is True
    assert payload["credential_env"]["client_id"] == "present"
    assert payload["credential_env"]["client_secret"] == "present"
    assert payload["required_scopes"] == [
        "tweet.read",
        "tweet.write",
        "users.read",
        "offline.access",
    ]
    assert any("OAuth 2.0" in item for item in payload["developer_portal_checks"])
    assert any("Read and write" in item for item in payload["developer_portal_checks"])
    assert any(
        "http://127.0.0.1:8080/callback" in item
        for item in payload["developer_portal_checks"]
    )
    assert "client-secret" not in output


def test_oauth_diagnose_text_mentions_x_authorization_error(capsys) -> None:
    assert (
        qaz_x.oauth_diagnose_command(
            redirect_uri="http://127.0.0.1:8080/callback",
            json_output=False,
        )
        == 0
    )

    output = capsys.readouterr().out

    assert "OAUTH_APP_SETTINGS_CHECKLIST" in output
    assert "Something went wrong" in output
    assert "You were not able to give access to the App" in output
    assert "http://127.0.0.1:8080/callback" in output
    assert "python marketing/x/scripts/qaz_x.py login" in output


def test_run_approved_blocks_execute_without_token(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    with mock.patch.object(qaz_x, "post_command") as post_command:
        assert (
            qaz_x.run_approved_command(
                execute=True,
                token_file=tmp_path / "missing.json",
            )
            == 1
        )

    post_command.assert_not_called()


def test_run_approved_dry_run_calls_post_without_token(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    with mock.patch.object(qaz_x, "post_command", return_value=0) as post_command:
        assert (
            qaz_x.run_approved_command(
                execute=False,
                token_file=tmp_path / "missing.json",
            )
            == 0
        )

    post_command.assert_called_once_with(
        execute=False, token_file=tmp_path / "missing.json"
    )


def test_campaign_dry_run_validates_and_previews_without_token(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    def fake_post_command(execute: bool, token_file: Path | None = None) -> int:
        print("POST_PAYLOAD")
        return 0

    with mock.patch.object(
        qaz_x, "post_command", side_effect=fake_post_command
    ) as post_command:
        assert (
            qaz_x.campaign_command(
                execute=False,
                token_file=tmp_path / "missing.json",
                json_output=True,
            )
            == 0
        )

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["mode"] == "dry-run"
    assert payload["posted"] is False
    assert payload["ready_to_post"] is False
    assert payload["checks"]["access_token"] == "missing"
    assert output.lstrip().startswith("{")
    assert payload["captured_output"] == ["POST_PAYLOAD"]
    post_command.assert_called_once_with(
        execute=False, token_file=tmp_path / "missing.json"
    )


def test_campaign_execute_calls_run_approved_when_ready(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    token_file = tmp_path / "tokens.json"
    token_file.write_text(json.dumps({"access_token": "file-token"}), encoding="utf-8")
    monkeypatch.setenv("QA_Z_X_POST_ENABLE", "1")
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    with mock.patch.object(qaz_x, "run_approved_command", return_value=0) as runner:
        assert (
            qaz_x.campaign_command(
                execute=True,
                token_file=token_file,
                json_output=True,
            )
            == 0
        )

    payload = json.loads(capsys.readouterr().out)

    assert payload["mode"] == "execute"
    assert payload["posted"] is True
    assert payload["ready_to_post"] is True
    runner.assert_called_once_with(execute=True, token_file=token_file)


def test_campaign_execute_failure_reports_blocked_next_action(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    token_file = tmp_path / "tokens.json"
    token_file.write_text(json.dumps({"access_token": "file-token"}), encoding="utf-8")
    monkeypatch.setenv("QA_Z_X_POST_ENABLE", "1")
    monkeypatch.delenv("X_USER_ACCESS_TOKEN", raising=False)

    with mock.patch.object(qaz_x, "run_approved_command", return_value=1):
        assert (
            qaz_x.campaign_command(
                execute=True,
                token_file=token_file,
                json_output=True,
            )
            == 1
        )

    payload = json.loads(capsys.readouterr().out)

    assert payload["posted"] is False
    assert payload["command_exit"] == 1
    assert "POST_BLOCKED" in payload["next_action"]


def test_setup_env_prints_copyable_powershell_without_secret_values(capsys) -> None:
    assert qaz_x.setup_env_command(shell="powershell") == 0

    output = capsys.readouterr().out

    assert "$env:X_CLIENT_ID=" in output
    assert "$env:X_CLIENT_SECRET=" in output
    assert "$env:QA_Z_X_POST_ENABLE=" in output
    assert "python marketing/x/scripts/qaz_x.py login" in output
    assert "python marketing/x/scripts/qaz_x.py campaign --dry-run --json" in output
    assert "python marketing/x/scripts/qaz_x.py campaign --execute" in output
