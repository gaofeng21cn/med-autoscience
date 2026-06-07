from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_json as _write_json,
    write_current_dispatch as _write_current_dispatch,
    write_scan_latest as _write_scan_latest,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_literature_provider_runtime import _complete_provider_payload


ACTION_TYPE = "complete_medical_paper_readiness_surface"


def _readiness_dispatch(*, study_id: str) -> dict[str, object]:
    dispatch = _dispatch(
        study_id=study_id,
        action_type=ACTION_TYPE,
        owner="MedAutoScience",
        required_output_surface=(
            "artifacts/medical_paper/<surface_key>.json or "
            "typed blocker:medical_paper_readiness_surface_input_required"
        ),
    )
    dispatch["surface_key"] = "literature_provider_runtime"
    dispatch["prompt_contract"]["surface_key"] = "literature_provider_runtime"
    return dispatch


def _readiness_dispatch_for_surface(*, study_id: str, surface_key: str) -> dict[str, object]:
    dispatch = _readiness_dispatch(study_id=study_id)
    dispatch["surface_key"] = surface_key
    dispatch["readiness_surface_identity"] = {
        "action_type": ACTION_TYPE,
        "surface_key": surface_key,
        "source": "current_owner_action",
    }
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["surface_key"] = surface_key
    prompt_contract["readiness_surface_identity"] = dict(dispatch["readiness_surface_identity"])
    return dispatch


def _attach_readiness_closeout_binding(dispatch: dict[str, object], *, study_id: str) -> dict[str, str]:
    source_fingerprint = f"truth-source::{study_id}::{ACTION_TYPE}"
    closeout_ref = (
        "artifacts/supervision/consumer/stage_attempt_closeouts/"
        "sat-medical-paper-readiness.json"
    )
    binding = {
        "surface_kind": "medical_paper_readiness_closeout_binding",
        "stage_run_id": f"stage-run::{study_id}::domain_owner/default-executor-dispatch",
        "stage_run_ref": f"stage-run::{study_id}::domain_owner/default-executor-dispatch",
        "stage_manifest_ref": (
            "artifacts/supervision/consumer/stage_manifests/"
            "domain_owner_default_executor_dispatch.json"
        ),
        "current_pointer_ref": (
            "artifacts/supervision/consumer/current_pointers/"
            "domain_owner_default_executor_dispatch.json"
        ),
        "closeout_refs": [closeout_ref],
        "source_fingerprint": source_fingerprint,
        "work_unit_fingerprint": source_fingerprint,
    }
    dispatch["closeout_binding"] = binding
    dispatch["closeout_refs"] = [closeout_ref]
    dispatch["source_fingerprint"] = source_fingerprint
    dispatch["work_unit_fingerprint"] = source_fingerprint
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract["closeout_binding"] = binding
    prompt_contract["closeout_refs"] = [closeout_ref]
    prompt_contract["source_fingerprint"] = source_fingerprint
    prompt_contract["work_unit_fingerprint"] = source_fingerprint
    return binding


def _write_readiness_dispatch(study_root: Path, profile, dispatch: dict[str, object]) -> None:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{ACTION_TYPE}.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)


def _drop_opl_execution_authorization(dispatch: dict[str, object]) -> None:
    dispatch.pop("opl_execution_authorization", None)
    dispatch.pop("opl_provider_attempt", None)
    dispatch.pop("stage_attempt", None)
    prompt_contract = dispatch["prompt_contract"]
    assert isinstance(prompt_contract, dict)
    prompt_contract.pop("opl_execution_authorization", None)
    prompt_contract.pop("opl_provider_attempt", None)
    owner_route = dispatch["owner_route"]
    assert isinstance(owner_route, dict)
    owner_route.pop("opl_execution_authorization", None)
    owner_route.pop("opl_provider_attempt", None)


