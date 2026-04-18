"""Tests for structured diff parsing."""

from __future__ import annotations

from qa_z.diffing.parser import parse_unified_diff


def test_parse_added_modified_deleted_and_renamed_files() -> None:
    diff = """\
diff --git a/src/qa_z/cli.py b/src/qa_z/cli.py
index 1111111..2222222 100644
--- a/src/qa_z/cli.py
+++ b/src/qa_z/cli.py
@@ -1 +1,2 @@
-old
+new
diff --git a/tests/test_old.py b/tests/test_old.py
deleted file mode 100644
--- a/tests/test_old.py
+++ /dev/null
@@ -1 +0,0 @@
-old test
diff --git a/docs/old.md b/docs/new.md
similarity index 90%
rename from docs/old.md
rename to docs/new.md
--- a/docs/old.md
+++ b/docs/new.md
@@ -1 +1 @@
-old
+new
diff --git a/src/qa_z/new_file.py b/src/qa_z/new_file.py
new file mode 100644
--- /dev/null
+++ b/src/qa_z/new_file.py
@@ -0,0 +1 @@
+created
"""

    change_set = parse_unified_diff(diff)

    assert change_set is not None
    assert change_set.source == "cli_diff"
    assert [
        (
            changed.path,
            changed.old_path,
            changed.status,
            changed.additions,
            changed.deletions,
            changed.language,
            changed.kind,
        )
        for changed in change_set.files
    ] == [
        ("src/qa_z/cli.py", "src/qa_z/cli.py", "modified", 1, 1, "python", "source"),
        ("tests/test_old.py", "tests/test_old.py", "deleted", 0, 1, "python", "test"),
        ("docs/new.md", "docs/old.md", "renamed", 1, 1, "markdown", "docs"),
        ("src/qa_z/new_file.py", None, "added", 1, 0, "python", "source"),
    ]


def test_parse_malformed_diff_returns_none() -> None:
    assert parse_unified_diff("this is not a unified diff") is None


def test_parse_typescript_source_test_and_config_files() -> None:
    diff = """\
diff --git a/src/app/widget.ts b/src/app/widget.ts
index 1111111..2222222 100644
--- a/src/app/widget.ts
+++ b/src/app/widget.ts
@@ -1 +1,2 @@
 old
+new
diff --git a/src/app/widget.test.tsx b/src/app/widget.test.tsx
index 1111111..2222222 100644
--- a/src/app/widget.test.tsx
+++ b/src/app/widget.test.tsx
@@ -1 +1,2 @@
 old
+new
diff --git a/tsconfig.json b/tsconfig.json
index 1111111..2222222 100644
--- a/tsconfig.json
+++ b/tsconfig.json
@@ -1 +1,2 @@
 {}
+{"compilerOptions": {"noEmit": true}}
diff --git a/vitest.config.ts b/vitest.config.ts
index 1111111..2222222 100644
--- a/vitest.config.ts
+++ b/vitest.config.ts
@@ -1 +1,2 @@
 export default {}
+export const test = {}
"""

    change_set = parse_unified_diff(diff)

    assert change_set is not None
    assert [
        (changed.path, changed.language, changed.kind) for changed in change_set.files
    ] == [
        ("src/app/widget.ts", "typescript", "source"),
        ("src/app/widget.test.tsx", "typescript", "test"),
        ("tsconfig.json", "json", "config"),
        ("vitest.config.ts", "typescript", "config"),
    ]
