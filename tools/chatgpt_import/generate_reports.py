#!/usr/bin/env python3
"""Generate deterministic Markdown reports from importer machine data."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def schema_report(manifest: dict[str, Any]) -> str:
    schema = manifest["schema"]
    shard_rows = [[name, manifest["shard_record_counts"].get(name, 0), "valid JSON"] for name in manifest["processed_shards"]]
    shard_rows += [["conversation_asset_file_names.json", manifest["asset_metadata_entries"], "valid JSON; metadata only"], ["shared_conversations.json", manifest["shared_records"], "valid JSON; secondary metadata"]]
    return f"""# ChatGPT Export Schema Report

> Audit date: 2026-07-17
> Source mode: read-only
> Result: all seven expected files exist and contain valid JSON.

## File validation

{md_table(['File', 'Records/entries', 'Validation'], shard_rows)}

All five numbered shards were loaded as one logical primary history. The importer never writes to the export directory.

## Observed primary schema

- Root of each numbered shard: JSON array.
- Primary records: {schema['primary_records']}.
- Conversation keys observed: `{', '.join(schema['conversation_keys'])}`.
- `mapping`: object keyed by node ID.
- Mapping nodes: {schema['mapping_nodes']}.
- Node keys observed: `{', '.join(schema['node_keys'])}`.
- Message objects: {schema['messages']}.
- Message keys observed: `{', '.join(schema['message_keys'])}`.
- Roles: {', '.join(f'`{key}` {value}' for key, value in schema['roles'].items())}.
- Content types: {', '.join(f'`{key}` {value}' for key, value in schema['content_types'].items())}.
- Conversations whose mapping contains at least one fork: {schema['branching_conversations']}.

## Ordering and branch interpretation

The export is a parent-linked message tree, not a flat chronological transcript. `current_node` identifies the selected leaf. The importer reconstructs the primary transcript by walking `parent` links from `current_node` to the root and reversing that lineage. Other leaves are preserved as alternative-branch suffixes after their divergence point. It does not sort the selected transcript solely by timestamp.

For classification only, every unique displayable message node is inspected in stable `(create_time, node_id)` order so relevant content on a non-current branch is not silently missed.

## Content handling

- `text` and textual parts of `multimodal_text` preserve fenced code and Mermaid/ASCII diagrams, but high-confidence credentials are replaced with explicit redaction placeholders before any extract is written.
- Image/file pointers become attachment-metadata markers; attachment bytes are not copied.
- `conversation_asset_file_names.json` supplies names only.
- `thoughts` and `reasoning_recap` are schema-counted but intentionally not emitted as conversational source content.
- Unknown structured parts are serialized visibly rather than discarded.

## Secondary shared data

`shared_conversations.json` contains {manifest['shared_records']} records. All {manifest['shared_overlap_with_primary']} shared conversation IDs overlap the primary history; there are {manifest['shared_only_records']} shared-only IDs. Shared rows therefore add metadata but no duplicate source extract.

## Schema risks

- The schema is undocumented and may change in future exports.
- Alternative branches can repeat context; the suffix representation minimizes repetition while retaining branch content.
- Attachment metadata does not prove the referenced asset exists or is safe to import.
- Message content can contain stale answers, personal data, or confidential project code; high-confidence credentials are redacted, but extracts remain unreviewed evidence rather than canonicals.
"""


def manifest_report(manifest: dict[str, Any]) -> str:
    disposition_rows = [[key, value] for key, value in manifest["disposition_counts"].items()]
    shard_rows = [[key, value] for key, value in manifest["shard_record_counts"].items()]
    category_rows = [[key, value] for key, value in sorted(manifest["category_counts"].items(), key=lambda item: (-item[1], item[0]))]
    duplicate_groups = len(manifest["duplicate_content_groups"])
    return f"""# ChatGPT Import Manifest

> Import date: 2026-07-17
> Scope: audit, extraction, and planning only
> Source directory: `/home/rahul/Downloads/chatgpt-export` (read-only)

## Outcome

- All five numbered conversation shards processed: **yes**.
- Primary records found: **{manifest['primary_records_found']}**.
- Unique primary conversations: **{manifest['unique_primary_conversations']}**.
- Duplicate records by conversation ID: **{manifest['duplicate_id_records']}**.
- Exact non-empty content duplicate groups: **{duplicate_groups}**.
- Shared records checked: **{manifest['shared_records']}**; overlap with primary: **{manifest['shared_overlap_with_primary']}**.
- Technical/potential/mixed source extracts written: **{manifest['extract_count']}**.
- Malformed primary records skipped: **{manifest['malformed_records']}**.
- Import/path errors: **{len(manifest['errors'])}**.

## Records by shard

{md_table(['Shard', 'Records'], shard_rows)}

## Classification dispositions

{md_table(['Disposition', 'Conversations'], disposition_rows)}

`mixed-content` is retained in Inbox for manual separation; it is not approved for permanent migration. `needs-manual-review` has no source note and appears in the review queue. `excluded-non-engineering` is represented only by aggregate/index metadata, never by a Markdown source extract.

