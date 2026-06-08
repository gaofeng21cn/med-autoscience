from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_output_surface_for_action_type,
)


ACTION_TYPE = "publication_handoff_owner_gate"
OWNER = "publication_gate_owner"
READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
READINESS_OWNER = "MedAutoScience"
READINESS_BLOCKER = "medical_paper_readiness_not_ready"
READINESS_MISSING_BLOCKER = "medical_paper_readiness_missing"
READINESS_REPAIR_ACTION_TYPE = "run_quality_repair_batch"
READINESS_REPAIR_OWNER = "write"
READINESS_REPAIR_REASON = "medical_paper_readiness_repair_required"
READINESS_REPAIR_WORK_UNIT = "readiness_blocker_publication_repair"
READINESS_GATE_REPAIR_ACTION_TYPE = "run_gate_clearing_batch"
READINESS_GATE_REPAIR_OWNER = "gate_clearing_batch"
READINESS_GATE_REPAIR_WORK_UNIT = "readiness_blocker_publication_gate_replay"

_WRITE_REPAIR_GAPS = frozenset(
    {
        "claim_evidence_consistency_failed",
        "claim_evidence_map_missing",
        "claim_evidence_map_missing_or_incomplete",
        "medical_publication_surface_blocked",
        "reviewer_first_concerns_unresolved",
        "storyline_not_publication_ready",
        "unsupported_citation_blockers_present",
    }
)
_GATE_REPAIR_GAPS = frozenset(
    {
        "current_package_stale",
        "stale_submission_minimal_authority",
        "submission_hardening_incomplete",
        "submission_minimal_missing",
        "submission_minimal_stale",
    }
)


