from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.work_unit_evidence_adoption_parts import (
    analysis_claim_evidence_repair_receipt,
    analysis_stage_memory_handoff,
    hard_methodology_unit_harmonization,
)


ANALYSIS_REPAIR_WORK_UNIT_ID = "analysis_claim_evidence_repair"
ANALYSIS_REPAIR_WORK_UNIT_IDS = frozenset(
    {
        ANALYSIS_REPAIR_WORK_UNIT_ID,
        "medical_prose_quality_analysis_source_documentation_repair",
    }
)
ANALYSIS_REPAIR_ROUTE_TARGET = "analysis-campaign"
ANALYSIS_REPAIR_ACTION = "run_quality_repair_batch"
ANALYSIS_REPAIR_REPORT_TYPE = "analysis_claim_evidence_repair_specificity_target_traceability_reaudit"
ANALYSIS_REPAIR_BATCH_REPORT_TYPE = "analysis_claim_evidence_repair"
ANALYSIS_REPAIR_REPORT_SUFFIX = Path(
    "artifacts",
    "reports",
    "analysis_claim_evidence_repair",
    "specificity_target_traceability_reaudit.json",
)
ANALYSIS_REPAIR_LATEST_REPORT_SUFFIX = Path("artifacts", "reports", "analysis_claim_evidence_repair", "latest.json")
MAS_QUALITY_REPAIR_REPORT_SUFFIX = Path("artifacts", "reports", "mas_quality_repair", "latest.json")
CONTROLLER_CONSUMPTION_REPORT_SUFFIX = Path("artifacts", "supervision", "controller_consumption", "latest.json")
MAS_QUALITY_REPAIR_REPORT_TYPE = "mas_quality_repair_batch"
ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE = "return_to_publication_gate_recheck"
ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE = "analysis_claim_evidence_current_run_handoff"
ANALYSIS_REPAIR_HANDOFF_STATUS = "exhausted_for_current_fingerprint"
ANALYSIS_REPAIR_HANDOFF_NEXT_ROUTE = "handoff_to_next_owner"
ANALYSIS_REPAIR_CONTROL_PACKET_KIND = "analysis_claim_evidence_current_run_repair_control_packet"
ANALYSIS_REPAIR_CONTROL_PACKET_STATUS = "completed_as_current_run_repair_control_packet"
ANALYSIS_REPAIR_SOURCE_REPAIR_KIND = "analysis_claim_evidence_source_repair"
ANALYSIS_REPAIR_SOURCE_REPAIR_STATUS = "completed"
ANALYSIS_REPAIR_RETRY_BACKOFF_HANDOFF_REPORT_TYPE = "analysis_claim_evidence_retry_backoff_dedupe_handoff"


def text(value: object) -> str | None:
    text_value = str(value or "").strip()
    return text_value or None


def timestamp_key(value: object) -> str | None:
    text_value = text(value)
    if text_value is None:
        return None
    if text_value.endswith("Z"):
        text_value = f"{text_value[:-1]}+00:00"
    return text_value


def read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def report_timestamp(payload: dict[str, Any]) -> str | None:
    return timestamp_key(
        payload.get("created_at")
        or payload.get("updated_at")
        or payload.get("emitted_at")
    )


def authorization_matches(authorization_context: dict[str, Any]) -> bool:
    actions = {
        str(action).strip()
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    }
    return (
        is_analysis_repair_work_unit_id(authorization_context.get("work_unit_id"))
        and text(authorization_context.get("route_target")) == ANALYSIS_REPAIR_ROUTE_TARGET
        and ANALYSIS_REPAIR_ACTION in actions
    )


def authorization_work_unit_id(authorization_context: dict[str, Any]) -> str:
    work_unit_id = text(authorization_context.get("work_unit_id"))
    return work_unit_id if work_unit_id in ANALYSIS_REPAIR_WORK_UNIT_IDS else ANALYSIS_REPAIR_WORK_UNIT_ID


