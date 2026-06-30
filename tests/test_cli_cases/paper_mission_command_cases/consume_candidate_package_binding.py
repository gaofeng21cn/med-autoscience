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
