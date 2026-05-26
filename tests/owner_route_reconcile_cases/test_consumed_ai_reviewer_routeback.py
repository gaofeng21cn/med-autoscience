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


def test_consumed_ai_reviewer_receipt_routes_owner_route_to_write(
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
            **_required_coverage(),
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
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
        "eval_id": "publication-eval::dm002::post-harmonization-write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {"trace_id": "ai-reviewer-os::post-harmonization"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "recommended_actions": [
            {
                "action_id": "dm002-current-ai-reviewer-write-pass",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "dm002_current_manuscript_write_pass",
                "next_work_unit": {
                    "unit_id": "dm002_current_manuscript_write_pass",
                    "lane": "write",
                    "summary": "Repair current AI reviewer manuscript findings.",
                },
            }
        ],
    }
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": "artifacts/publication_eval/latest.json",
        "eval_id": publication_eval["eval_id"],
        "reviewer_trace_ref": "artifacts/publication_eval/latest.json#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    domain_transition = {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "next_work_unit": {
            "unit_id": "dm002_current_manuscript_write_pass",
            "lane": "write",
            "summary": "Repair current AI reviewer manuscript findings.",
        },
        "controller_action": "request_opl_stage_attempt",
        "owner": "write",
        "typed_blocker": None,
        "guard_boundary": {
            "runner_boundary": "mas_domain_read_model_only",
            "required_owner_surface": "artifacts/publication_eval/latest.json",
        },
        "source_refs": ["artifacts/publication_eval/latest.json", str(analysis_path), str(evidence_ref)],
        "completion_receipt_consumption": completion_receipt_consumption,
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": domain_transition,
        "runtime_health_snapshot": {
            "attempt_state": "recovering",
            "canonical_runtime_action": "recover_runtime",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-consumed-ai-reviewer-write",
            "source_signature": "truth-source-dm002-consumed-ai-reviewer-write",
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
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "state": "blocked",
            "authority": "external_supervisor",
            "auto_apply_allowed": True,
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "top_action": {
                "action_type": "controller_repair",
                "owner": "mas_controller",
                "repair_kind": "analysis_claim_evidence_redrive",
                "auto_apply_allowed": True,
            },
        },
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
    assert study["domain_transition"]["completion_receipt_consumption"] == completion_receipt_consumption
    assert study["ai_reviewer_status"]["status"] == "present"
    assert study["ai_repair_lifecycle"] is None
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    assert study["action_queue"][0]["owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert study["blocked_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert study["why_not_applied"] == "opl_stage_attempt_admission_required"


def test_consumed_ai_reviewer_receipt_clears_stale_analysis_reviewer_lifecycle_in_observe_mode(
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
        "eval_id": "publication-eval::dm002::post-harmonization-observe-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {"trace_id": "ai-reviewer-os::post-harmonization-observe"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
    }
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": "artifacts/publication_eval/latest.json",
        "eval_id": publication_eval["eval_id"],
        "reviewer_trace_ref": "artifacts/publication_eval/latest.json#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    domain_transition = {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "next_work_unit": {
            "unit_id": "dm002_current_manuscript_write_pass",
            "lane": "write",
            "summary": "Repair current AI reviewer manuscript findings.",
        },
        "controller_action": "request_opl_stage_attempt",
        "owner": "write",
        "typed_blocker": None,
        "guard_boundary": {"required_owner_surface": "artifacts/publication_eval/latest.json"},
        "source_refs": ["artifacts/publication_eval/latest.json"],
        "completion_receipt_consumption": completion_receipt_consumption,
    }
    stale_lifecycle = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "state": "blocked",
        "blocked_reason": "analysis_harmonization_completed_ai_reviewer_review_required",
        "next_owner": "ai_reviewer",
        "external_supervisor_required": False,
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": domain_transition,
        "runtime_health_snapshot": {
            "attempt_state": "recovering",
            "canonical_runtime_action": "recover_runtime",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-consumed-ai-reviewer-observe",
            "source_signature": "truth-source-dm002-consumed-ai-reviewer-observe",
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
        "ai_repair_lifecycle": stale_lifecycle,
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["ai_repair_lifecycle"] is None
    assert study["owner_route"]["next_owner"] == "one-person-lab"
    assert study["owner_route"]["owner_reason"] == "opl_stage_attempt_admission_required"
    assert study["blocked_reason"] == "opl_stage_attempt_admission_required"
    assert study["why_not_applied"] == "opl_stage_attempt_admission_required"
