from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.quality_repair_batch_parts import (
    medical_prose_story_surface,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.upstream_paper_owner_surface import (
    _paper_write_supervisor_route_context,
    _write_blocked_publication_eval,
    _write_quality_summary,
)


DM002_CURRENT_WORK_UNIT = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fingerprint(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"size": len(data), "content_sha256": hashlib.sha256(data).hexdigest()}


def _previous_blocked_batch(
    *,
    source_eval_id: str,
    surface_refs: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_eval_id": source_eval_id,
        "status": "handoff_ready",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "repair_execution_evidence": {
            "status": "blocked",
            "blockers": ["manuscript_story_surface_delta_missing"],
            "manuscript_surface_hygiene": {
                "status": "blocked",
                "surface_refs": list(surface_refs),
                "story_surface_delta_required": True,
                "story_surface_delta_present": False,
                "story_surface_delta_refs": [],
            },
        },
    }


def _dm002_writer_story() -> str:
    return "\n\n".join(
        [
            "# External validation of a China-derived diabetes mortality score in NHANES",
            "## Abstract",
            "**Background:** Mortality scores transported across diabetes populations require separate assessment of ranking and absolute calibration.",
            "**Methods:** A fixed seven-predictor Cox model developed in 15,789 Chinese adults with diabetes was applied to 5,659 NHANES adults with diagnosed diabetes. The validation analysis used complete shared predictors, converted HDL cholesterol to mmol/L, and estimated discrimination, observed 5-year mortality, mean predicted risk, observed-to-expected ratio, Brier score, logistic calibration, and grouped calibration with 95% confidence intervals from bootstrap or Wilson methods.",
            "**Results:** The China cohort had 321 deaths, including 309 within 5 years. NHANES had 704 deaths within 5 years. The NHANES c-index was 0.734 (95% CI 0.714-0.757), observed 5-year mortality was 12.44% (95% CI 11.68%-13.17%), mean predicted risk was 2.33% (95% CI 2.33%-2.35%), and the observed-to-expected ratio was 5.33 (95% CI 5.02-5.65).",
            "**Conclusions:** The score retained moderate risk ordering but substantially underpredicted absolute mortality, so population-specific recalibration is required before absolute-risk use.",
            "## Introduction",
            "Diabetes mortality prediction models can rank patients in one setting and still miscalibrate when transported to another population. External validation should therefore report discrimination and calibration as distinct clinical properties.",
            "## Methods",
            "### Data sources and participants",
            "The development source was a China diabetes cohort, and the validation source was NHANES adults with diagnosed diabetes. The unweighted NHANES analysis describes the retained validation sample rather than national prevalence.",
            "### Variables and missing data",
            "Predictors were age, sex, smoking status, HbA1c, HDL cholesterol, systolic blood pressure, and diastolic blood pressure. Complete records for shared predictors, survival time, and event status were used; missing values were not imputed.",
            "### Prediction model and statistical analysis",
            "The fixed Cox proportional hazards model was evaluated at 5 years. Statistical analysis reported c-index, observed and predicted 5-year risk, observed-to-expected ratio, Brier score, logistic calibration intercept and slope, grouped calibration, bootstrap 95% confidence intervals, and Wilson intervals for grouped observed rates.",
            "## Results",
            "NHANES preserved moderate discrimination but showed severe absolute underprediction. The calibration intercept was 1.79 (95% CI 1.71-1.87), the calibration slope was 5.64 (95% CI 5.09-6.19), and the cohort-level calibration gap was 10.11 percentage points.",
            "## Discussion",
            "The main finding is transportable risk ordering with poor absolute calibration. Clinically, the model should support ranking or prioritization research only after local recalibration, not direct absolute-risk counseling.",
            "## Limitations",
            "The analysis used complete cases and an unweighted NHANES validation sample. Transportability may differ in survey-weighted, care-setting-specific, or prospectively recalibrated populations.",
            "## Conclusion",
            "A China-derived diabetes mortality score retained moderate risk ordering in NHANES but substantially underestimated absolute 5-year mortality.",
        ]
    ) + "\n"


def _write_dm002_template_inputs(study_root: Path) -> None:
    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json",
        {
            "schema_version": 1,
            "status": "completed",
            "model": {
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
            "hdl_unit_handling": {"mg_dl_to_mmol_l_factor": 0.02586},
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


def _write_minimal_paper_surfaces(paper_root: Path) -> None:
    for relative_path in (
        "claim_evidence_map.json",
        "evidence_ledger.json",
        "medical_manuscript_blueprint.json",
        "medical_prose_review.json",
        "results_narrative_map.json",
        "figure_semantics_manifest.json",
        "figures/figure_catalog.json",
        "tables/table_catalog.json",
    ):
        _write_json(paper_root / relative_path, {"schema_version": 1})


def _bind_publication_eval_to_current_manuscript(
    publication_eval_payload: dict[str, Any],
    *,
    paper_root: Path,
    manuscript_digest: str,
) -> dict[str, Any]:
    publication_eval_payload["reviewer_operating_system"] = {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": {"manuscript": str((paper_root / "draft.md").resolve())},
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_ref": str((paper_root.parent / "artifacts" / "publication_eval" / "medical_prose_review_request.json").resolve()),
                "request_digest": "sha256:" + "b" * 64,
                "manuscript_ref": str((paper_root / "draft.md").resolve()),
                "manuscript_digest": manuscript_digest,
                "route_back_required": True,
                "route_target": "write",
            }
        },
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": "sha256:" + "c" * 64,
            "evidence_ledger_digest": "sha256:" + "d" * 64,
            "claim_evidence_alignment_digest": "sha256:" + "e" * 64,
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": "owner-attempt::dm002-current",
            "fail_closed_when_missing": True,
            "missing_required_fields": ["display_source_reconciliation"],
        },
        "route_back_decision": {
            "recommended_action": "route_back_same_line",
            "rationale": "Current manuscript still needs write-owner repair.",
        },
    }
    return publication_eval_payload


