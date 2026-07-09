from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.paper_mission_owner_surface_cases.owner_route_test_helpers import write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def _publication_eval_record(study_root: Path) -> dict:
    return json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))


def _write_charter(
    study_root: Path,
    *,
    charter_id: str = "charter-dm",
    publication_objective: str = "Test publication objective.",
) -> None:
    write_json(
        study_root / "artifacts" / "controller" / "study_charter.json",
        {
            "charter_id": charter_id,
            "publication_objective": publication_objective,
        },
    )


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


def _write_ai_reviewer_eval(
    eval_path: Path,
    *,
    study_root: Path,
    quest_root: Path,
    eval_id: str,
    summary: str,
    include_specificity_targets: bool = False,
    evidence_refs: list[Path] | None = None,
) -> None:
    action = {
        "action_id": "publication-eval-action::return_to_controller::publication-blockers::9ca1d64e0d39136a",
        "action_type": "return_to_controller",
        "priority": "now",
        "reason": summary,
        "evidence_refs": [
            str(ref)
            for ref in (
                evidence_refs
                or [quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"]
            )
        ],
        "requires_controller_decision": True,
        "work_unit_fingerprint": "publication-blockers::9ca1d64e0d39136a",
    }
    if include_specificity_targets:
        action["specificity_targets"] = _complete_specificity_targets()
    write_json(
        eval_path,
        {
            "eval_id": eval_id,
            "study_id": study_root.name,
            "quest_id": "quest-dm",
            "emitted_at": "2026-05-05T08:00:00+00:00",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": summary,
                }
            },
            "delivery_context_refs": {"paper_root_ref": str(study_root / "paper")},
            "recommended_actions": [action],
        },
    )


