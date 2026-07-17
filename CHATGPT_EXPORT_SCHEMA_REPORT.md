# ChatGPT Export Schema Report

> Audit date: 2026-07-17
> Source mode: read-only
> Result: all seven expected files exist and contain valid JSON.

## File validation

| File | Records/entries | Validation |
| --- | --- | --- |
| conversations-000.json | 100 | valid JSON |
| conversations-001.json | 100 | valid JSON |
| conversations-002.json | 100 | valid JSON |
| conversations-003.json | 100 | valid JSON |
| conversations-004.json | 87 | valid JSON |
| conversation_asset_file_names.json | 143 | valid JSON; metadata only |
| shared_conversations.json | 13 | valid JSON; secondary metadata |

All five numbered shards were loaded as one logical primary history. The importer never writes to the export directory.

## Observed primary schema

- Root of each numbered shard: JSON array.
- Primary records: 487.
- Conversation keys observed: `conversation_id, conversation_template_id, create_time, current_node, default_model_slug, id, is_archived, is_do_not_remember, is_read_only, is_starred, is_study_mode, mapping, memory_scope, pinned_time, plugin_ids, title, update_time, voice`.
- `mapping`: object keyed by node ID.
- Mapping nodes: 5151.
- Node keys observed: `id, message, parent`.
- Message objects: 4664.
- Message keys observed: `author, content, create_time, id, metadata`.
- Roles: `assistant` 2617, `user` 2047.
- Content types: `multimodal_text` 101, `reasoning_recap` 174, `text` 4079, `thoughts` 310.
- Conversations whose mapping contains at least one fork: 78.

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

`shared_conversations.json` contains 13 records. All 13 shared conversation IDs overlap the primary history; there are 0 shared-only IDs. Shared rows therefore add metadata but no duplicate source extract.

## Schema risks

- The schema is undocumented and may change in future exports.
- Alternative branches can repeat context; the suffix representation minimizes repetition while retaining branch content.
- Attachment metadata does not prove the referenced asset exists or is safe to import.
- Message content can contain stale answers, personal data, or confidential project code; high-confidence credentials are redacted, but extracts remain unreviewed evidence rather than canonicals.
