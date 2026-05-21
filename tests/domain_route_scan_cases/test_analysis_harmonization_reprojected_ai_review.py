from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _required_coverage() -> dict[str, object]:
    return {
        "uncertainty": {
            "metrics_95ci": {
                "c_index": {"estimate": 0.72, "lower": 0.61, "upper": 0.82},
                "observed_expected_ratio": {"estimate": 0.98, "lower": 0.74, "upper": 1.28},
                "brier_5y": {"estimate": 0.06, "lower": 0.04, "upper": 0.09},
            },
        },
        "calibration": {
            "calibration_intercept": {"ci_95": {"lower": -0.35, "upper": 0.04}},
            "calibration_slope": {"ci_95": {"lower": 0.66, "upper": 1.08}},
        },
        "grouped_calibration": {
            "groups": [
                {
                    "group": 1,
                    "n": 100,
                    "mean_predicted_5y_risk": 0.02,
                    "observed_5y_rate": 0.01,
                    "observed_5y_rate_ci_95": {"lower": 0.0, "upper": 0.03},
                }
            ]
        },
    }


def test_completed_unit_harmonized_rerun_rejects_reprojected_old_ai_reviewer_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
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
            "generated_at": "2026-05-21T20:49:54+00:00",
            **_required_coverage(),
        },
    )
    analysis_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    _write_json(
        analysis_path,
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "generated_at": "2026-05-21T20:49:54+00:00",
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(evidence_ref),
            "next_owner": "ai_reviewer",
            "next_work_unit": "ai_reviewer_medical_prose_quality_review",
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    publication_eval = {
        "schema_version": 1,
        "eval_id": (
            "publication-eval::002-dm-china-us-mortality-attribution::"
            "002-dm-china-us-mortality-attribution::2026-05-20T18:14:12+00:00"
        ),
        "emitted_at": "2026-05-21T20:50:57+00:00",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(analysis_path), str(evidence_ref)],
        },
        "quality_assessment": {
            "clinical_significance": {"status": "ready", "evidence_refs": [str(analysis_path)]},
            "evidence_strength": {"status": "partial", "evidence_refs": [str(evidence_ref)]},
            "novelty_positioning": {"status": "partial"},
            "medical_journal_prose_quality": {"status": "partial"},
            "human_review_readiness": {"status": "partial"},
        },
        "future_facing_limitations_plan": [
            {"limitation": "Old reviewer record predates the current rerun evidence."}
        ],
        "reviewer_operating_system": {
            "contract_id": "medical_publication_ai_reviewer_os_v1",
            "currentness_checks": {"unit_harmonized_rerun_evidence_consumed": True},
        },
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "analysis-campaign",
            "owner": "analysis-campaign",
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-reprojected-old-ai-review",
            "source_signature": "truth-source-dm002-reprojected-old-ai-review",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_runtime_supervision_gap",
        "paper_stage": "publishability_gate_blocked",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == [
        "return_to_ai_reviewer_workflow"
    ]
    action = study["action_queue"][0]
    assert action["reason"] == "analysis_harmonization_completed_ai_reviewer_review_required"
    assert action["required_currentness_refs"] == [str(analysis_path), str(evidence_ref)]
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
