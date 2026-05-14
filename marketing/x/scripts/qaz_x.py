#!/usr/bin/env python3
"""Safe X launch automation for QA-Z.

The default path is dry-run only. The script never follows, likes, reposts,
DMs, or auto-replies. Optional real posting requires explicit environment gates
and a user-context OAuth token.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import csv
import io
import hashlib
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
POST_URL = "https://api.x.com/2/tweets"

DEFAULT_SCOPES = ("tweet.read", "tweet.write", "users.read", "offline.access")
DEFAULT_CONFIG: dict[str, Any] = {
    "account": "qazedhq",
    "github_url": "https://github.com/qazedhq/qa-z",
    "release_url": "https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha",
    "max_post_chars": 260,
    "max_mentions_per_post": 1,
    "posting_enabled_env": "QA_Z_X_POST_ENABLE",
    "token_env": "X_USER_ACCESS_TOKEN",
    "client_id_env": "X_CLIENT_ID",
    "client_secret_env": "X_CLIENT_SECRET",
    "oauth_state_file": ".state/oauth-state.json",
    "token_file": ".state/x_tokens.json",
    "redirect_uri": "http://127.0.0.1:8080/callback",
    "scopes": list(DEFAULT_SCOPES),
}

FORBIDDEN_CLAIMS = (
    "pipx install qa-z",
    "pypi is live",
    "testpypi is live",
    "official marketplace action",
    "github marketplace action",
    "thousands of users",
    "10k stars",
    "30k stars",
)
QUEUE_STATUSES = {"draft", "approved", "posted"}
POST_HEADING = re.compile(r"^## Post\s*$", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class CandidatePost:
    path: Path
    text: str


@dataclass(frozen=True)
class OAuthAuthorization:
    url: str
    state_file: Path
    state: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def config_path() -> Path:
    return ROOT / "config.example.json"


def queue_path() -> Path:
    return ROOT / "queue.json"


def resolve_root_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def load_config() -> dict[str, Any]:
    if config_path().exists():
        data = json.loads(config_path().read_text(encoding="utf-8"))
        merged = DEFAULT_CONFIG.copy()
        merged.update(data)
        return merged
    return DEFAULT_CONFIG.copy()


def extract_post(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = POST_HEADING.search(text)
    if not match:
        return ""
    rest = text[match.end() :].strip()
    sections = re.split(r"\n##\s+", rest, maxsplit=1)
    return sections[0].strip()


def iter_markdown_files() -> Iterable[Path]:
    for subdir in ("content/posts", "content/replies"):
        directory = ROOT / subdir
        if directory.exists():
            yield from sorted(directory.glob("*.md"))
    for extra in ("README.md", "USAGE.md"):
        path = ROOT / extra
        if path.exists():
            yield path


def load_queue() -> dict[str, Any]:
    if not queue_path().exists():
        raise SystemExit(f"Missing queue file: {queue_path()}")
    return json.loads(queue_path().read_text(encoding="utf-8"))


def save_queue(queue: Mapping[str, Any]) -> None:
    queue_path().write_text(
        json.dumps(queue, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_queue(queue: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    seen_ids: set[str] = set()
    posts = queue.get("posts", [])
    if not isinstance(posts, list):
        return ["queue.json: posts must be a list"]

    for index, item in enumerate(posts):
        if not isinstance(item, dict):
            failures.append(f"queue.json: post #{index + 1} must be an object")
            continue

        post_id = str(item.get("id", "")).strip()
        if not post_id:
            failures.append(f"queue.json: post #{index + 1} is missing id")
        elif post_id in seen_ids:
            failures.append(f"queue.json: duplicate post id {post_id!r}")
        seen_ids.add(post_id)

        status = str(item.get("status", "")).strip()
        if status not in QUEUE_STATUSES:
            failures.append(
                f"queue.json: {post_id or index + 1} has invalid status {status!r}"
            )

        file_value = str(item.get("file", "")).strip()
        if not file_value:
            failures.append(f"queue.json: {post_id or index + 1} is missing file")
            continue
        post_path = resolve_root_path(file_value)
        if not post_path.exists():
            failures.append(
                f"queue.json: {post_id or index + 1} missing file {file_value}"
            )
            continue
        if status in {"approved", "posted"} and not extract_post(post_path):
            failures.append(f"queue.json: {post_id or index + 1} has no ## Post body")

        posted_id = item.get("posted_id")
        if status == "posted" and not posted_id:
            failures.append(f"queue.json: {post_id or index + 1} is posted without id")
    return failures


def validate(quiet: bool = False) -> int:
    config = load_config()
    max_chars = int(config["max_post_chars"])
    max_mentions = int(config["max_mentions_per_post"])
    failures: list[str] = []
    seen_posts: dict[str, Path] = {}

    if queue_path().exists():
        failures.extend(validate_queue(load_queue()))

    for path in iter_markdown_files():
        text = path.read_text(encoding="utf-8").lower()

        for claim in FORBIDDEN_CLAIMS:
            if claim in text:
                failures.append(f"{path}: forbidden or premature claim: {claim!r}")

        post = extract_post(path)
        if not post:
            continue

        if len(post) > max_chars:
            failures.append(f"{path}: post is {len(post)} chars; limit {max_chars}")
        mentions = re.findall(r"(?<![\w])@\w+", post)
        if len(mentions) > max_mentions:
            failures.append(
                f"{path}: too many mentions ({len(mentions)} > {max_mentions})"
            )
        normalized = re.sub(r"\s+", " ", post.strip().lower())
        if normalized in seen_posts:
            failures.append(
                f"{path}: duplicate post body also in {seen_posts[normalized]}"
            )
        else:
            seen_posts[normalized] = path

        if (
            path.name == "day-00-launch.md"
            and config["github_url"].lower() not in post.lower()
        ):
            failures.append(f"{path}: launch post must include GitHub link")

    if failures:
        if not quiet:
            print("VALIDATION_FAILED")
            for item in failures:
                print(f"- {item}")
        return 1

    if not quiet:
        print("VALIDATION_PASSED")
    return 0


def queue_status() -> int:
    queue = load_queue()
    for post in queue.get("posts", []):
        print(
            f"{post['id']}: {post['status']} "
            f"file={post['file']} posted_id={post.get('posted_id')}"
        )
    return 0


def next_post() -> CandidatePost | None:
    queue = load_queue()
    for post in queue.get("posts", []):
        if post.get("status") == "approved" and not post.get("posted_id"):
            path = resolve_root_path(post["file"])
            return CandidatePost(path=path, text=extract_post(path))
    return None


def print_next() -> int:
    post = next_post()
    if not post:
        print("No approved unposted post.")
        return 0
    print(f"NEXT={post.path}")
    print(post.text)
    return 0


def load_token_from_file(path: Path) -> str | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    token = payload.get("access_token")
    if not token:
        return None
    return str(token)


def access_token(
    config: Mapping[str, Any], token_file: Path | None = None
) -> str | None:
    token_env = str(config["token_env"])
    env_token = os.environ.get(token_env)
    if env_token:
        return env_token
    configured_token_file = (
        resolve_root_path(token_file)
        if token_file is not None
        else resolve_root_path(str(config["token_file"]))
    )
    return load_token_from_file(configured_token_file)


def post_to_x(text: str, token_file: Path | None = None) -> dict[str, Any]:
    config = load_config()
    enabled = os.environ.get(str(config["posting_enabled_env"])) == "1"
    token = access_token(config, token_file)

    if not enabled:
        raise RuntimeError(
            f"Real posting disabled. Set {config['posting_enabled_env']}=1"
        )
    if not token:
        raise RuntimeError(
            f"Missing {config['token_env']} or token file {config['token_file']}"
        )

    body = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        POST_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "qa-z-x-launch-kit",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"X API rejected post: HTTP {error.code}: {detail}"
        ) from error


def post_command(execute: bool, token_file: Path | None = None) -> int:
    candidate = next_post()
    if not candidate:
        print("No approved unposted post.")
        return 0

    print("POST_PAYLOAD")
    print(json.dumps({"text": candidate.text}, indent=2))

    if not execute:
        print("DRY_RUN_ONLY")
        return 0

    if validate() != 0:
        return 1

    try:
        result = post_to_x(candidate.text, token_file)
    except RuntimeError as error:
        print("POST_BLOCKED")
        print(str(error))
        return 1
    print("POSTED")
    print(json.dumps(redacted_payload(result), indent=2))

    queue = load_queue()
    for item in queue.get("posts", []):
        if resolve_root_path(item.get("file", "")) == candidate.path:
            item["posted_id"] = result.get("data", {}).get("id")
            item["posted_at"] = utc_now()
            item["status"] = "posted"
            break
    save_queue(queue)
    return 0


def follow_plan(limit: int) -> int:
    path = ROOT / "data/follow_targets.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows[:limit]:
        print(
            f"@{row['handle']} | {row['list']} | {row['why']} | "
            f"{row['manual_engagement_note']}"
        )
    print("Manual action only. This script does not follow accounts.")
    return 0


def reply_drafts(topic: str | None) -> int:
    path = ROOT / "content/replies/templates.md"
    text = path.read_text(encoding="utf-8")
    if not topic:
        print(text)
        return 0

    topic_lower = topic.lower()
    blocks = re.split(r"\n##\s+", text)
    for block in blocks:
        if topic_lower in block.lower():
            print("## " + block.strip())
            return 0
    print(f"No matching topic found for {topic!r}. Showing all templates.\n")
    print(text)
    return 0


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def code_challenge(verifier: str) -> str:
    return base64url(hashlib.sha256(verifier.encode("ascii")).digest())


def create_oauth_authorization(
    redirect_uri: str,
    state_file: Path,
    scopes: Sequence[str] = DEFAULT_SCOPES,
) -> OAuthAuthorization:
    config = load_config()
    client_id = require_env(str(config["client_id_env"]))
    verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(32)
    challenge = code_challenge(verifier)
    resolved_state_file = resolve_root_path(state_file)
    resolved_state_file.parent.mkdir(parents=True, exist_ok=True)
    resolved_state_file.write_text(
        json.dumps(
            {
                "created_at": utc_now(),
                "redirect_uri": redirect_uri,
                "scopes": list(scopes),
                "state": state,
                "code_verifier": verifier,
                "code_challenge_method": "S256",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        quote_via=urllib.parse.quote,
    )
    return OAuthAuthorization(
        url=f"{AUTHORIZATION_URL}?{params}",
        state_file=resolved_state_file,
        state=state,
    )


def auth_url_command(
    redirect_uri: str,
    state_file: Path,
    scopes: Sequence[str] = DEFAULT_SCOPES,
) -> int:
    authorization = create_oauth_authorization(redirect_uri, state_file, scopes)
    print(f"AUTHORIZATION_URL={authorization.url}")
    print(f"STATE_FILE={authorization.state_file}")
    print(
        "Open the URL, approve the app, then run exchange-code with the returned code."
    )
    return 0


def parse_local_http_redirect(redirect_uri: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(redirect_uri)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port is None
    ):
        raise RuntimeError(
            "login requires a local HTTP redirect URI such as "
            "http://127.0.0.1:8080/callback"
        )
    return parsed


def is_local_http_redirect(redirect_uri: str) -> bool:
    try:
        parse_local_http_redirect(redirect_uri)
    except RuntimeError:
        return False
    return True


def oauth_diagnostics_payload(redirect_uri: str) -> dict[str, Any]:
    config = load_config()
    client_id_env = str(config["client_id_env"])
    client_secret_env = str(config["client_secret_env"])
    scopes = [str(scope) for scope in config.get("scopes", DEFAULT_SCOPES)]
    return {
        "status": "manual_x_developer_portal_check_required",
        "symptom": (
            "X may show: Something went wrong / "
            "You were not able to give access to the App."
        ),
        "redirect_uri": redirect_uri,
        "local_redirect_uri_valid": is_local_http_redirect(redirect_uri),
        "credential_env": {
            "client_id": "present" if os.environ.get(client_id_env) else "missing",
            "client_secret": (
                "present" if os.environ.get(client_secret_env) else "missing"
            ),
        },
        "required_scopes": scopes,
        "developer_portal_checks": [
            "Enable OAuth 2.0 in User authentication settings.",
            "Set App permissions to Read and write.",
            (
                "Use Web App, Automated App or Bot for confidential-client "
                "OAuth when X_CLIENT_SECRET is set."
            ),
            f"Callback / Redirect URL must exactly match: {redirect_uri}",
            "Set Website URL to a valid project or product URL.",
            "Save the app settings before retrying login.",
        ],
        "retry_command": (
            f'python marketing/x/scripts/qaz_x.py login --redirect-uri "{redirect_uri}"'
        ),
    }


def oauth_diagnose_command(redirect_uri: str, json_output: bool = False) -> int:
    payload = oauth_diagnostics_payload(redirect_uri)
    if json_output:
        print(json.dumps(payload, indent=2))
        return 0

    print("OAUTH_APP_SETTINGS_CHECKLIST")
    print(payload["symptom"])
    print(f"REDIRECT_URI={payload['redirect_uri']}")
    print(f"LOCAL_REDIRECT_URI_VALID={payload['local_redirect_uri_valid']}")
    print("CREDENTIAL_ENV")
    for key, value in payload["credential_env"].items():
        print(f"- {key}: {value}")
    print("REQUIRED_SCOPES")
    for scope in payload["required_scopes"]:
        print(f"- {scope}")
    print("DEVELOPER_PORTAL_CHECKS")
    for item in payload["developer_portal_checks"]:
        print(f"- {item}")
    print(f"RETRY={payload['retry_command']}")
    return 0


def wait_for_oauth_callback(
    redirect_uri: str,
    timeout_seconds: float,
) -> tuple[str, str | None]:
    parsed = parse_local_http_redirect(redirect_uri)
    result: dict[str, str] = {}

    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            request = urllib.parse.urlparse(self.path)
            if request.path != parsed.path:
                self.send_response(404)
                self.end_headers()
                return

            query = urllib.parse.parse_qs(request.query)
            if "error" in query:
                result["error"] = query["error"][0]
            elif "code" in query:
                result["code"] = query["code"][0]
                if "state" in query:
                    result["state"] = query["state"][0]
            else:
                result["error"] = "missing code"

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"QA-Z X authorization captured. You can close this tab.")

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = HTTPServer((str(parsed.hostname), int(parsed.port)), OAuthCallbackHandler)
    try:
        deadline = time.monotonic() + timeout_seconds
        while "code" not in result and "error" not in result:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Timed out waiting for X OAuth callback")
            server.timeout = min(0.2, remaining)
            server.handle_request()
    finally:
        server.server_close()

    if "error" in result:
        raise RuntimeError(f"X OAuth authorization failed: {result['error']}")
    return result["code"], result.get("state")


def basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def token_request(
    form: Mapping[str, str],
    client_id: str,
    client_secret: str | None,
) -> dict[str, Any]:
    body = dict(form)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "qa-z-x-launch-kit",
    }
    if client_secret:
        headers["Authorization"] = basic_auth_header(client_id, client_secret)
    else:
        body["client_id"] = client_id

    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"X OAuth token request failed: HTTP {error.code}: {detail}"
        ) from error


def redacted_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if key in {"access_token", "refresh_token", "id_token"}:
            redacted[key] = "<redacted>"
        elif isinstance(value, dict):
            redacted[key] = redacted_payload(value)
        else:
            redacted[key] = value
    return redacted


def write_token_file(token_file: Path, payload: Mapping[str, Any]) -> None:
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def exchange_code_command(
    code: str,
    state_file: Path,
    token_file: Path,
    returned_state: str | None = None,
) -> int:
    config = load_config()
    client_id = require_env(str(config["client_id_env"]))
    client_secret = os.environ.get(str(config["client_secret_env"]))
    resolved_state_file = resolve_root_path(state_file)
    state_payload = json.loads(resolved_state_file.read_text(encoding="utf-8"))
    if returned_state and returned_state != state_payload.get("state"):
        raise RuntimeError("Returned state does not match saved OAuth state")

    token_payload = token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": str(state_payload["redirect_uri"]),
            "code_verifier": str(state_payload["code_verifier"]),
        },
        client_id=client_id,
        client_secret=client_secret,
    )
    token_payload["obtained_at"] = utc_now()
    token_payload["scopes"] = state_payload.get("scopes", [])
    resolved_token_file = resolve_root_path(token_file)
    write_token_file(resolved_token_file, token_payload)
    print(f"TOKEN_SAVED={resolved_token_file}")
    print(json.dumps(redacted_payload(token_payload), indent=2))
    return 0


def refresh_token_command(refresh_token: str | None, token_file: Path) -> int:
    config = load_config()
    client_id = require_env(str(config["client_id_env"]))
    client_secret = os.environ.get(str(config["client_secret_env"]))
    resolved_token_file = resolve_root_path(token_file)
    existing_payload: dict[str, Any] = {}
    if resolved_token_file.exists():
        existing_payload = json.loads(resolved_token_file.read_text(encoding="utf-8"))
    token = refresh_token or existing_payload.get("refresh_token")
    if not token:
        raise RuntimeError("Missing refresh token")

    new_payload = token_request(
        {"grant_type": "refresh_token", "refresh_token": str(token)},
        client_id=client_id,
        client_secret=client_secret,
    )
    if "refresh_token" not in new_payload and "refresh_token" in existing_payload:
        new_payload["refresh_token"] = existing_payload["refresh_token"]
    new_payload["refreshed_at"] = utc_now()
    write_token_file(resolved_token_file, new_payload)
    print(f"TOKEN_REFRESHED={resolved_token_file}")
    print(json.dumps(redacted_payload(new_payload), indent=2))
    return 0


def login_command(
    redirect_uri: str,
    state_file: Path,
    token_file: Path,
    scopes: Sequence[str] = DEFAULT_SCOPES,
    open_browser: bool = True,
    timeout_seconds: float = 300,
) -> int:
    parse_local_http_redirect(redirect_uri)
    authorization = create_oauth_authorization(redirect_uri, state_file, scopes)
    print(f"AUTHORIZATION_URL={authorization.url}")
    print(f"STATE_FILE={authorization.state_file}")
    print(f"WAITING_FOR_CALLBACK={redirect_uri}")
    if open_browser:
        webbrowser.open(authorization.url)
    try:
        code, returned_state = wait_for_oauth_callback(redirect_uri, timeout_seconds)
    except RuntimeError as error:
        print("LOGIN_BLOCKED")
        print(str(error))
        print(
            "Run "
            f'`python marketing/x/scripts/qaz_x.py oauth-diagnose --redirect-uri "{redirect_uri}"` '
            "if the X page says Something went wrong."
        )
        raise
    return exchange_code_command(
        code, authorization.state_file, token_file, returned_state
    )


def readiness_next_action(checks: Mapping[str, str]) -> str:
    if checks["content_validation"] != "passed":
        return "Fix validation failures from `python marketing/x/scripts/qaz_x.py validate`."
    if checks["access_token"] != "present":
        return (
            "Run `python marketing/x/scripts/qaz_x.py login` to create a local "
            "token file. If X says Something went wrong, run "
            "`python marketing/x/scripts/qaz_x.py oauth-diagnose`."
        )
    if checks["approved_unposted_post"] != "present":
        return "Approve a draft post in queue.json before posting."
    if checks["posting_enable_env"] != "enabled":
        return "Review dry-run output, then set QA_Z_X_POST_ENABLE=1 before execute."
    return "Run `python marketing/x/scripts/qaz_x.py run-approved --execute`."


def readiness_payload(token_file: Path | None = None) -> dict[str, Any]:
    config = load_config()
    resolved_token_file = (
        resolve_root_path(token_file)
        if token_file is not None
        else resolve_root_path(str(config["token_file"]))
    )
    has_token = access_token(config, resolved_token_file) is not None
    has_next_post = next_post() is not None
    validation_exit = validate(quiet=True)
    checks = {
        "content_validation": "passed" if validation_exit == 0 else "failed",
        "client_id_env": (
            "present" if os.environ.get(str(config["client_id_env"])) else "missing"
        ),
        "client_secret_env": (
            "present" if os.environ.get(str(config["client_secret_env"])) else "missing"
        ),
        "access_token": "present" if has_token else "missing",
        "posting_enable_env": (
            "enabled"
            if os.environ.get(str(config["posting_enabled_env"])) == "1"
            else "disabled"
        ),
        "approved_unposted_post": "present" if has_next_post else "missing",
    }
    return {
        "ready_to_post": validation_exit == 0 and has_token and has_next_post,
        "execute_enabled": os.environ.get(str(config["posting_enabled_env"])) == "1",
        "token_file": str(resolved_token_file),
        "checks": checks,
        "next_action": readiness_next_action(checks),
    }


def doctor_command(token_file: Path | None = None, json_output: bool = False) -> int:
    payload = readiness_payload(token_file)
    if json_output:
        print(json.dumps(payload, indent=2))
    else:
        print(f"READY_TO_POST={payload['ready_to_post']}")
        for key, value in payload["checks"].items():
            print(f"{key}={value}")
        print(f"NEXT_ACTION={payload['next_action']}")
    return 0 if payload["ready_to_post"] else 1


def run_approved_command(execute: bool, token_file: Path | None = None) -> int:
    if execute:
        payload = readiness_payload(token_file)
        if not payload["ready_to_post"]:
            print("RUN_BLOCKED")
            print(f"NEXT_ACTION={payload['next_action']}")
            return 1
    return post_command(execute=execute, token_file=token_file)


def campaign_command(
    execute: bool,
    token_file: Path | None = None,
    json_output: bool = False,
) -> int:
    payload = readiness_payload(token_file)
    mode = "execute" if execute else "dry-run"
    output_buffer = io.StringIO()
    output_context = (
        contextlib.redirect_stdout(output_buffer)
        if json_output
        else contextlib.nullcontext()
    )
    with output_context:
        if execute:
            command_exit = run_approved_command(execute=True, token_file=token_file)
            posted = command_exit == 0 and payload["ready_to_post"]
        else:
            command_exit = post_command(execute=False, token_file=token_file)
            posted = False

    result = {
        "mode": mode,
        "posted": posted,
        "command_exit": command_exit,
        "ready_to_post": payload["ready_to_post"],
        "checks": payload["checks"],
        "next_action": payload["next_action"],
    }
    if execute and command_exit != 0:
        result["next_action"] = (
            "Resolve the POST_BLOCKED API error, then retry execute."
        )
    if json_output:
        captured_output = output_buffer.getvalue().splitlines()
        if captured_output:
            result["captured_output"] = captured_output
        print(json.dumps(result, indent=2))
    else:
        print(f"CAMPAIGN_MODE={mode}")
        print(f"READY_TO_POST={result['ready_to_post']}")
        print(f"POSTED={posted}")
        print(f"NEXT_ACTION={result['next_action']}")
    return command_exit


def setup_env_command(shell: str = "powershell") -> int:
    if shell != "powershell":
        raise RuntimeError("Only powershell setup output is supported on this repo.")

    print("# Paste values into this PowerShell session. Do not commit them.")
    print('$env:X_CLIENT_ID="<paste X OAuth2 client id>"')
    print('$env:X_CLIENT_SECRET="<paste X OAuth2 client secret>"')
    print(
        'python marketing/x/scripts/qaz_x.py login --redirect-uri "http://127.0.0.1:8080/callback"'
    )
    print("python marketing/x/scripts/qaz_x.py campaign --dry-run --json")
    print('$env:QA_Z_X_POST_ENABLE="1"')
    print("python marketing/x/scripts/qaz_x.py campaign --execute")
    return 0


def default_path_from_config(key: str) -> Path:
    config = load_config()
    return Path(str(config[key]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe QA-Z X launch automation")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")
    sub.add_parser("queue")
    sub.add_parser("next")

    setup_parser = sub.add_parser("setup-env")
    setup_parser.add_argument("--shell", default="powershell")

    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument(
        "--token-file", type=Path, default=default_path_from_config("token_file")
    )
    doctor_parser.add_argument("--json", action="store_true")

    oauth_diagnose_parser = sub.add_parser("oauth-diagnose")
    oauth_diagnose_parser.add_argument(
        "--redirect-uri", default=str(load_config()["redirect_uri"])
    )
    oauth_diagnose_parser.add_argument("--json", action="store_true")

    auth_parser = sub.add_parser("auth-url")
    auth_parser.add_argument(
        "--redirect-uri", default=str(load_config()["redirect_uri"])
    )
    auth_parser.add_argument(
        "--state-file", type=Path, default=default_path_from_config("oauth_state_file")
    )
    auth_parser.add_argument("--scope", dest="scopes", action="append")

    login_parser = sub.add_parser("login")
    login_parser.add_argument(
        "--redirect-uri", default=str(load_config()["redirect_uri"])
    )
    login_parser.add_argument(
        "--state-file", type=Path, default=default_path_from_config("oauth_state_file")
    )
    login_parser.add_argument(
        "--token-file", type=Path, default=default_path_from_config("token_file")
    )
    login_parser.add_argument("--scope", dest="scopes", action="append")
    login_parser.add_argument("--timeout", type=float, default=300)
    login_parser.add_argument("--no-open-browser", action="store_true")

    exchange_parser = sub.add_parser("exchange-code")
    exchange_parser.add_argument("--code", required=True)
    exchange_parser.add_argument("--state")
    exchange_parser.add_argument(
        "--state-file", type=Path, default=default_path_from_config("oauth_state_file")
    )
    exchange_parser.add_argument(
        "--token-file", type=Path, default=default_path_from_config("token_file")
    )

    refresh_parser = sub.add_parser("refresh-token")
    refresh_parser.add_argument("--refresh-token")
    refresh_parser.add_argument(
        "--token-file", type=Path, default=default_path_from_config("token_file")
    )

    post_parser = sub.add_parser("post")
    mode = post_parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    post_parser.add_argument("--token-file", type=Path)

    run_parser = sub.add_parser("run-approved")
    run_mode = run_parser.add_mutually_exclusive_group()
    run_mode.add_argument("--dry-run", action="store_true")
    run_mode.add_argument("--execute", action="store_true")
    run_parser.add_argument("--token-file", type=Path)

    campaign_parser = sub.add_parser("campaign")
    campaign_mode = campaign_parser.add_mutually_exclusive_group()
    campaign_mode.add_argument("--dry-run", action="store_true")
    campaign_mode.add_argument("--execute", action="store_true")
    campaign_parser.add_argument("--token-file", type=Path)
    campaign_parser.add_argument("--json", action="store_true")

    follow_parser = sub.add_parser("follow-plan")
    follow_parser.add_argument("--limit", type=int, default=30)

    reply_parser = sub.add_parser("reply-drafts")
    reply_parser.add_argument("--topic")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        return validate()
    if args.command == "queue":
        return queue_status()
    if args.command == "next":
        return print_next()
    if args.command == "setup-env":
        return setup_env_command(shell=args.shell)
    if args.command == "doctor":
        return doctor_command(token_file=args.token_file, json_output=bool(args.json))
    if args.command == "oauth-diagnose":
        return oauth_diagnose_command(args.redirect_uri, json_output=bool(args.json))
    if args.command == "auth-url":
        scopes = tuple(args.scopes) if args.scopes else tuple(load_config()["scopes"])
        return auth_url_command(args.redirect_uri, args.state_file, scopes)
    if args.command == "login":
        scopes = tuple(args.scopes) if args.scopes else tuple(load_config()["scopes"])
        return login_command(
            redirect_uri=args.redirect_uri,
            state_file=args.state_file,
            token_file=args.token_file,
            scopes=scopes,
            open_browser=not args.no_open_browser,
            timeout_seconds=args.timeout,
        )
    if args.command == "exchange-code":
        return exchange_code_command(
            args.code, args.state_file, args.token_file, args.state
        )
    if args.command == "refresh-token":
        return refresh_token_command(args.refresh_token, args.token_file)
    if args.command == "post":
        return post_command(execute=bool(args.execute), token_file=args.token_file)
    if args.command == "run-approved":
        return run_approved_command(
            execute=bool(args.execute), token_file=args.token_file
        )
    if args.command == "campaign":
        return campaign_command(
            execute=bool(args.execute),
            token_file=args.token_file,
            json_output=bool(args.json),
        )
    if args.command == "follow-plan":
        return follow_plan(args.limit)
    if args.command == "reply-drafts":
        return reply_drafts(args.topic)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
