from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_commands_cases.stage_closure_terminalizer import (
    _write_consumption_ledger,
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


def test_terminalize_stage_prefers_domain_transition_direct_closeout_over_old_consumption(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    stage_closure_ledger = importlib.import_module(
        "med_autoscience.paper_mission_stage_closure_ledger"
    )
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id

    old_transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::followthrough-02",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    old_ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "followthrough-02"
        / study_id
    )
    _write_consumption_ledger(
        ledger_root=old_ledger_root,
        study_id=study_id,
        candidate_ref="/tmp/followthrough-02/package_manifest.json",
        transaction=old_transaction,
    )
    (old_ledger_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": old_transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-old-followthrough",
                "paper_mission_transaction_ref": old_transaction["transaction_id"],
                "stage_packet_ref": (
                    old_transaction["transaction_id"] + "#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    old_transaction["transaction_id"] + "#opl_route_command"
                ),
                "work_unit_id": old_transaction["stage_id"],
                "work_unit_fingerprint": old_transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )
    stage_closure_ledger.write_paper_mission_stage_closure_decision(
        output_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_closure"
            / "old-followthrough"
        ),
        study_id=study_id,
        decision={
            "stage_id": old_transaction["stage_id"],
            "work_unit_id": old_transaction["stage_id"],
            "work_unit_fingerprint": old_transaction["idempotency"][
                "transaction_fingerprint"
            ],
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
                "next_owner": "MedAutoScience",
                "next_action": (
                    "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
                ),
                "authority_materialized": False,
            },
            "known_blockers": ["paper_mission_stage_route_domain_gate_pending"],
        },
        source_readback={
            "study_id": study_id,
            "source_ref": str(old_ledger_root / "consume_record.json"),
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "transaction_state": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": old_transaction,
        },
        source="test",
        forbidden_authority_writes=(),
        forbidden_authority_claims=(),
    )
    stale_receipt_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / "old-route-checkpoint"
        / study_id
    )
    stale_receipt_root.mkdir(parents=True)
    (stale_receipt_root / "receipt_owner_consumption.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_receipt_owner_consumption",
                "study_id": study_id,
                "status": "owner_consumption_applied",
                "authority_materialized": True,
                "stage_closure_decision": {
                    "surface_kind": "mas_stage_closure_decision",
                    "stage_id": old_transaction["stage_id"],
                    "work_unit_id": old_transaction["stage_id"],
                    "outcome": {
                        "kind": "next_stage_transition",
                        "transition_kind": "route_back_candidate_checkpoint",
                    },
                    "counts_as_typed_blocker": False,
                    "authority_boundary": {"writes_owner_receipt": False},
                },
            }
        ),
        encoding="utf-8",
    )

    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260704Tdomain-transition"
        / study_id
    )
    mission_root.mkdir(parents=True)
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": f"paper-mission::{study_id}::domain-transition",
                "study_id": study_id,
                "objective": "Current domain transition should drive AI reviewer.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "consume_result": {"status": "accepted"},
                "paper_mission_transaction": old_transaction,
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
            }
        ),
        encoding="utf-8",
    )

    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
    }

    monkeypatch.setattr(
        materialized_readback.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {"decision_type": "ai_reviewer_re_eval", "next_action": next_action},
    )
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-ai-reviewer"
        / study_id
    )
    closeout_root.mkdir(parents=True)
    inspect_projection = materialized_readback.build_materialized_mission_readback_if_available(
        profile=SimpleNamespace(
            name="Obesity",
            workspace_root=workspace_root,
            studies_root=workspace_root / "studies",
            default_publication_profile="general_medical_journal",
        ),
        profile_ref=profile_path,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source="test",
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    assert inspect_projection is not None
    direct_projection = inspect_projection["domain_transition_direct_stage_attempt"]
    carrier = direct_projection["opl_runtime_carrier"]
    (closeout_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": "review",
                "stage_attempt_id": "sat-ai-reviewer",
                "paper_mission_transaction_ref": carrier[
                    "paper_mission_transaction_ref"
                ],
                "stage_packet_ref": carrier["stage_terminal_decision_ref"],
                "opl_route_command_ref": carrier["opl_route_command_ref"],
                "route_identity_key": carrier["route_identity_key"],
                "work_unit_id": carrier["work_unit_id"],
                "work_unit_fingerprint": carrier["work_unit_fingerprint"],
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "closeout_refs": [
                    str(study_root / "artifacts/publication_eval/latest.json")
                ],
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )
    inspect_projection = materialized_readback.build_materialized_mission_readback_if_available(
        profile=SimpleNamespace(
            name="Obesity",
            workspace_root=workspace_root,
            studies_root=workspace_root / "studies",
            default_publication_profile="general_medical_journal",
        ),
        profile_ref=profile_path,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source="test",
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    assert inspect_projection is not None
    direct_projection = inspect_projection["domain_transition_direct_stage_attempt"]
    assert direct_projection["opl_runtime_readback_status"] == (
        "opl_runtime_terminal_readback_observed"
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--dry-run",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["source_readback_summary"]["surface_kind"] == (
        "paper_mission_domain_transition_direct_stage_attempt_readback"
    )
    assert payload["stage_closure_decision"]["stage_id"] == "review"
    assert payload["stage_closure_decision"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["stage_closure_decision"]["outcome"]["kind"] != "typed_blocker"
    assert "not_applicable_domain_transition_direct" not in payload[
        "stage_closure_decision"
    ]["known_blockers"]
    assert "domain_transition_direct_stage_attempt" not in payload[
        "stage_closure_decision"
    ]["known_blockers"]
    assert payload["stage_closure_decision"]["opl_closeout"][
        "stage_attempt_id"
    ] == "sat-ai-reviewer"

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["stage_closure_decision"]["stage_id"] == "review"

    inspect_projection = materialized_readback.build_materialized_mission_readback_if_available(
        profile=SimpleNamespace(
            name="Obesity",
            workspace_root=workspace_root,
            studies_root=workspace_root / "studies",
            default_publication_profile="general_medical_journal",
        ),
        profile_ref=profile_path,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source="test",
        enable_opl_live_probe=True,
        opl_bin=None,
    )

    assert inspect_projection is not None
    assert inspect_projection["paper_mission_stage_closure_ledger_readback"][
        "stage_id"
    ] == "review"
    assert inspect_projection["stage_closure_decision"]["stage_id"] == "review"
    assert inspect_projection["stage_closure_decision"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert inspect_projection["stage_closure_decision"]["outcome"][
        "transition_kind"
    ] == "current_package_mirror_sync"
    assert inspect_projection["canonical_next_action_source"] == (
        "stage_closure.next_action"
    )
    assert inspect_projection["next_action"]["action_family"] == "paper.delivery.sync"

def test_terminalize_stage_prefers_domain_transition_direct_closeout_without_materialized_mission(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    materialized_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.materialized_mission_readback"
    )
    direct_handoff = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands.direct_next_action_handoff"
    )
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True, exist_ok=True)

    old_transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::followthrough-02",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    old_ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "followthrough-02"
        / study_id
    )
    _write_consumption_ledger(
        ledger_root=old_ledger_root,
        study_id=study_id,
        candidate_ref="/tmp/followthrough-02/package_manifest.json",
        transaction=old_transaction,
    )
    (old_ledger_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": old_transaction["opl_route_command"]["target"],
                "stage_attempt_id": "sat-old-followthrough",
                "paper_mission_transaction_ref": old_transaction["transaction_id"],
                "stage_packet_ref": (
                    old_transaction["transaction_id"] + "#stage_terminal_decision"
                ),
                "opl_route_command_ref": (
                    old_transaction["transaction_id"] + "#opl_route_command"
                ),
                "work_unit_id": old_transaction["stage_id"],
                "work_unit_fingerprint": old_transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )

    next_action = {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "action_id": "next-action-ai-reviewer",
        "study_id": study_id,
        "stage_id": "review",
        "outcome_ref": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
        "action_family": "paper.review.ai_reviewer",
        "action_kind": "owner_review",
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "executor_target": "mas_owner_callable",
        "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "ai_reviewer_medical_prose_quality_review::source::fresh"
        ),
    }
    monkeypatch.setattr(
        materialized_readback.study_domain_transition_table,
        "project_domain_transition",
        lambda **_: {"decision_type": "ai_reviewer_re_eval", "next_action": next_action},
    )

    profile = SimpleNamespace(
        name="Obesity",
        workspace_root=workspace_root,
        studies_root=workspace_root / "studies",
        default_publication_profile="general_medical_journal",
    )
    handoff = direct_handoff.build_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback={
            "mission_id": old_transaction["mission_id"],
            "study_id": study_id,
        },
        next_action=next_action,
    )
    carrier = handoff["opl_runtime_carrier"]
    closeout_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-ai-reviewer"
        / study_id
    )
    closeout_root.mkdir(parents=True)
    (closeout_root / "stage_attempt_closeout_packet.json").write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "status": "completed",
                "study_id": study_id,
                "stage_id": "review",
                "stage_attempt_id": "sat-ai-reviewer",
                "paper_mission_transaction_ref": carrier[
                    "paper_mission_transaction_ref"
                ],
                "stage_packet_ref": carrier["stage_terminal_decision_ref"],
                "opl_route_command_ref": carrier["opl_route_command_ref"],
                "route_identity_key": carrier["route_identity_key"],
                "work_unit_id": carrier["work_unit_id"],
                "work_unit_fingerprint": carrier["work_unit_fingerprint"],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "authority_boundary": {"record_only_surface": True},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "terminalize-stage",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--dry-run",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["source_readback_summary"]["surface_kind"] == (
        "paper_mission_domain_transition_direct_stage_attempt_readback"
    )
    assert payload["stage_closure_decision"]["stage_id"] == "review"
    assert payload["stage_closure_decision"]["opl_closeout"][
        "stage_attempt_id"
    ] == "sat-ai-reviewer"

