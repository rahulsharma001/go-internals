"""Unit tests for schema-safe ordering, branches, assets, and classification."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from classifier import classify
from import_chatgpt import conversation_paths, render_extract, safe_name


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


if __name__ == "__main__":
    unittest.main()
