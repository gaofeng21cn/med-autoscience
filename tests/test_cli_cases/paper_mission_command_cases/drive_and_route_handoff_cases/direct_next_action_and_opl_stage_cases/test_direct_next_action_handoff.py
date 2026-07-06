from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from med_autoscience.cli_parts.paper_mission_command_parts import (
    opl_runtime_submission,
)
from med_autoscience.cli_parts.paper_mission_command_parts import (
    direct_next_action_handoff as direct_handoff,
)


def test_direct_next_action_transaction_uses_domain_transition_mission_identity() -> None:
    transaction = direct_handoff.build_direct_next_action_transaction(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback={
            "mission_id": (
                "paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "medical_prose_write_repair_publication_gate_replay::one-shot-migration"
            ),
        },
        next_action={
            "stage_id": "write",
            "owner": "write",
            "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
            ),
            "action_type": "request_opl_stage_attempt",
            "action_family": "paper.write.prose_repair",
        },
    )

    assert transaction["mission_id"] == (
        "paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "domain-transition::write::"
        "dm003-bounded-prose-repair-after-post-sync-reviewer-record"
    )
    assert transaction["transaction_id"].endswith(
        "::paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
        "domain-transition::write::"
        "dm003-bounded-prose-repair-after-post-sync-reviewer-record"
    )


def test_direct_next_action_transaction_rotates_idempotency_after_owner_consumed_route_checkpoint() -> None:
    next_action = {
        "stage_id": "write",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
    }
    base_readback = {"mission_id": "paper-mission::dm003::domain-transition"}
    owner_consumed_readback = {
        **base_readback,
        "current_opl_runtime_carrier_readback": {
            "owner_consumption_readback_ref": (
                "/tmp/receipt_owner_consumption.json"
            ),
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
                "route_checkpoint_evidence_ref": (
                    "/tmp/stage_attempt_closeout_packet.json"
                ),
            },
        },
    }

    initial = direct_handoff.build_direct_next_action_transaction(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback=base_readback,
        next_action=next_action,
    )
    successor = direct_handoff.build_direct_next_action_transaction(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback=owner_consumed_readback,
        next_action=next_action,
    )

    assert initial["transaction_id"] == successor["transaction_id"]
    assert initial["idempotency"]["idempotency_key"] != successor["idempotency"][
        "idempotency_key"
    ]
    successor_epoch = (
        "/tmp/receipt_owner_consumption.json::/tmp/stage_attempt_closeout_packet.json"
    )
    assert successor["idempotency"]["idempotency_key"].endswith(
        f"::successor::{direct_handoff._stable_sha256(successor_epoch)[:12]}"
    )


def test_direct_next_action_runtime_request_carries_owner_consumption_successor_delta() -> None:
    next_action = {
        "stage_id": "write",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "outcome_ref": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
    }
    no_epoch_handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root="/tmp/dm003"),
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback={"mission_id": "paper-mission::dm003::domain-transition"},
        next_action=next_action,
    )
    successor_handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root="/tmp/dm003"),
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback={
            "mission_id": "paper-mission::dm003::domain-transition",
            "current_opl_runtime_carrier_readback": {
                "owner_consumption_readback_ref": (
                    "/tmp/receipt_owner_consumption.json"
                ),
                "mas_receipt_consumption": {
                    "status": "owner_consumed_route_checkpoint",
                    "route_checkpoint_evidence_ref": (
                        "/tmp/stage_attempt_closeout_packet.json"
                    ),
                },
            },
        },
        next_action=next_action,
    )

    initial_request = (
        opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
            no_epoch_handoff
        )
    )
    successor_request = (
        opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
            successor_handoff
        )
    )

    assert initial_request is not None
    assert successor_request is not None
    assert initial_request["dedupe_key"] != successor_request["dedupe_key"]
    assert initial_request["payload"]["request_idempotency_key"] != successor_request[
        "payload"
    ]["request_idempotency_key"]
    assert successor_request["payload"]["owner_consumption_readback_ref"] == (
        "/tmp/receipt_owner_consumption.json"
    )
    assert successor_request["payload"]["advancing_delta_identity"][
        "owner_consumption_readback_ref"
    ] == "/tmp/receipt_owner_consumption.json"
    assert successor_request["payload"]["advancing_delta_identity"][
        "route_checkpoint_evidence_ref"
    ] == "/tmp/stage_attempt_closeout_packet.json"


