from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_materializer_selects_identity_different_current_owner_action_over_prior_typed_blocker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
            ),
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "stage_packet_not_current_selected_dispatch",
                    "owner": "one-person-lab",
                    "work_unit_id": "publication_gate_replay",
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "target_surface": {
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json"
            },
        },
        "current_owner_ticket": {
            "surface_kind": "mas_current_owner_ticket",
            "owner": "write",
            "allowed_action": "run_gate_clearing_batch",
            "work_unit": {
                "work_unit_id": "ai_reviewer_record_gate_consumption",
            },
            "target_surface": {
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        },
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "studies": [progress_payload],
            "action_queue": [],
        },
    )

    def read_progress(**_: object) -> dict[str, object]:
        return dict(progress_payload)

    monkeypatch.setattr(progress_module, "read_study_progress", read_progress)

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["request_task_count"] == 1
    assert result["default_executor_dispatch_count"] == 1
    assert result["request_tasks"][0]["action_type"] == "run_quality_repair_batch"
    assert result["request_tasks"][0]["authority"] == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    )
    assert result["default_executor_dispatches"][0]["dispatch_status"] == "dry_run"
    assert result["request_tasks"][0]["handoff_packet"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert (
        result["default_executor_dispatches"][0]["source_action"]["work_unit_id"]
        == "analysis_claim_evidence_repair"
    )
    assert (
        result["default_executor_dispatches"][0]["action_fingerprint"]
        == "publication-blockers::497d1260db522f01"
    )
