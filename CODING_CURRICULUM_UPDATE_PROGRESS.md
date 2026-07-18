---
type: migration-progress
scope: dsa-backend-lld
status: in-progress
last_updated: 2026-07-18
---

# Coding Curriculum Update Progress

## Pre-change audit plan

This plan is the safety gate for the requested cross-vault update. Changes are limited to `02 Go/`, `03 DSA/`, `06 Interviews/`, `08 Quick Revision/`, `10 Templates/`, interview-related dashboard files, and the two root reports named in the request.

1. Inventory existing DSA problems, pattern notes, Go canonical notes, dashboards, and any runnable implementations.
2. Map requested problems to existing canonical notes before creating files; preserve source traceability and existing solution material.
3. Create the requested folders, templates, trackers, plans, and Markdown dashboards without touching unrelated domains.
4. Scaffold one canonical note per requested problem. Existing complete solutions remain only where already present; new notes receive implementation workspaces, not copied solutions.
5. Create LLD package scaffolds with valid package names and non-failing tests; enrich only the first five requested packages.
6. Add concise revision indexes and an adjustable 12-week execution schedule.
7. Validate exact curriculum counts, metadata, local links, package names, compilation, tests, race tests, and the final changed-file scope.

## Completed work

- Read and accepted the root `AGENTS.md` constraints.
- Inventoried the scoped vault areas and identified reusable DSA and Worker Pool canonicals.

## Pending work

- Batch 1 scaffolding and normalization.
- First detailed enrichment batch.
- Verification and final migration report.

## Exact next task

Create the four templates, canonical folder layout, and generated trackers from the audited curriculum lists.

## Verification commands

Commands will be finalized after generation. They will include metadata/link validation, `go test ./...`, `go test -race ./...`, and `tools/security/scan-secrets.sh` if a commit is requested.