def report_candidates(quest_root: Path, *, active_run_id: str | None = None) -> tuple[Path, ...]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    candidates = [
        resolved_quest_root / ANALYSIS_REPAIR_REPORT_SUFFIX,
        resolved_quest_root / ANALYSIS_REPAIR_LATEST_REPORT_SUFFIX,
        resolved_quest_root / MAS_QUALITY_REPAIR_REPORT_SUFFIX,
        resolved_quest_root / CONTROLLER_CONSUMPTION_REPORT_SUFFIX,
    ]
    candidates.extend(
        analysis_stage_memory_handoff.closeout_candidates(
            quest_root=resolved_quest_root,
            active_run_id=active_run_id,
        )
    )
    history_root = resolved_quest_root / ".ds" / "cold_archive" / "report_history"
    if history_root.exists():
        candidates.extend(
            sorted(
                path
                for path in history_root.rglob(ANALYSIS_REPAIR_REPORT_SUFFIX.name)
                if path.match(f"*/{ANALYSIS_REPAIR_REPORT_SUFFIX.as_posix()}")
            )
        )
        report_store = history_root / "artifacts" / "reports"
        if report_store.exists():
            candidates.extend(sorted(report_store.glob("report-*.json")))
    return tuple(candidates)


def normalize_report_payload(
    payload: dict[str, Any],
    *,
    authorization_context: dict[str, Any],
) -> dict[str, Any]:
    if analysis_stage_memory_handoff.is_handoff(payload):
        return analysis_stage_memory_handoff.normalize_payload(
            payload,
            authorization_context=authorization_context,
            analysis_repair_work_unit_id=authorization_work_unit_id(authorization_context),
            handoff_report_type=ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE,
            handoff_status=ANALYSIS_REPAIR_HANDOFF_STATUS,
        )
    return payload


