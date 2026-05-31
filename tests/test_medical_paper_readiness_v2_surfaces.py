from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.reviewer_os_fixture_helpers import (
    claim_evidence_alignment_digest,
    ready_claim_evidence_alignment_gate,
)


V2_SURFACE_KEYS = {
    "literature_provider_runtime",
    "route_decision_orchestrator",
    "statistical_discipline_operations",
    "revision_rebuttal_loop",
    "authoring_runtime_authorization",
    "real_workspace_soak_monitor",
}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _provider_payload() -> dict[str, object]:
    return {
        "search_strategy": {
            "query": "diabetes mortality prediction",
            "mesh_terms": ["Diabetes Mellitus"],
            "keywords": ["mortality", "risk prediction", "diabetes"],
        },
        "study_rationale": "A transportable mortality risk model addresses a clinically actionable prognostic gap.",
        "search_date": "2026-05-04",
        "providers": [
            {
                "provider_name": "pubmed",
                "query": "diabetes mortality prediction",
                "retrieved_at": "2026-05-04T01:00:00+08:00",
                "source_refs": ["pubmed:query:001"],
                "credential_status": {"status": "ready", "credential_ref": "env:PUBMED_API_KEY"},
                "rate_limit_status": {"status": "ok", "backoff": {"retry_after_seconds": 0}},
                "cache_freshness": {"status": "fresh"},
                "provider_response_ledger_refs": ["ops/provider_responses/pubmed-001.json"],
                "items": [
                    {
                        "category": "anchor_papers",
                        "ref": "pmid:1",
                        "citation_ledger_ref": "paper/citation_ledger.json#pmid-1",
                    },
                ],
            },
            {
                "provider_name": "crossref",
                "query": "diabetes mortality prediction guideline review",
                "retrieved_at": "2026-05-04T01:01:00+08:00",
                "source_refs": ["crossref:query:001"],
                "credential_status": {"status": "ready", "credential_ref": "env:CROSSREF_MAILTO"},
                "rate_limit_status": {"status": "ok", "backoff": {"retry_after_seconds": 0}},
                "cache_freshness": {"status": "fresh"},
                "provider_response_ledger_refs": ["ops/provider_responses/crossref-001.json"],
                "items": [
                    {
                        "category": "guidelines",
                        "ref": "guideline:tripod-ai",
                        "citation_ledger_ref": "paper/citation_ledger.json#tripod-ai",
                    },
                    {
                        "category": "systematic_reviews",
                        "ref": "pmid:review",
                        "citation_ledger_ref": "paper/citation_ledger.json#review",
                    },
                ],
            },
            {
                "provider_name": "semantic_scholar",
                "query": "diabetes mortality prediction clinical neighbor",
                "retrieved_at": "2026-05-04T01:02:00+08:00",
                "source_refs": ["semantic_scholar:query:001"],
                "credential_status": {
                    "status": "ready",
                    "credential_ref": "env:SEMANTIC_SCHOLAR_API_KEY",
                },
                "rate_limit_status": {"status": "ok", "backoff": {"retry_after_seconds": 0}},
                "cache_freshness": {"status": "fresh"},
                "provider_response_ledger_refs": ["ops/provider_responses/semantic-scholar-001.json"],
                "items": [
                    {
                        "category": "journal_neighbor_refs",
                        "ref": "journal:neighbor",
                        "score": 0.91,
                        "score_source_ref": "ops/literature_scores/neighbor.json",
                        "citation_ledger_ref": "paper/citation_ledger.json#neighbor",
                    },
                ],
            },
        ],
        "screening_decisions": [{"decision": "include", "reason": "same endpoint"}],
        "citation_ledger_refs": ["paper/citation_ledger.json"],
    }


def _route_candidate() -> dict[str, object]:
    return {
        "line_id": "transportable-risk-model",
        "dimensions": {
            "novelty": 5,
            "clinical_relevance": 5,
            "data_fit": 5,
            "external_validation": 4,
            "analysis_feasibility": 5,
            "journal_fit": 4,
            "risk_cost": 1,
            "stop_threshold": "stop if external validation unavailable",
        },
        "evidence_refs": ["artifacts/medical_paper/literature_provider_runtime.json"],
        "stage_output_refs": [
            "artifacts/stage_knowledge/idea/closeouts/transportable-risk-model.json",
            "artifacts/stage_knowledge/idea/latest.json",
        ],
    }


def _revision_rebuttal_payload() -> dict[str, object]:
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


