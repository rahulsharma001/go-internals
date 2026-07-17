"""Unit tests for schema-safe ordering, branches, assets, and classification."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from classifier import classify
from import_chatgpt import conversation_paths, render_extract, safe_name, sanitize_export_text


class ImporterTests(unittest.TestCase):
    def test_primary_lineage_and_alternative_branch(self) -> None:
        record = {
            "current_node": "answer-b",
            "mapping": {
                "root": {"id": "root", "parent": None, "message": None},
                "question": {"id": "question", "parent": "root", "message": None},
                "answer-a": {"id": "answer-a", "parent": "question", "message": None},
                "answer-b": {"id": "answer-b", "parent": "question", "message": None},
            },
        }
        primary, branches, errors = conversation_paths(record)
        self.assertEqual(primary, ["root", "question", "answer-b"])
        self.assertEqual(branches, [("answer-a", ["answer-a"], "question")])
        self.assertEqual(errors, [])

    def test_content_not_title_drives_definitive_classification(self) -> None:
        result = classify("Go Backend Interview", "Please rewrite this room confirmation message.")
        self.assertNotEqual(result.disposition, "engineering-relevant")
        result = classify("New chat", "```go\npackage main\nfunc main() {}\n```\nExplain goroutines and channels.")
        self.assertEqual(result.disposition, "engineering-relevant")

    def test_non_engineering_is_excluded(self) -> None:
        result = classify("Migraine treatment", "What medicine and dosage should I ask my doctor about for pain?")
        self.assertEqual(result.disposition, "excluded-non-engineering")

    def test_safe_filename_is_stable(self) -> None:
        self.assertEqual(safe_name("Go: Slices/Maps?", "2026-01-02T00:00:00Z", "abcdef123"), "2026-01-02 - Go- Slices-Maps - abcdef12.md")

    def test_source_extracts_redact_credentials(self) -> None:
        source = (
            "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE "
            "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
            "Password: eightchars\n"
            "postgresql://user:actual-password@db.example.invalid/app"
        )
        sanitized = sanitize_export_text(source)
        self.assertIn("[REDACTED_AWS_ACCESS_KEY_ID]", sanitized)
        self.assertIn("[REDACTED_AWS_SECRET_ACCESS_KEY]", sanitized)
        self.assertIn("Password: [REDACTED_CREDENTIAL]", sanitized)
        self.assertIn("postgresql://[REDACTED_CREDENTIALS]@db.example.invalid/app", sanitized)
        self.assertNotIn("eightchars", sanitized)
        self.assertNotIn("actual-password", sanitized)

    def test_source_redaction_preserves_placeholders_and_variables(self) -> None:
        source = "AWS_SECRET_ACCESS_KEY=mockSecret\n$password = Helper::make($password);"
        self.assertEqual(sanitize_export_text(source), source)


if __name__ == "__main__":
    unittest.main()
