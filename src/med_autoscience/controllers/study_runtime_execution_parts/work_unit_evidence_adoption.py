from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent
from med_autoscience.controllers.work_unit_evidence_adoption_parts import (
    analysis_claim_evidence_repair_receipt,
    analysis_stage_memory_handoff,
    generic_completed_work_unit,
    hard_methodology_unit_harmonization,
)


_ANALYSIS_REPAIR_WORK_UNIT_ID = "analysis_claim_evidence_repair"
_ANALYSIS_REPAIR_WORK_UNIT_IDS = frozenset(
    {
        _ANALYSIS_REPAIR_WORK_UNIT_ID,
        "medical_prose_quality_analysis_source_documentation_repair",
    }
)
_ANALYSIS_REPAIR_ROUTE_TARGET = "analysis-campaign"
_ANALYSIS_REPAIR_ACTION = "run_quality_repair_batch"
_ANALYSIS_REPAIR_REPORT_TYPE = "analysis_claim_evidence_repair_specificity_target_traceability_reaudit"
_ANALYSIS_REPAIR_BATCH_REPORT_TYPE = "analysis_claim_evidence_repair"
_ANALYSIS_REPAIR_REPORT_SUFFIX = Path(
    "artifacts",
    "reports",
    "analysis_claim_evidence_repair",
    "specificity_target_traceability_reaudit.json",
)
_ANALYSIS_REPAIR_LATEST_REPORT_SUFFIX = Path("artifacts", "reports", "analysis_claim_evidence_repair", "latest.json")
_MAS_QUALITY_REPAIR_REPORT_SUFFIX = Path("artifacts", "reports", "mas_quality_repair", "latest.json")
_CONTROLLER_CONSUMPTION_REPORT_SUFFIX = Path("artifacts", "supervision", "controller_consumption", "latest.json")
_MAS_QUALITY_REPAIR_REPORT_TYPE = "mas_quality_repair_batch"
_ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE = "return_to_publication_gate_recheck"
_ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE = "analysis_claim_evidence_current_run_handoff"
_ANALYSIS_REPAIR_HANDOFF_STATUS = "exhausted_for_current_fingerprint"
_ANALYSIS_REPAIR_HANDOFF_NEXT_ROUTE = "handoff_to_next_owner"
_ANALYSIS_REPAIR_CONTROL_PACKET_KIND = "analysis_claim_evidence_current_run_repair_control_packet"
_ANALYSIS_REPAIR_CONTROL_PACKET_STATUS = "completed_as_current_run_repair_control_packet"
_ANALYSIS_REPAIR_SOURCE_REPAIR_KIND = "analysis_claim_evidence_source_repair"
_ANALYSIS_REPAIR_SOURCE_REPAIR_STATUS = "completed"
_ANALYSIS_REPAIR_RETRY_BACKOFF_HANDOFF_REPORT_TYPE = "analysis_claim_evidence_retry_backoff_dedupe_handoff"
_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY = "last_controller_decision_authorization"
_WORK_UNIT_TARGET_CONTEXT_KEYS = (
    "specificity_targets",
    "work_unit_targets",
    "blocking_artifact_refs",
    "blocker_details",
    "gate_blocker_details",
    "gaps",
    "source_path",
)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _is_analysis_repair_work_unit_id(value: object) -> bool:
    return _text(value) in _ANALYSIS_REPAIR_WORK_UNIT_IDS