def report_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    hard_methodology_target = _authorization_has_hard_methodology_target(authorization_context)
    result = payload.get("result")
    explicit_work_unit_id = text(payload.get("work_unit_id"))
    explicit_route_target = text(payload.get("route_target"))
    explicit_action = text(payload.get("action"))
    explicit_report_type = text(payload.get("report_type"))
    explicit_report_kind = text(payload.get("report_kind"))
    if is_exhausted_handoff(payload):
        return (
            is_analysis_repair_work_unit_id(explicit_work_unit_id)
            and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
            and text(payload.get("next_owner")) is not None
            and text(payload.get("next_work_unit")) is not None
            and (not hard_methodology_target or _hard_methodology_report_satisfies_authorization(payload))
            and _handoff_report_is_current(
                payload=payload,
                authorization_context=authorization_context,
            )
        )
    if hard_methodology_target:
        return False
    if _is_current_run_control_packet(payload):
        return (
            is_analysis_repair_work_unit_id(explicit_work_unit_id)
            and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
            and _specificity_target_results_are_complete(payload)
            and _mas_quality_repair_report_is_current(
                payload=payload,
                authorization_context=authorization_context,
            )
        )
    if _source_repair_packet_matches(
        payload=payload,
        authorization_context=authorization_context,
    ):
        return True
    if analysis_claim_evidence_repair_receipt.matches(
        payload=payload,
        authorization_context=authorization_context,
        is_analysis_repair_work_unit_id=is_analysis_repair_work_unit_id,
        work_unit_fingerprint_matches=_work_unit_fingerprint_matches,
        report_is_current=_mas_quality_repair_report_is_current,
    ):
        return True
    if explicit_work_unit_id is not None and not is_analysis_repair_work_unit_id(explicit_work_unit_id):
        return False
    if explicit_route_target is not None and explicit_route_target != ANALYSIS_REPAIR_ROUTE_TARGET:
        return False
    if explicit_action is not None and explicit_action != ANALYSIS_REPAIR_ACTION:
        return False
    if _batch_report_matches(payload=payload, authorization_context=authorization_context):
        return True
    if explicit_report_type == MAS_QUALITY_REPAIR_REPORT_TYPE or explicit_report_kind == MAS_QUALITY_REPAIR_REPORT_TYPE:
        if not _mas_quality_repair_report_is_current(
            payload=payload,
            authorization_context=authorization_context,
        ):
            return False
        return (
            is_analysis_repair_work_unit_id(explicit_work_unit_id)
            and explicit_route_target == ANALYSIS_REPAIR_ROUTE_TARGET
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
    has_legacy_report_identity = explicit_report_type == ANALYSIS_REPAIR_REPORT_TYPE
    has_explicit_report_identity = (
        is_analysis_repair_work_unit_id(explicit_work_unit_id)
        and explicit_route_target == ANALYSIS_REPAIR_ROUTE_TARGET
        and explicit_action == ANALYSIS_REPAIR_ACTION
    )
    return (
        (has_legacy_report_identity or has_explicit_report_identity)
        and result.get("local_traceability_repair_complete") is True
        and _int_value(result.get("unresolved_local_defect_count")) == 0
        and _int_value(result.get("gate_owned_or_nonlocal_defect_count")) == 0
        and text(result.get("recommended_next_route")) == ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE
    )


def adoption_payload(
    *,
    report_path: Path,
    report_payload: dict[str, Any],
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    source: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "active_run_id": active_run_id,
        "report_ref": str(report_path),
        "created_at": report_timestamp(report_payload),
        "work_unit_id": authorization_work_unit_id(authorization_context),
        "route_target": ANALYSIS_REPAIR_ROUTE_TARGET,
        "recommended_next_route": recommended_next_route(report_payload),
        "source": source,
        "result": normalized_repair_result(
            report_payload=report_payload,
            authorization_context=authorization_context,
        ),
    }
    if artifact_kind := text(report_payload.get("artifact_kind")):
        payload["artifact_kind"] = artifact_kind
    if report_status := text(report_payload.get("status")):
        payload["status"] = report_status
    if blocked_reason := text(report_payload.get("blocked_reason")):
        payload["blocked_reason"] = blocked_reason
    next_owner = report_next_owner(report_payload)
    next_work_unit = report_next_work_unit(report_payload) if is_exhausted_handoff(report_payload) else None
    if _is_source_repair_packet(report_payload):
        next_work_unit = None
    analysis_lane_status = text(report_payload.get("analysis_lane_status"))
    if analysis_lane_status is not None:
        payload["analysis_lane_status"] = analysis_lane_status
    if next_owner is not None:
        payload["next_owner"] = next_owner
    if next_work_unit is not None:
        payload["next_work_unit"] = next_work_unit
    if dedupe_recommendation := text(report_payload.get("dedupe_recommendation")):
        payload["dedupe_recommendation"] = dedupe_recommendation
    return payload


def owner_handoff_payload(
    *,
    report_payload: dict[str, Any],
    report_path: Path,
    source: str,
) -> dict[str, Any] | None:
    next_owner = report_next_owner(report_payload)
    if text(report_payload.get("analysis_lane_status")) != ANALYSIS_REPAIR_HANDOFF_STATUS or next_owner is None:
        return None
    return {
        "reason": ANALYSIS_REPAIR_HANDOFF_STATUS,
        "next_owner": next_owner,
        "next_work_unit": report_next_work_unit(report_payload),
        "report_ref": str(report_path),
        "source": source,
    }


def result_requires_runtime_relaunch(result: dict[str, Any]) -> bool:
    if text(result.get("analysis_lane_status")) == ANALYSIS_REPAIR_HANDOFF_STATUS:
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


def is_analysis_repair_work_unit_id(value: object) -> bool:
    return text(value) in ANALYSIS_REPAIR_WORK_UNIT_IDS


def is_exhausted_handoff(payload: dict[str, Any]) -> bool:
    return (
        text(payload.get("repair_packet_type"))
        in {
            ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE,
            ANALYSIS_REPAIR_RETRY_BACKOFF_HANDOFF_REPORT_TYPE,
        }
        or text(payload.get("report_type"))
        in {
            ANALYSIS_REPAIR_HANDOFF_REPORT_TYPE,
            ANALYSIS_REPAIR_RETRY_BACKOFF_HANDOFF_REPORT_TYPE,
        }
    ) and text(payload.get("analysis_lane_status")) == ANALYSIS_REPAIR_HANDOFF_STATUS


def recommended_next_route(report_payload: dict[str, Any]) -> str:
    if is_exhausted_handoff(report_payload):
        return ANALYSIS_REPAIR_HANDOFF_NEXT_ROUTE
    return ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE


def report_next_owner(report_payload: dict[str, Any]) -> str | None:
    direct_next_owner = text(report_payload.get("next_owner"))
    if direct_next_owner is not None:
        return direct_next_owner
    remaining_blockers = report_payload.get("remaining_blockers")
    if isinstance(remaining_blockers, dict):
        return text(remaining_blockers.get("next_owner"))
    return None


def report_next_work_unit(report_payload: dict[str, Any]) -> str | None:
    direct_next_work_unit = text(report_payload.get("next_work_unit"))
    if direct_next_work_unit is not None:
        return direct_next_work_unit
    next_work_unit = report_payload.get("next_work_unit")
    if isinstance(next_work_unit, dict):
        return text(next_work_unit.get("unit_id"))
    return None


def normalized_repair_result(
    *,
    report_payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> dict[str, Any]:
    if is_exhausted_handoff(report_payload):
        return {
            "local_traceability_repair_complete": True,
            "analysis_lane_status": ANALYSIS_REPAIR_HANDOFF_STATUS,
            "meaningful_artifact_delta": bool(report_payload.get("meaningful_artifact_delta")),
            "specificity_target_count": int(report_payload.get("specificity_target_count") or 0),
            "publication_gate_cleared": False,
            "writing_ready_after_repair": False,
            "finalize_ready_after_repair": False,
            **hard_methodology_unit_harmonization.normalized_requirement_flag(report_payload, text=text),
        }
    if _is_current_run_control_packet(report_payload):
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
    if _is_source_repair_packet(report_payload):
        specificity_targets = [
            item for item in report_payload.get("specificity_target_results") or [] if isinstance(item, dict)
        ]
        source_repairs = [item for item in report_payload.get("source_repairs") or [] if isinstance(item, dict)]
        remaining_blockers = report_payload.get("remaining_blockers")
        if not isinstance(remaining_blockers, dict):
            remaining_blockers = {}
        publication_surface_blockers = [
            item for item in remaining_blockers.get("medical_publication_surface_blockers") or [] if text(item)
        ]
        reporting_audit_blockers = [
            item for item in remaining_blockers.get("medical_reporting_audit_blockers") or [] if text(item)
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


def _int_value(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _report_is_current_for_authorization(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    decision_time = timestamp_key(authorization_context.get("decision_emitted_at"))
    if decision_time is None:
        return True
    report_time = report_timestamp(payload)
    if report_time is None:
        return True
    return report_time >= decision_time


def _work_unit_fingerprint_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    expected = text(authorization_context.get("work_unit_fingerprint"))
    controller = payload.get("controller")
    observed = text(payload.get("work_unit_fingerprint"))
    if observed is None and isinstance(controller, dict):
        observed = text(controller.get("work_unit_fingerprint"))
    return expected is None or observed == expected


def _work_unit_fingerprint_explicitly_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    expected = text(authorization_context.get("work_unit_fingerprint"))
    if expected is None:
        return False
    controller = payload.get("controller")
    observed = text(payload.get("work_unit_fingerprint"))
    if observed is None and isinstance(controller, dict):
        observed = text(controller.get("work_unit_fingerprint"))
    return observed == expected


def _specificity_target_count(authorization_context: dict[str, Any]) -> int:
    targets = authorization_context.get("specificity_targets")
    if not isinstance(targets, list):
        return 0
    return sum(1 for item in targets if isinstance(item, dict))


def _authorization_has_hard_methodology_target(authorization_context: dict[str, Any]) -> bool:
    return hard_methodology_unit_harmonization.authorization_has_target(
        authorization_context,
        text=text,
    )


def _hard_methodology_report_satisfies_authorization(payload: dict[str, Any]) -> bool:
    return hard_methodology_unit_harmonization.report_satisfies_authorization(
        payload,
        report_next_work_unit=report_next_work_unit,
        text=text,
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
        text(item.get("target_id")) is not None and text(item.get("status")) is not None
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
    return text(controller.get(key))


def _is_current_run_control_packet(payload: dict[str, Any]) -> bool:
    return (
        text(payload.get("artifact_kind")) == ANALYSIS_REPAIR_CONTROL_PACKET_KIND
        and text(payload.get("status")) == ANALYSIS_REPAIR_CONTROL_PACKET_STATUS
    )


def _is_source_repair_packet(payload: dict[str, Any]) -> bool:
    return (
        text(payload.get("artifact_kind")) == ANALYSIS_REPAIR_SOURCE_REPAIR_KIND
        and text(payload.get("status")) == ANALYSIS_REPAIR_SOURCE_REPAIR_STATUS
    )


def _specificity_target_results_are_complete(payload: dict[str, Any]) -> bool:
    targets = payload.get("specificity_target_results")
    if not isinstance(targets, list):
        return False
    target_payloads = [item for item in targets if isinstance(item, dict)]
    if len(target_payloads) != len(targets):
        return False
    return bool(target_payloads) and all(
        text(item.get("target_id")) is not None
        and (text(item.get("status")) is not None or text(item.get("result")) is not None)
        for item in target_payloads
    )


def _source_repairs_are_complete(payload: dict[str, Any]) -> bool:
    repairs = payload.get("source_repairs")
    if not isinstance(repairs, list):
        return False
    repair_payloads = [item for item in repairs if isinstance(item, dict)]
    return bool(repair_payloads) and len(repair_payloads) == len(repairs) and all(
        text(item.get("path")) is not None for item in repair_payloads
    )


def _source_repair_packet_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return (
        _is_source_repair_packet(payload)
        and is_analysis_repair_work_unit_id(payload.get("work_unit_id"))
        and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
        and _mas_quality_repair_report_is_current(
            payload=payload,
            authorization_context=authorization_context,
        )
        and payload.get("meaningful_artifact_delta") is True
        and _specificity_target_results_are_complete(payload)
        and _source_repairs_are_complete(payload)
    )


def _batch_report_matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    if text(payload.get("report_type")) != ANALYSIS_REPAIR_BATCH_REPORT_TYPE:
        return False
    repair_counts = payload.get("repair_counts")
    if not isinstance(repair_counts, dict):
        return False
    return (
        is_analysis_repair_work_unit_id(_controller_field(payload, "active_work_unit_id"))
        and _controller_field(payload, "route_target") == ANALYSIS_REPAIR_ROUTE_TARGET
        and ANALYSIS_REPAIR_ACTION in (_controller_field(payload, "controller_actions") or "")
        and _work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
        and _mas_quality_repair_report_is_current(
            payload=payload,
            authorization_context=authorization_context,
        )
        and _int_value(repair_counts.get("unresolved_local_defect_count")) == 0
        and _int_value(repair_counts.get("gate_owned_or_nonlocal_defect_count")) == 0
        and text(payload.get("recommended_next_route")) == ANALYSIS_REPAIR_RECOMMENDED_NEXT_ROUTE
    )
