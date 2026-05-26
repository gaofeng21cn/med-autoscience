from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.upstream_paper_owner_surface import (
    _paper_write_supervisor_route_context,
    _write_blocked_publication_eval,
    _write_json,
    _write_quality_summary,
)


@pytest.mark.parametrize(
    ("work_unit_id", "work_unit_fingerprint"),
    [
        (
            "dm002_same_line_publication_paper_repair",
            "dm002_same_line_publication_paper_repair_20260521",
        ),
        (
            "dm002_same_line_methods_display_package_repair",
            "domain-transition::route_back_same_line::dm002_same_line_methods_display_package_repair",
        ),
        (
            "dm002_same_line_display_table_package_repair",
            "domain-transition::route_back_same_line::dm002_same_line_display_table_package_repair",
        ),
        (
            "dm002_current_publication_hardening_after_ai_reviewer_eval",
            "dm002_current_ai_reviewer_publication_hardening_live_draft_f93aae_20260522T203041Z",
        ),
        (
            "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            "dm002_current_ai_reviewer_publication_eval_live_draft_2dcd51592c6a_20260524T175827Z",
        ),
        (
            "dm002_current_manuscript_reporting_consistency_write_repair",
            "domain-transition::route_back_same_line::dm002_current_manuscript_reporting_consistency_write_repair",
        ),
    ],
)
def test_dm002_publication_paper_repair_updates_external_validation_manuscript(
    monkeypatch: Any,
    tmp_path: Path,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm-china-us-mortality-attribution",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="mortality_attribution",
    )
    quest_id = "quest-002"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nOutdated external-validation draft surface.\n", encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _write_dm002_rerun_evidence(study_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "route_key_question": "Repair current external-validation manuscript findings.",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": "write",
                "summary": "Repair DM002 as a clean external-validation paper.",
            },
        }
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked", "reviewer_first_concerns_unresolved"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::dm002-medical-prose",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "selected_publication_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            "explicit_publication_work_unit": {
                "unit_id": work_unit_id,
                "lane": "write",
            },
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "unit_results": [],
        },
    )
    route_context = {
        **_paper_write_supervisor_route_context(),
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": work_unit_fingerprint,
        },
    }

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=route_context,
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert "writer_worker_handoff" not in result
    evidence = result["repair_execution_evidence"]
    assert evidence["repair_work_unit"]["unit_id"] == work_unit_id
    assert evidence["status"] == "progress_delta_candidate"
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_required"] is True
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is True
    changed_paths = {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in evidence["canonical_artifact_delta"]["artifact_refs"]
    }
    assert "paper/draft.md" in changed_paths
    assert "paper/build/review_manuscript.md" in changed_paths
    assert "paper/tables/generated/T2_time_to_event_performance_summary.md" in changed_paths
    story_text = (paper_root / "draft.md").read_text(encoding="utf-8")
    assert "External validation of a China-derived diabetes mortality score in NHANES" in story_text
    assert "15,789" in story_text
    assert "321" in story_text
    assert "5,659" in story_text
    assert "704" in story_text
    assert "0.734 (95% CI 0.714-0.757)" in story_text
    assert "12.44% (95% CI 11.68%-13.17%)" in story_text
    assert "2.33% (95% CI 2.33%-2.35%)" in story_text
    assert "O:E ratio was 5.33 (95% CI 5.02-5.65)" in story_text
    assert "Brier score was 0.118 (95% CI 0.111-0.125)" in story_text
    assert "calibration slope was 5.64 (95% CI 5.09-6.19)" in story_text
    assert "calibration intercept was 1.79 (95% CI 1.71-1.87)" in story_text
    assert "decile 1" in story_text
    assert "decile 10" in story_text
    assert "HDL cholesterol was converted from mg/dL to mmol/L using 0.02586" in story_text
    assert "nonparametric bootstrap replicates" in story_text
    assert "lifelines 0.30.3" in story_text
    assert "unweighted NHANES" in story_text
    assert "10.11 percentage points" in story_text
    assert "age, sex, smoking status, HbA1c, HDL cholesterol, systolic blood pressure, and diastolic blood pressure" in story_text
    assert "hdl_mmol_l" not in story_text
    assert "% percentage points" not in story_text
    table2_text = (
        paper_root / "tables" / "generated" / "T2_time_to_event_performance_summary.md"
    ).read_text(encoding="utf-8")
    assert "| C-index | 0.760 | 0.734 (95% CI 0.714-0.757) |" in table2_text
    assert "| Observed-to-expected ratio | 1.00 | 5.33 (95% CI 5.02-5.65) |" in table2_text
    assert "| Brier score | 0.019 | 0.118 (95% CI 0.111-0.125) |" in table2_text
    assert "| Calibration intercept | Not estimated | 1.79 (95% CI 1.71-1.87) |" in table2_text
    assert "| Calibration slope | Not estimated | 5.64 (95% CI 5.09-6.19) |" in table2_text
    assert "interval estimates for O/E ratio and Brier score" not in table2_text
    assert "calibration slope" not in table2_text.lower().split("metrics not available", 1)[-1]
    forbidden_runtime_terms = (
        "MAS",
        "AI reviewer",
        "verified outputs",
        "accepted records",
        "source gaps",
        "submission readiness",
        "repair note",
        "manuscript repair",
        "quality repair",
        "publication gate",
        "controller",
        "raw-scale",
        "preprocessing error",
    )
    assert not any(term in story_text for term in forbidden_runtime_terms)
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == story_text
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (paper_root / "submission_minimal").exists()


