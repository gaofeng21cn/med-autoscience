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
            "method": "nonparametric_bootstrap_fixed_model_external_validation",
            "replicates": 200,
            "metrics_95ci": {
                "c_index": {"estimate": 0.72, "lower": 0.61, "upper": 0.82},
                "observed_expected_ratio": {"estimate": 0.98, "lower": 0.74, "upper": 1.28},
                "brier_5y": {"estimate": 0.06, "lower": 0.04, "upper": 0.09},
            },
        },
        "calibration": {
            "calibration_intercept": {"estimate": -0.12, "ci_95": {"lower": -0.35, "upper": 0.04}},
            "calibration_slope": {"estimate": 0.88, "ci_95": {"lower": 0.66, "upper": 1.08}},
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


def test_completed_unit_harmonized_rerun_without_surface_routes_stale_ai_reviewer_eval_back_to_review(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::pre-harmonization-review",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "future_facing_limitations_plan": [{"limitation": "External validation uncertainty remains open."}],
    }
    evidence_ref, analysis_path = _write_completed_analysis_result(study_root, include_surface=False)
    status_payload, progress_payload = _projection_inputs(
        study_root=study_root,
        quest_root=quest_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval=publication_eval,
    )
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

    action = result["studies"][0]["action_queue"][0]
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["reason"] == "analysis_harmonization_completed_ai_reviewer_review_required"
    assert action["source_ref"] == str(analysis_path)
    assert action["required_currentness_refs"] == [str(analysis_path), str(evidence_ref)]


def test_completed_unit_harmonized_rerun_preempts_stale_ai_reviewer_write_routeback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    evidence_ref, analysis_path = _write_completed_analysis_result(
        study_root,
        include_surface=True,
        generated_at="2026-06-02T09:57:37+00:00",
    )
    publication_eval = _stale_ai_reviewer_write_routeback_eval(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        analysis_path=analysis_path,
        evidence_ref=evidence_ref,
    )
    status_payload, progress_payload = _projection_inputs(
        study_root=study_root,
        quest_root=quest_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval=publication_eval,
    )
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
    action = study["action_queue"][0]
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["owner"] == "ai_reviewer"
    assert action["reason"] == "analysis_harmonization_completed_ai_reviewer_review_required"
    assert action["source_ref"] == str(analysis_path)
    assert action["required_currentness_refs"] == [str(analysis_path), str(evidence_ref)]
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def _write_completed_analysis_result(
    study_root: Path,
    *,
    include_surface: bool,
    generated_at: str | None = None,
) -> tuple[Path, Path]:
    evidence_ref = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    evidence_payload = {
        "surface": "unit_harmonized_external_validation_rerun_evidence",
        "schema_version": 1,
        "status": "completed",
        **_required_coverage(),
        "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
    }
    if generated_at is not None:
        evidence_payload["generated_at"] = generated_at
    _write_json(evidence_ref, evidence_payload)
    analysis_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    analysis_payload = {
        "schema_version": 1,
        "study_id": "002-dm-china-us-mortality-attribution",
        "owner": "analysis_harmonization_owner",
        "work_unit": "unit_harmonized_external_validation_rerun",
        "status": "completed",
        "unit_harmonized_rerun_completed": True,
        "rerun_evidence_ref": str(evidence_ref),
        "next_owner": "ai_reviewer",
        "next_work_unit": "ai_reviewer_medical_prose_quality_review",
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "medical_claim_authoring_allowed": False,
        "publication_eval_written": False,
        "controller_decision_written": False,
    }
    if include_surface:
        analysis_payload["surface"] = "analysis_harmonization_owner_result"
    if generated_at is not None:
        analysis_payload["generated_at"] = generated_at
    _write_json(analysis_path, analysis_payload)
    return evidence_ref, analysis_path


def _projection_inputs(
    *,
    study_root: Path,
    quest_root: Path,
    study_id: str,
    quest_id: str,
    publication_eval: dict,
) -> tuple[dict, dict]:
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
            "truth_epoch": "truth-epoch-dm002-analysis-currentness",
            "source_signature": "truth-source-dm002-analysis-currentness",
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
    }
    return status_payload, progress_payload


def _stale_ai_reviewer_write_routeback_eval(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    analysis_path: Path,
    evidence_ref: Path,
) -> dict:
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::stale-write-routeback::20260602T082805Z",
        "emitted_at": "2026-06-02T08:28:05+00:00",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
            "source_refs": [str(analysis_path), str(evidence_ref)],
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request-current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(study_root / "paper" / "draft.md"),
                    "manuscript_digest": "sha256:manuscript-current",
                },
            }
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "reason": "Consume the current AI reviewer record and route the paper back to write.",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "consume_current_ai_reviewer_record_then_prose_gate_package_replay"
                ),
                "next_work_unit": {
                    "unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
                    "lane": "write",
                    "summary": (
                        "Consume the current AI reviewer record, refresh prose currentness, "
                        "and replay package gates."
                    ),
                },
            }
        ],
    }
