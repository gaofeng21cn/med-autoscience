from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers.owner_route_reconcile_parts import story_surface_delta_actions


REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")
REPAIR_EXECUTION_RECEIPT_RELATIVE_PATH = Path("artifacts/controller/repair_execution_receipts/latest.json")
REPAIR_PROGRESS_AI_REVIEWER_REASON = "repair_progress_ai_reviewer_recheck_required"
REPAIR_PROGRESS_GATE_REPLAY_REASON = "repair_progress_gate_replay_required"
AI_REVIEWER_RECHECK_WORK_UNIT = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
GATE_REPLAY_WORK_UNIT = "publication_gate_replay"


def accepted_repair_progress_followup_action(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    root = Path(study_root).expanduser().resolve()
    evidence_path = root / REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH
    receipt_path = root / REPAIR_EXECUTION_RECEIPT_RELATIVE_PATH
    evidence = _read_json_object(evidence_path)
    receipt = _read_json_object(receipt_path)
    if not _accepted_repair_progress(evidence=evidence, receipt=receipt):
        return None
    source_eval_id = (
        _text(evidence.get("source_eval_id"))
        or _text(_mapping(evidence.get("repair_work_unit")).get("source_eval_id"))
        or _text(_mapping(evidence.get("review_finding")).get("source_eval_id"))
        or _text(publication_eval_payload.get("eval_id"))
    )
    ai_reviewer_request_ref = _text(evidence.get("ai_reviewer_recheck_request_ref")) or _text(
        receipt.get("ai_reviewer_recheck_request_ref")
    )
    if ai_reviewer_request_ref is not None and _ai_reviewer_request_is_current(
        study_root=root,
        request_ref=ai_reviewer_request_ref,
    ) and not _current_ai_reviewer_record_already_available(
        study_root=root,
        publication_eval_payload=publication_eval_payload,
    ):
        return _repair_progress_followup_payload(
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            reason=REPAIR_PROGRESS_AI_REVIEWER_REASON,
            next_work_unit=AI_REVIEWER_RECHECK_WORK_UNIT,
            required_output_surface="artifacts/publication_eval/latest.json",
            route_target="review",
            evidence=evidence,
            receipt=receipt,
            evidence_path=evidence_path,
            receipt_path=receipt_path,
            source_eval_id=source_eval_id,
            request_ref=ai_reviewer_request_ref,
        )
    gate_replay_ref = _first_text_item(evidence.get("gate_replay_refs")) or _text(receipt.get("gate_replay_request_ref"))
    if gate_replay_ref is None:
        return None
    return _repair_progress_followup_payload(
        action_type="run_gate_clearing_batch",
        owner="gate_clearing_batch",
        reason=REPAIR_PROGRESS_GATE_REPLAY_REASON,
        next_work_unit=GATE_REPLAY_WORK_UNIT,
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        route_target="finalize",
        evidence=evidence,
        receipt=receipt,
        evidence_path=evidence_path,
        receipt_path=receipt_path,
        source_eval_id=source_eval_id,
        request_ref=gate_replay_ref,
    )


def pending_ai_reviewer_recheck_consumes_current_write_routeback(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> bool:
    action = story_surface_delta_actions.write_owner_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if action is None:
        return False
    expected_eval_id = _text(publication_eval_payload.get("eval_id"))
    expected_work_unit = _text(action.get("controller_work_unit_id")) or _text(action.get("next_work_unit"))
    if expected_eval_id is None or expected_work_unit is None:
        return False
    resolved_study_root = Path(study_root).expanduser().resolve()
    evidence = _read_json_object(resolved_study_root / REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH)
    if evidence is None:
        return False
    if _text(evidence.get("status")) not in {"progress_delta_candidate", "controller_progress_delta_candidate"}:
        return False
    if evidence.get("ai_reviewer_recheck_required") is not True:
        return False
    if evidence.get("ai_reviewer_recheck_done") is not True:
        return False
    if _string_items(evidence.get("blockers")):
        return False
    source_eval_id = _text(evidence.get("source_eval_id")) or _text(_mapping(evidence.get("review_finding")).get("source_eval_id"))
    if source_eval_id != expected_eval_id:
        return False
    repair_work_unit = _mapping(evidence.get("repair_work_unit"))
    if _text(repair_work_unit.get("unit_id")) != expected_work_unit:
        return False
    recheck_ref = _text(evidence.get("ai_reviewer_recheck_request_ref"))
    if recheck_ref is None:
        return False
    recheck_path = Path(recheck_ref).expanduser()
    if not recheck_path.is_absolute():
        recheck_path = resolved_study_root / recheck_path
    request = _read_json_object(recheck_path)
    if request is None:
        return False
    if _text(request.get("request_kind")) != "return_to_ai_reviewer_workflow":
        return False
    if _text(request.get("request_owner")) not in {None, "ai_reviewer"}:
        return False
    return _text(_mapping(request.get("request_lifecycle")).get("state")) in {"requested", "assigned"}


def _accepted_repair_progress(
    *,
    evidence: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
) -> bool:
    if not evidence or not receipt:
        return False
    if _text(evidence.get("status")) not in {"progress_delta_candidate", "controller_progress_delta_candidate"}:
        return False
    if evidence.get("progress_delta_candidate") is not True:
        return False
    if _mapping(evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is not True:
        return False
    if _string_items(evidence.get("blockers")):
        return False
    if receipt.get("accepted") is not True:
        return False
    if receipt.get("direct_current_package_write") is True:
        return False
    if receipt.get("quality_authorized") is True or receipt.get("submission_authorized") is True:
        return False
    if _text(receipt.get("typed_blocker")) is not None or _text(receipt.get("blocked_reason")) is not None:
        return False
    return True


def _current_ai_reviewer_record_already_available(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> bool:
    if (
        _text(publication_eval_payload.get(ai_reviewer_publication_eval_records.PROJECTION_SOURCE_KIND_FIELD))
        == ai_reviewer_publication_eval_records.PROJECTION_SOURCE_KIND_AI_REVIEWER_RECORD
    ):
        return True
    return (
        ai_reviewer_publication_eval_records.latest_current_ai_reviewer_publication_eval_record(
            study_root=study_root,
            current_publication_eval=publication_eval_payload,
        )
        is not None
    )


def _ai_reviewer_request_is_current(*, study_root: Path, request_ref: str) -> bool:
    request_path = Path(request_ref).expanduser()
    if not request_path.is_absolute():
        request_path = Path(study_root).expanduser().resolve() / request_path
    request = _read_json_object(request_path)
    if request is None:
        return False
    if _text(request.get("request_kind")) != "return_to_ai_reviewer_workflow":
        return False
    if _text(request.get("request_owner")) not in {None, "ai_reviewer"}:
        return False
    lifecycle = _mapping(request.get("request_lifecycle"))
    state = _text(lifecycle.get("state"))
    if state in {"requested", "assigned"}:
        return True
    if state is not None:
        return False
    if _text(lifecycle.get("blocked_reason")) is not None:
        return False
    return any(
        _text(lifecycle.get(key)) is not None
        for key in ("assessment_ref", "source_ref", "stale_record_ref")
    ) or bool(_string_items(lifecycle.get("required_currentness_refs")))


def _repair_progress_followup_payload(
    *,
    action_type: str,
    owner: str,
    reason: str,
    next_work_unit: str,
    required_output_surface: str,
    route_target: str,
    evidence: Mapping[str, Any],
    receipt: Mapping[str, Any],
    evidence_path: Path,
    receipt_path: Path,
    source_eval_id: str | None,
    request_ref: str,
) -> dict[str, Any]:
    source_fingerprint = _text(evidence.get("source_fingerprint"))
    work_unit_fingerprint = source_fingerprint or _text(_mapping(evidence.get("repair_work_unit")).get("fingerprint"))
    return {
        "action_type": action_type,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": reason,
        "summary": (
            "A MAS owner repair already produced an accepted paper/product delta; route the current "
            "work unit to the next reviewer/gate owner instead of repeating the readiness check."
        ),
        "required_output_surface": required_output_surface,
        "route_target": route_target,
        "next_work_unit": next_work_unit,
        "executable_work_unit": next_work_unit,
        "controller_work_unit_id": next_work_unit,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_eval_id": source_eval_id,
        "source_fingerprint": source_fingerprint,
        "source_ref": str(evidence_path),
        "repair_execution_evidence_ref": str(evidence_path),
        "repair_execution_receipt_ref": str(receipt_path),
        "owner_receipt_ref": str(receipt_path),
        "repair_progress_request_ref": request_ref,
        "target_surface": {
            "surface": "owner_action_output_target_surface",
            "schema_version": 1,
            "action_type": action_type,
            "surface_ref": required_output_surface,
            "request_ref": request_ref,
            "source": "repair_execution_evidence.accepted_owner_receipt",
        },
        "repair_progress_followup": {
            "paper_delta_observed": True,
            "accepted_owner_receipt": True,
            "source_work_unit_id": _text(_mapping(evidence.get("repair_work_unit")).get("unit_id"))
            or _text(receipt.get("work_unit_id")),
            "source_fingerprint": source_fingerprint,
            "superseded_readiness_action": "complete_medical_paper_readiness_surface",
            "superseded_readiness_repair_action": "run_quality_repair_batch",
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _first_text_item(value: object) -> str | None:
    return next(iter(_string_items(value)), None)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


__all__ = [
    "REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH",
    "accepted_repair_progress_followup_action",
    "pending_ai_reviewer_recheck_consumes_current_write_routeback",
]
