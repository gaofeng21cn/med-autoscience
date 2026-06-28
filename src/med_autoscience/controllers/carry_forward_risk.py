from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.owner_callable_action_policy import (
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


BUDGET_EXHAUSTED_SURFACE_KIND = "mas_progress_first_budget_exhausted_decision"
CARRY_FORWARD_RECEIPT_SURFACE_KIND = "mas_progress_first_carry_forward_risk_receipt"
CARRY_FORWARD_ACTION_TYPE = "run_quality_repair_batch"
CARRY_FORWARD_WORK_UNIT_ID = "publishability_repair_sprint"
CARRY_FORWARD_SOURCE = "progress_first_budget_exhausted.carry_forward_risk_receipt"


def carry_forward_status(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    decision = _budget_exhausted_decision(payload)
    if not decision:
        return None
    receipt = _receipt_from_decision(decision)
    return {
        key: value
        for key, value in {
            "surface_kind": "mas_progress_first_carry_forward_risk_status",
            "schema_version": 1,
            "status": "advanced_with_carry_forward_risk"
            if _decision_allows_successor(decision)
            else "blocked_for_fatal_risk",
            "decision": _text(decision.get("decision")),
            "severity": _text(decision.get("severity")),
            "fatal": decision.get("fatal") is True,
            "ordinary_progress_may_advance": decision.get("ordinary_progress_may_advance") is True,
            "readiness_claim_allowed": decision.get("readiness_claim_allowed") is True,
            "study_id": _text(decision.get("study_id")) or _text(receipt.get("study_id")),
            "action_type": _text(decision.get("action_type")) or _text(receipt.get("action_type")),
            "work_unit_id": _text(decision.get("work_unit_id")) or _text(receipt.get("work_unit_id")),
            "work_unit_fingerprint": _text(decision.get("work_unit_fingerprint"))
            or _text(receipt.get("work_unit_fingerprint")),
            "unresolved_reason": _text(receipt.get("unresolved_reason"))
            or _text(decision.get("blocker_reason")),
            "risk_owner": _text(receipt.get("risk_owner")),
            "next_route_policy": _text(receipt.get("next_route_policy")),
            "next_allowed_outcomes": _string_items(decision.get("next_allowed_outcomes")),
            "revisit_condition": _text(receipt.get("revisit_condition")),
            "authority_boundary": _carry_forward_authority_boundary(receipt),
            "forbidden_claims": _forbidden_claims(receipt),
            "carry_forward_risk_receipt": receipt or None,
        }.items()
        if value not in (None, "", [], {})
    }


def carry_forward_successor_action(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    decision = _budget_exhausted_decision(payload)
    if not _decision_allows_successor(decision):
        return None
    receipt = _receipt_from_decision(decision)
    if not receipt:
        return None
    study_id = _text(decision.get("study_id")) or _text(receipt.get("study_id"))
    work_unit_fingerprint = _text(decision.get("work_unit_fingerprint")) or _text(
        receipt.get("work_unit_fingerprint")
    )
    if study_id is None or work_unit_fingerprint is None:
        return None
    quest_id = _text(_mapping(payload).get("quest_id")) or _text(decision.get("quest_id"))
    successor_fingerprint = _successor_fingerprint(
        study_id=study_id,
        source_work_unit_fingerprint=work_unit_fingerprint,
        unresolved_reason=_text(receipt.get("unresolved_reason"))
        or _text(decision.get("blocker_reason")),
    )
    owner = request_owner_for_action_type(CARRY_FORWARD_ACTION_TYPE)
    target_surface = {
        "surface": "owner_action_output_target_surface",
        "schema_version": 1,
        "action_type": CARRY_FORWARD_ACTION_TYPE,
        "surface_ref": request_output_surface_for_action_type(CARRY_FORWARD_ACTION_TYPE),
        "source": "progress_first_carry_forward_risk",
    }
    owner_route = owner_route_part.ensure_owner_route_v2(
        {
            "surface": "domain_route_owner_route",
            "schema_version": 2,
            "study_id": study_id,
            "quest_id": quest_id,
            "truth_epoch": _text(decision.get("truth_epoch"))
            or f"carry-forward-risk::{study_id}",
            "route_epoch": _text(decision.get("truth_epoch"))
            or f"carry-forward-risk::{study_id}",
            "runtime_health_epoch": _text(decision.get("runtime_health_epoch")),
            "source_fingerprint": successor_fingerprint,
            "work_unit_fingerprint": successor_fingerprint,
            "current_owner": "mas_controller",
            "next_owner": owner,
            "owner_reason": "progress_first_carry_forward_risk",
            "failure_signature": "progress_first_carry_forward_risk",
            "allowed_actions": [CARRY_FORWARD_ACTION_TYPE],
            "blocked_actions": [],
            "idempotency_key": f"owner-route::{study_id}::carry-forward-risk::{successor_fingerprint}",
            "source_refs": {
                "source": CARRY_FORWARD_SOURCE,
                "budget_exhausted_decision_ref": BUDGET_EXHAUSTED_SURFACE_KIND,
                "carry_forward_risk_receipt_ref": CARRY_FORWARD_RECEIPT_SURFACE_KIND,
                "source_action_type": _text(decision.get("action_type")),
                "source_work_unit_id": _text(decision.get("work_unit_id")),
                "source_work_unit_fingerprint": work_unit_fingerprint,
                "work_unit_id": CARRY_FORWARD_WORK_UNIT_ID,
                "work_unit_fingerprint": successor_fingerprint,
                "owner_route_currentness_basis": {
                    "source": CARRY_FORWARD_SOURCE,
                    "source_eval_id": CARRY_FORWARD_RECEIPT_SURFACE_KIND,
                    "truth_epoch": _text(decision.get("truth_epoch"))
                    or f"carry-forward-risk::{study_id}",
                    "runtime_health_epoch": _text(decision.get("runtime_health_epoch")),
                    "work_unit_id": CARRY_FORWARD_WORK_UNIT_ID,
                    "work_unit_fingerprint": successor_fingerprint,
                },
            },
        }
    )
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": CARRY_FORWARD_ACTION_TYPE,
        "action_id": f"carry-forward-risk-successor::{study_id}",
        "reason": "progress_first_budget_exhausted_nonfatal_carry_forward",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
        "next_owner": owner,
        "authority": CARRY_FORWARD_SOURCE,
        "required_output_surface": request_output_surface_for_action_type(CARRY_FORWARD_ACTION_TYPE),
        "source": CARRY_FORWARD_SOURCE,
        "source_surface": CARRY_FORWARD_SOURCE,
        "source_ref": CARRY_FORWARD_RECEIPT_SURFACE_KIND,
        "work_unit_id": CARRY_FORWARD_WORK_UNIT_ID,
        "next_work_unit": CARRY_FORWARD_WORK_UNIT_ID,
        "work_unit_fingerprint": successor_fingerprint,
        "action_fingerprint": successor_fingerprint,
        "allowed_actions": [CARRY_FORWARD_ACTION_TYPE],
        "required_delta_kind": "carry_forward_risk_repair_delta_or_typed_blocker",
        "target_surface": target_surface,
        "acceptance_refs": [
            "canonical_manuscript_story_surface_delta",
            "typed_blocker:manuscript_story_surface_delta_missing",
            CARRY_FORWARD_RECEIPT_SURFACE_KIND,
        ],
        "owner_receipt_required": True,
        "carry_forward_risk": carry_forward_status(payload),
        "forbidden_claims": _forbidden_claims(receipt),
        "owner_route_currentness_basis": _mapping(
            _mapping(owner_route.get("source_refs")).get("owner_route_currentness_basis")
        ),
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": CARRY_FORWARD_ACTION_TYPE,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": CARRY_FORWARD_SOURCE,
            "source_ref": CARRY_FORWARD_RECEIPT_SURFACE_KIND,
            "work_unit_id": CARRY_FORWARD_WORK_UNIT_ID,
            "work_unit_fingerprint": successor_fingerprint,
            "action_fingerprint": successor_fingerprint,
            "required_delta_kind": "carry_forward_risk_repair_delta_or_typed_blocker",
            "target_surface": target_surface,
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in action.items() if value not in (None, "", [], {})}


def fatal_budget_exhausted_blocker(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    decision = _budget_exhausted_decision(payload)
    if _text(decision.get("surface_kind")) != BUDGET_EXHAUSTED_SURFACE_KIND:
        return None
    if _text(decision.get("decision")) != "block_for_fatal_risk":
        return None
    if decision.get("fatal") is not True:
        return None
    source = _mapping(payload)
    study_id = _text(decision.get("study_id")) or _text(source.get("study_id"))
    reason = _text(decision.get("blocker_reason")) or "fatal_budget_exhausted_risk"
    work_unit_id = _text(decision.get("work_unit_id")) or _text(decision.get("action_type"))
    fingerprint = _text(decision.get("work_unit_fingerprint"))
    basis = {
        key: value
        for key, value in {
            "source": "progress_first_budget_exhausted.fatal_blocker",
            "source_eval_id": BUDGET_EXHAUSTED_SURFACE_KIND,
            "truth_epoch": _text(decision.get("truth_epoch"))
            or (f"fatal-budget::{study_id}" if study_id else None),
            "runtime_health_epoch": _text(decision.get("runtime_health_epoch")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        }.items()
        if value is not None
    }
    return {
        key: value
        for key, value in {
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_type": reason,
            "blocker_kind": reason,
            "blocked_reason": reason,
            "reason": reason,
            "owner": "MedAutoScience",
            "write_permitted": False,
            "study_id": study_id,
            "action_type": _text(decision.get("action_type")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_ref": BUDGET_EXHAUSTED_SURFACE_KIND,
            "budget_exhausted_decision": dict(decision),
            "fatal_budget_exhausted_risk": carry_forward_status(payload),
            "currentness_basis": basis,
            "owner_route_currentness_basis": basis,
        }.items()
        if value not in (None, "", [], {})
    }


def _budget_exhausted_decision(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _mapping(payload)
    if _text(source.get("surface_kind")) == BUDGET_EXHAUSTED_SURFACE_KIND:
        return source
    for candidate in _candidate_mappings(source):
        if _text(candidate.get("surface_kind")) == BUDGET_EXHAUSTED_SURFACE_KIND:
            return candidate
    return {}


def _candidate_mappings(payload: Mapping[str, Any]) -> Iterable[dict[str, Any]]:
    for key in (
        "budget_exhausted_decision",
        "progress_first_budget_exhausted_decision",
    ):
        candidate = _mapping(payload.get(key))
        if candidate:
            yield candidate
    for parent_key in (
        "carry_forward_policy",
        "anti_loop_budget",
        "typed_blocker",
        "current_execution_envelope",
        "progress_first_monitoring_summary",
        "progress_first",
    ):
        parent = _mapping(payload.get(parent_key))
        if parent:
            yield from _candidate_mappings(parent)
    current_work_unit = _mapping(payload.get("current_work_unit"))
    if current_work_unit:
        yield from _candidate_mappings(_mapping(current_work_unit.get("state")))
        yield from _candidate_mappings(_mapping(current_work_unit.get("typed_blocker")))


def _decision_allows_successor(decision: Mapping[str, Any]) -> bool:
    if _text(decision.get("surface_kind")) != BUDGET_EXHAUSTED_SURFACE_KIND:
        return False
    if _text(decision.get("decision")) != "advance_with_carry_forward_risk":
        return False
    if decision.get("fatal") is True:
        return False
    if decision.get("ordinary_progress_may_advance") is not True:
        return False
    return bool(_receipt_from_decision(decision))


def _receipt_from_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _mapping(decision.get("carry_forward_risk_receipt"))
    if _text(receipt.get("surface_kind")) != CARRY_FORWARD_RECEIPT_SURFACE_KIND:
        return {}
    return receipt


def _carry_forward_authority_boundary(receipt: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(receipt.get("authority_boundary"))
    boundary = {
        "authority": False,
        "projection_only": True,
        "can_claim_publication_ready": False,
        "can_claim_submission_ready": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "can_write_paper_body": False,
        "can_write_current_package": False,
    }
    boundary.update(explicit)
    return boundary


def _forbidden_claims(receipt: Mapping[str, Any]) -> list[str]:
    explicit = _string_items(receipt.get("forbidden_claims"))
    if explicit:
        return explicit
    return [
        "publication_ready",
        "submission_ready",
        "quality_complete",
        "readiness_complete",
        "controller_decision_written",
        "publication_eval_written",
        "paper_body_written",
        "current_package_written",
    ]


def _successor_fingerprint(
    *,
    study_id: str,
    source_work_unit_fingerprint: str,
    unresolved_reason: str | None,
) -> str:
    encoded = json.dumps(
        {
            "source": CARRY_FORWARD_SOURCE,
            "source_work_unit_fingerprint": source_work_unit_fingerprint,
            "study_id": study_id,
            "unresolved_reason": unresolved_reason,
            "work_unit_id": CARRY_FORWARD_WORK_UNIT_ID,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"carry-forward-risk::{study_id}::{digest}"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = [
    "BUDGET_EXHAUSTED_SURFACE_KIND",
    "CARRY_FORWARD_ACTION_TYPE",
    "CARRY_FORWARD_RECEIPT_SURFACE_KIND",
    "CARRY_FORWARD_SOURCE",
    "CARRY_FORWARD_WORK_UNIT_ID",
    "carry_forward_status",
    "carry_forward_successor_action",
    "fatal_budget_exhausted_blocker",
]
