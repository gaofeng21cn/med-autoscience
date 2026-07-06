from __future__ import annotations

import importlib
from pathlib import Path

from med_autoscience.paper_mission_stage_closure_ledger import (
    latest_paper_mission_stage_closure_decision_readback,
    write_paper_mission_stage_closure_decision,
)
from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_stage_closure_readback_accepts_latest_followthrough_for_base_transaction(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_id = "obesity_multicenter_phenotype_atlas"
    base_ref = (
        "paper-mission-transaction::obesity_multicenter_phenotype_atlas::"
        "submission_milestone_candidate::paper-mission::"
        "obesity_multicenter_phenotype_atlas::paper_mission_import::one-shot-migration"
    )
    followthrough_ref = (
        "paper-mission-transaction::obesity_multicenter_phenotype_atlas::"
        "submission_milestone_candidate::followthrough::followthrough-01::"
        "paper-mission::obesity_multicenter_phenotype_atlas::"
        "paper_mission_import::one-shot-migration"
    )

    write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "f6_submission_stage_packet"
        ),
        study_id=study_id,
        decision={
            "stage_id": "submission_milestone_candidate",
            "work_unit_id": "submission_milestone_candidate",
            "outcome": {"kind": "next_stage_transition"},
        },
        source_readback={
            "mission_id": "mission-base",
            "paper_mission_transaction": {
                "transaction_id": base_ref,
                "stage_id": "submission_milestone_candidate",
            },
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready",),
    )
    output_manifest = write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "paper_mission_terminalize_stage"
        ),
        study_id=study_id,
        decision={
            "stage_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "work_unit_id": "submission_milestone_candidate::followthrough::followthrough-01",
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
        source_readback={
            "mission_id": "mission-followthrough",
            "paper_mission_transaction": {
                "transaction_id": followthrough_ref,
                "stage_id": "submission_milestone_candidate::followthrough::followthrough-01",
            },
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready",),
    )

    readback = latest_paper_mission_stage_closure_decision_readback(
        workspace_root=workspace_root,
        study_id=study_id,
        transaction_ref=base_ref,
    )

    assert readback is not None
    assert readback["decision_ref"] == output_manifest["stage_closure_decision_ref"]
    assert readback["paper_mission_transaction_ref"] == followthrough_ref
    assert readback["stage_id"] == (
        "submission_milestone_candidate::followthrough::followthrough-01"
    )
    assert readback["can_claim_paper_progress"] is False


def test_stage_closure_readback_accepts_base_for_followthrough_transaction(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    base_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
        "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
    )
    followthrough_ref = (
        "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
        "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
        "::followthrough::89b46ab394eb"
    )

    output_manifest = write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "paper_mission_terminalize_stage"
        ),
        study_id=study_id,
        decision={
            "stage_id": "write",
            "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
        source_readback={
            "mission_id": "mission-base",
            "paper_mission_transaction": {
                "transaction_id": base_ref,
                "stage_id": "write",
            },
        },
        source="test",
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
        forbidden_authority_claims=("publication_ready",),
    )

    readback = latest_paper_mission_stage_closure_decision_readback(
        workspace_root=workspace_root,
        study_id=study_id,
        transaction_ref=followthrough_ref,
    )

    assert readback is not None
    assert readback["decision_ref"] == output_manifest["stage_closure_decision_ref"]
    assert readback["paper_mission_transaction_ref"] == base_ref
    assert readback["stage_id"] == "write"
    assert readback["can_claim_paper_progress"] is False


def test_consumption_ledger_route_back_projection_uses_stage_closure_ledger() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    transaction = {
        "transaction_id": (
            "paper-mission-transaction::003-dpcc-primary-care-phenotype-treatment-gap::"
            "write::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
            "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
            "::followthrough::89b46ab394eb"
        ),
        "study_id": study_id,
        "stage_id": "write",
        "stage_terminal_decision": {
            "decision_kind": "continue_same_stage",
            "next_owner": "write",
            "next_work_unit": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        },
    }
    stage_closure_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "projection_status": "terminalizer_outcome_observed",
        "source_surface_kind": "paper_mission_stage_closure_ledger",
        "decision_ref": "/tmp/dm003/stage_closure_decision.json",
        "stage_id": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
            "next_owner": "MedAutoScience",
            "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
            "authority_materialized": False,
        },
        "authority_boundary": {
            "authority_materialized": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_submission_ready_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
    }

    payload = commands._consumption_ledger_route_back_projection(
        transaction_readback={
            "paper_mission_transaction": transaction,
            "stage_terminal_decision": transaction["stage_terminal_decision"],
            "opl_route_command": {
                "command_kind": "resume_stage",
                "target": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            },
            "opl_runtime_carrier": {},
            "opl_runtime_carrier_readback": {},
            "opl_runtime_readback_status": None,
            "terminal_owner_gate_owner_answer_readback": {
                "owner_answer_shape": "route_back_evidence_ref"
            },
            "next_owner_or_human_decision": {
                "kind": "owner_or_route",
                "next_owner": "write",
            },
            "transaction_state": "accepted_submission_milestone_candidate",
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
        },
        consumption_readback={
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "opl_route_handoff": {},
        },
        base_readback={"study_id": study_id},
        stage_closure_ledger_readback=stage_closure_decision,
    )

    assert payload is not None
    assert payload["stage_closure_decision"]["projection_status"] == (
        "terminalizer_outcome_observed"
    )
    assert payload["stage_closure_decision_ref"] == (
        "/tmp/dm003/stage_closure_decision.json"
    )
    assert payload["stage_closure_outcome"] == "next_stage_transition"
    assert payload["canonical_next_action_source"] == "stage_closure.next_action"
    assert payload["next_action"]["work_unit_id"] == (
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )
