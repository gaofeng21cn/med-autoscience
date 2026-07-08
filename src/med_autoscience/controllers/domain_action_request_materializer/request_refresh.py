from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_action_request_lifecycle

from . import materializer_core


def ai_reviewer_request_refresh(
    *,
    study_root: Path,
    study_id: str,
    apply: bool,
) -> dict[str, Any] | None:
    request_path = domain_action_request_lifecycle.stable_ai_reviewer_request_path(study_root=study_root)
    packet = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root)
    if packet is None:
        return None
    refreshed = domain_action_request_lifecycle.ai_reviewer_request_with_latest_record(
        study_root=study_root,
        packet=packet,
    )
    changed = refreshed != packet
    if apply and changed:
        write_json(request_path, refreshed)
    return {
        "surface": "ai_reviewer_request_refresh",
        "schema_version": 1,
        "study_id": study_id,
        "request_path": str(request_path),
        "refresh_status": "refreshed" if changed else "unchanged",
        "written": bool(apply and changed),
        "publication_eval_record_ref": materializer_core.text(refreshed.get("publication_eval_record_ref")),
        "attached_eval_id": materializer_core.text(
            materializer_core.mapping(refreshed.get("ai_reviewer_record")).get("eval_id")
        ),
        "blocked_reason": materializer_core.text(
            materializer_core.mapping(refreshed.get("request_lifecycle")).get("blocked_reason")
        ),
    }


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


__all__ = [
    "ai_reviewer_request_refresh",
    "read_json_object",
    "write_json",
]
