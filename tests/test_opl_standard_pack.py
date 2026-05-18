from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from med_autoscience.action_catalog import build_mas_action_catalog
from med_autoscience.opl_standard_pack import build_standard_pack
from med_autoscience.runtime_protocol.runtime_lifecycle_store_parts.family_adoption import (
    build_family_stage_control_plane,
)


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


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
    assert "skill" in generated["pack_compiler_input"]["generated_surfaces_requested"]
    assert generated["action_catalog"]["catalog_role"] == (
        "domain_action_intent_and_handler_target_input_for_opl_generated_descriptors"
    )


def test_opl_standard_pack_runtime_guard_stages_declare_runtime_event_refs() -> None:
    generated = build_standard_pack()

    for stage in generated["stage_control_plane"]["stages"]:
        if not stage["trust_boundary"]["runtime_guard_required"]:
            continue
        refs = stage["trust_boundary"].get("runtime_event_refs")
        assert refs
        assert refs == stage["stage_contract"].get("runtime_event_refs")
        assert all(str(ref).startswith("runtime_event:") for ref in refs)
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
