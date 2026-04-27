from . import shared_base as _shared_base


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared_base)

def make_quest(
    tmp_path: Path,
    *,
    medicalized: bool,
    ama_defaults: bool,
    figure_caption_override: str | None = None,
    include_methods_manifest: bool | None = None,
    include_results_narrative_map: bool | None = None,
    include_figure_semantics_manifest: bool | None = None,
    include_claim_evidence_map: bool | None = None,
    include_evidence_ledger: bool | None = None,
    include_derived_analysis_manifest: bool | None = None,
    figure_led_results: bool | None = None,
    include_reproducibility_supplement: bool | None = None,
    include_endpoint_provenance_note: bool | None = None,
    include_review_ledger: bool | None = None,
    include_operational_method_labels: bool | None = None,
    include_complete_model_registry: bool | None = None,
    include_complete_results_sections: bool | None = None,
    include_model_method_details: bool | None = None,
    include_case_mix_boundary_fields: bool | None = None,
    align_missing_data_policy_ids: bool | None = None,
    include_structured_introduction: bool | None = None,
    include_structured_methods: bool | None = None,
    include_structured_results: bool | None = None,
    include_question_mark_prose: bool | None = None,
    generated_figure_text_override: str | None = None,
    renderer_contract_override: dict[str, object] | None = None,
) -> Path:
    quest_root = tmp_path / "runtime" / "quests" / "002-early-residual-risk"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    paper_root = worktree_root / "paper"
    if include_methods_manifest is None:
        include_methods_manifest = medicalized
    if include_results_narrative_map is None:
        include_results_narrative_map = medicalized
    if include_figure_semantics_manifest is None:
        include_figure_semantics_manifest = medicalized
    if include_claim_evidence_map is None:
        include_claim_evidence_map = medicalized
    if include_evidence_ledger is None:
        include_evidence_ledger = medicalized
    if include_derived_analysis_manifest is None:
        include_derived_analysis_manifest = medicalized
    if figure_led_results is None:
        figure_led_results = not medicalized
    if include_reproducibility_supplement is None:
        include_reproducibility_supplement = medicalized
    if include_endpoint_provenance_note is None:
        include_endpoint_provenance_note = medicalized
    if include_review_ledger is None:
        include_review_ledger = medicalized
    if include_operational_method_labels is None:
        include_operational_method_labels = medicalized
    if include_complete_model_registry is None:
        include_complete_model_registry = medicalized
    if include_complete_results_sections is None:
        include_complete_results_sections = medicalized
    if include_model_method_details is None:
        include_model_method_details = medicalized
    if include_case_mix_boundary_fields is None:
        include_case_mix_boundary_fields = medicalized
    if align_missing_data_policy_ids is None:
        align_missing_data_policy_ids = medicalized
    if include_structured_introduction is None:
        include_structured_introduction = medicalized
    if include_structured_methods is None:
        include_structured_methods = medicalized
    if include_structured_results is None:
        include_structured_results = medicalized
    if include_question_mark_prose is None:
        include_question_mark_prose = False

    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "002-early-residual-risk",
            "status": "running",
            "active_run_id": "run-1",
            "active_interaction_id": "progress-1",
            "pending_user_message_count": 0,
        },
    )
    dump_json(quest_root / ".ds" / "user_message_queue.json", {"version": 1, "pending": [], "completed": []})
    (quest_root / ".ds" / "interaction_journal.jsonl").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / ".ds" / "interaction_journal.jsonl").write_text("", encoding="utf-8")
    (quest_root / "baselines" / "local" / "baseline-1").mkdir(parents=True, exist_ok=True)
    (quest_root / "baselines" / "local" / "baseline-1" / "verification.md").write_text(
        "# Verification\n\n"
        "- keep the `removal_rate` 3-month MRI provenance caveat explicit and re-audit it in the methods\n",
        encoding="utf-8",
    )

    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
                "compile_report_path": "paper/build/compile_report.json",
            },
        },
    )
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown": "paper/build/review_manuscript.md",
            "output_pdf": "paper/paper.pdf",
            "defaults_path": "paper/latex/review_defaults.yaml",
        },
    )
    (paper_root / "paper.pdf").write_text("%PDF", encoding="utf-8")

    if include_review_ledger:
        _write_review_ledger(paper_root / "review" / "review_ledger.json")

    if medicalized:
        endpoint_statement = (
            "The endpoint was based on the audited removal_rate field and should be interpreted as a working proxy "
            "for early residual status with an explicit 3-month MRI provenance caveat.\n\n"
        )
        introduction_section = (
            "## Introduction\n\n"
            "Persistent postoperative endocrine burden remains clinically relevant after surgery for clinically nonfunctioning pituitary tumors because surveillance intensity, hormone replacement planning, and long-horizon follow-up all depend on how residual endocrine risk is framed for the treating team.\n\n"
            "Recent postoperative endocrine and prediction studies have reported center-level outcomes, model comparisons, and recovery patterns, but they still leave a gap between broad outcome description and a narrow follow-up stratifier that can be read directly at a fixed postoperative landmark.\n\n"
            "In this retrospective single-center cohort, we therefore evaluated whether a manuscript-safe postoperative model could support a narrow medical follow-up decision route by comparing calibration, prediction error, and clinical utility across prespecified candidate packages.\n\n"
        )
        methods_section = (
            "## Materials and Methods\n\n"
            "### Study design and cohort\n\n"
            "This retrospective single-center cohort included adults undergoing surgery between January 2018 and December 2024.\n\n"
            "### Variable definition and measurement\n\n"
            "Predictors, outcome fields, and audited landmark variables were extracted from the curated study registry and reviewed against the endpoint provenance caveat.\n\n"
            "### Model building\n\n"
            "The manuscript-facing model registry defined the baseline package, the extended preoperative package, and the comparison rationale for each candidate model.\n\n"
            "### Validation framework\n\n"
            "All candidate packages were evaluated under the shared calibration-first selection rule using repeated cross-validation, with discrimination, calibration, and decision utility reported together.\n\n"
        )
        results_section = (
            "## Results\n\n"
            "### Cohort characteristics\n\n"
            "The cohort accounting and endpoint totals remained stable after applying the prespecified inclusion and exclusion rules.\n\n"
            "### Unified validation and clinical utility\n\n"
            "The extended preoperative model improved calibration and clinical utility in the primary comparison while preserving the intended medical interpretation boundary.\n\n"
            "### Added-value assessment of model complexity\n\n"
            "The complexity audit showed that any gain in discrimination had to be judged alongside calibration and decision utility rather than in isolation.\n"
        )
        draft_text = "# Draft\n\n## Abstract\n\nWe assessed whether an extended preoperative model could improve residual-risk estimation.\n\n"
        review_text = "---\n" 'title: "Study title"\n' "---\n\n"
        if include_structured_introduction:
            draft_text += introduction_section
            review_text += introduction_section
        else:
            draft_text += (
                "## Introduction\n\n"
                "Persistent postoperative endocrine burden remains clinically relevant after surgery, and many recent studies have explored related outcomes without fully resolving how follow-up should be stratified in practice.\n\n"
            )
            review_text += (
                "## Introduction\n\n"
                "Persistent postoperative endocrine burden remains clinically relevant after surgery, and many recent studies have explored related outcomes without fully resolving how follow-up should be stratified in practice.\n\n"
            )
        if include_structured_methods:
            draft_text += methods_section
            review_text += methods_section
        else:
            draft_text += (
                "## Materials and Methods\n\n"
                "This retrospective single-center cohort included adults undergoing surgery between January 2018 and December 2024, and the endpoint was interpreted within the audited postoperative route.\n\n"
            )
            review_text += (
                "## Materials and Methods\n\n"
                "This retrospective single-center cohort included adults undergoing surgery between January 2018 and December 2024, and the endpoint was interpreted within the audited postoperative route.\n\n"
            )
        if include_endpoint_provenance_note:
            draft_text += endpoint_statement
            review_text += endpoint_statement
        if include_structured_results:
            draft_text += results_section
            review_text += results_section
        else:
            draft_text += (
                "## Results\n\n"
                "The main manuscript results were clinically coherent and broadly favored the extended preoperative model across the headline metrics.\n"
            )
            review_text += (
                "## Results\n\n"
                "The main manuscript results were clinically coherent and broadly favored the extended preoperative model across the headline metrics.\n"
            )
        figure_title = "Threshold-specific operating characteristics for the extended preoperative model"
        figure_caption = "This figure summarizes operating characteristics and risk-group profiles."
        table_caption = "This table summarizes cohort characteristics."
    else:
        draft_text = (
            "# Draft\n\n"
            "## Abstract\n\n"
            "We kept the deployment-facing mainline and baseline-comparable comparison on the locked cohort. "
            "The model improved roc_auc and average_precision while reducing brier_score.\n"
        )
        review_text = (
            "---\n"
            'title: "Study title"\n'
            "---\n\n"
            "## Methods\n\n"
            "The calibration-first comparison framework used v2026-03-28 labels and internal A1 versus A0 naming.\n\n"
            "The deployment-facing story stayed on the locked cohort and baseline-comparable surface. "
            "Calibration_intercept and calibration_slope were reported directly.\n"
        )
        figure_title = "Operating thresholds and deployment-facing risk stratification"
        figure_caption = (
            "The locked cohort and validation contract remain explicit. "
            "online service: https://figures.example/refine. Publication-grade figure refinement is recommended with deepscientist."
        )
        table_caption = "Baseline-comparable summary on the locked cohort."
    if figure_caption_override is not None:
        figure_caption = figure_caption_override
    if figure_led_results:
        draft_text += "\n## Results\n\nFigure 1 shows the main model comparison. Table 1 summarizes the subgroup results.\n"
        review_text += "\nFigure 1 shows the primary discrimination result. Table 1 summarizes the cohort-level findings.\n"
    if include_question_mark_prose:
        draft_text += "\nCould this model be enough for postoperative follow-up?\n"
        review_text += "\nCan this model become the preferred route for postoperative follow-up?\n"

    (paper_root / "draft.md").write_text(draft_text, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").write_text(review_text, encoding="utf-8")
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F4",
                    "template_id": "roc_curve_binary",
                    "renderer_family": "r_ggplot2",
                    "input_schema_id": "binary_prediction_curve_inputs_v1",
                    "qc_profile": "publication_evidence_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_evidence_curve",
                        "layout_sidecar_path": "paper/figures/generated/F4.layout.json",
                        "issues": [],
                    },
                    "title": figure_title,
                    "caption": figure_caption,
                    "paper_role": "main_text",
                    "export_paths": ["paper/figures/F4.png", "paper/figures/F4.pdf"],
                }
            ],
        },
    )
    generated_figure_text = generated_figure_text_override or "<svg><text>clean figure</text></svg>\n"
    (paper_root / "figures" / "generated" / "F4.svg").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "figures" / "generated" / "F4.svg").write_text(generated_figure_text, encoding="utf-8")
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "table_shell_id": "table1_baseline_characteristics",
                    "input_schema_id": "baseline_characteristics_schema_v1",
                    "qc_profile": "publication_table_baseline",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Patient characteristics",
                    "caption": table_caption,
                    "paper_role": "main_text",
                    "asset_paths": ["paper/tables/T1.csv", "paper/tables/T1.md"],
                }
            ],
        },
    )
    (paper_root / "latex").mkdir(parents=True, exist_ok=True)

    if ama_defaults:
        (paper_root / "latex" / "american-medical-association.csl").write_text("csl", encoding="utf-8")
        (paper_root / "latex" / "review_defaults.yaml").write_text(
            "from: markdown\n"
            "to: pdf\n"
            "pdf-engine: xelatex\n"
            "citeproc: true\n"
            "csl: american-medical-association.csl\n",
            encoding="utf-8",
        )
    else:
        (paper_root / "latex" / "review_defaults.yaml").write_text(
            "from: markdown\n"
            "to: pdf\n"
            "pdf-engine: xelatex\n"
            "citeproc: true\n",
            encoding="utf-8",
        )

    if include_methods_manifest:
        missing_data_policy_id = "preop_missingness_policy_v1"
        derived_missing_data_policy_id = (
            missing_data_policy_id if align_missing_data_policy_ids else "derived_missingness_policy_v2"
        )
        reproducibility_missing_data_policy_id = (
            missing_data_policy_id if align_missing_data_policy_ids else "supplement_missingness_policy_v3"
        )
        model_registry = [
            {
                "model_id": "M1",
                "manuscript_name": "Extended preoperative model",
                "role": "primary",
                "family": "Gradient boosting classifier",
                "origin": "Built from the prespecified preoperative variable set with clinically motivated feature transformations.",
                "inputs": ["clinical variables", "preoperative imaging descriptors"],
                "target": "Early residual risk",
                "fit_procedure": "Repeated nested cross-validation with locked tuning policy and final pooled out-of-fold estimation.",
                "selection_rationale": "Primary manuscript model because it balanced discrimination, calibration, and clinical utility.",
                "comparison_rationale": "Included as the main clinically useful preoperative model to compare against the reference logistic baseline and the prespecified benchmark families.",
                "claim_boundary": "Associational risk prediction only; no mechanistic or causal claim.",
                **(
                    {
                        "input_scope": "Preoperative-only evidence base defined before surgery and excluding pathology or postoperative variables.",
                        "feature_construction": "Continuous imaging measures were combined with clinically motivated categorical encodings before model fitting.",
                        "predictor_selection_strategy": "Candidate preoperative predictors were prespecified from the data dictionary and retained according to the locked modeling workflow.",
                    }
                    if include_model_method_details
                    else {}
                ),
            }
        ]
        if include_complete_model_registry:
            model_registry.append(
                {
                    "model_id": "M2",
                    "manuscript_name": "Pathology-augmented comparison model",
                    "role": "extension",
                    "family": "Logistic regression",
                    "origin": "Extended the same preoperative evidence base by adding postoperative pathology features for contextual comparison.",
                    "inputs": ["clinical variables", "preoperative imaging descriptors", "pathology features"],
                    "target": "Early residual risk",
                    "fit_procedure": "Repeated nested cross-validation with the same outer resampling structure as the primary model.",
                    "selection_rationale": "Contextual extension to quantify whether postoperative pathology materially changed discrimination or utility.",
                    "comparison_rationale": "Included to quantify how much postoperative pathology altered performance beyond the preoperative evidence base without redefining the main preoperative claim.",
                    "claim_boundary": "Extension comparison only; not part of the preoperative clinical-use recommendation.",
                    **(
                        {
                            "input_scope": "Uses the same preoperative evidence base as the primary model, with postoperative pathology added only for contextual comparison.",
                            "feature_construction": "Retained the clinically informed preoperative encoding scheme and appended pathology descriptors without redefining the endpoint.",
                            "predictor_selection_strategy": "Started from the locked preoperative variable set and added pathology variables as a prespecified extension rather than as a de novo feature search.",
                        }
                        if include_model_method_details
                        else {}
                    ),
                }
            )
        else:
            model_registry.append(
                {
                    "model_id": "M2",
                    "manuscript_name": "Pathology-augmented comparison model",
                    "family": "Logistic regression",
                    "inputs": ["clinical variables", "pathology features"],
                    "target": "Early residual risk",
                }
            )
        dump_json(
            paper_root / "methods_implementation_manifest.json",
            {
                "schema_version": 1,
                "study_design": {
                    "center": "Single tertiary referral center.",
                    "time_window": "January 2018 to December 2024.",
                    "study_design": "Retrospective cohort study.",
                    "ethics": "Approved by the institutional review board with waiver of informed consent where applicable.",
                    "inclusion_criteria": "Adults with NF-PitNET undergoing first surgery and evaluable postoperative outcome data.",
                    "exclusion_criteria": "Repeat surgery, missing core endpoint data, or incomplete baseline records.",
                    "cohort_definition": "Adults undergoing resection for NF-PitNET.",
                    "endpoint_definition": "Early residual risk within the prespecified postoperative window.",
                    "variable_definitions": "Predictors were prespecified clinical and imaging variables defined in the frozen data dictionary.",
                    "split_strategy": "Locked train/validation/test workflow with patient-level separation.",
                    "missing_data_strategy": "Predefined imputation and missingness indicators where required.",
                    "missing_data_policy_id": missing_data_policy_id,
                    **(
                        {
                            "case_mix_summary": "The cohort was dominated by macroadenomas treated at a tertiary referral center, with relatively few small tumors.",
                            "applicability_boundary": "The manuscript should primarily position conclusions for larger surgically treated NF-PitNETs rather than for incidentally detected small tumors.",
                        }
                        if include_case_mix_boundary_fields
                        else {}
                    ),
                },
                "model_registry": model_registry,
                "software_stack": [
                    {"package": "python", "version": "3.12", "role": "runtime"},
                    {"package": "scikit-learn", "version": "1.5.0", "role": "model training"},
                ],
                "statistical_analysis": {
                    "primary_metrics": ["AUC", "calibration", "decision-curve analysis"],
                    "subgroup_strategy": "Prespecified subgroup comparisons with interaction-aware reporting.",
                },
                "causal_boundary": {
                    "claim_level": "associational",
                    "allowed_language": "risk stratification and association",
                    "not_allowed": "causal effect claims",
                },
                "method_labels": (
                    [
                        {
                            "label": "calibration-first",
                            "operational_definition": "Model ranking prioritized calibration and decision-curve performance before discrimination gains.",
                            "implementation_anchor": "Nested selection report and threshold utility analysis.",
                        }
                    ]
                    if include_operational_method_labels
                    else []
                ),
            },
        )

    if include_results_narrative_map:
        sections = [
            {
                "section_id": "R1",
                "section_title": "Primary performance and clinical utility",
                "research_question": "Does the extended preoperative model improve early residual-risk assessment?",
                "direct_answer": "Yes. The model improved discrimination, calibration, and decision-curve utility.",
                "supporting_display_items": ["F4", "T1"],
                "key_quantitative_findings": [
                    "Discrimination improved over the baseline clinical model.",
                    "Clinical utility gains persisted across decision thresholds.",
                ],
                "clinical_meaning": "The model can support preoperative risk stratification rather than merely restating descriptive differences.",
                "boundary": "The result supports prediction and utility, not causal inference.",
            }
        ]
        if include_complete_results_sections:
            sections.append(
                {
                    "section_id": "R2",
                    "section_title": "Threshold interpretation and subgroup consistency",
                    "research_question": "Were threshold-level summaries and subgroup patterns clinically consistent with the primary finding?",
                    "direct_answer": "Yes. The threshold summaries were illustrative rather than prescriptive, and subgroup patterns did not reverse the main clinical direction.",
                    "supporting_display_items": ["F4", "T1"],
                    "key_quantitative_findings": [
                        "Illustrative threshold summaries did not imply a recommended cut-off.",
                        "Subgroup contrasts preserved the same qualitative direction of effect."
                    ],
                    "clinical_meaning": "Supports careful translation of risk estimates without overclaiming a universal intervention threshold.",
                    "boundary": "Exploratory subgroup and threshold interpretation only; not a transportability claim.",
                }
            )
        else:
            sections.append(
                {
                    "section_id": "R2",
                    "section_title": "Threshold interpretation and subgroup consistency",
                    "research_question": "Were threshold-level summaries and subgroup patterns clinically consistent with the primary finding?",
                    "supporting_display_items": ["F4", "T1"],
                    "key_quantitative_findings": [
                        "Illustrative threshold summaries did not imply a recommended cut-off."
                    ],
                    "clinical_meaning": "Supports careful translation of risk estimates.",
                }
            )
        dump_json(
            paper_root / "results_narrative_map.json",
            {
                "schema_version": 1,
                "sections": sections,
            },
        )

    if include_figure_semantics_manifest:
        renderer_contract = {
            "figure_semantics": "evidence",
            "renderer_family": "r_ggplot2",
            "template_id": "roc_curve_binary",
            "selection_rationale": (
                "This result figure is regenerated from the locked R analysis stack so the plotted "
                "evidence remains coupled to the audited statistical outputs."
            ),
            "layout_qc_profile": "publication_evidence_curve",
            "required_exports": ["png", "pdf"],
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        }
        if renderer_contract_override is not None:
            renderer_contract.update(renderer_contract_override)
        dump_json(
            paper_root / "figure_semantics_manifest.json",
            {
                "schema_version": 1,
                "figures": [
                    {
                        "figure_id": "F4",
                        "story_role": "threshold_interpretation",
                        "research_question": "How should threshold-level summaries be interpreted clinically without overstating them as recommended cut-offs?",
                        "direct_message": "Threshold-level operating summaries are illustrative translation aids rather than recommended intervention cut-offs.",
                        "clinical_implication": "Supports preoperative communication and shared decision support while preserving uncertainty around treatment action thresholds.",
                        "interpretation_boundary": "The figure does not establish an externally validated treatment threshold.",
                        "panel_messages": [
                            {
                                "panel_id": "A",
                                "message": "Threshold summaries quantify trade-offs across illustrative operating points."
                            },
                            {
                                "panel_id": "B",
                                "message": "Risk strata visualize distributional separation rather than mandated clinical bins."
                            },
                        ],
                        "legend_glossary": [
                            {
                                "term": "treat all",
                                "explanation": "Assumes every patient is managed as high risk at the chosen threshold."
                            },
                            {
                                "term": "treat none",
                                "explanation": "Assumes no patient is managed as high risk at the chosen threshold."
                            },
                        ],
                        "threshold_semantics": "Thresholds are illustrative operating points used to show trade-offs, not recommended cut-offs.",
                        "stratification_basis": "Risk groups were formed for display and are not prespecified clinical categories.",
                        "recommendation_boundary": "No formal recommendation threshold is proposed from this figure.",
                        "renderer_contract": renderer_contract,
                    }
                ],
            },
        )

    if include_claim_evidence_map:
        dump_json(
            paper_root / "claim_evidence_map.json",
            {
                "schema_version": 1,
                "claims": [
                    {
                        "claim_id": "C1",
                        "statement": "The main manuscript route is supported by the threshold interpretation figure and the baseline table.",
                        "status": "supported_main_text",
                        "paper_role": "main_text",
                        "display_bindings": ["F4", "T1"],
                        "sections": ["results", "discussion"],
                        "evidence_items": [
                            {
                                "item_id": "EXP-001",
                                "support_level": "primary",
                                "source_paths": ["paper/results_narrative_map.json"],
                            }
                        ],
                        "limitations": ["Illustrative threshold interpretation only."],
                    }
                ],
            },
        )

    if include_evidence_ledger:
        dump_json(
            paper_root / "evidence_ledger.json",
            {
                "schema_version": 1,
                "claims": [
                    {
                        "claim_id": "C1",
                        "statement": "The audited manuscript keeps one main-text claim with direct quantitative support and an explicit hold boundary.",
                        "status": "supported",
                        "submission_scope": "main_text",
                        "evidence": [
                            {
                                "evidence_id": "EV1",
                                "kind": "display",
                                "source_paths": ["paper/claim_evidence_map.json", "paper/results_narrative_map.json"],
                                "support_level": "direct",
                                "summary": "The threshold interpretation figure and the baseline table support the retained main-text statement.",
                            }
                        ],
                        "gaps": [
                            {
                                "gap_id": "G1",
                                "description": "External transport validation is still pending for any treatment-facing escalation language.",
                                "submission_impact": "Keep the claim inside an interpretation boundary and out of recommendation language.",
                            }
                        ],
                        "recommended_actions": [
                            {
                                "action_id": "A1",
                                "priority": "required",
                                "description": "Retain conservative manuscript wording until transport validation is earned.",
                            }
                        ],
                    }
                ],
            },
        )

    if include_derived_analysis_manifest:
        dump_json(
            paper_root / "derived_analysis_manifest.json",
            {
                "schema_version": 1,
                "analyses": [
                    {
                        "analysis_id": "A1",
                        "linked_display_items": ["F4", "T1"],
                        "purpose": "Summarize threshold-level trade-offs and subgroup-facing interpretation after the primary model comparison.",
                        "data_source": "Repeated outer-resampling predictions and the locked analysis tables.",
                        "derivation_procedure": "Operating characteristics were summarized from pooled out-of-fold predictions across the prespecified threshold grid.",
                        "resampling_design": "Repeated nested cross-validation with patient-level separation.",
                        "refit_policy": "Models were refit within each outer split under the locked tuning policy before pooled summarization.",
                        "missing_data_handling": "Used the same predefined imputation policy as the main analysis.",
                        "missing_data_policy_id": derived_missing_data_policy_id,
                        "correlation_or_collinearity_assessment": "Not applicable for this threshold-level summary because no new multivariable coefficient model was fit.",
                        "interpretation_boundary": "Supports interpretation of the primary model output and not an externally transportable treatment rule."
                    }
                ],
            },
        )

    if include_reproducibility_supplement:
        dump_json(
            paper_root / "manuscript_safe_reproducibility_supplement.json",
            {
                "schema_version": 1,
                "software_versions": [
                    {"package": "python", "version": "3.12"},
                    {"package": "scikit-learn", "version": "1.5.0"},
                ],
                "random_seed_policy": "Fixed seeds across repeated nested validation with the manifest recorded in the experiment package.",
                "key_hyperparameters": [
                    {"model_id": "M1", "parameters": {"max_depth": 3, "learning_rate": 0.05}}
                ],
                "missing_data_strategy": "Median imputation plus missingness indicators where prespecified.",
                "missing_data_policy_id": reproducibility_missing_data_policy_id,
                "metric_definitions": [
                    {"metric": "AUC", "definition": "Area under the ROC curve."},
                    {"metric": "Net benefit", "definition": "Decision-curve net benefit across prespecified thresholds."},
                ],
            },
        )

    if include_endpoint_provenance_note:
        (paper_root / "endpoint_provenance_note.md").write_text(
            "# Endpoint Provenance Note\n\n"
            "- endpoint_name: removal_rate\n"
            "- provenance_caveat: In the frozen cohort, `removal_rate` is treated as a working early residual / non-GTR label and retains an explicit 3-month MRI provenance caveat.\n"
            "- manuscript_required_statement: The endpoint was based on the audited removal_rate field and should be interpreted as a working proxy for early residual status with an explicit 3-month MRI provenance caveat.\n",
            encoding="utf-8",
        )

    return quest_root


