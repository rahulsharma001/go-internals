# ChatGPT import tool

This standard-library-only Python 3 importer treats the five numbered files as
one history, deduplicates by conversation ID, inspects every displayable message
for classification, follows `current_node` parent links for the primary branch,
and preserves alternative branch suffixes separately.

It reads attachment names as metadata only. It does not copy attachments and
does not write anywhere inside the export directory.

```bash
python3 tools/chatgpt_import/import_chatgpt.py \
  --source /home/rahul/Downloads/chatgpt-export \
  --vault /home/rahul/Documents/engineering-os

python3 -m unittest discover -s tools/chatgpt_import -p 'test_*.py'
```

Generated machine-readable files live under `01 Inbox/ChatGPT Export/`.
Re-running against identical inputs produces byte-identical indexes and source
extracts because no wall-clock timestamp or random value is written.
