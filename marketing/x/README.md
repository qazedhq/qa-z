# QA-Z X Launch Kit

This directory contains the manual launch operations kit for the QA-Z X account:
[https://x.com/qazedhq](https://x.com/qazedhq).

QA-Z positioning: **QA-Z 🛡️ - Make AI coding safe to merge.**

Actual posting, following, list creation, pinning, replying, and profile updates
must be done manually in the X UI by a human operator. The scripts in this
directory only validate markdown and print dry-run payloads. They do not log in,
call the X API, post, follow, like, reply, DM, or store credentials.

## Directory Map

- [account-profile.md](account-profile.md) - profile copy, visual guidance, and
  brand-account strategy.
- [bio-options.md](bio-options.md) - short bio variants, with the top three
  marked.
- [pinned-post.md](pinned-post.md) - three candidate pinned posts.
- [launch-thread.md](launch-thread.md) - short and long launch thread drafts.
- [posting-rules.md](posting-rules.md) - QA-Z-specific safe behavior rules.
- [manual-launch-checklist.md](manual-launch-checklist.md) - human launch steps.
- [posts/](posts/) - Day 0 through Day 6 launch-week posts.
- [replies/](replies/) - non-spammy reply templates by conversation type.
- [lists/](lists/) - suggested X lists and initial accounts to follow manually.
- [tracking/](tracking/) - metrics template and launch log.
- [scripts/](scripts/) - local validation and dry-run helpers.

## Safety Rules

- Do not request, print, store, or use X API tokens.
- Do not post to X from repository automation.
- Do not auto-follow, auto-like, auto-reply, auto-DM, or mass-mention anyone.
- Do not duplicate posts or replies.
- Do not ask people to star QA-Z repeatedly.
- Do not claim PyPI, TestPyPI, package-registry, or GitHub Marketplace
  availability.
- Do not invent adoption numbers, stars, users, companies, quotes, or
  testimonials.
- Keep every public claim tied to the repository, the alpha release, checked-in
  demo assets, or observable QA-Z behavior.

## Local Checks

Run these before copying any text into X:

```bash
python marketing/x/scripts/validate_x_posts.py
python marketing/x/scripts/x_post_dry_run.py marketing/x/pinned-post.md
```

The dry-run script prints candidate payloads only. It intentionally refuses to
post, even when `--post` is passed.
