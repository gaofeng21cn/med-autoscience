from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _complete_specificity_targets() -> list[dict[str, str]]:
    return [
        {
            "target_kind": "claim",
            "target_id": "primary_mortality_risk_claim",
            "source_path": "paper/claim_evidence_map.json",
            "blocking_reason": "Primary claim needs the exact unsupported endpoint named.",
        },
        {
            "target_kind": "figure",
            "target_id": "figure_2",
            "source_path": "paper/figures/figure_2.png",
            "blocking_reason": "Figure 2 legend and modeled endpoint are not aligned.",
        },
        {
            "target_kind": "table",
            "target_id": "table_1",
            "source_path": "paper/tables/table_1.csv",
            "blocking_reason": "Table 1 denominators are not traceable to the cohort definition.",
        },
        {
            "target_kind": "metric",
            "target_id": "c_statistic",
            "source_path": "artifacts/results/model_performance.json",
            "blocking_reason": "Discrimination metric is cited without a source path.",
        },
        {
            "target_kind": "source_path",
            "target_id": "external_validation_dataset",
            "source_path": "artifacts/results/external_validation.json",
            "blocking_reason": "External validation source path is missing from the gate blocker.",
        },
    ]


def test_supervisor_scan_stops_requeueing_specificity_when_gate_names_concrete_targets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    publication_eval = {
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::specificity",
                "action_type": "return_to_controller",
                "next_work_unit": {"unit_id": "gate_needs_specificity", "summary": "Name concrete targets."},
                "work_unit_fingerprint": "publication-blockers::same",
                "reason": "Publication gate names concrete blockers.",
                "specificity_targets": _complete_specificity_targets(),
            }
        ],
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "publication_gate_specificity_required",
            "execution_owner_guard": {"supervisor_only": True},
            "publication_eval": publication_eval,
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "quality_review_loop": {"closure_state": "open"},
            "control_plane_snapshot": {"blocking_reasons": ["publication_eval.ai_reviewer_required"]},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "publication_gate_specificity_required",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["gate_specificity"]["status"] == "specific_targets_present"
    assert study["gate_specificity"]["required"] is False
    assert study["gate_specificity"]["missing_target_kinds"] == []
    assert study["gate_specificity"]["covered_target_kinds"] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"


