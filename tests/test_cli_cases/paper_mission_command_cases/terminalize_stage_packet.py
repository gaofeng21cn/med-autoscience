from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.paper_mission_command_helpers import _write_profile_with_study


def test_terminalize_stage_uses_explicit_stage_packet_over_stale_consumption(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_id = "obesity_multicenter_phenotype_atlas"
    profile_path = _write_profile_with_study(tmp_path, study_id=study_id)
    stage_attempt_root = (
        tmp_path
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
    (tmp_path / route_back_ref).write_text(
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
            str(tmp_path / "ops" / "medautoscience" / "paper_mission_stage_closure"),
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
