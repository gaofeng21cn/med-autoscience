from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from med_autoscience.action_catalog import build_mas_action_catalog
from med_autoscience.opl_standard_pack import build_standard_pack
from med_autoscience.runtime_protocol.runtime_lifecycle_store_parts.agent_pack_refs import (
    AGENT_PROMPT_REFS,
)
from med_autoscience.runtime_protocol.runtime_lifecycle_store_parts.family_adoption import (
    build_family_stage_control_plane,
)


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


def _assert_pack_path_is_real(path: str) -> None:
    resolved = REPO_ROOT / path
    assert resolved.exists(), path
    assert resolved.is_file(), path
    text = resolved.read_text(encoding="utf-8").strip()
    assert text, path
    forbidden = {"TODO", "TBD"}
    assert not any(token in text for token in forbidden), path


def test_opl_standard_pack_root_contracts_match_mas_canonical_metadata() -> None:
    generated = build_standard_pack()
    action_catalog = build_mas_action_catalog()
    stage_plane = build_family_stage_control_plane(family_action_catalog=action_catalog)

    assert _read_contract("domain_descriptor") == generated["domain_descriptor"]
    assert _read_contract("action_catalog") == generated["action_catalog"]
    assert _read_contract("stage_control_plane") == generated["stage_control_plane"]
    assert _read_contract("functional_privatization_audit") == generated["functional_privatization_audit"]

    assert generated["action_catalog"]["actions"] == action_catalog["actions"]
    assert generated["stage_control_plane"]["stages"] == stage_plane["stages"]
    assert generated["pack_compiler_input"]["generated_surface_owner"] == "one-person-lab"
    assert generated["pack_compiler_input"]["canonical_semantic_pack_root"] == "agent/"
    assert generated["pack_compiler_input"]["canonical_semantic_pack_role"] == (
        "declarative_medical_research_semantics_for_opl_pack_compiler"
    )
    assert generated["pack_compiler_input"]["src_role"] == (
        "domain_handler_minimal_authority_functions_and_native_helpers_only"
    )
    assert generated["pack_compiler_input"]["src_must_not_be_canonical_semantic_pack"] is True
    required_paths = generated["pack_compiler_input"]["required_domain_pack_paths"]
    assert "agent/stages/stage_route_contract.yaml" in required_paths
    assert set(AGENT_PROMPT_REFS.values()) <= set(required_paths)
    assert all(str(path).startswith("agent/") for path in required_paths)
    for path in required_paths:
        _assert_pack_path_is_real(str(path))
    assert generated["pack_compiler_input"]["minimal_authority_semantic_model"] == (
        "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
    )
    assert generated["pack_compiler_input"]["allowed_judgment_modes"] == [
        "ai_first_stage_gate",
        "ai_first_record_validator",
        "mechanical_guard",
        "refs_only_adapter",
    ]
    assert generated["pack_compiler_input"]["verdict_function_model_retired"] is True
    assert generated["pack_compiler_input"]["gate_validator_ref"] == (
        "src/med_autoscience/controllers/ai_first_private_authority.py::"
        "validate_ai_first_private_authority_gate"
    )
    assert generated["pack_compiler_input"]["runtime_enforcement_status"] == (
        "contract_validator_landed"
    )
    assert generated["pack_compiler_input"]["program_output_policy"] == (
        "programs_validate_ai_first_stage_gate_records_and_emit_receipts_or_typed_blockers_only"
    )
    assert generated["pack_compiler_input"]["ai_first_stage_gate_function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
    ]
    assert generated["pack_compiler_input"]["ai_first_record_validator_function_ids"] == [
        "artifact_mutation_authorization"
    ]
    assert generated["pack_compiler_input"]["mechanical_guard_function_ids"] == [
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    assert generated["pack_compiler_input"]["minimal_authority_functions"][:5] == [
        "publication_quality_stage_gate_boundary",
        "ai_reviewer_quality_stage_gate_boundary",
        "artifact_mutation_stage_gate_boundary",
        "publication_route_memory_accept_reject_stage_gate_boundary",
        "source_readiness_stage_gate_boundary",
    ]
    assert generated["pack_compiler_input"]["backward_readable_minimal_authority_ids"] == [
        "publication_quality_verdict_authorizer",
        "ai_reviewer_quality_decision_authorizer",
        "artifact_mutation_authorizer",
        "publication_route_memory_accept_reject_decider",
        "source_readiness_verdict_authorizer",
    ]
    assert generated["pack_compiler_input"]["requires_ai_first_record"] is True
    independent_policy = generated["pack_compiler_input"][
        "independent_executor_reviewer_agent_policy"
    ]
    assert independent_policy["required"] is True
    assert independent_policy["separate_invocation_required"] is True
    assert independent_policy["separate_context_record_required"] is True
    assert independent_policy["separate_task_record_required"] is True
    assert independent_policy["separate_receipt_required"] is True
    assert independent_policy["self_review_closes_quality_gate"] is False
    assert {
        item["program_role"]
        for item in generated["pack_compiler_input"]["stage_quality_gate_boundaries"]
    } == {"validator", "materializer", "guard"}
    assert {
        item["judgment_mode"]
        for item in generated["pack_compiler_input"]["stage_quality_gate_boundaries"]
    } == {"ai_first_stage_gate", "ai_first_record_validator"}
    assert all(
        item["program_may_emit_pass_ready_verdict"] is False
        for item in generated["pack_compiler_input"]["stage_quality_gate_boundaries"]
    )
    policy = generated["private_functional_surface_policy"]
    assert policy["allowed_private_surface_classes"] == [
        "ai_first_stage_quality_gate_boundary",
        "domain_native_helper_implementation",
        "owner_receipt_signer",
    ]
    assert "domain_truth_verdict_authorizer" not in policy["allowed_private_surface_classes"]
    assert not any(
        item.endswith("_authorizer") for item in policy["allowed_private_surface_classes"]
    )
    assert policy["forbidden_primary_allowed_private_surface_models"] == [
        "domain_truth_verdict_authorizer",
        "*_authorizer",
    ]
    assert policy["allowed_judgment_modes"] == generated["pack_compiler_input"][
        "allowed_judgment_modes"
    ]
    assert policy["verdict_function_model_retired"] is True
    assert policy["gate_validator_ref"] == generated["pack_compiler_input"]["gate_validator_ref"]
    assert policy["runtime_enforcement_status"] == generated["pack_compiler_input"][
        "runtime_enforcement_status"
    ]
    assert policy["program_output_policy"] == generated["pack_compiler_input"][
        "program_output_policy"
    ]
    assert policy["requires_ai_first_record"] is True
    assert policy["independent_executor_reviewer_agent_policy"] == independent_policy
    assert generated["generated_surface_handoff"]["domain_repo_can_own_generated_surface"] is False
    assert generated["generated_surface_handoff"]["consumes_agent_pack_refs"] is True
    assert generated["generated_surface_handoff"]["agent_pack_ref_source"] == (
        "contracts/pack_compiler_input.json#/required_domain_pack_paths"
    )
    handoff_policy = generated["generated_surface_handoff"]["generated_surface_policy"]
    assert handoff_policy["must_read_semantics_from"] == "agent/"
    assert "MAS study truth" in handoff_policy["must_not_write"]
    assert "publication verdict" in handoff_policy["must_not_write"]
    assert "current_package" in handoff_policy["must_not_write"]
    oma_handoff = generated["generated_surface_handoff"]["oma_agent_evidence_handoff"]
    assert oma_handoff["consumer_id"] == "opl-meta-agent.agent:evidence"
    assert oma_handoff["production_acceptance_ref"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json",
        "role": "mas_domain_owned_production_acceptance",
        "body_included": False,
    }
    assert oma_handoff["agent_lab_handoff_ref"]["ref"] == "contracts/agent_lab_handoff.json"
    assert oma_handoff["owner_receipt_authority_ref"]["ref"] == "contracts/owner_receipt_contract.json"
    assert oma_handoff["quality_authority_ref"]["role"] == "mas_quality_publication_authority"
    assert oma_handoff["artifact_authority_ref"]["ref"] == "contracts/artifact_locator_contract.json"
    assert oma_handoff["memory_authority_ref"]["ref"] == "contracts/memory_descriptor.json"
    assert {
        hint["ref"]
        for hint in oma_handoff["editable_surface_hints"]
    } >= {
        "agent/prompts",
        "agent/skills",
        "agent/knowledge",
        "agent/quality_gates",
        "contracts/generated_surface_handoff.json",
        "contracts/agent_lab_handoff.json",
    }
    assert all(hint["body_included"] is False for hint in oma_handoff["editable_surface_hints"])
    assert oma_handoff["consumer_policy"] == {
        "oma_may_consume_refs": True,
        "oma_may_emit_candidate_patch_work_order": True,
        "oma_may_sign_owner_receipt": False,
        "oma_may_write_quality_verdict": False,
        "oma_may_write_artifact_body": False,
        "oma_may_write_memory_body": False,
    }
    assert "skill" in generated["pack_compiler_input"]["generated_surfaces_requested"]
    assert generated["action_catalog"]["catalog_role"] == (
        "domain_action_intent_and_handler_target_input_for_opl_generated_descriptors"
    )


def test_opl_standard_pack_runtime_guard_stages_declare_runtime_event_refs() -> None:
    generated = build_standard_pack()

    for stage in generated["stage_control_plane"]["stages"]:
        launch_packet = stage["codex_cli_launch_packet"]
        assert launch_packet["surface_kind"] == "mas_codex_cli_stage_launch_packet"
        assert launch_packet["stage_id"] == stage["stage_id"]
        assert launch_packet["executor_requirements"] == "Codex CLI default"
        assert launch_packet["prompt_ref"] == stage["prompt_refs"][0]
        assert set(launch_packet["tool_refs"]["allowed_action_refs"]) == set(stage["allowed_action_refs"])
        assert launch_packet["skill_refs"] == stage["skills"]
        assert launch_packet["knowledge_refs"] == stage["knowledge_refs"]
        assert launch_packet["quality_gate_refs"] == stage["evaluation"]
        assert launch_packet["quality_pack_refs"] == stage["quality_pack_refs"]
        assert launch_packet["expected_receipt_refs"]["owner_receipt_contract_ref"] == (
            "/product_entry_manifest/owner_receipt_contract"
        )
        assert launch_packet["expected_receipt_refs"]["stage_status_ref"] == "/progress_projection"
        assert launch_packet["expected_receipt_refs"]["runtime_event_refs"] == (
            stage["stage_contract"]["runtime_event_refs"]
        )
        assert set(launch_packet["expected_receipt_refs"]["valid_outcomes"]) == {
            "owner_receipt",
            "typed_blocker",
            "route_back_request",
            "human_gate_request",
            "no_op_with_currentness_proof",
        }
        assert launch_packet["ai_first_boundary"]["contract_role"] == "boundary_and_evidence_refs_only"
        assert launch_packet["ai_first_boundary"]["script_verdict_authority"] is False
        assert launch_packet["ai_first_boundary"]["self_review_closes_quality_gate"] is False
        assert "quality_verdict" in launch_packet["forbidden_authority"]
        assert "publication_readiness" in launch_packet["forbidden_authority"]
        assert "script_exit_code_as_publication_quality_verdict" in launch_packet[
            "forbidden_authority"
        ]
        prompt_refs = stage["prompt_refs"]
        assert len(prompt_refs) == 1
        prompt_ref = prompt_refs[0]
        assert prompt_ref["role"] == "stage_prompt"
        assert prompt_ref["ref_kind"] == "repo_path"
        assert prompt_ref["ref"] == AGENT_PROMPT_REFS[stage["stage_id"]]
        assert str(prompt_ref["ref"]).startswith("agent/prompts/")
        _assert_pack_path_is_real(str(prompt_ref["ref"]))
        assert any(ref["role"] == "stage_domain_policy" for ref in stage["policy_refs"])
        assert all(
            str(ref["ref"]).startswith("agent/") or ref["role"] in {"route_contract", "stage_led_policy"}
            for ref in stage["policy_refs"]
        )
        assert any(ref["role"] == "domain_pack_skill_policy" for ref in stage["skills"])
        assert any(ref["role"] == "domain_pack_knowledge" for ref in stage["knowledge_refs"])
        assert any(ref["role"] == "agent_quality_gate" for ref in stage["evaluation"])
        if not stage["trust_boundary"]["runtime_guard_required"]:
            continue
        refs = stage["trust_boundary"].get("runtime_event_refs")
        assert refs
        assert refs == stage["stage_contract"].get("runtime_event_refs")
        assert all(str(ref).startswith("runtime_event:") for ref in refs)
        assert stage["stage_contract"]["source_scope_refs"]
        assert stage["stage_contract"]["cohort_query_refs"]
        assert stage["stage_contract"]["trigger_refs"]
        assert stage["stage_contract"]["monitor_refs"]
        assert stage["stage_contract"]["dashboard_metric_refs"]
        assert any(ref["role"] == "opl_provider_stage_launch_trigger" for ref in stage["stage_contract"]["trigger_refs"])
    assert generated["action_catalog"]["descriptor_projection_owner"] == "one-person-lab"
    assert generated["action_catalog"]["domain_handler_target_owner"] == "MedAutoScience"
    assert generated["functional_privatization_audit"]["functional_followthrough_gap_summary"][
        "classification_gap_count"
    ] == 0
    followthrough = generated["functional_privatization_audit"]["functional_followthrough_gap_summary"]
    assert followthrough["functional_structure_gap_count"] == 0
    assert followthrough["remaining_gap_classification"] == "live_provider_paper_line_evidence_gates"
    assert followthrough["remaining_items_are_evidence_gates"] is True
    assert followthrough["remaining_functional_followthrough_gate_ids"] == []
    assert followthrough["remaining_functional_followthrough_gates"] == []
    assert followthrough["closed_functional_structure_gate_ids"] == [
        "generated_surface_active_caller_cutover",
        "refs_only_adapter_thinning",
        "legacy_cleanup_physical_retirement",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
    ]
    assert followthrough["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]
    audit = generated["functional_privatization_audit"]
    functional_boundary = audit["functional_consumer_boundary"]
    runtime_role = functional_boundary["runtime_lifecycle_sqlite_role"]
    assert runtime_role["classification"] == "refs_only_adapter"
    assert runtime_role["authority"] == "refs_only_index_not_generic_persistence_engine"
    assert runtime_role["body_policy"] == "refs_receipts_blockers_only"
    assert runtime_role["generic_owner_claim_allowed"] is False
    assert runtime_role["mas_may_claim_generic_persistence_engine"] is False
    assert runtime_role["mas_may_write_domain_truth"] is False

    inventory = {
        item["module_id"]: item
        for item in functional_boundary["functional_module_inventory"]
    }
    private_runtime_refs_only_modules = {
        "runtime_lifecycle_sqlite_reference_adapter": {
            "boundary": "refs_only_sqlite_lifecycle_index_not_generic_runtime_owner",
            "must_not_emit": "generic_runtime_verdict",
        },
        "runtime_storage_maintenance": {
            "boundary": "refs_only_adapter_no_generic_cleanup_policy_owner",
            "must_not_emit": "generic_cleanup_policy",
        },
        "terminal_attach_transport": {
            "boundary": "refs_only_terminal_projection_no_generic_attach_runtime_owner",
            "must_not_emit": "generic_terminal_runtime_owner",
        },
    }
    for module_id, expected in private_runtime_refs_only_modules.items():
        item = inventory[module_id]
        assert item["classification"] == "refs_only_adapter"
        assert item["authority_boundary"] == expected["boundary"]
        provenance_boundary = item["provenance_boundary"]
        assert provenance_boundary["generic_owner_claim_allowed"] is False
        assert provenance_boundary["body_policy"].endswith("_only")
        assert expected["must_not_emit"] in provenance_boundary["must_not_emit"]
        assert "paper_closure_verdict" in provenance_boundary["must_not_emit"]


def test_opl_generated_interfaces_compile_mas_standard_pack() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [str(opl_bin), "agents", "interfaces", "--repo-dir", str(REPO_ROOT), "--json"],
        cwd=opl_root,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    bundle = payload["generated_agent_interfaces"]

    assert bundle["source_kind"] == "standard_agent_repo_contracts"
    assert bundle["status"] == "ready"
    assert bundle["owner"] == "one-person-lab"
    assert bundle["domain_repo_can_own_generated_surface"] is False
    assert bundle["blocker_reasons"] == []
    assert bundle["cli"]["status"] == "ready"
    assert bundle["mcp"]["status"] == "ready"
    assert bundle["skill"]["status"] == "ready"
    assert bundle["product_entry"]["status"] == "ready"
    assert bundle["openai_tool"]["status"] == "ready"
    assert bundle["ai_sdk"]["status"] == "ready"
    generated = build_standard_pack()
    assert {item["stage_id"] for item in bundle["stage_routes"]} == {
        stage["stage_id"] for stage in generated["stage_control_plane"]["stages"]
    }


def test_opl_standard_scaffold_validates_mas_pack() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [str(opl_bin), "agents", "scaffold", "--validate", str(REPO_ROOT), "--json"],
        cwd=opl_root,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    validation = payload["standard_domain_agent_scaffold"]["validation"]

    assert validation["status"] == "passed"
    assert validation["blockers"] == []
    assert validation["missing_contract_files"] == []
    assert validation["missing_forbidden_role_guards"] == []
