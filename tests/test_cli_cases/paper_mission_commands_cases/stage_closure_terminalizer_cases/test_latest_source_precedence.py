from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

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


def test_terminalize_stage_prefers_latest_consumption_closeout_over_inspect_placeholder(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / study_id
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260701Tstale-inspect"
        / study_id
    )
    mission_root.mkdir(parents=True)
    stale_transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::stale-inspect",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": stale_transaction["mission_id"],
                "study_id": study_id,
                "objective": "Stale inspect source that must not drive terminalize-stage.",
                "mission_state": "planned",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "claim_permissions": {
                    "can_claim_artifact_delta": False,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "consume_result": {"status": "not_consumed"},
                "paper_mission_transaction": stale_transaction,
            }
        ),
        encoding="utf-8",
    )
    transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::reviewer-revision",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
        / "foreground-reviewer-revision"
        / study_id
    )
    _write_consumption_ledger(
        ledger_root=ledger_root,
        study_id=study_id,
        candidate_ref="/tmp/reviewer-revision/package_manifest.json",
        transaction=transaction,
    )
    closeout_ref = ledger_root / "stage_attempt_closeout_packet.json"
    closeout_ref.write_text(
        json.dumps(
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "completed",
                    "study_id": study_id,
                    "stage_id": transaction["opl_route_command"]["target"],
                    "stage_attempt_id": "sat-current-reviewer",
                    "stage_packet_ref": transaction["transaction_id"]
                + "#stage_terminal_decision",
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "route_identity_key": transaction["transaction_id"] + "::route",
                "work_unit_id": transaction["stage_id"],
                "work_unit_fingerprint": transaction["idempotency"][
                    "transaction_fingerprint"
                ],
                "provider_completion_is_domain_completion": False,
                "provider_completion_is_domain_ready": False,
                "domain_completion_claimed": False,
                "domain_ready_claimed": False,
                "closeout_refs": [
                    str(study_root / "artifacts/publication_eval/medical_prose_review.json"),
                ],
                "paper_stage_log": {
                    "duration": {"status": "observed", "seconds": 732},
                    "token_usage": {"status": "missing", "total_tokens": None},
                    "cost": {"status": "observed_or_unreported", "usd": 0},
                },
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
    summary = payload["source_readback_summary"]
    assert summary["surface_kind"] == "paper_mission_consumption_ledger_transaction_readback"
    assert payload["mission_id"] == transaction["mission_id"]
    assert payload["stage_closure_decision"]["stage_id"] == transaction["stage_id"]
    assert payload["stage_closure_decision"]["identity"][
        "paper_mission_transaction_ref"
    ] == transaction["transaction_id"]
    closeout = payload["stage_closure_decision"]["opl_closeout"]
    assert closeout["status"] == "opl_runtime_terminal_readback_observed"
    assert closeout["stage_attempt_id"] == "sat-current-reviewer"
    assert payload["authority_boundary"]["writes_authority"] is False


def test_terminalize_stage_prefers_newer_stage_attempt_over_stale_transaction_match(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_one_shot_migration"
        / "20260707Tstale-transaction"
        / study_id
    )
    mission_root.mkdir(parents=True)
    transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::stale-write",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    transaction["transaction_id"] = (
        f"paper-mission-transaction::{study_id}::write::legacy-one-shot"
    )
    transaction["stage_id"] = "write"
    transaction["work_unit_id"] = work_unit_id
    transaction["stage_terminal_decision"]["target_stage_id"] = "write"
    transaction["stage_terminal_decision"]["target_work_unit_id"] = work_unit_id
    transaction["stage_terminal_decision"]["next_work_unit"] = work_unit_id
    transaction["opl_route_command"]["target"] = "write"
    transaction["opl_route_command"]["source_terminal_decision_ref"] = (
        transaction["transaction_id"] + "#stage_terminal_decision"
    )
    (mission_root / "paper_mission_run.json").write_text(
        json.dumps(
            {
                "schema_version": "paper-mission-run.v1",
                "mission_id": transaction["mission_id"],
                "study_id": study_id,
                "objective": "Stale write route that has been superseded.",
                "mission_state": "consumed",
                "artifact_delta_ledger": [],
                "source_refs": [],
                "authority_touchpoints": [],
                "forbidden_write_guard": _paper_mission_forbidden_write_guard(),
                "consume_result": {"status": "accepted"},
                "claim_permissions": {
                    "can_claim_artifact_delta": True,
                    "can_claim_owner_handoff": True,
                    "can_claim_publication_ready": False,
                    "can_claim_current_package": False,
                    "can_claim_owner_receipt_written": False,
                },
                "paper_mission_transaction": transaction,
                "one_shot_migration_readback": {
                    "consume_candidate_status": "accepted",
                },
            }
        ),
        encoding="utf-8",
    )

    def write_stage_attempt(
        *,
        attempt_id: str,
        stage_packet_ref: str,
        timestamp: float,
    ) -> Path:
        attempt_root = (
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_stage_attempts"
            / attempt_id
            / study_id
        )
        attempt_root.mkdir(parents=True)
        route_back_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            f"{study_id}/route_back_evidence_packet.json"
        )
        closeout_ref = (
            f"ops/medautoscience/paper_mission_stage_attempts/{attempt_id}/"
            f"{study_id}/stage_attempt_closeout_packet.json"
        )
        route_back = {
            "surface_kind": "paper_mission_stage_route_back_evidence_packet",
            "stage_attempt_id": attempt_id,
            "study_id": study_id,
            "stage_id": "write",
            "work_unit_id": work_unit_id,
            "stage_packet_ref": stage_packet_ref,
            "owner_answer_kind": "route_back_evidence_ref",
            "route_back_evidence_ref": route_back_ref,
            "source_evidence": {
                "paper_mission_transaction_ref": stage_packet_ref,
            },
        }
        closeout = {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "route_back_evidence_candidate",
            "study_id": study_id,
            "stage_id": "write",
            "work_unit_id": work_unit_id,
            "stage_attempt_id": attempt_id,
            "stage_packet_ref": stage_packet_ref,
            "owner_answer_kind": "route_back_evidence_ref",
            "route_back_evidence_ref": route_back_ref,
            "closeout_ref": closeout_ref,
            "closeout_refs": [closeout_ref, route_back_ref],
            "authority_boundary": {"record_only_surface": True},
        }
        route_path = attempt_root / "route_back_evidence_packet.json"
        closeout_path = attempt_root / "stage_attempt_closeout_packet.json"
        route_path.write_text(json.dumps(route_back), encoding="utf-8")
        closeout_path.write_text(json.dumps(closeout), encoding="utf-8")
        os.utime(route_path, (timestamp, timestamp))
        os.utime(closeout_path, (timestamp, timestamp))
        return closeout_path

    old_closeout_path = write_stage_attempt(
        attempt_id="sat-old-transaction-match",
        stage_packet_ref=transaction["transaction_id"],
        timestamp=1_788_000_000.0,
    )
    new_closeout_path = write_stage_attempt(
        attempt_id="sat-new-domain-transition",
        stage_packet_ref=f"paper-mission-transaction::{study_id}::write::domain-transition",
        timestamp=1_788_000_600.0,
    )
    terminalizer_readback = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands."
        "stage_closure_terminalizer_readback"
    )
    profile = importlib.import_module("med_autoscience.profiles").load_profile(
        profile_path
    )
    old_source_readback = (
        terminalizer_readback._build_terminalizer_source_readback_from_stage_packet(
            profile=profile,
            profile_ref=profile_path,
            study_id=study_id,
            stage_packet=old_closeout_path,
            source="test:stale-stage-packet",
        )
    )
    selected_source = (
        terminalizer_readback._latest_stage_attempt_route_back_source_readback(
            profile=profile,
            profile_ref=profile_path,
            study_id=study_id,
            source_readback=old_source_readback,
            source="test:autodiscovery",
        )
    )

    assert selected_source is not None
    assert selected_source["opl_runtime_carrier_readback"]["terminal_closeout"][
        "stage_attempt_id"
    ] == "sat-new-domain-transition"
    current_runtime_source_readback = {
        "paper_mission_transaction": transaction,
        "next_action": {
            "stage_id": "write",
            "work_unit_id": work_unit_id,
        },
        "current_opl_runtime_carrier_readback": {
            "terminal_closeout": {
                "stage_attempt_id": "sat-new-domain-transition",
                "closeout_refs": [str(new_closeout_path)],
            },
        },
    }
    selected_current_runtime_source = (
        terminalizer_readback._latest_stage_attempt_route_back_source_readback(
            profile=profile,
            profile_ref=profile_path,
            study_id=study_id,
            source_readback=current_runtime_source_readback,
            source="test:current-runtime-autodiscovery",
        )
    )

    assert selected_current_runtime_source is not None
    assert selected_current_runtime_source["opl_runtime_carrier_readback"][
        "terminal_closeout"
    ]["stage_attempt_id"] == "sat-new-domain-transition"

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
    closeout = payload["stage_closure_decision"]["opl_closeout"]
    assert closeout["stage_attempt_id"] == "sat-new-domain-transition"
    assert payload["stage_closure_decision"]["identity"][
        "paper_mission_transaction_ref"
    ] == f"paper-mission-transaction::{study_id}::write::domain-transition"