def _write_ready_literature_intelligence(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json",
        {
            "surface": "literature_intelligence_os",
            "status": "ready",
            "search_strategy": {
                "query": "diabetes mortality prediction",
                "mesh_terms": ["Diabetes Mellitus"],
                "keywords": ["diabetes mortality", "transportability"],
            },
            "search_date": "2026-06-06",
            "why_worth_doing": "Provider-backed evidence supports the current study framing.",
            "provider_provenance": [
                {
                    "provider_name": "pubmed",
                    "query": "diabetes mortality prediction",
                    "retrieved_at": "2026-06-06T08:00:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/pubmed.json"],
                },
                {
                    "provider_name": "crossref",
                    "query": "diabetes mortality guideline review",
                    "retrieved_at": "2026-06-06T08:01:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/crossref.json"],
                },
                {
                    "provider_name": "semantic_scholar",
                    "query": "diabetes mortality clinical neighbor",
                    "retrieved_at": "2026-06-06T08:02:00Z",
                    "response_status": "ok",
                    "source_refs": ["artifacts/medical_paper/provider_responses/semantic-scholar.json"],
                },
            ],
            "anchor_papers": ["pmid:12345"],
            "guidelines": ["guideline:TRIPOD+AI"],
            "systematic_reviews": ["doi:10.1000/systematic-review"],
            "journal_neighbor_refs": ["semantic_scholar:S2PAPER1"],
            "citation_ledger_refs": [
                "paper/evidence_ledger.json#pmid-12345",
                "paper/evidence_ledger.json#tripod-ai",
                "paper/evidence_ledger.json#systematic-review",
                "paper/evidence_ledger.json#semantic-S2PAPER1",
            ],
            "screening_decisions": [
                {
                    "ref": "pmid:12345",
                    "decision": "include",
                    "reason": "Study anchor.",
                }
            ],
        },
    )


