from __future__ import annotations

from pathlib import Path

from .shared_base import dump_json


def write_medical_manuscript_blueprint_fixture(paper_root: Path) -> None:
    dump_json(
        paper_root / "medical_manuscript_blueprint.json",
        {
            "schema_version": 1,
            "surface": "medical_manuscript_blueprint",
            "authoring_provenance": {
                "owner": "ai_author",
                "source_kind": "medical_manuscript_blueprint",
                "policy_id": "medical_manuscript_blueprint_v1",
                "ai_reviewer_required": False,
            },
            "study_id": "002-early-residual-risk",
            "argument_sequence": [
                "clinical_problem",
                "evidence_gap",
                "study_objective",
                "target_population",
                "study_design",
                "main_findings_by_clinical_importance",
                "clinical_interpretation",
                "discussion_claim_boundary",
                "limitations",
            ],
            "clinical_problem": (
                "Postoperative endocrine follow-up after NF-PitNET surgery requires a clinically legible "
                "risk-stratification frame."
            ),
            "evidence_gap": (
                "Existing descriptive outcome reports do not fully define how preoperative information should "
                "shape early residual-risk interpretation."
            ),
            "study_objective": (
                "To evaluate whether a prespecified preoperative model supports restrained residual-risk "
                "interpretation in a retrospective cohort."
            ),
            "target_population": "Adults undergoing surgery for NF-PitNET with evaluable postoperative outcome data.",
            "study_design": "Retrospective single-center cohort study.",
            "main_findings_by_clinical_importance": [
                {
                    "rank": 1,
                    "section_id": "R1",
                    "clinical_finding": (
                        "The extended preoperative model improved calibration and decision-curve utility."
                    ),
                    "quantitative_support": ["Discrimination and decision utility favored the extended model."],
                    "clinical_meaning": (
                        "The result supports risk stratification language rather than treatment-threshold claims."
                    ),
                    "interpretation_boundary": "Associational prediction support only.",
                    "supporting_display_items": ["F4", "T1"],
                }
            ],
            "clinical_interpretation": (
                "Results should be interpreted as bounded prediction evidence for follow-up stratification."
            ),
            "claim_evidence_map": [
                {
                    "claim_id": "C1",
                    "statement": "The main manuscript claim is supported by mapped model-performance evidence.",
                    "status": "supported_main_text",
                    "paper_role": "main_text",
                    "evidence_item_count": 1,
                    "display_bindings": ["F4", "T1"],
                    "limitations": ["External transport validation is not established."],
                }
            ],
            "figure_table_rhetorical_roles": [
                {
                    "display_id": "F4",
                    "display_type": "figure",
                    "story_role": "threshold_interpretation",
                    "rhetorical_role": "Support restrained interpretation of decision thresholds.",
                    "interpretation_boundary": "No formal recommendation threshold is proposed.",
                }
            ],
            "discussion_claim_boundary": (
                "The Discussion must keep conclusions within internal validation and avoid treatment escalation."
            ),
            "limitations": [
                "Single-center retrospective design.",
                "External transport validation is not established.",
            ],
            "journal_voice_target": {
                "voice": "neutral_clinical_original_research",
                "reader_expectation": (
                    "clinical problem -> evidence gap -> objective -> main findings -> clinical interpretation -> limitations"
                ),
                "style_sources": [
                    "Zeiger biomedical research paper clear-writing and paper-text model",
                    "Gopen and Swan reader-expectation information flow",
                    "JAMA concise, specific, informative, non-overstated medical-journal wording",
                    "Elsevier medical manuscript audience, relevance, and avoid-overstatement guidance",
                    "JAMA Network Open original investigation prose exemplars",
                ],
            },
            "source_refs": [
                str(paper_root / "results_narrative_map.json"),
                str(paper_root / "claim_evidence_map.json"),
                str(paper_root / "figure_semantics_manifest.json"),
                str(paper_root / "evidence_ledger.json"),
            ],
        },
    )


def write_medical_prose_review_fixture(paper_root: Path, *, verdict: str) -> None:
    normalized_verdict = verdict if verdict in {"clear", "revise", "block"} else "block"
    dump_json(
        paper_root / "review" / "medical_prose_review.json",
        {
            "schema_version": 1,
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "medical_prose_review",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
            },
            "medical_journal_prose_quality": {
                "status": "ready" if normalized_verdict == "clear" else "partial" if normalized_verdict == "revise" else "blocked",
                "overall_style_verdict": normalized_verdict,
                "summary": (
                    "AI reviewer judged the manuscript prose clear enough for medical journal style."
                    if normalized_verdict == "clear"
                    else "AI reviewer judged that the manuscript still reads too much like a work report."
                ),
                "section_level_diagnosis": {
                    "introduction": "Clinical problem, evidence gap, and objective are evaluated by AI reviewer.",
                    "results": "Findings should lead sentences before figure/table citations.",
                    "discussion": "Interpretation should remain restrained and limitation-aware.",
                },
                "representative_bad_sentences": (
                    [] if normalized_verdict == "clear" else ["Figure 1 shows that the model worked well."]
                ),
                "representative_rewrites": (
                    []
                    if normalized_verdict == "clear"
                    else [
                        {
                            "before": "Figure 1 shows that the model worked well.",
                            "after": (
                                "The extended model improved risk stratification across the prespecified "
                                "threshold range, with the display used to show the supporting operating characteristics."
                            ),
                        }
                    ]
                ),
                "route_back_recommendation": {
                    "required": normalized_verdict != "clear",
                    "route_target": "none" if normalized_verdict == "clear" else "write",
                    "reason": (
                        "Medical journal prose is clear."
                        if normalized_verdict == "clear"
                        else "Rewrite work-report residue before quality closure."
                    ),
                },
            },
            "mechanical_safety_flags": [],
            "source_refs": [
                str(paper_root / "draft.md"),
                str(paper_root / "medical_manuscript_blueprint.json"),
                str(paper_root / "claim_evidence_map.json"),
                str(paper_root / "results_narrative_map.json"),
                str(paper_root / "figure_semantics_manifest.json"),
                str(paper_root / "review" / "review_ledger.json"),
            ],
        },
    )
