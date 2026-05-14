from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RECOMMENDED_NEXT_ROUTE = "return_to_publication_gate_recheck"
NEXT_OWNER = "publication_gate"


def report_candidates(
    quest_root: Path,
    *,
    active_run_id: str | None = None,
) -> tuple[Path, ...]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    roots = (
        resolved_quest_root / "artifacts" / "runtime" / "work_unit_receipts",
        resolved_quest_root / "artifacts" / "write",
        resolved_quest_root / "artifacts" / "intake",
    )
    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates.extend(path for path in root.glob("*.json") if path.is_file())
    candidates = sorted(candidates, key=_mtime_ns, reverse=True)
    resolved_active_run_id = _text(active_run_id)
    if resolved_active_run_id is None:
        return tuple(candidates)
    active_run_candidates = [path for path in candidates if resolved_active_run_id in path.name]
    other_candidates = [path for path in candidates if path not in active_run_candidates]
    return tuple(active_run_candidates + other_candidates)


def read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def matches_completed_work_unit(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
    analysis_repair_authorized: bool,
) -> bool:
    if analysis_repair_authorized:
        return False
    if _text(payload.get("status")) != "completed":
        return False
    if payload.get("meaningful_artifact_delta") is not True:
        return False
    if not _payload_is_unblocked(payload):
        return False
    decision_matches = _decision_id_explicitly_matches(
        payload=payload,
        authorization_context=authorization_context,
    )
    if decision_matches and not _payload_work_unit_matches_if_present(
        payload=payload,
        authorization_context=authorization_context,
    ):
        return False
    if not decision_matches and not _report_is_current_for_authorization(
        payload=payload,
        authorization_context=authorization_context,
    ):
        return False
    if not decision_matches and not _work_unit_ids_match(
        payload=payload,
        authorization_context=authorization_context,
    ):
        return False
    return _route_target_matches_if_present(
        payload=payload,
        authorization_context=authorization_context,
    )


def normalized_result(report_payload: dict[str, Any]) -> dict[str, Any]:
    result = report_payload.get("result")
    normalized = dict(result) if isinstance(result, dict) else {}
    normalized.update(
        {
            "completed": True,
            "meaningful_artifact_delta": bool(report_payload.get("meaningful_artifact_delta")),
            "artifact_refs_count": _artifact_ref_count(report_payload.get("artifact_refs")),
            "source_refs_count": _artifact_ref_count(report_payload.get("source_refs")),
            "publication_gate_recheck_required": True,
        }
    )
    return normalized


def report_timestamp(payload: dict[str, Any]) -> str | None:
    return _timestamp_key(
        payload.get("created_at")
        or payload.get("updated_at")
        or payload.get("emitted_at")
    )


def _payload_is_unblocked(payload: dict[str, Any]) -> bool:
    if _text(payload.get("blocked_reason")) is not None:
        return False
    if payload.get("blocked") is True:
        return False
    if payload.get("quality_gate_relaxed") is True:
        return False
    route_outcome = payload.get("route_outcome")
    if isinstance(route_outcome, dict) and route_outcome.get("blocked") is True:
        return False
    if isinstance(route_outcome, dict) and route_outcome.get("quality_gate_relaxed") is True:
        return False
    for key in ("authority_boundary", "mutations_performed"):
        boundary = payload.get(key)
        if isinstance(boundary, dict) and boundary.get("quality_gate_relaxed") is True:
            return False
    return True


def _report_is_current_for_authorization(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    decision_time = _timestamp_key(authorization_context.get("decision_emitted_at"))
    if decision_time is None:
        return True
    report_time = report_timestamp(payload)
    return report_time is not None and report_time >= decision_time


def _decision_id_explicitly_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    expected = _text(authorization_context.get("decision_id"))
    if expected is None:
        return False
    observed = _text(payload.get("decision_id")) or _text(payload.get("controller_decision_id"))
    controller = payload.get("controller")
    if observed is None and isinstance(controller, dict):
        observed = _text(controller.get("decision_id")) or _text(controller.get("controller_decision_id"))
    return observed == expected


def _payload_work_unit_matches_if_present(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    observed_values = _observed_work_unit_values(payload)
    if not observed_values:
        return True
    expected_values = _expected_work_unit_values(authorization_context)
    return bool(expected_values & observed_values)


def _work_unit_ids_match(*, payload: dict[str, Any], authorization_context: dict[str, Any]) -> bool:
    return bool(
        _expected_work_unit_values(authorization_context)
        & _observed_work_unit_values(payload)
    )


def _expected_work_unit_values(authorization_context: dict[str, Any]) -> set[str]:
    next_work_unit = authorization_context.get("next_work_unit")
    next_unit_id = _text(next_work_unit.get("unit_id")) if isinstance(next_work_unit, dict) else None
    return {
        text
        for text in (
            _text(authorization_context.get("work_unit_id")),
            _text(authorization_context.get("route_key_question")),
            next_unit_id,
        )
        if text is not None
    }


def _observed_work_unit_values(payload: dict[str, Any]) -> set[str]:
    values = {
        text
        for text in (
            _text(payload.get("work_unit_id")),
            _text(payload.get("unit_id")),
            _text(payload.get("route_key_question")),
        )
        if text is not None
    }
    next_work_unit = payload.get("next_work_unit")
    if isinstance(next_work_unit, dict):
        next_unit_id = _text(next_work_unit.get("unit_id"))
        if next_unit_id is not None:
            values.add(next_unit_id)
    return values


def _route_target_matches_if_present(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    observed = _text(payload.get("route_target"))
    if observed is None:
        return True
    expected = _text(authorization_context.get("route_target"))
    return expected is not None and observed == expected


def _artifact_ref_count(value: object) -> int:
    if not isinstance(value, list):
        return 0
    return sum(1 for item in value if isinstance(item, dict) or _text(item) is not None)


def _timestamp_key(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return text


def _mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
