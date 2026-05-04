from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _complete_surface_payloads() -> dict[str, dict[str, object]]:
    return {
        "literature_scout": {
            "search_strategy": {"query": "diabetes mortality prediction", "mesh_terms": ["Diabetes Mellitus"]},
            "search_date": "2026-05-03",
            "anchor_papers": ["pmid:1"],
            "guidelines": ["TRIPOD+AI"],
            "journal_neighbor_refs": ["paper:near-neighbor"],
        },
        "study_line_selection": {
            "selected_line_id": "primary-risk-model",
            "dimensions": {
                "novelty": "moderate",
                "clinical_relevance": "high",
                "data_fit": "high",
                "analysis_plasticity": "moderate",
                "external_validation": "available",
                "journal_fit": "good",
                "cost_risk": "bounded",
                "stop_threshold": "no external validation or poor calibration",
            },
            "discarded_alternatives": ["weak-clustering"],
        },
        "archetype_analysis_contract": {
            "status": "resolved",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "guideline_family": "TRIPOD+AI",
        },
        "bounded_analysis_candidate_board": {
            "candidates": [
                {
                    "mode": "exploit",
                    "target_claim": "primary transportability claim",
                    "expected_evidence_gain": "close calibration concern",
                    "cost_risk": "bounded",
                    "clinical_interpretability": "high",
                    "decision": "run",
                    "decision_reason": "reviewer concern targets calibration",
                }
            ]
        },
        "stop_loss_memo": {
            "attempted_paths": ["primary-risk-model"],
            "failure_reason": "",
            "evidence_gain_ceiling": "not reached",
            "alternative_routes": ["external-validation-only"],
            "human_gate_question": "",
            "decision": "continue",
        },
    }


def _complete_soak_stage_evidence() -> dict[str, list[str]]:
    return {
        "literature_scout": ["artifacts/medical_paper/literature_scout.json"],
        "line_selection": ["artifacts/medical_paper/study_line_selection.json"],
        "main_analysis": ["paper/medical_analysis_contract.json"],
        "bounded_analysis": ["artifacts/medical_paper/bounded_analysis_candidate_board.json"],
        "route_back": ["artifacts/controller_decisions/latest.json"],
        "stop_loss": ["artifacts/medical_paper/stop_loss_memo.json"],
        "revision_reopen": ["artifacts/task_intake/latest.json"],
        "runtime_recovery": ["artifacts/runtime/runtime_supervision/latest.json"],
        "finalize_rebuild": ["paper/submission_minimal/current_package.zip"],
        "final_pre_submission_audit": ["artifacts/publication_eval/latest.json"],
    }


def _reviewer_operating_system() -> dict[str, object]:
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": {
            "manuscript": "paper/manuscript.md",
            "study_charter": "artifacts/controller/study_charter.json",
            "evidence_ledger": "paper/evidence_ledger.json",
            "review_ledger": "paper/review/review_ledger.json",
            "medical_manuscript_blueprint": "paper/medical_manuscript_blueprint.json",
            "claim_evidence_map": "paper/claim_evidence_map.json",
            "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
            "publication_gate_projection": "artifacts/publication_eval/latest.json",
        },
        "rubric_scores": {
            dimension: {
                "status": "ready",
                "rationale": f"{dimension} is ready.",
                "evidence_refs": ["paper/evidence_ledger.json"],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is ready.",
            }
            for dimension in dimensions
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "authorize_full_manuscript_drafting",
            "rationale": "All authoring inputs are ready.",
        },
    }


def _complete_literature_provider_runtime_payload() -> dict[str, object]:
    return {
        "providers": [
            {
                "provider_name": "pubmed",
                "response_status": "ok",
                "query": "diabetes mortality prediction",
                "retrieved_at": "2026-05-03T00:00:00Z",
                "source_refs": ["pubmed:search:1"],
                "items": [
                    {"category": "anchor_papers", "ref": "pmid:1"},
                    {"category": "guidelines", "ref": "TRIPOD+AI"},
                    {"category": "systematic_reviews", "ref": "pmid:review"},
                    {"category": "journal_neighbor_refs", "ref": "paper:near-neighbor"},
                ],
            }
        ],
        "search_strategy": {"query": "diabetes mortality prediction"},
        "search_date": "2026-05-03",
        "citation_ledger_refs": ["paper/citation_ledger.json"],
        "screening_decisions": [{"decision": "include", "reason": "same endpoint"}],
    }


