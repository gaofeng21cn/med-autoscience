from __future__ import annotations

from typing import Mapping


STANDARD_AGENT_BOUNDARY_KEYS = {
    "schema_version",
    "surface_kind",
    "status",
    "consumer_role",
    "generic_surface_owner",
    "generic_surfaces_consumed_from_opl",
    "mas_does_not_own",
    "mas_domain_authority_surfaces",
    "declarative_pack_compiler_input",
    "generated_surface_handoff",
    "generated_default_caller_boundary",
    "standard_agent_purity",
    "minimal_authority_function_manifest",
    "functional_surface_classification",
    "functional_module_inventory",
    "functional_module_inventory_summary",
    "functional_followthrough_gap_summary",
    "domain_authority_refs_retirement_gates",
    "domain_authority_refs_index_role",
    "opl_functional_harness_consumer_coverage",
    "standard_agent_purity_guard",
    "standard_agent_purity_guard_scope",
    "proof_surfaces",
    "forbidden_regressions",
}

STANDARD_AGENT_HANDOFF_KEYS = {
    "surface_kind",
    "version",
    "target_domain_id",
    "status",
    "generic_runtime_owner",
    "domain_owner",
    "domain_intent_adapter_role",
    "standard_agent_purity",
    "active_domain_allowed_actions",
    "forbidden_mas_roles",
    "opl_replacement_surfaces",
    "code_path_roles",
    "generated_default_caller_boundary",
    "default_caller_policy",
    "authority_boundary",
}

EXPECTED_CLASSIFICATION_COUNTS = {
    "declarative_pack_generated_surface": 7,
    "domain_authority_refs": 5,
    "minimal_authority_function": 3,
}


def assert_standard_agent_purity_boundary(boundary: Mapping[str, object]) -> None:
    assert set(boundary) == STANDARD_AGENT_BOUNDARY_KEYS

    purity = boundary["standard_agent_purity"]
    assert isinstance(purity, Mapping)
    assert purity["surface_kind"] == "mas_standard_opl_agent_purity"
    assert purity["status"] == "pure_standard_agent_active"
    assert purity["default_runtime_owner"] == "one-person-lab"
    assert purity["generated_surface_owner"] == "one-person-lab"
    assert purity["domain_owner"] == "med-autoscience"
    assert purity["active_private_generic_residue_count"] == 0
    assert purity["functional_structure_gap_count"] == 0
    assert purity["default_caller_count"] == 0
    assert purity["runtime_package_residue_count"] == 0
    assert "active_compatibility_aliases" not in purity
    assert purity["retired_alias_residue_refs"] == []
    assert purity["history_detail_in_default_read_model"] is False
    assert purity["domain_projection_policy"] == (
        "refs_receipts_blockers_only_no_body_verdict_or_blob"
    )
    assert set(purity["retained_surface_classes"]) == set(EXPECTED_CLASSIFICATION_COUNTS)
    assert "mas_owned_generic_queue" in purity["forbidden_active_claims"]

    guard = boundary["standard_agent_purity_guard"]
    assert isinstance(guard, Mapping)
    assert guard["status"] == "standard_agent_purity_guard"
    assert guard["default_caller_count"] == 0
    assert guard["default_manager"] == "opl"
    assert guard["runtime_package_residue_count"] == 0
    assert "active_compatibility_aliases" not in guard
    assert guard["retired_alias_residue_refs"] == []

    summary = boundary["functional_module_inventory_summary"]
    assert isinstance(summary, Mapping)
    assert summary["total_count"] == 15
    assert summary["classification_counts"] == EXPECTED_CLASSIFICATION_COUNTS
    assert summary["classification_gap_count"] == 0
    assert summary["functional_structure_gap_count"] == 0
    assert summary["active_private_generic_residue_count"] == 0


def assert_standard_agent_purity_handoff(handoff: Mapping[str, object]) -> None:
    assert set(handoff) == STANDARD_AGENT_HANDOFF_KEYS

    purity = handoff["standard_agent_purity"]
    assert isinstance(purity, Mapping)
    assert purity["surface_kind"] == "mas_standard_opl_agent_purity"
    assert purity["status"] == "pure_standard_agent_active"
    assert purity["default_runtime_owner"] == "one-person-lab"
    assert purity["generated_surface_owner"] == "one-person-lab"
    assert purity["domain_owner"] == "med-autoscience"
    assert purity["active_generic_owner_claim_allowed"] is False
    assert purity["default_caller_count"] == 0
    assert purity["runtime_package_residue_count"] == 0
    assert "active_compatibility_aliases" not in purity
    assert purity["retired_alias_residue_refs"] == []
    assert purity["history_policy"]["default_read_model_exposes_history_details"] is False
    assert purity["domain_projection_policy"] == (
        "refs_receipts_blockers_only_no_body_verdict_or_blob"
    )
    assert "mas_generic_runtime_owner" in purity["forbidden_active_claims"]
