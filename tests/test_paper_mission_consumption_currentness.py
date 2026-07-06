from __future__ import annotations

import json
import os
from pathlib import Path

from med_autoscience.controllers.owner_route_handoff_parts.paper_mission_consumption_route_handoff import (
    _paper_mission_handoff_timestamp_key,
    latest_paper_mission_consumption_route_handoff,
)
from med_autoscience.controllers.paper_mission_currentness import (
    receipt_owner_consumption_superseded_by_consumption,
    receipt_owner_consumption_superseded_by_stage_closure,
)
from med_autoscience.paper_mission_consumption_readback import (
    _ledger_timestamp_key,
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier
from med_autoscience.paper_mission_transaction import build_paper_mission_transaction


AUDIT_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)


def test_consumption_transaction_readback_prefers_newest_mtime_over_run_id(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    old_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tzz_old_takeover_dm002_submit",
        transaction_ref="paper-mission-transaction::dm002::old-takeover",
        fingerprint="fingerprint::dm002::old-takeover",
    )
    fresh_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Taa_fresh_main_drive_dm002",
        transaction_ref="paper-mission-transaction::dm002::fresh-drive",
        fingerprint="fingerprint::dm002::fresh-drive",
    )
    os.utime(old_record, (1_000_000_000, 1_000_000_000))
    os.utime(fresh_record, (2_000_000_000, 2_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(fresh_record)
    assert readback["paper_mission_transaction"]["transaction_id"] == (
        "paper-mission-transaction::dm002::fresh-drive"
    )
    assert readback["opl_runtime_carrier"]["work_unit_fingerprint"] == (
        "fingerprint::dm002::fresh-drive"
    )


def test_consumption_route_handoff_prefers_newest_mtime_over_run_id(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    old_handoff = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tzz_old_takeover_dm002_submit",
        transaction_ref="paper-mission-transaction::dm002::old-takeover",
        fingerprint="fingerprint::dm002::old-takeover",
    ).parent / "opl_route_handoff.json"
    fresh_handoff = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Taa_fresh_main_drive_dm002",
        transaction_ref="paper-mission-transaction::dm002::fresh-drive",
        fingerprint="fingerprint::dm002::fresh-drive",
    ).parent / "opl_route_handoff.json"
    os.utime(old_handoff, (1_000_000_000, 1_000_000_000))
    os.utime(fresh_handoff, (2_000_000_000, 2_000_000_000))

    handoff = latest_paper_mission_consumption_route_handoff(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert handoff["source_ref"] == str(fresh_handoff)
    assert handoff["paper_mission_transaction_ref"] == (
        "paper-mission-transaction::dm002::fresh-drive"
    )
    assert handoff["opl_runtime_carrier"]["work_unit_fingerprint"] == (
        "fingerprint::dm002::fresh-drive"
    )


def test_consumption_currentness_prefers_external_delta_over_later_drive_noop(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    external_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260628T034633Z_repair_execution_delta",
        transaction_ref="paper-mission-transaction::dm003::followthrough-02",
        fingerprint="fingerprint::dm003::repair-delta",
        external_delta_ref="/workspace/studies/dm003/artifacts/controller/repair_execution_evidence/latest.json",
    )
    later_noop_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="paper_mission_drive/followthrough-02",
        transaction_ref="paper-mission-transaction::dm003::followthrough-02",
        fingerprint="fingerprint::dm003::repair-delta",
    )
    os.utime(external_record, (2_000_000_000, 2_000_000_000))
    os.utime(external_record.parent / "opl_route_handoff.json", (2_000_000_000, 2_000_000_000))
    os.utime(later_noop_record, (3_000_000_000, 3_000_000_000))
    os.utime(
        later_noop_record.parent / "opl_route_handoff.json",
        (3_000_000_000, 3_000_000_000),
    )

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )
    handoff = latest_paper_mission_consumption_route_handoff(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(external_record)
    assert handoff["source_ref"] == str(external_record.parent / "opl_route_handoff.json")


def test_consumption_currentness_prefers_newer_paper_facing_delta_over_old_external_delta(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    external_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260628T080615Z_quality_repair_delta",
        transaction_ref="paper-mission-transaction::dm002::quality-repair",
        fingerprint="fingerprint::dm002::quality-repair",
        external_delta_ref="/workspace/studies/dm002/artifacts/controller/repair_execution_evidence/latest.json",
    )
    low_quality_handoff_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260629T_low_quality_handoff_consume_v3",
        transaction_ref="paper-mission-transaction::dm002::low-quality-handoff",
        fingerprint="fingerprint::dm002::low-quality-handoff",
        paper_facing_delta_ref=(
            "/workspace/ops/medautoscience/paper_mission_candidate_package/"
            "20260629T_low_quality_handoff/dm002/paper_facing_candidate_delta.json"
        ),
    )
    os.utime(external_record, (2_000_000_000, 2_000_000_000))
    os.utime(low_quality_handoff_record, (3_000_000_000, 3_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(low_quality_handoff_record)
    assert readback["candidate_ref"] == str(
        low_quality_handoff_record.parent / "package_manifest.json"
    )


def test_consumption_currentness_prefers_reviewer_revision_over_old_submission_candidate(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    old_submission_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260701T045145Z_manuscript_volume_clinical_figures_submit",
        transaction_ref="paper-mission-transaction::obesity::submission-candidate",
        fingerprint="fingerprint::obesity::submission-candidate",
        paper_facing_delta_ref="/workspace/obesity/submission/paper_facing_delta.json",
    )
    reviewer_revision_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260701T1425Z_external_sci_registry_review",
        transaction_ref="paper-mission-transaction::obesity::reviewer-revision",
        fingerprint="fingerprint::obesity::reviewer-revision",
        milestone_kind="reviewer_revision_candidate",
        relative_candidate_ref=True,
    )
    os.utime(old_submission_record, (2_000_000_000, 2_000_000_000))
    os.utime(reviewer_revision_record, (3_000_000_000, 3_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )
    handoff = latest_paper_mission_consumption_route_handoff(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(reviewer_revision_record)
    assert readback["candidate_ref"] == str(
        Path("ops")
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "20260701T1425Z_external_sci_registry_review"
        / study_id
        / "package_manifest.json"
    )
    assert handoff["source_ref"] == str(
        reviewer_revision_record.parent / "opl_route_handoff.json"
    )


def test_consumption_ledger_timestamp_keys_accept_z_run_ids(tmp_path: Path) -> None:
    z_run_path = (
        tmp_path
        / "paper_mission_consumption_ledger"
        / "20260624Zmain_drive_dm002_fresh"
        / "002-dm-china-us-mortality-attribution"
        / "consume_record.json"
    )

    assert _ledger_timestamp_key(z_run_path) == "20260624Zmain_drive_dm002_fresh"
    assert _paper_mission_handoff_timestamp_key(z_run_path) == (
        "20260624Zmain_drive_dm002_fresh"
    )


def test_consumption_transaction_readback_rejects_cross_identity_packets(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    consume_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tcross_identity_dm002",
        transaction_ref="paper-mission-transaction::dm002::canonical",
        fingerprint="fingerprint::dm002::canonical",
    )
    _patch_json(
        consume_record.parent / "stage_terminal_decision.json",
        {
            "stage_terminal_decision_ref": (
                "paper-mission-transaction::dm002::other#stage_terminal_decision"
            )
        },
    )

    assert (
        latest_paper_mission_consumption_transaction_readback(
            workspace_root=workspace_root,
            study_id=study_id,
        )
        is None
    )


def test_consumption_transaction_readback_keeps_accepted_candidate_when_route_handoff_is_route_back(
    tmp_path: Path,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    consume_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="paper_mission_drive/followthrough-02",
        transaction_ref="paper-mission-transaction::dm003::followthrough-02",
        fingerprint="fingerprint::dm003::followthrough-02",
    )
    _patch_json(
        consume_record.parent / "stage_terminal_decision.json",
        {"transaction_state": "route_back"},
    )

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["source_ref"] == str(consume_record)
    assert readback["selected_outcome"] == "accepted_candidate"
    assert readback["consume_candidate_status"] == (
        "accepted_submission_milestone_candidate"
    )
    assert readback["stage_terminal_decision"]["decision_kind"] == "route_back"
    assert readback["opl_route_command"]["command_kind"] == "route_back"
    assert readback["transaction_state"] == "route_back"


def test_route_back_consumption_does_not_supersede_consumed_typed_blocker_receipt(
    tmp_path: Path,
) -> None:
    study_id = "obesity_multicenter_phenotype_atlas"
    workspace_root = tmp_path / "workspace"
    receipt_ref = workspace_root / "ops" / "medautoscience" / "receipt.json"
    receipt_ref.parent.mkdir(parents=True)
    receipt_ref.write_text("{}", encoding="utf-8")
    consume_record = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="paper_mission_drive",
        transaction_ref="paper-mission-transaction::obesity::submission-candidate",
        fingerprint="fingerprint::obesity::submission-candidate",
    )
    _patch_json(
        consume_record.parent / "stage_terminal_decision.json",
        {"transaction_state": "route_back"},
    )
    os.utime(receipt_ref, (2_000_000_000, 2_000_000_000))
    os.utime(consume_record, (3_000_000_000, 3_000_000_000))

    readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    )

    assert readback["transaction_state"] == "route_back"
    assert (
        receipt_owner_consumption_superseded_by_consumption(
            receipt_owner_consumption_readback={
                "status": "owner_consumption_applied",
                "source_ref": str(receipt_ref),
                "mas_receipt_consumption": {
                    "status": "owner_consumed_typed_blocker",
                },
                "stage_closure_decision": {
                    "outcome": {"kind": "typed_blocker"}
                },
            },
            consumption_ledger_readback=readback,
        )
        is False
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
                "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
            },
        },
    ) is False