def test_dm002_current_hardening_preserves_external_validation_writer_delta(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "002-dm-china-us-mortality-attribution"
    paper_root = study_root / "paper"
    old_text = "# Draft\n\nOutdated external-validation draft surface.\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(old_text, encoding="utf-8")
    old_refs = [
        {
            "path": str((paper_root / relative_path).resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": _fingerprint(paper_root / relative_path),
        }
        for relative_path in ("draft.md", "build/review_manuscript.md")
    ]
    writer_story = _dm002_writer_story()
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        (paper_root / relative_path).write_text(writer_story, encoding="utf-8")
    _write_dm002_template_inputs(study_root)
    source_eval_id = "publication-eval::dm002::current"

    changed_paths = medical_prose_story_surface.materialize_medical_prose_story_surfaces(
        paper_root=paper_root,
        work_unit_id=DM002_CURRENT_WORK_UNIT,
        source_eval_id=source_eval_id,
        previous_quality_repair_batch=_previous_blocked_batch(
            source_eval_id=source_eval_id,
            surface_refs=old_refs,
        ),
    )

    assert changed_paths == []
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == writer_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == writer_story


def test_dm002_display_table_repair_preserves_ai_reviewer_bound_current_manuscript_without_closing(
    monkeypatch: Any,
    tmp_path: Path,
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
    writer_story = _dm002_writer_story()
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(writer_story, encoding="utf-8")
    _write_minimal_paper_surfaces(paper_root)
    _write_dm002_template_inputs(study_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "route_key_question": "Repair current external-validation manuscript findings.",
            "work_unit_fingerprint": "dm002-display-table-current-ai-reviewer-record",
            "next_work_unit": {
                "unit_id": medical_prose_story_surface.DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
                "lane": "write",
                "summary": "Repair DM002 display/table manuscript surface.",
            },
        }
    )
    manuscript_digest = _sha256_text(writer_story)
    publication_eval_payload = _bind_publication_eval_to_current_manuscript(
        publication_eval_payload,
        paper_root=paper_root,
        manuscript_digest=manuscript_digest,
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::previous",
            "status": "executed",
            "ok": True,
            "repair_execution_evidence": {
                "status": "progress_delta_candidate",
                "manuscript_surface_hygiene": {
                    "status": "clear",
                    "surface_refs": [],
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                    "story_surface_delta_refs": [],
                },
            },
        },
    )

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
                "unit_id": medical_prose_story_surface.DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
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
            "work_unit_id": medical_prose_story_surface.DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "dm002-display-table-current-ai-reviewer-record",
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
    assert result["status"] == "handoff_ready"
    assert result["next_owner"] == "write"
    assert result["writer_worker_handoff"]["typed_blocker_if_unresolved"] == "manuscript_story_surface_delta_missing"
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == writer_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == writer_story
    evidence = result["repair_execution_evidence"]
    assert evidence["status"] == "blocked"
    assert evidence["progress_delta_candidate"] is False
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_refs"] == []
    assert "manuscript_story_surface_delta_missing" in evidence["blockers"]
    upstream_result = result["gate_clearing_batch"]["unit_results"][0]["result"]
    assert upstream_result["ai_reviewer_recheck_request_ref"] is None
    assert upstream_result["ai_reviewer_recheck_deferred_reason"] == "manuscript_story_surface_delta_missing"
    assert _sha256_text(writer_story) == manuscript_digest


def test_dm002_display_table_repair_fail_closes_when_ai_reviewer_bound_digest_is_not_live(
    monkeypatch: Any,
    tmp_path: Path,
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
    stale_story = _dm002_writer_story()
    live_story = stale_story.replace(
        "substantially underestimated absolute 5-year mortality.",
        "currently live text was overwritten after reviewer binding.",
    )
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(live_story, encoding="utf-8")
    _write_minimal_paper_surfaces(paper_root)
    _write_dm002_template_inputs(study_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "route_key_question": "Repair current external-validation manuscript findings.",
            "work_unit_fingerprint": "dm002-display-table-current-ai-reviewer-record",
            "next_work_unit": {
                "unit_id": medical_prose_story_surface.DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
                "lane": "write",
                "summary": "Repair DM002 display/table manuscript surface.",
            },
        }
    )
    publication_eval_payload = _bind_publication_eval_to_current_manuscript(
        publication_eval_payload,
        paper_root=paper_root,
        manuscript_digest=_sha256_text(stale_story),
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
                "unit_id": medical_prose_story_surface.DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
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
            "work_unit_id": medical_prose_story_surface.DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "dm002-display-table-current-ai-reviewer-record",
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

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "quality_repair_batch_current_manuscript_digest_mismatch"
    assert "writer_worker_handoff" not in result
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == live_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == live_story


def test_dm002_current_hardening_consumes_preserved_delta_and_requests_ai_recheck(
    monkeypatch: Any,
    tmp_path: Path,
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
    old_text = "# Draft\n\nOutdated external-validation draft surface.\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(old_text, encoding="utf-8")
    old_refs = [
        {
            "path": str((paper_root / relative_path).resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": _fingerprint(paper_root / relative_path),
        }
        for relative_path in ("draft.md", "build/review_manuscript.md")
    ]
    writer_story = _dm002_writer_story()
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        (paper_root / relative_path).write_text(writer_story, encoding="utf-8")
    _write_minimal_paper_surfaces(paper_root)
    _write_dm002_template_inputs(study_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "route_key_question": "Repair current external-validation manuscript findings.",
            "work_unit_fingerprint": "dm002-current-ai-reviewer-record",
            "next_work_unit": {
                "unit_id": DM002_CURRENT_WORK_UNIT,
                "lane": "write",
                "summary": "Repair DM002 as a clean external-validation paper.",
            },
        }
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        _previous_blocked_batch(
            source_eval_id=publication_eval_payload["eval_id"],
            surface_refs=old_refs,
        ),
    )

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
            "explicit_publication_work_unit": {"unit_id": DM002_CURRENT_WORK_UNIT, "lane": "write"},
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
            "work_unit_id": DM002_CURRENT_WORK_UNIT,
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "dm002-current-ai-reviewer-record",
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
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == writer_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == writer_story
    evidence = result["repair_execution_evidence"]
    assert evidence["status"] == "progress_delta_candidate"
    assert evidence["ai_reviewer_recheck_done"] is True
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is True
    story_refs = evidence["manuscript_surface_hygiene"]["story_surface_delta_refs"]
    assert {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in story_refs
    } == {"paper/draft.md", "paper/build/review_manuscript.md"}
    assert {ref["fingerprint"]["content_sha256"] for ref in story_refs} == {
        _fingerprint(paper_root / "draft.md")["content_sha256"]
    }
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    assert request_path.exists()


def test_quality_repair_batch_fail_closes_unknown_explicit_route_work_unit(
    monkeypatch: Any,
    tmp_path: Path,
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
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent manuscript.\n", encoding="utf-8")
    _write_minimal_paper_surfaces(paper_root)
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
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
            "blockers": ["medical_publication_surface_blocked"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::dm002-medical-prose",
        },
    )
    called: dict[str, bool] = {}
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: called.setdefault("gate_batch_called", True),
    )
    route_context = {
        **_paper_write_supervisor_route_context(),
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "unknown_stage_log_work_unit",
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "domain-transition::route_back_same_line::unknown_stage_log_work_unit",
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

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "controller_route_work_unit_unsupported"
    assert called == {}
