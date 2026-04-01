from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_quest(
    tmp_path: Path,
    *,
    medicalized: bool,
    ama_defaults: bool,
    figure_caption_override: str | None = None,
    include_methods_manifest: bool | None = None,
    include_results_narrative_map: bool | None = None,
    include_figure_semantics_manifest: bool | None = None,
    include_derived_analysis_manifest: bool | None = None,
    figure_led_results: bool | None = None,
    include_reproducibility_supplement: bool | None = None,
    include_endpoint_provenance_note: bool | None = None,
    include_operational_method_labels: bool | None = None,
    include_complete_model_registry: bool | None = None,
    include_complete_results_sections: bool | None = None,
    include_model_method_details: bool | None = None,
    include_case_mix_boundary_fields: bool | None = None,
    align_missing_data_policy_ids: bool | None = None,
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
    if include_derived_analysis_manifest is None:
        include_derived_analysis_manifest = medicalized
    if figure_led_results is None:
        figure_led_results = not medicalized
    if include_reproducibility_supplement is None:
        include_reproducibility_supplement = medicalized
    if include_endpoint_provenance_note is None:
        include_endpoint_provenance_note = medicalized
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

    if medicalized:
        draft_text = (
            "# Draft\n\n"
            "## Abstract\n\n"
            "We assessed whether an extended preoperative model could improve residual-risk estimation.\n"
            "\n## Results\n\n"
            "The primary question was whether the extended preoperative model improved discrimination and calibration "
            "over the preoperative baseline. The answer was yes, with concordant gains in discrimination, calibration, "
            "and clinical utility that remained directionally consistent across the prespecified strata.\n"
        )
        review_text = (
            "---\n"
            'title: "Study title"\n'
            "---\n\n"
            "## Methods\n\n"
            "This retrospective single-center cohort included adults undergoing surgery between January 2018 and December 2024. "
            "The endpoint was based on the audited removal_rate field and should be interpreted as a working proxy for early residual status with an explicit 3-month MRI provenance caveat. "
            "The calibration-first label was operationally defined as optimizing model selection on calibration and clinical utility rather than on discrimination alone.\n\n"
            "## Results\n\n"
            "The main results section was organized around the prespecified research questions rather than around "
            "individual display items. The extended preoperative model improved calibration and clinical utility, and "
            "the subgroup analyses supported the same clinical direction of effect.\n"
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

    (paper_root / "draft.md").write_text(draft_text, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").write_text(review_text, encoding="utf-8")
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F4",
                    "title": figure_title,
                    "caption": figure_caption,
                    "paper_role": "main_text",
                    "export_paths": ["paper/figures/F4.png"],
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
                    "title": "Patient characteristics",
                    "caption": table_caption,
                    "paper_role": "main_text",
                    "asset_paths": ["paper/tables/T1.md"],
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
        renderer_contract = renderer_contract_override or {
            "figure_semantics": "evidence",
            "renderer_family": "python",
            "selection_rationale": (
                "This result figure is regenerated from the locked Python analysis stack so the plotted "
                "evidence remains coupled to the audited statistical outputs."
            ),
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        }
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


def test_build_report_flags_forbidden_terms_and_missing_ama_defaults(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(
        tmp_path,
        medicalized=False,
        ama_defaults=False,
        include_methods_manifest=False,
        include_results_narrative_map=False,
        include_figure_semantics_manifest=False,
        include_derived_analysis_manifest=False,
        figure_led_results=True,
        include_reproducibility_supplement=False,
        include_endpoint_provenance_note=False,
        include_operational_method_labels=False,
    )

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert "ama_pdf_defaults_missing" in report["blockers"]
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    assert "results_narrative_map_missing_or_incomplete" in report["blockers"]
    assert "figure_semantics_manifest_missing_or_incomplete" in report["blockers"]
    assert "derived_analysis_manifest_missing_or_incomplete" in report["blockers"]
    assert "figure_table_led_results_narration_present" in report["blockers"]
    assert "manuscript_safe_reproducibility_supplement_missing_or_incomplete" in report["blockers"]
    assert "endpoint_provenance_note_missing_or_unapplied" in report["blockers"]
    assert "undefined_methodology_labels_present" in report["blockers"]
    assert report["ama_csl_present"] is False
    assert report["ama_pdf_defaults_present"] is False
    assert any(hit["phrase"] == "deployment-facing" for hit in report["top_hits"])
    assert any(hit["phrase"] == "online service:" for hit in report["top_hits"])
    assert any(hit["phrase"] == "roc_auc" for hit in report["top_hits"])
    assert any(hit["phrase"] == "average_precision" for hit in report["top_hits"])
    assert any(hit["phrase"] == "brier_score" for hit in report["top_hits"])
    assert any(hit["phrase"] == "calibration_intercept" for hit in report["top_hits"])
    assert any(hit["phrase"] == "calibration_slope" for hit in report["top_hits"])
    assert any(hit["phrase"] == "Figure 1 shows" for hit in report["top_hits"])
    assert any(hit["phrase"] == "calibration-first" for hit in report["top_hits"])
    assert any("endpoint_provenance_note" in hit["pattern_id"] for hit in report["top_hits"])


def test_build_report_clears_when_assets_are_medicalized_and_ama_defaults_exist(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "clear"
    assert report["blockers"] == []
    assert report["ama_csl_present"] is True
    assert report["ama_pdf_defaults_present"] is True
    assert report["top_hits"] == []


def test_build_report_blocks_generic_tool_disclosure_labels_in_caption(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        figure_caption_override=(
            "This figure summarizes operating characteristics. "
            "Publication-grade refinement remains external "
            "(open-source: https://example.com/repo; online service: https://figure-service.example.com)."
        ),
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(hit["phrase"] == "open-source:" for hit in report["top_hits"])
    assert any(hit["phrase"] == "online service:" for hit in report["top_hits"])


def test_build_report_blocks_poster_style_figure_export_annotations(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        generated_figure_text_override=(
            "<svg><text>Sources: grouped-center summary.md</text>"
            "<text>Why this matters</text></svg>\n"
        ),
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(hit["phrase"] == "Sources:" for hit in report["top_hits"])
    assert any(hit["phrase"] == "Why this matters" for hit in report["top_hits"])


def test_build_report_blocks_when_secondary_model_entry_is_incomplete(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_complete_model_registry=False,
    )

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]


def test_build_report_blocks_when_model_entry_omits_input_scope_and_construction_details(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_model_method_details=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"])
    assert "input_scope" in excerpts
    assert "feature_construction" in excerpts
    assert "predictor_selection_strategy" in excerpts


def test_build_report_blocks_when_model_entry_omits_comparison_rationale(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    manifest_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "methods_implementation_manifest.json"
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["model_registry"][1].pop("comparison_rationale", None)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"])
    assert "comparison_rationale" in excerpts


def test_build_report_blocks_when_case_mix_and_applicability_boundary_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_case_mix_boundary_fields=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_implementation_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"])
    assert "case_mix_summary" in excerpts
    assert "applicability_boundary" in excerpts


def test_build_report_blocks_when_missing_data_policy_ids_are_inconsistent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        align_missing_data_policy_ids=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "missing_data_policy_inconsistent" in report["blockers"]
    assert any(hit["pattern_id"] == "missing_data_policy_inconsistent" for hit in report["top_hits"])


def test_build_report_blocks_when_main_text_figure_is_not_used_in_results_narrative_map(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    narrative_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "results_narrative_map.json"
    payload = json.loads(narrative_path.read_text(encoding="utf-8"))
    for section in payload["sections"]:
        section["supporting_display_items"] = ["T1"]
    narrative_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "results_narrative_map_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "results_narrative_map_missing_main_figure_reference" for hit in report["top_hits"])


def test_build_report_blocks_when_later_results_section_is_incomplete(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_complete_results_sections=False,
    )

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "blocked"
    assert "results_narrative_map_missing_or_incomplete" in report["blockers"]


def test_build_report_blocks_when_evidence_figure_uses_html_svg_renderer(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        renderer_contract_override={
            "figure_semantics": "evidence",
            "renderer_family": "html_svg",
            "selection_rationale": "The figure uses a hand-crafted SVG poster layout.",
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "figure_semantics_manifest_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "figure_semantics_manifest" for hit in report["top_hits"])
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"] if hit["pattern_id"] == "figure_semantics_manifest")
    assert "renderer_family" in excerpts
    assert "html_svg" in excerpts


def test_build_report_blocks_when_renderer_contract_allows_fallback(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        renderer_contract_override={
            "figure_semantics": "evidence",
            "renderer_family": "python",
            "selection_rationale": "The evidence plot should stay on the audited Python stack.",
            "fallback_on_failure": True,
            "failure_action": "block_and_fix_environment",
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "figure_semantics_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"] if hit["pattern_id"] == "figure_semantics_manifest")
    assert "fallback_on_failure" in excerpts


def test_run_controller_stops_then_enqueues_medical_surface_message(tmp_path: Path, monkeypatch) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, medicalized=False, ama_defaults=False)
    stopped: list[tuple[str, str, str]] = []

    def fake_post_quest_control(*, daemon_url: str, quest_id: str, action: str, source: str) -> dict:
        stopped.append((daemon_url, quest_id, action))
        return {"ok": True, "status": "stopped", "source": source}

    monkeypatch.setattr(module.med_deepscientist_transport, "post_quest_control", fake_post_quest_control)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        daemon_url="http://127.0.0.1:20999",
    )

    assert stopped == [("http://127.0.0.1:20999", "002-early-residual-risk", "stop")]
    assert result["intervention_enqueued"] is True
    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert len(queue["pending"]) == 1
    content = queue["pending"][0]["content"]
    assert "deployment-facing" in content
    assert "Do not advertise tooling in figure captions." in content
    assert "AMA" in content
    assert "methods_implementation_manifest.json" in content
    assert "results_narrative_map.json" in content
    assert "figure_semantics_manifest.json" in content
    assert "derived_analysis_manifest.json" in content
    assert "manuscript_safe_reproducibility_supplement.json" in content
    assert "endpoint_provenance_note.md" in content
    assert result["top_hits"]


def test_run_controller_without_daemon_url_enqueues_but_does_not_stop(tmp_path: Path, monkeypatch) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, medicalized=False, ama_defaults=False)
    stopped: list[tuple[str, str, str]] = []

    def fake_post_quest_control(*, daemon_url: str, quest_id: str, action: str, source: str) -> dict:
        stopped.append((daemon_url, quest_id, action))
        return {"ok": True, "status": "stopped", "source": source}

    monkeypatch.setattr(module.med_deepscientist_transport, "post_quest_control", fake_post_quest_control)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        daemon_url=None,
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert stopped == []
    assert result["stop_result"] is None
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1


def test_build_surface_state_uses_runtime_protocol_quest_state(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    seen: dict[str, object] = {}

    def fake_load_runtime_state(path: Path) -> dict[str, object]:
        seen["quest_root"] = path
        return {"status": "patched", "quest_id": quest_root.name}

    monkeypatch.setattr(module.quest_state, "load_runtime_state", fake_load_runtime_state)

    state = module.build_surface_state(quest_root)

    assert seen == {"quest_root": quest_root}
    assert state.runtime_state["status"] == "patched"
