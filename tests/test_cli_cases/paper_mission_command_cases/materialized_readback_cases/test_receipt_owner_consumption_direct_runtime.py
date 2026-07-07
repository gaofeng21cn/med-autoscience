from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_direct_stage_attempt_handoff_reads_owner_consumption_from_top_level_receipt() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    profile = SimpleNamespace(workspace_root="/tmp/workspace")
    readback = materialized_readback._domain_transition_direct_next_action_runtime_readback(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        study_root=Path("/tmp/study"),
        inspect_readback={
            "mission_id": (
                "paper-mission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "paper_mission_import::one-shot-migration"
            ),
            "receipt_owner_consumption_readback": {
                "source_ref": "/tmp/receipt_owner_consumption.json",
                "mas_receipt_consumption": {
                    "status": "owner_consumed_route_checkpoint",
                    "route_checkpoint_evidence_ref": "/tmp/sat-current-closeout.json",
                },
            },
        },
        next_action={
            "surface_kind": "mas_next_action_envelope",
            "schema_version": 1,
            "action_id": "next-action-dm003",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_id": "write",
            "outcome_ref": (
                "domain-transition::route_back_same_line::"
                "medical_prose_write_repair::source::fresh"
            ),
            "action_family": "paper.write.prose_repair",
            "action_kind": "paper_write",
            "action_type": "request_opl_stage_attempt",
            "owner": "write",
            "executor_target": "mas_owner_callable",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "medical_prose_write_repair::source::fresh"
            ),
        },
        canonical_next_action_source="domain_transition.next_action",
        enable_opl_live_probe=False,
        opl_bin=Path("/tmp/missing-opl"),
    )

    assert readback["opl_route_handoff"]["owner_consumption_readback_ref"] == (
        "/tmp/receipt_owner_consumption.json"
    )
    assert readback["opl_route_handoff"]["route_checkpoint_evidence_ref"] == (
        "/tmp/sat-current-closeout.json"
    )


def test_direct_terminal_closeout_can_override_next_action_source() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )
    refreshed_stage_closure = {
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
        }
    }
    refreshed_next_action = {
        "action_family": "paper.stage_closure.owner_consumption",
        "action_type": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
    }

    for module in (materialized_readback, paper_mission_commands):
        original_terminalize = module._terminalize_stage_closure_from_readback
        original_next_action = module._next_action_for_stage_closure_decision
        try:
            module._terminalize_stage_closure_from_readback = (
                lambda *_args, **_kwargs: refreshed_stage_closure
            )
            module._next_action_for_stage_closure_decision = (
                lambda **_kwargs: refreshed_next_action
            )
            stage_closure_decision, next_action_override, canonical_source = (
                module._override_next_action_from_direct_terminal_closeout(
                    direct_next_action_runtime={
                        "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
                        "opl_runtime_carrier_readback": {
                            "mas_receipt_consumption": {
                                "status": "requires_mas_owner_consumption"
                            }
                        },
                    },
                    stage_closure_decision={"outcome": {"kind": "owner_receipt"}},
                    transaction_readback={"paper_mission_transaction": {"study_id": "003"}},
                    typed_blocker_resolution_readback=None,
                    next_action_override={"action_family": "paper.write.prose_repair"},
                    canonical_next_action_source="domain_transition.next_action",
                )
            )
        finally:
            module._terminalize_stage_closure_from_readback = original_terminalize
            module._next_action_for_stage_closure_decision = original_next_action

        assert stage_closure_decision == refreshed_stage_closure
        assert next_action_override == refreshed_next_action
        assert canonical_source == "stage_closure.next_action"


def test_direct_terminal_closeout_does_not_override_after_owner_consumed_route_checkpoint() -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    paper_mission_commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    for module in (materialized_readback, paper_mission_commands):
        stage_closure_decision, next_action_override, canonical_source = (
            module._override_next_action_from_direct_terminal_closeout(
                direct_next_action_runtime={
                    "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
                    "opl_route_handoff": {
                        "owner_consumption_readback_ref": "/tmp/receipt_owner_consumption.json"
                    },
                    "opl_runtime_carrier_readback": {
                        "mas_receipt_consumption": {
                            "status": "requires_mas_owner_consumption"
                        }
                    },
                },
                stage_closure_decision={"outcome": {"kind": "owner_receipt"}},
                transaction_readback={"paper_mission_transaction": {"study_id": "003"}},
                typed_blocker_resolution_readback=None,
                next_action_override={"action_family": "paper.write.prose_repair"},
                canonical_next_action_source="domain_transition.next_action",
                receipt_owner_consumption_readback={
                    "status": "owner_consumption_applied",
                    "source_ref": "/tmp/receipt_owner_consumption.json",
                    "mas_receipt_consumption": {
                        "status": "owner_consumed_route_checkpoint"
                    },
                },
            )
        )

        assert stage_closure_decision == {"outcome": {"kind": "owner_receipt"}}
        assert next_action_override == {"action_family": "paper.write.prose_repair"}
        assert canonical_source == "domain_transition.next_action"


