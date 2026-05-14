# X Launch Usage

Recommended daily loop:

```powershell
python marketing/x/scripts/qaz_x.py validate
python marketing/x/scripts/qaz_x.py doctor
python marketing/x/scripts/qaz_x.py next
python marketing/x/scripts/qaz_x.py campaign --dry-run
python marketing/x/scripts/qaz_x.py follow-plan --limit 30
```

Use `post --execute` only after reviewing the dry-run payload.

One-time token setup:

```powershell
python marketing/x/scripts/qaz_x.py setup-env
$env:X_CLIENT_ID="<your X OAuth2 client id>"
$env:X_CLIENT_SECRET="<your X OAuth2 client secret>"
python marketing/x/scripts/qaz_x.py oauth-diagnose --redirect-uri "http://127.0.0.1:8080/callback"
python marketing/x/scripts/qaz_x.py login --redirect-uri "http://127.0.0.1:8080/callback"
```

If the X authorization page says `Something went wrong` or `You were not able to
give access to the App`, update the X Developer Portal app settings so OAuth 2.0
is enabled, app permissions are Read and write, and the callback URL exactly
matches `http://127.0.0.1:8080/callback`.

Actual posting:

```powershell
$env:QA_Z_X_POST_ENABLE="1"
python marketing/x/scripts/qaz_x.py campaign --execute
```

Blocked or excluded automation:

- auto follow
- auto like
- auto repost
- auto DM
- auto reply
- random mention campaigns
- duplicate promotional replies
