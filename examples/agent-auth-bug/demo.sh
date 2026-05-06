#!/usr/bin/env sh
set -eu

qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z guard --title "AI auth bug caught by QA-Z" --slug ai-auth-bug --deep auto
