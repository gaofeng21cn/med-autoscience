from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.research_integrity.reference_verification import (
    build_reference_verification_payload,
)


SURFACE_KIND = "research_integrity_review_publication_gate_stage_hook"
SCHEMA_VERSION = 1
HOOK_ID = "research-integrity-review-publication-gate-stage-hook"
TRIGGERED_ACTION = "research-integrity-reference-verification"
TARGET_STAGE_IDS = (
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
)
TRIGGER_POINTS = (
    "reference_list_entered",
    "manuscript_closeout_entered",
    "review_gate_entered",
    "publication_gate_entered",
)
REQUIRED_GATE_INPUT_SURFACES = (
    "reference_verification_attestations",
    "claim_citation_support_matrix_v2",
    "manuscript_consistency_meta_review",
)
LOOKUP_PROVIDERS = (
    "crossref",
    "pubmed",
    "openalex",
    "semantic_scholar",
    "publisher",
    "crossmark",
)
FORBIDDEN_AUTHORITY_FLAGS = (
    "can_write_mas_study_truth",
    "can_write_publication_eval_latest",
    "can_write_publication_eval",
    "can_write_controller_decisions",
    "can_mutate_current_package",
    "can_write_current_package",
    "can_sign_owner_receipt",
    "can_write_owner_receipt",
    "can_materialize_typed_blocker",
    "can_write_typed_blocker",
    "can_materialize_human_gate",
    "can_write_runtime_queue_or_provider_attempt",
    "can_authorize_publication_quality",
    "can_authorize_publication_readiness",
    "can_authorize_submission_readiness",
)


def build_review_publication_gate_stage_hook_payload(
    *,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("research integrity stage hook `payload` 必须是 mapping。")

    reference_verification = build_reference_verification_payload(payload=payload)
    gate_input = _research_integrity_gate_input(reference_verification)
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "hook_id": HOOK_ID,
        "hook_role": "mandatory_review_publication_gate_input",
        "target_stage_ids": list(TARGET_STAGE_IDS),
        "stage_obligation": stage_obligation(),
        "stage_hook_consumers": ["review_gate", "publication_gate"],
        "trigger_points": list(TRIGGER_POINTS),
        "triggered_action": TRIGGERED_ACTION,
        "triggered_opl_connect_provider_lookup_contract": (
            triggered_opl_connect_provider_lookup_contract()
        ),
        "stage_launch_required_input": stage_launch_required_input(),
        "required_gate_input_surfaces": list(REQUIRED_GATE_INPUT_SURFACES),
        "status": reference_verification["status"],
        "stage_context": _stage_context(payload),
        "surfaces": {
            "research_integrity_reference_verification": reference_verification,
            "research_integrity_gate_input_bundle": gate_input,
        },
        "gate_input_bundle": gate_input,
        "blocker_candidates": reference_verification["blocker_candidates"],
        "review_candidates": reference_verification["review_candidates"],
        "authority_boundary": authority_boundary(),
    }


def stage_obligation() -> dict[str, Any]:
    return {
        "surface_kind": "research_integrity_stage_hook_obligation",
        "schema_version": SCHEMA_VERSION,
        "hook_id": HOOK_ID,
        "command": HOOK_ID,
        "obligation_level": "mandatory",
        "hook_role": "mandatory_review_publication_gate_input",
        "target_stage_ids": list(TARGET_STAGE_IDS),
        "trigger_points": list(TRIGGER_POINTS),
        "triggered_action": TRIGGERED_ACTION,
        "triggered_opl_connect_provider_lookup_contract": (
            triggered_opl_connect_provider_lookup_contract()
        ),
        "stage_launch_required_input": stage_launch_required_input(),
        "required_gate_input_surfaces": list(REQUIRED_GATE_INPUT_SURFACES),
        "mandatory_gate_input": True,
        "live_owner_consumption_claimed": False,
        "authority_boundary": authority_boundary(),
        "contract_ref": "contracts/research-integrity-layer.json#/stage_hook_obligation",
        "completion_boundary": completion_boundary(),
    }


