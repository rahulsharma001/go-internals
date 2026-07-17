#!/usr/bin/env python3
"""End-to-end validation for source safety, completeness, and idempotence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from import_chatgpt import EXPECTED


REPORTS = [
    "CHATGPT_EXPORT_SCHEMA_REPORT.md",
    "CHATGPT_IMPORT_MANIFEST.md",
    "CHATGPT_MIGRATION_PLAN.md",
    "CHATGPT_IMPORT_REVIEW_QUEUE.md",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_hashes(vault: Path) -> dict[str, str]:
    paths = [
        vault / "01 Inbox" / "ChatGPT Export" / "classification_index.json",
        vault / "01 Inbox" / "ChatGPT Export" / "import_manifest.json",
        *(vault / name for name in REPORTS),
        *(sorted((vault / "01 Inbox" / "ChatGPT Export" / "Extracted").glob("*.md"))),
    ]
    return {str(path.relative_to(vault)): digest(path) for path in paths}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--vault", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    vault = args.vault.resolve()
    tool = vault / "tools" / "chatgpt_import"

    source_before = {name: digest(source / name) for name in EXPECTED}
    before = output_hashes(vault)
    subprocess.run([sys.executable, str(tool / "import_chatgpt.py"), "--source", str(source), "--vault", str(vault)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(tool / "generate_reports.py"), "--vault", str(vault)], check=True)
    source_after = {name: digest(source / name) for name in EXPECTED}
    after = output_hashes(vault)

    failures: list[str] = []
    if source_before != source_after:
        failures.append("one or more source JSON files changed")
    if before != after:
        changed = sorted(set(before) ^ set(after) | {name for name in set(before) & set(after) if before[name] != after[name]})
        failures.append(f"outputs are not byte-idempotent: {changed}")

    manifest = json.loads((vault / "01 Inbox" / "ChatGPT Export" / "import_manifest.json").read_text(encoding="utf-8"))
    index = json.loads((vault / "01 Inbox" / "ChatGPT Export" / "classification_index.json").read_text(encoding="utf-8"))
    records = index["records"]
    ids = [record["conversation_id"] for record in records]
    extracts = list((vault / "01 Inbox" / "ChatGPT Export" / "Extracted").glob("*.md"))
    if manifest["processed_shards"] != [f"conversations-{i:03d}.json" for i in range(5)]:
        failures.append("not all five shards are recorded in order")
    if len(records) != manifest["unique_primary_conversations"] or len(ids) != len(set(ids)):
        failures.append("classification index count/uniqueness mismatch")
    if len(extracts) != manifest["extract_count"]:
        failures.append("extract directory count does not match manifest")
    for record in records:
        should_extract = record["disposition"] in {"engineering-relevant", "potentially engineering-relevant", "mixed-content"}
        if bool(record.get("extract_file")) != should_extract:
            failures.append(f"extract policy mismatch for {record['conversation_id']}")
            break
        if record.get("extract_file") and not (vault / "01 Inbox" / "ChatGPT Export" / "Extracted" / record["extract_file"]).is_file():
            failures.append(f"missing extract for {record['conversation_id']}")
            break

    if failures:
        print("VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    result = {
        "status": "passed",
        "source_files_unchanged": len(source_before),
        "shards_processed": len(manifest["processed_shards"]),
        "unique_conversations_indexed": len(records),
        "extracts_validated": len(extracts),
        "byte_idempotent_outputs": len(after),
        "importer_errors": len(manifest["errors"]),
    }
    (vault / "01 Inbox" / "ChatGPT Export" / "validation_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("VALIDATION PASSED")
    print(f"- source files unchanged: {len(source_before)}")
    print(f"- shards processed: {len(manifest['processed_shards'])}")
    print(f"- unique conversations indexed: {len(records)}")
    print(f"- extracts validated: {len(extracts)}")
    print(f"- byte-idempotent outputs: {len(after)}")
    print(f"- importer errors: {len(manifest['errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
