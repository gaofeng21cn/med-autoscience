from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import med_autoscience.controllers.opl_unique_control_plane_boundary.functional_followthrough_gaps as followthrough_gaps
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
