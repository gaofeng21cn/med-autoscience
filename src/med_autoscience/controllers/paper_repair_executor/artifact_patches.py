from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import paper_authority_migration


def has_structured_patch(work_unit: Mapping[str, Any]) -> bool:
    patch = _mapping(work_unit.get("canonical_patch"))
    if _text(patch.get("replacement_text")):
        return True
    if _text(patch.get("append_text")):
        return True
    return bool(_text(work_unit.get("replacement_text")) or _text(work_unit.get("append_text")))


def apply_structured_patch(*, existing: str, work_unit: Mapping[str, Any]) -> str:
    patch = _mapping(work_unit.get("canonical_patch"))
    replacement_text = _text(patch.get("replacement_text")) or _text(work_unit.get("replacement_text"))
    append_text = _text(patch.get("append_text")) or _text(work_unit.get("append_text"))
    target_text = _text(patch.get("target_text")) or _text(work_unit.get("target_text"))
    target_claim = _text(work_unit.get("target_claim"))
    if replacement_text and target_text and target_text in existing:
        return existing.replace(target_text, replacement_text)
    if replacement_text and target_claim and target_claim in existing:
        return existing.replace(target_claim, replacement_text)
    if append_text:
        return existing.rstrip() + f"\n\n{append_text}\n"
    if replacement_text:
        return existing.rstrip() + f"\n\n{replacement_text}\n"
    return existing


def apply_json_artifact_patches(*, study_root: Path, work_unit: Mapping[str, Any]) -> list[Path]:
    changed: list[Path] = []
    for patch in _json_artifact_patch_items(work_unit):
        path = _json_artifact_patch_path(study_root=study_root, patch=patch)
        payload = read_json(path)
        updated = False
        for update in _json_artifact_patch_updates(patch):
            if _apply_json_path_update(payload, update):
                updated = True
        if updated:
            write_json(path, payload)
            changed.append(path)
    return changed


def apply_text_artifact_patches(*, study_root: Path, work_unit: Mapping[str, Any]) -> list[Path]:
    changed: list[Path] = []
    for patch in _text_artifact_patch_items(work_unit):
        path = _text_artifact_patch_path(study_root=study_root, patch=patch)
        existing = path.read_text(encoding="utf-8")
        updated = _apply_text_artifact_patch(existing=existing, patch=patch)
        if updated != existing:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(updated if updated.endswith("\n") else updated + "\n", encoding="utf-8")
            changed.append(path)
    return changed


def json_artifact_patch_blocker(work_unit: Mapping[str, Any]) -> str | None:
    for patch in _json_artifact_patch_items(work_unit):
        relative_path = _text(patch.get("relative_path"))
        if relative_path is None:
            return "json_artifact_patch_relative_path_missing"
        if not _json_artifact_patch_relative_path_allowed(relative_path):
            return "json_artifact_patch_path_not_allowed"
        if not _json_artifact_patch_updates(patch):
            return "json_artifact_patch_updates_missing"
        for update in _json_artifact_patch_updates(patch):
            if not _json_path(update.get("path")):
                return "json_artifact_patch_update_path_missing"
            if "value" not in update:
                return "json_artifact_patch_update_value_missing"
    return None


def text_artifact_patch_blocker(work_unit: Mapping[str, Any]) -> str | None:
    for patch in _text_artifact_patch_items(work_unit):
        relative_path = _text(patch.get("relative_path"))
        if relative_path is None:
            return "text_artifact_patch_relative_path_missing"
        if not _text_artifact_patch_relative_path_allowed(relative_path):
            return "text_artifact_patch_path_not_allowed"
        replacement_text = _text(patch.get("replacement_text"))
        append_text = _text(patch.get("append_text"))
        if not replacement_text and not append_text:
            return "text_artifact_patch_update_missing"
    return None


