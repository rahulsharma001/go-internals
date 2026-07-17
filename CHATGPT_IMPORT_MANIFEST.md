# ChatGPT Import Manifest

> Import date: 2026-07-17
> Scope: audit, extraction, and planning only
> Source directory: `/home/rahul/Downloads/chatgpt-export` (read-only)

## Outcome

- All five numbered conversation shards processed: **yes**.
- Primary records found: **487**.
- Unique primary conversations: **487**.
- Duplicate records by conversation ID: **0**.
- Exact non-empty content duplicate groups: **0**.
- Shared records checked: **13**; overlap with primary: **13**.
- Technical/potential/mixed source extracts written: **213**.
- Malformed primary records skipped: **0**.
- Import/path errors: **0**.

## Records by shard

| Shard | Records |
| --- | --- |
| conversations-000.json | 100 |
| conversations-001.json | 100 |
| conversations-002.json | 100 |
| conversations-003.json | 100 |
| conversations-004.json | 87 |

## Classification dispositions

| Disposition | Conversations |
| --- | --- |
| engineering-relevant | 95 |
| excluded-non-engineering | 213 |
| mixed-content | 81 |
| needs-manual-review | 61 |
| potentially engineering-relevant | 37 |

`mixed-content` is retained in Inbox for manual separation; it is not approved for permanent migration. `needs-manual-review` has no source note and appears in the review queue. `excluded-non-engineering` is represented only by aggregate/index metadata, never by a Markdown source extract.

## Technical categories

Counts overlap because one conversation may cover several categories. They measure source candidates, not canonical-note requirements.

| Category | Conversations matched |
| --- | --- |
| system-design foundations | 110 |
| reliability and observability | 106 |
| Go foundations | 103 |
| DSA and NeetCode | 99 |
| AWS | 88 |
| Kubernetes and infrastructure | 80 |
| distributed-system patterns | 79 |
| caching and Redis | 75 |
| Kafka and messaging | 70 |
| Go concurrency | 65 |
| Linux and networking | 63 |
| security | 58 |
| databases | 56 |
| Go networking and testing | 44 |
| Go collections | 40 |
| structs, methods and interfaces | 35 |
| Google preparation roadmap | 34 |
| production projects | 29 |
| Go runtime and internals | 26 |
| interview mistakes | 22 |
| real system designs | 9 |
| behavioural and leadership preparation | 7 |
| interview experiences | 5 |

## Deduplication

Primary deduplication uses `conversation_id` (falling back to `id`). If multiple shard records share an ID, the importer deterministically retains the version with the largest mapping, then newest update time. Exact body fingerprints are also reported. This export contains no duplicate primary IDs and no exact non-empty body duplicates.

All 13 shared IDs already exist in the primary history, so no shared record produced a second extract.

## Generated data

- `01 Inbox/ChatGPT Export/Extracted/`: 213 unreviewed Markdown extracts.
- `01 Inbox/ChatGPT Export/classification_index.json`: one machine record for every primary conversation, including excluded/manual records.
- `01 Inbox/ChatGPT Export/import_manifest.json`: machine manifest, schema statistics, counts, and errors.

Generated extracts are deterministic and can be regenerated. They preserve original IDs, titles, dates, source shards, selected branch order, alternative branches, code blocks, and attachment pointers.

## Errors

No importer errors were recorded.
