from __future__ import annotations

from copy import deepcopy
import importlib
from pathlib import Path

import pytest

import med_autoscience.controllers.opl_unique_control_plane_boundary.functional_followthrough_gaps as followthrough_gaps
import med_autoscience.controllers.opl_provider_ready_adapter.opl_unique_control_plane_handoff as provider_handoff
import med_autoscience.controllers.opl_provider_ready_adapter.skeleton_mapping as skeleton_mapping
from med_autoscience.controllers.opl_unique_control_plane_boundary import consumer_migration
from med_autoscience.controllers.opl_unique_control_plane_boundary import (
    consumer_migration_inventory,
)
from tests.standard_agent_purity_helpers import assert_standard_agent_purity_boundary


def test_opl_unique_control_plane_boundary_top_level_callable_is_retired() -> None:
    package = importlib.import_module(
        "med_autoscience.controllers.opl_unique_control_plane_boundary"
    )

    assert not hasattr(package, "build_opl_unique_control_plane_boundary")


def test_consumer_migration_contract_is_standard_agent_purity_and_pack_input_only() -> None:
    boundary = consumer_migration.build_functional_consumer_boundary()

    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert set(boundary["mas_does_not_own"]) >= {
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_workbench",
    }
    assert boundary["declarative_pack_compiler_input"]["compiler_owner"] == "one-person-lab"
    assert boundary["generated_surface_handoff"]["mas_handwritten_shell_expansion_allowed"] is False
    assert boundary["functional_module_inventory_summary"]["active_private_generic_residue_count"] == 0
    assert boundary["standard_agent_purity"]["source_morphology"]["status"] == "clean"
    assert boundary["standard_agent_purity"]["source_morphology"][
        "source_truth_available"
    ] is True
    assert_standard_agent_purity_boundary(boundary)

    decision = boundary["physical_retirement_decision"]
    decision_ref = decision["canonical_ref"]
    inventory = {
        item["module_id"]: item for item in boundary["functional_module_inventory"]
    }
    for module_id in (
        "generic_cli_mcp_product_wrappers",
        "paper_mission_owner_surface_materialize_dispatch_shell",
        "workbench_portal_generic_shell",
    ):
        gate = inventory[module_id]["bridge_exit_gate"]
        assert gate["current_status"] == (
            "physical_retirement_authorized_for_exact_migration_scope"
        )
        assert gate["domain_repo_physical_delete_authorized"] is True
        assert gate["physical_delete_authorized_by_refs"] is True
        assert gate["owner_decision_refs"] == [decision_ref]
        assert gate["owner_decision_result_shape"] == "physical_delete_authorization_ref"
        assert gate["physical_delete_authorization_refs"] == [decision_ref]
        assert gate["required_before_retire"] == []
        assert gate["authority_boundary"]["is_runtime_owner_receipt"] is False
        assert gate["authority_boundary"]["can_claim_domain_ready"] is False
    inventory = {
        item["module_id"]: item for item in boundary["functional_module_inventory"]
    }
    assert inventory["workbench_portal_generic_shell"]["latest_thinning_evidence"][
        "read_model_materializer_boundary"
    ]["domain_repo_physical_delete_authorized"] is True
    assert inventory["paper_mission_owner_surface_materialize_dispatch_shell"][
        "latest_thinning_evidence"
    ]["domain_repo_physical_delete_authorized"] is True


def test_generated_surface_and_skeleton_mappings_only_reference_current_paths() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    boundary = consumer_migration.build_functional_consumer_boundary()
    handoff = boundary["generated_surface_handoff"]
    current_paths = {
        path
        for surface in handoff["handoff_surfaces"]
        for path in surface["current_paths"]
    }
    skeleton = skeleton_mapping.build_physical_skeleton_layout_audit_surface()
    current_paths.update(
        path
        for slot in skeleton["slots"]
        for path in slot["repo_paths"]
    )

    assert "src/med_autoscience/controllers/current_work_unit/workspace_projection.py" not in current_paths
    assert all((repo_root / path).exists() for path in current_paths)


