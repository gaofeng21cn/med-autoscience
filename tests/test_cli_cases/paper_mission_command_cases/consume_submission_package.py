from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import *  # noqa: F401,F403


def test_paper_mission_consume_candidate_accepts_submission_package_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "002-dm-china-us-mortality-attribution"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    mission_id = f"paper-mission::{study_id}::gate-clearing::route-back"
    transaction = _paper_mission_transaction_payload(
        mission_id=mission_id,
        study_id=study_id,
        decision_kind="route_back",
    )
    package_root = tmp_path / "candidate-package" / study_id
    package_root.mkdir(parents=True)
    candidate_manifest = {
        "candidate_id": "paper-mission-candidate::dm002::submission",
        "mission_id": mission_id,
        "study_id": study_id,
        "requested_outcome": "accepted_candidate",
        "candidate_manifest_ref": str(package_root / "candidate_manifest.json"),
        "candidate_artifact_refs": [
            str(package_root / "paper_facing_candidate_delta.json"),
        ],
        "source_readiness_refs": ["source-readiness:dm002"],
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
        "next_owner": "mission_executor",
        "resume_condition": "MAS consumes or routes back the milestone package",
        "paper_mission_transaction": transaction,
    }
    (package_root / "candidate_manifest.json").write_text(
        json.dumps(candidate_manifest),
        encoding="utf-8",
    )
    package_manifest = {
        "surface_kind": "paper_mission_foreground_candidate_package_manifest",
        "schema_version": 1,
        "mode": "non_authority_candidate_package",
        "milestone_kind": "submission_milestone_candidate",
        "study_id": study_id,
        "mission_id": mission_id,
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_current_package": False,
        "can_claim_owner_receipt_written": False,
        "artifact_refs": {
            "candidate_manifest": str(package_root / "candidate_manifest.json"),
            "paper_facing_candidate_delta": str(
                package_root / "paper_facing_candidate_delta.json"
            ),
            "owner_decision_packet": str(package_root / "owner_decision_packet.json"),
        },
        "paper_facing_candidate_delta_ref": str(
            package_root / "paper_facing_candidate_delta.json"
        ),
        "owner_consumption_request_ref": str(
            package_root / "owner_consumption_request.json"
        ),
        "owner_blocker_packet_ref": str(package_root / "owner_blocker_packet.json"),
        "forbidden_authority_writes": ["owner receipt", "typed blocker"],
        "forbidden_authority_claims": ["submission_ready"],
    }
    package_manifest_path = package_root / "package_manifest.json"
    package_manifest_path.write_text(json.dumps(package_manifest), encoding="utf-8")
    output_root = tmp_path / "consumption-ledger"

    exit_code = cli.main(
        [
            "paper-mission",
            "consume-candidate",
            "--candidate",
            str(package_manifest_path),
            "--output-root",
            str(output_root),
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
    assert payload["authority_consume_readback"]["status"] == "accepted_candidate"
    assert payload["authority_consume_readback"]["candidate_id"] == (
        "paper-mission-candidate::dm002::submission"
    )
    assert payload["authority_consume_readback"]["candidate_manifest_input"][
        "resolved_manifest_ref"
    ] == str(package_root / "candidate_manifest.json")
    assert payload["paper_mission_transaction_readback"]["source"] == (
        "candidate_manifest"
    )
    assert payload["transaction_state"] == "terminal_decision_recorded"
    assert payload["opl_route_command"]["command_kind"] == "route_back"
    assert payload["consume_output_manifest"]["mode"] == "governed_consume_record"
    assert payload["consume_output_manifest"]["route_command_kind"] == "route_back"
    assert payload["consume_output_manifest"]["writes_authority"] is False
    assert payload["consume_output_manifest"]["writes_runtime"] is False
    assert payload["consume_output_manifest"]["writes_yang_authority"] is False
    _assert_forbidden_authority_untouched(tmp_path, study_id=study_id)
