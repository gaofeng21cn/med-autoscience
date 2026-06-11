from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.agent_tool_arsenal import (
    build_agent_tool_arsenal_index,
    build_capability_invocation_plan,
)
from med_autoscience.scientific_capability_registry import (
    build_capability_owner_consumption_evidence,
    resolve_scientific_capabilities,
)


SURFACE_KIND = "mas_hosted_ordinary_path_consumption_evidence"
SCHEMA_VERSION = 1
CONTRACT_REF = "contracts/hosted_ordinary_path_consumption.json"


def build_hosted_ordinary_path_consumption_evidence(
    *,
    current_owner_delta: Mapping[str, Any],
    invocation_result: Mapping[str, Any] | None = None,
    owner_response_refs: Mapping[str, Any] | None = None,
    arsenal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = arsenal if arsenal is not None else build_agent_tool_arsenal_index()
    plan = build_capability_invocation_plan(
        current_owner_delta=current_owner_delta,
        arsenal=payload,
    )
    resolution = resolve_scientific_capabilities(
        current_owner_delta=current_owner_delta,
    )
    consumption_evidence = (
        build_capability_owner_consumption_evidence(
            invocation_result=invocation_result,
            current_owner_delta=current_owner_delta,
            owner_response_refs=owner_response_refs,
        )
        if isinstance(invocation_result, Mapping)
        else None
    )
    selected_capabilities = [
        _capability_digest(item)
        for item in _mapping_list(resolution.get("selected_capabilities"))
    ]
    primary_card = _mapping(plan.get("primary_operational_card"))
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "contract_ref": CONTRACT_REF,
        "status": "ready_for_hosted_consumption",
        "ordinary_planning_root": "current_owner_delta",
        "hosted_runtime_owner": "one-person-lab",
        "domain_owner": "MedAutoScience",
        "current_owner_delta_identity": _current_owner_summary(current_owner_delta),
        "ordinary_path_consumes": {
            "agent_execution_index": True,
            "operational_tool_card": True,
            "capability_invocation_plan": True,
            "tool_result_envelope_recovery": True,
            "scientific_capability_resolution": True,
            "owner_consumption_evidence_packet": consumption_evidence is not None,
        },
        "agent_execution_index_ref": "contracts/agent_tool_arsenal.json#/agent_execution_index",
        "primary_operational_card_ref": _primary_card_ref(plan),
        "capability_invocation_plan": _plan_digest(plan),
        "result_envelope_schema_ref": _text(plan.get("result_envelope_schema_ref")),
        "lightweight_executor_receipt_contract_ref": _text(
            plan.get("lightweight_executor_receipt_contract_ref")
        ),
        "primary_operational_card": {
            "card_kind": _text(primary_card.get("card_kind")),
            "tool_id": _text(primary_card.get("tool_id")),
            "tool_mode": _text(primary_card.get("tool_mode")),
            "action_id": _text(primary_card.get("action_id")),
            "action_type": _text(primary_card.get("action_type")),
            "default_invocation": dict(_mapping(primary_card.get("default_invocation"))),
            "required_refs": _text_list(primary_card.get("required_refs")),
            "preflight_checks": _text_list(primary_card.get("preflight_checks")),
            "next_safe_actions": list(primary_card.get("next_safe_actions") or []),
            "allowed_writes": _text_list(primary_card.get("allowed_writes")),
            "forbidden_authority": _text_list(primary_card.get("forbidden_authority")),
        },
        "scientific_capability_resolution": {
            "status": _text(resolution.get("status")),
            "selected_count": int(resolution.get("selected_count") or 0),
            "selected_capabilities": selected_capabilities,
            "fail_open": bool(resolution.get("fail_open")),
            "mainline_waits_for_capability": bool(
                resolution.get("mainline_waits_for_capability")
            ),
            "missing_capability_blocks_owner_action": bool(
                resolution.get("missing_capability_blocks_owner_action")
            ),
        },
        "owner_consumption_evidence": (
            _owner_consumption_digest(consumption_evidence)
            if isinstance(consumption_evidence, Mapping)
            else None
        ),
        "friction_policy": {
            "human_operator_manual_tool_selection_required": False,
            "raw_contract_direct_read_required": False,
            "default_preflight_added": False,
            "sidecar_blocks_owner_action": False,
            "missing_capability_blocks_owner_action": False,
            "missing_owner_response_refs_blocks": False,
            "mainline_waits_for_live_soak": False,
            "docker_or_dind_required": False,
        },
        "authority_boundary": {
            "evidence_packet_is_authority_outcome": False,
            "can_write_domain_truth": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_write_paper_or_package": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_authorize_publication_quality": False,
            "can_authorize_artifact_authority": False,
            "can_block_current_owner_action": False,
        },
    }