def stage_launch_required_input(*, stage_id: str | None = None) -> dict[str, Any]:
    target_stage_ids = [stage_id] if stage_id else list(TARGET_STAGE_IDS)
    payload = {
        "surface_kind": "research_integrity_stage_launch_required_input",
        "schema_version": SCHEMA_VERSION,
        "hook_id": HOOK_ID,
        "command": HOOK_ID,
        "target_stage_ids": target_stage_ids,
        "launch_surface": "codex_cli_launch_packet",
        "readback_surface": "stage_contract.mandatory_pre_gate_checks",
        "triggered_action": TRIGGERED_ACTION,
        "trigger_points": list(TRIGGER_POINTS),
        "required_gate_input_surfaces": list(REQUIRED_GATE_INPUT_SURFACES),
        "triggered_opl_connect_provider_lookup_contract": (
            triggered_opl_connect_provider_lookup_contract()
        ),
        "mandatory_before_stage_completion": True,
        "required_before_owner_receipt_or_typed_blocker": True,
        "mandatory_gate_input": True,
        "live_owner_consumption_claimed": False,
        "authority_boundary": authority_boundary(),
    }
    if stage_id is not None:
        payload["stage_id"] = stage_id
    return payload


def completion_boundary() -> dict[str, Any]:
    return {
        "non_live_callable_stage_obligation_can_claim": True,
        "live_owner_consumption_claimed": False,
        "live_truth_requires": [
            "OPL Connect provider readback or receipt",
            "MAS owner surface consumption",
            "AI reviewer or publication gate receipt",
            "runtime or artifact readback for the exact study work unit",
        ],
    }


def triggered_opl_connect_provider_lookup_contract() -> dict[str, Any]:
    return {
        "surface_kind": "opl_connect_provider_lookup_contract",
        "schema_version": SCHEMA_VERSION,
        "owner": "OPL connector substrate",
        "triggered_by_hook_id": HOOK_ID,
        "triggered_action": TRIGGERED_ACTION,
        "lookup_providers": list(LOOKUP_PROVIDERS),
        "provider_receipt_consumed_by": TRIGGERED_ACTION,
        "mandatory_gate_input_only": True,
        "live_owner_consumption_claimed": False,
        "can_write_provider_attempt": False,
        "can_write_runtime_queue": False,
    }


def authority_boundary() -> dict[str, Any]:
    return {
        "outputs_are_gate_inputs": True,
        "surface_authority": "mandatory_stage_hook_gate_input_only",
        "can_request_provider_lookup": True,
        **{flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS},
    }


def _research_integrity_gate_input(reference_verification: Mapping[str, Any]) -> Mapping[str, Any]:
    surfaces = reference_verification.get("surfaces")
    if not isinstance(surfaces, Mapping):
        raise ValueError("reference verification output missing surfaces.")
    gate_input = surfaces.get("research_integrity_gate_input_bundle")
    if not isinstance(gate_input, Mapping):
        raise ValueError("reference verification output missing research_integrity_gate_input_bundle.")
    return gate_input


def _stage_context(payload: Mapping[str, Any]) -> dict[str, str]:
    context: dict[str, str] = {}
    for field_name in (
        "stage_id",
        "stage_event",
        "stage_hook_ref",
        "manuscript_ref",
        "reference_manager_ref",
    ):
        text = str(payload.get(field_name) or "").strip()
        if text:
            context[field_name] = text
    return context


__all__ = [
    "FORBIDDEN_AUTHORITY_FLAGS",
    "HOOK_ID",
    "LOOKUP_PROVIDERS",
    "REQUIRED_GATE_INPUT_SURFACES",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "TARGET_STAGE_IDS",
    "TRIGGERED_ACTION",
    "TRIGGER_POINTS",
    "authority_boundary",
    "build_review_publication_gate_stage_hook_payload",
    "completion_boundary",
    "stage_obligation",
    "stage_launch_required_input",
    "triggered_opl_connect_provider_lookup_contract",
]
