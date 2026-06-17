from __future__ import annotations

import importlib

from med_autoscience.action_catalog import build_mas_action_catalog


RECOVERY_FIELDS = {
    "retryability",
    "staleness",
    "missing_refs",
    "next_safe_actions",
    "owner_needed",
    "receipt_refs",
    "typed_blocker_refs",
    "diagnostic_refs",
    "no_forbidden_authority_claim",
}


def test_agent_tool_arsenal_builds_agent_facing_cards_from_action_catalog() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    arsenal = module.build_agent_tool_arsenal_index()
    catalog_action_ids = {item["action_id"] for item in build_mas_action_catalog()["actions"]}
    cards = {item["action_id"]: item for item in arsenal["tool_cards"]}

    assert arsenal["surface_kind"] == "mas_agent_tool_arsenal_index"
    assert arsenal["contract_id"] == "mas_agent_tool_arsenal.v1"
    assert arsenal["audience"] == "autonomous_agent_executor"
    assert arsenal["human_operator_role"] == "governance_and_authorization_not_manual_tool_composition"
    assert arsenal["ordinary_planning_root"] == "current_owner_delta"
    assert arsenal["authority_boundary"]["selection_runtime_owner"] == "one-person-lab"
    assert arsenal["authority_boundary"]["capability_runtime_owner"] == "one-person-lab"
    assert arsenal["authority_boundary"]["capability_runtime_kind"] == "OPL Capability Runtime"
    assert arsenal["authority_boundary"]["opl_owns_capability_selection_runtime"] is True
    assert arsenal["authority_boundary"]["opl_owns_capability_invocation_runtime"] is True
    assert arsenal["authority_boundary"]["mas_selector_authority"] is False
    assert arsenal["authority_boundary"]["mas_tool_invocation_runtime_authority"] is False
    assert arsenal["authority_boundary"]["missing_refs_trigger_mutating_invocation"] is False
    assert arsenal["authority_boundary"]["capability_plan_can_write_domain_truth"] is False
    assert arsenal["authority_boundary"]["capability_plan_can_authorize_publication_quality"] is False
    assert arsenal["agent_execution_index"]["authority_boundary"]["selection_runtime_owner"] == "one-person-lab"
    assert arsenal["agent_execution_index"]["authority_boundary"]["mas_selector_authority"] is False
    assert set(cards) == catalog_action_ids
    assert {item["action_id"] for item in arsenal["tool_index_entries"]} == catalog_action_ids

    progress = cards["study_progress"]
    assert progress["surface_kind"] == "mas_tool_use_card"
    assert progress["tool_id"] == "study_progress"
    assert progress["callability"] == "mcp_runtime"
    assert progress["risk_annotations"]["readOnlyHint"] is True
    assert progress["risk_annotations"]["requires_human_gate"] is False
    assert progress["risk_annotations"]["requires_opl_stage_attempt_or_lease"] is False
    assert progress["authority_effects"]["can_return_owner_receipt"] is False
    assert progress["allowed_writes"] == []
    assert progress["result_envelope_schema_ref"] == (
        "contracts/agent_tool_arsenal.json#/result_envelope_schema"
    )
    assert progress["lightweight_executor_receipt_contract_ref"] == (
        "src/med_autoscience/lightweight_executor_receipts.py::build_lightweight_executor_receipt_contract"
    )
    assert progress["executor_receipt_ref_policy"] == {
        "field": "executor_receipt_ref",
        "required": False,
        "receipt_only": True,
        "can_block_current_owner_action": False,
    }
    assert "current_owner_delta" in progress["when_to_use"]
    assert progress["default_invocation"] == {
        "surface": "mcp",
        "tool_name": "study_progress",
        "arguments": {},
    }
    assert progress["required_refs"] == ["profile_ref", "study_id"]
    assert progress["discovery_hint"]["planning_root"] == "current_owner_delta"
    assert "study_progress" in progress["discovery_hint"]["aliases"]
    assert progress["fit_signal"]["required_refs_are_selection_blockers"] is False
    assert progress["invocation_gate"]["fail_closed"] is True
    assert progress["invocation_gate"]["required_refs"] == ["profile_ref", "study_id"]
    assert progress["adaptation_policy"]["policy"] == "exact_contract_match"
    assert progress["authority_boundary"]["selection_runtime_owner"] == "one-person-lab"
    assert progress["authority_boundary"]["capability_runtime_owner"] == "one-person-lab"
    assert progress["authority_boundary"]["mas_selector_authority"] is False
    assert progress["authority_boundary"]["mas_tool_invocation_runtime_authority"] is False
    assert progress["authority_boundary"]["missing_refs_trigger_mutating_invocation"] is False
    assert progress["optional_refs"] == []
    assert progress["preflight_checks"] == [
        "confirm_current_owner_delta_matches_card_applicability",
        "verify_required_refs_available",
        "check_allowed_writes_and_forbidden_authority",
    ]
    assert "structured_payload_matches_output_schema" in progress["success_signals"]
    assert progress["failure_classes"]["missing_refs"]["retryability"] == "retry_after_refs"
    assert progress["next_safe_actions"][0]["action"] == "invoke_tool"
    assert progress["operational"]["default_invocation"] == progress["default_invocation"]
    assert progress["operational"]["required_refs"] == progress["required_refs"]

    capability_registry = arsenal["scientific_capability_registry"]
    assert capability_registry["surface_kind"] == "mas_scientific_capability_registry"
    assert capability_registry["default_policy"]["fail_open"] is True
    assert capability_registry["default_policy"]["mainline_waits_for_capability"] is False
    assert any(
        item["capability_id"] == "display_pack_visual_capability"
        for item in capability_registry["capabilities"]
    )
    capability_card = cards["scientific_capability_registry"]
    assert capability_card["tool_id"] == "scientific_capability_registry"
    assert capability_card["callability"] == "mcp_runtime"
    assert capability_card["risk_annotations"]["readOnlyHint"] is False
    assert capability_card["risk_annotations"]["destructiveHint"] is False
    assert capability_card["risk_annotations"]["requires_opl_stage_attempt_or_lease"] is False
    assert capability_card["authority_effects"]["can_return_owner_receipt"] is False
    assert "artifacts/advisory/external_learning_sidecar/latest.json" in capability_card["allowed_writes"]
    assert "artifacts/runtime/evo_scientist_sidecar/latest.json" in capability_card["allowed_writes"]

    display_orchestrate = cards["display_pack_orchestrate"]
    assert display_orchestrate["tool_id"] == "display_pack_agent"
    assert display_orchestrate["tool_mode"] == "orchestrate"
    assert display_orchestrate["callability"] == "mcp_runtime"
    assert display_orchestrate["mcp_invocation"] == {
        "tool_name": "display_pack_agent",
        "mode": "orchestrate",
        "public_runtime": True,
    }
    assert "display_pack" in display_orchestrate["discovery_hint"]["capability_tags"]
    assert display_orchestrate["fit_signal"]["required_refs_are_selection_blockers"] is False
    assert display_orchestrate["adaptation_policy"]["policy"] == (
        "adaptable_baseline_not_exact_contract"
    )
    assert display_orchestrate["invocation_gate"]["fail_closed"] is True
    assert display_orchestrate["risk_annotations"]["readOnlyHint"] is True
    assert display_orchestrate["allowed_writes"] == []

    display_preflight = cards["display_pack_preflight"]
    assert display_preflight["tool_id"] == "display_pack_agent"
    assert display_preflight["tool_mode"] == "preflight"
    assert display_preflight["callability"] == "mcp_runtime"
    assert display_preflight["mcp_invocation"] == {
        "tool_name": "display_pack_agent",
        "mode": "preflight",
        "public_runtime": True,
    }
    assert display_preflight["risk_annotations"]["readOnlyHint"] is True

    dispatch = cards["domain_handler_dispatch"]
    assert dispatch["effect"] == "mutating"
    assert dispatch["callability"] == "descriptor_only"
    assert dispatch["risk_annotations"]["readOnlyHint"] is False
    assert dispatch["risk_annotations"]["requires_opl_stage_attempt_or_lease"] is True
    assert dispatch["non_read_only_gate"] == {
        "surface_kind": "mas_agent_tool_non_read_only_gate",
        "gate_policy": "current_owner_delta_or_human_gate_with_owner_receipt_typed_blocker_proof",
        "requires_current_owner_delta": True,
        "requires_current_owner_delta_match": True,
        "requires_human_gate": False,
        "requires_human_gate_or_owner_delta": True,
        "requires_owner_receipt_or_typed_blocker_proof": True,
        "owner_receipt_or_typed_blocker_proof_replaces_publication_quality": False,
        "can_substitute_owner_receipt": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_provider_admission": False,
        "can_start_worker_attempt": False,
    }
    assert dispatch["invocation_gate"]["non_read_only_gate_policy"] == dispatch["non_read_only_gate"]["gate_policy"]
    assert dispatch["invocation_gate"]["owner_receipt_or_typed_blocker_required"] is True
    assert dispatch["authority_effects"]["can_return_owner_receipt"] is True
    assert "publication_quality" in dispatch["forbidden_authority"]
    assert "current_package" in dispatch["forbidden_authority"]