def _complete_route_candidate(line_id: str = "primary-risk-model") -> dict[str, object]:
    return {
        "line_id": line_id,
        "title": "Primary risk model",
        "dimensions": {
            "novelty": 5,
            "clinical_relevance": 5,
            "data_fit": 5,
            "external_validation": 4,
            "analysis_feasibility": 5,
            "journal_fit": 4,
            "risk_cost": 1,
            "stop_threshold": "stop if transportability cannot be evaluated",
        },
        "evidence_refs": ["artifacts/medical_paper/literature_provider_runtime.json"],
    }


def _complete_revision_rebuttal_payload() -> dict[str, object]:
    return {
        "reviewer_comments": [
            {
                "comment_id": "R1-1",
                "source": "reviewer_1",
                "concern": "External validation needs clearer calibration evidence.",
                "severity": "major",
                "requested_change": "Add calibration and net-benefit analysis.",
                "target_section": "Results",
            }
        ],
        "evidence_ledger_refs": ["paper/evidence_ledger.json"],
        "review_ledger_refs": ["paper/review/review_ledger.json"],
    }


def _complete_authoring_runtime_authorization_inputs() -> dict[str, object]:
    return {
        "target_journal_writing_layer": {
            "target_journal_family": "clinical epidemiology",
            "section_plan": [
                {"section": "Introduction", "writing_role": "bounded clinical rationale"},
                {"section": "Results", "writing_role": "finding-led paragraphs"},
            ],
        },
        "claim_to_paragraph_map": {
            "claims": [
                {
                    "claim_id": "claim-primary",
                    "paragraph_id": "results-p1",
                    "evidence_refs": ["paper/evidence_ledger.json#claim-primary"],
                    "reviewer_concern_refs": ["paper/review/review_ledger.json#concern-primary"],
                }
            ]
        },
        "display_to_claim_map": {
            "links": [
                {
                    "display_id": "table-2",
                    "claim_ids": ["claim-primary"],
                    "evidence_refs": ["paper/evidence_ledger.json#table-2"],
                }
            ]
        },
        "restrained_language_strategy": {
            "strategy_id": "restrained-clinical-language-v1",
            "overstrong_claim_controls": [
                {"claim_id": "claim-primary", "required_qualifier": "was associated with"}
            ],
        },
        "evidence_ledger_ref": "paper/evidence_ledger.json",
        "review_ledger_ref": "paper/review/review_ledger.json",
        "publication_eval": {
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": ["artifacts/publication_eval/latest.json"],
                "ai_reviewer_required": False,
            },
            "reviewer_operating_system": _reviewer_operating_system(),
            "quality_claim_authorized": True,
            "publication_critique": {
                "concerns": [
                    {
                        "concern_id": "concern-primary",
                        "claim_id": "claim-primary",
                        "display_id": "table-2",
                        "evidence_ref": "paper/evidence_ledger.json#claim-primary",
                        "reviewer_concern_ref": "paper/review/review_ledger.json#concern-primary",
                    }
                ]
            },
            "quality_assessment": {
                key: {
                    "status": "ready",
                    "summary": f"{key} is ready.",
                    "evidence_refs": ["paper/evidence_ledger.json"],
                }
                for key in (
                    "clinical_significance",
                    "evidence_strength",
                    "novelty_positioning",
                    "medical_journal_prose_quality",
                    "human_review_readiness",
                )
            },
        },
        "calibration_case_refs": [
            "ai_reviewer_calibration_corpus#thin_first_draft",
            "ai_reviewer_calibration_corpus#overstrong_claim",
        ],
    }


