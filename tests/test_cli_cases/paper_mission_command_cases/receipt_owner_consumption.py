from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    latest_receipt_owner_consumption_readback,
)

from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study


def _readback(
    *,
    study_id: str,
    stage_outcome: str,
    transition_kind: str | None,
    package_kind: str,
    can_submit: bool,
    consumption_next_legal_action: str | None = None,
) -> dict[str, object]:
    outcome: dict[str, object] = {
        "kind": stage_outcome,
        "next_legal_action": "record_typed_blocker",
    }
    if transition_kind:
        outcome["transition_kind"] = transition_kind
    if consumption_next_legal_action is None:
        consumption_next_legal_action = (
            "record_typed_blocker"
            if stage_outcome == "typed_blocker"
            else "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
        )
    return {
        "surface_kind": "paper_mission_materialized_readback",
        "schema_version": 1,
        "study_id": study_id,
        "mission_state": "consumed",
        "current_package": {
            "status": "current",
            "package_kind": package_kind,
            "can_submit": can_submit,
            "quality_gate_status": "clear" if can_submit else "blocked",
            "known_blockers": [] if can_submit else ["bundle_build_allowed_false"],
            "root": f"/tmp/{study_id}/manuscript/current_package",
            "zip_path": f"/tmp/{study_id}/manuscript/current_package.zip",
            "zip_exists": True,
        },
        "stage_closure_decision": {
            "decision_ref": f"mas://paper-mission/{study_id}/stage-closure",
            "outcome": outcome,
        },
        "stage_closure_outcome": stage_outcome,
        "durable_mission_stop_guard": {
            "durable_stop_allowed": False,
        },
        "opl_runtime_carrier_readback": {
            "runtime_readback_status": "terminal_closeout_observed",
            "receipt_evidence": {
                "receipt_kind": "opl_transition_receipt",
                "receipt_ref": "opl://stage-attempts/sat-receipt",
                "impact_receipt_kind": "mas_impact_receipt",
                "impact_receipt_ref": "opl://stage-attempts/sat-receipt/mas-impact",
                "runtime_closeout_ref": (
                    "opl://family-runtime/tasks/frt-receipt/terminal-closeout-readback"
                ),
                "can_claim_paper_progress": False,
            },
            "opl_transition_receipt": {
                "surface_kind": "opl_transition_receipt",
                "receipt_status": "terminal_closeout_observed",
                "role": "transport_receipt_only",
                "task_id": "frt-receipt",
                "task_status": "blocked",
                "stage_attempt_id": "sat-receipt",
                "stage_attempt_ref": "opl://stage-attempts/sat-receipt",
                "closeout_receipt_status": "accepted_typed_closeout",
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
                "can_claim_paper_progress": False,
            },
            "mas_receipt_consumption": {
                "surface_kind": "mas_receipt_consumption_projection",
                "status": "requires_mas_owner_consumption",
                "next_legal_action": consumption_next_legal_action,
                "forbidden_next_action": "synonymous_route_back_redrive",
                "durable_stop_allowed": False,
                "can_claim_paper_progress": False,
                "can_claim_publication_ready": False,
            },
        },
    }


def test_receipt_owner_consumption_classifies_dm002_typed_blocker_without_authority_write(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm002-readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="typed_blocker",
                transition_kind=None,
                package_kind="current_package",
                can_submit=False,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_evidence_materialized"
    assert payload["write_permitted"] is False
    assert payload["authority_materialized"] is False
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "record_typed_blocker_owner_consumption_required"
    )
    assert payload["owner_consumption_verdict"]["required_authority_surface_exists"] is True
    assert payload["owner_consumption_verdict"]["implemented_surface_role"] == (
        "mas_owner_consumption_authority_apply_surface"
    )
    assert payload["owner_consumption_verdict"]["forbidden_next_action"] == (
        "synonymous_route_back_redrive"
    )
    assert payload["current_package"]["can_submit"] is False
    assert payload["submission_ready_claim_authorized"] is False
    assert "publication_eval/latest.json" in payload["forbidden_authority_writes"]


def test_receipt_owner_consumption_keeps_dm003_submission_ready_mirror_non_terminal(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="submission_ready_package",
                can_submit=True,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
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
            str(tmp_path / "receipt-owner-consumption"),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["current_package"]["package_kind"] == "submission_ready_package"
    assert payload["current_package"]["can_submit"] is True
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "consume_route_back_checkpoint_owner_consumption_required"
    )
    assert payload["owner_consumption_verdict"]["can_claim_submission_ready"] is False
    assert payload["owner_consumption_verdict"]["durable_stop_allowed"] is False
    assert payload["output_manifest"]["writes_authority"] is False
    packet_ref = Path(payload["output_manifest"]["packet_ref"])
    assert packet_ref.exists()
    assert json.loads(packet_ref.read_text(encoding="utf-8"))[
        "submission_ready_claim_authorized"
    ] is False


