from __future__ import annotations

from collections.abc import Mapping
from typing import Any

FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
)


def diagnose_typed_blocker_resolution_gap(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
    profile_ref: str,
    source: str = "unknown",
) -> dict[str, Any]:
    validation = _validate_readback(
        paper_mission_readback=paper_mission_readback,
        study_id=study_id,
    )
    if validation["valid"] is not True:
        return {
            "surface_kind": "paper_mission_typed_blocker_resolution",
            "schema_version": 1,
            "status": "blocked_missing_consumed_typed_blocker_readback",
            "study_id": study_id,
            "profile_ref": profile_ref,
            "source": source,
            "write_permitted": False,
            "authority_materialized": False,
            "readback_validation": validation,
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        }

    package = _current_package_summary(paper_mission_readback)
    receipt = _mapping(paper_mission_readback.get("receipt_owner_consumption_readback"))
    decision = _mapping(paper_mission_readback.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    typed_ref = _first_text(
        _mapping(receipt.get("mas_receipt_consumption")).get("typed_blocker_evidence_ref"),
        outcome.get("typed_blocker_evidence_ref"),
    )
    blocker = _first_text(outcome.get("blocker_type"), "paper_mission_typed_blocker")
    return {
        "surface_kind": "paper_mission_typed_blocker_resolution",
        "schema_version": 1,
        "status": "blocked_missing_typed_blocker_resolution_surface",
        "study_id": study_id,
        "profile_ref": profile_ref,
        "source": source,
        "write_permitted": False,
        "authority_materialized": False,
        "paper_ready_claim_authorized": False,
        "publication_ready_claim_authorized": False,
        "submission_ready_claim_authorized": False,
        "readback_validation": validation,
        "typed_blocker": {
            "blocker_type": blocker,
            "next_owner": _text(outcome.get("next_owner")) or "MedAutoScience",
            "next_action": _text(outcome.get("next_action"))
            or "resolve_typed_blocker_or_route_redesign",
            "typed_blocker_evidence_ref": typed_ref,
        },
        "current_package": package,
        "owner_route_defect": {
            "defect_kind": "mas_typed_blocker_resolution_owner_surface_missing",
            "missing_command_or_api": (
                "paper-mission typed-blocker-resolution --apply-owner-decision "
                "| --apply-human-gate | --apply-route-redesign"
            ),
            "required_inputs": [
                "paper-mission inspect --request-opl-runtime-readback JSON",
                "next_action.action_family=blocked.typed",
                "receipt_owner_consumption_readback.status=owner_consumption_applied",
                "receipt_owner_consumption_readback.mas_receipt_consumption.status=owner_consumed_typed_blocker",
                "stage_closure_decision.outcome.kind=typed_blocker",
                "current_package projection",
            ],
            "allowed_write_set": [
                "MAS governed owner decision packet after authority contract exists",
                "MAS governed human gate after authority contract exists",
                "MAS governed route redesign / successor work-unit decision after authority contract exists",
                "non-authority diagnostic JSON returned by this command",
            ],
            "forbidden_write_set": list(FORBIDDEN_AUTHORITY_WRITES),
            "verification": [
                "focused CLI/controller tests",
                "fresh paper-mission inspect readback for DM002 and DM003",
                "fresh delivery-inspect readback before any submission-ready claim",
            ],
        },
        "next_legal_command": (
            "implement MAS typed-blocker resolution apply surface, then rerun "
            "paper-mission typed-blocker-resolution with the matching --apply-* mode"
        ),
        "forbidden_next_actions": [
            "synonymous OPL runtime redrive",
            "paper.gate.publishability_replay without a changed owner decision or source signature",
            "manual Yang authority/current_package/publication_eval/controller_decision edits",
        ],
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _validate_readback(
    *,
    paper_mission_readback: Mapping[str, Any],
    study_id: str,
) -> dict[str, Any]:
    missing: list[str] = []
    mismatched: list[str] = []
    if _text(paper_mission_readback.get("study_id")) != study_id:
        mismatched.append("study_id")
    next_action = _mapping(paper_mission_readback.get("next_action"))
    if _text(next_action.get("action_family")) != "blocked.typed":
        mismatched.append("next_action.action_family")
    if _text(next_action.get("action_kind")) != "stop_with_typed_blocker":
        mismatched.append("next_action.action_kind")
    if _text(next_action.get("owner")) != "mas_authority_kernel":
        mismatched.append("next_action.owner")

    decision = _mapping(paper_mission_readback.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    if not decision:
        missing.append("stage_closure_decision")
    elif _text(outcome.get("kind")) != "typed_blocker":
        mismatched.append("stage_closure_decision.outcome.kind")

    receipt = _mapping(paper_mission_readback.get("receipt_owner_consumption_readback"))
    if not receipt:
        missing.append("receipt_owner_consumption_readback")
    else:
        if _text(receipt.get("status")) != "owner_consumption_applied":
            mismatched.append("receipt_owner_consumption_readback.status")
        consumption = _mapping(receipt.get("mas_receipt_consumption"))
        if _text(consumption.get("status")) != "owner_consumed_typed_blocker":
            mismatched.append("receipt_owner_consumption_readback.mas_receipt_consumption.status")
    return {
        "valid": not missing and not mismatched,
        "missing_required_fields": missing,
        "mismatched_fields": mismatched,
    }


def _current_package_summary(readback: Mapping[str, Any]) -> dict[str, Any]:
    package = _mapping(readback.get("current_package"))
    return {
        "status": _first_text(package.get("status"), package.get("freshness_status")),
        "package_kind": _text(package.get("package_kind")),
        "can_submit": package.get("can_submit") is True,
        "quality_gate_status": _text(package.get("quality_gate_status")),
        "known_blockers": _text_list(package.get("known_blockers")),
        "root": _text(package.get("root")),
        "zip_path": _text(package.get("zip_path")),
        "zip_exists": package.get("zip_exists") is True,
        "generated_from_current_source": package.get("generated_from_current_source") is True,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text:
            return text
    return None


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]

