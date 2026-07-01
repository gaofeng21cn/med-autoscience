from __future__ import annotations

from typing import Any

CONTROLLER_ID = "descriptive_registry_evidence_materializer"


def _claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "cohort-denominator-accounting",
            "statement": (
                "The Hunan Obesity Alliance registry provides an auditable denominator for a descriptive "
                "multicenter obesity phenotype report."
            ),
            "status": "supported_for_source_layer_accounting",
            "paper_role": "main_text",
            "display_bindings": ["F1"],
            "sections": ["Methods: Study design and cohort", "Results: Cohort Denominator and Source Layers"],
            "evidence_items": [
                {
                    "item_id": "cohort-flow-source-layer-display",
                    "support_level": "direct",
                    "source_paths": ["paper/cohort_flow.json", "paper/figures/generated/F1.layout.json"],
                }
            ],
        },
        {
            "claim_id": "baseline-characteristics-supported",
            "statement": (
                "Baseline demographic, anthropometric, metabolic comorbidity, and psychobehavioral data "
                "availability can be reported descriptively by registry source."
            ),
            "status": "supported_descriptive",
            "paper_role": "main_text",
            "display_bindings": ["T1"],
            "sections": ["Results: Baseline characteristics"],
            "evidence_items": [
                {
                    "item_id": "table1-baseline-characteristics",
                    "support_level": "direct",
                    "source_paths": ["paper/baseline_characteristics_schema.json", "paper/tables/generated/T1_baseline_characteristics.csv"],
                }
            ],
        },
        {
            "claim_id": "bmi-metabolic-burden-supported",
            "statement": (
                "BMI-category strata support descriptive reporting of metabolic comorbidity burden using "
                "available-record denominators."
            ),
            "status": "supported_descriptive",
            "paper_role": "main_text",
            "display_bindings": ["T2"],
            "sections": ["Results: BMI and metabolic comorbidity burden"],
            "evidence_items": [
                {
                    "item_id": "table2-bmi-metabolic-burden",
                    "support_level": "direct",
                    "source_paths": [
                        "paper/phenotype_gap_summary_schema.json",
                        "paper/tables/T2_phenotype_gap_summary.csv",
                        "paper/tables/generated/T2_phenotype_gap_summary.csv",
                    ],
                }
            ],
        },
        {
            "claim_id": "center-psychobehavioral-support-supported",
            "statement": (
                "Center completeness and Xiangya2 psychobehavioral availability can be reported as "
                "descriptive support surfaces without alliance-wide generalization."
            ),
            "status": "supported_descriptive_boundary",
            "paper_role": "main_text",
            "display_bindings": ["T3"],
            "sections": ["Results: Center completeness and Xiangya2 subcohort"],
            "evidence_items": [
                {
                    "item_id": "table3-center-psychobehavioral-support",
                    "support_level": "direct",
                    "source_paths": [
                        "paper/transition_site_support_summary_schema.json",
                        "paper/tables/T3_transition_site_support_summary.csv",
                        "paper/tables/generated/T3_transition_site_support_summary.csv",
                    ],
                }
            ],
        },
        {
            "claim_id": "descriptive-cross-sectional-boundary",
            "statement": (
                "The manuscript is limited to a STROBE-aligned descriptive cross-sectional registry atlas "
                "and does not support population-level burden, cause-and-effect, future-risk, "
                "or treatment-response claims."
            ),
            "status": "boundary_supported",
            "paper_role": "main_text",
            "display_bindings": ["F1", "T1", "T2", "T3"],
            "sections": ["Introduction", "Methods: Statistical analysis", "Discussion", "Conclusions"],
            "evidence_items": [
                {
                    "item_id": "descriptive-boundary-contract",
                    "support_level": "direct_boundary",
                    "source_paths": ["study.yaml", "paper/medical_reporting_contract.json", "paper/evidence_ledger.json"],
                }
            ],
        },
    ]