## Technical categories

Counts overlap because one conversation may cover several categories. They measure source candidates, not canonical-note requirements.

{md_table(['Category', 'Conversations matched'], category_rows)}

## Deduplication

Primary deduplication uses `conversation_id` (falling back to `id`). If multiple shard records share an ID, the importer deterministically retains the version with the largest mapping, then newest update time. Exact body fingerprints are also reported. This export contains no duplicate primary IDs and no exact non-empty body duplicates.

All 13 shared IDs already exist in the primary history, so no shared record produced a second extract.

## Generated data

- `01 Inbox/ChatGPT Export/Extracted/`: {manifest['extract_count']} unreviewed Markdown extracts.
- `01 Inbox/ChatGPT Export/classification_index.json`: one machine record for every primary conversation, including excluded/manual records.
- `01 Inbox/ChatGPT Export/import_manifest.json`: machine manifest, schema statistics, counts, and errors.

Generated extracts are deterministic and can be regenerated. They preserve original IDs, titles, dates, source shards, selected branch order, alternative branches, code blocks, and attachment pointers while replacing high-confidence credentials with deterministic redaction placeholders.

## Errors

{('No importer errors were recorded.' if not manifest['errors'] else md_table(['Source', 'Error'], [[item.get('source'), item.get('error')] for item in manifest['errors']]))}
"""


def review_report(records: list[dict[str, Any]], errors: list[dict[str, str]]) -> str:
    groups = defaultdict(list)
    for record in records:
        groups[record["disposition"]].append(record)
    sections = ["# ChatGPT Import Review Queue", "", "> Generated from content-based heuristics. Review changes disposition only in the machine rules/index workflow; do not promote an Inbox extract directly into a canonical.", ""]
    descriptions = {
        "needs-manual-review": "No sufficiently specific engineering or excluded-domain content signal. No source extract was created.",
        "mixed-content": "Engineering and excluded-domain signals coexist. Separate only the engineering passages during migration; keep personal material out of the vault.",
        "potentially engineering-relevant": "Exactly one message-content category matched. Confirm usefulness before migration.",
    }
    for disposition in ("needs-manual-review", "mixed-content", "potentially engineering-relevant"):
        rows = []
        for record in sorted(groups[disposition], key=lambda item: (item.get("create_time") or "", item["conversation_id"])):
            extract = record.get("extract_file") or "not created"
            rows.append([record["conversation_id"], record["title"], ", ".join(record["categories"]) or "none", ", ".join(record["exclusion_evidence"]) or "none", extract])
        sections += [f"## {disposition} ({len(rows)})", "", descriptions[disposition], "", md_table(["Conversation ID", "Title", "Technical categories", "Excluded-domain signals", "Extract"], rows), ""]
    sections += ["## Import errors", "", "No errors." if not errors else md_table(["Source", "Error"], [[item.get("source"), item.get("error")] for item in errors]), ""]
    sections += ["## Review decisions", "", "For each reviewed record, record: keep technical passages, exclude, split mixed content, merge into an existing canonical later, or retain as source-only. Do not invent project ownership, scale, impact, or interview outcomes during triage.", ""]
    return "\n".join(sections)


def migration_report(manifest: dict[str, Any], records: list[dict[str, Any]]) -> str:
    # This shortlist combines exact failure-signal matches with manually audited
    # adjacent conversations. Generic topic matches remain in the JSON index.
    priority_ids = {
        "6974ed44-b94c-8322-8f3c-0b684c7e8bba",  # DSA Focus vs Go
        "69f0f564-696c-8321-96a9-42d209cc4862",  # Go Structs and Pointers
        "69f646ad-f5d8-8320-a796-ea63cab363ed",  # DSA Prep with Go
        "69f8c79f-0024-8323-8c2a-13a02404bc79",  # Go Backend Interview Prep
        "6a0880d8-e788-83a3-887b-78916efd303e",  # Go Program Correction
        "6a11f5e6-8020-8321-8234-5e3661848716",  # 45-Day Backend Interview Plan
        "6a33ff36-963c-83ee-92df-8e6684d5aedd",  # Go Developer Feedback
        "6a3b81c9-7418-83e8-85d6-683e381ed9ab",  # Senior Go Interview Prep
        "6a44bb84-6f10-83ee-917a-0d957485f633",  # Senior Golang Interview Q&A
        "6a5778fc-3758-83ee-9998-cba2bb1b0577",  # exact implementation failure cluster
    }
    priority_records = [record for record in records if record["conversation_id"] in priority_ids]
    priority_rows = [[record["conversation_id"], record["title"], ", ".join(record["priority_flags"]) or "manually shortlisted adjacent source", record.get("extract_file") or "review only"] for record in priority_records]
    concept_rows = [[key, value] for key, value in sorted(manifest["system_design_concept_counts"].items(), key=lambda item: (-item[1], item[0]))]
    project_rows = []
    project_assessment = {
        "NCS Permission Versioning": "Substantive candidates exist, especially Permission Version Analysis and Versioned Permissions Planning; ownership and metrics still require verification.",
        "CEE Conductor Migration": "Multiple code/architecture candidates exist around DALM, GetContacts, Conductor networking, and refactoring; exact migration boundary and personal ownership remain unverified.",
        "CoMarketer WebSocket Architecture": "Matches are incidental/name mentions; no clearly substantive project-specific conversation was established automatically.",
        "PulseCheck Monitoring System": "The Pulsecheck conversation is a substantive candidate, but other matches are mostly reused name/context; verify which material describes the actual project.",
    }
    for project, count in manifest["project_counts"].items():
        project_rows.append([project, count, project_assessment[project]])
    return f"""# ChatGPT Migration Plan

