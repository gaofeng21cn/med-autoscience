from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any


def _same_ref_path(left: str | None, right: str | None) -> bool:
    left_text = _strip_ref_fragment(left)
    right_text = _strip_ref_fragment(right)
    if left_text is None or right_text is None:
        return False
    if left_text == right_text:
        return True
    left_path = Path(left_text)
    right_path = Path(right_text)
    if left_path.is_absolute() and not right_path.is_absolute():
        return left_text.endswith(f"/{right_text}")
    if right_path.is_absolute() and not left_path.is_absolute():
        return right_text.endswith(f"/{left_text}")
    return False


def _read_closeout_ref(progress: Mapping[str, Any], ref: str) -> dict[str, Any]:
    path_text = _strip_ref_fragment(ref)
    if path_text is None:
        return {}
    for path in _candidate_ref_paths(progress, path_text):
        payload = _read_json_object(path)
        if payload:
            return payload
    return {}


def _candidate_ref_paths(progress: Mapping[str, Any], path_text: str) -> list[Path]:
    ref_path = Path(path_text).expanduser()
    if ref_path.is_absolute():
        return [ref_path]
    candidates: list[Path] = []
    workspace_root = _path(progress.get("workspace_root"))
    study_root = _path(progress.get("study_root"))
    if workspace_root is not None:
        candidates.append(workspace_root / ref_path)
    if study_root is not None:
        candidates.append(study_root / ref_path)
        study_id = _text(progress.get("study_id"))
        if study_id:
            prefix = f"studies/{study_id}/"
            if path_text.startswith(prefix):
                candidates.append(study_root / path_text.removeprefix(prefix))
        if study_root.name and path_text.startswith(f"{study_root.name}/"):
            candidates.append(study_root.parent / ref_path)
    return _dedupe_paths(candidates)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, NotADirectoryError, OSError, json.JSONDecodeError):
        return {}
    return _mapping(payload)


def _strip_ref_fragment(ref: str | None) -> str | None:
    text = _text(ref)
    if text is None:
        return None
    return text.split("#", 1)[0]


def _path(value: object) -> Path | None:
    text = _text(value)
    return Path(text).expanduser() if text is not None else None


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _dedupe(values: list[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