def _write_target_journal_writing_layer(study_root: Path) -> None:
    _write_json(
        study_root / "paper" / "target_journal_writing_layer.json",
        {
            "surface": "target_journal_writing_layer",
            "schema_version": 1,
            "role": "ai_reviewer_quality_context",
            "target_journal_family": "general_internal_medicine",
            "near_neighbor_style_corpus": [
                {
                    "journal": "JAMA Internal Medicine",
                    "article_role": "near_neighbor",
                    "style_ref": "workspace_literature:jamainternmed-anchor",
                }
            ],
            "section_plan": {
                "Introduction": "clinical problem, evidence gap, objective",
                "Methods": "cohort, endpoint, analysis, bias controls",
                "Results": "primary finding before display references",
                "Discussion": "principal finding, prior work, interpretation, limitations",
            },
            "claim_to_paragraph_map": [
                {
                    "claim_id": "primary_claim",
                    "section": "Results",
                    "paragraph_role": "principal finding",
                    "evidence_refs": ["paper/evidence_ledger.json#primary_claim"],
                }
            ],
            "display_to_claim_map": [
                {
                    "display_id": "Figure 1",
                    "claim_id": "primary_claim",
                    "display_role": "supports primary finding",
                }
            ],
            "restrained_language_strategy": {
                "forbidden_phrases": ["proves", "definitively establishes"],
                "required_claim_qualifiers": ["was associated with", "may support"],
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )


def _write_ready_literature_provider_runtime_with_nested_intelligence(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json",
        {
            "surface": "literature_provider_runtime",
            "schema_version": 1,
            "status": "ready",
            "source_basis": "verified_literature_materialization",
            "source_refs": ["artifacts/publication_eval/literature_materialization.json"],
            "literature_intelligence_payload": {
                "search_strategy": {
                    "query": "primary-care diabetes phenotype treatment gap",
                    "mesh_terms": ["Diabetes Mellitus"],
                    "keywords": ["primary care", "phenotype", "treatment gap"],
                },
                "search_date": "2026-06-06",
                "searched_sources": ["artifacts/publication_eval/literature_materialization.json"],
                "provider_provenance": [
                    {
                        "provider_name": "pubmed",
                        "query": "primary-care diabetes phenotype treatment gap",
                        "retrieved_at": "2026-06-06T08:00:00Z",
                        "response_status": "ok",
                        "source_refs": ["artifacts/publication_eval/literature_materialization.json"],
                    },
                    {
                        "provider_name": "crossref",
                        "query": "primary-care diabetes guideline systematic review",
                        "retrieved_at": "2026-06-06T08:01:00Z",
                        "response_status": "ok",
                        "source_refs": ["artifacts/publication_eval/literature_materialization.json"],
                    },
                    {
                        "provider_name": "semantic_scholar",
                        "query": "primary-care diabetes phenotype neighbor",
                        "retrieved_at": "2026-06-06T08:02:00Z",
                        "response_status": "ok",
                        "source_refs": ["artifacts/publication_eval/literature_materialization.json"],
                    },
                ],
                "why_worth_doing": "Provider runtime evidence supports the DPCC phenotype and treatment-gap framing.",
                "anchor_papers": ["pmid:41469089"],
                "guidelines": ["doi:10.1136/fmch-2025-003765"],
                "systematic_reviews": ["doi:10.1038/s43856-023-00360-3"],
                "journal_neighbor_refs": ["semantic_scholar:S2PAPER1"],
                "high_score_neighbor_refs": [
                    {
                        "ref": "semantic_scholar:S2PAPER1",
                        "score": 0.91,
                        "score_source_ref": "semantic_scholar:verified-literature-materialization",
                    }
                ],
                "screening_decisions": [
                    {
                        "ref": "pmid:41469089",
                        "decision": "include",
                        "reason": "Current provider runtime anchor for the clinical context.",
                    }
                ],
                "citation_ledger_refs": [
                    "paper/evidence_ledger.json#pmid-41469089",
                    "paper/evidence_ledger.json#doi-10-1136-fmch-2025-003765",
                    "paper/evidence_ledger.json#doi-10-1038-s43856-023-00360-3",
                    "paper/evidence_ledger.json#semantic-S2PAPER1",
                ],
            },
        },
    )


def _write_target_journal_source_surfaces(study_root: Path) -> None:
    _write_json(
        study_root / "paper" / "medical_journal_style_corpus.json",
        {
            "surface": "medical_journal_style_corpus",
            "schema_version": 1,
            "source_refs": [
                {
                    "source_id": "jama_author_instructions",
                    "label": "JAMA Instructions for Authors",
                    "style_takeaway": "Use concise medical writing and quantify results with uncertainty.",
                },
                {
                    "source_id": "jama_network_open_neighbor",
                    "label": "JAMA Network Open diabetes prediction neighbor",
                    "style_takeaway": "State clinical context, objective, methods, results, and limitations plainly.",
                },
            ],
        },
    )
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "primary_mortality_claim",
                    "sections": ["Results"],
                    "evidence_items": [
                        {
                            "source_paths": [
                                "paper/results_narrative_map.json#primary_mortality_claim",
                                "paper/tables/table_catalog.json#T2",
                            ]
                        }
                    ],
                    "display_bindings": [
                        {
                            "display_id": "T2",
                            "display_role": "primary results table",
                        },
                        {
                            "display_id": "F2",
                            "display_role": "model performance figure",
                        },
                    ],
                    "prohibited_interpretations": [
                        "Do not imply causal attribution beyond the observational design."
                    ],
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {"display_id": "T2", "title": "Primary mortality attribution results"},
                {"display_id": "F2", "title": "Model performance and calibration"},
            ],
        },
    )
    _write_json(
        study_root / "paper" / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [{"figure_id": "F2", "claim_id": "primary_mortality_claim"}],
        },
    )
    _write_json(
        study_root / "paper" / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [{"table_id": "T2", "claim_id": "primary_mortality_claim"}],
        },
    )
    _write_json(
        study_root / "paper" / "results_narrative_map.json",
        {
            "schema_version": 1,
            "primary_result": "Primary mortality risk differences should be reported with uncertainty.",
        },
    )
    _write_json(
        study_root / "paper" / "medical_manuscript_blueprint.json",
        {
            "schema_version": 1,
            "sections": ["Introduction", "Methods", "Results", "Discussion"],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "schema_version": 1,
            "restraint_principles": [
                "Use associated with language.",
                "Keep causal language out of observational findings.",
            ],
        },
    )