def test_scan_domain_routes_stops_requeueing_specificity_when_gate_names_concrete_targets(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
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
        module.domain_status_projection,
        "progress_projection",
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
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            module.domain_status_projection.progress_projection(),
            {
                "study_id": "001-dm-cvd-mortality-risk",
                "current_stage": "publication_supervision",
                "paper_stage": "publishability_gate_blocked",
                "quality_review_loop": {"closure_state": "open"},
                "authority_snapshot": {"blocking_reasons": ["publication_eval.ai_reviewer_required"]},
                "ai_repair_lifecycle": {
                    "state": "external_supervisor_required",
                    "blocked_reason": "publication_gate_specificity_required",
                    "external_supervisor_required": True,
                    "projection_only": True,
                },
            },
            "quest-dm",
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
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


def test_scan_domain_routes_keeps_specificity_queued_when_targets_lack_source_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.paper_mission_owner_surface")
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
        module.domain_status_projection,
        "progress_projection",
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
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            module.domain_status_projection.progress_projection(),
            {
                "study_id": "001-dm-cvd-mortality-risk",
                "current_stage": "publication_supervision",
                "paper_stage": "bundle_stage_blocked",
                "quality_review_loop": {"closure_state": "open"},
            },
            "quest-dm",
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
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
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(study_root)
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
    record = _publication_eval_record(study_root)
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
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(study_root)
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
    record = _publication_eval_record(study_root)
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
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(study_root)
    _write_ai_reviewer_eval(
        eval_path,
        study_root=study_root,
        quest_root=quest_root,
        eval_id="publication-eval::old-ai-reviewer",
        summary="AI reviewer evaluated the same blocked bundle gate fingerprint.",
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
    record = _publication_eval_record(study_root)
    assert record["assessment_provenance"]["owner"] == "mechanical_projection"
    assert record["assessment_provenance"]["ai_reviewer_required"] is True
    assert [item["target_kind"] for item in record["recommended_actions"][0]["specificity_targets"]] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]


def test_publication_gate_materialization_preserves_clean_cutover_ai_reviewer_blocked_eval(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "002-dm-china-us-mortality-attribution"
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "002-dm-china-us-mortality-attribution"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(
        study_root,
        charter_id="charter-dm002",
        publication_objective="Rebuild clean migrated paper authority.",
    )
    write_json(
        eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::clean-cutover-ai-reviewer",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "emitted_at": "2026-05-17T12:00:00+00:00",
            "evaluation_scope": "publication",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            },
            "verdict": {"overall_verdict": "blocked"},
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
            "recommended_actions": [
                {
                    "action_id": "paper-authority-clean-migration-rebuild",
                    "action_type": "return_to_controller",
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-17T12:01:00+00:00",
        "status": "clear",
        "blockers": [],
        "quest_id": "002-dm-china-us-mortality-attribution",
        "paper_root": str(study_root / "paper"),
        "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
        "main_result_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
        "submission_minimal_manifest_path": str(
            study_root / "paper" / "submission_minimal" / "submission_manifest.json"
        ),
        "current_required_action": "continue_bundle_stage",
        "supervisor_phase": "bundle_stage_ready",
        "force_publication_gate_specificity_refresh": True,
    }

    result = decision_module._materialize_publication_eval_from_gate_report(
        study_root=study_root,
        study_id="002-dm-china-us-mortality-attribution",
        quest_root=quest_root,
        quest_id="002-dm-china-us-mortality-attribution",
        publication_gate_report=report,
    )

    assert result["eval_id"] == "publication-eval::clean-cutover-ai-reviewer"
    record = _publication_eval_record(study_root)
    assert record["assessment_provenance"]["owner"] == "ai_reviewer"
    assert record["verdict"]["overall_verdict"] == "blocked"


def test_publication_gate_materialization_preserves_current_ai_reviewer_eval_over_semantically_same_blocked_bundle_gate(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(study_root)
    _write_ai_reviewer_eval(
        eval_path,
        study_root=study_root,
        quest_root=quest_root,
        eval_id="publication-eval::new-ai-reviewer",
        summary="AI reviewer evaluated the same blocked bundle gate fingerprint.",
        include_specificity_targets=True,
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

    assert result["eval_id"] == "publication-eval::new-ai-reviewer"
    record = _publication_eval_record(study_root)
    assert record["assessment_provenance"]["owner"] == "ai_reviewer"
    assert record["eval_id"] == "publication-eval::new-ai-reviewer"


def test_publication_gate_materialization_preserves_current_ai_reviewer_eval_over_return_to_publishability_gate(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(study_root)
    _write_ai_reviewer_eval(
        eval_path,
        study_root=study_root,
        quest_root=quest_root,
        eval_id="publication-eval::dm002-ai-reviewer-current",
        summary="AI reviewer evaluated the same publishability gate work-unit fingerprint.",
        include_specificity_targets=True,
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

    assert result["eval_id"] == "publication-eval::dm002-ai-reviewer-current"
    record = _publication_eval_record(study_root)
    assert record["assessment_provenance"]["owner"] == "ai_reviewer"
    assert record["eval_id"] == "publication-eval::dm002-ai-reviewer-current"


def test_publication_gate_materialization_force_refreshes_specificity_targets_over_ai_reviewer_eval(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(study_root)
    _write_ai_reviewer_eval(
        eval_path,
        study_root=study_root,
        quest_root=quest_root,
        eval_id="publication-eval::current-ai-reviewer",
        summary="AI reviewer evaluated the same blocked bundle gate fingerprint.",
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
    record = _publication_eval_record(study_root)
    assert record["assessment_provenance"]["owner"] == "mechanical_projection"
    assert [item["target_kind"] for item in record["recommended_actions"][0]["specificity_targets"]] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]


def test_publication_gate_materialization_preserves_clean_cutover_ai_reviewer_eval(
    tmp_path: Path,
) -> None:
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision.publication_and_submission")
    study_root = tmp_path / "workspace" / "studies" / "001-dm-cvd-mortality-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-dm"
    eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    receipt_path = study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "latest.json"
    (quest_root / "artifacts" / "reports" / "publishability_gate").mkdir(parents=True)
    _write_charter(study_root)
    _write_ai_reviewer_eval(
        eval_path,
        study_root=study_root,
        quest_root=quest_root,
        eval_id="publication-eval::current-clean-cutover-ai-reviewer",
        summary="Rerun publication gate and delivery sync after clean migration.",
        evidence_refs=[receipt_path],
    )
    write_json(
        receipt_path,
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "new_mas_authority_established",
            "study_id": "001-dm-cvd-mortality-risk",
            "new_mas_authority": {
                "owner": "ai_reviewer",
                "publication_eval_ref": str(eval_path),
                "eval_id": "publication-eval::current-clean-cutover-ai-reviewer",
            },
        },
    )
    report = {
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-17T08:01:00+00:00",
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

    assert result["eval_id"] == "publication-eval::current-clean-cutover-ai-reviewer"
    record = _publication_eval_record(study_root)
    assert record["assessment_provenance"]["owner"] == "ai_reviewer"
    assert record["eval_id"] == "publication-eval::current-clean-cutover-ai-reviewer"
