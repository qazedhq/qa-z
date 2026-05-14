# QA-Z X Safe Automation

This folder contains repo-owned launch operations for X.

It automates only the safe parts:

- validate post copy before publishing
- inspect the approved posting queue
- dry-run the next payload
- publish the next approved post through `POST /2/tweets`
- generate manual follow and reply worklists
- help create and refresh OAuth 2.0 PKCE user tokens

It intentionally does not automate follows, likes, reposts, DMs, unsolicited replies, random mentions, or repeated engagement comments.

## Quick Start

```powershell
python marketing/x/scripts/qaz_x.py validate
python marketing/x/scripts/qaz_x.py doctor
python marketing/x/scripts/qaz_x.py queue
python marketing/x/scripts/qaz_x.py next
python marketing/x/scripts/qaz_x.py campaign --dry-run
python marketing/x/scripts/qaz_x.py follow-plan --limit 30
python marketing/x/scripts/qaz_x.py reply-drafts --topic ai-coding-agents
```

## OAuth Setup

Use environment variables for credentials. Do not write client secrets or tokens
to tracked files.

Generate the copy-paste operator script:

```powershell
python marketing/x/scripts/qaz_x.py setup-env
```

Then paste your values into the printed environment variable commands.

```powershell
$env:X_CLIENT_ID="<your X OAuth2 client id>"
$env:X_CLIENT_SECRET="<your X OAuth2 client secret>"
python marketing/x/scripts/qaz_x.py oauth-diagnose --redirect-uri "http://127.0.0.1:8080/callback"
python marketing/x/scripts/qaz_x.py login --redirect-uri "http://127.0.0.1:8080/callback"
```

`login` opens the authorization URL, waits for the localhost callback, exchanges
the returned code, and writes the token file. If browser launch is blocked, use
the manual two-step flow:

```powershell
python marketing/x/scripts/qaz_x.py auth-url --redirect-uri "http://127.0.0.1:8080/callback"
python marketing/x/scripts/qaz_x.py exchange-code --code "<code from redirect>"
```

The token file is written under `marketing/x/.state/`, which is ignored by git.

### X Developer Portal Checklist

If X shows `Something went wrong` or `You were not able to give access to the
App`, the authorization page failed before QA-Z could receive a callback. Check
the X Developer Portal app settings, then retry `login`.

```powershell
python marketing/x/scripts/qaz_x.py oauth-diagnose --redirect-uri "http://127.0.0.1:8080/callback"
```

Required settings for this kit:

- OAuth 2.0 enabled in User authentication settings
- App permissions set to Read and write
- Callback / Redirect URL exactly set to `http://127.0.0.1:8080/callback`
- Website URL set to a valid project or product URL
- Scopes available for the app: `tweet.read`, `tweet.write`, `users.read`,
  `offline.access`

## Real Posting

Dry-run is the default. Real posting requires an explicit enable flag and either
`X_USER_ACCESS_TOKEN` or a local token file created by `exchange-code`.

```powershell
$env:QA_Z_X_POST_ENABLE="1"
python marketing/x/scripts/qaz_x.py campaign --execute
```

After a successful post, `queue.json` records the returned post id and marks the
queued item as `posted`.

`campaign --execute` refuses to call the network unless `doctor` can see a valid
approved post and a user access token.

## Manual Engagement

```powershell
python marketing/x/scripts/qaz_x.py follow-plan --limit 30
python marketing/x/scripts/qaz_x.py reply-drafts --topic semgrep
```

These commands only print worklists and drafts for manual use.