def _write_revision_rebuttal_loop_sources(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::dm002::ai-reviewer-record::20260606T080000Z",
            "study_id": "002-dm-china-us-mortality-attribution",
            "schema_version": 1,
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
            },
            "gaps": [
                {
                    "gap_id": "gap-claim-restraint",
                    "gap_type": "claim",
                    "severity": "must_fix",
                    "summary": "Reviewer requested more restrained wording for the mortality gap claim.",
                    "evidence_refs": [
                        "paper/claim_evidence_map.json#C1",
                        "artifacts/stage_outputs/_body_authority/current_body/paper/evidence_ledger.json#C1",
                    ],
                }
            ],
            "quality_assessment": {
                "evidence_strength": {
                    "status": "blocked",
                    "summary": "The evidence ledger must be cited before rebuttal closure.",
                    "reviewer_revision_advice": "Add additional analysis or evidence repair before acceptance.",
                    "evidence_refs": ["paper/claim_evidence_map.json#C1"],
                }
            },
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::route-back",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "route_target": "write",
                    "route_key_question": "What same-line repair is required before package handoff?",
                    "route_rationale": "Reviewer concerns remain unresolved.",
                    "requires_controller_decision": True,
                    "evidence_refs": ["paper/review/review_ledger.json#gap-claim-restraint"],
                }
            ],
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "ai_reviewer_required": False,
                "policy_id": "publication_critique.default",
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "schema_version": "claim_evidence_map_v2",
            "claims": [
                {
                    "claim_id": "C1",
                    "sections": ["Results"],
                    "statement": "Observed diabetes mortality gap requires restrained reporting.",
                    "evidence_items": [
                        {
                            "item_id": "C1-main",
                            "source_paths": ["paper/results_narrative_map.json#C1"],
                            "summary": "Primary result supports a descriptive cohort difference.",
                            "support_level": "primary",
                        }
                    ],
                    "status": "supported_with_limitations",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper" / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [
                {
                    "item_id": "C1-main",
                    "kind": "analysis_result",
                    "summary": "Primary result ledger entry for the descriptive mortality gap.",
                    "source_paths": ["paper/results_narrative_map.json#C1"],
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "review" / "review_ledger.json",
        {
            "schema_version": 1,
            "status": "active",
            "concerns": [
                {
                    "concern_id": "gap-claim-restraint",
                    "reviewer_id": "ai_reviewer",
                    "severity": "major",
                    "status": "open",
                    "summary": "Reviewer requested more restrained wording for the mortality gap claim.",
                }
            ],
        },
    )


def _write_revision_rebuttal_loop_surface(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "revision_rebuttal_loop.json",
        {
            "surface": "revision_rebuttal_loop",
            "schema_version": 1,
            "status": "ready",
            "reviewer_comment_count": 1,
            "durable_refs": {
                "evidence_ledger_refs": [
                    str(
                        study_root
                        / "artifacts"
                        / "stage_outputs"
                        / "_body_authority"
                        / "paper_authority_cutover"
                        / "current_body"
                        / "paper"
                        / "evidence_ledger.json"
                    )
                ],
                "review_ledger_refs": [str(study_root / "paper" / "review" / "review_ledger.json")],
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )


def _write_readiness_surfaces_before_revision_rebuttal(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "literature_provider_runtime.json",
        {
            "surface": "literature_provider_runtime",
            "status": "ready",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "literature_scout.json",
        {
            "search_strategy": {"query": "diabetes mortality"},
            "search_date": "2026-06-06",
            "anchor_papers": ["pmid:25869581"],
            "guidelines": ["doi:10.1155/2018/4638327"],
            "journal_neighbor_refs": ["doi:10.5334/gh.1131"],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "study_line_selection.json",
        {
            "selected_line_id": "002-dm-china-us-mortality-attribution",
            "dimensions": {
                "novelty": 3,
                "clinical_relevance": 4,
                "data_fit": 4,
                "analysis_plasticity": 3,
                "external_validation": 3,
                "journal_fit": 3,
                "cost_risk": 2,
                "stop_threshold": "owner_review_required",
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "paper" / "medical_analysis_contract.json",
        {
            "surface": "archetype_specific_analysis_contract",
            "status": "resolved",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "required_analysis_packages": ["discrimination_metrics"],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "bounded_analysis_candidate_board.json",
        {
            "surface": "bounded_analysis_candidate_board",
            "candidates": [
                {
                    "analysis_package": "discrimination_metrics",
                    "target_claim": "Validate mortality risk discrimination.",
                    "expected_evidence_gain": "Quantify model discrimination.",
                    "cost_risk": "bounded",
                    "statistical_risk": "requires_precision_and_calibration_binding",
                    "clinical_interpretability": "owner-review-required-before-quality-claim",
                    "decision": "explore",
                    "decision_reason": "Required by the analysis contract.",
                }
            ],
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "stop_loss_memo.json",
        {
            "surface": "stop_loss_memo",
            "decision": "continue",
            "attempted_paths": ["complete_medical_paper_readiness_surface"],
            "evidence_gain_ceiling": "meaningful_revision_loop_expected",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_target_journal_writing_layer(study_root)
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "surface": "real_study_soak_matrix_evidence",
            "overall_status": "complete",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json",
        {
            "surface": "route_decision_orchestrator",
            "status": "ready",
            "route_decision": "proceed_to_baseline",
            "controller_decision_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            "controller_decision": {
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "statistical_discipline_operations.json",
        {
            "surface": "statistical_discipline_operations",
            "status": "ready",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )


def _write_stage_output_owner_receipt(study_root: Path, stage_id: str) -> None:
    _write_json(
        study_root / "artifacts" / "stage_outputs" / stage_id / "receipts" / "owner_receipt.json",
        {
            "surface": "stage_owner_receipt",
            "stage_id": stage_id,
            "status": "completed",
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    )


def _write_complete_soak_stage_refs(study_root: Path) -> None:
    for relative_ref in (
        "artifacts/stage_outputs/01-study_intake/receipts/owner_receipt.json",
        "artifacts/stage_outputs/01-study_intake/projection/current_owner_delta.json",
        "artifacts/stage_outputs/04-analysis_execution/analysis_run_record.json",
        "artifacts/stage_outputs/04-analysis_execution/primary_results_artifact_set.json",
        "artifacts/stage_outputs/05-evidence_synthesis/evidence_synthesis_matrix.json",
        "artifacts/medical_paper/stop_loss_memo.json",
        "artifacts/medical_paper/revision_rebuttal_loop.json",
        "artifacts/supervision/consumer/default_executor_execution/history.jsonl",
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
    ):
        _write_json(
            study_root / relative_ref,
            {
                "surface": "durable_stage_ref",
                "relative_ref": relative_ref,
                "quality_claim_authorized": False,
                "mechanical_projection_can_authorize_quality": False,
            },
        )


def _write_literature_materialization(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "publication_eval" / "literature_materialization.json",
        {
            "schema_version": 1,
            "records": [
                {
                    "record_id": "lit-001",
                    "title": "Guidelines on primary healthcare for type 2 diabetes in China, 2025",
                    "doi": "10.1136/fmch-2025-003765",
                    "pubmed": {"pmid": "41469089"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["background", "methods/context"],
                },
                {
                    "record_id": "lit-002",
                    "title": "Precision subclassification of type 2 diabetes: a systematic review",
                    "doi": "10.1038/s43856-023-00360-3",
                    "pubmed": {"pmid": "37798471"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["background", "methods/context"],
                },
            ],
        },
    )


def _write_mortality_literature_materialization(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "publication_eval" / "literature_materialization.json",
        {
            "schema_version": 1,
            "records": [
                {
                    "record_id": "mortality-anchor",
                    "title": "Development and validation of a predictive risk model for all-cause mortality in type 2 diabetes",
                    "doi": "10.1016/j.diabres.2015.02.015",
                    "pubmed": {"pmid": "25869581"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["background", "methods/context"],
                },
                {
                    "record_id": "mortality-systematic",
                    "title": "Systematic review of diabetes mortality prediction models",
                    "doi": "10.2337/dc08-1047",
                    "pubmed": {"pmid": "18809629"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["systematic review"],
                },
                {
                    "record_id": "mortality-guideline",
                    "title": "Guideline statement for diabetes mortality risk model reporting",
                    "doi": "10.1155/2018/4638327",
                    "pubmed": {"pmid": "30116741"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["guideline"],
                },
                {
                    "record_id": "mortality-neighbor",
                    "title": "Prediction of Five-Year Cardiovascular Disease Risk in People with Type 2 Diabetes Mellitus",
                    "doi": "10.5334/gh.1131",
                    "pubmed": {"pmid": "36051323"},
                    "materialization_status": "verified_pubmed",
                    "claim_links": ["neighbor"],
                },
            ],
        },
    )

__all__ = [name for name in globals() if not name.startswith("__")]