def typed_blocker_followup_action(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    if _medical_paper_readiness_ready(progress):
        return None
    delta = _current_owner_delta(progress)
    if _readiness_action(delta) != READINESS_ACTION_TYPE:
        return None
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return None
    source_ref = _text(delta.get("source_ref"))
    readiness = _mapping(progress.get("medical_paper_readiness"))
    next_action = _readiness_next_action(readiness=readiness, delta=delta)
    surface_key = _readiness_surface_key(next_action=next_action, delta=delta)
    if not _readiness_next_action_identifies_followup(
        next_action=next_action,
        surface_key=surface_key,
    ):
        return None
    work_unit_fingerprint = (
        _text(delta.get("delta_id"))
        or _readiness_work_unit_fingerprint(
            source_ref=source_ref,
            surface_key=surface_key,
        )
    )
    return {
        "action_type": READINESS_ACTION_TYPE,
        "authority": "mas_owner_surface",
        "owner": _text(delta.get("owner")) or READINESS_OWNER,
        "request_owner": _text(delta.get("owner")) or READINESS_OWNER,
        "recommended_owner": _text(delta.get("owner")) or READINESS_OWNER,
        "reason": _text(delta.get("reason")) or READINESS_BLOCKER,
        "summary": "Complete the MAS medical-paper readiness surface named by the terminal handoff typed blocker.",
        "required_output_surface": _text(delta.get("required_input")) or READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "next_action": next_action or None,
        "work_unit_id": READINESS_ACTION_TYPE,
        "next_work_unit": READINESS_ACTION_TYPE,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_ref": source_ref,
        "source_surface": "stage_kernel_projection.current_owner_delta",
        "blocked_surface": _text(delta.get("blocked_surface")) or ACTION_TYPE,
        "latest_owner_answer_ref": _text(delta.get("latest_owner_answer_ref")) or source_ref,
        "latest_owner_answer_kind": _text(delta.get("latest_owner_answer_kind")) or _text(delta.get("source_kind")),
        "terminal_publication_handoff": False,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
    }


def readiness_blocker_repair_action(
    *,
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if _medical_paper_readiness_ready(progress):
        return None
    delta = _current_owner_delta(progress)
    if _readiness_action(delta) != READINESS_ACTION_TYPE:
        return None
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return None
    blocker_reason = _text(delta.get("reason")) or _text(delta.get("latest_owner_answer_reason"))
    if blocker_reason != READINESS_MISSING_BLOCKER:
        return None
    gap_ids = _publication_eval_gap_ids(publication_eval_payload or {})
    if not gap_ids:
        return None
    action_type, owner, work_unit = _readiness_repair_route(gap_ids)
    if action_type is None or owner is None or work_unit is None:
        return None
    source_ref = _text(delta.get("source_ref"))
    source_eval_id = _text(_mapping(publication_eval_payload).get("eval_id"))
    fingerprint = _readiness_repair_work_unit_fingerprint(
        source_eval_id=source_eval_id,
        gap_ids=gap_ids,
    )
    return {
        "action_type": action_type,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": READINESS_REPAIR_REASON,
        "summary": (
            "Stage 08 recorded a stable medical-paper readiness blocker; derive the next owner "
            "repair from publication_eval gaps instead of re-running the same readiness check."
        ),
        "required_output_surface": _readiness_repair_required_output_surface(action_type),
        "route_target": "write" if owner == READINESS_REPAIR_OWNER else "publication_gate",
        "next_work_unit": work_unit,
        "executable_work_unit": work_unit,
        "controller_work_unit_id": work_unit,
        "work_unit_fingerprint": fingerprint,
        "source_surface": "stage_kernel_projection.current_owner_delta",
        "source_ref": source_ref,
        "readiness_blocker_ref": source_ref,
        "source_eval_id": source_eval_id,
        "publication_eval_gap_ids": gap_ids,
        "readiness_blocker_followup_superseded": READINESS_ACTION_TYPE,
        "blocked_surface": _text(delta.get("blocked_surface")) or ACTION_TYPE,
        "latest_owner_answer_ref": _text(delta.get("latest_owner_answer_ref")) or source_ref,
        "latest_owner_answer_kind": _text(delta.get("latest_owner_answer_kind")) or _text(delta.get("source_kind")),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "readiness_repair_contract": {
            "diagnostic_blocker": READINESS_MISSING_BLOCKER,
            "repeated_readiness_check_allowed": False,
            "accepted_owner_outputs": [
                "canonical manuscript story-surface delta",
                "claim-evidence semantic delta",
                "review ledger or reviewer/gate delta",
                "stable typed blocker for the concrete repair unit",
            ],
        },
    }


def terminal_publication_handoff_action(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    index = _mapping(progress.get("stage_artifact_index"))
    if _text(index.get("surface_kind")) != "stage_artifact_index":
        return None
    owner_action = _mapping(index.get("next_owner_action"))
    if _text(owner_action.get("action_type")) != ACTION_TYPE:
        return None
    if owner_action.get("terminal_publication_handoff") is not True and (
        _text(owner_action.get("required_delta_kind"))
        != "publication_handoff_owner_receipt_or_typed_blocker"
    ):
        return None
    work_unit_id = _text(owner_action.get("work_unit_id")) or ACTION_TYPE
    current_stage = _stage_id(index.get("current_stage")) or "08-publication_package_handoff"
    owner = _text(owner_action.get("next_owner")) or OWNER
    contract_refs = _stage_artifact_contract_refs(owner_action)
    return {
        "action_type": ACTION_TYPE,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": ACTION_TYPE,
        "summary": "Evaluate terminal publication handoff and write an owner receipt or stable typed blocker.",
        "required_output_surface": _text(owner_action.get("required_output_surface"))
        or request_output_surface_for_action_type(ACTION_TYPE),
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "work_unit_fingerprint": _text(owner_action.get("work_unit_fingerprint"))
        or f"stage-artifact-index::{current_stage}::{work_unit_id}",
        "source_ref": _text(owner_action.get("source_ref"))
        or _text(owner_action.get("manifest_ref"))
        or _text(owner_action.get("receipt_ref")),
        "source_surface": "stage_artifact_index.next_owner_action",
        "stage_artifact_index_source": "stage_artifact_index.next_owner_action",
        "stage_artifact_current_stage": current_stage,
        "stage_artifact_contract_refs": contract_refs,
        "required_delta_kind": _text(owner_action.get("required_delta_kind")),
        "target_surface": _mapping(owner_action.get("target_surface")) or None,
        "artifact_first_authority": True,
        "terminal_publication_handoff": True,
        "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission_ready": False,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def action_queue_with_terminal_publication_handoff(
    *,
    actions: list[dict[str, Any]],
    progress: Mapping[str, Any],
    study_id: str,
    quest_id: str | None,
    decorate_action: Callable[..., dict[str, Any]],
    publication_eval_payload: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    repair = readiness_blocker_repair_action(
        progress=progress,
        publication_eval_payload=publication_eval_payload,
    )
    if repair is not None:
        return [decorate_action(study_id=study_id, quest_id=quest_id, action=repair)]
    followup = typed_blocker_followup_action(progress)
    if followup is not None:
        return [decorate_action(study_id=study_id, quest_id=quest_id, action=followup)]
    if _stage_kernel_readiness_answer_without_followup(progress):
        return []
    if _has_current_controller_action(actions):
        return actions
    action = terminal_publication_handoff_action(progress)
    if action is None:
        return actions
    return [decorate_action(study_id=study_id, quest_id=quest_id, action=action)]


def projection_fields(progress: Mapping[str, Any], actions: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    stage_artifact_index = _mapping(progress.get("stage_artifact_index"))
    current_action = _mapping(progress.get("current_executable_owner_action"))
    result: dict[str, Any] = {}
    if _text(stage_artifact_index.get("surface_kind")) == "stage_artifact_index":
        result["stage_artifact_index"] = stage_artifact_index
    repair_action = _readiness_repair_action_from_actions(actions or [])
    if repair_action is not None:
        result["current_executable_owner_action"] = _projection_action_from_repair(repair_action)
        return result
    followup = typed_blocker_followup_action(progress)
    if followup is not None:
        result["current_executable_owner_action"] = _projection_action_from_followup(followup)
        return result
    if _stage_kernel_readiness_answer_without_followup(progress):
        return result
    if _has_current_controller_action(actions or []):
        return result
    if _text(current_action.get("surface_kind")) == "current_executable_owner_action":
        result["current_executable_owner_action"] = current_action
    return result


def _readiness_repair_action_from_actions(actions: list[Mapping[str, Any]]) -> dict[str, Any] | None:
    for action in actions:
        payload = _mapping(action)
        if _text(payload.get("reason")) != READINESS_REPAIR_REASON:
            continue
        if _text(payload.get("readiness_blocker_followup_superseded")) != READINESS_ACTION_TYPE:
            continue
        if _text(payload.get("action_type")) not in {
            READINESS_REPAIR_ACTION_TYPE,
            READINESS_GATE_REPAIR_ACTION_TYPE,
        }:
            continue
        return payload
    return None


def _has_current_controller_action(actions: list[Mapping[str, Any]]) -> bool:
    for action in actions:
        if _mapping(action.get("controller_route")).get("decision_path"):
            return True
    return False


def _stage_artifact_contract_refs(owner_action: Mapping[str, Any]) -> dict[str, str]:
    refs = {
        "manifest_ref": _text(owner_action.get("manifest_ref")),
        "receipt_ref": _text(owner_action.get("receipt_ref")),
        "artifact_native_contract_ref": _text(owner_action.get("artifact_native_contract_ref")),
        "domain_stage_pack_ref": _text(owner_action.get("domain_stage_pack_ref")),
    }
    return {key: value for key, value in refs.items() if value is not None}


def _projection_action_from_followup(action: Mapping[str, Any]) -> dict[str, Any]:
    target_surface = {
        "ref_kind": "mas_owner_surface",
        "surface_ref": _text(action.get("required_output_surface")) or READINESS_ACTION_TYPE,
        "blocked_surface": _text(action.get("blocked_surface")) or ACTION_TYPE,
    }
    if surface_key := _text(action.get("surface_key")):
        target_surface["surface_key"] = surface_key
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": _text(action.get("source_surface")) or "stage_kernel_projection.current_owner_delta",
        "next_owner": _text(action.get("owner")) or READINESS_OWNER,
        "work_unit_id": _text(action.get("work_unit_id")) or READINESS_ACTION_TYPE,
        "allowed_actions": [_text(action.get("action_type")) or READINESS_ACTION_TYPE],
        "owner_receipt_required": True,
        "required_delta_kind": "medical_paper_readiness_surface_or_typed_blocker",
        "target_surface": target_surface,
        "target_surface_specificity": "stage_kernel_typed_blocker_followup",
        "surface_key": _text(action.get("surface_key")),
        "next_action": _mapping(action.get("next_action")) or None,
        "blocked_surface": _text(action.get("blocked_surface")) or ACTION_TYPE,
        "source_ref": _text(action.get("source_ref")),
        "latest_owner_answer_ref": _text(action.get("latest_owner_answer_ref"))
        or _text(action.get("source_ref")),
        "latest_owner_answer_kind": _text(action.get("latest_owner_answer_kind")),
        "artifact_first_precedence": {
            "superseded_stage_artifact_action": ACTION_TYPE,
            "reason": _text(action.get("reason")) or "medical_paper_readiness_not_ready",
            "typed_blocker_followup_takes_precedence": True,
        },
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _projection_action_from_repair(action: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _text(action.get("action_type")) or READINESS_REPAIR_ACTION_TYPE
    owner = _text(action.get("owner")) or READINESS_REPAIR_OWNER
    work_unit = _text(action.get("next_work_unit")) or _text(action.get("work_unit_id")) or READINESS_REPAIR_WORK_UNIT
    target_surface = {
        "ref_kind": "mas_owner_surface",
        "surface_ref": _text(action.get("required_output_surface"))
        or _readiness_repair_required_output_surface(action_type),
        "blocked_surface": _text(action.get("blocked_surface")) or ACTION_TYPE,
    }
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": _text(action.get("source_surface")) or "stage_kernel_projection.current_owner_delta",
        "next_owner": owner,
        "work_unit_id": work_unit,
        "allowed_actions": [action_type],
        "owner_receipt_required": True,
        "required_delta_kind": (
            "paper_product_semantic_delta_or_concrete_typed_blocker"
            if action_type == READINESS_REPAIR_ACTION_TYPE
            else "publication_gate_delta_or_concrete_typed_blocker"
        ),
        "target_surface": target_surface,
        "target_surface_specificity": "readiness_blocker_derived_repair",
        "source_ref": _text(action.get("source_ref")),
        "latest_owner_answer_ref": _text(action.get("latest_owner_answer_ref"))
        or _text(action.get("source_ref")),
        "latest_owner_answer_kind": _text(action.get("latest_owner_answer_kind")),
        "publication_eval_gap_ids": _text_items(action.get("publication_eval_gap_ids")),
        "artifact_first_precedence": {
            "superseded_stage_artifact_action": READINESS_ACTION_TYPE,
            "reason": READINESS_MISSING_BLOCKER,
            "typed_blocker_followup_takes_precedence": False,
            "publication_eval_gap_repair_takes_precedence": True,
        },
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _readiness_next_action(*, readiness: Mapping[str, Any], delta: Mapping[str, Any]) -> dict[str, Any]:
    next_action = _mapping(delta.get("next_action")) or _mapping(readiness.get("next_action"))
    if not next_action:
        return {}
    return {
        key: value
        for key, value in next_action.items()
        if value not in (None, "", [], {})
    }


def _readiness_surface_key(*, next_action: Mapping[str, Any], delta: Mapping[str, Any]) -> str | None:
    return _text(delta.get("surface_key")) or _text(next_action.get("surface_key"))


def _readiness_next_action_identifies_followup(
    *,
    next_action: Mapping[str, Any],
    surface_key: str | None,
) -> bool:
    if not next_action:
        return False
    if surface_key is not None:
        return True
    action = _text(next_action.get("action_id")) or _text(next_action.get("action_type"))
    if action is not None and action not in {READINESS_ACTION_TYPE, "continue_managed_execution"}:
        return True
    if _text(next_action.get("route_target")) or _text(next_action.get("next_owner")):
        return True
    if _text(next_action.get("work_unit_id")):
        return True
    return bool(_mapping(next_action.get("target_surface")))


def _readiness_action(delta: Mapping[str, Any]) -> str | None:
    return _text(delta.get("action")) or _text(delta.get("action_type"))


def _stage_kernel_readiness_answer_without_followup(progress: Mapping[str, Any]) -> bool:
    if _medical_paper_readiness_ready(progress):
        return False
    delta = _current_owner_delta(progress)
    if _readiness_action(delta) != READINESS_ACTION_TYPE:
        return False
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return False
    next_action = _readiness_next_action(
        readiness=_mapping(progress.get("medical_paper_readiness")),
        delta=delta,
    )
    surface_key = _readiness_surface_key(next_action=next_action, delta=delta)
    return not _readiness_next_action_identifies_followup(
        next_action=next_action,
        surface_key=surface_key,
    )


def _is_stage_kernel_typed_blocker_followup(delta: Mapping[str, Any]) -> bool:
    if _text(delta.get("reason")) == READINESS_BLOCKER:
        return True
    if _text(delta.get("source_kind")) == "typed_blocker":
        return True
    if _text(delta.get("required_input")) == READINESS_ACTION_TYPE:
        return True
    if _text(delta.get("blocked_surface")) == ACTION_TYPE:
        return True
    if _text(delta.get("latest_owner_answer_kind")) == "typed_blocker":
        return True
    return bool(_text_items(delta.get("typed_blocker_refs")))


def _readiness_work_unit_fingerprint(*, source_ref: str | None, surface_key: str | None) -> str:
    suffix = surface_key or "unspecified_surface"
    return f"stage-current-owner-delta::{READINESS_ACTION_TYPE}::{suffix}::{source_ref or 'unknown'}"


def _readiness_repair_route(gap_ids: list[str]) -> tuple[str | None, str | None, str | None]:
    gap_set = set(gap_ids)
    if gap_set & _WRITE_REPAIR_GAPS:
        return READINESS_REPAIR_ACTION_TYPE, READINESS_REPAIR_OWNER, READINESS_REPAIR_WORK_UNIT
    if gap_set & _GATE_REPAIR_GAPS:
        return READINESS_GATE_REPAIR_ACTION_TYPE, READINESS_GATE_REPAIR_OWNER, READINESS_GATE_REPAIR_WORK_UNIT
    return None, None, None


def _readiness_repair_required_output_surface(action_type: str) -> str:
    if action_type == READINESS_GATE_REPAIR_ACTION_TYPE:
        return (
            "publication gate replay/currentness delta or "
            "typed blocker:readiness_blocker_publication_gate_replay_required"
        )
    return (
        "canonical manuscript story-surface delta, claim-evidence semantic delta, "
        "reviewer/gate delta, or typed blocker:readiness_blocker_publication_repair_required"
    )


def _readiness_repair_work_unit_fingerprint(
    *,
    source_eval_id: str | None,
    gap_ids: list[str],
) -> str:
    eval_part = source_eval_id or "unknown-publication-eval"
    gap_part = "+".join(sorted(gap_ids)) if gap_ids else "unspecified-gap"
    return f"readiness-blocker-repair::{eval_part}::{gap_part}"


def _publication_eval_gap_ids(publication_eval_payload: Mapping[str, Any]) -> list[str]:
    gap_ids: list[str] = []
    for gap in publication_eval_payload.get("gaps") or []:
        if not isinstance(gap, Mapping):
            continue
        for key in ("gap_id", "blocker", "blocking_reason", "reason", "id"):
            _append_unique_text(gap_ids, gap.get(key))
        for key in ("blockers", "blocking_reasons"):
            for item in _text_items(gap.get(key)):
                _append_unique_text(gap_ids, item)
    return gap_ids


def _append_unique_text(items: list[str], value: object) -> None:
    text = _text(value)
    if text is not None and text not in items:
        items.append(text)


def _current_owner_delta(progress: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(progress.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    delta = _mapping(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return _mapping(stage_run_kernel.get("current_owner_delta"))


def _medical_paper_readiness_ready(progress: Mapping[str, Any]) -> bool:
    readiness = _mapping(progress.get("medical_paper_readiness"))
    return _text(readiness.get("overall_status")) == "ready"


def _stage_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("stage_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = [
    "ACTION_TYPE",
    "OWNER",
    "action_queue_with_terminal_publication_handoff",
    "projection_fields",
    "readiness_blocker_repair_action",
    "terminal_publication_handoff_action",
    "typed_blocker_followup_action",
]