def test_direct_next_action_uses_latest_consumed_receipt_when_current_carrier_is_stale() -> None:
    next_action = {
        "stage_id": "write",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "outcome_ref": (
            "domain-transition::route_back_same_line::"
            "medical_prose_write_repair::source::4e2a1295ce4c3eae"
        ),
    }
    handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root="/tmp/dm003"),
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        inspect_readback={
            "mission_id": "paper-mission::dm003::domain-transition",
            "current_opl_runtime_carrier_readback": {
                "mas_receipt_consumption": {
                    "status": "requires_mas_owner_consumption",
                    "route_checkpoint_evidence_ref": "/tmp/old-closeout.json",
                },
            },
            "receipt_owner_consumption_readback": {
                "status": "owner_consumption_applied",
                "source_ref": "/tmp/receipt_owner_consumption.json",
                "mas_receipt_consumption": {
                    "status": "owner_consumed_route_checkpoint",
                    "route_checkpoint_evidence_ref": "/tmp/new-closeout.json",
                },
            },
        },
        next_action=next_action,
    )
    request = opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
        handoff
    )

    assert request is not None
    assert handoff["owner_consumption_status"] == "owner_consumed_route_checkpoint"
    assert handoff["route_checkpoint_evidence_ref"] == "/tmp/new-closeout.json"
    assert request["payload"]["advancing_delta_identity"][
        "route_checkpoint_evidence_ref"
    ] == "/tmp/new-closeout.json"
    successor_epoch = "/tmp/receipt_owner_consumption.json::/tmp/new-closeout.json"
    assert request["payload"]["request_idempotency_key"].endswith(
        "::successor::"
        f"{direct_handoff._stable_sha256(successor_epoch)[:12]}::opl-request"
    )


def test_direct_next_action_runtime_request_carries_latest_task_intake_scope(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    task_intake_root = study_root / "artifacts" / "controller" / "task_intake"
    task_intake_root.mkdir(parents=True)
    task_intake_path = task_intake_root / "latest.json"
    task_intake_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "study-task::dm003::20260705T064542Z",
                "emitted_at": "2026-07-05T06:45:42+00:00",
                "study_id": study_id,
                "task_intake_kind": "reviewer_revision",
                "task_intent": (
                    "Revise DM003 through MAS canonical paper surfaces, including "
                    "Figure 4 count/% repair, medication-field-present Table 3, "
                    "Figure 1 cohort/support surfaces, Discussion literature dialogue, "
                    "abstract compression, renal-risk exploratory framing, and "
                    "supplementary retention."
                ),
                "constraints": [
                    "Do not change the main phenotype-atlas narrative.",
                    "Do not bypass MAS/OPL canonical owner routes.",
                ],
                "evidence_boundary": [
                    "Age/calendar-year/HbA1c-threshold sensitivity must route back if missing."
                ],
                "trusted_inputs": ["/tmp/reviewer-advice.txt"],
                "first_cycle_outputs": [
                    "new canonical manuscript and package",
                    "reviewer coverage audit",
                ],
                "revision_intake": {
                    "kind": "reviewer_revision",
                    "status": "active",
                    "checklist": [
                        "text_revisions",
                        "tables_figures",
                        "follow_up_evidence",
                    ],
                    "checklist_items": [
                        {
                            "id": "text_revisions",
                            "label": "text revisions",
                            "status": "pending",
                            "requirement": "Revise abstract and discussion.",
                        },
                        {
                            "id": "tables_figures",
                            "label": "tables/figures",
                            "status": "pending",
                            "requirement": "Repair Figure 1/Figure 4 and promote sensitivity Table 3.",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    next_action = {
        "stage_id": "write",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::medical_prose_write_repair"
        ),
        "action_type": "request_opl_stage_attempt",
        "action_family": "paper.write.prose_repair",
        "outcome_ref": (
            "domain-transition::route_back_same_line::medical_prose_write_repair"
        ),
    }
    plain_handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root=tmp_path / "plain-workspace"),
        study_id=study_id,
        inspect_readback={"mission_id": "paper-mission::dm003::domain-transition"},
        next_action=next_action,
    )

    handoff = direct_handoff.build_direct_next_action_handoff(
        profile=SimpleNamespace(workspace_root=workspace_root),
        study_id=study_id,
        inspect_readback={"mission_id": "paper-mission::dm003::domain-transition"},
        next_action=next_action,
    )
    plain_runtime_request = (
        opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
            plain_handoff
        )
    )
    runtime_request = opl_runtime_submission._opl_stage_route_runtime_request_from_handoff(
        handoff
    )

    assert plain_runtime_request is not None
    assert runtime_request is not None
    assert handoff["task_intake_kind"] == "reviewer_revision"
    assert handoff["task_intake_ref"]["artifact_path"] == str(task_intake_path)
    assert "Figure 4 count/% repair" in handoff["task_intake_summary"]["task_intent"]
    assert {
        "ref_id": "study_task_intake::latest",
        "ref_kind": "study_task_intake",
        "uri": str(task_intake_path),
    } in handoff["paper_mission_transaction"]["paper_audit_pack_refs"][
        "review_ledger_delta"
    ]
    assert runtime_request["payload"]["task_intake_kind"] == "reviewer_revision"
    assert runtime_request["payload"]["task_intake_ref"]["artifact_path"] == str(
        task_intake_path
    )
    assert "Figure 4 count/% repair" in runtime_request["payload"][
        "task_intake_summary"
    ]["task_intent"]
    assert "Figure 4 count/% repair" in runtime_request["payload"]["user_stage_log"][
        "stage_goal"
    ]
    assert str(task_intake_path) in runtime_request["payload"]["user_stage_log"][
        "evidence_refs"
    ]
    assert "text_revisions" in runtime_request["payload"]["user_stage_log"][
        "task_scope"
    ]["revision_checklist"]
    assert "tables_figures" in runtime_request["payload"]["user_stage_log"][
        "task_scope"
    ]["revision_checklist"]
    assert plain_runtime_request["dedupe_key"] != runtime_request["dedupe_key"]
