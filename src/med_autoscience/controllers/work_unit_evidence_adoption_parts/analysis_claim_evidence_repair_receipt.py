from __future__ import annotations

from typing import Any, Callable


RECEIPT_ID_PREFIX = "analysis-claim-evidence-repair::"
ROUTE_TARGET = "analysis-campaign"
ACTION = "run_quality_repair_batch"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _nested_controller_action(payload: dict[str, Any]) -> str | None:
    controller_action = payload.get("controller_action_invoked_first")
    if not isinstance(controller_action, dict):
        return None
    return _text(controller_action.get("action"))


def is_targeted_receipt(payload: dict[str, Any]) -> bool:
    receipt_id = _text(payload.get("receipt_id"))
    return receipt_id is not None and receipt_id.startswith(RECEIPT_ID_PREFIX)


def _targeted_publication_specificity_targets_are_complete(payload: dict[str, Any]) -> bool:
    targets = payload.get("targeted_publication_specificity_targets")
    if not isinstance(targets, list):
        return False
    target_payloads = [item for item in targets if isinstance(item, dict)]
    if len(target_payloads) != len(targets):
        return False
    return bool(target_payloads) and all(
        _text(item.get("target_id")) is not None
        and _text(item.get("target_kind")) is not None
        and _text(item.get("source_path")) is not None
        for item in target_payloads
    )


def _canonical_artifact_delta_is_meaningful(payload: dict[str, Any]) -> bool:
    delta = payload.get("canonical_artifact_delta")
    return isinstance(delta, dict) and delta.get("meaningful_artifact_delta") is True


def _surface_replay_cleared_target(payload: dict[str, Any]) -> bool:
    verification = payload.get("verification")
    if not isinstance(verification, dict):
        return False
    replay = verification.get("medical_publication_surface_replay")
    if not isinstance(replay, dict):
        return False
    return (
        _text(replay.get("table_figure_claim_map_status")) == "clear"
        or _text(replay.get("cleared_blocker")) == "table_figure_claim_map_missing_or_incomplete"
    )


def matches(
    *,
    payload: dict[str, Any],
    authorization_context: dict[str, Any],
    is_analysis_repair_work_unit_id: Callable[[object], bool],
    work_unit_fingerprint_matches: Callable[..., bool],
    report_is_current: Callable[..., bool],
) -> bool:
    return (
        is_targeted_receipt(payload)
        and is_analysis_repair_work_unit_id(payload.get("work_unit_id"))
        and _text(payload.get("lane")) == ROUTE_TARGET
        and _nested_controller_action(payload) == ACTION
        and work_unit_fingerprint_matches(payload=payload, authorization_context=authorization_context)
        and report_is_current(payload=payload, authorization_context=authorization_context)
        and _targeted_publication_specificity_targets_are_complete(payload)
        and _canonical_artifact_delta_is_meaningful(payload)
        and _surface_replay_cleared_target(payload)
    )


def normalized_result(
    *,
    report_payload: dict[str, Any],
    specificity_target_count: int,
) -> dict[str, Any]:
    targeted_specificity_targets = [
        item
        for item in report_payload.get("targeted_publication_specificity_targets") or []
        if isinstance(item, dict)
    ]
    delta = report_payload.get("canonical_artifact_delta")
    if not isinstance(delta, dict):
        delta = {}
    changed_artifacts = [item for item in delta.get("changed_artifacts") or [] if isinstance(item, dict)]
    verification = report_payload.get("verification")
    if not isinstance(verification, dict):
        verification = {}
    replay = verification.get("medical_publication_surface_replay")
    if not isinstance(replay, dict):
        replay = {}
    remaining_blockers = [item for item in replay.get("remaining_blockers") or [] if _text(item)]
    return {
        "local_traceability_repair_complete": True,
        "meaningful_artifact_delta": bool(delta.get("meaningful_artifact_delta")),
        "specificity_targets_repaired_or_classified": len(targeted_specificity_targets),
        "missing_target_files_after_repair": 0,
        "targets_with_repair_markers": len(targeted_specificity_targets),
        "changed_artifacts_count": len(changed_artifacts),
        "publication_surface_remaining_blocker_count": len(remaining_blockers),
        "publication_gate_recheck_required": True,
        "publication_gate_cleared": False,
        "writing_ready_after_repair": False,
        "finalize_ready_after_repair": False,
        "specificity_target_count": specificity_target_count,
    }
