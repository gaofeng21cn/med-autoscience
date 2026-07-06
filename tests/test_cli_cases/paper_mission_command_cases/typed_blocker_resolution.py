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


def test_typed_blocker_resolution_accepts_successor_owner_action_envelope(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback = _readback(
        study_id=study_id,
        package_kind="current_package",
        can_submit=False,
    )
    readback["next_action"] = {
        "action_family": "paper.package.submission_minimal",
        "action_kind": "package_materialization",
        "owner": "mas_authority_kernel",
        "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
    }
    readback_file = tmp_path / "successor-owner-action-readback.json"
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

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
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_route_redesign_applied"
    assert payload["readback_validation"]["valid"] is True
    assert payload["next_owner_action"]["work_unit_id"] == (
        "submission_blocker_degraded_handoff_or_quality_repair"
    )
    assert payload["executable_owner_route"]["accepted_answer_shape"][
        "shape_kind"
    ] == "quality_repair_or_degraded_handoff"


def test_typed_blocker_resolution_accepts_route_back_owner_action_without_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    readback = _readback(
        study_id=study_id,
        package_kind="current_package",
        can_submit=False,
    )
    readback.pop("receipt_owner_consumption_readback")
    readback["stage_closure_decision"] = {
        "outcome": {
            "kind": "next_stage_transition",
            "transition_kind": "route_back_candidate_checkpoint",
        }
    }
    readback["next_action"] = {
        "action_family": "paper.package.submission_minimal",
        "action_kind": "package_materialization",
        "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
        "owner": "mas_authority_kernel",
        "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        "work_unit_fingerprint": "7ca5e4d5e993dd9304f45400",
    }
    readback_file = tmp_path / "route-back-owner-action-readback.json"
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

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
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_route_redesign_applied"
    assert payload["readback_validation"] == {
        "valid": True,
        "missing_required_fields": [],
        "mismatched_fields": [],
    }
    assert payload["next_owner_action"]["action_type"] == (
        "classify_quality_blockers_or_materialize_degraded_handoff_gate"
    )
    assert payload["next_owner_action"]["required_delta_kind"] == (
        "typed_blocker_resolution_owner_action"
    )


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


def test_typed_blocker_resolution_hydrates_existing_audit_current_package(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    study_root = tmp_path / "workspace" / "studies" / study_id
    current_package = study_root / "manuscript" / "current_package"
    (current_package / "audit").mkdir(parents=True)
    (study_root / "manuscript").mkdir(exist_ok=True)
    (study_root / "manuscript" / "current_package.zip").write_bytes(b"zip")
    (current_package / "SUBMISSION_TODO.md").write_text(
        "\n".join(
            [
                "# Submission TODO",
                "",
                "Pending items:",
                "- Authors: pending",
                "- Ethics: pending",
            ]
        ),
        encoding="utf-8",
    )
    (current_package / "audit" / "submission_manifest.json").write_text(
        json.dumps(
            {
                "package_kind": "current_package",
                "can_submit": False,
                "quality_gate_status": "not_blocked",
                "known_blockers": [],
                "generated_from_current_source": True,
            }
        ),
        encoding="utf-8",
    )
    readback = _readback(
        study_id=study_id,
        package_kind="current_package",
        can_submit=False,
    )
    readback["study_root"] = str(study_root)
    readback.pop("current_package")
    readback.pop("next_action")
    readback_file = tmp_path / "readback-without-package-projection.json"
    readback_file.write_text(json.dumps(readback), encoding="utf-8")

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
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    package = payload["current_package"]
    assert package["package_kind"] == "current_package"
    assert package["can_submit"] is False
    assert package["zip_exists"] is True
    assert package["generated_from_current_source"] is True
    assert package["quality_gate_status"] == "not_blocked"
    assert package["known_blockers"] == []
    assert package["administrative_todo"] == ["Authors: pending", "Ethics: pending"]
    assert payload["executable_owner_route"]["paper_facing_delta"]["package_kind"] == (
        "current_package"
    )


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
    assert successor["authority_boundary"]["writes_authority"] is False
    assert packet["executable_owner_route"]["next_owner"] == "mas_authority_kernel"
    assert packet["executable_owner_route"]["paper_facing_delta"]["delta_kind"] == (
        "submission_authority_owner_verdict"
    )
    assert packet["executable_owner_route"]["accepted_answer_shape"]["shape_kind"] == (
        "owner_receipt_or_human_gate"
    )
    assert packet["executable_owner_route"]["route_back"]["route_back_to"] == (
        "paper-mission inspect"
    )
    assert packet["executable_owner_route"]["verification"]["owner_readback_command"].endswith(
        f"--study-id {study_id} --format json"
    )
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
    assert payload["executable_owner_route"]["paper_facing_delta"]["delta_kind"] == (
        "submission_authority_owner_verdict"
    )
    assert payload["executable_owner_route"]["accepted_answer_shape"]["shape_kind"] == (
        "submission_authority_owner_gate_decision"
    )
    assert payload["next_owner_action"]["action_type"] == (
        "materialize_submission_ready_owner_verdict_or_human_gate"
    )
    assert payload["next_owner_action"]["paper_facing_delta"]["delta_kind"] == (
        "submission_authority_owner_verdict"
    )
    assert payload["next_owner_action"]["accepted_answer_shape"]["shape_kind"] == (
        "submission_authority_owner_gate_decision"
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
    assert payload["executable_owner_route"]["paper_facing_delta"]["delta_kind"] == (
        "human_gate_decision"
    )
    assert payload["executable_owner_route"]["accepted_answer_shape"]["shape_kind"] == (
        "human_gate_or_degraded_handoff"
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
    assert next_action["paper_facing_delta"]["delta_kind"] == (
        "submission_authority_owner_verdict"
    )
    assert next_action["accepted_answer_shape"]["shape_kind"] == (
        "owner_receipt_or_human_gate"
    )
    assert next_action["route_back"]["route_back_to"] == "paper-mission inspect"
    assert next_action["authority_boundary"]["can_claim_submission_ready"] is False
    assert next_action["diagnostic_refs"] == [
        {
            "role": "typed_blocker_resolution",
            "ref": typed_readback["source_ref"],
        }
    ]
    assert "current_executable_owner_action" not in payload
    paper_action = payload["paper_facing_action"]
    assert paper_action["status"] == "owner_action_ready"
    assert paper_action["source_surface"] == "paper_mission.next_action"
    assert paper_action["next_owner"] == "mas_authority_kernel"
    assert paper_action["action_type"] == (
        "consume_submission_ready_package_authority_or_human_gate"
    )
    assert paper_action["paper_facing_delta"]["delta_kind"] == (
        "submission_authority_owner_verdict"
    )
    assert paper_action["next_step"].startswith("等待 mas_authority_kernel owner")
    assert paper_action["authority_boundary"]["can_write_owner_receipt"] is False
    assert paper_action["authority_boundary"]["can_claim_submission_ready"] is False


def test_paper_mission_inspect_prefers_domain_transition_ai_reviewer_over_old_resolution(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    study_root = tmp_path / "workspace" / "studies" / study_id
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_path.parent.mkdir(parents=True)
    publication_eval_path.write_text(
        json.dumps(
            {
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "partial",
                        "summary": "Reviewer revision requires a fresh medical prose review.",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
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
            "--output-root",
            str(output_root),
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

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

    assert exit_code == 0
    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert next_action["action_family"] == "paper.review.ai_reviewer"
    assert next_action["owner"] == "ai_reviewer"
    assert next_action["action_type"] == "return_to_ai_reviewer_workflow"
    assert next_action["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert "typed_blocker_resolution_readback" not in payload


def test_paper_mission_inspect_prefers_domain_transition_write_attempt_over_old_resolution(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    study_root = tmp_path / "workspace" / "studies" / study_id
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval_path.parent.mkdir(parents=True)
    publication_eval_path.write_text(
        json.dumps(
            {
                "eval_id": (
                    "publication-eval::obesity_multicenter_phenotype_atlas::"
                    "medical-methods-registry-repair::current"
                ),
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "ready",
                        "summary": "Current AI reviewer record routes a same-line registry reporting repair.",
                    }
                },
                "recommended_actions": [
                    {
                        "action_id": "obesity-current-methods-registry-repair",
                        "action_type": "route_back_same_line",
                        "requires_controller_decision": True,
                        "route_target": "write",
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "medical_methods_and_registry_reporting_repair"
                        ),
                        "next_work_unit": {
                            "unit_id": "medical_methods_and_registry_reporting_repair",
                            "lane": "write",
                            "summary": (
                                "Repair Methods, Results terminology, variable-definition "
                                "table, adult-only sensitivity/missingness display "
                                "requirements, and internal prose residue."
                            ),
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    controller_decision_path.parent.mkdir(parents=True)
    controller_decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "obesity-current-methods-registry-repair",
                "decision_type": "route_back_same_line",
                "study_id": study_id,
                "quest_id": study_id,
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": "run_quality_repair_batch"}],
                "route_target": "write",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "medical_methods_and_registry_reporting_repair"
                ),
                "next_work_unit": {
                    "unit_id": "medical_methods_and_registry_reporting_repair",
                    "lane": "write",
                    "summary": (
                        "Repair Methods, Results terminology, variable-definition "
                        "table, adult-only sensitivity/missingness display "
                        "requirements, and internal prose residue."
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
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
            "--output-root",
            str(output_root),
            "--apply-route-redesign",
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

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

    assert exit_code == 0
    assert payload["canonical_next_action_source"] == "domain_transition.next_action"
    assert payload["domain_transition"]["decision_type"] == "route_back_same_line"
    assert payload["domain_transition"]["route_target"] == "write"
    assert next_action["action_type"] == "request_opl_stage_attempt"
    assert next_action["owner"] == "write"
    assert next_action["stage_id"] == "write"
    assert next_action["work_unit_id"] == "medical_methods_and_registry_reporting_repair"
    assert next_action["work_unit_fingerprint"] == (
        "domain-transition::route_back_same_line::"
        "medical_methods_and_registry_reporting_repair"
    )
    assert "typed_blocker_resolution_readback" not in payload


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