def _ledger_claims_from_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ledger_claims: list[dict[str, Any]] = []
    for claim in claims:
        evidence = []
        for item in claim.get("evidence_items") or []:
            evidence.append(
                {
                    "evidence_id": item["item_id"],
                    "kind": "descriptive_registry_table" if "table" in item["item_id"] else "contract",
                    "support_level": item["support_level"],
                    "source_paths": list(item["source_paths"]),
                    "summary": claim["statement"],
                }
            )
        claim_id = str(claim["claim_id"])
        ledger_claims.append(
            {
                "claim_id": claim_id,
                "statement": claim["statement"],
                "status": claim["status"],
                "submission_scope": "main_text_with_limitations",
                "evidence": evidence,
                "gaps": [
                    {
                        "gap_id": f"{claim_id}-descriptive-scope-limitation",
                        "description": (
                            "The evidence supports descriptive registry reporting only and does not establish "
                            "population-level burden, future risk, cause-and-effect relationships, "
                            "or treatment response."
                        ),
                        "submission_impact": (
                            "Keep the claim bounded to available-record denominators and preserve the "
                            "limitation in Results, Discussion, and Conclusions."
                        ),
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": f"{claim_id}-maintain-claim-guardrail",
                        "priority": "required_before_submission",
                        "description": (
                            "Bind the claim to its listed display and source paths, and avoid prevalence, "
                            "cause-and-effect, future-risk, or treatment-response wording in the manuscript."
                        ),
                    }
                ],
            }
        )
    return ledger_claims


def _results_narrative_map() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sections": [
            {
                "section_id": "cohort_source_layer_accounting",
                "section_title": "Cohort denominator and source layers",
                "research_question": (
                    "What analytic denominator and source-layer structure support the descriptive registry atlas?"
                ),
                "direct_answer": (
                    "F1 and T1 define the available analytic denominator and source-stratified baseline context."
                ),
                "supporting_display_items": ["F1", "T1"],
                "key_quantitative_findings": [
                    "Analytic records are reported from the QC deidentified registry table.",
                    "Baseline variables use available-record denominators by registry source.",
                ],
                "clinical_meaning": (
                    "The source-layer accounting defines where the descriptive findings can be interpreted."
                ),
                "boundary": (
                    "Descriptive denominator accounting only; not a population-level burden "
                    "or cause-and-effect estimate."
                ),
            },
            {
                "section_id": "bmi_metabolic_comorbidity_burden",
                "section_title": "BMI category and metabolic comorbidity burden",
                "research_question": (
                    "How are metabolic comorbidities distributed across BMI-category strata in available records?"
                ),
                "direct_answer": (
                    "T2 reports metabolic comorbidity burden by BMI category using available-record denominators."
                ),
                "supporting_display_items": ["T2"],
                "key_quantitative_findings": [
                    "BMI strata are summarized with record counts, BMI medians, and comorbidity denominators.",
                    "Unknown binary values are excluded from available denominators rather than counted as negative.",
                ],
                "clinical_meaning": (
                    "The table supports descriptive prioritization of phenotype burden within the observed registry."
                ),
                "boundary": "No treatment-response, future-risk, or population-level burden claim is made.",
            },
            {
                "section_id": "center_psychobehavioral_support",
                "section_title": "Center completeness and Xiangya2 psychobehavioral support",
                "research_question": (
                    "What center completeness and Xiangya2 psychobehavioral coverage are available for reporting?"
                ),
                "direct_answer": (
                    "T3 reports exported-center support and Xiangya2 psychobehavioral availability as boundary evidence."
                ),
                "supporting_display_items": ["T3"],
                "key_quantitative_findings": [
                    "Center counts and analytic-record availability are reported as support surfaces.",
                    "PHQ-9 and GAD-7 availability are interpreted as Xiangya2 subcohort support only.",
                ],
                "clinical_meaning": (
                    "Psychobehavioral measures can support a subcohort description but not alliance-wide generalization."
                ),
                "boundary": "Subcohort availability is not generalized beyond observed coverage.",
            },
        ],
    }