def test_thin_legacy_stage_closure_keeps_owner_consumption_visible(tmp_path: Path) -> None:
    materialized_readback = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback"
    )
    receipt_ref = tmp_path / "receipt_owner_consumption.json"
    stage_ref = tmp_path / "stage_closure_decision.json"
    receipt_ref.write_text("{}", encoding="utf-8")
    stage_ref.write_text("{}", encoding="utf-8")

    assert not materialized_readback._receipt_superseded_by_stage_closure(
        receipt_owner_consumption_readback={
            "status": "owner_consumption_applied",
            "source_ref": str(receipt_ref),
            "mas_receipt_consumption": {"status": "owner_consumed_route_checkpoint"},
            "stage_closure_decision": {
                "stage_id": "write",
                "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
                "route_checkpoint_evidence_ref": "/tmp/sat-current-closeout.json",
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
            "work_unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
            "opl_closeout": {"stage_attempt_id": "sat-legacy-thin"},
            "outcome": {
                "kind": "next_stage_transition",
                "transition_kind": "route_back_candidate_checkpoint",
            },
        },
    )


def test_paper_mission_inspect_projects_receipt_owner_consumption_without_materialized_mission(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::external-sci-registry-review-v3"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=transaction,
    )

    consume_exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_consumption_ledger"
                / "sat-current"
            ),
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    assert consume_exit_code == 0
    consume_payload = json.loads(capsys.readouterr().out)
    readback_file = tmp_path / "receipt-source-readback.json"
    readback_file.write_text(
        json.dumps(
            {
                **consume_payload,
                "surface_kind": "paper_mission_materialized_readback",
                "mission_state": "consumed",
                "stage_closure_decision": {
                    "decision_ref": f"mas://paper-mission/{study_id}/receipt-owner-consumption",
                    "stage_id": "finalize",
                    "work_unit_id": "provider_hosted_guarded_apply",
                    "outcome": {
                        "kind": "next_stage_transition",
                        "transition_kind": "route_back_candidate_checkpoint",
                        "can_submit": False,
                    },
                },
                "stage_closure_outcome": "next_stage_transition",
                "current_package": {
                    "status": "stale",
                    "package_kind": "current_package",
                    "can_submit": False,
                    "known_blockers": ["prose_revision_required"],
                },
                "opl_runtime_carrier_readback": {
                    "runtime_readback_status": "terminal_closeout_observed",
                    "receipt_evidence": {
                        "receipt_kind": "opl_transition_receipt",
                        "receipt_ref": "opl://stage-attempts/sat-obesity/receipt",
                        "impact_receipt_kind": "mas_impact_receipt",
                        "impact_receipt_ref": "opl://stage-attempts/sat-obesity/mas-impact",
                        "can_claim_paper_progress": False,
                    },
                    "opl_transition_receipt": {
                        "surface_kind": "opl_transition_receipt",
                        "receipt_status": "terminal_closeout_observed",
                        "role": "transport_receipt_only",
                        "task_id": "frt-obesity",
                        "task_status": "completed",
                        "stage_attempt_id": "sat-obesity",
                        "stage_attempt_ref": "opl://stage-attempts/sat-obesity",
                        "closeout_receipt_status": "accepted_typed_closeout",
                        "can_claim_paper_progress": False,
                    },
                    "mas_receipt_consumption": {
                        "surface_kind": "mas_receipt_consumption_projection",
                        "status": "requires_mas_owner_consumption",
                        "next_legal_action": "record_typed_blocker",
                        "forbidden_next_action": "synonymous_route_back_redrive",
                        "durable_stop_allowed": False,
                        "can_claim_paper_progress": False,
                        "can_claim_publication_ready": False,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    receipt_exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--output-root",
            str(
                workspace_root
                / "ops"
                / "medautoscience"
                / "paper_mission_receipt_owner_consumption"
            ),
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    assert receipt_exit_code == 0
    receipt_payload = json.loads(capsys.readouterr().out)
    assert receipt_payload["status"] == "owner_consumption_applied"

    inspect_exit_code = cli.main(
        [
            "paper-mission",
            "inspect",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert inspect_exit_code == 0
    assert payload["surface_kind"] == "paper_mission_consumption_ledger_transaction_readback"
    assert payload["receipt_owner_consumption_readback"]["status"] == (
        "owner_consumption_applied"
    )
    assert payload["mas_receipt_consumption"]["status"] == (
        "owner_consumed_route_checkpoint"
    )
    assert payload["consume_candidate_status"] == "route_back"
    assert payload["mission_state"] == "route_back"
    assert payload["stage_closure_outcome"] == "next_stage_transition"
    assert payload["next_action"]["action_family"] != (
        "paper.stage_closure.owner_consumption"
    )