def _write_time_to_event_direct_migration_surface(quest_root: Path, *, include_f5: bool) -> None:
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "status": "resolved",
            "display_shell_plan": TIME_TO_EVENT_DIRECT_MIGRATION_DISPLAY_PLAN,
        },
    )
    figure_entries = [
        {
            "figure_id": "F1",
            "template_id": "cohort_flow_figure",
            "renderer_family": "python",
            "input_schema_id": "cohort_flow_shell_inputs_v1",
            "qc_profile": "publication_illustration_flow",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_illustration_flow",
                "layout_sidecar_path": "paper/figures/generated/F1.layout.json",
                "issues": [],
            },
            "title": "Cohort derivation and endpoint inventory",
            "caption": "Cohort flow and endpoint inventory for the formal analysis cohort.",
            "paper_role": "main_text",
            "export_paths": [
                "paper/figures/F1_cohort_flow.png",
                "paper/figures/F1_cohort_flow.svg",
                "paper/figures/F1_cohort_flow.pdf",
            ],
        },
        {
            "figure_id": "F2",
            "template_id": "time_to_event_discrimination_calibration_panel",
            "renderer_family": "python",
            "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
            "qc_profile": "publication_evidence_curve",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_evidence_curve",
                "layout_sidecar_path": "paper/figures/generated/F2.layout.json",
                "issues": [],
            },
            "title": "Discrimination and grouped calibration",
            "caption": "Primary endpoint discrimination and grouped calibration.",
            "paper_role": "main_text",
            "export_paths": ["paper/figures/F2_validation.png", "paper/figures/F2_validation.pdf"],
        },
        {
            "figure_id": "F3",
            "template_id": "time_to_event_risk_group_summary",
            "renderer_family": "python",
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "qc_profile": "publication_survival_curve",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_survival_curve",
                "layout_sidecar_path": "paper/figures/generated/F3.layout.json",
                "issues": [],
            },
            "title": "Primary risk-group summary",
            "caption": "Predicted versus observed five-year risk and observed event concentration across prespecified tertiles.",
            "paper_role": "main_text",
            "export_paths": ["paper/figures/F3_risk_group_summary.png", "paper/figures/F3_risk_group_summary.pdf"],
        },
        {
            "figure_id": "F4",
            "template_id": "time_to_event_decision_curve",
            "renderer_family": "python",
            "input_schema_id": "time_to_event_decision_curve_inputs_v1",
            "qc_profile": "publication_decision_curve",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_decision_curve",
                "layout_sidecar_path": "paper/figures/generated/F4.layout.json",
                "issues": [],
            },
            "title": "Time-to-event decision curve",
            "caption": "Clinical utility at the prespecified five-year horizon.",
            "paper_role": "main_text",
            "export_paths": ["paper/figures/F4_dca.png", "paper/figures/F4_dca.pdf"],
        },
    ]
    if include_f5:
        figure_entries.append(
            {
                "figure_id": "F5",
                "template_id": "multicenter_generalizability_overview",
                "renderer_family": "python",
                "input_schema_id": "multicenter_generalizability_inputs_v1",
                "qc_profile": "publication_multicenter_overview",
                "qc_result": {
                    "status": "pass",
                    "checked_at": "2026-04-03T10:00:00+00:00",
                    "engine_id": "display_layout_qc_v1",
                    "qc_profile": "publication_multicenter_overview",
                    "layout_sidecar_path": "paper/figures/generated/F5.layout.json",
                    "issues": [],
                },
                "title": "Internal multicenter generalizability",
                "caption": "Center-level generalizability summary for the internal multicenter evaluation.",
                "paper_role": "main_text",
                "export_paths": ["paper/figures/F5_generalizability.png", "paper/figures/F5_generalizability.pdf"],
            }
        )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": figure_entries,
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "table_shell_id": "table1_baseline_characteristics",
                    "input_schema_id": "baseline_characteristics_schema_v1",
                    "qc_profile": "publication_table_baseline",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Patient characteristics",
                    "caption": "Baseline characteristics of the modeling cohort.",
                    "paper_role": "main_text",
                    "asset_paths": ["paper/tables/T1.csv", "paper/tables/T1.md"],
                },
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Time-to-event performance summary",
                    "caption": "Performance summary across primary and supportive endpoints.",
                    "paper_role": "main_text",
                    "asset_paths": ["paper/tables/T2.md"],
                },
            ],
        },
    )
    semantics_entries = [
        {
            "figure_id": "F1",
            "story_role": "study_setup",
            "research_question": "How was the analysis cohort derived and how were the primary endpoints inventoried?",
            "direct_message": "The analytic cohort and endpoint inventory were prespecified before model evaluation.",
            "clinical_implication": "Defines the denominator and endpoint framing for all downstream performance claims.",
            "interpretation_boundary": "Describes cohort derivation and endpoint accounting only.",
            "panel_messages": [{"panel_id": "A", "message": "The cohort derivation is numerically explicit."}],
            "legend_glossary": [{"term": "endpoint inventory", "explanation": "Lists the paper-facing endpoints carried into evaluation."}],
            "threshold_semantics": "No decision threshold is encoded in this illustration.",
            "stratification_basis": "No risk stratification is implied by the cohort flow shell.",
            "recommendation_boundary": "No clinical recommendation is proposed from the cohort flow shell.",
            "renderer_contract": {
                "figure_semantics": "illustration",
                "renderer_family": "python",
                "template_id": "cohort_flow_figure",
                "selection_rationale": "The cohort flow shell is rendered from the audited illustration pipeline.",
                "layout_qc_profile": "publication_illustration_flow",
                "required_exports": ["png", "svg", "pdf"],
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
        {
            "figure_id": "F2",
            "story_role": "performance_validation",
            "research_question": "Did the primary endpoint show aligned discrimination and grouped calibration?",
            "direct_message": "The primary endpoint showed concordant discrimination and grouped calibration support.",
            "clinical_implication": "Supports calibrated time-to-event risk communication in the main manuscript.",
            "interpretation_boundary": "Internal validation only; no transport claim.",
            "panel_messages": [{"panel_id": "A", "message": "Discrimination and grouped calibration are shown together."}],
            "legend_glossary": [{"term": "grouped calibration", "explanation": "Observed event-free probability across prespecified risk groups."}],
            "threshold_semantics": "No treatment threshold is proposed by the validation panel.",
            "stratification_basis": "Risk groups were prespecified for paper-facing calibration display.",
            "recommendation_boundary": "The panel supports validation, not a clinical intervention threshold.",
            "renderer_contract": {
                "figure_semantics": "evidence",
                "renderer_family": "python",
                "template_id": "time_to_event_discrimination_calibration_panel",
                "selection_rationale": "The validation panel stays on the audited direct-migration template.",
                "layout_qc_profile": "publication_evidence_curve",
                "required_exports": ["png", "pdf"],
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
        {
            "figure_id": "F3",
            "story_role": "risk_stratification",
            "research_question": "Did tertile-based grouping concentrate observed events and separate five-year risk?",
            "direct_message": "Observed five-year events concentrated in the highest tertile and were absent in the low-risk tertile.",
            "clinical_implication": "Supports clinically interpretable risk layering in the main manuscript.",
            "interpretation_boundary": "Shows tertile-based five-year risk separation rather than a full survival-curve reconstruction.",
            "panel_messages": [{"panel_id": "A", "message": "Predicted and observed five-year risks rise stepwise from low to high tertiles."}],
            "legend_glossary": [{"term": "risk tertile", "explanation": "Ordered groups formed from predicted five-year risk."}],
            "threshold_semantics": "No intervention threshold is encoded in the tertile summary.",
            "stratification_basis": "Groups are derived from the prespecified manuscript five-year risk stratification.",
            "recommendation_boundary": "Risk-group separation does not by itself define a treatment rule.",
            "renderer_contract": {
                "figure_semantics": "evidence",
                "renderer_family": "python",
                "template_id": "time_to_event_risk_group_summary",
                "selection_rationale": "The manuscript requires the audited two-panel tertile summary rather than a grouped KM fallback.",
                "layout_qc_profile": "publication_survival_curve",
                "required_exports": ["png", "pdf"],
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
        {
            "figure_id": "F4",
            "story_role": "clinical_utility",
            "research_question": "Did the model preserve clinical utility across the prespecified horizon?",
            "direct_message": "Net benefit remained positive across the prespecified threshold range.",
            "clinical_implication": "Supports horizon-aware clinical utility interpretation without overclaiming treatment cut-offs.",
            "interpretation_boundary": "The curve is horizon-specific and does not establish a universal threshold.",
            "panel_messages": [{"panel_id": "A", "message": "Net benefit is summarized over the prespecified threshold range."}],
            "legend_glossary": [{"term": "net benefit", "explanation": "Clinical utility relative to treat-all and treat-none references."}],
            "threshold_semantics": "Thresholds are illustrative operating points, not recommended cut-offs.",
            "stratification_basis": "The decision-curve display is threshold-based rather than group-based.",
            "recommendation_boundary": "No single intervention threshold is recommended from this figure.",
            "renderer_contract": {
                "figure_semantics": "evidence",
                "renderer_family": "python",
                "template_id": "time_to_event_decision_curve",
                "selection_rationale": "The horizon-aware decision curve stays on the audited direct-migration template.",
                "layout_qc_profile": "publication_decision_curve",
                "required_exports": ["png", "pdf"],
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
    ]
    if include_f5:
        semantics_entries.append(
            {
                "figure_id": "F5",
                "story_role": "generalizability",
                "research_question": "Did the internal multicenter assessment preserve support across centers?",
                "direct_message": "Center-level estimates remained directionally aligned with the overall performance signal.",
                "clinical_implication": "Supports cautious internal generalizability framing in the manuscript discussion.",
                "interpretation_boundary": "Internal center-level support only; not external transport validation.",
                "panel_messages": [{"panel_id": "A", "message": "Center-level interval support is summarized explicitly."}],
                "legend_glossary": [{"term": "center support", "explanation": "Center-level estimate with uncertainty interval."}],
                "threshold_semantics": "No treatment threshold is encoded in the generalizability overview.",
                "stratification_basis": "Centers are displayed as prespecified data-partition units rather than risk strata.",
                "recommendation_boundary": "The overview does not establish external transportability on its own.",
                "renderer_contract": {
                    "figure_semantics": "evidence",
                    "renderer_family": "python",
                    "template_id": "multicenter_generalizability_overview",
                    "selection_rationale": "The center-level overview remains on the audited multicenter template.",
                    "layout_qc_profile": "publication_multicenter_overview",
                    "required_exports": ["png", "pdf"],
                    "fallback_on_failure": False,
                    "failure_action": "block_and_fix_environment",
                },
            }
        )
    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": semantics_entries,
        },
    )
    narrative_sections = [
        {
            "section_id": "R1",
            "section_title": "Cohort derivation and baseline definition",
            "research_question": "How was the formal analysis cohort defined?",
            "direct_answer": "The cohort derivation and endpoint inventory were prespecified before evaluation.",
            "supporting_display_items": ["F1", "T1"],
            "key_quantitative_findings": ["Cohort flow and baseline structure were fixed before model evaluation."],
            "clinical_meaning": "Defines the clinical denominator for the current analysis.",
            "boundary": "Descriptive cohort accounting only.",
        },
        {
            "section_id": "R2",
            "section_title": "Primary validation and risk stratification",
            "research_question": "Did the primary endpoint support performance and risk separation?",
            "direct_answer": "Yes. Discrimination, grouped calibration, and grouped survival separation were directionally consistent.",
            "supporting_display_items": ["F2", "F3"],
            "key_quantitative_findings": ["Performance and survival separation remained aligned across the prespecified displays."],
            "clinical_meaning": "Supports the manuscript's risk-stratification framing.",
            "boundary": "Internal validation only.",
        },
        {
            "section_id": "R3",
            "section_title": "Clinical utility",
            "research_question": "Did the model preserve clinical utility at the main horizon?",
            "direct_answer": "Yes. Net benefit remained favorable across the prespecified threshold range.",
            "supporting_display_items": ["F4", "T2"],
            "key_quantitative_findings": ["Clinical utility remained favorable at the manuscript horizon."],
            "clinical_meaning": "Supports threshold-aware clinical interpretation without overclaiming a treatment rule.",
            "boundary": "No universal threshold recommendation is proposed.",
        },
    ]
    if include_f5:
        narrative_sections.append(
            {
                "section_id": "R4",
                "section_title": "Internal multicenter generalizability",
                "research_question": "Was the internal multicenter signal directionally preserved?",
                "direct_answer": "Yes. Center-level support remained directionally aligned with the overall estimate.",
                "supporting_display_items": ["F5"],
                "key_quantitative_findings": ["Center-level support remained within a clinically interpretable range."],
                "clinical_meaning": "Supports cautious generalizability framing within the internal multicenter setting.",
                "boundary": "Internal center-level support only; not external transport validation.",
            }
        )
    dump_json(
        paper_root / "results_narrative_map.json",
        {
            "schema_version": 1,
            "sections": narrative_sections,
        },
    )