def _materialize_complete_v2_readiness_inputs(study_root: Path) -> None:
    literature_runtime = importlib.import_module("med_autoscience.controllers.literature_provider_runtime")
    route_orchestrator = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    stats_runtime = importlib.import_module("med_autoscience.controllers.statistical_discipline_runtime")
    rebuttal_loop = importlib.import_module("med_autoscience.controllers.revision_rebuttal_loop")
    authoring = importlib.import_module("med_autoscience.controllers.ai_reviewer_journal_loop")
    soak_monitor = importlib.import_module("med_autoscience.controllers.real_workspace_soak_monitor")

    literature_runtime.materialize_literature_provider_runtime(
        study_root=study_root,
        payload=_complete_literature_provider_runtime_payload(),
    )
    route_projection = route_orchestrator.materialize_route_decision_orchestration(
        study_root=study_root,
        candidates=[_complete_route_candidate()],
        requested_action="select_line",
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json",
        route_projection,
    )
    stats_projection = stats_runtime.build_statistical_discipline_operations_projection(
        stats_runtime.build_statistical_discipline_contract(study_archetype="prediction_model"),
        bounded_board={
            "candidates": [
                {
                    "target_claim": "transportable mortality risk prediction",
                    "expected_evidence_gain": "close calibration and net-benefit concern",
                    "statistical_risk": "moderate",
                    "clinical_interpretability": "high",
                    "decision": "exploit",
                    "decision_reason": "reviewer concern targets calibration and utility",
                    "primary_evidence_basis": "calibration slope, confidence interval, and decision-curve net benefit",
                }
            ]
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "statistical_discipline_operations.json",
        stats_projection,
    )
    rebuttal_loop.materialize_revision_rebuttal_loop(study_root, _complete_revision_rebuttal_payload())
    _write_json(
        study_root / "artifacts" / "medical_paper" / "authoring_runtime_authorization.json",
        authoring.build_authoring_runtime_authorization(**_complete_authoring_runtime_authorization_inputs()),
    )
    roots = _materialize_complete_v2_soak_monitor_inputs(study_root)
    soak_monitor.materialize_real_workspace_soak_monitor(study_roots=roots)


def _materialize_complete_v2_soak_monitor_inputs(study_root: Path) -> list[Path]:
    roots = [
        study_root,
        study_root.parent / "observational-study",
        study_root.parent / "subtype-study",
    ]
    archetypes = [
        "prediction_model/external_validation",
        "observational_real_world",
        "subtype_or_triage",
    ]
    for root, archetype in zip(roots, archetypes, strict=True):
        _write_json(
            root / "artifacts" / "medical_paper" / "real_study_soak_matrix_evidence.json",
            _complete_v2_soak_monitor_study_payload(study_id=root.name, study_archetype=archetype),
        )
    return roots


def _complete_v2_soak_monitor_study_payload(
    *,
    study_id: str,
    study_archetype: str,
) -> dict[str, object]:
    return {
        "study_id": study_id,
        "study_archetype": study_archetype,
        "stages": [
            "literature_scout",
            "line_selection",
            "baseline",
            "primary_analysis",
            "bounded_analysis",
            "route_back",
            "stop_loss",
            "revision_reopen",
            "runtime_recovery",
            "finalize_rebuild",
            "final_pre_submission_audit",
        ],
        "contracts": {
            "literature_contract": True,
            "statistical_contract": True,
            "external_validation_fixture": True,
        },
        "fixtures": {"external_validation": True},
        "result_strength": "adequate",
        "route_action": "continue",
        "durable_refs": [f"artifacts/medical_paper/{study_id}.json"],
    }


def _materialize_complete_readiness_inputs(module: object, study_root: Path) -> None:
    for surface_key, payload in _complete_surface_payloads().items():
        module.materialize_medical_paper_readiness_surface(
            study_root=study_root,
            surface_key=surface_key,
            payload=payload,
        )
    _write_json(
        study_root / "paper" / "target_journal_writing_layer.json",
        {
            "surface": "target_journal_writing_layer",
            "schema_version": 1,
            "role": "ai_reviewer_quality_context",
            "target_journal_family": "general_internal_medicine",
            "near_neighbor_style_corpus": [{"journal": "JAMA", "style_ref": "workspace_lit:jama"}],
            "section_plan": {
                "Introduction": "gap and objective",
                "Methods": "cohort and analysis",
                "Results": "primary finding",
                "Discussion": "interpretation and limits",
            },
            "claim_to_paragraph_map": [
                {
                    "claim_id": "primary_claim",
                    "section": "Results",
                    "evidence_refs": ["evidence:primary"],
                    "reviewer_concern_refs": ["review:primary"],
                }
            ],
            "display_to_claim_map": [{"display_id": "Table 2", "claim_id": "primary_claim"}],
            "restrained_language_strategy": {"required_claim_qualifiers": ["was associated with"]},
            "mechanical_projection_can_authorize_quality": False,
            "quality_claim_authorized": False,
        },
    )
    _materialize_complete_v2_readiness_inputs(study_root)


def test_medical_paper_readiness_surface_marks_complete_study_ready(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "study"
    _materialize_complete_readiness_inputs(module, study_root)
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {"stage_evidence": _complete_soak_stage_evidence()},
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    assert readiness["surface"] == "medical_paper_readiness"
    assert readiness["overall_status"] == "ready"
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False
    assert readiness["next_action"]["action_id"] == "continue_managed_execution"
    assert {item["surface_key"]: item["status"] for item in readiness["capability_surfaces"]} == {
        "literature_scout": "present",
        "study_line_selection": "present",
        "archetype_analysis_contract": "present",
        "bounded_analysis_candidate_board": "present",
        "stop_loss_memo": "present",
        "target_journal_writing_layer": "present",
        "real_study_soak_matrix_evidence": "present",
        "literature_provider_runtime": "present",
        "route_decision_orchestrator": "present",
        "statistical_discipline_operations": "present",
        "revision_rebuttal_loop": "present",
        "authoring_runtime_authorization": "present",
        "real_workspace_soak_monitor": "present",
    }


def test_medical_paper_readiness_consumes_long_horizon_canonical_surfaces(tmp_path: Path) -> None:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    literature_module = importlib.import_module("med_autoscience.controllers.literature_intelligence_os")
    line_module = importlib.import_module("med_autoscience.controllers.study_line_decision_engine")
    stats_module = importlib.import_module("med_autoscience.controllers.statistical_discipline_runtime")
    route_module = importlib.import_module("med_autoscience.controllers.route_control_stoploss")
    study_root = tmp_path / "study"

    literature_module.materialize_literature_intelligence_os(
        study_root=study_root,
        payload={
            "search_strategy": {"query": "diabetes mortality prediction", "mesh_terms": ["Diabetes Mellitus"]},
            "search_date": "2026-05-03",
            "searched_sources": ["PubMed"],
            "anchor_papers": ["pmid:1"],
            "guidelines": ["TRIPOD+AI"],
            "systematic_reviews": ["pmid:review"],
            "journal_neighbor_refs": ["paper:near-neighbor"],
            "screening_decisions": [{"decision": "include", "reason": "same endpoint"}],
            "citation_ledger_refs": ["paper/citation_ledger.json"],
        },
    )
    line_module.materialize_study_line_decision(
        study_root=study_root,
        candidates=[
            {
                "line_id": "primary-risk-model",
                "dimensions": {
                    "novelty": 4,
                    "clinical_relevance": 5,
                    "data_fit": 5,
                    "external_validation": 4,
                    "analysis_feasibility": 4,
                    "journal_fit": 4,
                    "risk_cost": 1,
                    "stop_threshold": "poor calibration or no external validation",
                },
                "evidence_refs": ["artifacts/medical_paper/literature_intelligence_os.json"],
            }
        ],
    )
    readiness_module.materialize_medical_paper_readiness_surface(
        study_root=study_root,
        surface_key="archetype_analysis_contract",
        payload=stats_module.build_statistical_discipline_contract(study_archetype="prediction_model"),
    )
    readiness_module.materialize_medical_paper_readiness_surface(
        study_root=study_root,
        surface_key="bounded_analysis_candidate_board",
        payload={
            "candidates": [
                {
                    "target_claim": "transportable mortality risk prediction",
                    "expected_evidence_gain": "close calibration and net-benefit concern",
                    "statistical_risk": "moderate",
                    "clinical_interpretability": "high",
                    "decision": "exploit",
                    "decision_reason": "reviewer concern targets calibration and utility",
                }
            ]
        },
    )
    route_module.materialize_route_control_stoploss_memo(
        root=study_root,
        current_route="analysis-campaign",
        decision="stop_loss",
        evidence_state="weak",
        stop_pressure="high",
        attempted_paths=["primary-risk-model"],
        failure_reasons=["external validation did not transport"],
        continuation_cost="high",
        evidence_gain_ceiling="low",
        alternative_routes=["external-validation-only"],
        evidence_refs=["artifacts/publication_eval/latest.json"],
    )
    _write_json(
        study_root / "paper" / "target_journal_writing_layer.json",
        {
            "surface": "target_journal_writing_layer",
            "schema_version": 1,
            "role": "ai_reviewer_quality_context",
            "target_journal_family": "general_internal_medicine",
            "near_neighbor_style_corpus": [{"journal": "JAMA", "style_ref": "workspace_lit:jama"}],
            "section_plan": {
                "Introduction": "gap and objective",
                "Methods": "cohort and analysis",
                "Results": "primary finding",
                "Discussion": "interpretation and limits",
            },
            "claim_to_paragraph_map": [
                {
                    "claim_id": "primary_claim",
                    "section": "Results",
                    "evidence_refs": ["evidence:primary"],
                    "reviewer_concern_refs": ["review:primary"],
                }
            ],
            "display_to_claim_map": [{"display_id": "Table 2", "claim_id": "primary_claim"}],
            "restrained_language_strategy": {"required_claim_qualifiers": ["was associated with"]},
            "mechanical_projection_can_authorize_quality": False,
            "quality_claim_authorized": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {"stage_evidence": _complete_soak_stage_evidence()},
    )
    _materialize_complete_v2_readiness_inputs(study_root)

    readiness = readiness_module.build_medical_paper_readiness_surface(study_root=study_root)

    assert readiness["overall_status"] == "ready"
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["literature_scout"]["status"] == "present"
    assert by_key["literature_scout"]["evidence_refs"] == [
        str(study_root.resolve() / "artifacts" / "medical_paper" / "literature_intelligence_os.json")
    ]
    assert by_key["study_line_selection"]["status"] == "present"
    assert by_key["archetype_analysis_contract"]["status"] == "present"
    assert by_key["bounded_analysis_candidate_board"]["status"] == "present"
    assert by_key["stop_loss_memo"]["status"] == "present"
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False


def test_medical_paper_readiness_marks_sanitized_real_study_soak_evidence_present(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "sanitized-study"
    _materialize_complete_readiness_inputs(module, study_root)
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "fixture_kind": "sanitized_real_study_soak_fixture",
            "contains_phi": False,
            "stage_evidence": _complete_soak_stage_evidence(),
        },
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    soak_surface = by_key["real_study_soak_matrix_evidence"]
    assert readiness["overall_status"] == "ready"
    assert soak_surface["status"] == "present"
    assert soak_surface["missing_reason"] == ""
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False


def test_medical_paper_readiness_blocks_sanitized_soak_fixture_with_missing_stage(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "sanitized-study"
    _materialize_complete_readiness_inputs(module, study_root)
    stage_evidence = _complete_soak_stage_evidence()
    stage_evidence.pop("runtime_recovery")
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "fixture_kind": "sanitized_real_study_soak_fixture",
            "contains_phi": False,
            "stage_evidence": stage_evidence,
        },
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    soak_surface = by_key["real_study_soak_matrix_evidence"]
    assert readiness["overall_status"] == "blocked"
    assert soak_surface["status"] == "partial"
    assert soak_surface["missing_reason"] == "missing_required_soak_stage"
    assert soak_surface["missing_stage_gaps"] == [
        {
            "stage": "runtime_recovery",
            "missing_reason": "missing_durable_evidence_ref",
        }
    ]
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False


def test_medical_paper_readiness_surface_fails_closed_when_inputs_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "study"
    module.materialize_medical_paper_readiness_surface(
        study_root=study_root,
        surface_key="literature_scout",
        payload=_complete_surface_payloads()["literature_scout"],
    )

    readiness = module.build_medical_paper_readiness_surface(study_root=study_root)

    assert readiness["overall_status"] == "blocked"
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False
    assert readiness["next_action"] == {
        "action_id": "complete_medical_paper_readiness_surface",
        "surface_key": "study_line_selection",
        "summary": "补齐 Study Line Selection Scorecard 后再继续自动论文链路。",
    }
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["literature_scout"]["status"] == "present"
    assert by_key["study_line_selection"]["status"] == "missing"
    assert by_key["study_line_selection"]["missing_reason"] == "missing_canonical_artifact"


def test_medical_paper_readiness_materializer_rejects_incomplete_payload(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")

    result = module.materialize_medical_paper_readiness_surface(
        study_root=tmp_path / "study",
        surface_key="bounded_analysis_candidate_board",
        payload={"candidates": []},
    )

    assert result["surface_key"] == "bounded_analysis_candidate_board"
    assert result["status"] == "blocked"
    assert result["artifact_path"].endswith("artifacts/medical_paper/bounded_analysis_candidate_board.json")

    readiness = module.build_medical_paper_readiness_surface(study_root=tmp_path / "study")
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}
    assert by_key["bounded_analysis_candidate_board"]["status"] == "blocked"
    assert by_key["bounded_analysis_candidate_board"]["missing_reason"] == "missing_candidates"