def test_agent_tool_arsenal_resolver_keeps_candidates_when_refs_are_missing() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    resolution = module.resolve_capability_candidates(
        current_owner_delta={
            "action_type": "display_pack_orchestrate",
            "display_intent": "Create a ROC curve for model performance.",
        },
        task_intent="need display pack visual baseline for ROC figure",
        available_refs=["current_owner_delta"],
    )

    assert resolution["surface_kind"] == "mas_capability_resolution"
    assert resolution["planning_root"] == "current_owner_delta"
    assert resolution["discovery_fail_closed"] is False
    assert resolution["hard_gate_fail_closed"] is True
    assert resolution["selection_policy"]["discovery"] == "soft_match_high_recall"
    assert resolution["selection_policy"]["invocation"] == "hard_contract_fail_closed"
    assert resolution["authority_boundary"]["selection_runtime_owner"] == "one-person-lab"
    assert resolution["authority_boundary"]["capability_runtime_owner"] == "one-person-lab"
    assert resolution["authority_boundary"]["mas_selector_authority"] is False
    assert resolution["authority_boundary"]["missing_refs_trigger_mutating_invocation"] is False

    candidates = {item["action_id"]: item for item in resolution["candidate_tools"]}
    display = candidates["display_pack_orchestrate"]
    assert display["tool_id"] == "display_pack_agent"
    assert display["tool_mode"] == "orchestrate"
    assert display["fit_policy"] == "adaptable_baseline_not_exact_contract"
    assert display["fit_score"] > 0
    assert "paper_root" in display["missing_refs"]
    assert "repo_root" in display["missing_refs"]
    assert display["hard_gate_status"] == "blocked_until_refs"
    assert display["candidate_retained_despite_missing_refs"] is True
    assert display["next_safe_actions"][0]["action"] == "collect_missing_refs"
    assert display["invocation_gate"]["fail_closed"] is True
    assert display["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert display["authority_boundary"]["selection_runtime_owner"] == "one-person-lab"
    assert display["authority_boundary"]["capability_runtime_owner"] == "one-person-lab"
    assert display["authority_boundary"]["mas_selector_authority"] is False
    assert display["authority_boundary"]["missing_refs_trigger_mutating_invocation"] is False


def test_agent_tool_arsenal_resolver_scores_exact_owner_callable_but_keeps_hard_gate() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    resolution = module.resolve_capability_candidates(
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "source_ref": "artifacts/controller_decisions/latest.json",
        },
        available_refs=[
            "current_owner_delta",
            "opl_stage_attempt_or_lease",
            "controller_decisions/latest.json",
            "publication_eval/latest.json",
            "paper_root",
        ],
    )

    repair = next(
        item
        for item in resolution["candidate_tools"]
        if item["tool_id"] == "owner_callable:run_quality_repair_batch"
    )
    assert repair["fit_policy"] == "exact_contract_match"
    assert repair["hard_gate_status"] == "ready"
    assert repair["missing_refs"] == []
    assert repair["requires"]["owner_receipt_or_typed_blocker"] is True
    assert repair["invocation_gate"]["fail_closed"] is True
    assert repair["authority_boundary"]["owner_receipt_or_typed_blocker_required"] is True


