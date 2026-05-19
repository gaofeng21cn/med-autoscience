from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_consumes_completed_unit_harmonized_rerun_without_requeue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [],
    }
    evidence_ref = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_json(
        evidence_ref,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "schema_version": 1,
            "status": "completed",
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "blocked_reason": None,
            "typed_blocker_owner": None,
            "typed_blocker": None,
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(evidence_ref),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_type": "bounded_analysis",
            "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
            "next_work_unit": {
                "unit_id": "unit_harmonized_external_validation_rerun",
                "selected_route_option": "rebuild_reproducible_model_route",
                "terminal_source_provenance_blocker_consumed": True,
                "clean_reproducible_model_rebuild_authorized": True,
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_user",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-hard-methodology",
            "source_signature": "truth-source-dm002-hard-methodology",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "state": "blocked",
            "blocked_reason": "domain_transition_ai_reviewer_re_eval",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    queued_actions = [action["action_type"] for action in study["action_queue"]]
    assert "unit_harmonized_external_validation_rerun" not in queued_actions
    assert "recover_transport_model_provenance" not in queued_actions