def _closed_charter_expectations(now: str) -> list[dict[str, Any]]:
    notes = {
        "study_charter": "Study charter is linked and used as the primary manuscript boundary authority.",
        "strobe_cross_sectional_analysis_plan": "Reporting contract and checklist close STROBE-aligned descriptive reporting requirements.",
        "cohort_flow": "Active F1 display-pack exports support denominator and source-layer accounting.",
        "table1_baseline_characteristics": "T1 baseline characteristics table is materialized from the QC deidentified registry table.",
        "center_completeness_summary": "T3 closes center completeness with exported-center and available-record summaries.",
        "bmi_metabolic_comorbidity_burden": "T2 closes BMI-category metabolic comorbidity burden with available-record denominators.",
        "xiangya2_psychobehavioral_subcohort_analysis": "T3 closes the Xiangya2 psychobehavioral availability surface with subcohort boundary guardrails.",
        "missingness_and_qc_supplement": "Missingness and QC support is linked through the descriptive registry materialization receipt.",
        "evidence_ledger": "Evidence ledger records claim, display, and charter expectation closures.",
        "claim_guardrails": (
            "Claim map and evidence ledger preserve descriptive guardrails against population-level burden "
            "and cause-and-effect overstatement."
        ),
    }
    return [
        {
            "expectation_key": "minimum_sci_ready_evidence_package",
            "expectation_text": key,
            "status": "closed",
            "closed_at": now,
            "note": note,
        }
        for key, note in notes.items()
    ]


def _reporting_checklist(now: str) -> dict[str, Any]:
    evidence = [
        "paper/medical_reporting_contract.json",
        "paper/baseline_characteristics_schema.json",
        "paper/phenotype_gap_summary_schema.json",
        "paper/transition_site_support_summary_schema.json",
        "paper/display_registry.json",
    ]
    return {
        "schema_version": 1,
        "status": "closed",
        "closed_at": now,
        "domains": [
            {
                "domain_id": domain_id,
                "status": "closed",
                "closed_at": now,
                "evidence": evidence,
            }
            for domain_id in (
                "source_of_data_and_participants",
                "candidate_predictors_and_missing_data",
                "outcome_definition_and_follow_up",
            )
        ],
    }


def _medical_analysis_contract(study_payload: dict[str, Any], now: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "materialized",
        "materialized_at": now,
        "controller": CONTROLLER_ID,
        "study_id": study_payload.get("study_id"),
        "analysis_role": "descriptive_registry_evidence",
        "allowed_claim_scope": [
            "descriptive_cross_sectional_registry_atlas",
            "available_record_denominator_summaries",
            "xiangya2_psychobehavioral_subcohort_boundary",
        ],
        "disallowed_claim_scope": list(study_payload.get("truth_surface_policy", {}).get("redlines") or []),
        "source_tables": {
            "canonical_interchange_table": (
                study_payload.get("data_management_policy", {}).get("canonical_interchange_table")
            ),
            "data_dictionary": study_payload.get("data_management_policy", {}).get("data_dictionary"),
            "quality_report": study_payload.get("data_management_policy", {}).get("quality_report"),
        },
        "outputs": [
            "paper/baseline_characteristics_schema.json",
            "paper/phenotype_gap_summary_schema.json",
            "paper/transition_site_support_summary_schema.json",
            "paper/tables/T2_phenotype_gap_summary.csv",
            "paper/tables/T3_transition_site_support_summary.csv",
        ],
    }



__all__ = [
    "_claim_rows",
    "_closed_charter_expectations",
    "_ledger_claims_from_claims",
    "_medical_analysis_contract",
    "_reporting_checklist",
    "_results_narrative_map",
]