def test_agent_tool_arsenal_indexes_owner_callable_cards_with_lifecycle_contract() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    arsenal = module.build_agent_tool_arsenal_index()
    owner_cards = {item["action_type"]: item for item in arsenal["owner_callable_cards"]}
    repair = owner_cards["run_quality_repair_batch"]

    assert repair["surface_kind"] == "mas_owner_callable_tool_card"
    assert repair["card_kind"] == "owner_callable"
    assert repair["owner"] == "quality_repair_batch"
    assert repair["callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert "controller_decisions/latest.json" in repair["input_refs"]
    assert "paper/draft.md" in repair["allowed_writes"]
    assert "artifacts/publication_eval/latest.json" in repair["forbidden_writes"]
    assert repair["closeout_contract"]["requires_owner_receipt_or_typed_blocker"] is True
    assert repair["non_read_only_gate"]["requires_current_owner_delta"] is True
    assert repair["non_read_only_gate"]["requires_owner_receipt_or_typed_blocker_proof"] is True
    assert repair["non_read_only_gate"]["can_substitute_owner_receipt"] is False
    assert repair["authority_boundary"]["owner_receipt_or_typed_blocker_required"] is True
    assert repair["authority_boundary"]["owner_receipt_or_typed_blocker_proof_replaces_publication_quality"] is False
    assert repair["authority_boundary"]["can_substitute_owner_receipt"] is False
    assert repair["result_envelope_schema_ref"] == (
        "contracts/agent_tool_arsenal.json#/result_envelope_schema"
    )

    schema = arsenal["result_envelope_schema"]
    assert schema["title"] == "MAS ToolResultEnvelope"
    assert {"surface_kind", "tool_id", "status", "audit_trail", "authority_boundary"} <= set(
        schema["required"]
    )
    assert schema["properties"]["status"]["enum"] == [
        "succeeded",
        "blocked",
        "no_op_current",
        "failed",
    ]
    assert schema["properties"]["executor_receipt_ref"]["type"] == "string"
    assert schema["properties"]["lightweight_executor_receipt_contract_ref"]["const"] == (
        "src/med_autoscience/lightweight_executor_receipts.py::build_lightweight_executor_receipt_contract"
    )
    assert schema["properties"]["retryability"]["enum"] == [
        "retry_safe",
        "retry_after_refs",
        "no_retry",
        "owner_needed",
    ]
    assert schema["properties"]["staleness"]["type"] == "object"
    assert schema["properties"]["missing_refs"]["type"] == "array"
    assert schema["properties"]["next_safe_actions"]["type"] == "array"
    assert schema["properties"]["owner_needed"]["type"] == "boolean"
    assert schema["properties"]["receipt_refs"]["type"] == "array"
    assert schema["properties"]["typed_blocker_refs"]["type"] == "array"
    assert schema["properties"]["diagnostic_refs"]["type"] == "array"
    assert schema["properties"]["no_forbidden_authority_claim"]["type"] == "boolean"
    assert "recovery" in schema["required"]
    recovery = schema["properties"]["recovery"]
    assert recovery["type"] == "object"
    assert RECOVERY_FIELDS <= set(recovery["required"])
    assert recovery["properties"]["no_forbidden_authority_claim"]["const"] is True


def test_agent_tool_arsenal_builds_capability_invocation_plan_from_current_owner_delta() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    plan = module.build_capability_invocation_plan(
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "source_ref": "artifacts/controller_decisions/latest.json",
            "work_unit_fingerprint": "sha256:test",
        }
    )

    assert plan["surface_kind"] == "mas_capability_invocation_plan"
    assert plan["planning_root"] == "current_owner_delta"
    assert plan["selected_card_kind"] == "owner_callable"
    assert plan["selected_action_type"] == "run_quality_repair_batch"
    assert plan["selected_tool_id"] == "owner_callable:run_quality_repair_batch"
    assert plan["requires"]["owner_receipt_or_typed_blocker"] is True
    assert plan["requires"]["current_owner_delta_match"] is True
    assert plan["requires"]["human_gate_or_owner_delta"] is True
    assert plan["requires"]["owner_receipt_or_typed_blocker_proof"] is True
    assert plan["authority_boundary"]["can_write_publication_quality"] is False
    assert plan["authority_boundary"]["owner_receipt_or_typed_blocker_proof_replaces_publication_quality"] is False
    assert plan["authority_boundary"]["capability_invocation_plan_replaces_owner_receipt"] is False
    assert plan["authority_boundary"]["selection_runtime_owner"] == "one-person-lab"
    assert plan["authority_boundary"]["capability_runtime_owner"] == "one-person-lab"
    assert plan["authority_boundary"]["capability_runtime_kind"] == "OPL Capability Runtime"
    assert plan["authority_boundary"]["mas_selector_authority"] is False
    assert plan["authority_boundary"]["mas_tool_invocation_runtime_authority"] is False
    assert plan["authority_boundary"]["missing_refs_trigger_mutating_invocation"] is False
    assert plan["authority_boundary"]["capability_plan_can_write_domain_truth"] is False
    assert plan["authority_boundary"]["capability_plan_can_authorize_publication_quality"] is False
    assert "verify_required_input_refs" in plan["invocation_steps"]
    assert "verify_current_owner_delta_or_human_gate" in plan["invocation_steps"]
    assert "emit_tool_result_envelope" in plan["invocation_steps"]
    assert "attach_optional_lightweight_executor_receipt_ref" in plan["invocation_steps"]
    assert plan["requires"]["executor_receipt_ref_required"] is False
    assert plan["requires"]["lightweight_executor_receipt_contract_ref"] == (
        "src/med_autoscience/lightweight_executor_receipts.py::build_lightweight_executor_receipt_contract"
    )
    assert plan["authority_boundary"]["executor_receipt_can_block_current_owner_action"] is False
    assert plan["selection_policy"]["primary_selection"] == "owner_callable"
    assert plan["primary_operational_card"]["tool_id"] == "owner_callable:run_quality_repair_batch"
    assert plan["fallback_cards"] == []
    assert plan["next_safe_actions"][0]["action"] == "invoke_owner_callable_surface"

    display_plan = module.build_capability_invocation_plan(
        current_owner_delta={
            "action_type": "display_pack_orchestrate",
            "source_ref": "paper/figure_intent.json",
            "work_unit_fingerprint": "sha256:display",
        }
    )

    assert display_plan["selected_card_kind"] == "action_catalog"
    assert display_plan["selected_action_id"] == "display_pack_orchestrate"
    assert display_plan["selected_tool_id"] == "display_pack_agent"
    assert display_plan["selected_tool_mode"] == "orchestrate"
    assert display_plan["requires"]["owner_receipt_or_typed_blocker"] is False
    assert display_plan["requires"]["current_owner_delta_match"] is True
    assert display_plan["requires"]["human_gate_or_owner_delta"] is False
    assert display_plan["requires"]["owner_receipt_or_typed_blocker_proof"] is False
    assert display_plan["requires"]["executor_receipt_ref_required"] is False
    assert display_plan["authority_boundary"]["selection_runtime_owner"] == "one-person-lab"
    assert display_plan["authority_boundary"]["mas_selector_authority"] is False
    assert display_plan["primary_operational_card"]["tool_id"] == "display_pack_agent"
    assert display_plan["primary_operational_card"]["default_invocation"]["arguments"] == {
        "mode": "orchestrate"
    }


