from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from med_autoscience.paper_mission_transaction import PaperMissionTransaction


SURFACE_KIND = "mas_paper_mission_stage_run_context"
SOURCE_KIND = "paper_mission_transaction_artifact_context"
OPL_DOMAIN_ID = "mas"


def paper_mission_stage_run_context(
    transaction_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Build refs-only StageRun context without semantic transition authority."""
    transaction = PaperMissionTransaction.from_payload(transaction_payload).to_dict()
    transaction_id = _required_text(transaction, "transaction_id")
    mission_id = _required_text(transaction, "mission_id")
    study_id = _required_text(transaction, "study_id")
    stage_id = _required_text(transaction, "stage_id")
    stage_run_ref = _required_text(transaction, "stage_run_ref")
    decision = _mapping(transaction.get("stage_terminal_decision"))
    route = _mapping(transaction.get("ai_route_context"))
    idempotency = _mapping(transaction.get("idempotency"))
    idempotency_key = _optional_text(idempotency.get("idempotency_key")) or transaction_id
    transaction_fingerprint = (
        _optional_text(idempotency.get("transaction_fingerprint")) or transaction_id
    )
    work_unit_id = _optional_text(decision.get("work_unit_id")) or stage_id
    work_unit_fingerprint = (
        _optional_text(decision.get("work_unit_fingerprint"))
        or transaction_fingerprint
    )
    return validate_paper_mission_stage_run_context(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "source_kind": SOURCE_KIND,
            "domain_id": OPL_DOMAIN_ID,
            "route_selection_owner": "codex_cli",
            "paper_mission_transaction_ref": transaction_id,
            "stage_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
            "route_context_ref": f"{transaction_id}#ai_route_context",
            "stage_run_ref": stage_run_ref,
            "study_id": study_id,
            "mission_id": mission_id,
            "stage_id": stage_id,
            "action_type": _optional_text(decision.get("decision_kind"))
            or "artifact_context_available",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "route_identity_key": f"{transaction_id}::route",
            "attempt_idempotency_key": f"{idempotency_key}::opl-attempt",
            "idempotency_key": idempotency_key,
            "route_context": deepcopy(route),
            "quality_debt": list(transaction.get("transaction_quality_debt") or []),
            "declarative_target_stage_id": _optional_text(
                route.get("declarative_target_stage_id")
            ),
            "progress_first": {
                "artifact_is_next_stage_input": True,
                "negative_result_is_evidence": True,
                "next_stage_may_start": True,
                "route_may_skip_repeat_reverse_or_target_any_declared_stage": True,
                "blocks_stage_transition": False,
            },
            "authority_boundary": {
                "context_can_select_route": False,
                "context_can_reject_codex_route": False,
                "opl_can_run_semantic_transition_controller": False,
                "provider_completion_is_domain_completion": False,
            },
            "provider_admission_requires_opl_runtime_result": False,
            "carrier_status": "context_available",
            "next_stage_may_start": True,
        }
    )


def validate_paper_mission_stage_run_context(
    carrier: Mapping[str, Any],
) -> dict[str, Any]:
    payload = deepcopy(dict(carrier))
    if _required_text(payload, "surface_kind") != SURFACE_KIND:
        raise ValueError("paper mission StageRun context surface_kind mismatch")
    for field in (
        "paper_mission_transaction_ref",
        "stage_run_ref",
        "study_id",
        "stage_id",
        "route_identity_key",
        "attempt_idempotency_key",
    ):
        _required_text(payload, field)
    if payload.get("provider_admission_requires_opl_runtime_result") is not False:
        raise ValueError("StageRun context cannot require a semantic runtime result")
    if payload.get("next_stage_may_start") is not True:
        raise ValueError("StageRun context must preserve progress-first advancement")
    return payload


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = _optional_text(mapping.get(key))
    if value is None:
        raise ValueError(f"missing required text field: {key}")
    return value


def _optional_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


__all__ = [
    "SOURCE_KIND",
    "OPL_DOMAIN_ID",
    "SURFACE_KIND",
    "paper_mission_stage_run_context",
    "validate_paper_mission_stage_run_context",
]
