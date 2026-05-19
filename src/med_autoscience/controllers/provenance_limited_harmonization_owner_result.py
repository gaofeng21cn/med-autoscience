from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import provenance_limited_harmonization_owner


OWNER = provenance_limited_harmonization_owner.OWNER
WORK_UNIT = provenance_limited_harmonization_owner.WORK_UNIT
BLOCKED_REASON = provenance_limited_harmonization_owner.BLOCKED_REASON
REBUILD_ROUTE_REQUIRED = provenance_limited_harmonization_owner.REBUILD_ROUTE_REQUIRED
RESULT_RELATIVE_PATH = provenance_limited_harmonization_owner.RESULT_RELATIVE_PATH


def result_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RESULT_RELATIVE_PATH


def read_result(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(result_path(study_root=study_root))


def required_output_satisfied(*, study_root: Path) -> bool:
    return result_satisfies_required_output(read_result(study_root=study_root))


def result_satisfies_required_output(payload: Mapping[str, Any] | None) -> bool:
    result = _mapping(payload)
    if not _matches_result(result):
        return False
    if result.get("provenance_limited_audit_completed") is True:
        return True
    return result_is_accepted_typed_blocker(result)


def result_is_accepted_typed_blocker(payload: Mapping[str, Any] | None) -> bool:
    result = _mapping(payload)
    if not _matches_result(result):
        return False
    if _text(result.get("status")) != "blocked":
        return False
    if _text(result.get("typed_blocker_owner")) != OWNER:
        return False
    typed_blocker = _mapping(result.get("typed_blocker"))
    blocker_id = _text(typed_blocker.get("blocker_id"))
    return blocker_id in {BLOCKED_REASON, REBUILD_ROUTE_REQUIRED}


def typed_blocker_state(*, study_root: Path) -> dict[str, Any] | None:
    payload = read_result(study_root=study_root)
    if not result_satisfies_required_output(payload):
        return None
    result = _mapping(payload)
    blocked_reason = _text(result.get("blocked_reason"))
    if blocked_reason is None:
        return None
    return {
        "blocked_reason": blocked_reason,
        "next_owner": _text(result.get("next_owner")) or OWNER,
        "external_supervisor_required": False,
    }


def output_pending_for_result(payload: Mapping[str, Any] | None) -> bool:
    return not result_satisfies_required_output(payload)


def controller_decision_requests_audit(*, study_root: Path) -> bool:
    return provenance_limited_harmonization_owner.controller_decision_requests_audit(study_root=study_root)


def current_controller_decision_requests_audit(*, study_root: Path) -> bool:
    root = Path(study_root).expanduser().resolve()
    decision_path = root / "artifacts" / "controller_decisions" / "latest.json"
    if not controller_decision_requests_audit(study_root=root):
        return False
    decision_mtime = _path_mtime(decision_path)
    if decision_mtime is None:
        return False
    trigger_paths = (
        root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        root / "artifacts" / "controller" / "source_provenance" / "latest.json",
    )
    return not any((mtime := _path_mtime(path)) is not None and mtime > decision_mtime for path in trigger_paths)


def _matches_result(payload: Mapping[str, Any]) -> bool:
    if _text(payload.get("surface")) != "provenance_limited_harmonization_owner_result":
        return False
    if _text(payload.get("owner")) != OWNER:
        return False
    return _text(payload.get("work_unit")) == WORK_UNIT


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _path_mtime(path: Path) -> float | None:
    try:
        return Path(path).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "BLOCKED_REASON",
    "OWNER",
    "REBUILD_ROUTE_REQUIRED",
    "RESULT_RELATIVE_PATH",
    "WORK_UNIT",
    "controller_decision_requests_audit",
    "current_controller_decision_requests_audit",
    "output_pending_for_result",
    "read_result",
    "required_output_satisfied",
    "result_is_accepted_typed_blocker",
    "result_path",
    "result_satisfies_required_output",
    "typed_blocker_state",
]
