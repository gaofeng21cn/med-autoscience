from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import (
    _assert_forbidden_authority_untouched,
    _paper_mission_transaction_payload,
    _write_profile_with_study,
    _write_submission_milestone_package,
)


def test_paper_mission_consume_candidate_rebinds_typed_blocker_package_refs(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::paper_mission_import::one-shot"
    old_package_ref = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "old"
        / study_id
        / "package_manifest.json"
    )
    old_transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="continue_same_stage",
    )
    old_transaction["idempotency"]["idempotency_key"] = (
        f"{study_id}::submission_blocker_human_gate::"
        f"submission-milestone-candidate-consumed::{old_package_ref}::"
        "candidate-ref-missing::transaction-ref-missing"
    )
    old_transaction["artifact_delta_refs"] = [
        {
            "ref_id": "submission_milestone_artifact::old",
            "ref_kind": "submission_milestone_candidate_artifact",
            "uri": str(old_package_ref.parent / "paper_facing_candidate_delta.json"),
        }
    ]
    package_path = _write_submission_milestone_package(
        workspace_root=workspace_root,
        study_id=study_id,
        mission_id=mission_id,
        base_transaction=old_transaction,
    )
    package_manifest = json.loads(package_path.read_text(encoding="utf-8"))
    package_manifest["artifact_refs"] = {
        **package_manifest.get("artifact_refs", {}),
        "mission_candidate_artifact_delta": str(
            package_path.parent / "mission_candidate_artifact_delta.json"
        ),
        "owner_decision_packet": str(package_path.parent / "owner_decision_packet.json"),
    }
    package_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    owner_blocker_packet = json.loads(
        (package_path.parent / "owner_blocker_packet.json").read_text(
            encoding="utf-8"
        )
    )
    owner_blocker_packet["blocker_kind"] = "typed_blocker"
    owner_blocker_packet["current_terminal_decision"] = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": "accepted typed-blocker context as a package-bound candidate",
        "next_owner": "mission_executor",
        "next_work_unit": "submission_blocker_human_gate",
        "route_command": "resume_stage",
        "route_target": "submission_blocker_human_gate",
    }
    (package_path.parent / "owner_blocker_packet.json").write_text(
        json.dumps(owner_blocker_packet),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--dry-run",
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
    idempotency_key = payload["paper_mission_transaction"]["idempotency"][
        "idempotency_key"
    ]
    artifact_refs = payload["paper_mission_transaction"]["artifact_delta_refs"]
    artifact_uris = [item["uri"] for item in artifact_refs]
    assert str(package_path) in idempotency_key
    assert str(old_package_ref) not in idempotency_key
    assert str(package_path.parent / "paper_facing_candidate_delta.json") in artifact_uris
    assert str(package_path.parent / "mission_candidate_artifact_delta.json") in (
        artifact_uris
    )
    assert str(package_path.parent / "owner_decision_packet.json") in artifact_uris
    assert str(old_package_ref.parent / "paper_facing_candidate_delta.json") not in (
        artifact_uris
    )
    assert payload["opl_runtime_carrier"]["idempotency_key"] == idempotency_key
    assert str(package_path) in payload["opl_runtime_carrier"][
        "attempt_idempotency_key"
    ]
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)


def test_paper_mission_consume_candidate_materializes_reviewer_revision_route(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    workspace_root = tmp_path / "workspace"
    mission_id = f"paper-mission::{study_id}::paper_mission_import::one-shot"
    package_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_candidate_package"
        / "external-sci-review"
        / study_id
    )
    package_root.mkdir(parents=True)
    action_matrix = (
        package_root
        / "paper_facing_candidate_artifacts"
        / "reviewer_action_matrix.json"
    )
    action_matrix.parent.mkdir(parents=True)
    action_matrix.write_text(
        json.dumps({"concerns": [{"id": "SCI-001", "severity": "major"}]}),
        encoding="utf-8",
    )
    owner_request = package_root / "owner_consumption_request.json"
    owner_request.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_owner_consumption_request",
                "requested_action": "consume_external_sci_registry_review_as_reviewer_revision",
                "recommended_next_route": "analysis-campaign_then_write",
            }
        ),
        encoding="utf-8",
    )
    package_path = package_root / "package_manifest.json"
    package_path.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_foreground_candidate_package_manifest",
                "schema_version": 1,
                "mode": "non_authority_candidate_package",
                "milestone_kind": "reviewer_revision_candidate",
                "candidate_content_kind": "external_high_quality_sci_review_intake",
                "study_id": study_id,
                "mission_id": mission_id,
                "candidate_is_authority": False,
                "source_readiness_refs": ["publication_eval/latest.json"],
                "quality_auditor_requirement": {
                    "independent_auditor_required": True,
                    "owner": "MedAutoScience",
                },
                "artifact_authority_boundary": {
                    "artifact_authority_owner": "MedAutoScience",
                    "candidate_is_authority": False,
                    "can_update_current_package": False,
                    "can_write_paper_body": False,
                },
                "artifact_refs": {
                    "reviewer_action_matrix": str(action_matrix),
                    "owner_consumption_request": str(owner_request),
                },
                "recommended_next_route": "analysis-campaign_then_write",
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_path),
            "--dry-run",
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
    assert payload["transaction_state"] == "reviewer_revision_candidate_ready"
    assert payload["next_action"]["action_kind"] == "submit_to_opl_runtime"
    assert (
        payload["next_action"]["authority_boundary"]["can_submit_to_opl_runtime"]
        is True
    )
    assert payload["next_action"]["work_unit_id"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["stage_terminal_decision"]["next_work_unit"] == (
        "ai_reviewer_medical_prose_quality_review"
    )
    assert payload["stage_terminal_decision"]["reviewer_revision_candidate_ref"] == (
        str(package_path)
    )
    assert str(action_matrix) in {
        item["uri"]
        for item in payload["paper_mission_transaction"]["artifact_delta_refs"]
    }
    assert payload["mutation_policy"]["writes_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)