def test_inspect_prefers_latest_consumption_transaction_over_placeholder(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    transaction = _paper_mission_transaction_payload(
        mission_id=f"paper-mission::{study_id}::reviewer-revision",
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    _write_consumption_ledger(
        ledger_root=(
            workspace_root
            / "ops"
            / "medautoscience"
            / "paper_mission_consumption_ledger"
            / "foreground-reviewer-revision"
            / study_id
        ),
        study_id=study_id,
        candidate_ref="/tmp/reviewer-revision/package_manifest.json",
        transaction=transaction,
    )

    exit_code = cli.main(
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

    assert exit_code == 0
    assert payload["surface_kind"] == "paper_mission_consumption_ledger_transaction_readback"
    assert payload["paper_mission_command"] == "inspect"
    assert payload["paper_mission_current_transaction_source"] == (
        "paper_mission_consumption_ledger"
    )
    assert payload["mission_id"] == transaction["mission_id"]
    assert payload["paper_mission_transaction"]["transaction_id"] == (
        transaction["transaction_id"]
    )
    assert payload["stage_terminal_decision"]["next_owner"] == "mission_executor"


def _write_consumption_ledger(
    *,
    ledger_root: Path,
    study_id: str,
    candidate_ref: str,
    transaction: dict,
) -> None:
    ledger_root.mkdir(parents=True)
    stage_ref = transaction["transaction_id"] + "#stage_terminal_decision"
    route_ref = transaction["transaction_id"] + "#opl_route_command"
    carrier = _paper_mission_carrier_for_transaction(transaction)
    consume_record = {
        "surface_kind": "mas_paper_mission_candidate_consumption_record",
        "study_id": study_id,
        "candidate_ref": candidate_ref,
        "candidate_id": "reviewer-revision-v3",
        "status": "accepted",
        "selected_outcome": "accepted",
        "route_handoff_status": "ready_for_opl_route_command",
        "paper_mission_transaction_ref": transaction["transaction_id"],
        "stage_terminal_decision_ref": stage_ref,
        "opl_route_command_ref": route_ref,
        "counts_as_stage_terminalizer_evidence": True,
        "counts_as_opl_route_handoff_evidence": True,
        "authority_materialized": False,
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": {"writes_authority": False},
        "consume_result": {"status": "accepted"},
    }
    (ledger_root / "consume_record.json").write_text(
        json.dumps(consume_record),
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
                "candidate_ref": candidate_ref,
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "stage_terminal_decision_ref": stage_ref,
                "stage_id": transaction["stage_id"],
                "stage_run_ref": transaction["stage_run_ref"],
                "stage_terminal_decision": transaction["stage_terminal_decision"],
                "transaction_state": "accepted_submission_milestone_candidate",
                "authority_boundary": {"writes_authority": False},
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_command.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_opl_route_command_packet",
                "study_id": study_id,
                "candidate_ref": candidate_ref,
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "opl_route_command_ref": route_ref,
                "opl_route_command": transaction["opl_route_command"],
                "opl_runtime_carrier": carrier,
                "authority_boundary": {"writes_authority": False},
            }
        ),
        encoding="utf-8",
    )
    (ledger_root / "opl_route_handoff.json").write_text(
        json.dumps(
            {
                "surface_kind": "mas_paper_mission_opl_route_handoff_record",
                "study_id": study_id,
                "handoff_status": "ready_for_opl_route_command",
                "can_submit_to_opl_runtime": True,
                "transaction_materialized": True,
                "paper_mission_transaction_ref": transaction["transaction_id"],
                "stage_terminal_decision_ref": stage_ref,
                "opl_route_command_ref": route_ref,
                "stage_terminal_decision": transaction["stage_terminal_decision"],
                "opl_route_command": transaction["opl_route_command"],
                "route_command_kind": transaction["opl_route_command"]["command_kind"],
                "opl_runtime_carrier": carrier,
                "authority_boundary": {"writes_authority": False},
            }
        ),
        encoding="utf-8",
    )


def _paper_mission_carrier_for_transaction(transaction: dict) -> dict:
    identity = transaction["idempotency"]
    decision = transaction["stage_terminal_decision"]
    work_unit_id = (
        decision.get("next_work_unit")
        if decision.get("decision_kind") == "continue_same_stage"
        else None
    ) or transaction["stage_id"]
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "source_kind": "paper_mission_transaction_opl_route_command",
        "projection_only": True,
        "paper_mission_transaction_ref": transaction["transaction_id"],
        "stage_terminal_decision_ref": transaction["transaction_id"]
        + "#stage_terminal_decision",
        "opl_route_command_ref": transaction["transaction_id"] + "#opl_route_command",
        "study_id": transaction["study_id"],
        "stage_run_ref": transaction["stage_run_ref"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": identity["transaction_fingerprint"],
        "route_identity_key": transaction["transaction_id"] + "::route",
        "idempotency_key": identity["idempotency_key"],
        "attempt_idempotency_key": identity["idempotency_key"] + "::opl-attempt",
        "request_idempotency_key": identity["idempotency_key"] + "::opl-request",
        "opl_route_command": transaction["opl_route_command"],
        "aggregate_identity": {
            "aggregate_id": transaction["transaction_id"],
            "mission_id": transaction["mission_id"],
            "study_id": transaction["study_id"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": identity["transaction_fingerprint"],
        },
    }
