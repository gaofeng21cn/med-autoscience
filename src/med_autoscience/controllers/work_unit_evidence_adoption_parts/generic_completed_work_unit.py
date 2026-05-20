from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


RECOMMENDED_NEXT_ROUTE = "return_to_publication_gate_recheck"
NEXT_OWNER = "publication_gate"
CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY = "last_controller_decision_authorization"
RUNTIME_RELAY_DELIVERY_MODES = frozenset({"managed_runtime_chat", "durable_queue_fallback"})
DELIVERED_EVENT_TYPE = "delivered"
SKIPPED_DUPLICATE_EVENT_TYPE = "skipped_duplicate"


def report_candidates(
    quest_root: Path,
    *,
    active_run_id: str | None = None,
    delivered_run_ids: Iterable[str] = (),
) -> tuple[Path, ...]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_active_run_id = _text(active_run_id)
    authorized_run_ids = _unique_texts((resolved_active_run_id, *tuple(delivered_run_ids)))
    roots = (
        resolved_quest_root / "artifacts" / "runtime" / "work_unit_receipts",
        resolved_quest_root / "artifacts" / "write",
        resolved_quest_root / "artifacts" / "intake",
    )
    candidates: list[Path] = []
    turn_closeouts_root = resolved_quest_root / "artifacts" / "runtime" / "turn_closeouts"
    for run_id in authorized_run_ids:
        active_closeout = turn_closeouts_root / f"{run_id}.json"
        if active_closeout.exists():
            candidates.append(active_closeout)
    if turn_closeouts_root.exists():
        candidates.extend(
            path
            for path in turn_closeouts_root.glob("*.json")
            if path.is_file() and path not in candidates
        )
    for root in roots:
        if root.exists():
            candidates.extend(path for path in root.glob("*.json") if path.is_file())
    candidates = sorted(candidates, key=_mtime_ns, reverse=True)
    if not authorized_run_ids:
        return tuple(candidates)
    active_run_candidates = [path for path in candidates if any(run_id in path.name for run_id in authorized_run_ids)]
    other_candidates = [path for path in candidates if path not in active_run_candidates]
    return tuple(active_run_candidates + other_candidates)


def has_matching_relay_marker(
    *,
    quest_root: Path,
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    work_unit_target_context_keys: tuple[str, ...],
) -> bool:
    return _matching_relay_marker(
        quest_root=quest_root,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        work_unit_target_context_keys=work_unit_target_context_keys,
        require_active_run_match=True,
    ) is not None


def relay_run_ids_for_authorization(
    *,
    quest_root: Path,
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    work_unit_target_context_keys: tuple[str, ...],
) -> tuple[str, ...]:
    marker = _matching_relay_marker(
        quest_root=quest_root,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        work_unit_target_context_keys=work_unit_target_context_keys,
        require_active_run_match=False,
    )
    if marker is None:
        return ()
    return _unique_texts((_text(marker.get("active_run_id")),))


