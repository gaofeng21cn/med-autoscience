from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import source_provenance_owner


OWNER = source_provenance_owner.OWNER
WORK_UNIT = source_provenance_owner.WORK_UNIT
BLOCKED_REASON = source_provenance_owner.BLOCKED_REASON
RESULT_RELATIVE_PATH = source_provenance_owner.RESULT_RELATIVE_PATH
TERMINAL_ROUTE_BLOCKED_REASON = "methodology_reframe_required"
TERMINAL_ROUTE_NEXT_OWNER = "decision"


def result_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RESULT_RELATIVE_PATH


def read_result(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(result_path(study_root=study_root))


def required_output_satisfied(*, study_root: Path) -> bool:
    root = Path(study_root).expanduser().resolve()
    payload = read_result(study_root=root)
    if analysis_harmonization_supersedes_result(study_root=root, result_payload=payload):
        return False
    return result_satisfies_required_output(payload)


def result_satisfies_required_output(payload: Mapping[str, Any] | None) -> bool:
    result = _mapping(payload)
    if not _matches_source_provenance_owner_result(result):
        return False
    if result.get("transport_model_provenance_recovered") is True:
        return True
    return result_is_accepted_typed_blocker(result)


def result_is_accepted_typed_blocker(payload: Mapping[str, Any] | None) -> bool:
    result = _mapping(payload)
    if not _matches_source_provenance_owner_result(result):
        return False
    if _text(result.get("status")) != "blocked":
        return False
    if _text(result.get("blocked_reason")) != BLOCKED_REASON:
        return False
    if _text(result.get("typed_blocker_owner")) != OWNER:
        return False
    typed_blocker = _mapping(result.get("typed_blocker"))
    if typed_blocker and _text(typed_blocker.get("blocker_id")) != BLOCKED_REASON:
        return False
    if not _has_current_provenance_search(result):
        return False
    return result.get("transport_model_provenance_recovered") is not True


def _has_current_provenance_search(payload: Mapping[str, Any]) -> bool:
    search = _mapping(payload.get("provenance_search"))
    if search.get("searched") is not True:
        return False
    if search.get("result_summary_acceptance_allowed") is not False:
        return False
    if search.get("substitute_refit_allowed") is not False:
        return False
    return "accepted_bundle_ref" in search


def typed_blocker_state(*, study_root: Path) -> dict[str, Any] | None:
    root = Path(study_root).expanduser().resolve()
    payload = read_result(study_root=root)
    if analysis_harmonization_supersedes_result(study_root=root, result_payload=payload):
        return None
    if not result_is_accepted_typed_blocker(payload):
        return None
    return {
        "blocked_reason": TERMINAL_ROUTE_BLOCKED_REASON,
        "source_blocked_reason": BLOCKED_REASON,
        "next_owner": TERMINAL_ROUTE_NEXT_OWNER,
        "terminal_source_provenance_blocker": True,
        "external_supervisor_required": False,
    }


def output_pending_for_result(payload: Mapping[str, Any] | None) -> bool:
    return not result_satisfies_required_output(payload)


def analysis_harmonization_supersedes_result(
    *,
    study_root: Path,
    result_payload: Mapping[str, Any] | None,
) -> bool:
    result = _mapping(result_payload)
    if not _matches_source_provenance_owner_result(result):
        return False
    root = Path(study_root).expanduser().resolve()
    analysis_path = root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    analysis = _read_json_object(analysis_path)
    route = _mapping(_mapping(analysis).get("blocking_owner_route"))
    if _text(route.get("blocked_reason")) != BLOCKED_REASON:
        return False
    if _text(route.get("next_owner")) != OWNER:
        return False
    if _text(route.get("next_work_unit")) != WORK_UNIT:
        return False
    result_mtime = _path_mtime(result_path(study_root=root))
    analysis_mtime = _path_mtime(analysis_path)
    if result_mtime is None or analysis_mtime is None:
        return False
    return analysis_mtime > result_mtime


def _matches_source_provenance_owner_result(payload: Mapping[str, Any]) -> bool:
    if _text(payload.get("surface")) != "source_provenance_owner_result":
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
    "RESULT_RELATIVE_PATH",
    "TERMINAL_ROUTE_BLOCKED_REASON",
    "TERMINAL_ROUTE_NEXT_OWNER",
    "WORK_UNIT",
    "analysis_harmonization_supersedes_result",
    "output_pending_for_result",
    "read_result",
    "required_output_satisfied",
    "result_is_accepted_typed_blocker",
    "result_path",
    "result_satisfies_required_output",
    "typed_blocker_state",
]
