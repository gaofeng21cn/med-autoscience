from __future__ import annotations

import json
import os
from pathlib import Path

from med_autoscience.controllers.paper_mission_currentness import (
    receipt_owner_consumption_superseded_by_stage_closure,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption.storage import (
    _write_output_packet,
)
from tests.test_paper_mission_consumption_currentness_cases.shared import (
    _receipt_owner_consumption_payload,
)


def test_newer_route_checkpoint_stage_closure_supersedes_stale_route_checkpoint_receipt(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stage_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    receipt_ref.parent.mkdir(parents=True)
    stage_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    stage_ref.write_text("{}", encoding="utf-8")
    os.utime(receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(stage_ref, (3_000_000_000, 3_000_000_000))

    assert receipt_owner_consumption_superseded_by_stage_closure(
        receipt_owner_consumption_readback={
            "status": "owner_consumption_applied",
            "source_ref": str(receipt_ref),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            },
            "stage_closure_decision": {
                "stage_id": "submission_milestone_candidate",
                "work_unit_id": "submission_milestone_candidate",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    f"sat-stale/{study_id}/stage_attempt_closeout_packet.json"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-stale",
                "opl_closeout": {"stage_attempt_id": "sat-stale"},
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                },
            },
        },
        stage_closure_ledger_readback={
            "source_ref": str(stage_ref),
            "stage_id": "write",
            "work_unit_id": (
                "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
            ),
            "route_checkpoint_evidence_ref": (
                "ops/medautoscience/paper_mission_stage_attempts/"
                "sat-current/stage_attempt_closeout_packet.json"
            ),
            "receipt_evidence_ref": "opl://stage-attempts/sat-current",
            "opl_closeout": {"stage_attempt_id": "sat-current"},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
    )


def test_newer_non_route_stage_closure_supersedes_stale_route_checkpoint_receipt(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stage_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    receipt_ref.parent.mkdir(parents=True)
    stage_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    stage_ref.write_text("{}", encoding="utf-8")
    os.utime(receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(stage_ref, (3_000_000_000, 3_000_000_000))

    assert receipt_owner_consumption_superseded_by_stage_closure(
        receipt_owner_consumption_readback={
            "status": "owner_consumption_applied",
            "source_ref": str(receipt_ref),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            },
            "stage_closure_decision": {
                "stage_id": "write",
                "work_unit_id": "medical_prose_write_repair",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                },
            },
        },
        stage_closure_ledger_readback={
            "source_ref": str(stage_ref),
            "stage_id": "review",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "current_package_mirror_sync",
            },
        },
    )


def test_receipt_owner_consumption_write_preserves_newer_route_checkpoint(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    output_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
    )
    older_checkpoint = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-old"
        / "stage_attempt_closeout_packet.json"
    )
    newer_checkpoint = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-new"
        / "stage_attempt_closeout_packet.json"
    )
    older_checkpoint.parent.mkdir(parents=True)
    newer_checkpoint.parent.mkdir(parents=True)
    older_checkpoint.write_text("{}", encoding="utf-8")
    newer_checkpoint.write_text("{}", encoding="utf-8")
    os.utime(older_checkpoint, (2_000_000_000, 2_000_000_000))
    os.utime(newer_checkpoint, (3_000_000_000, 3_000_000_000))
    newer_payload = _receipt_owner_consumption_payload(
        study_id=study_id,
        checkpoint_ref=(
            "ops/medautoscience/paper_mission_stage_attempts/"
            "sat-new/stage_attempt_closeout_packet.json"
        ),
    )
    older_payload = _receipt_owner_consumption_payload(
        study_id=study_id,
        checkpoint_ref=(
            "ops/medautoscience/paper_mission_stage_attempts/"
            "sat-old/stage_attempt_closeout_packet.json"
        ),
    )

    _write_output_packet(
        output_root=output_root,
        study_id=study_id,
        payload=newer_payload,
        writes_authority=True,
    )
    manifest = _write_output_packet(
        output_root=output_root,
        study_id=study_id,
        payload=older_payload,
        writes_authority=True,
    )

    assert manifest["write_skipped_stale_route_checkpoint"] is True
    payload = json.loads(
        (output_root / study_id / "receipt_owner_consumption.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["mas_receipt_consumption"]["route_checkpoint_evidence_ref"].endswith(
        "sat-new/stage_attempt_closeout_packet.json"
    )


def test_same_route_checkpoint_stage_closure_does_not_supersede_receipt(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stage_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    receipt_ref.parent.mkdir(parents=True)
    stage_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    stage_ref.write_text("{}", encoding="utf-8")
    os.utime(receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(stage_ref, (3_000_000_000, 3_000_000_000))
    checkpoint_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        f"sat-current/{study_id}/stage_attempt_closeout_packet.json"
    )
    decision = {
        "stage_id": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "route_checkpoint_evidence_ref": checkpoint_ref,
        "receipt_evidence_ref": "opl://stage-attempts/sat-current",
        "opl_closeout": {"stage_attempt_id": "sat-current"},
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
        },
    }

    assert receipt_owner_consumption_superseded_by_stage_closure(
        receipt_owner_consumption_readback={
            "status": "owner_consumption_applied",
            "source_ref": str(receipt_ref),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            },
            "stage_closure_decision": decision,
        },
        stage_closure_ledger_readback={
            "source_ref": str(stage_ref),
            **decision,
        },
    ) is False


