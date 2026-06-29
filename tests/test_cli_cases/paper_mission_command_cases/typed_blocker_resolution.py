from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

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


def test_typed_blocker_resolution_reports_missing_owner_apply_surface(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "readback.json"
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
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "blocked_missing_typed_blocker_resolution_surface"
    assert payload["write_permitted"] is False
    assert payload["authority_materialized"] is False
    assert payload["submission_ready_claim_authorized"] is False
    assert payload["current_package"]["can_submit"] is True
    assert payload["owner_route_defect"]["defect_kind"] == (
        "mas_typed_blocker_resolution_owner_surface_missing"
    )
    assert "paper-mission typed-blocker-resolution --apply-owner-decision" in payload[
        "owner_route_defect"
    ]["missing_command_or_api"]
    assert "current_package" in payload["forbidden_authority_writes"]


def test_typed_blocker_resolution_fails_closed_without_consumed_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "readback.json"
    readback_file.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "next_action": {
                    "action_family": "blocked.typed",
                    "action_kind": "stop_with_typed_blocker",
                    "owner": "mas_authority_kernel",
                },
                "stage_closure_decision": {"outcome": {"kind": "typed_blocker"}},
            }
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
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "blocked_missing_consumed_typed_blocker_readback"
    assert payload["readback_validation"]["missing_required_fields"] == [
        "receipt_owner_consumption_readback"
    ]


def test_typed_blocker_resolution_route_redesign_writes_non_authority_packet(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "readback.json"
    output_root = (
        tmp_path / "ops" / "medautoscience" / "paper_mission_typed_blocker_resolution"
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
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    manifest = payload["output_manifest"]
    packet = json.loads(Path(manifest["packet_ref"]).read_text(encoding="utf-8"))
    owner_decision = json.loads(
        Path(manifest["owner_decision_packet_ref"]).read_text(encoding="utf-8")
    )
    successor = json.loads(
        Path(manifest["successor_work_unit_ref"]).read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert payload["status"] == "owner_route_redesign_applied"
    assert payload["apply_mode"] == "route_redesign"
    assert payload["resolution_packet_materialized"] is True
    assert payload["authority_materialized"] is False
    assert payload["writes_authority"] is False
    assert payload["submission_ready_claim_authorized"] is False
    assert manifest["writes_authority"] is False
    assert manifest["writes_yang_authority"] is False
    assert owner_decision["authority_boundary"]["writes_owner_receipt"] is False
    assert owner_decision["authority_boundary"]["writes_human_gate"] is False
    assert successor["work_unit_id"] == "submission_authority_owner_verdict"
    assert packet["status"] == "owner_route_redesign_applied"
    assert packet["authority_materialized"] is False


def test_typed_blocker_resolution_owner_decision_writes_non_authority_packet(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "readback.json"
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
            "--apply-owner-decision",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_decision_resolution_packet_materialized"
    assert payload["apply_mode"] == "owner_decision"
    assert payload["resolution_packet_materialized"] is True
    assert payload["authority_materialized"] is False
    assert payload["writes_authority"] is False
    assert payload["owner_decision_packet"]["decision_kind"] == "owner_decision"
    assert payload["owner_decision_packet"]["authority_boundary"][
        "writes_owner_receipt"
    ] is False
    assert payload["owner_decision_packet"]["authority_boundary"][
        "writes_human_gate"
    ] is False
    assert payload["successor_work_unit"]["work_unit_id"] == (
        "submission_ready_authority_closeout"
    )
    assert payload["next_owner_action"]["action_type"] == (
        "materialize_submission_ready_owner_verdict_or_human_gate"
    )


def test_typed_blocker_resolution_human_gate_writes_non_authority_packet(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                package_kind="current_package",
                can_submit=False,
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
            "--apply-human-gate",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "human_gate_resolution_packet_materialized"
    assert payload["apply_mode"] == "human_gate"
    assert payload["resolution_packet_materialized"] is True
    assert payload["authority_materialized"] is False
    assert payload["writes_authority"] is False
    assert payload["owner_decision_packet"]["decision_kind"] == "human_gate"
    assert payload["owner_decision_packet"]["authority_boundary"][
        "writes_owner_receipt"
    ] is False
    assert payload["owner_decision_packet"]["authority_boundary"][
        "writes_human_gate"
    ] is False
    assert payload["successor_work_unit"]["work_unit_id"] == (
        "submission_blocker_human_gate"
    )
    assert payload["next_owner_action"]["action_type"] == (
        "await_human_or_mas_authority_decision_for_submission_blocker"
    )


def test_typed_blocker_resolution_packet_projects_canonical_next_action(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
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
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    materialized_payload = json.loads(capsys.readouterr().out)
    packet_path = Path(materialized_payload["output_manifest"]["packet_ref"])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["next_owner_action"].pop("action_type", None)
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

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
    next_action = payload["next_action"]
    typed_readback = payload["typed_blocker_resolution_readback"]

    assert exit_code == 0
    assert typed_readback["status"] == "owner_route_redesign_applied"
    assert typed_readback["source_surface_kind"] == (
        "paper_mission_typed_blocker_resolution_ledger"
    )
    assert next_action["surface_kind"] == "mas_next_action_envelope"
    assert next_action["action_family"] == "paper.package.submission_minimal"
    assert next_action["action_kind"] == "package_materialization"
    assert next_action["owner"] == "mas_authority_kernel"
    assert next_action["action_type"] == (
        "consume_submission_ready_package_authority_or_human_gate"
    )
    assert next_action["allowed_actions"] == [
        "consume_submission_ready_package_authority_or_human_gate"
    ]
    assert next_action["work_unit_id"] == "submission_authority_owner_verdict"
    assert next_action["authority_boundary"]["can_claim_submission_ready"] is False
    assert next_action["diagnostic_refs"] == [
        {
            "role": "typed_blocker_resolution",
            "ref": typed_readback["source_ref"],
        }
    ]


def test_typed_blocker_resolution_rejects_forbidden_output_root(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback_file = tmp_path / "readback.json"
    readback_file.write_text(
        json.dumps(
            _readback(
                study_id=study_id,
                package_kind="current_package",
                can_submit=False,
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        cli.main(
            [
                "paper-mission",
                "typed-blocker-resolution",
                "--profile",
                str(profile_path),
                "--study-id",
                study_id,
                "--paper-mission-readback-file",
                str(readback_file),
                "--apply-route-redesign",
                "--output-root",
                str(
                    tmp_path
                    / "workspace"
                    / "studies"
                    / study_id
                    / "artifacts"
                    / "publication_eval"
                ),
                "--format",
                "json",
            ]
        )
