from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_command_helpers import (
    DM_CANARY_FIXTURE_ROOT,
    FORBIDDEN_AUTHORITY_RELATIVE_PATHS,
    _assert_forbidden_authority_untouched,
    _paper_mission_forbidden_write_guard,
    _paper_mission_transaction_payload,
    _write_candidate_manifest,
    _write_matching_domain_gate_closeout,
    _write_paper_source_fixture,
    _write_profile_with_study,
    _write_submission_milestone_package,
)


def test_consumption_ledger_inspect_ignores_stale_current_handoff_after_owner_consumed_route_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "workspace" / "studies" / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM",
        workspace_root=tmp_path / "workspace",
        studies_root=tmp_path / "workspace" / "studies",
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone::current-write"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    work_unit_fingerprint = (
        "domain-transition::route_back_same_line::"
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )
    stage_terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": "MAS canonical next action requests the current write repair work unit.",
        "next_owner": "write",
        "next_work_unit": work_unit_id,
        "recommended_next_action": "request_opl_stage_attempt",
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_next_action_ref": work_unit_fingerprint,
    }
    opl_route_command = {
        "command_kind": "resume_stage",
        "target": work_unit_id,
        "reason": "MAS canonical next action requests the current write repair work unit.",
        "runtime_owner": "one-person-lab",
    }
    opl_runtime_carrier = {
        "surface_kind": "mas_domain_progress_transition_request",
        "study_id": study_id,
        "stage_id": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "target_runtime_owner": "one-person-lab",
        "route_identity_key": "route::dm003-current-write",
        "attempt_idempotency_key": "attempt::dm003-current-write",
        "request_idempotency_key": "request::dm003-current-write",
    }

    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: {
            "source_ref": (
                "ops/medautoscience/paper_mission_receipt_owner_consumption/"
                f"{study_id}/receipt_owner_consumption.json"
            ),
            "status": "owner_consumption_applied",
            "stage_closure_decision": {
                "decision_ref": f"{mission_id}#stage-closure",
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "next_owner": "MedAutoScience",
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-review/stage_attempt_closeout_packet.json"
                    ),
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "next_legal_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-review",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-review/stage_attempt_closeout_packet.json"
                ),
                "can_claim_paper_progress": False,
            },
        },
    )
    monkeypatch.setattr(
        commands.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
            },
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "schema_version": 1,
                "action_id": "next-action-ai-reviewer",
                "study_id": study_id,
                "stage_id": "review",
                "action_family": "paper.review.ai_reviewer",
                "action_kind": "owner_review",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "executor_target": "mas_owner_callable",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "work_unit_fingerprint": "domain-transition::ai-reviewer",
            },
        },
    )

    payload = commands._consumption_ledger_inspect_readback(
        profile=profile,
        profile_ref=tmp_path / "dm.local.toml",
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        consumption_readback={
            "surface_kind": "paper_mission_consumption_readback",
            "mission_id": mission_id,
            "study_id": study_id,
            "selected_outcome": "accepted_submission_milestone_candidate",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": transaction,
            "stage_terminal_decision": stage_terminal_decision,
            "opl_route_command": opl_route_command,
            "opl_runtime_carrier": opl_runtime_carrier,
            "opl_route_handoff": {
                "handoff_status": "ready_for_opl_route_command",
                "next_owner": "write",
                "can_submit_to_opl_runtime": True,
                "stage_terminal_decision": stage_terminal_decision,
                "opl_route_command": opl_route_command,
                "opl_runtime_carrier": opl_runtime_carrier,
            },
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"]["action_family"] == "paper.review.ai_reviewer"
    assert payload["next_action"]["owner"] == "ai_reviewer"
    assert payload["next_action"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert payload["domain_transition_direct_stage_attempt"]["opl_route_handoff"][
        "work_unit_id"
    ] == "ai_reviewer_medical_prose_quality_review"
    assert payload["domain_transition_direct_stage_attempt"]["opl_route_handoff"][
        "owner_consumption_readback_ref"
    ] == (
        "ops/medautoscience/paper_mission_receipt_owner_consumption/"
        f"{study_id}/receipt_owner_consumption.json"
    )
    assert payload["domain_transition_direct_stage_attempt"]["opl_route_handoff"][
        "route_checkpoint_evidence_ref"
    ] == (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-review/stage_attempt_closeout_packet.json"
    )


def test_stage_closure_terminalizer_supersedes_legacy_route_back_checkpoint() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )

    decision = commands._terminalize_stage_closure_from_readback(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "mission_id": "mission-002",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": {
                "transaction_id": "txn-002",
                "stage_id": "submission_milestone_candidate",
            },
            "stage_terminal_decision": {
                "status": "accepted_submission_milestone_candidate",
                "reason": "paper_mission_stage_route_domain_gate_pending",
            },
            "stage_closure_decision": {
                "decision_signature": "legacy-signature-before-blocker-normalization",
                "outcome": {"transition_kind": "route_back_candidate_checkpoint"},
                "observability_gaps": [
                    "duration_ms_missing",
                    "token_usage_missing",
                    "cost_usd_missing",
                ],
            },
        }
    )

    assert decision["repeated_without_semantic_delta"] is True
    assert decision["outcome"]["kind"] == "typed_blocker"
    assert (
        decision["outcome"]["blocker_type"]
        == "route_back_checkpoint_without_semantic_delta"
    )
    assert "observability_gaps" not in decision
    assert decision["opl_closeout"]["duration"]["missing_duration_reason"] == (
        "stage_closeout_status_missing::duration_not_recorded"
    )
    assert decision["opl_closeout"]["token_usage"]["missing_token_usage_reason"] == (
        "stage_closeout_status_missing::token_usage_not_recorded"
    )
    assert decision["opl_closeout"]["cost"]["missing_cost_reason"] == (
        "stage_closeout_status_missing::cost_not_recorded"
    )


def test_durable_stop_guard_rejects_non_terminal_next_stage_transitions() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )

    for transition_kind in (
        "current_package_mirror_sync",
        "route_back_candidate_checkpoint",
        "bounded_quality_repair_iteration",
    ):
        guard = commands._durable_mission_stop_guard(
            consume_candidate_status="stage_closure_observed",
            stage_closure_decision={
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": transition_kind,
                }
            },
        )

        assert guard["durable_stop_allowed"] is False

    degraded_guard = commands._durable_mission_stop_guard(
        consume_candidate_status="stage_closure_observed",
        stage_closure_decision={
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "degraded_handoff",
            }
        },
    )
    assert degraded_guard["durable_stop_allowed"] is True