def test_supervisor_scan_keeps_specificity_queued_when_targets_lack_source_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    publication_eval = {
        "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::specificity",
                "action_type": "return_to_controller",
                "next_work_unit": {"unit_id": "gate_needs_specificity", "summary": "Name concrete targets."},
                "reason": "Publication gate names incomplete blockers.",
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "primary_mortality_risk_claim",
                        "blocking_reason": "Primary claim needs the exact unsupported endpoint named.",
                    }
                ],
            }
        ],
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_status": "stopped",
            "reason": "publication_gate_specificity_required",
            "publication_eval": publication_eval,
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_blocked",
            "quality_review_loop": {"closure_state": "open"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["gate_specificity"]["required"] is True
    assert study["gate_specificity"]["status"] == "blocked"
    assert study["gate_specificity"]["target_validation_error"] == (
        "publication eval specificity target source_path must be non-empty"
    )
    assert study["action_queue"][0]["action_type"] == "publication_gate_specificity_required"


def test_publication_gate_materialization_adds_concrete_specificity_targets(tmp_path: Path) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    (study_root / "artifacts" / "controller").mkdir(parents=True)
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    (study_root / "artifacts" / "controller" / "study_charter.json").write_text(
        (
            '{'
            '"charter_id":"charter-dm",'
            '"publication_objective":"Test publication objective."'
            '}'
        ),
        encoding="utf-8",
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-05T00:00:00+00:00",
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
            "figure_semantics_manifest_missing_or_incomplete",
            "submission_hardening_incomplete",
        ],
        "quest_id": "quest-dm",
        "paper_root": str(study_root / "paper"),
        "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "main_result_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
        "medical_publication_surface_report_path": str(study_root / "paper" / "medical_publication_surface.json"),
        "submission_minimal_manifest_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        "current_required_action": "return_to_publishability_gate",
        "controller_stage_note": "Publication gate must name concrete blockers.",
        "blocking_artifact_refs": [
            {
                "blocker": "claim_evidence_consistency_failed",
                "artifact_path": str(study_root / "paper" / "claim_evidence_map.json"),
                "artifact_role": "claim_evidence_map",
                "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
            },
            {
                "blocker": "figure_semantics_manifest_missing_or_incomplete",
                "artifact_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                "artifact_role": "figure_catalog",
                "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            },
        ],
    }

    result = decision_module._materialize_publication_eval_from_gate_report(
        study_root=study_root,
        study_id="001-dm-cvd-mortality-risk",
        quest_root=quest_root,
        quest_id="quest-dm",
        publication_gate_report=report,
    )

    assert result is not None
    payload = (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8")
    record = __import__("json").loads(payload)
    targets = record["recommended_actions"][0]["specificity_targets"]
    assert [item["target_kind"] for item in targets] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert all(item["source_path"] for item in targets)


def test_publication_gate_materialization_uses_default_metric_source_when_report_main_result_is_null(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    (study_root / "artifacts" / "controller").mkdir(parents=True)
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    (study_root / "artifacts" / "controller" / "study_charter.json").write_text(
        (
            "{"
            '"charter_id":"charter-dm",'
            '"publication_objective":"Test publication objective."'
            "}"
        ),
        encoding="utf-8",
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-05T00:00:00+00:00",
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
        ],
        "quest_id": "quest-dm",
        "paper_root": str(study_root / "paper"),
        "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "main_result_path": None,
        "medical_publication_surface_report_path": str(
            quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
        ),
        "submission_minimal_manifest_path": str(
            study_root / "paper" / "submission_minimal" / "submission_manifest.json"
        ),
        "current_required_action": "return_to_publishability_gate",
        "controller_stage_note": "Publication gate must name concrete blockers.",
        "blocking_artifact_refs": [
            {
                "blocker": "stale_submission_minimal_authority",
                "artifact_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
                "artifact_role": "submission_minimal_authority",
            },
            {
                "blocker": "submission_hardening_incomplete",
                "artifact_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
                "artifact_role": "submission_minimal_authority",
                "source_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
        ],
    }

    result = decision_module._materialize_publication_eval_from_gate_report(
        study_root=study_root,
        study_id="001-dm-cvd-mortality-risk",
        quest_root=quest_root,
        quest_id="quest-dm",
        publication_gate_report=report,
    )

    assert result is not None
    payload = (study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8")
    record = __import__("json").loads(payload)
    targets = record["recommended_actions"][0]["specificity_targets"]
    metric_targets = [item for item in targets if item["target_kind"] == "metric"]
    assert metric_targets == [
        {
            "target_kind": "metric",
            "target_id": "main_result_metrics",
            "source_path": str((quest_root / "artifacts" / "results" / "main_result.json").resolve()),
            "blocking_reason": "stale_submission_minimal_authority",
        }
    ]


def test_publication_gate_materialization_refreshes_blocked_bundle_targets_over_current_ai_reviewer_eval(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    charter_path.parent.mkdir(parents=True)
    charter_path.write_text(
        (
            "{"
            '"charter_id":"charter-dm",'
            '"publication_objective":"Test publication objective."'
            "}"
        ),
        encoding="utf-8",
    )
    eval_path.parent.mkdir(parents=True)
    eval_path.write_text(
        __import__("json").dumps(
            {
                "eval_id": "publication-eval::old-ai-reviewer",
                "study_id": "001-dm-cvd-mortality-risk",
                "quest_id": "quest-dm",
                "emitted_at": "2026-05-05T08:00:00+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "ready",
                        "summary": "Earlier AI reviewer prose assessment.",
                    }
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(study_root / "paper"),
                },
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::return_to_controller::publication-blockers::9ca1d64e0d39136a",
                        "action_type": "return_to_controller",
                        "priority": "now",
                        "reason": "AI reviewer evaluated the same blocked bundle gate fingerprint.",
                        "evidence_refs": [
                            str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                        ],
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "publication-blockers::9ca1d64e0d39136a",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-05T00:00:00+00:00",
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
        ],
        "quest_id": "quest-dm",
        "paper_root": str(study_root / "paper"),
        "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "main_result_path": None,
        "submission_minimal_manifest_path": str(
            study_root / "paper" / "submission_minimal" / "submission_manifest.json"
        ),
        "current_required_action": "complete_bundle_stage",
        "supervisor_phase": "bundle_stage_blocked",
        "controller_stage_note": "Bundle stage is currently blocked by concrete publication gate blockers.",
    }

    result = decision_module._materialize_publication_eval_from_gate_report(
        study_root=study_root,
        study_id="001-dm-cvd-mortality-risk",
        quest_root=quest_root,
        quest_id="quest-dm",
        publication_gate_report=report,
    )

    assert result is not None
    assert result["eval_id"] != "publication-eval::old-ai-reviewer"
    record = __import__("json").loads(eval_path.read_text(encoding="utf-8"))
    assert record["assessment_provenance"]["owner"] == "mechanical_projection"
    assert record["assessment_provenance"]["ai_reviewer_required"] is True
    assert [item["target_kind"] for item in record["recommended_actions"][0]["specificity_targets"]] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]


def test_publication_gate_materialization_preserves_current_ai_reviewer_eval_over_semantically_same_blocked_bundle_gate(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    charter_path.parent.mkdir(parents=True)
    charter_path.write_text(
        (
            "{"
            '"charter_id":"charter-dm",'
            '"publication_objective":"Test publication objective."'
            "}"
        ),
        encoding="utf-8",
    )
    eval_path.parent.mkdir(parents=True)
    eval_path.write_text(
        __import__("json").dumps(
            {
                "eval_id": "publication-eval::new-ai-reviewer",
                "study_id": "001-dm-cvd-mortality-risk",
                "quest_id": "quest-dm",
                "emitted_at": "2026-05-05T08:00:00+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "underdefined",
                        "summary": "AI reviewer evaluated the current blocked bundle gate.",
                    }
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(study_root / "paper"),
                },
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::return_to_controller::publication-blockers::9ca1d64e0d39136a",
                        "action_type": "return_to_controller",
                        "priority": "now",
                        "reason": "AI reviewer evaluated the same blocked bundle gate fingerprint.",
                        "evidence_refs": [
                            str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                        ],
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "publication-blockers::9ca1d64e0d39136a",
                        "specificity_targets": _complete_specificity_targets(),
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-05T08:01:00+00:00",
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
        ],
        "quest_id": "quest-dm",
        "paper_root": str(study_root / "paper"),
        "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "main_result_path": None,
        "submission_minimal_manifest_path": str(
            study_root / "paper" / "submission_minimal" / "submission_manifest.json"
        ),
        "current_required_action": "complete_bundle_stage",
        "supervisor_phase": "bundle_stage_blocked",
        "controller_stage_note": "Bundle stage is currently blocked by concrete publication gate blockers.",
    }

    result = decision_module._materialize_publication_eval_from_gate_report(
        study_root=study_root,
        study_id="001-dm-cvd-mortality-risk",
        quest_root=quest_root,
        quest_id="quest-dm",
        publication_gate_report=report,
    )

    assert result == {"eval_id": "publication-eval::new-ai-reviewer", "artifact_path": str(eval_path)}
    record = __import__("json").loads(eval_path.read_text(encoding="utf-8"))
    assert record["assessment_provenance"]["owner"] == "ai_reviewer"
    assert record["eval_id"] == "publication-eval::new-ai-reviewer"


def test_publication_gate_materialization_preserves_current_ai_reviewer_eval_over_return_to_publishability_gate(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    charter_path.parent.mkdir(parents=True)
    charter_path.write_text(
        (
            "{"
            '"charter_id":"charter-dm",'
            '"publication_objective":"Test publication objective."'
            "}"
        ),
        encoding="utf-8",
    )
    eval_path.parent.mkdir(parents=True)
    eval_path.write_text(
        __import__("json").dumps(
            {
                "eval_id": "publication-eval::dm002-ai-reviewer-current",
                "study_id": "001-dm-cvd-mortality-risk",
                "quest_id": "quest-dm",
                "emitted_at": "2026-05-05T08:00:00+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "underdefined",
                        "summary": "AI reviewer evaluated the current publishability gate work unit.",
                    }
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(study_root / "paper"),
                },
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::return_to_controller::publication-blockers::9ca1d64e0d39136a",
                        "action_type": "return_to_controller",
                        "priority": "now",
                        "reason": "AI reviewer evaluated the same publishability gate work-unit fingerprint.",
                        "evidence_refs": [
                            str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                        ],
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "publication-blockers::9ca1d64e0d39136a",
                        "specificity_targets": _complete_specificity_targets(),
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-05T08:01:00+00:00",
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
        ],
        "quest_id": "quest-dm",
        "paper_root": str(study_root / "paper"),
        "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "main_result_path": None,
        "submission_minimal_manifest_path": str(
            study_root / "paper" / "submission_minimal" / "submission_manifest.json"
        ),
        "current_required_action": "return_to_publishability_gate",
        "supervisor_phase": "publishability_gate_blocked",
        "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
        "controller_stage_note": "Return to publishability gate with concrete blockers.",
    }

    result = decision_module._materialize_publication_eval_from_gate_report(
        study_root=study_root,
        study_id="001-dm-cvd-mortality-risk",
        quest_root=quest_root,
        quest_id="quest-dm",
        publication_gate_report=report,
    )

    assert result == {"eval_id": "publication-eval::dm002-ai-reviewer-current", "artifact_path": str(eval_path)}
    record = __import__("json").loads(eval_path.read_text(encoding="utf-8"))
    assert record["assessment_provenance"]["owner"] == "ai_reviewer"
    assert record["eval_id"] == "publication-eval::dm002-ai-reviewer-current"


def test_publication_gate_materialization_force_refreshes_specificity_targets_over_ai_reviewer_eval(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    charter_path.parent.mkdir(parents=True)
    charter_path.write_text(
        (
            "{"
            '"charter_id":"charter-dm",'
            '"publication_objective":"Test publication objective."'
            "}"
        ),
        encoding="utf-8",
    )
    eval_path.parent.mkdir(parents=True)
    eval_path.write_text(
        __import__("json").dumps(
            {
                "eval_id": "publication-eval::current-ai-reviewer",
                "study_id": "001-dm-cvd-mortality-risk",
                "quest_id": "quest-dm",
                "emitted_at": "2026-05-05T08:00:00+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "underdefined",
                        "summary": "AI reviewer evaluated the current blocked bundle gate.",
                    }
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(study_root / "paper"),
                },
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::return_to_controller::publication-blockers::9ca1d64e0d39136a",
                        "action_type": "return_to_controller",
                        "priority": "now",
                        "reason": "AI reviewer evaluated the same blocked bundle gate fingerprint.",
                        "evidence_refs": [
                            str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                        ],
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "publication-blockers::9ca1d64e0d39136a",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-05T08:01:00+00:00",
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
        ],
        "quest_id": "quest-dm",
        "paper_root": str(study_root / "paper"),
        "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "main_result_path": None,
        "submission_minimal_manifest_path": str(
            study_root / "paper" / "submission_minimal" / "submission_manifest.json"
        ),
        "current_required_action": "complete_bundle_stage",
        "supervisor_phase": "bundle_stage_blocked",
        "controller_stage_note": "Bundle stage is currently blocked by concrete publication gate blockers.",
        "force_publication_gate_specificity_refresh": True,
    }

    result = decision_module._materialize_publication_eval_from_gate_report(
        study_root=study_root,
        study_id="001-dm-cvd-mortality-risk",
        quest_root=quest_root,
        quest_id="quest-dm",
        publication_gate_report=report,
    )

    assert result is not None
    assert result["eval_id"] != "publication-eval::current-ai-reviewer"
    record = __import__("json").loads(eval_path.read_text(encoding="utf-8"))
    assert record["assessment_provenance"]["owner"] == "mechanical_projection"
    assert [item["target_kind"] for item in record["recommended_actions"][0]["specificity_targets"]] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
