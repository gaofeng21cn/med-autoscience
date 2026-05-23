from __future__ import annotations

import importlib

import pytest

import med_autoscience.controllers.domain_slo_scheduler_projection_parts.functional_followthrough_gaps as followthrough_gaps
from med_autoscience.controllers.domain_slo_scheduler_projection_parts import consumer_migration


def test_domain_slo_scheduler_projection_top_level_callable_is_retired() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.controllers.domain_slo_scheduler_projection")


def test_consumer_migration_contract_is_tombstone_and_pack_input_only() -> None:
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
    assert boundary["no_resurrection_proof"]["cleanup_only_commands"] == []
    assert boundary["no_resurrection_proof"]["forbidden_explicit_callers"] == [
        "retired:runtime-supervision-status --profile <profile> --manager local",
        "retired:runtime-ensure-supervision --profile <profile> --manager local",
        "retired:runtime-remove-supervision --profile <profile> --manager local",
    ]


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
        legacy_cleanup_items=[],
    )

    assert summary["status"] == "functional_structure_gaps_remaining"
    assert summary["functional_structure_gap_count"] == 1
    assert summary["remaining_items_are_evidence_gates"] is False
    assert summary["remaining_gap_classification"] == "functional_structure_followthrough_gates"
