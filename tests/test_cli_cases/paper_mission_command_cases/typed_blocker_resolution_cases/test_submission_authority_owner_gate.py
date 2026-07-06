from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study


def _readback(*, study_id: str, package_kind: str, can_submit: bool) -> dict[str, object]:
    return {
        "study_id": study_id,
        "next_action": {
            "action_family": "blocked.typed",
            "action_kind": "stop_with_typed_blocker",
            "owner": "mas_authority_kernel",
        },
        "stage_closure_decision": {
            "outcome": {
                "kind": "typed_blocker",
                "blocker_type": "paper_mission_stage_route_domain_gate_pending",
                "next_owner": "MedAutoScience",
                "next_action": "resolve_typed_blocker_or_route_redesign",
                "typed_blocker_evidence_ref": f"/tmp/{study_id}/typed-blocker.json",
            }
        },
        "receipt_owner_consumption_readback": {
            "status": "owner_consumption_applied",
            "apply_mode": "route_checkpoint" if can_submit else "typed_blocker",
            "mas_receipt_consumption": {
                "status": "owner_consumed_typed_blocker",
                "typed_blocker_evidence_ref": f"/tmp/{study_id}/typed-blocker.json",
            },
        },
        "current_package": {
            "status": "current",
            "package_kind": package_kind,
            "can_submit": can_submit,
            "quality_gate_status": "clear" if can_submit else "blocked",
            "known_blockers": [] if can_submit else ["bundle_build_allowed_false"],
            "root": f"/tmp/{study_id}/manuscript/current_package",
            "zip_path": f"/tmp/{study_id}/manuscript/current_package.zip",
            "zip_exists": True,
            "generated_from_current_source": True,
        },
    }


def test_paper_mission_inspect_retires_submission_authority_owner_gate_after_matching_event(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    interventions = importlib.import_module("med_autoscience.controllers.study_interventions")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    study_root = tmp_path / "workspace" / "studies" / study_id
    readback_file = tmp_path / "readback.json"
    output_root = (
        tmp_path
        / "workspace"
        / "ops"
        / "medautoscience"
        / "paper_mission_typed_blocker_resolution"
    )
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                package_kind="submission_ready_package",
                can_submit=True,
            )
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "typed-blocker-resolution",
            "--profile",
            str(profile_path),
            "--study-id",
            study_id,
            "--paper-mission-readback-file",
            str(readback_file),
            "--output-root",
            str(output_root),
            "--apply-owner-decision",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    materialized_payload = json.loads(capsys.readouterr().out)
    next_owner_action = materialized_payload["next_owner_action"]
    interventions.owner_gate_decision_record(
        study_root=study_root,
        study_id=study_id,
        action_type=next_owner_action["action_type"],
        work_unit_id=next_owner_action["work_unit_id"],
        work_unit_fingerprint=next_owner_action["work_unit_fingerprint"],
        blocker_type="submission_ready_authority_closeout_required",
        decision="accept_submission_ready_authority_closeout",
        reason="test owner gate decision already recorded",
        recorded_at="2026-06-30T02:32:16+00:00",
        apply=True,
        source="codex",
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
    typed_readback = payload["typed_blocker_resolution_readback"]
    gate_readback = payload["submission_authority_owner_gate_readback"]

    assert exit_code == 0
    assert "next_action" not in payload
    assert "next_action" not in payload["paper_mission_transaction_readback"]
    assert typed_readback["next_owner_action"] is None
    assert typed_readback["submission_authority_owner_gate_readback"] == gate_readback
    assert gate_readback["status"] == "owner_gate_recorded"
    assert gate_readback["decision"] == "accept_submission_ready_authority_closeout"
    assert gate_readback["duplicate_owner_gate_action_retired"] is True
    assert gate_readback["authority_materialized"] is False
    assert gate_readback["writes_owner_receipt"] is False
    assert gate_readback["writes_human_gate_authority"] is False
    assert payload["paper_facing_action"]["status"] == "awaiting_submission_authority_closeout"
    assert payload["paper_facing_action"]["source_surface"] == (
        "submission_authority_owner_gate_readback"
    )
    assert payload["paper_facing_action"]["next_legal_action"] == (
        "await_submission_authority_or_human_gate_closeout"
    )
    assert payload["paper_facing_action"]["owner_gate_decision_ref"] == (
        gate_readback["owner_gate_decision_ref"]
    )
    assert (
        payload["paper_facing_action"]["authority_boundary"]["can_claim_submission_ready"]
        is False
    )