def test_receipt_owner_consumption_fails_closed_without_opl_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "missing-receipt.json"
    readback_file.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_materialized_readback",
                "study_id": study_id,
                "stage_closure_decision": {"outcome": {"kind": "typed_blocker"}},
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "blocked_missing_consumable_opl_receipt"
    assert payload["readback_validation"]["missing_required_fields"] == [
        "opl_runtime_carrier_readback",
        "opl_runtime_carrier_readback.opl_transition_receipt",
        "opl_runtime_carrier_readback.receipt_evidence",
        "opl_runtime_carrier_readback.mas_receipt_consumption",
    ]
    assert payload["implementation_gap"]["gap_kind"] == (
        "mas_owner_consumption_authority_apply_surface_missing"
    )


def test_receipt_owner_consumption_accepts_top_level_receipt_projection(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback = _readback(
        study_id=study_id,
        stage_outcome="typed_blocker",
        transition_kind=None,
        package_kind="current_package",
        can_submit=False,
    )
    carrier = readback["opl_runtime_carrier_readback"]
    assert isinstance(carrier, dict)
    readback["receipt_evidence"] = carrier.pop("receipt_evidence")
    readback["opl_transition_receipt"] = carrier.pop("opl_transition_receipt")
    readback["mas_receipt_consumption"] = carrier.pop("mas_receipt_consumption")
    readback_file = tmp_path / "top-level-receipt.json"
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_evidence_materialized"
    assert payload["readback_validation"]["valid"] is True
    assert payload["owner_consumption_verdict"]["required_authority_surface_exists"] is True


def test_receipt_owner_consumption_apply_typed_blocker_writes_safe_consumption_ledger(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm002-readback.json"
    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="typed_blocker",
                transition_kind=None,
                package_kind="current_package",
                can_submit=False,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
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
            str(output_root),
            "--apply-typed-blocker",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    packet_ref = Path(payload["output_manifest"]["packet_ref"])
    packet = json.loads(packet_ref.read_text(encoding="utf-8"))
    latest = latest_receipt_owner_consumption_readback(
        workspace_root=tmp_path,
        study_id=study_id,
    )

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["apply_mode"] == "typed_blocker"
    assert payload["authority_materialized"] is True
    assert payload["submission_ready_claim_authorized"] is False
    assert payload["output_manifest"]["writes_authority"] is True
    assert payload["output_manifest"]["writes_yang_authority"] is False
    assert payload["stage_closure_decision"]["outcome"]["kind"] == "typed_blocker"
    assert payload["stage_closure_decision"]["counts_as_typed_blocker"] is True
    assert payload["stage_closure_decision"]["authority_boundary"]["writes_owner_receipt"] is False
    assert payload["stage_closure_decision"]["authority_boundary"]["writes_typed_blocker"] is False
    assert payload["stage_closure_decision"]["authority_boundary"]["writes_human_gate"] is False
    assert payload["stage_closure_decision"]["authority_boundary"]["writes_current_package"] is False
    assert packet["status"] == "owner_consumption_applied"
    assert latest is not None
    assert latest["source_ref"] == str(packet_ref)


def test_receipt_owner_consumption_apply_route_checkpoint_records_typed_blocker_not_submission_ready(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm003-readback.json"
    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="submission_ready_package",
                can_submit=True,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
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
            str(output_root),
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["current_package"]["package_kind"] == "submission_ready_package"
    assert payload["current_package"]["can_submit"] is True
    assert payload["submission_ready_claim_authorized"] is False
    assert payload["owner_consumption_verdict"]["can_claim_submission_ready"] is False
    assert payload["stage_closure_decision"]["outcome"]["kind"] == "typed_blocker"
    assert payload["stage_closure"]["outcome_kind"] == "typed_blocker"
    assert payload["stage_closure"]["transition_kind"] is None
    assert payload["stage_closure_decision"]["outcome"]["can_submit"] is True
    assert payload["stage_closure_decision"]["authority_boundary"][
        "writes_current_package"
    ] is False


def test_receipt_owner_consumption_route_checkpoint_can_require_typed_blocker_apply(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "obesity-readback.json"
    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_receipt_owner_consumption"
    )
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="next_stage_transition",
                transition_kind="route_back_candidate_checkpoint",
                package_kind="current_package",
                can_submit=False,
                consumption_next_legal_action="record_typed_blocker",
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
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
            str(output_root),
            "--apply-typed-blocker",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_consumption_applied"
    assert payload["apply_mode"] == "typed_blocker"
    assert payload["owner_consumption_verdict"]["verdict_kind"] == (
        "record_typed_blocker_owner_consumption_required"
    )
    assert payload["owner_consumption_verdict"]["required_authority_surface"] == (
        "paper-mission receipt-owner-consumption --apply-typed-blocker"
    )
    assert payload["stage_closure_decision"]["outcome"]["kind"] == "typed_blocker"
    assert payload["stage_closure"]["outcome_kind"] == "typed_blocker"
    assert payload["submission_ready_claim_authorized"] is False


def test_receipt_owner_consumption_apply_mode_mismatch_fails_closed(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "dm002-readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                stage_outcome="typed_blocker",
                transition_kind=None,
                package_kind="current_package",
                can_submit=False,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "receipt-owner-consumption",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--apply-route-checkpoint",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "blocked_apply_mode_mismatch"
    assert payload["write_permitted"] is False
    assert payload["authority_materialized"] is False
    assert payload["requested_apply_mode"] == "route_checkpoint"
    assert payload["expected_apply_mode"] == "typed_blocker"
