from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study


def test_terminalize_stage_uses_explicit_stage_packet_over_stale_consumption(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    stage_attempt_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-review"
    )
    stage_attempt_root.mkdir(parents=True)
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-review/route_back_evidence_packet.json"
    )
    (workspace_root / route_back_ref).write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_stage_attempt_route_back_evidence_packet",
                "study_id": study_id,
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "owner_answer_kind": "route_back_evidence_ref",
                "owner_answer_ref": (
                    "ops/medautoscience/paper_mission_stage_attempts/"
                    "sat-review/attempt_candidate_manifest.json"
                ),
            }
        ),
        encoding="utf-8",
    )
    stage_packet = stage_attempt_root / "stage_attempt_closeout_packet.json"
    stage_packet.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_stage_attempt_closeout_packet",
                "study_id": study_id,
                "stage_id": "review",
                "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                "stage_attempt_id": "sat-review",
                "status": "completed",
                "route_back_evidence_ref": route_back_ref,
                "provider_attempt_ref": "opl://stage-attempts/sat-review",
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
            "--stage-packet",
            str(stage_packet),
            "--output-root",
            str(workspace_root / "ops" / "medautoscience" / "paper_mission_stage_closure"),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    decision = payload["stage_closure_decision"]
    assert decision["stage_id"] == "review"
    assert decision["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert decision["opl_closeout"]["stage_attempt_id"] == "sat-review"
    assert decision["blocker_taxonomy"]["unknown"] == []
    assert decision["outcome"]["kind"] == "next_stage_transition"
    assert decision["outcome"]["transition_kind"] == "route_back_candidate_checkpoint"
    assert payload["opl_runtime_carrier_readback"]["opl_transition_receipt"][
        "stage_attempt_id"
    ] == "sat-review"
    assert payload["source_readback_summary"]["surface_kind"] == (
        "paper_mission_stage_attempt_closeout_readback"
    )


def test_terminalize_stage_autodiscovers_route_back_stage_packet_before_stale_consumption(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    stage_attempt_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-current"
    )
    stage_attempt_root.mkdir(parents=True)
    route_back_ref = (
        "ops/medautoscience/paper_mission_stage_attempts/"
        "sat-current/route_back_evidence_packet.json"
    )
    (workspace_root / route_back_ref).write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_stage_attempt_route_back_evidence_packet",
                "study_id": study_id,
                "stage_id": "write",
                "work_unit_id": "medical_methods_and_registry_reporting_repair",
                "owner_answer_kind": "route_back_evidence_ref",
            }
        ),
        encoding="utf-8",
    )
    closeout_ref = stage_attempt_root / "stage_attempt_closeout_packet.json"
    closeout_ref.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "study_id": study_id,
                "stage_id": "write",
                "work_unit_id": "medical_methods_and_registry_reporting_repair",
                "stage_attempt_id": "sat-current",
                "status": "completed",
                "owner_answer_kind": "route_back_evidence_ref",
                "route_back_evidence_ref": route_back_ref,
                "provider_attempt_ref": "opl://stage-attempts/sat-current",
            }
        ),
        encoding="utf-8",
    )
    stale_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
        / study_id
    )
    stale_root.mkdir(parents=True)
    (stale_root / "receipt_owner_consumption.json").write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_receipt_owner_consumption",
                "schema_version": 1,
                "status": "owner_consumption_applied",
                "study_id": study_id,
                "mas_receipt_consumption": {
                    "surface_kind": "mas_receipt_consumption_projection",
                    "status": "owner_consumed_typed_blocker",
                    "owner_result_kind": "typed_blocker",
                },
                "stage_closure_decision": {
                    "surface_kind": "mas_stage_closure_decision",
                    "outcome": {
                        "kind": "typed_blocker",
                        "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                    },
                    "counts_as_typed_blocker": True,
                },
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
            "--output-root",
            str(workspace_root / "ops" / "medautoscience" / "paper_mission_stage_closure"),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["source_readback_summary"]["surface_kind"] == (
        "paper_mission_stage_attempt_closeout_readback"
    )
    assert payload["stage_closure_decision"]["outcome"]["kind"] == (
        "next_stage_transition"
    )
    assert payload["stage_closure_decision"]["outcome"]["transition_kind"] == (
        "route_back_candidate_checkpoint"
    )
    assert payload["stage_closure_decision"].get("counts_as_typed_blocker") is not True


def test_terminalizer_source_prefers_current_live_closeout_over_stale_domain_transition(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts."
        "stage_closure_terminalizer_readback"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    transaction_ref = (
        f"paper-mission-transaction::{study_id}::write::paper-mission::{study_id}"
        "::medical_prose_write_repair_publication_gate_replay::one-shot-migration"
        "::followthrough::08c2efa65b67"
    )
    closeout_ref = (
        tmp_path
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-current"
        / "stage_attempt_closeout_packet.json"
    )
    closeout_ref.parent.mkdir(parents=True)
    closeout_ref.write_text("{}", encoding="utf-8")
    source_readback = {
        "surface_kind": "paper_mission_consumption_ledger_transaction_readback",
        "study_id": study_id,
        "mission_state": "route_back",
        "consume_candidate_status": "accepted_submission_milestone_candidate",
        "paper_mission_transaction": {"transaction_id": transaction_ref},
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-current",
                "closeout_ref": str(closeout_ref),
                "paper_mission_transaction_ref": transaction_ref,
            }
        },
    }
    profile = SimpleNamespace(
        workspace_root=tmp_path,
        studies_root=tmp_path / "studies",
    )

    monkeypatch.setattr(
        module,
        "_build_materialized_mission_readback_if_available",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        module,
        "_build_paper_mission_readback",
        lambda **kwargs: source_readback,
    )
    monkeypatch.setattr(
        module,
        "_latest_stage_attempt_route_back_source_readback",
        lambda **kwargs: None,
    )

    def stale_domain_transition(**kwargs):
        raise AssertionError("stale domain-transition direct readback should not win")

    monkeypatch.setattr(
        module,
        "_domain_transition_direct_terminal_source_readback",
        stale_domain_transition,
    )

    assert (
        module._build_terminalizer_source_readback(
            profile=profile,
            profile_ref=tmp_path / "profile.toml",
            study_id=study_id,
            source="test",
        )
        is source_readback
    )


def test_terminalizer_reterminalizes_stale_closure_when_current_live_closeout_differs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_command_parts."
        "stage_closure_terminalizer_readback"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    transaction_ref = (
        f"paper-mission-transaction::{study_id}::write::paper-mission::{study_id}"
        "::medical_prose_write_repair_publication_gate_replay::one-shot-migration"
        "::followthrough::08c2efa65b67"
    )
    closeout_ref = (
        tmp_path
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
        / "sat-current"
        / "stage_attempt_closeout_packet.json"
    )
    closeout_ref.parent.mkdir(parents=True)
    closeout_ref.write_text("{}", encoding="utf-8")
    source_readback = {
        "mission_state": "route_back",
        "consume_candidate_status": "accepted_submission_milestone_candidate",
        "paper_mission_transaction": {"transaction_id": transaction_ref},
        "opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-current",
                "closeout_ref": str(closeout_ref),
                "paper_mission_transaction_ref": transaction_ref,
            }
        },
    }
    existing_decision = {
        "opl_closeout": {"stage_attempt_id": "sat-stale"},
    }

    assert module._stage_closure_decision_uses_stale_terminal_closeout(
        existing_decision=existing_decision,
        source_readback=source_readback,
        workspace_root=tmp_path,
    )