def test_same_route_checkpoint_with_missing_refs_does_not_supersede_receipt(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stage_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    receipt_ref.parent.mkdir(parents=True)
    stage_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    stage_ref.write_text("{}", encoding="utf-8")
    os.utime(receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(stage_ref, (3_000_000_000, 3_000_000_000))
    decision = {
        "stage_id": "submission_milestone_candidate",
        "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        "route_checkpoint_evidence_ref": (
            "ops/medautoscience/paper_mission_stage_attempts/"
            "sat-current/stage_attempt_closeout_packet.json"
        ),
        "receipt_evidence_ref": "opl://stage-attempts/sat-current",
        "opl_closeout": {"stage_attempt_id": "sat-current"},
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
        },
    }

    assert receipt_owner_consumption_superseded_by_stage_closure(
        receipt_owner_consumption_readback={
            "status": "owner_consumption_applied",
            "source_ref": str(receipt_ref),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            },
            "stage_closure_decision": decision,
        },
        stage_closure_ledger_readback={
            "source_ref": str(stage_ref),
            "stage_id": decision["stage_id"],
            "work_unit_id": decision["work_unit_id"],
            "opl_closeout": decision["opl_closeout"],
            "outcome": decision["outcome"],
        },
    ) is False


def test_older_mismatched_route_checkpoint_stage_closure_does_not_supersede_newer_receipt(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stage_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    receipt_ref.parent.mkdir(parents=True)
    stage_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    stage_ref.write_text("{}", encoding="utf-8")
    os.utime(stage_ref, (2_000_000_000, 2_000_000_000))
    os.utime(receipt_ref, (3_000_000_000, 3_000_000_000))

    assert receipt_owner_consumption_superseded_by_stage_closure(
        receipt_owner_consumption_readback={
            "status": "owner_consumption_applied",
            "source_ref": str(receipt_ref),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            },
            "stage_closure_decision": {
                "stage_id": "write",
                "work_unit_id": "medical_prose_write_repair",
                "route_checkpoint_evidence_ref": "opl://family-runtime/tasks/stale",
                "receipt_evidence_ref": "opl://stage-attempts/sat-stale",
                "opl_closeout": {"stage_attempt_id": "sat-stale"},
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                },
            },
        },
        stage_closure_ledger_readback={
            "source_ref": str(stage_ref),
            "stage_id": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": str(stage_ref),
            "opl_closeout": {"stage_attempt_id": "sat-current"},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "next_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
            },
        },
    ) is False


def test_thin_legacy_stage_closure_does_not_supersede_consumed_route_checkpoint_receipt(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    receipt_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
        / "receipt_owner_consumption.json"
    )
    stage_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_closure"
        / "paper_mission_terminalize_stage"
        / study_id
        / "stage_closure_decision.json"
    )
    receipt_ref.parent.mkdir(parents=True)
    stage_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    stage_ref.write_text("{}", encoding="utf-8")
    os.utime(receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(stage_ref, (3_000_000_000, 3_000_000_000))

    assert receipt_owner_consumption_superseded_by_stage_closure(
        receipt_owner_consumption_readback={
            "status": "owner_consumption_applied",
            "source_ref": str(receipt_ref),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
            },
            "stage_closure_decision": {
                "stage_id": "write",
                "work_unit_id": (
                    "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
                ),
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current/stage_attempt_closeout_packet.json"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-current",
                "opl_closeout": {"stage_attempt_id": "sat-current"},
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                },
            },
        },
        stage_closure_ledger_readback={
            "source_ref": str(stage_ref),
            "stage_id": "write",
            "work_unit_id": (
                "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
            ),
            "opl_closeout": {"stage_attempt_id": "sat-legacy-thin"},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "next_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
            },
        },
    ) is False
