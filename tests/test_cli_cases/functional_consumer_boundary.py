from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.standard_agent_purity_helpers import assert_standard_agent_purity_boundary

from .shared import write_profile


def test_sidecar_export_projects_functional_consumer_boundary(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=workspace_root)

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    boundary = payload["functional_consumer_boundary"]
    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert_standard_agent_purity_boundary(boundary)

    assert set(boundary["mas_does_not_own"]) >= {
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_workbench",
    }
    assert set(boundary["mas_domain_authority_surfaces"]) >= {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "owner_receipt",
        "safe_action_refs",
    }

    pack_input = boundary["declarative_pack_compiler_input"]
    assert pack_input["surface_kind"] == "mas_declarative_pack_compiler_input"
    assert pack_input["compiler_owner"] == "one-person-lab"
    assert pack_input["compiler_outputs_expected"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_action_adapter",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    assert pack_input["mas_long_term_code_owner"] == "minimal_authority_functions_only"

    handoff = boundary["generated_surface_handoff"]
    assert handoff["surface_kind"] == "mas_generated_surface_handoff"
    assert handoff["generated_surface_owner"] == "one-person-lab"
    assert handoff["current_mas_role"] == "domain_handler_and_refs_projection_source"
    assert handoff["long_term_mas_owner"] is False
    assert handoff["mas_handwritten_shell_expansion_allowed"] is False
    handoff_by_id = {item["surface_id"]: item for item in handoff["handoff_surfaces"]}
    assert set(handoff_by_id) == {
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "domain_action_adapter_export_dispatch",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    }
    assert handoff_by_id["sidecar"]["current_role"] == "domain_owner_route_refs_export_dispatch_source"
    assert handoff_by_id["domain_action_adapter_export_dispatch"]["current_role"] == (
        "domain_action_adapter"
    )
    assert handoff_by_id["skill"]["current_role"] == (
        "domain_skill_handler_target_and_pack_refs_only"
    )
    assert handoff_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert handoff_by_id["sidecar"]["target_role"] == "opl_generated_sidecar_handoff_surface"
    assert handoff_by_id["domain_action_adapter_export_dispatch"]["target_role"] == (
        "opl_generated_domain_action_adapter_handoff_surface"
    )
    generated_default = boundary["generated_default_caller_boundary"]
    assert generated_default["status"] == "opl_generated_hosted_shell_is_default_caller"
    assert generated_default["default_caller_owner"] == "one-person-lab"
    assert generated_default["mas_handwritten_shell_default_caller_allowed"] is False
    assert generated_default["all_default_surfaces_generated"] is True
    generated_surfaces = {
        item["surface_id"]: item for item in generated_default["surface_boundaries"]
    }
    assert set(generated_surfaces) == {
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_action_adapter",
        "workbench",
    }
    assert generated_surfaces["domain_action_adapter"]["mas_allowed_role"] == "domain_action_adapter"
    assert generated_surfaces["domain_action_adapter"]["parity_ref"] == (
        "domain_action_adapter_descriptor_parity"
    )
    assert generated_surfaces["workbench"]["default_caller_owner"] == "one-person-lab"
    assert all(item["mas_generic_owner_allowed"] is False for item in generated_surfaces.values())

    authority = boundary["minimal_authority_function_manifest"]
    assert authority["surface_kind"] == "mas_minimal_authority_function_manifest"
    assert authority["function_count"] == 7
    assert authority["all_other_program_surfaces"] == "opl_generated_or_domain_refs_projection_source"

    coverage = boundary["opl_functional_harness_consumer_coverage"]
    assert coverage["coverage_items"] == [
        "refs_only_memory_writeback_chain",
        "queue_stage_attempt_typed_closeout",
        "generic_transition_runner",
        "restart_dead_letter_repair_human_gate_state_chain",
    ]
    assert coverage["opl_harness_pass_is_paper_closure"] is False
    assert coverage["opl_harness_pass_is_publication_ready"] is False
    assert coverage["mas_owns_generic_runtime"] is False
    assert coverage["refs_only_memory_writeback_chain"]["body_included"] is False

    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 15
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert "local_launchd_scheduler_install_path" not in inventory_by_id
    assert "workspace_local_watch_service_wrappers" not in inventory_by_id
    assert "domain_health_diagnostic_loop_shell" not in inventory_by_id
    assert inventory_by_id["domain_authority_refs_index"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
        "src/med_autoscience/opl_domain_pack/",
        "src/med_autoscience/controllers/owner_route_handoff_parts/substrate_adapter.py",
    ]
    assert inventory_by_id["paper_work_unit_outbox_index"]["classification"] == "domain_authority_refs"
    assert inventory_by_id["artifact_authority"]["cannot_absorb_reason"] == (
        "Canonical manuscript/package mutation and submission authority are MAS artifact authority."
    )

    followthrough = boundary["functional_followthrough_gap_summary"]
    assert followthrough["status"] == "functional_structure_gaps_remaining"
    assert followthrough["classification_gap_count"] == 0
    assert followthrough["functional_structure_gap_count"] == 2
    assert followthrough["remaining_items_are_evidence_gates"] is False
    assert followthrough["remaining_functional_followthrough_gate_ids"] == [
        "standard_agent_purity_guard",
        "domain_ref_consumer_physical_thinning",
    ]
    assert "standard_agent_purity_guard" not in followthrough["closed_functional_structure_gate_ids"]
    assert set(followthrough["remaining_evidence_gate_ids"]) == {
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    }