def _reviewer_operating_system() -> dict[str, object]:
    eval_id = "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00"
    request_digest = "sha256:" + "a" * 64
    manuscript_ref = "paper/manuscript.md"
    manuscript_digest = "sha256:" + "c" * 64
    claim_alignment = ready_claim_evidence_alignment_gate()
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
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": request_digest,
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
            },
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
            },
            "source_eval": {
                "status": "current",
                "eval_id": eval_id,
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": eval_id,
            },
        },
        "claim_evidence_alignment": claim_alignment,
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "ready",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": request_digest,
            "evidence_ledger_digest": "sha256:" + "e" * 64,
            "claim_evidence_alignment_digest": claim_evidence_alignment_digest(claim_alignment),
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": "ai-reviewer-attempt-001",
            "fail_closed_when_missing": True,
            "missing_required_fields": [],
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Readiness is limited to the current reviewed manuscript snapshot.",
                "impact_on_claim": "Publication-facing claims must remain within reviewed evidence support.",
                "required_future_analysis_data_or_design": "Repeat reviewer readiness checks after substantive changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
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
            "calibration_refs_applied": [
                "ai_reviewer_calibration_corpus#thin_first_draft",
                "ai_reviewer_calibration_corpus#overstrong_claim",
            ],
            "calibration_judgment": {
                "role": "required_authoring_judgment_input",
                "refs": [
                    "ai_reviewer_calibration_corpus#thin_first_draft",
                    "ai_reviewer_calibration_corpus#overstrong_claim",
                ],
            },
        },
    }


def _authoring_inputs() -> dict[str, object]:
    return {
        "target_journal_writing_layer": {
            "target_journal_family": "clinical epidemiology",
            "section_plan": [{"section": "Results", "writing_role": "finding-led paragraphs"}],
        },
        "claim_to_paragraph_map": {
            "claims": [
                {
                    "claim_id": "claim-primary",
                    "paragraph_id": "results-p1",
                    "evidence_refs": ["paper/evidence_ledger.json#claim-primary"],
                    "reviewer_concern_refs": [
                        "paper/review/review_ledger.json#concern-primary"
                    ],
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
                {"case_ref": "ai_reviewer_calibration_corpus#overstrong_claim"}
            ],
        },
        "evidence_ledger_ref": "paper/evidence_ledger.json",
        "review_ledger_ref": "paper/review/review_ledger.json",
        "publication_eval": {
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [
                    "artifacts/publication_eval/latest.json",
                    "paper/evidence_ledger.json",
                    "paper/review/review_ledger.json",
                ],
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
        },
        "calibration_case_refs": [
            "ai_reviewer_calibration_corpus#thin_first_draft",
            "ai_reviewer_calibration_corpus#overstrong_claim",
        ],
    }


def _complete_soak_matrix_payload() -> dict[str, object]:
    return {
        "study_id": "prediction-model-study",
        "study_archetype": "prediction_model",
        "stages": [
            "literature_scout",
            "line_selection",
            "main_analysis",
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
        "durable_refs": ["artifacts/medical_paper/real_study_soak_matrix_evidence.json"],
    }


def _soak_monitor_study_payload(
    *,
    study_id: str,
    study_archetype: str,
    route_action: str = "continue",
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
        "route_action": route_action,
        "durable_refs": [f"artifacts/medical_paper/{study_id}.json"],
    }


def _materialize_complete_soak_monitor_inputs(study_root: Path) -> list[Path]:
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
            _soak_monitor_study_payload(study_id=root.name, study_archetype=archetype),
        )
    return roots


def _materialize_complete_v2_surfaces(study_root: Path) -> None:
    literature_runtime = importlib.import_module("med_autoscience.controllers.literature_provider_runtime")
    route_orchestrator = importlib.import_module("med_autoscience.controllers.route_decision_orchestrator")
    stats_runtime = importlib.import_module("med_autoscience.controllers.statistical_discipline_runtime")
    rebuttal_loop = importlib.import_module("med_autoscience.controllers.revision_rebuttal_loop")
    authoring = importlib.import_module("med_autoscience.controllers.ai_reviewer_journal_loop")
    soak_monitor = importlib.import_module("med_autoscience.controllers.real_workspace_soak_monitor")

    literature_runtime.materialize_literature_provider_runtime(
        study_root=study_root,
        payload=_provider_payload(),
    )
    route_projection = route_orchestrator.materialize_route_decision_orchestration(
        study_root=study_root,
        candidates=[_route_candidate()],
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
                    "primary_evidence_basis": "calibration slope and decision-curve net benefit",
                }
            ]
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "statistical_discipline_operations.json",
        stats_projection,
    )
    rebuttal_loop.materialize_revision_rebuttal_loop(study_root, _revision_rebuttal_payload())
    _write_json(
        study_root / "artifacts" / "medical_paper" / "authoring_runtime_authorization.json",
        authoring.build_authoring_runtime_authorization(**_authoring_inputs()),
    )
    monitor_roots = _materialize_complete_soak_monitor_inputs(study_root)
    soak_monitor.materialize_real_workspace_soak_monitor(study_roots=monitor_roots)