def active_paper_root(study_root: Path) -> Path:
    resolved_study_root = Path(study_root).expanduser().resolve()
    stage_native_root = paper_authority_migration.stage_native_body_authority_root(
        study_root=resolved_study_root
    )
    stage_native_paper_root = stage_native_root / "paper"
    if _paper_surface_exists(stage_native_paper_root) or (
        stage_native_root / "paper_authority_receipt.json"
    ).exists():
        return stage_native_paper_root.resolve()
    return (resolved_study_root / "paper").resolve()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _json_artifact_patch_items(work_unit: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    patches = work_unit.get("json_artifact_patches")
    if not isinstance(patches, list):
        return []
    return [patch for patch in patches if isinstance(patch, Mapping)]


def _text_artifact_patch_items(work_unit: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    patches = work_unit.get("text_artifact_patches")
    if not isinstance(patches, list):
        return []
    return [patch for patch in patches if isinstance(patch, Mapping)]


def _json_artifact_patch_updates(patch: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    updates = patch.get("updates")
    if not isinstance(updates, list):
        return []
    return [update for update in updates if isinstance(update, Mapping)]


def _json_artifact_patch_path(*, study_root: Path, patch: Mapping[str, Any]) -> Path:
    relative_path = _text(patch.get("relative_path"))
    if relative_path is None or not _json_artifact_patch_relative_path_allowed(relative_path):
        raise ValueError("json artifact patch path is not allowed")
    paper_relative_path = Path(relative_path).relative_to("paper")
    return (active_paper_root(study_root) / paper_relative_path).resolve()


def _text_artifact_patch_path(*, study_root: Path, patch: Mapping[str, Any]) -> Path:
    relative_path = _text(patch.get("relative_path"))
    if relative_path is None or not _text_artifact_patch_relative_path_allowed(relative_path):
        raise ValueError("text artifact patch path is not allowed")
    paper_relative_path = Path(relative_path).relative_to("paper")
    return (active_paper_root(study_root) / paper_relative_path).resolve()


def _json_artifact_patch_relative_path_allowed(relative_path: str) -> bool:
    path = Path(relative_path)
    parts = path.parts
    return (
        not path.is_absolute()
        and ".." not in parts
        and len(parts) >= 2
        and parts[0] == "paper"
        and "current_package" not in parts
        and path.suffix == ".json"
    )


def _text_artifact_patch_relative_path_allowed(relative_path: str) -> bool:
    path = Path(relative_path)
    parts = path.parts
    return (
        not path.is_absolute()
        and ".." not in parts
        and len(parts) >= 2
        and parts[0] == "paper"
        and "current_package" not in parts
        and path.suffix in {".md", ".csv", ".txt"}
    )


def _apply_text_artifact_patch(*, existing: str, patch: Mapping[str, Any]) -> str:
    target_text = _text(patch.get("target_text"))
    replacement_text = _text(patch.get("replacement_text"))
    append_text = _text(patch.get("append_text"))
    if replacement_text and target_text and target_text in existing:
        return existing.replace(target_text, replacement_text)
    if append_text:
        return existing.rstrip() + f"\n\n{append_text}\n"
    if replacement_text and not target_text:
        return existing.rstrip() + f"\n\n{replacement_text}\n"
    return existing


def _apply_json_path_update(payload: dict[str, Any], update: Mapping[str, Any]) -> bool:
    path = _json_path(update.get("path"))
    if not path:
        return False
    cursor: Any = payload
    for token in path[:-1]:
        cursor = _json_child(cursor, token)
        if cursor is None:
            return False
    final = path[-1]
    if isinstance(cursor, list) and isinstance(final, int) and 0 <= final < len(cursor):
        if cursor[final] == update.get("value"):
            return False
        cursor[final] = update.get("value")
        return True
    if isinstance(cursor, dict) and isinstance(final, str):
        if cursor.get(final) == update.get("value"):
            return False
        cursor[final] = update.get("value")
        return True
    return False


def _json_child(value: Any, token: str | int) -> Any | None:
    if isinstance(value, list) and isinstance(token, int) and 0 <= token < len(value):
        return value[token]
    if isinstance(value, dict) and isinstance(token, str):
        return value.get(token)
    return None


def _json_path(value: object) -> list[str | int]:
    if not isinstance(value, list):
        return []
    result: list[str | int] = []
    for item in value:
        if isinstance(item, int):
            result.append(item)
        elif isinstance(item, str) and item:
            result.append(item)
        else:
            return []
    return result


def _paper_surface_exists(paper_root: Path) -> bool:
    return any(
        (paper_root / relative_path).exists()
        for relative_path in (
            "draft.md",
            "manuscript.md",
            "claim_evidence_map.json",
            "evidence_ledger.json",
            "review/review_ledger.json",
        )
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
