from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_FILENAME = "MEDICAL_FORK_MANIFEST.json"
CONTROLLED_ENGINE_IDS = frozenset({"medicaldeepscientist", "med-deepscientist"})
CONTROLLED_ENGINE_FAMILIES = frozenset({"MedicalDeepScientist", "MedDeepScientist"})


def _normalize_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_commits(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    normalized: list[str] = []
    for item in value:
        commit = None
        if isinstance(item, dict):
            commit = _normalize_string(item.get("commit"))
        else:
            commit = _normalize_string(item)
        if commit:
            normalized.append(commit)
    return tuple(normalized)


def inspect_med_deepscientist_repo_manifest(repo_root: Path | str | None) -> dict[str, Any]:
    manifest_path: Path | None = None
    if repo_root is not None:
        manifest_path = (Path(repo_root).expanduser() / MANIFEST_FILENAME).resolve(strict=False)

    result: dict[str, Any] = {
        "manifest_path": str(manifest_path) if manifest_path is not None else None,
        "manifest_found": False,
        "manifest_parsable": False,
        "manifest_payload": None,
        "engine_family": None,
        "freeze_base_commit": None,
        "applied_commits": (),
        "is_controlled_fork": False,
        "upstream_remote_name": None,
        "upstream_branch": None,
        "upstream_ref": None,
        "checks": {
            "manifest_file_exists": False,
            "manifest_payload_is_mapping": False,
        },
        "issues": [],
    }

    if manifest_path is None:
        return result

    if not manifest_path.is_file():
        return result

    result["manifest_found"] = True
    result["checks"]["manifest_file_exists"] = True

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        result["issues"].append(f"manifest_parse_failed:{error}")
        return result

    result["manifest_parsable"] = True

    if not isinstance(payload, dict):
        result["issues"].append("manifest_payload_not_mapping")
        return result

    result["checks"]["manifest_payload_is_mapping"] = True
    result["manifest_payload"] = dict(payload)

    engine_family = _normalize_string(payload.get("engine_family"))
    if engine_family:
        result["engine_family"] = engine_family

    engine_id = _normalize_string(payload.get("engine_id"))

    freeze_base_commit = _normalize_string(payload.get("freeze_base_commit"))
    if not freeze_base_commit:
        upstream_source = payload.get("upstream_source")
        if isinstance(upstream_source, dict):
            freeze_base_commit = _normalize_string(upstream_source.get("base_commit"))
    if freeze_base_commit:
        result["freeze_base_commit"] = freeze_base_commit

    result["applied_commits"] = _normalize_commits(payload.get("applied_commits"))

    upstream_tracking = payload.get("upstream_tracking")
    if isinstance(upstream_tracking, dict):
        upstream_remote_name = _normalize_string(upstream_tracking.get("remote_name"))
        upstream_branch = _normalize_string(upstream_tracking.get("branch"))
        upstream_ref = _normalize_string(upstream_tracking.get("ref"))
        if upstream_remote_name:
            result["upstream_remote_name"] = upstream_remote_name
        if upstream_branch:
            result["upstream_branch"] = upstream_branch
        if upstream_ref:
            result["upstream_ref"] = upstream_ref

    is_controlled = payload.get("is_controlled_fork")
    if isinstance(is_controlled, bool):
        result["is_controlled_fork"] = is_controlled
    elif engine_id in CONTROLLED_ENGINE_IDS or result["engine_family"] in CONTROLLED_ENGINE_FAMILIES:
        result["is_controlled_fork"] = True

    return result
