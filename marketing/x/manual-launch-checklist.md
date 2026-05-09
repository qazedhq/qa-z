# Manual Launch Checklist

Complete these steps in the X UI and repository tools. Do not automate X actions.

## Profile

- [ ] Confirm the `@qazedhq` handle resolves to the QA-Z account.
- [ ] Upload the profile image.
- [ ] Upload the header or social preview image.
- [ ] Set the account name to `QA-Z 🛡️`.
- [ ] Set the bio.
- [ ] Set the website to [https://github.com/qazedhq/qa-z](https://github.com/qazedhq/qa-z).
- [ ] Set the location to `Open source`.

## Launch Setup

- [ ] Pick one pinned post option.
- [ ] Run `python marketing/x/scripts/x_post_dry_run.py marketing/x/pinned-post.md`.
- [ ] Copy the selected pinned post manually into X.
- [ ] Pin the selected post manually.
- [ ] Create the X lists from [lists/](lists/).
- [ ] Manually follow the initial accounts after reviewing each account.

## Day 0

- [ ] Run `python marketing/x/scripts/validate_x_posts.py`.
- [ ] Publish the Day 0 launch post manually.
- [ ] Add the post URL to [tracking/launch-log.md](tracking/launch-log.md).
- [ ] Record baseline metrics in
  [tracking/metrics-template.md](tracking/metrics-template.md).

## Launch Week

- [ ] Publish at most one planned launch-week post per day.
- [ ] Reply only when the reply is relevant and non-spammy.
- [ ] Track repeated questions.
- [ ] Collect questions for a future FAQ.
- [ ] Log demo or install failures without overstating adoption.