> Prepared: 2026-07-17
> Status: extraction complete; permanent knowledge migration not started

## Migration boundary

The 213 extracts are immutable-style source evidence in Inbox, not a new knowledge base. Migrate one category at a time into existing canonical owners. Every promoted passage must retain its conversation ID/source link. Mixed records must be split during review, and unsupported claims remain unverified.

## Ordered execution plan

1. **Foundation implementation failures** — review the flagged conversations, especially `6a5778fc-3758-83ee-9998-cba2bb1b0577`, then improve existing slice/map/struct/method/interface/embedding/error canonicals and drills only where the source adds unique evidence. Create personal mistake and re-test records only from the user-confirmed failures.
2. **DSA in Go** — separate reusable Go syntax from language-independent patterns; historical Java solutions become a queue for fresh Go attempts, not copied solution notes.
3. **Verified project evidence** — triage NCS and CEE first because source candidates are concrete; then PulseCheck; leave CoMarketer blocked unless direct evidence is found/confirmed.
4. **System-design patterns** — promote reusable concepts one at a time, linking systems to patterns instead of copying explanations.
5. **Databases/messaging/cache/reliability/security** — select source-backed concepts by interview priority and verify version-sensitive claims.
6. **Kubernetes/AWS/Linux/networking/observability** — separate operational mechanics from system-design decisions and project claims.
7. **Interview/behavioural evidence** — verify all personal claims and metrics before producing STAR/project notes.

## High-priority source candidates

The following shortlist combines classifier failure signals with manually audited adjacent Go/interview conversations. Heuristics can over-match; the review decision remains manual.

{md_table(['Conversation ID', 'Title', 'Priority flags', 'Extract'], priority_rows)}

The strongest single source is **Golang Implementation Fluency Issues** (`6a5778fc…`): it explicitly records the balanced four-part slice failure, map/slice syntax failure, theory/implementation gap, Java NeetCode practice for Go roles, interface invocation difficulty, and embedding/construction concerns. It should seed one verified interview-mistake cluster and scheduled re-tests—not duplicate all existing Go canonicals.

## System-design source map

Counts are conversation mentions/content matches, not proof that each deserves a note.

{md_table(['Concept', 'Candidate conversations'], concept_rows)}

For every real-system design, use the vault standard plus a separate under-five-minute revision. Reusable Saga/outbox/CDC/CQRS/cache/idempotency/retry/circuit-breaker/bulkhead/backpressure/rate-limit/sharding/replication/locking material must have one canonical owner and be linked from Uber/YouTube/project designs.

## Project evidence assessment

{md_table(['Project', 'Matched conversations', 'Audit assessment'], project_rows)}

Before updating a project canonical, create a claim ledger with: exact source passage, business problem, previous limitation, ownership, architecture, implementation, trade-off, failure/lesson, measurable impact source, redesign idea, STAR phrasing, and follow-up questions. Unknowns remain explicit.

## Per-category migration checklist

- Freeze the category's extract list from `classification_index.json`.
- Review mixed/manual false positives before content work.
- Map each useful passage to an existing canonical owner or a justified future canonical.
- Record source conversation ID and date.
- Verify technical/version-sensitive claims and all personal claims.
- Improve the canonical; do not create a parallel explanation.
- Add/update revision/drill/question assets only when they support a distinct learning action.
- Run executable examples/tests and link observed mistakes to scheduled re-tests.
- Archive superseded originals only in a later, separately approved execution stage.

## Explicitly deferred

No permanent note was reorganized, merged, rewritten from the export, or archived in this run. No readiness status, drill result, project metric, or personal achievement was inferred from ChatGPT text.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    args = parser.parse_args()
    vault = args.vault.resolve()
    manifest = load(vault / "01 Inbox" / "ChatGPT Export" / "import_manifest.json")
    records = load(vault / "01 Inbox" / "ChatGPT Export" / "classification_index.json")["records"]
    reports = {
        "CHATGPT_EXPORT_SCHEMA_REPORT.md": schema_report(manifest),
        "CHATGPT_IMPORT_MANIFEST.md": manifest_report(manifest),
        "CHATGPT_IMPORT_REVIEW_QUEUE.md": review_report(records, manifest["errors"]),
        "CHATGPT_MIGRATION_PLAN.md": migration_report(manifest, records),
    }
    for name, content in reports.items():
        (vault / name).write_text(content.rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