def test_agent_tool_arsenal_completeness_diagnostic_maps_runtime_and_support_tools() -> None:
    module = importlib.import_module("med_autoscience.agent_tool_arsenal")

    diagnostic = module.build_agent_tool_arsenal_completeness_diagnostic(
        mcp_tool_names={
            "doctor_audit",
            "workspace_readiness",
            "research_assets",
            "study_progress",
            "open_auto_research_soak",
            "publication_status",
            "display_pack_agent",
            "scientific_capability_registry",
            "authority_operations",
            "agent_tool_arsenal",
        }
    )

    assert diagnostic["surface_kind"] == "mas_agent_tool_arsenal_completeness_diagnostic"
    assert diagnostic["status"] == "complete"
    assert diagnostic["issues"] == []
    assert diagnostic["required_tool_card_fields"] == [
        "mcp_invocation",
        "risk_annotations",
        "discovery_hint",
        "fit_signal",
        "invocation_gate",
        "adaptation_policy",
        "authority_boundary",
        "result_envelope_schema_ref",
        "forbidden_authority",
        "idempotency_policy",
        "current_delta_applicability",
        "default_invocation",
        "required_refs",
        "optional_refs",
        "preflight_checks",
        "success_signals",
        "failure_classes",
        "next_safe_actions",
    ]
    assert diagnostic["public_runtime_mcp_tools"] == [
        "authority_operations",
        "display_pack_agent",
        "scientific_capability_registry",
        "study_progress",
    ]
    assert diagnostic["lightweight_executor_receipt_contract_ref"] == (
        "src/med_autoscience/lightweight_executor_receipts.py::build_lightweight_executor_receipt_contract"
    )
    assert diagnostic["executor_receipt_ref_policy"]["receipt_only"] is True
    assert diagnostic["executor_receipt_ref_policy"]["can_block_current_owner_action"] is False
    assert "agent_tool_arsenal" in diagnostic["support_or_diagnostic_mcp_tools"]
    assert "doctor_audit" in diagnostic["support_or_diagnostic_mcp_tools"]
    assert diagnostic["authority_boundary"]["diagnostic_only"] is True
    assert diagnostic["authority_boundary"]["support_or_diagnostic_tools_are_projection_only"] is True
    assert diagnostic["authority_boundary"]["non_read_only_tools_require_current_owner_delta_or_human_gate"] is True
    assert diagnostic["authority_boundary"]["non_read_only_tools_require_owner_receipt_or_typed_blocker_proof"] is True
    assert diagnostic["doctor_surface_kind"] == "mas_agent_tool_arsenal_drift_parity_doctor"
    assert diagnostic["parity_summary"]["status"] == "complete"
    assert diagnostic["parity_summary"]["public_runtime_manifest_missing"] == []
    assert diagnostic["parity_summary"]["missing_public_runtime_mcp_tools"] == []
    assert diagnostic["parity_summary"]["doctor_audit_available"] is True
    assert diagnostic["parity_summary"]["agent_tool_arsenal_available"] is True
    assert diagnostic["parity_summary"]["support_or_diagnostic_tool_count"] >= 1
    drift_checks = {item["check_id"]: item for item in diagnostic["drift_checks"]}
    assert drift_checks["tool_card_operational_contract"]["status"] == "passed"
    assert drift_checks["result_envelope_recovery_contract"]["status"] == "passed"
    assert drift_checks["mcp_manifest_tool_card_parity"]["status"] == "passed"
    assert drift_checks["doctor_audit_support_surface_parity"]["status"] == "passed"