def test_consumption_route_handoff_rejects_cross_identity_carrier(
    tmp_path: Path,
) -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    workspace_root = tmp_path / "workspace"
    handoff_ref = _write_ledger(
        workspace_root=workspace_root,
        study_id=study_id,
        run_id="20260624Tcross_carrier_dm002",
        transaction_ref="paper-mission-transaction::dm002::canonical",
        fingerprint="fingerprint::dm002::canonical",
    ).parent / "opl_route_handoff.json"
    _patch_json(
        handoff_ref,
        {
            "opl_runtime_carrier": {
                "paper_mission_transaction_ref": (
                    "paper-mission-transaction::dm002::other"
                ),
                "stage_terminal_decision_ref": (
                    "paper-mission-transaction::dm002::other"
                    "#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    "paper-mission-transaction::dm002::other#opl_route_command"
                ),
                "work_unit_fingerprint": "fingerprint::dm002::other",
            }
        },
    )

    assert (
        latest_paper_mission_consumption_route_handoff(
            workspace_root=workspace_root,
            study_id=study_id,
        )
        is None
    )


def _write_ledger(
    *,
    workspace_root: Path,
    study_id: str,
    run_id: str,
    transaction_ref: str,
    fingerprint: str,
    external_delta_ref: str | None = None,
    paper_facing_delta_ref: str | None = None,
    milestone_kind: str | None = None,
    relative_candidate_ref: bool = False,
) -> Path:
    ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / run_id
        / study_id
    )
    ledger_root.mkdir(parents=True)
    transaction = _transaction(
        study_id=study_id,
        run_id=run_id,
        transaction_ref=transaction_ref,
        fingerprint=fingerprint,
    )
    carrier = paper_mission_opl_runtime_carrier(transaction)
    candidate_manifest = ledger_root / "package_manifest.json"
    if relative_candidate_ref:
        candidate_manifest = (
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_candidate_package"
            / run_id
            / study_id
            / "package_manifest.json"
        )
        candidate_manifest.parent.mkdir(parents=True, exist_ok=True)
    candidate_ref = candidate_manifest
    if relative_candidate_ref:
        candidate_ref = candidate_ref.relative_to(workspace_root)
    consume_record = {
        "surface_kind": "mas_paper_mission_candidate_consumption_record",
        "schema_version": 1,
        "study_id": study_id,
        "candidate_ref": str(candidate_ref),
        "candidate_id": f"candidate::{run_id}",
        "status": "accepted_candidate",
        "selected_outcome": "accepted_candidate",
        "route_handoff_status": "ready_for_opl_route_command",
        "paper_mission_transaction_ref": transaction_ref,
        "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "counts_as_stage_terminalizer_evidence": True,
        "counts_as_opl_route_handoff_evidence": True,
        "authority_materialized": False,
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": _authority_boundary(),
    }
    if paper_facing_delta_ref:
        consume_record["consume_result"] = {
            "status": "accepted",
            "outcome": "accepted_candidate",
            "authority_materialized": False,
            "paper_facing_delta_ref": paper_facing_delta_ref,
        }
    handoff = {
        "surface_kind": "mas_paper_mission_opl_route_handoff_record",
        "schema_version": 1,
        "study_id": study_id,
        "mission_id": transaction["mission_id"],
        "candidate_ref": str(candidate_ref),
        "handoff_status": "ready_for_opl_route_command",
        "next_owner": "mission_executor",
        "paper_mission_transaction_ref": transaction_ref,
        "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
        "stage_terminal_decision": transaction["stage_terminal_decision"],
        "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
        "opl_route_command": transaction["opl_route_command"],
        "opl_runtime_carrier": carrier,
        "route_command_kind": "route_back",
        "route_target": "paper-stage::gate-clearing",
        "transaction_materialized": True,
        "can_submit_to_opl_runtime": True,
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": _authority_boundary(),
    }
    (ledger_root / "consume_record.json").write_text(
        json.dumps(consume_record),
        encoding="utf-8",
    )
    candidate_manifest.write_text(
        json.dumps(
            {
                "milestone_kind": milestone_kind,
                "adopted_external_paper_delta_ref": external_delta_ref,
                "paper_facing_candidate_delta_ref": paper_facing_delta_ref,
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "consume_readback.json").write_text(
        json.dumps({"paper_mission_transaction": transaction}),
        encoding="utf-8",
    )
    (ledger_root / "stage_terminal_decision.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_stage_terminal_decision_packet",
                "study_id": study_id,
                "candidate_ref": str(candidate_ref),
                "paper_mission_transaction_ref": transaction_ref,
                "stage_terminal_decision_ref": f"{transaction_ref}#stage_terminal_decision",
                "transaction_state": transaction["stage_terminal_decision"]["status"],
                "stage_id": transaction["stage_id"],
                "stage_run_ref": transaction["stage_run_ref"],
                "stage_terminal_decision": transaction["stage_terminal_decision"],
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_command.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_opl_route_command_packet",
                "study_id": study_id,
                "candidate_ref": str(candidate_ref),
                "paper_mission_transaction_ref": transaction_ref,
                "opl_route_command_ref": f"{transaction_ref}#opl_route_command",
                "opl_route_command": transaction["opl_route_command"],
                "opl_runtime_carrier": carrier,
                **transaction["opl_route_command"],
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_handoff.json").write_text(
        json.dumps(handoff),
        encoding="utf-8",
    )
    return ledger_root / "consume_record.json"


def _transaction(
    *,
    study_id: str,
    run_id: str,
    transaction_ref: str,
    fingerprint: str,
) -> dict[str, object]:
    transaction = build_paper_mission_transaction(
        mission_id=f"paper-mission::{study_id}::{run_id}",
        study_id=study_id,
        stage_id="paper-stage::gate-clearing",
        stage_run_ref=f"opl-stage-run://{study_id}/{run_id}",
        terminal_decision={
            "decision_kind": "route_back",
            "status": "terminal_decision_recorded",
            "reason": "candidate needs a claim/evidence repair pass",
            "next_owner": "mission_executor",
            "target_stage_id": "paper-stage::gate-clearing",
            "repair_scope": "claim-evidence-repair",
        },
        artifact_delta_refs=[
            {
                "ref_id": f"artifact-delta::{run_id}",
                "ref_kind": "candidate_artifact_delta",
                "uri": f"mission://{study_id}/{run_id}/artifact-delta",
            }
        ],
        paper_audit_pack_refs={
            family: [
                {
                    "ref_id": f"{family}::{run_id}",
                    "ref_kind": family,
                    "uri": f"mission://{study_id}/{run_id}/{family}",
                }
            ]
            for family in AUDIT_FAMILIES
        },
        idempotency_basis=run_id,
    )
    transaction["transaction_id"] = transaction_ref
    transaction["opl_route_command"][
        "source_terminal_decision_ref"
    ] = f"{transaction_ref}#stage_terminal_decision"
    transaction["idempotency"]["transaction_fingerprint"] = fingerprint
    return transaction


def _patch_json(path: Path, updates: dict[str, object]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(payload.get(key), dict):
            payload[key].update(value)
        else:
            payload[key] = value
    path.write_text(json.dumps(payload), encoding="utf-8")


def _authority_boundary() -> dict[str, bool]:
    return {
        "writes_authority_surface": False,
        "writes_publication_eval": False,
        "writes_controller_decision": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_current_package": False,
        "can_write_paper_body": False,
        "can_write_runtime_queue": False,
        "can_write_opl_outbox": False,
        "can_write_opl_event": False,
        "can_write_opl_stage_run": False,
        "can_write_provider_attempt": False,
    }