@pytest.mark.parametrize(
    "decision_case",
    ["authorization_false", "decision_missing", "decision_invalid"],
)
def test_physical_retirement_decision_fails_closed_across_derived_surfaces(
    decision_case: str,
) -> None:
    decision: object
    if decision_case == "authorization_false":
        decision = deepcopy(
            followthrough_gaps.PRIVATE_SURFACE_PHYSICAL_RETIREMENT_DECISION
        )
        decision["authorization"]["physical_delete_authorized"] = False
    elif decision_case == "decision_missing":
        decision = None
    else:
        decision = {"authorization": "invalid"}

    boundary = consumer_migration.build_functional_consumer_boundary(
        physical_retirement_decision=decision
    )
    decision_readback = boundary["physical_retirement_decision"]
    assert decision_readback["physical_delete_authorized"] is False
    assert decision_readback["owner_decision_refs"] == []
    assert decision_readback["authority_boundary"]["can_claim_domain_ready"] is False
    assert boundary["standard_agent_purity"][
        "domain_repo_physical_delete_authorized"
    ] is False
    assert boundary["standard_agent_purity_guard"][
        "domain_repo_physical_delete_authorized"
    ] is False

    summary = boundary["functional_followthrough_gap_summary"]
    assert summary["domain_repo_physical_delete_authorized"] is False
    decision_gates = [
        gate
        for gate in summary["remaining_functional_followthrough_gates"]
        if gate.get("physical_retirement_decision_ref")
    ]
    assert decision_gates
    assert all(gate["physical_delete_authorized"] is False for gate in decision_gates)

    inventory = {
        item["module_id"]: item for item in boundary["functional_module_inventory"]
    }
    for module_id in (
        "generic_cli_mcp_product_wrappers",
        "paper_mission_owner_surface_materialize_dispatch_shell",
        "workbench_portal_generic_shell",
    ):
        gate = inventory[module_id]["bridge_exit_gate"]
        assert gate["current_status"] == (
            "physical_retirement_decision_missing_or_not_authorized"
        )
        assert gate["domain_repo_physical_delete_authorized"] is False
        assert gate["physical_delete_authorized_by_refs"] is False
        assert gate["owner_decision_refs"] == []
        assert gate["physical_delete_authorization_refs"] == []
        assert gate["required_before_retire"] == [
            "valid_domain_owner_physical_retirement_decision"
        ]
    assert inventory["workbench_portal_generic_shell"]["latest_thinning_evidence"][
        "read_model_materializer_boundary"
    ]["domain_repo_physical_delete_authorized"] is False
    assert inventory["paper_mission_owner_surface_materialize_dispatch_shell"][
        "latest_thinning_evidence"
    ]["domain_repo_physical_delete_authorized"] is False

    handoff = provider_handoff.build_opl_unique_control_plane_handoff(
        physical_retirement_decision=decision
    )
    assert handoff["standard_agent_purity"][
        "domain_repo_physical_delete_authorized"
    ] is False


def test_source_morphology_reopens_purity_gate_for_private_generic_symbol(
    tmp_path: Path,
) -> None:
    source_path = (
        tmp_path
        / "src"
        / "med_autoscience"
        / "controllers"
        / "artifact_lifecycle_inventory.py"
    )
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        "def build_artifact_lifecycle_inventory():\n    return {}\n",
        encoding="utf-8",
    )

    morphology = consumer_migration_inventory.build_source_morphology(
        repo_root=tmp_path
    )
    boundary = consumer_migration.build_functional_consumer_boundary(
        repo_root=tmp_path
    )

    assert morphology["active_private_generic_residue_count"] == 1
    assert morphology["active_private_generic_residue_module_ids"] == [
        "artifact_lifecycle_storage_audit_shell"
    ]
    assert morphology["active_private_generic_residues"][0]["token"] == (
        "def build_artifact_lifecycle_inventory("
    )
    assert boundary["standard_agent_purity"]["status"] == (
        "standard_agent_source_shape_residue_or_scan_gap"
    )
    assert boundary["functional_followthrough_gap_summary"][
        "remaining_functional_followthrough_gate_ids"
    ] == ["standard_agent_purity_guard"]


def test_functional_structure_gap_count_reopens_when_closure_proof_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gates = tuple(dict(item) for item in followthrough_gaps.FUNCTIONAL_STRUCTURE_CLOSURE_GATES)
    reopened_gate = dict(gates[0])
    reopened_gate["closure_proof_refs"] = []
    monkeypatch.setattr(
        followthrough_gaps,
        "FUNCTIONAL_STRUCTURE_CLOSURE_GATES",
        (reopened_gate, *gates[1:]),
    )

    summary = followthrough_gaps.build_functional_followthrough_gap_summary(
        classification_counts={},
        source_morphology={
            "source_truth_available": True,
            "source_purity_gap_count": 0,
            "active_private_generic_residue_count": 0,
            "active_private_generic_residue_module_ids": [],
        },
    )

    assert summary["status"] == "functional_structure_gaps_remaining"
    assert summary["functional_structure_gap_count"] == 1
    assert summary["remaining_items_are_evidence_gates"] is False
    assert summary["remaining_gap_classification"] == "functional_structure_followthrough_gates"
