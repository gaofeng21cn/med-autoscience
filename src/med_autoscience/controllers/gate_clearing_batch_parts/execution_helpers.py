from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_json_object_from_cli_stdout(stdout: str) -> dict[str, Any]:
    text = (stdout or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        payload = None
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                candidate, consumed = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if text[index + consumed :].strip():
                continue
            payload = candidate
            break
        if payload is None:
            raise
    if not isinstance(payload, dict):
        raise RuntimeError("CLI returned a non-object JSON payload")
    return payload


def run_workspace_display_repair_script(*, paper_root: Path) -> dict[str, Any]:
    script_path = paper_root / "build" / "generate_display_exports.py"
    if not script_path.exists():
        return {
            "status": "missing",
            "script_path": str(script_path),
        }
    completed = subprocess.run(
        [shutil.which("python3") or sys.executable, str(script_path)],
        cwd=str(paper_root.parent),
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "status": "updated",
        "script_path": str(script_path),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


_PAPER_LIVE_PATH_SURFACES = (
    "selected_outline.json",
    "evidence_ledger.json",
    "claim_evidence_map.json",
    "figure_catalog.json",
    "table_catalog.json",
    "figures/figure_catalog.json",
    "tables/table_catalog.json",
    "paper_bundle_manifest.json",
    "baseline_inventory.json",
)
_PATH_KEYS = frozenset(
    {
        "asset_paths",
        "compiled_markdown_path",
        "compile_report_path",
        "delivery_source_paths",
        "export_paths",
        "figure_catalog_path",
        "layout_sidecar_path",
        "missing_source_paths",
        "output_paths",
        "pdf_path",
        "planned_export_paths",
        "rendered_export_paths",
        "rendered_layout_sidecar_path",
        "source_paths",
        "source_relative_paths",
        "table_catalog_path",
    }
)


def _is_path_like_text(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if "://" in text:
        return False
    return (
        text.startswith(("/", "~", ".", "paper/"))
        or "/" in text
        or "\\" in text
        or Path(text).suffix != ""
    )


def _collapse_duplicate_paper_segments(path: Path) -> Path:
    parts = list(path.parts)
    collapsed: list[str] = []
    for part in parts:
        if part == "paper" and collapsed and collapsed[-1] == "paper":
            continue
        collapsed.append(part)
    return Path(*collapsed) if collapsed else path


def _paper_suffix(path: Path) -> Path | None:
    parts = list(path.parts)
    for index in range(len(parts) - 1, -1, -1):
        part = parts[index]
        if part == "paper":
            suffix_parts = parts[index + 1 :]
            return Path(*suffix_parts) if suffix_parts else Path()
    return None


def _relative_path_for_root(path: Path, *, target_root: Path) -> str:
    normalized = _collapse_duplicate_paper_segments(path)
    try:
        return normalized.resolve(strict=False).relative_to(target_root.resolve(strict=False)).as_posix()
    except ValueError:
        return os.path.relpath(
            normalized.resolve(strict=False),
            target_root.resolve(strict=False),
        ).replace(os.sep, "/")


def _resolve_live_path(
    value: str,
    *,
    source_root: Path,
    target_root: Path,
    current_workspace_root: Path,
    legacy_workspace_roots: tuple[Path, ...],
) -> str:
    raw = value.strip()
    if not _is_path_like_text(raw):
        return value
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = source_root / candidate
    candidate = _collapse_duplicate_paper_segments(candidate)
    paper_target_root = target_root if target_root.name == "paper" else target_root / "paper"
    paper_suffix = _paper_suffix(candidate)
    if paper_suffix is not None:
        candidate = paper_target_root / paper_suffix
    for legacy_root in legacy_workspace_roots:
        try:
            suffix = candidate.resolve(strict=False).relative_to(legacy_root.resolve(strict=False))
        except ValueError:
            continue
        candidate = current_workspace_root / suffix
        break
    return _relative_path_for_root(candidate, target_root=target_root)


def _is_under_path(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _normalize_path_payload(
    value: Any,
    *,
    key: str | None,
    source_root: Path,
    target_root: Path,
    current_workspace_root: Path,
    legacy_workspace_roots: tuple[Path, ...],
) -> tuple[Any, bool]:
    if isinstance(value, dict):
        changed = False
        normalized: dict[str, Any] = {}
        for child_key, child_value in value.items():
            child_normalized, child_changed = _normalize_path_payload(
                child_value,
                key=str(child_key),
                source_root=source_root,
                target_root=target_root,
                current_workspace_root=current_workspace_root,
                legacy_workspace_roots=legacy_workspace_roots,
            )
            normalized[child_key] = child_normalized
            changed = changed or child_changed
        return normalized, changed
    if isinstance(value, list):
        changed = False
        normalized_list: list[Any] = []
        for item in value:
            item_normalized, item_changed = _normalize_path_payload(
                item,
                key=key,
                source_root=source_root,
                target_root=target_root,
                current_workspace_root=current_workspace_root,
                legacy_workspace_roots=legacy_workspace_roots,
            )
            normalized_list.append(item_normalized)
            changed = changed or item_changed
        return normalized_list, changed
    if isinstance(value, str) and key in _PATH_KEYS:
        normalized = _resolve_live_path(
            value,
            source_root=source_root,
            target_root=target_root,
            current_workspace_root=current_workspace_root,
            legacy_workspace_roots=legacy_workspace_roots,
        )
        return normalized, normalized != value
    return value, False


def _candidate_legacy_workspace_roots(*, current_workspace_root: Path, profile: Any) -> tuple[Path, ...]:
    roots: list[Path] = []
    legacy_runtime_root = getattr(profile, "med_deepscientist_runtime_root", None)
    if legacy_runtime_root is not None:
        legacy_path = Path(legacy_runtime_root).expanduser().resolve()
        roots.extend(
            [
                legacy_path,
                legacy_path.parent,
                legacy_path.parent.parent,
            ]
        )
    current_parts = current_workspace_root.parts
    for index, part in enumerate(current_parts):
        if part == "workspace":
            roots.append(Path(*current_parts[:index], "legacy-workspace"))
            roots.append(Path(*current_parts[:index], "legacy", "workspace"))
    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        key = str(root.expanduser().resolve(strict=False))
        if key in seen:
            continue
        seen.add(key)
        unique.append(Path(key))
    return tuple(unique)


def repair_paper_live_paths(
    *,
    profile: Any,
    quest_id: str,
    workspace_root: Path,
    current_workspace_root: Path,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_current_workspace_root = Path(current_workspace_root).expanduser().resolve()
    paper_root = resolved_workspace_root / "paper"
    legacy_workspace_roots = _candidate_legacy_workspace_roots(
        current_workspace_root=resolved_current_workspace_root,
        profile=profile,
    )
    repaired_files: list[str] = []
    for relative_path in _PAPER_LIVE_PATH_SURFACES:
        path = paper_root / relative_path
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        normalized, changed = _normalize_path_payload(
            payload,
            key=None,
            source_root=paper_root,
            target_root=resolved_workspace_root,
            current_workspace_root=resolved_current_workspace_root,
            legacy_workspace_roots=legacy_workspace_roots,
        )
        if changed and isinstance(normalized, dict):
            path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            repaired_files.append(str(path))
    quest_root = Path(getattr(profile, "managed_runtime_quests_root", resolved_workspace_root.parent.parent))
    return {
        "ok": True,
        "status": "updated" if repaired_files else "current",
        "source": "mas_runtime_core",
        "external_mds_required": False,
        "quest_id": quest_id,
        "quest_root": str((quest_root / quest_id).expanduser().resolve()),
        "workspace_root": str(resolved_workspace_root),
        "current_workspace_root": str(resolved_current_workspace_root),
        "legacy_workspace_roots": [str(path) for path in legacy_workspace_roots],
        "repaired_files": repaired_files,
    }