def test_v2_surfaces_are_first_class_readiness_capabilities(tmp_path: Path) -> None:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "study"
    _materialize_complete_v2_surfaces(study_root)

    readiness = readiness_module.build_medical_paper_readiness_surface(study_root=study_root)
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}

    assert V2_SURFACE_KEYS <= set(by_key)
    assert readiness["required_count"] == 13
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False
    for surface_key in V2_SURFACE_KEYS:
        assert by_key[surface_key]["status"] == "present"
        assert by_key[surface_key]["evidence_refs"]
        assert by_key[surface_key]["missing_reason"] == ""


def test_v2_surfaces_fail_closed_when_missing(tmp_path: Path) -> None:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")

    readiness = readiness_module.build_medical_paper_readiness_surface(study_root=tmp_path / "study")
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}

    assert V2_SURFACE_KEYS <= set(by_key)
    for surface_key in V2_SURFACE_KEYS:
        assert by_key[surface_key]["status"] == "missing"
        assert by_key[surface_key]["missing_reason"] == "missing_canonical_artifact"
    assert readiness["overall_status"] == "missing"
    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False


def test_v2_route_decision_blocks_unsupported_decision(tmp_path: Path) -> None:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    path = (
        tmp_path
        / "study"
        / "artifacts"
        / "medical_paper"
        / "route_decision_orchestrator.json"
    )
    _write_json(
        path,
        {
            "surface": "route_decision_orchestrator",
            "status": "ready",
            "route_decision": "continue_analysis",
            "controller_decision_ref": "artifacts/controller_decisions/latest.json",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )

    readiness = readiness_module.build_medical_paper_readiness_surface(study_root=tmp_path / "study")
    route_surface = {
        item["surface_key"]: item
        for item in readiness["capability_surfaces"]
    }["route_decision_orchestrator"]

    assert route_surface["status"] == "blocked"
    assert route_surface["missing_reason"] == "unsupported_route_decision"


def test_v2_blockers_project_specific_missing_reasons(tmp_path: Path) -> None:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    study_root = tmp_path / "study"
    root = study_root / "artifacts" / "medical_paper"
    _write_json(
        root / "statistical_discipline_operations.json",
        {
            "surface": "statistical_discipline_operations",
            "status": "blocked",
            "blockers": ["missing_external_validation"],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        root / "revision_rebuttal_loop.json",
        {
            "surface": "revision_rebuttal_loop",
            "status": "blocked",
            "blockers": ["missing_review_ledger_refs"],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        root / "authoring_runtime_authorization.json",
        {
            "surface": "ai_reviewer_journal_writing_authorization",
            "full_drafting_authorized": False,
            "blockers": ["publication_eval_missing"],
            "quality_claim_authorized": False,
            "authority": {"mechanical_projection_can_authorize_quality": False},
        },
    )
    _write_json(
        root / "real_workspace_soak_monitor.json",
        {
            "surface": "real_workspace_soak_monitor",
            "overall_status": "partial",
            "next_action": "cover_missing_archetypes",
            "authority_contract": {
                "can_mutate_runtime": False,
                "can_authorize_quality": False,
                "can_authorize_submission": False,
                "can_authorize_finalize": False,
            },
        },
    )

    readiness = readiness_module.build_medical_paper_readiness_surface(study_root=study_root)
    by_key = {item["surface_key"]: item for item in readiness["capability_surfaces"]}

    assert by_key["statistical_discipline_operations"]["status"] == "blocked"
    assert by_key["statistical_discipline_operations"]["missing_reason"] == "missing_external_validation"
    assert by_key["revision_rebuttal_loop"]["status"] == "blocked"
    assert by_key["revision_rebuttal_loop"]["missing_reason"] == "missing_review_ledger_refs"
    assert by_key["authoring_runtime_authorization"]["status"] == "blocked"
    assert by_key["authoring_runtime_authorization"]["missing_reason"] == "publication_eval_missing"
    assert by_key["real_workspace_soak_monitor"]["status"] == "partial"
    assert by_key["real_workspace_soak_monitor"]["missing_reason"] == "cover_missing_archetypes"