def _write_dm002_rerun_evidence(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "unit_harmonized_external_validation_rerun.json",
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "schema_version": 1,
            "status": "completed",
            "model": {
                "model_family": "clean_rebuild_penalized_cox_ph",
                "duration_col": "os_time",
                "event_col": "os_event",
                "feature_order": ["Age", "Sex", "Smoke", "HbA1c", "hdl_mmol_l", "SBP", "DBP"],
                "baseline_survival_at_5y": 0.980658000724163,
                "software": {
                    "python_packages": {
                        "lifelines": "0.30.3",
                        "numpy": "2.4.4",
                        "pandas": "2.3.3",
                    }
                },
            },
            "hdl_unit_handling": {
                "china_input_hdl_unit": "mmol/L",
                "nhanes_raw_hdl_unit": "mg/dL",
                "nhanes_model_hdl_unit": "mmol/L",
                "mg_dl_to_mmol_l_factor": 0.02586,
            },
            "cohorts": {
                "china": {"n": 15789, "events": 321},
                "nhanes": {"n": 5659, "events": 704},
            },
            "comparison": {
                "china_development": {
                    "n": 15789,
                    "events": 321,
                    "events_within_horizon": 309,
                    "c_index": 0.7599854745055089,
                    "mean_predicted_5y_risk": 0.019599702325312857,
                    "observed_5y_rate": 0.019570587117613527,
                    "observed_expected_ratio": 0.9985145076585308,
                    "brier_5y": 0.01906629863762726,
                    "predicted_minus_observed_5y_risk": 0.000029115207699329654,
                },
                "unit_harmonized_nhanes": {
                    "n": 5659,
                    "events": 704,
                    "events_within_horizon": 704,
                    "c_index": 0.7339238095812027,
                    "mean_predicted_5y_risk": 0.02334524823555533,
                    "observed_5y_rate": 0.12440360487718678,
                    "observed_expected_ratio": 5.328861943207669,
                    "brier_5y": 0.1183137082995992,
                },
            },
            "uncertainty": {
                "method": "nonparametric_bootstrap_fixed_model_external_validation",
                "replicates": 200,
                "random_seed": 20260521,
                "metrics_95ci": {
                    "c_index": {
                        "estimate": 0.7339238095812027,
                        "lower": 0.7136005734658573,
                        "upper": 0.7570014837925402,
                    },
                    "mean_predicted_5y_risk": {
                        "estimate": 0.02334524823555533,
                        "lower": 0.023254250634213474,
                        "upper": 0.023453616648824744,
                    },
                    "observed_5y_rate": {
                        "estimate": 0.12440360487718678,
                        "lower": 0.1167962537550804,
                        "upper": 0.13167078989220712,
                    },
                    "observed_expected_ratio": {
                        "estimate": 5.328861943207669,
                        "lower": 5.0183840729013225,
                        "upper": 5.651435725369566,
                    },
                    "brier_5y": {
                        "estimate": 0.1183137082995992,
                        "lower": 0.11109170307405553,
                        "upper": 0.1251732493863354,
                    },
                },
            },
            "calibration": {
                "method": "horizon_logistic_calibration_fixed_predictions",
                "calibration_intercept": {
                    "estimate": 1.785961064431998,
                    "ci_95": {"lower": 1.706863968638565, "upper": 1.8650581602254312},
                },
                "calibration_slope": {
                    "estimate": 5.636254585329421,
                    "ci_95": {"lower": 5.08518851503234, "upper": 6.187320655626501},
                },
            },
            "grouped_calibration": {
                "method": "risk_quantile_groups_with_wilson_intervals",
                "group_count": 10,
                "groups": [
                    {
                        "group": 1,
                        "n": 566,
                        "mean_predicted_5y_risk": 0.016129469961225135,
                        "observed_5y_events": 13,
                        "observed_5y_rate": 0.022968197879858657,
                        "observed_5y_rate_ci_95": {
                            "lower": 0.013470882925079992,
                            "upper": 0.038897354142905224,
                        },
                    },
                    {
                        "group": 10,
                        "n": 565,
                        "mean_predicted_5y_risk": 0.030835628503751072,
                        "observed_5y_events": 214,
                        "observed_5y_rate": 0.3787610619469027,
                        "observed_5y_rate_ci_95": {
                            "lower": 0.3397082045230421,
                            "upper": 0.41945146312433107,
                        },
                    },
                ],
            },
        },
    )