def _authorization_analysis_repair_work_unit_id(authorization_context: dict[str, Any]) -> str:
    work_unit_id = _text(authorization_context.get("work_unit_id"))
    return work_unit_id if work_unit_id in _ANALYSIS_REPAIR_WORK_UNIT_IDS else _ANALYSIS_REPAIR_WORK_UNIT_ID


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _write_json_mapping(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _int_value(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _timestamp_key(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return text


def _report_timestamp(payload: dict[str, Any]) -> str | None:
    return _timestamp_key(
        payload.get("created_at")
        or payload.get("updated_at")
        or payload.get("emitted_at")
    )


def _report_is_current_for_authorization(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    decision_time = _timestamp_key(authorization_context.get("decision_emitted_at"))
    if decision_time is None:
        return True
    report_time = _report_timestamp(payload)
    if report_time is None:
        return True
    return report_time >= decision_time


def _stage_memory_closeout_candidates(
    *,
    quest_root: Path,
    active_run_id: str | None,
) -> tuple[Path, ...]:
    return analysis_stage_memory_handoff.closeout_candidates(
        quest_root=quest_root,
        active_run_id=active_run_id,
    )


def _report_candidates(quest_root: Path, *, active_run_id: str | None = None) -> tuple[Path, ...]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    candidates = [
        resolved_quest_root / _ANALYSIS_REPAIR_REPORT_SUFFIX,
        resolved_quest_root / _ANALYSIS_REPAIR_LATEST_REPORT_SUFFIX,
        resolved_quest_root / _MAS_QUALITY_REPAIR_REPORT_SUFFIX,
        resolved_quest_root / _CONTROLLER_CONSUMPTION_REPORT_SUFFIX,
    ]
    candidates.extend(
        _stage_memory_closeout_candidates(
            quest_root=resolved_quest_root,
            active_run_id=active_run_id,
        )
    )
    history_root = resolved_quest_root / ".ds" / "cold_archive" / "report_history"
    if history_root.exists():
        candidates.extend(
            sorted(
                path
                for path in history_root.rglob(_ANALYSIS_REPAIR_REPORT_SUFFIX.name)
                if path.match(f"*/{_ANALYSIS_REPAIR_REPORT_SUFFIX.as_posix()}")
            )
        )
        report_store = history_root / "artifacts" / "reports"
        if report_store.exists():
            candidates.extend(sorted(report_store.glob("report-*.json")))
    return tuple(candidates)


def _authorization_matches_analysis_repair(authorization_context: dict[str, Any]) -> bool:
    actions = {
        str(action).strip()
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    }
    return (
        _is_analysis_repair_work_unit_id(authorization_context.get("work_unit_id"))
        and _text(authorization_context.get("route_target")) == _ANALYSIS_REPAIR_ROUTE_TARGET
        and _ANALYSIS_REPAIR_ACTION in actions
    )


def _work_unit_fingerprint_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    expected = _text(authorization_context.get("work_unit_fingerprint"))
    controller = payload.get("controller")
    observed = _text(payload.get("work_unit_fingerprint"))
    if observed is None and isinstance(controller, dict):
        observed = _text(controller.get("work_unit_fingerprint"))
    return expected is None or observed == expected


def _work_unit_fingerprint_explicitly_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    expected = _text(authorization_context.get("work_unit_fingerprint"))
    if expected is None:
        return False
    controller = payload.get("controller")
    observed = _text(payload.get("work_unit_fingerprint"))
    if observed is None and isinstance(controller, dict):
        observed = _text(controller.get("work_unit_fingerprint"))
    return observed == expected


def _is_analysis_repair_stage_memory_handoff(payload: dict[str, Any]) -> bool:
    return analysis_stage_memory_handoff.is_handoff(payload)


def _normalize_report_payload(
    payload: dict[str, Any],
    *,
    authorization_context: dict[str, Any],
) -> dict[str, Any]:
    if _is_analysis_repair_stage_memory_handoff(payload):
        return analysis_stage_memory_handoff.normalize_payload(
            payload,
            authorization_context=authorization_context,
            analysis_repair_work_unit_id=_authorization_analysis_repair_work_unit_id(authorization_context),
            handoff_report_type=_ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE,
            handoff_status=_ANALYSIS_REPAIR_HANDOFF_STATUS,
        )
    return payload


def _specificity_target_count(authorization_context: dict[str, Any]) -> int:
    targets = authorization_context.get("specificity_targets")
    if not isinstance(targets, list):
        return 0
    return sum(1 for item in targets if isinstance(item, dict))


def _authorization_has_hard_methodology_target(authorization_context: dict[str, Any]) -> bool:
    return hard_methodology_unit_harmonization.authorization_has_target(
        authorization_context,
        text=_text,
    )


def _hard_methodology_report_satisfies_authorization(payload: dict[str, Any]) -> bool:
    return hard_methodology_unit_harmonization.report_satisfies_authorization(
        payload,
        report_next_work_unit=_report_next_work_unit,
        text=_text,
    )


def _mas_quality_repair_metrics_are_complete(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    metrics = payload.get("metrics_summary")
    if not isinstance(metrics, dict):
        return False
    target_count = _specificity_target_count(authorization_context)
    repaired = _int_value(metrics.get("specificity_targets_repaired_or_classified"))
    missing = _int_value(metrics.get("missing_target_files_after_repair"))
    markers = _int_value(metrics.get("targets_with_repair_markers"))
    if missing != 0:
        return False
    if target_count > 0:
        return repaired == target_count and markers == target_count
    return (repaired or 0) > 0 and (markers or 0) > 0


def _mas_quality_repair_specificity_targets_are_complete(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    targets = payload.get("specificity_targets")
    if not isinstance(targets, list):
        return False
    target_payloads = [item for item in targets if isinstance(item, dict)]
    if len(target_payloads) != len(targets):
        return False
    target_count = _specificity_target_count(authorization_context)
    if target_count > 0 and len(target_payloads) < target_count:
        return False
    if target_count == 0 and not target_payloads:
        return False
    return all(
        _text(item.get("target_id")) is not None and _text(item.get("status")) is not None
        for item in target_payloads
    )


def _mas_quality_repair_report_is_current(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return _report_is_current_for_authorization(
        payload=payload,
        authorization_context=authorization_context,
    ) or _work_unit_fingerprint_explicitly_matches(
        payload=payload,
        authorization_context=authorization_context,
    )


def _handoff_report_is_current(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return _report_is_current_for_authorization(
        payload=payload,
        authorization_context=authorization_context,
    ) or _work_unit_fingerprint_explicitly_matches(
        payload=payload,
        authorization_context=authorization_context,
    )


def _controller_field(payload: dict[str, Any], key: str) -> str | None:
    controller = payload.get("controller")
    if not isinstance(controller, dict):
        return None
    return _text(controller.get(key))


def _is_analysis_repair_exhausted_handoff(payload: dict[str, Any]) -> bool:
    return (
        _text(payload.get("repair_packet_type"))
        in {
            _ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE,
            _ANALYSIS_REPAIR_RETRY_BACKOFF_HANDOFF_REPORT_TYPE,
        }
        or _text(payload.get("report_type"))
        in {
            _ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE,
            _ANALYSIS_REPAIR_RETRY_BACKOFF_HANDOFF_REPORT_TYPE,
        }
    ) and _text(payload.get("analysis_lane_status")) == _ANALYSIS_REPAIR_HANDOFF_STATUS


def _is_analysis_repair_current_run_control_packet(payload: dict[str, Any]) -> bool:
    return (
        _text(payload.get("artifact_kind")) == _ANALYSIS_REPAIR_CONTROL_PACKET_KIND
        and _text(payload.get("status")) == _ANALYSIS_REPAIR_CONTROL_PACKET_STATUS
    )


def _is_analysis_repair_source_repair_packet(payload: dict[str, Any]) -> bool:
    return (
        _text(payload.get("artifact_kind")) == _ANALYSIS_REPAIR_SOURCE_REPAIR_KIND
        and _text(payload.get("status")) == _ANALYSIS_REPAIR_SOURCE_REPAIR_STATUS
    )


def _specificity_target_results_are_complete(payload: dict[str, Any]) -> bool:
    targets = payload.get("specificity_target_results")
    if not isinstance(targets, list):
        return False
    target_payloads = [item for item in targets if isinstance(item, dict)]
    if len(target_payloads) != len(targets):
        return False
    return bool(target_payloads) and all(
        _text(item.get("target_id")) is not None
        and (_text(item.get("status")) is not None or _text(item.get("result")) is not None)
        for item in target_payloads
    )


def _source_repairs_are_complete(payload: dict[str, Any]) -> bool:
    repairs = payload.get("source_repairs")
    if not isinstance(repairs, list):
        return False
    repair_payloads = [item for item in repairs if isinstance(item, dict)]
    return bool(repair_payloads) and len(repair_payloads) == len(repairs) and all(
        _text(item.get("path")) is not None for item in repair_payloads
    )


def _analysis_repair_source_repair_packet_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return (
        _is_analysis_repair_source_repair_packet(payload)
        and _is_analysis_repair_work_unit_id(payload.get("work_unit_id"))
        and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
        and _mas_quality_repair_report_is_current(
            payload=payload,
            authorization_context=authorization_context,
        )
        and payload.get("meaningful_artifact_delta") is True
        and _specificity_target_results_are_complete(payload)
        and _source_repairs_are_complete(payload)
    )


def _analysis_repair_batch_report_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    if _text(payload.get("report_type")) != _ANALYSIS_REPAIR_BATCH_REPORT_TYPE:
        return False
    repair_counts = payload.get("repair_counts")
    if not isinstance(repair_counts, dict):
        return False
    return (
        _is_analysis_repair_work_unit_id(_controller_field(payload, "active_work_unit_id"))
        and _controller_field(payload, "route_target") == _ANALYSIS_REPAIR_ROUTE_TARGET
        and _ANALYSIS_REPAIR_ACTION in (_controller_field(payload, "controller_actions") or "")
        and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
        and _mas_quality_repair_report_is_current(
            payload=payload,
            authorization_context=authorization_context,
        )
        and _int_value(repair_counts.get("unresolved_local_defect_count")) == 0
        and _int_value(repair_counts.get("gate_owned_or_nonlocal_defect_count")) == 0
        and _text(payload.get("recommended_next_route")) == _ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE
    )


def _report_matches_analysis_repair(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    hard_methodology_target = _authorization_has_hard_methodology_target(authorization_context)
    result = payload.get("result")
    explicit_work_unit_id = _text(payload.get("work_unit_id"))
    explicit_route_target = _text(payload.get("route_target"))
    explicit_action = _text(payload.get("action"))
    explicit_report_type = _text(payload.get("report_type"))
    explicit_report_kind = _text(payload.get("report_kind"))
    if _is_analysis_repair_exhausted_handoff(payload):
        return (
            _is_analysis_repair_work_unit_id(explicit_work_unit_id)
            and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
            and _text(payload.get("next_owner")) is not None
            and _text(payload.get("next_work_unit")) is not None
            and (not hard_methodology_target or _hard_methodology_report_satisfies_authorization(payload))
            and _handoff_report_is_current(
                payload=payload,
                authorization_context=authorization_context,
            )
        )
    if hard_methodology_target:
        return False
    if _is_analysis_repair_current_run_control_packet(payload):
        return (
            _is_analysis_repair_work_unit_id(explicit_work_unit_id)
            and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
            and _specificity_target_results_are_complete(payload)
            and _mas_quality_repair_report_is_current(
                payload=payload,
                authorization_context=authorization_context,
            )
        )
    if _analysis_repair_source_repair_packet_matches(
        payload=payload,
        authorization_context=authorization_context,
    ):
        return True
    if analysis_claim_evidence_repair_receipt.matches(
        payload=payload,
        authorization_context=authorization_context,
        is_analysis_repair_work_unit_id=_is_analysis_repair_work_unit_id,
        work_unit_fingerprint_matches=_work_unit_fingerprint_matches,
        report_is_current=_mas_quality_repair_report_is_current,
    ):
        return True
    if explicit_work_unit_id is not None and not _is_analysis_repair_work_unit_id(explicit_work_unit_id):
        return False
    if explicit_route_target is not None and explicit_route_target != _ANALYSIS_REPAIR_ROUTE_TARGET:
        return False
    if explicit_action is not None and explicit_action != _ANALYSIS_REPAIR_ACTION:
        return False
    if _analysis_repair_batch_report_matches(
        payload=payload,
        authorization_context=authorization_context,
    ):
        return True
    if (
        explicit_report_type == _MAS_QUALITY_REPAIR_REPORT_TYPE
        or explicit_report_kind == _MAS_QUALITY_REPAIR_REPORT_TYPE
    ):
        if not _mas_quality_repair_report_is_current(
            payload=payload,
            authorization_context=authorization_context,
        ):
            return False
        return (
            _is_analysis_repair_work_unit_id(explicit_work_unit_id)
            and explicit_route_target == _ANALYSIS_REPAIR_ROUTE_TARGET
            and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
            and (
                _mas_quality_repair_metrics_are_complete(
                    payload=payload,
                    authorization_context=authorization_context,
                )
                or _mas_quality_repair_specificity_targets_are_complete(
                    payload=payload,
                    authorization_context=authorization_context,
                )
            )
        )
    if not isinstance(result, dict):
        return False
    if not _report_is_current_for_authorization(
        payload=payload,
        authorization_context=authorization_context,
    ):
        return False
    has_legacy_report_identity = explicit_report_type == _ANALYSIS_REPAIR_REPORT_TYPE
    has_explicit_report_identity = (
        _is_analysis_repair_work_unit_id(explicit_work_unit_id)
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


def _normalized_repair_result(
    *,
    report_payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> dict[str, Any]:
    if _is_analysis_repair_exhausted_handoff(report_payload):
        return {
            "local_traceability_repair_complete": True,
            "analysis_lane_status": _ANALYSIS_REPAIR_HANDOFF_STATUS,
            "meaningful_artifact_delta": bool(report_payload.get("meaningful_artifact_delta")),
            "specificity_target_count": int(report_payload.get("specificity_target_count") or 0),
            "publication_gate_cleared": False,
            "writing_ready_after_repair": False,
            "finalize_ready_after_repair": False,
            **hard_methodology_unit_harmonization.normalized_requirement_flag(report_payload, text=_text),
        }
    if _is_analysis_repair_current_run_control_packet(report_payload):
        specificity_targets = [
            item for item in report_payload.get("specificity_target_results") or [] if isinstance(item, dict)
        ]
        return {
            "local_traceability_repair_complete": True,
            "meaningful_artifact_delta": bool(report_payload.get("meaningful_artifact_delta")),
            "specificity_targets_repaired_or_classified": len(specificity_targets),
            "missing_target_files_after_repair": 0,
            "targets_with_repair_markers": len(specificity_targets),
            "publication_gate_cleared": False,
            "writing_ready_after_repair": False,
            "finalize_ready_after_repair": False,
            "specificity_target_count": _specificity_target_count(authorization_context),
        }
    if _is_analysis_repair_source_repair_packet(report_payload):
        specificity_targets = [
            item for item in report_payload.get("specificity_target_results") or [] if isinstance(item, dict)
        ]
        source_repairs = [item for item in report_payload.get("source_repairs") or [] if isinstance(item, dict)]
        remaining_blockers = report_payload.get("remaining_blockers")
        if not isinstance(remaining_blockers, dict):
            remaining_blockers = {}
        publication_surface_blockers = [
            item for item in remaining_blockers.get("medical_publication_surface_blockers") or [] if _text(item)
        ]
        reporting_audit_blockers = [
            item for item in remaining_blockers.get("medical_reporting_audit_blockers") or [] if _text(item)
        ]
        return {
            "local_traceability_repair_complete": True,
            "meaningful_artifact_delta": bool(report_payload.get("meaningful_artifact_delta")),
            "specificity_targets_repaired_or_classified": len(specificity_targets),
            "missing_target_files_after_repair": 0,
            "targets_with_repair_markers": len(specificity_targets),
            "source_repairs_count": len(source_repairs),
            "publication_surface_blocker_count": len(publication_surface_blockers),
            "reporting_audit_blocker_count": len(reporting_audit_blockers),
            "publication_gate_cleared": False,
            "writing_ready_after_repair": False,
            "finalize_ready_after_repair": False,
            "specificity_target_count": _specificity_target_count(authorization_context),
        }
    if analysis_claim_evidence_repair_receipt.is_targeted_receipt(report_payload):
        return analysis_claim_evidence_repair_receipt.normalized_result(
            report_payload=report_payload,
            specificity_target_count=_specificity_target_count(authorization_context),
        )
    metrics = report_payload.get("metrics_summary")
    if isinstance(metrics, dict):
        return {
            "local_traceability_repair_complete": True,
            "specificity_targets_repaired_or_classified": int(
                metrics.get("specificity_targets_repaired_or_classified") or 0
            ),
            "missing_target_files_after_repair": int(metrics.get("missing_target_files_after_repair") or 0),
            "targets_with_repair_markers": int(metrics.get("targets_with_repair_markers") or 0),
            "publication_gate_cleared": bool(metrics.get("publication_gate_cleared")),
            "writing_ready_after_repair": bool(metrics.get("writing_ready_after_repair")),
            "finalize_ready_after_repair": bool(metrics.get("finalize_ready_after_repair")),
            "specificity_target_count": _specificity_target_count(authorization_context),
        }
    specificity_targets = report_payload.get("specificity_targets")
    if isinstance(specificity_targets, list):
        target_payloads = [item for item in specificity_targets if isinstance(item, dict)]
        remaining_gate_statuses = [
            item.get("remaining_gate_status")
            for item in target_payloads
            if isinstance(item.get("remaining_gate_status"), dict)
        ]
        return {
            "local_traceability_repair_complete": True,
            "specificity_targets_repaired_or_classified": len(target_payloads),
            "missing_target_files_after_repair": 0,
            "targets_with_repair_markers": len(target_payloads),
            "publication_gate_cleared": any(
                status.get("publication_gate_clear") is True for status in remaining_gate_statuses
            ),
            "writing_ready_after_repair": any(
                status.get("writing_ready") is True for status in remaining_gate_statuses
            ),
            "finalize_ready_after_repair": any(
                status.get("finalize_ready") is True for status in remaining_gate_statuses
            ),
            "specificity_target_count": _specificity_target_count(authorization_context),
        }
    repair_counts = report_payload.get("repair_counts")
    if isinstance(repair_counts, dict):
        return {
            "local_traceability_repair_complete": True,
            "changed_files_count": int(repair_counts.get("changed_files_count") or 0),
            "unresolved_local_defect_count": int(repair_counts.get("unresolved_local_defect_count") or 0),
            "gate_owned_or_nonlocal_defect_count": int(repair_counts.get("gate_owned_or_nonlocal_defect_count") or 0),
            "publication_gate_cleared": False,
            "writing_ready_after_repair": False,
            "finalize_ready_after_repair": False,
        }
    result = dict(report_payload.get("result") or {})
    return {
        "local_traceability_repair_complete": True,
        "unresolved_local_defect_count": int(result.get("unresolved_local_defect_count") or 0),
        "gate_owned_or_nonlocal_defect_count": int(result.get("gate_owned_or_nonlocal_defect_count") or 0),
    }


def _report_next_owner(report_payload: dict[str, Any]) -> str | None:
    direct_next_owner = _text(report_payload.get("next_owner"))
    if direct_next_owner is not None:
        return direct_next_owner
    remaining_blockers = report_payload.get("remaining_blockers")
    if isinstance(remaining_blockers, dict):
        return _text(remaining_blockers.get("next_owner"))
    return None


def _report_next_work_unit(report_payload: dict[str, Any]) -> str | None:
    direct_next_work_unit = _text(report_payload.get("next_work_unit"))
    if direct_next_work_unit is not None:
        return direct_next_work_unit
    next_work_unit = report_payload.get("next_work_unit")
    if isinstance(next_work_unit, dict):
        return _text(next_work_unit.get("unit_id"))
    return None


def _report_recommended_next_route(report_payload: dict[str, Any]) -> str:
    if _is_analysis_repair_exhausted_handoff(report_payload):
        return _ANALYSIS_REPAIR_HANDOFF_NEXT_ROUTE
    return _ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE


def _result_requires_runtime_relaunch(result: dict[str, Any]) -> bool:
    if _text(result.get("analysis_lane_status")) == _ANALYSIS_REPAIR_HANDOFF_STATUS:
        return False
    if result.get("publication_gate_recheck_required") is True:
        return True
    for key in (
        "publication_gate_cleared",
        "writing_ready_after_repair",
        "finalize_ready_after_repair",
    ):
        if result.get(key) is False:
            return True
    return False


def _existing_artifact_written_payload(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> dict[str, Any] | None:
    events = control_intent.events_for_business_key_since(
        study_root=study_root,
        business_key=identity.business_key,
        recorded_at=authorization_context.get("decision_emitted_at"),
    )
    for event in events:
        if _text(event.get("event_type")) != "artifact_written":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict):
            return dict(payload)
        return {}
    return None


def existing_controller_work_unit_evidence_adoption(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> dict[str, Any] | None:
    existing_payload = _existing_artifact_written_payload(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )
    if existing_payload is None:
        return None
    return {
        **existing_payload,
        "already_recorded": True,
    }


def _controller_work_unit_lifecycle_projection(lifecycle: dict[str, Any] | None) -> dict[str, Any]:
    payload = lifecycle if isinstance(lifecycle, dict) else {}
    return {
        "lifecycle_state": str(payload.get("lifecycle_state") or "new").strip() or "new",
        "latest_event_type": payload.get("latest_event_type"),
        "delivery_blocked": bool(payload.get("delivery_blocked")),
        "block_reason": payload.get("block_reason"),
        "terminal_consumed": bool(payload.get("terminal_consumed")),
    }


def _mark_controller_work_unit_evidence_adopted(
    *,
    quest_root: Path,
    authorization_context: dict[str, Any],
    evidence_adoption: dict[str, Any],
    lifecycle: dict[str, Any],
) -> None:
    runtime_state_path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    runtime_state = _read_json_mapping(runtime_state_path)
    runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY] = {
        "decision_id": str(authorization_context.get("decision_id") or "").strip(),
        "route_target": str(authorization_context.get("route_target") or "").strip(),
        "route_key_question": str(authorization_context.get("route_key_question") or "").strip(),
        "source_route_key_question": str(authorization_context.get("source_route_key_question") or "").strip() or None,
        "work_unit_id": str(authorization_context.get("work_unit_id") or "").strip() or None,
        "work_unit_fingerprint": str(authorization_context.get("work_unit_fingerprint") or "").strip() or None,
        "next_work_unit": dict(authorization_context.get("next_work_unit") or {}),
        "blocking_work_units": list(authorization_context.get("blocking_work_units") or []),
        "control_intent_key": str(authorization_context.get("control_intent_key") or "").strip() or None,
        "control_intent_identity": dict(authorization_context.get("control_intent_identity") or {}),
        "active_run_id": _text(evidence_adoption.get("active_run_id")),
        "delivery_mode": "controller_work_unit_evidence_adoption",
        "message_id": None,
        "source": _text(evidence_adoption.get("source")),
        "evidence_adoption": {
            key: evidence_adoption.get(key)
            for key in (
                "report_ref",
                "created_at",
                "recommended_next_route",
                "status",
                "artifact_kind",
                "already_recorded",
            )
            if key in evidence_adoption
        },
        "controller_work_unit_lifecycle": _controller_work_unit_lifecycle_projection(lifecycle),
    }
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in authorization_context:
            runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY][key] = authorization_context[key]
    _write_json_mapping(runtime_state_path, runtime_state)


def record_controller_work_unit_evidence_adoption(
    *,
    status: Any,
    study_root: Path,
    quest_root: Path | None = None,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
    evidence_adoption: dict[str, Any],
) -> None:
    decision_emitted_at = _timestamp_key(authorization_context.get("decision_emitted_at"))
    if decision_emitted_at is not None:
        lifecycle = control_intent.lifecycle_state_since(
            study_root=study_root,
            identity=identity,
            recorded_at=decision_emitted_at,
        )
    else:
        lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    relaunch_required = _result_requires_runtime_relaunch(dict(evidence_adoption.get("result") or {}))
    next_owner = _text(evidence_adoption.get("next_owner")) or "publication_gate"
    next_work_unit = _text(evidence_adoption.get("next_work_unit"))
    status.extras["controller_work_unit_evidence_adoption"] = evidence_adoption
    status.extras["controller_decision_authorization_deduped"] = {
        "control_intent_key": authorization_context.get("control_intent_key"),
        "source": "controller_work_unit_evidence_adoption",
        "lifecycle": lifecycle,
    }
    status.extras["controller_work_unit_next_route"] = {
        "recommended_next_route": evidence_adoption.get("recommended_next_route"),
        "owner": next_owner,
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": relaunch_required,
    }
    if next_work_unit is not None:
        status.extras["controller_work_unit_next_route"]["next_work_unit"] = next_work_unit
    if quest_root is not None:
        _mark_controller_work_unit_evidence_adopted(
            quest_root=quest_root,
            authorization_context=authorization_context,
            evidence_adoption=evidence_adoption,
            lifecycle=lifecycle,
        )


def _has_prior_delivery_or_duplicate(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> bool:
    return any(
        _text(event.get("event_type")) in {"delivered", "skipped_duplicate"}
        for event in control_intent.events_for_business_key_since(
            study_root=study_root,
            business_key=identity.business_key,
            recorded_at=authorization_context.get("decision_emitted_at"),
        )
    )


def _has_prior_delivery_or_duplicate_for_business_key(
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
    existing_payload = existing_controller_work_unit_evidence_adoption(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )
    if existing_payload is not None:
        return existing_payload
    has_delivery_for_current_decision = _has_prior_delivery_or_duplicate(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )
    has_delivery_for_same_business_key = _has_prior_delivery_or_duplicate_for_business_key(
        study_root=study_root,
        identity=identity,
    )
    has_matching_relay_marker = generic_completed_work_unit.has_matching_relay_marker(
        quest_root=quest_root,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        work_unit_target_context_keys=_WORK_UNIT_TARGET_CONTEXT_KEYS,
    )
    if (
        not has_delivery_for_current_decision
        and not has_delivery_for_same_business_key
        and not has_matching_relay_marker
    ):
        return None
    if _authorization_matches_analysis_repair(authorization_context):
        for report_path in _report_candidates(quest_root, active_run_id=active_run_id):
            if not report_path.exists():
                continue
            report_payload = _normalize_report_payload(
                _read_json_mapping(report_path),
                authorization_context=authorization_context,
            )
            if not _report_matches_analysis_repair(
                payload=report_payload,
                authorization_context=authorization_context,
            ):
                continue
            if not has_delivery_for_current_decision and not _is_analysis_repair_exhausted_handoff(report_payload):
                continue
            payload = {
                "active_run_id": active_run_id,
                "report_ref": str(report_path),
                "created_at": _report_timestamp(report_payload),
                "work_unit_id": _authorization_analysis_repair_work_unit_id(authorization_context),
                "route_target": _ANALYSIS_REPAIR_ROUTE_TARGET,
                "recommended_next_route": _report_recommended_next_route(report_payload),
                "source": source,
                "result": _normalized_repair_result(
                    report_payload=report_payload,
                    authorization_context=authorization_context,
                ),
            }
            if artifact_kind := _text(report_payload.get("artifact_kind")):
                payload["artifact_kind"] = artifact_kind
            if report_status := _text(report_payload.get("status")):
                payload["status"] = report_status
            if blocked_reason := _text(report_payload.get("blocked_reason")):
                payload["blocked_reason"] = blocked_reason
            next_owner = _report_next_owner(report_payload)
            next_work_unit = (
                _report_next_work_unit(report_payload)
                if _is_analysis_repair_exhausted_handoff(report_payload)
                else None
            )
            if _is_analysis_repair_source_repair_packet(report_payload):
                next_work_unit = None
            analysis_lane_status = _text(report_payload.get("analysis_lane_status"))
            if analysis_lane_status is not None:
                payload["analysis_lane_status"] = analysis_lane_status
            if next_owner is not None:
                payload["next_owner"] = next_owner
            if next_work_unit is not None:
                payload["next_work_unit"] = next_work_unit
            if dedupe_recommendation := _text(report_payload.get("dedupe_recommendation")):
                payload["dedupe_recommendation"] = dedupe_recommendation
            control_intent.append_event(
                study_root=study_root,
                identity=identity,
                event_type="artifact_written",
                payload=payload,
            )
            if analysis_lane_status == _ANALYSIS_REPAIR_HANDOFF_STATUS and next_owner is not None:
                control_intent.append_event(
                    study_root=study_root,
                    identity=identity,
                    event_type="owner_handoff",
                    payload={
                        "reason": _ANALYSIS_REPAIR_HANDOFF_STATUS,
                        "next_owner": next_owner,
                        "next_work_unit": next_work_unit,
                        "report_ref": str(report_path),
                        "source": source,
                    },
                )
            return payload
        return None
    for report_path in generic_completed_work_unit.report_candidates(quest_root, active_run_id=active_run_id):
        report_payload = generic_completed_work_unit.read_json_mapping(report_path)
        if not generic_completed_work_unit.matches_completed_work_unit(
            payload=report_payload,
            authorization_context=authorization_context,
            analysis_repair_authorized=False,
            active_run_id=active_run_id,
        ):
            continue
        payload = {
            "active_run_id": active_run_id,
            "report_ref": str(report_path),
            "created_at": generic_completed_work_unit.report_timestamp(report_payload),
            "work_unit_id": _text(authorization_context.get("work_unit_id")),
            "route_target": _text(authorization_context.get("route_target")),
            "recommended_next_route": generic_completed_work_unit.RECOMMENDED_NEXT_ROUTE,
            "source": source,
            "next_owner": generic_completed_work_unit.NEXT_OWNER,
            "result": generic_completed_work_unit.normalized_result(report_payload),
        }
        if artifact_kind := _text(report_payload.get("artifact_kind")):
            payload["artifact_kind"] = artifact_kind
        if report_status := _text(report_payload.get("status")):
            payload["status"] = report_status
        control_intent.append_event(
            study_root=study_root,
            identity=identity,
            event_type="artifact_written",
            payload=payload,
        )
        return payload
    return None
