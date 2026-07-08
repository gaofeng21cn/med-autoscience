from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from med_autoscience.cli import paper_mission_commands as commands
from med_autoscience.cli.paper_mission_commands.drive_readback import (
    build_paper_mission_drive_readback,
    _drive_owner_action_stop_readback,
    _drive_should_submit_direct_next_action,
)
from med_autoscience.cli.paper_mission_commands import (
    opl_runtime_submission,
)
from med_autoscience.cli.paper_mission_commands import (
    materialized_mission_readback as materialized_readback,
)
from med_autoscience.cli.paper_mission_commands import (
    direct_next_action_handoff as direct_handoff,
)
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


def test_consumption_ledger_inspect_prefers_domain_transition_after_route_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review"
        ),
    }
    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: {
            "status": "owner_consumption_applied",
            "stage_closure_decision": {
                "decision_ref": f"{transaction['transaction_id']}#stage_closure_decision",
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "next_owner": "MedAutoScience",
                    "can_submit": False,
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
            "next_action": next_action,
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
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert payload["next_action"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert payload["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )


def test_consumption_ledger_inspect_prefers_domain_transition_after_owner_consumed_route_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-write",
        "study_id": study_id,
        "stage_id": "write",
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
        ),
    }
    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: {
            "status": "owner_consumption_applied",
            "stage_closure_decision": {
                "authority_materialized": True,
                "decision_ref": f"{transaction['transaction_id']}#stage_closure_decision",
                "stage_id": "write",
                "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                "opl_closeout": {
                    "status": "opl_runtime_terminal_readback_observed",
                    "stage_attempt_id": "sat-current-write",
                    "work_unit_id": (
                        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
                    ),
                },
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "next_owner": "MedAutoScience",
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-current-write/stage_attempt_closeout_packet.json"
                    ),
                    "can_submit": False,
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "next_legal_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-current-write",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current-write/stage_attempt_closeout_packet.json"
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
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                "lane": "write",
            },
            "next_action": next_action,
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
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"]["action_family"] == "paper.write.prose_repair"
    assert payload["next_action"]["action_type"] == "request_opl_stage_attempt"
    assert payload["stage_closure_decision"]["work_unit_id"] == (
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )


def test_consumption_ledger_inspect_ignores_stale_receipt_when_stage_closure_attempt_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    stale_receipt = {
        "status": "owner_consumption_applied",
        "stage_closure_decision": {
            "decision_ref": f"{transaction['transaction_id']}#stage_closure_decision",
            "stage_id": "write",
            "work_unit_id": "medical_prose_write_repair",
            "opl_closeout": {"stage_attempt_id": "sat-stale"},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "next_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
            },
        },
        "mas_receipt_consumption": {
            "status": "owner_consumed_route_checkpoint",
        },
    }
    current_stage_closure = {
        "surface_kind": "mas_stage_closure_decision",
        "source_surface_kind": "paper_mission_stage_closure_ledger",
        "stage_id": "write",
        "work_unit_id": "medical_prose_write_repair",
        "paper_mission_transaction_ref": (
            "ops/medautoscience/paper_mission_stage_attempts/"
            "sat-current/stage_attempt_closeout_packet.json"
        ),
        "opl_closeout": {"stage_attempt_id": "sat-current"},
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
            "next_action": (
                "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
            ),
        },
    }
    stage_selector_calls = []

    def _current_stage_closure(**_: object) -> dict[str, object]:
        stage_selector_calls.append(True)
        return current_stage_closure

    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: stale_receipt,
    )
    monkeypatch.setattr(
        commands,
        "_latest_current_stage_closure_for_consumption",
        _current_stage_closure,
    )
    monkeypatch.setattr(
        commands.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {"study_id": study_id},
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
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert stage_selector_calls
    assert "receipt_owner_consumption_readback" not in payload
    assert payload["stage_closure_decision"]["opl_closeout"]["stage_attempt_id"] == (
        "sat-current"
    )


def test_consumption_ledger_inspect_prefers_domain_transition_after_consumed_route_checkpoint_when_work_unit_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-write",
        "study_id": study_id,
        "stage_id": "write",
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
        ),
    }
    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: {
            "status": "owner_consumption_applied",
            "stage_closure_decision": {
                "authority_materialized": True,
                "decision_ref": f"{transaction['transaction_id']}#stage_closure_decision",
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "opl_closeout": {
                    "status": "opl_runtime_terminal_readback_observed",
                    "stage_attempt_id": "sat-current-review",
                    "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                },
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "next_owner": "MedAutoScience",
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-current-review/stage_attempt_closeout_packet.json"
                    ),
                    "can_submit": False,
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "next_legal_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-current-review",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current-review/stage_attempt_closeout_packet.json"
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
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                "lane": "write",
            },
            "next_action": next_action,
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
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"]["action_family"] == "paper.write.prose_repair"
    assert payload["stage_closure_decision"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )


def test_consumption_ledger_inspect_prefers_same_stage_domain_transition_after_owner_consumed_route_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-write",
        "study_id": study_id,
        "stage_id": "write",
        "action_family": "paper.write.prose_repair",
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::medical_prose_write_repair"
        ),
    }
    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: {
            "status": "owner_consumption_applied",
            "stage_closure_decision": {
                "authority_materialized": True,
                "decision_ref": f"{transaction['transaction_id']}#stage_closure_decision",
                "stage_id": "write",
                "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                "opl_closeout": {
                    "status": "opl_runtime_terminal_readback_observed",
                    "stage_attempt_id": "sat-current-write",
                    "work_unit_id": (
                        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
                    ),
                },
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": (
                        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                    ),
                    "next_owner": "MedAutoScience",
                    "route_checkpoint_evidence_ref": (
                        "ops/medautoscience/paper_mission_stage_attempts/"
                        "sat-current-write/stage_attempt_closeout_packet.json"
                    ),
                    "can_submit": False,
                },
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "owner_consumed_route_checkpoint",
                "next_legal_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "receipt_evidence_ref": "opl://stage-attempts/sat-current-write",
                "route_checkpoint_evidence_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-current-write/stage_attempt_closeout_packet.json"
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
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "controller_action": "request_opl_stage_attempt",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
            },
            "next_action": next_action,
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
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["next_action"]["action_family"] == "paper.write.prose_repair"
    assert payload["next_action"]["action_type"] == "request_opl_stage_attempt"
    assert payload["next_action"]["work_unit_id"] == "medical_prose_write_repair"