def build_hosted_ordinary_path_consumption_contract() -> dict[str, Any]:
    sample_delta = {
        "action_type": "run_quality_repair_batch",
        "action_id": "hosted-ordinary-path-sample",
        "owner": "MedAutoScience",
        "work_unit_id": "hosted-consumption-sample",
        "work_unit_fingerprint": "sha256:hosted-consumption-sample",
        "source_ref": "projection/current_owner_delta.json",
    }
    return {
        "surface_kind": "mas_hosted_ordinary_path_consumption_contract",
        "schema_version": SCHEMA_VERSION,
        "contract_ref": CONTRACT_REF,
        "owner": "MedAutoScience",
        "hosted_runtime_owner": "one-person-lab",
        "purpose": (
            "Prove that the OPL hosted ordinary path can consume MAS AgentExecutionIndex, "
            "OperationalToolCard, CapabilityInvocationPlan, ToolResultEnvelope recovery, "
            "Scientific Capability Registry resolution, and owner-consumption evidence "
            "without introducing a MAS private runtime or blocking advisory gate."
        ),
        "planning_root": "current_owner_delta",
        "source_refs": {
            "agent_tool_arsenal": "contracts/agent_tool_arsenal.json",
            "scientific_capability_registry": (
                "src/med_autoscience/scientific_capability_registry.py"
            ),
            "builder": (
                "src/med_autoscience/hosted_ordinary_path_consumption.py::"
                "build_hosted_ordinary_path_consumption_evidence"
            ),
        },
        "required_consumed_surfaces": [
            "agent_execution_index",
            "operational_tool_card",
            "capability_invocation_plan",
            "tool_result_envelope_recovery",
            "scientific_capability_resolution",
            "owner_consumption_evidence_packet",
        ],
        "friction_policy": {
            "human_operator_manual_tool_selection_required": False,
            "raw_contract_direct_read_required": False,
            "new_default_preflight": False,
            "sidecar_blocks_owner_action": False,
            "missing_capability_blocks_owner_action": False,
            "missing_owner_response_refs_blocks": False,
            "docker_or_dind_required": False,
        },
        "authority_boundary": {
            "opl_can_write_domain_truth": False,
            "opl_can_authorize_publication_quality": False,
            "opl_can_write_owner_receipt": False,
            "opl_can_write_typed_blocker": False,
            "evidence_packet_can_claim_paper_progress": False,
        },
        "sample_evidence": build_hosted_ordinary_path_consumption_evidence(
            current_owner_delta=sample_delta
        ),
    }


def _plan_digest(plan: Mapping[str, Any]) -> dict[str, Any]:
    requires = _mapping(plan.get("requires"))
    selection = _mapping(plan.get("selection_policy"))
    return {
        "surface_kind": _text(plan.get("surface_kind")),
        "planning_root": _text(plan.get("planning_root")),
        "selected_card_kind": _text(plan.get("selected_card_kind")),
        "selected_tool_id": _text(plan.get("selected_tool_id")),
        "selected_action_id": _text(plan.get("selected_action_id")),
        "selected_action_type": _text(plan.get("selected_action_type")),
        "requires_owner_receipt_or_typed_blocker": bool(
            requires.get("owner_receipt_or_typed_blocker")
        ),
        "executor_receipt_ref_required": bool(
            requires.get("executor_receipt_ref_required")
        ),
        "primary_selection": _text(selection.get("primary_selection")),
        "support_or_diagnostic_tools_auto_selected": bool(
            selection.get("support_or_diagnostic_tools_auto_selected")
        ),
        "missing_capability_default": _text(selection.get("missing_capability_default")),
        "invocation_steps": _text_list(plan.get("invocation_steps")),
    }


def _capability_digest(capability: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "capability_id": _text(capability.get("capability_id")),
        "capability_family": _text(capability.get("capability_family")),
        "invocation_kind": _text(capability.get("invocation_kind")),
        "candidate_ref": _text(capability.get("candidate_ref")),
        "refs_only": bool(capability.get("refs_only")),
        "can_block_current_owner_action": bool(
            capability.get("can_block_current_owner_action")
        ),
        "requires_explicit_invoke": bool(capability.get("requires_explicit_invoke")),
    }


def _owner_consumption_digest(evidence: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": _text(evidence.get("surface_kind")),
        "status": _text(evidence.get("status")),
        "capability_id": _text(evidence.get("capability_id")),
        "capability_family": _text(evidence.get("capability_family")),
        "output_refs": _text_list(evidence.get("output_refs")),
        "owner_consumption_status": _text(evidence.get("owner_consumption_status")),
        "owner_receipt_ref": _optional_text(evidence.get("owner_receipt_ref")),
        "typed_blocker_ref": _optional_text(evidence.get("typed_blocker_ref")),
        "reviewer_receipt_ref": _optional_text(evidence.get("reviewer_receipt_ref")),
        "route_back_evidence_ref": _optional_text(evidence.get("route_back_evidence_ref")),
        "counts_as_progress": bool(evidence.get("counts_as_progress")),
        "can_authorize_owner_action": bool(evidence.get("can_authorize_owner_action")),
        "mainline_waits_for_owner_consumption": bool(
            evidence.get("mainline_waits_for_owner_consumption")
        ),
        "missing_owner_response_refs_blocks": bool(
            evidence.get("missing_owner_response_refs_blocks")
        ),
        "fail_open": bool(evidence.get("fail_open")),
    }


def _primary_card_ref(plan: Mapping[str, Any]) -> str:
    selected = (
        _text(plan.get("selected_action_id"))
        or _text(plan.get("selected_action_type"))
        or _text(plan.get("selected_tool_id"))
    )
    return f"contracts/agent_tool_arsenal.json#/tool_cards/{selected}"


def _current_owner_summary(delta: Mapping[str, Any]) -> dict[str, str]:
    return {
        "action_type": _text(delta.get("action_type")),
        "action_id": _text(delta.get("action_id")),
        "owner": _text(delta.get("owner")),
        "work_unit_id": _text(delta.get("work_unit_id")),
        "work_unit_fingerprint": _text(delta.get("work_unit_fingerprint")),
        "source_ref": _text(delta.get("source_ref")),
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return [text for item in value if (text := _text(item))]


def _optional_text(value: object) -> str | None:
    text = _text(value)
    return text or None


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "CONTRACT_REF",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_hosted_ordinary_path_consumption_contract",
    "build_hosted_ordinary_path_consumption_evidence",
]
