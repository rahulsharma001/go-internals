#!/usr/bin/env python3
"""Import a ChatGPT export into deterministic, traceable Obsidian source extracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from classifier import Classification, classify


EXPECTED = [*(f"conversations-{i:03d}.json" for i in range(5)), "conversation_asset_file_names.json", "shared_conversations.json"]
EXTRACT_DISPOSITIONS = {"engineering-relevant", "potentially engineering-relevant", "mixed-content"}
DISPLAYABLE_CONTENT_TYPES = {"text", "multimodal_text"}

AWS_ACCESS_KEY_ID = re.compile(r"\b(?:AKIA|ASIA|AIDA|AROA|AIPA|ANPA|ANVA|AGPA)[A-Z0-9]{16}\b")
AWS_SECRET_ASSIGNMENT = re.compile(r"(?i)(\baws_secret_access_key\b\s*[:=]\s*)([\"']?)([^\s\"'`,;}{]{8,})([\"']?)")
QUOTED_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:password|passwd|pwd|client_secret|oauth_client_secret|jwt_secret|signing_secret|api_key|access_token|refresh_token)\b\s*[:=]\s*)([\"'])(.*?)(\2)"
)
UNQUOTED_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:password|passwd|pwd|client_secret|oauth_client_secret|jwt_secret|signing_secret|api_key|access_token|refresh_token)\b\s*[:=]\s*)([^\s\"'`,;}{]{8,})"
)


def approved_demonstration_value(value: str) -> bool:
    return bool(
        re.search(r"(?:REDACTED|EXAMPLE|DUMMY|FAKE|MOCK|CHANGEME|YOUR[_-]|PLACEHOLDER|\.\.\.)", value, re.I)
        or re.fullmatch(r"<[^>]+>", value)
        or value.startswith("$")
        or "(" in value
        or ")" in value
    )


def sanitize_export_text(text: str) -> str:
    """Redact high-confidence credentials while retaining technical context."""

    text = re.sub(
        r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----.*?-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        text,
        flags=re.S,
    )
    text = re.sub(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b", "[REDACTED_GITHUB_TOKEN]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{20,}\b", "[REDACTED_API_TOKEN]", text)
    text = re.sub(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b", "[REDACTED_SLACK_TOKEN]", text)
    text = re.sub(
        r"\bBearer\s+[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
        "Bearer [REDACTED_JWT]",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\b(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^/\s:@]+:[^/\s@]+@",
        lambda match: f"{match.group(1)}://[REDACTED_CREDENTIALS]@",
        text,
        flags=re.I,
    )

    sanitized_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if AWS_ACCESS_KEY_ID.search(line):
            line = re.sub(r"(?<![A-Za-z0-9/+])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+])", "[REDACTED_AWS_SECRET_ACCESS_KEY]", line)
            line = AWS_ACCESS_KEY_ID.sub("[REDACTED_AWS_ACCESS_KEY_ID]", line)

        def redact_aws_secret(match: re.Match[str]) -> str:
            value = match.group(3)
            if approved_demonstration_value(value):
                return match.group(0)
            return f"{match.group(1)}[REDACTED_AWS_SECRET_ACCESS_KEY]"

        def redact_quoted(match: re.Match[str]) -> str:
            value = match.group(3)
            if approved_demonstration_value(value):
                return match.group(0)
            return f"{match.group(1)}{match.group(2)}[REDACTED_CREDENTIAL]{match.group(4)}"

        def redact_unquoted(match: re.Match[str]) -> str:
            value = match.group(2)
            if approved_demonstration_value(value):
                return match.group(0)
            return f"{match.group(1)}[REDACTED_CREDENTIAL]"

        line = AWS_SECRET_ASSIGNMENT.sub(redact_aws_secret, line)
        line = QUOTED_CREDENTIAL_ASSIGNMENT.sub(redact_quoted, line)
        line = UNQUOTED_CREDENTIAL_ASSIGNMENT.sub(redact_unquoted, line)
        sanitized_lines.append(line)
    return "".join(sanitized_lines)


def json_load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def timestamp(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def conversation_id(record: dict[str, Any]) -> str | None:
    value = record.get("conversation_id") or record.get("id")
    return str(value) if value else None


def asset_name(pointer: str, assets: dict[str, Any]) -> str | None:
    key = pointer.removeprefix("file-service://")
    candidates = (key, f"{key}.dat")
    for candidate in candidates:
        if candidate in assets:
            value = assets[candidate]
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                for field in ("file_name", "filename", "name"):
                    if value.get(field):
                        return str(value[field])
            return str(value)
    return None


def render_part(part: Any, assets: dict[str, Any]) -> str:
    if isinstance(part, str):
        return part
    if isinstance(part, (int, float, bool)):
        return str(part)
    if isinstance(part, dict):
        content_type = part.get("content_type")
        if content_type == "image_asset_pointer" or part.get("asset_pointer"):
            pointer = str(part.get("asset_pointer") or "unknown")
            name = asset_name(pointer, assets)
            detail = f"; original filename: {name}" if name else ""
            return f"[Attachment metadata: {pointer}{detail}]"
        for field in ("text", "content"):
            if isinstance(part.get(field), str):
                return str(part[field])
        return f"[Structured content: {json.dumps(part, ensure_ascii=False, sort_keys=True)}]"
    return f"[Unsupported content: {type(part).__name__}]"


def message_text(message: dict[str, Any], assets: dict[str, Any]) -> str:
    content = message.get("content")
    if not isinstance(content, dict) or content.get("content_type") not in DISPLAYABLE_CONTENT_TYPES:
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""
    return "\n\n".join(filter(None, (render_part(part, assets).strip() for part in parts))).strip()


def all_body(record: dict[str, Any], assets: dict[str, Any]) -> str:
    mapping = record.get("mapping")
    if not isinstance(mapping, dict):
        return ""
    ordered: list[tuple[float, str, str]] = []
    for node_id, node in mapping.items():
        if not isinstance(node, dict) or not isinstance(node.get("message"), dict):
            continue
        message = node["message"]
        text = message_text(message, assets)
        if text:
            ordered.append((float(message.get("create_time") or 0), str(node_id), text))
    return "\n".join(item[2] for item in sorted(ordered))


def lineage(mapping: dict[str, Any], leaf: str | None) -> tuple[list[str], list[str]]:
    path: list[str] = []
    errors: list[str] = []
    seen: set[str] = set()
    node_id = leaf
    while node_id:
        if node_id in seen:
            errors.append(f"cycle detected at node {node_id}")
            break
        seen.add(node_id)
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            errors.append(f"missing or malformed node {node_id}")
            break
        path.append(node_id)
        parent = node.get("parent")
        node_id = str(parent) if parent else None
    path.reverse()
    return path, errors


def conversation_paths(record: dict[str, Any]) -> tuple[list[str], list[tuple[str, list[str], str | None]], list[str]]:
    mapping = record.get("mapping")
    if not isinstance(mapping, dict):
        return [], [], ["mapping is not an object"]
    current = record.get("current_node")
    primary, errors = lineage(mapping, str(current) if current else None)
    parents = {str(node.get("parent")) for node in mapping.values() if isinstance(node, dict) and node.get("parent")}
    leaves = sorted(str(node_id) for node_id in mapping if str(node_id) not in parents)
    branches: list[tuple[str, list[str], str | None]] = []
    for leaf in leaves:
        if leaf == current:
            continue
        path, path_errors = lineage(mapping, leaf)
        errors.extend(path_errors)
        common = 0
        while common < min(len(primary), len(path)) and primary[common] == path[common]:
            common += 1
        branch_from = primary[common - 1] if common else None
        suffix = path[common:]
        if suffix:
            branches.append((leaf, suffix, branch_from))
    return primary, branches, errors


def render_message(node_id: str, node: dict[str, Any], assets: dict[str, Any]) -> str:
    message = node.get("message")
    if not isinstance(message, dict):
        return ""
    body = sanitize_export_text(message_text(message, assets))
    if not body:
        return ""
    author = message.get("author") if isinstance(message.get("author"), dict) else {}
    role = str(author.get("role") or "unknown").title()
    created = timestamp(message.get("create_time")) or "unknown"
    return f"### {role}\n\n<!-- node_id: {node_id}; created_at: {created} -->\n\n{body}\n"


def safe_name(title: str, created: str | None, cid: str) -> str:
    cleaned = re.sub(r"[^\w .()&+-]+", "-", title, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .-") or "Untitled Conversation"
    cleaned = cleaned[:90].rstrip()
    date = created[:10] if created else "unknown-date"
    return f"{date} - {cleaned} - {cid[:8]}.md"


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_extract(record: dict[str, Any], classification: Classification, assets: dict[str, Any], source_files: list[str], shared_overlap: bool = False) -> tuple[str, list[str]]:
    cid = conversation_id(record) or "unknown"
    title = str(record.get("title") or "Untitled Conversation")
    created = timestamp(record.get("create_time"))
    updated = timestamp(record.get("update_time"))
    mapping = record.get("mapping") if isinstance(record.get("mapping"), dict) else {}
    primary, branches, errors = conversation_paths(record)
    frontmatter = [
        "---", "type: chatgpt-source-extract", "status: unprocessed", f"conversation_id: {yaml_string(cid)}",
        f"title: {yaml_string(title)}", f"created_at: {yaml_string(created or '')}", f"updated_at: {yaml_string(updated or '')}",
        f"classification: {classification.disposition}", "categories:",
        *(f"  - {yaml_string(item)}" for item in classification.categories), "source_files:",
        *(f"  - {yaml_string(item)}" for item in source_files), f"shared_export_overlap: {str(shared_overlap).lower()}", "---", "",
    ]
    lines = frontmatter + [
        f"# {title}", "", "> [!warning] Unreviewed source extract",
        "> This preserves source material for audit and later curation. It may contain incorrect, stale, confidential, or personal data. Do not promote claims or metrics without verification.", "",
        "## Classification", "", f"- Disposition: `{classification.disposition}`",
        f"- Categories: {', '.join(classification.categories) or 'none'}",
        f"- Priority flags: {', '.join(classification.priority_flags) or 'none'}",
        f"- System-design concepts: {', '.join(classification.system_design_concepts) or 'none'}",
        f"- Project flags: {', '.join(classification.project_flags) or 'none'}", "",
        "## Source metadata", "", f"- Conversation ID: `{cid}`", f"- Created: {created or 'unknown'}", f"- Updated: {updated or 'unknown'}",
        f"- Primary source: {', '.join(source_files)}", f"- Current node: `{record.get('current_node') or 'unknown'}`",
        f"- Mapping nodes: {len(mapping)}", f"- Alternative branch leaves preserved: {len(branches)}", "",
        "## Primary branch", "",
    ]
    for node_id in primary:
        rendered = render_message(node_id, mapping.get(node_id, {}), assets)
        if rendered:
            lines.append(rendered)
    if branches:
        lines += ["## Alternative branches", "", "These are non-current branches. Each section contains only the suffix after it diverged from the primary lineage.", ""]
        for leaf, suffix, branch_from in branches:
            lines += [f"### Branch leaf `{leaf}`", "", f"Diverged after node: `{branch_from or 'root'}`", ""]
            for node_id in suffix:
                rendered = render_message(node_id, mapping.get(node_id, {}), assets)
                if rendered:
                    lines.append(rendered.replace("### ", "#### ", 1))
    return "\n".join(lines).rstrip() + "\n", errors


def schema_summary(files: list[Path], datasets: list[Any]) -> dict[str, Any]:
    root_types = Counter(type(data).__name__ for data in datasets)
    record_keys: Counter[str] = Counter()
    node_keys: Counter[str] = Counter()
    message_keys: Counter[str] = Counter()
    content_types: Counter[str] = Counter()
    roles: Counter[str] = Counter()
    records = nodes = messages = branches = 0
    for data in datasets[:5]:
        if not isinstance(data, list):
            continue
        records += len(data)
        for record in data:
            if not isinstance(record, dict):
                continue
            record_keys.update(record.keys())
            mapping = record.get("mapping")
            if not isinstance(mapping, dict):
                continue
            nodes += len(mapping)
            parent_counts = Counter(str(node.get("parent")) for node in mapping.values() if isinstance(node, dict) and node.get("parent"))
            if any(count > 1 for count in parent_counts.values()):
                branches += 1
            for node in mapping.values():
                if not isinstance(node, dict):
                    continue
                node_keys.update(node.keys())
                message = node.get("message")
                if not isinstance(message, dict):
                    continue
                messages += 1
                message_keys.update(message.keys())
                author = message.get("author") or {}
                roles[str(author.get("role"))] += 1
                content = message.get("content") or {}
                content_types[str(content.get("content_type"))] += 1
    return {
        "files": [path.name for path in files], "root_types": dict(sorted(root_types.items())), "primary_records": records,
        "mapping_nodes": nodes, "messages": messages, "branching_conversations": branches,
        "conversation_keys": sorted(record_keys), "node_keys": sorted(node_keys), "message_keys": sorted(message_keys),
        "content_types": dict(sorted(content_types.items())), "roles": dict(sorted(roles.items())),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    vault = args.vault.resolve()
    errors: list[dict[str, str]] = []
    paths = [source / name for name in EXPECTED]
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        print(f"Missing expected files: {', '.join(missing)}", file=sys.stderr)
        return 2
    datasets: list[Any] = []
    for path in paths:
        try:
            datasets.append(json_load(path))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Invalid JSON {path.name}: {exc}", file=sys.stderr)
            return 2
    if args.validate_only:
        print(json.dumps(schema_summary(paths, datasets), indent=2, sort_keys=True))
        return 0

    assets = datasets[5] if isinstance(datasets[5], dict) else {}
    shared = datasets[6] if isinstance(datasets[6], list) else []
    candidates: dict[str, list[tuple[dict[str, Any], str, int]]] = defaultdict(list)
    shard_counts: dict[str, int] = {}
    malformed_records = 0
    for shard_index, data in enumerate(datasets[:5]):
        shard = paths[shard_index].name
        if not isinstance(data, list):
            errors.append({"source": shard, "error": "root is not an array"})
            continue
        shard_counts[shard] = len(data)
        for record_index, record in enumerate(data):
            if not isinstance(record, dict):
                malformed_records += 1
                errors.append({"source": f"{shard}#{record_index}", "error": "record is not an object"})
                continue
            cid = conversation_id(record)
            if not cid:
                malformed_records += 1
                errors.append({"source": f"{shard}#{record_index}", "error": "record has no conversation ID"})
                continue
            candidates[cid].append((record, shard, record_index))

    records: list[tuple[dict[str, Any], list[str]]] = []
    duplicate_id_records = 0
    for cid, versions in sorted(candidates.items()):
        duplicate_id_records += max(0, len(versions) - 1)
        ranked = sorted(
            versions,
            key=lambda item: (
                len(item[0].get("mapping") or {}) if isinstance(item[0].get("mapping"), dict) else 0,
                float(item[0].get("update_time") or 0),
                item[1], -item[2],
            ),
            reverse=True,
        )
        selected = ranked[0][0]
        records.append((selected, sorted({item[1] for item in versions})))

    shared_ids = {str(item.get("conversation_id")) for item in shared if isinstance(item, dict) and item.get("conversation_id")}
    primary_ids = {conversation_id(record) for record, _ in records}
    content_fingerprints: dict[str, list[str]] = defaultdict(list)
    previous_manifest_path = vault / "01 Inbox" / "ChatGPT Export" / "import_manifest.json"
    previous_generated: set[str] = set()
    if previous_manifest_path.is_file():
        try:
            previous_manifest = json_load(previous_manifest_path)
            previous_generated = set(previous_manifest.get("generated_extract_files") or []) if isinstance(previous_manifest, dict) else set()
        except (OSError, json.JSONDecodeError):
            previous_generated = set()
    output_dir = vault / "01 Inbox" / "ChatGPT Export" / "Extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    index_records: list[dict[str, Any]] = []
    generated_files: list[str] = []
    disposition_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    concept_counts: Counter[str] = Counter()
    project_counts: Counter[str] = Counter()
    branch_count = 0
    extracted = 0
    for record, source_files in sorted(records, key=lambda item: ((item[0].get("create_time") or 0), conversation_id(item[0]) or "")):
        cid = conversation_id(record) or "unknown"
        title = str(record.get("title") or "Untitled Conversation")
        body = all_body(record, assets)
        fingerprint = hashlib.sha256(body.encode("utf-8")).hexdigest() if body else None
        if fingerprint:
            content_fingerprints[fingerprint].append(cid)
        result = classify(title, body)
        disposition_counts[result.disposition] += 1
        category_counts.update(result.categories)
        priority_counts.update(result.priority_flags)
        concept_counts.update(result.system_design_concepts)
        project_counts.update(result.project_flags)
        primary, branches, path_errors = conversation_paths(record)
        branch_count += 1 if branches else 0
        for error in path_errors:
            errors.append({"source": cid, "error": error})
        filename = None
        if result.disposition in EXTRACT_DISPOSITIONS:
            content, render_errors = render_extract(record, result, assets, source_files, cid in shared_ids)
            for error in render_errors:
                errors.append({"source": cid, "error": error})
            filename = safe_name(title, timestamp(record.get("create_time")), cid)
            destination = output_dir / filename
            destination.write_text(content, encoding="utf-8")
            generated_files.append(str(destination.relative_to(vault)))
            extracted += 1
        entry = {
            "conversation_id": cid, "title": title, "create_time": timestamp(record.get("create_time")),
            "update_time": timestamp(record.get("update_time")), "source_files": source_files,
            "message_content_inspected": True, "mapping_nodes": len(record.get("mapping") or {}) if isinstance(record.get("mapping"), dict) else 0,
            "primary_path_nodes": len(primary), "alternative_branch_leaves": len(branches), "shared_export_overlap": cid in shared_ids,
            "extract_file": filename, **asdict(result),
        }
        index_records.append(entry)

    duplicate_content_groups = [ids for ids in content_fingerprints.values() if len(ids) > 1]
    index = {
        "format_version": 1, "source_directory": str(source), "generated_at_policy": "deterministic; no wall-clock timestamp stored",
        "records": index_records,
    }
    index_path = vault / "01 Inbox" / "ChatGPT Export" / "classification_index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Remove only stale files previously declared as generated by this tool and
    # still carrying the generated extract marker. Source JSON and hand-written
    # notes are never deletion candidates.
    for stale_relative in sorted(previous_generated - set(generated_files)):
        stale = vault / stale_relative
        try:
            if stale.is_file() and "type: chatgpt-source-extract" in stale.read_text(encoding="utf-8")[:500]:
                stale.unlink()
        except OSError as exc:
            errors.append({"source": stale_relative, "error": f"could not remove stale generated extract: {exc}"})
    manifest = {
        "format_version": 1, "expected_files": EXPECTED, "valid_json_files": [path.name for path in paths],
        "processed_shards": [paths[i].name for i in range(5)], "shard_record_counts": shard_counts,
        "primary_records_found": sum(shard_counts.values()), "unique_primary_conversations": len(records),
        "duplicate_id_records": duplicate_id_records, "duplicate_content_groups": duplicate_content_groups,
        "shared_records": len(shared), "shared_overlap_with_primary": len(shared_ids & primary_ids), "shared_only_records": len(shared_ids - primary_ids),
        "asset_metadata_entries": len(assets), "malformed_records": malformed_records, "branching_conversations": branch_count,
        "disposition_counts": dict(sorted(disposition_counts.items())), "category_counts": dict(sorted(category_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())), "system_design_concept_counts": dict(sorted(concept_counts.items())),
        "project_counts": dict(sorted(project_counts.items())), "extract_count": extracted,
        "generated_extract_files": generated_files, "errors": errors, "schema": schema_summary(paths, datasets),
    }
    manifest_path = vault / "01 Inbox" / "ChatGPT Export" / "import_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("processed_shards", "unique_primary_conversations", "duplicate_id_records", "shared_overlap_with_primary", "disposition_counts", "extract_count", "errors")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
