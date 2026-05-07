from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent


_ANALYSIS_REPAIR_WORK_UNIT_ID = "analysis_claim_evidence_repair"
_ANALYSIS_REPAIR_ROUTE_TARGET = "analysis-campaign"
_ANALYSIS_REPAIR_ACTION = "run_quality_repair_batch"
_ANALYSIS_REPAIR_REPORT_TYPE = "analysis_claim_evidence_repair_specificity_target_traceability_reaudit"
_ANALYSIS_REPAIR_REPORT_SUFFIX = Path(
    "artifacts",
    "reports",
    "analysis_claim_evidence_repair",
    "specificity_target_traceability_reaudit.json",
)
_ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE = "return_to_publication_gate_recheck"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _int_value(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _report_candidates(quest_root: Path) -> tuple[Path, ...]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    current = resolved_quest_root / _ANALYSIS_REPAIR_REPORT_SUFFIX
    candidates = [current]
    history_root = resolved_quest_root / ".ds" / "cold_archive" / "report_history"
    if history_root.exists():
        candidates.extend(
            sorted(
                path
                for path in history_root.rglob(_ANALYSIS_REPAIR_REPORT_SUFFIX.name)
                if path.match(f"*/{_ANALYSIS_REPAIR_REPORT_SUFFIX.as_posix()}")
            )
        )
    return tuple(candidates)


def _authorization_matches_analysis_repair(authorization_context: dict[str, Any]) -> bool:
    actions = {
        str(action).strip()
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    }
    return (
        _text(authorization_context.get("work_unit_id")) == _ANALYSIS_REPAIR_WORK_UNIT_ID
        and _text(authorization_context.get("route_target")) == _ANALYSIS_REPAIR_ROUTE_TARGET
        and _ANALYSIS_REPAIR_ACTION in actions
    )


def _report_matches_analysis_repair(payload: dict[str, Any]) -> bool:
    result = payload.get("result")
    if not isinstance(result, dict):
        return False
    explicit_work_unit_id = _text(payload.get("work_unit_id"))
    explicit_route_target = _text(payload.get("route_target"))
    explicit_action = _text(payload.get("action"))
    explicit_report_type = _text(payload.get("report_type"))
    if explicit_work_unit_id is not None and explicit_work_unit_id != _ANALYSIS_REPAIR_WORK_UNIT_ID:
        return False
    if explicit_route_target is not None and explicit_route_target != _ANALYSIS_REPAIR_ROUTE_TARGET:
        return False
    if explicit_action is not None and explicit_action != _ANALYSIS_REPAIR_ACTION:
        return False
    has_legacy_report_identity = explicit_report_type == _ANALYSIS_REPAIR_REPORT_TYPE
    has_explicit_report_identity = (
        explicit_work_unit_id == _ANALYSIS_REPAIR_WORK_UNIT_ID
        and explicit_route_target == _ANALYSIS_REPAIR_ROUTE_TARGET
        and explicit_action == _ANALYSIS_REPAIR_ACTION
    )
    return (
        (has_legacy_report_identity or has_explicit_report_identity)
        and result.get("local_traceability_repair_complete") is True
        and _int_value(result.get("unresolved_local_defect_count")) == 0
        and _int_value(result.get("gate_owned_or_nonlocal_defect_count")) == 0
        and _text(result.get("recommended_next_route")) == _ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE
    )


def _existing_artifact_written_payload(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
) -> dict[str, Any] | None:
    for event in control_intent.events_for_business_key(
        study_root=study_root,
        business_key=identity.business_key,
    ):
        if _text(event.get("event_type")) != "artifact_written":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict):
            return dict(payload)
        return {}
    return None


def _has_prior_delivery_or_duplicate(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
) -> bool:
    return any(
        _text(event.get("event_type")) in {"delivered", "skipped_duplicate"}
        for event in control_intent.events_for_business_key(
            study_root=study_root,
            business_key=identity.business_key,
        )
    )


def adopt_controller_work_unit_evidence_if_present(
    *,
    study_root: Path,
    quest_root: Path,
    authorization_context: dict[str, Any],
    identity: control_intent.ControlIntentIdentity,
    active_run_id: str | None,
    source: str,
) -> dict[str, Any] | None:
    if not _authorization_matches_analysis_repair(authorization_context):
        return None
    existing_payload = _existing_artifact_written_payload(study_root=study_root, identity=identity)
    if existing_payload is not None:
        return {
            **existing_payload,
            "already_recorded": True,
        }
    if not _has_prior_delivery_or_duplicate(study_root=study_root, identity=identity):
        return None
    for report_path in _report_candidates(quest_root):
        if not report_path.exists():
            continue
        report_payload = _read_json_mapping(report_path)
        if not _report_matches_analysis_repair(report_payload):
            continue
        result = dict(report_payload.get("result") or {})
        payload = {
            "active_run_id": active_run_id,
            "report_ref": str(report_path),
            "created_at": _text(report_payload.get("created_at") or report_payload.get("emitted_at")),
            "work_unit_id": _ANALYSIS_REPAIR_WORK_UNIT_ID,
            "route_target": _ANALYSIS_REPAIR_ROUTE_TARGET,
            "recommended_next_route": _ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE,
            "source": source,
            "result": {
                "local_traceability_repair_complete": True,
                "unresolved_local_defect_count": int(result.get("unresolved_local_defect_count") or 0),
                "gate_owned_or_nonlocal_defect_count": int(result.get("gate_owned_or_nonlocal_defect_count") or 0),
            },
        }
        control_intent.append_event(
            study_root=study_root,
            identity=identity,
            event_type="artifact_written",
            payload=payload,
        )
        return payload
    return None