def test_consumption_ledger_inspect_attaches_study_progress_paper_mission_run_when_materialized_run_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    workspace_root = tmp_path / "workspace"
    studies_root = workspace_root / "studies"
    study_root = studies_root / study_id
    study_root.mkdir(parents=True)
    profile = SimpleNamespace(
        name="DM-CVD",
        workspace_root=workspace_root,
        studies_root=studies_root,
    )
    mission_id = f"paper-mission::{study_id}::submission-milestone"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )

    monkeypatch.setattr(
        commands,
        "_study_progress_paper_mission_overlay",
        lambda **_: {
            "paper_mission_run": {
                "mission_id": mission_id,
                "mission_state": "consumed",
                "current_objective": {
                    "objective": "review_current_paper_delta",
                    "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                },
            },
            "current_objective": {
                "objective": "review_current_paper_delta",
                "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            },
            "next_owner_or_human_decision": {
                "kind": "owner_or_route",
                "next_owner": "write",
                "route_command": "resume_stage",
                "route_target": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            },
            "current_stage": "queued",
        },
    )
    monkeypatch.setattr(
        commands,
        "_latest_receipt_owner_consumption_readback",
        lambda **_: None,
    )
    monkeypatch.setattr(
        commands,
        "_consumption_ledger_route_back_projection",
        lambda **_: None,
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
        },
        study_root=study_root,
        enable_opl_live_probe=False,
        opl_bin=tmp_path / "missing-opl",
    )

    assert payload["paper_mission_run"]["mission_id"] == mission_id
    assert payload["paper_mission_run"]["mission_state"] == "consumed"
    assert payload["current_objective"]["objective"] == "review_current_paper_delta"
    assert payload["next_owner_or_human_decision"]["next_owner"] == "write"
    assert payload["current_stage"] == "queued"