def _matching_relay_marker(
    *,
    quest_root: Path,
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    work_unit_target_context_keys: tuple[str, ...],
    require_active_run_match: bool,
) -> dict[str, Any] | None:
    runtime_state = read_json_mapping(Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json")
    marker = runtime_state.get(CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY)
    if not isinstance(marker, dict):
        return None
    if _text(marker.get("delivery_mode")) not in RUNTIME_RELAY_DELIVERY_MODES:
        return None
    if _text(marker.get("message_id")) is None:
        return None
    current_active_run_id = _text(active_run_id)
    marker_active_run_id = _text(marker.get("active_run_id"))
    if require_active_run_match and current_active_run_id is not None and marker_active_run_id != current_active_run_id:
        return None
    if not _target_context_matches(
        marker=marker,
        authorization_context=authorization_context,
        work_unit_target_context_keys=work_unit_target_context_keys,
    ):
        return None
    if _intent_key_matches(marker=marker, authorization_context=authorization_context):
        return marker
    if _route_marker_matches(marker=marker, authorization_context=authorization_context):
        return marker
    return None


def delivered_run_ids_for_business_key(
    *,
    events: Iterable[dict[str, Any]],
    decision_emitted_at: object,
) -> tuple[str, ...]:
    cutoff = _timestamp_key(decision_emitted_at)
    delivered_run_ids: list[str] = []
    seen: set[str] = set()
    for event in events:
        if _text(event.get("event_type")) != DELIVERED_EVENT_TYPE:
            continue
        recorded_at = _timestamp_key(event.get("recorded_at"))
        if cutoff is not None and (recorded_at is None or recorded_at < cutoff):
            continue
        payload = event.get("payload")
        active_run_id = _text(payload.get("active_run_id")) if isinstance(payload, dict) else None
        if active_run_id is None or active_run_id in seen:
            continue
        seen.add(active_run_id)
        delivered_run_ids.append(active_run_id)
    return tuple(delivered_run_ids)


def has_delivery_or_duplicate(events: Iterable[dict[str, Any]]) -> bool:
    return any(
        _text(event.get("event_type")) in {DELIVERED_EVENT_TYPE, SKIPPED_DUPLICATE_EVENT_TYPE}
        for event in events
    )


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
    active_run_id: str | None = None,
    delivered_run_ids: Iterable[str] = (),
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
    if (
        not decision_matches
        and not _work_unit_ids_match(payload=payload, authorization_context=authorization_context)
        and not _active_run_matches(payload=payload, active_run_id=active_run_id)
        and not _delivered_run_matches(payload=payload, delivered_run_ids=delivered_run_ids)
        and not _artifact_refs_match_expected_work_unit(
            payload=payload,
            authorization_context=authorization_context,
        )
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


def owner_handoff_payload(*, report_path: Path, source: str) -> dict[str, Any]:
    return {
        "reason": "completed_work_unit_evidence_adopted",
        "next_owner": NEXT_OWNER,
        "next_work_unit": None,
        "report_ref": str(report_path),
        "source": source,
    }


def is_completed_adoption_payload(payload: dict[str, Any]) -> bool:
    return _text(payload.get("status")) == "completed" and _text(payload.get("recommended_next_route")) == RECOMMENDED_NEXT_ROUTE


def _target_context_matches(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
    work_unit_target_context_keys: tuple[str, ...],
) -> bool:
    return all(
        key not in authorization_context or marker.get(key) == authorization_context.get(key)
        for key in work_unit_target_context_keys
    )


def _intent_key_matches(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    expected = _text(authorization_context.get("control_intent_key"))
    observed = _text(marker.get("control_intent_key"))
    return expected is not None and observed == expected


def _route_marker_matches(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return (
        _text(marker.get("decision_id")) == _text(authorization_context.get("decision_id"))
        and _text(marker.get("route_target")) == _text(authorization_context.get("route_target"))
        and _text(marker.get("route_key_question")) == _text(authorization_context.get("route_key_question"))
    )


def report_timestamp(payload: dict[str, Any]) -> str | None:
    return _timestamp_key(
        payload.get("created_at")
        or payload.get("updated_at")
        or payload.get("emitted_at")
        or payload.get("completed_at")
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


def _active_run_matches(*, payload: dict[str, Any], active_run_id: str | None) -> bool:
    expected = _text(active_run_id)
    if expected is None:
        return False
    return _text(payload.get("run_id")) == expected or _text(payload.get("active_run_id")) == expected


def _delivered_run_matches(*, payload: dict[str, Any], delivered_run_ids: Iterable[str]) -> bool:
    delivered = set(_unique_texts(delivered_run_ids))
    if not delivered:
        return False
    return _text(payload.get("run_id")) in delivered or _text(payload.get("active_run_id")) in delivered


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


def _artifact_refs_match_expected_work_unit(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    expected_values = _expected_work_unit_values(authorization_context)
    if "manuscript_story_repair" not in expected_values:
        return False
    refs = _artifact_ref_texts(payload.get("artifact_refs"))
    return any(ref.endswith("paper/draft.md") for ref in refs) and any(
        ref.endswith("paper/build/review_manuscript.md") for ref in refs
    )


def _artifact_ref_texts(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    refs: list[str] = []
    for item in value:
        if isinstance(item, dict):
            text = _text(item.get("path") or item.get("artifact_path"))
        else:
            text = _text(item)
        if text is not None:
            refs.append(text)
    return tuple(refs)


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


def _unique_texts(values: Iterable[object]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)
