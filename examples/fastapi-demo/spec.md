# Spec

Invoice reads return `200` for the owner or an admin.

Invoice reads return `403` for a non-owner member.

The QA loop should leave JSON and Markdown artifacts that can be reviewed or converted into a repair prompt.
