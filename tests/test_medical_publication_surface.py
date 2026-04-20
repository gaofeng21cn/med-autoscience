from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from med_autoscience import display_registry

TIME_TO_EVENT_DIRECT_MIGRATION_DISPLAY_PLAN = [
    {
        "display_id": "cohort_flow",
        "display_kind": "figure",
        "requirement_key": "cohort_flow_figure",
        "catalog_id": "F1",
    },
    {
        "display_id": "discrimination_calibration",
        "display_kind": "figure",
        "requirement_key": "time_to_event_discrimination_calibration_panel",
        "catalog_id": "F2",
    },
    {
        "display_id": "km_risk_stratification",
        "display_kind": "figure",
        "requirement_key": "time_to_event_risk_group_summary",
        "catalog_id": "F3",
    },
    {
        "display_id": "decision_curve",
        "display_kind": "figure",
        "requirement_key": "time_to_event_decision_curve",
        "catalog_id": "F4",
    },
    {
        "display_id": "multicenter_generalizability",
        "display_kind": "figure",
        "requirement_key": "multicenter_generalizability_overview",
        "catalog_id": "F5",
    },
    {
        "display_id": "baseline_characteristics",
        "display_kind": "table",
        "requirement_key": "table1_baseline_characteristics",
        "catalog_id": "T1",
    },
    {
        "display_id": "time_to_event_performance_summary",
        "display_kind": "table",
        "requirement_key": "table2_time_to_event_performance_summary",
        "catalog_id": "T2",
    },
]


def _canonicalize_registry_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return normalized
    if display_registry.is_evidence_figure_template(normalized):
        return display_registry.get_evidence_figure_spec(normalized).template_id
    if display_registry.is_illustration_shell(normalized):
        return display_registry.get_illustration_shell_spec(normalized).shell_id
    if display_registry.is_table_shell(normalized):
        return display_registry.get_table_shell_spec(normalized).shell_id
    return normalized


def full_id(value: str) -> str:
    return _canonicalize_registry_id(value)


def _normalize_namespaced_ids(payload: Any) -> Any:
    if isinstance(payload, dict):
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized_value = _normalize_namespaced_ids(value)
            if key in {"requirement_key", "template_id", "shell_id", "table_shell_id"} and isinstance(
                normalized_value, str
            ):
                normalized_value = _canonicalize_registry_id(normalized_value)
            normalized[key] = normalized_value
        return normalized
    if isinstance(payload, list):
        return [_normalize_namespaced_ids(item) for item in payload]
    return payload


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_payload = _normalize_namespaced_ids(payload)
    path.write_text(json.dumps(normalized_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_review_ledger(path: Path, *, summary: str = "Clarify the endpoint boundary in Results.") -> None:
    dump_json(
        path,
        {
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer_1",
                    "summary": summary,
                    "severity": "major",
                    "status": "open",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                }
            ],
        },
    )


def _write_study_charter(study_root: Path, *, study_id: str = "002-early-residual-risk") -> Path:
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    dump_json(
        charter_path,
        {
            "schema_version": 1,
            "charter_id": f"charter::{study_id}::v1",
            "study_id": study_id,
            "publication_objective": "Deliver a manuscript-safe residual-risk paper package.",
            "paper_quality_contract": {
                "frozen_at_startup": True,
                "downstream_contract_roles": {
                    "evidence_ledger": "records evidence against evidence expectations",
                    "review_ledger": "records review closure against review expectations",
                    "final_audit": "audits readiness against the charter contract",
                },
            },
        },
    )
    return charter_path


def _paper_root_from_quest(quest_root: Path) -> Path:
    return quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"


def _attach_study_charter_context(monkeypatch, module, tmp_path: Path, quest_root: Path) -> Path:
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 002-early-residual-risk\n", encoding="utf-8")
    _write_study_charter(study_root)

    paper_root = _paper_root_from_quest(quest_root)
    monkeypatch.setattr(
        module,
        "resolve_paper_root_context",
        lambda _: SimpleNamespace(
            paper_root=paper_root,
            worktree_root=paper_root.parent,
            quest_root=quest_root,
            study_id="002-early-residual-risk",
            study_root=study_root,
        ),
        raising=False,
    )
    return study_root


def _attach_public_anchor_study_context(monkeypatch, module, tmp_path: Path, quest_root: Path) -> Path:
    study_root = tmp_path / "studies" / "004-public-anchor-route"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(
        "study_id: 004-public-anchor-route\n"
        "public_data_anchors:\n"
        "  - dataset_id: mapping-pituitary\n"
        "    role: anatomy_anchor\n"
        "  - dataset_id: geo-gse169498\n"
        "    role: biology_anchor\n",
        encoding="utf-8",
    )
    _write_study_charter(study_root, study_id="004-public-anchor-route")

    paper_root = _paper_root_from_quest(quest_root)

    monkeypatch.setattr(
        module,
        "resolve_paper_root_context",
        lambda _: SimpleNamespace(
            paper_root=paper_root,
            worktree_root=paper_root.parent,
            quest_root=quest_root,
            study_id="004-public-anchor-route",
            study_root=study_root,
        ),
        raising=False,
    )
    return study_root


def _inject_public_data_surface_mentions(quest_root: Path) -> None:
    paper_root = _paper_root_from_quest(quest_root)
    review_path = paper_root / "build" / "review_manuscript.md"
    review_path.write_text(
        review_path.read_text(encoding="utf-8")
        + "\nPublic MRI and omics datasets remain appendix-grade anatomy and biology anchors.\n",
        encoding="utf-8",
    )
    draft_path = paper_root / "draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8")
        + "\nPublic anatomy and biology anchors were retained for the manuscript-facing route.\n",
        encoding="utf-8",
    )
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"][0]["title"] = "Public anatomy and biology anchors remain appendix-grade contextual support"
    dump_json(figure_catalog_path, figure_catalog)


def _write_public_evidence_decisions(quest_root: Path, decisions: list[dict[str, Any]]) -> None:
    derived_manifest_path = _paper_root_from_quest(quest_root) / "derived_analysis_manifest.json"
    payload = json.loads(derived_manifest_path.read_text(encoding="utf-8"))
    payload["public_evidence_decisions"] = decisions
    dump_json(derived_manifest_path, payload)


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
            "export_paths": ["paper/figures/F1_cohort_flow.png", "paper/figures/F1_cohort_flow.svg"],
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
                "required_exports": ["png", "svg"],
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
            "clinical_meaning": "Defines the clinical denominator for the manuscript-facing analyses.",
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
    assert "introduction_structure_missing_or_incomplete" in report["blockers"]
    assert "methods_section_structure_missing_or_incomplete" in report["blockers"]
    assert "results_section_structure_missing_or_incomplete" in report["blockers"]
    assert "figure_semantics_manifest_missing_or_incomplete" in report["blockers"]
    assert "evidence_ledger_missing_or_incomplete" in report["blockers"]
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
    assert report["evidence_ledger_present"] is True
    assert report["evidence_ledger_valid"] is True


def test_build_report_projects_study_charter_linkage_for_ledgers(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    study_root = _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root)

    report = module.build_surface_report(module.build_surface_state(quest_root))
    linkage = report["charter_contract_linkage"]

    assert linkage["status"] == "linked"
    assert linkage["study_charter_ref"] == {
        "charter_id": "charter::002-early-residual-risk::v1",
        "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
    }
    assert linkage["paper_quality_contract"]["present"] is True
    assert linkage["ledger_linkages"]["evidence_ledger"]["status"] == "linked"
    assert linkage["ledger_linkages"]["review_ledger"]["status"] == "linked"

    markdown = module.render_surface_markdown(report)
    assert "## Charter Contract Linkage" in markdown
    assert "charter::002-early-residual-risk::v1" in markdown
    assert "- evidence_ledger_linkage_status: `linked`" in markdown
    assert "- review_ledger_linkage_status: `linked`" in markdown


def test_build_report_blocks_when_study_charter_is_missing(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    study_root = _attach_study_charter_context(monkeypatch, module, tmp_path, quest_root)
    (study_root / "artifacts" / "controller" / "study_charter.json").unlink()

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "study_charter_missing" in report["blockers"]
    assert report["charter_contract_linkage"]["status"] == "study_charter_missing"


def test_build_report_blocks_when_evidence_ledger_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_evidence_ledger=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "evidence_ledger_missing_or_incomplete" in report["blockers"]
    assert report["evidence_ledger_present"] is False
    assert report["evidence_ledger_valid"] is False


def test_build_report_blocks_when_evidence_ledger_shape_is_invalid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    evidence_ledger_path = _paper_root_from_quest(quest_root) / "evidence_ledger.json"
    dump_json(
        evidence_ledger_path,
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Incomplete shape for blocker coverage.",
                }
            ],
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "evidence_ledger_missing_or_incomplete" in report["blockers"]
    assert report["evidence_ledger_present"] is True
    assert report["evidence_ledger_valid"] is False
    assert any(hit["pattern_id"] == "evidence_ledger" for hit in report["top_hits"])
    assert report["ama_csl_present"] is True
    assert report["ama_pdf_defaults_present"] is True


def test_build_report_ignores_unreferenced_generated_readme(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    readme_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "figures" / "generated" / "README.md"
    readme_path.write_text(
        "# Generated Figure Outputs\n\n"
        "Any unreferenced stale generated files are pruned during `materialize-display-surface`.\n",
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert all(not hit["path"].endswith("paper/figures/generated/README.md") for hit in report["top_hits"])


def test_build_report_allows_generic_clinical_surface_language(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    draft_path = paper_root / "draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").replace(
            "### Added-value assessment of model complexity",
            "### Monotonic score surface\n\n"
            "The core logistic model remained recoverable on a conventional regression surface.\n\n"
            "### Added-value assessment of model complexity",
        ),
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert all(hit["pattern_id"] != "surface" for hit in report["top_hits"])


def test_build_report_blocks_when_introduction_does_not_follow_three_move_structure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_introduction=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "introduction_structure_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "introduction_structure" for hit in report["top_hits"])


def test_build_report_blocks_when_methods_subsections_are_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_methods=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "methods_section_structure_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "methods_section_structure" for hit in report["top_hits"])


def test_build_report_blocks_when_results_section_lacks_subsection_structure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_structured_results=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "results_section_structure_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "results_section_structure" for hit in report["top_hits"])


def test_build_report_accepts_quick_review_with_top_level_main_sections(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    review_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "build"
        / "review_manuscript.md"
    )
    review_text = review_path.read_text(encoding="utf-8")
    review_text = review_text.replace("\n## Introduction\n", "\n# Introduction\n")
    review_text = review_text.replace("\n## Materials and Methods\n", "\n# Materials and Methods\n")
    review_text = review_text.replace("\n## Results\n", "\n# Results\n")
    review_path.write_text(review_text, encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "introduction_structure_missing_or_incomplete" not in report["blockers"]
    assert "methods_section_structure_missing_or_incomplete" not in report["blockers"]
    assert "results_section_structure_missing_or_incomplete" not in report["blockers"]


def test_build_report_accepts_review_with_relative_subsection_levels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    review_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "build"
        / "review_manuscript.md"
    )
    review_text = review_path.read_text(encoding="utf-8")
    review_text = review_text.replace("\n## Introduction\n", "\n# Introduction\n")
    review_text = review_text.replace("\n## Materials and Methods\n", "\n# Materials and Methods\n")
    review_text = review_text.replace("\n### Study design and cohort\n", "\n## Study design and cohort\n")
    review_text = review_text.replace(
        "\n### Variable definition and measurement\n",
        "\n## Variable definition and measurement\n",
    )
    review_text = review_text.replace("\n### Model building\n", "\n## Model building\n")
    review_text = review_text.replace("\n### Validation framework\n", "\n## Validation framework\n")
    review_text = review_text.replace("\n## Results\n", "\n# Results\n")
    review_text = review_text.replace("\n### Cohort characteristics\n", "\n## Cohort characteristics\n")
    review_text = review_text.replace(
        "\n### Unified validation and clinical utility\n",
        "\n## Unified validation and clinical utility\n",
    )
    review_text = review_text.replace(
        "\n### Added-value assessment of model complexity\n",
        "\n## Added-value assessment of model complexity\n",
    )
    review_text = review_text.replace("\n## Discussion\n", "\n# Discussion\n")
    review_path.write_text(review_text, encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "introduction_structure_missing_or_incomplete" not in report["blockers"]
    assert "methods_section_structure_missing_or_incomplete" not in report["blockers"]
    assert "results_section_structure_missing_or_incomplete" not in report["blockers"]


def test_build_report_blocks_when_non_formal_question_sentence_appears(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_question_mark_prose=True,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "non_formal_question_sentence_present" in report["blockers"]
    assert any(hit["pattern_id"] == "non_formal_question_sentence" for hit in report["top_hits"])


def test_scan_non_formal_question_sentences_does_not_use_backtracking_question_regex(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    manuscript_path = tmp_path / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True)
    manuscript_path.write_text(
        "## Discussion\n"
        + ("This clause keeps extending the same manuscript sentence " * 200)
        + "does the supervisor tick remain bounded?\n",
        encoding="utf-8",
    )

    class ExplodingQuestionRegex:
        def finditer(self, text: str):
            raise AssertionError("question sentence scanning must not depend on the backtracking regex")

    monkeypatch.setattr(module, "QUESTION_SENTENCE_RE", ExplodingQuestionRegex(), raising=False)

    hits = module.scan_non_formal_question_sentences(manuscript_path)

    assert len(hits) == 1
    assert hits[0]["pattern_id"] == "non_formal_question_sentence"
    assert hits[0]["location"] == "line 2"
    assert hits[0]["phrase"].endswith("does the supervisor tick remain bounded?")


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


def test_build_report_blocks_when_review_ledger_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_review_ledger=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "review_ledger_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "review_ledger" for hit in report["top_hits"])


def test_build_report_blocks_when_review_ledger_shape_is_invalid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    review_ledger_path = _paper_root_from_quest(quest_root) / "review" / "review_ledger.json"
    dump_json(
        review_ledger_path,
        {
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer_1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "open",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [],
                }
            ],
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "review_ledger_missing_or_incomplete" in report["blockers"]
    assert any(
        hit["pattern_id"] == "review_ledger" and "revision_links" in hit["excerpt"]
        for hit in report["top_hits"]
    )


def test_build_report_accepts_valid_review_ledger(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "review_ledger_missing_or_incomplete" not in report["blockers"]
    assert report["review_ledger_present"] is True
    assert report["review_ledger_valid"] is True


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


def test_build_report_allows_supplementary_cohort_flow_without_results_narrative_reference(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    narrative_path = paper_root / "results_narrative_map.json"

    figure_payload = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    for figure in figure_payload["figures"]:
        if figure.get("figure_id") == "F1":
            figure["paper_role"] = "supplementary"
            break
    dump_json(figure_catalog_path, figure_payload)

    narrative_payload = json.loads(narrative_path.read_text(encoding="utf-8"))
    for section in narrative_payload["sections"]:
        supporting_items = [
            str(item).strip()
            for item in (section.get("supporting_display_items") or [])
            if str(item).strip() != "F1"
        ]
        section["supporting_display_items"] = supporting_items or ["T1"]
    narrative_path.write_text(json.dumps(narrative_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "figure_catalog_missing_or_incomplete" not in report["blockers"]
    assert "results_narrative_map_missing_or_incomplete" not in report["blockers"]
    assert not any(
        hit["pattern_id"] in {"results_narrative_map_missing_main_figure_reference", "figure_catalog"}
        and hit["phrase"] == "F1"
        for hit in report["top_hits"]
    )


def test_build_report_blocks_when_results_sections_are_supported_only_by_setup_displays(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = _paper_root_from_quest(quest_root)
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog_payload = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    for figure in figure_catalog_payload.get("figures", []):
        figure["paper_role"] = "supplementary"
    figure_catalog_payload.setdefault("figures", []).append(
        {
            "figure_id": "F1",
            "template_id": "cohort_flow_figure",
            "renderer_family": "python",
            "input_schema_id": "cohort_flow_shell_inputs_v1",
            "qc_profile": "publication_illustration_flow",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-05T00:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_illustration_flow",
                "layout_sidecar_path": "paper/figures/generated/F1.layout.json",
                "issues": [],
            },
            "title": "Cohort flow",
            "caption": "Cohort flow for the descriptive survey route.",
            "paper_role": "main_text",
            "export_paths": ["paper/figures/F1.png", "paper/figures/F1.svg"],
        }
    )
    dump_json(figure_catalog_path, figure_catalog_payload)
    dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "status": "resolved",
            "display_shell_plan": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                },
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                },
            ],
        },
    )
    narrative_path = paper_root / "results_narrative_map.json"
    narrative_payload = json.loads(narrative_path.read_text(encoding="utf-8"))
    for section in narrative_payload["sections"]:
        section["supporting_display_items"] = ["F1", "T1"]
    narrative_path.write_text(json.dumps(narrative_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "results_display_surface_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "results_narrative_map_setup_only_display_support" for hit in report["top_hits"])


def test_build_report_blocks_when_required_display_catalog_item_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _write_time_to_event_direct_migration_surface(quest_root, include_f5=False)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "required_display_catalog_coverage_incomplete" in report["blockers"]
    assert any(
        hit["pattern_id"] == "required_display_catalog_item_missing" and hit["phrase"] == "F5"
        for hit in report["top_hits"]
    )


def test_build_report_blocks_when_main_text_claim_binding_is_missing_from_catalog(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    claim_map_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "claim_evidence_map.json"
    payload = json.loads(claim_map_path.read_text(encoding="utf-8"))
    payload["claims"][0]["display_bindings"] = ["F5", "T1"]
    claim_map_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "claim_evidence_map_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "claim_evidence_map_missing_display_binding" for hit in report["top_hits"])


def test_build_report_accepts_complete_required_display_catalog_coverage(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _write_time_to_event_direct_migration_surface(quest_root, include_f5=True)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "required_display_catalog_coverage_incomplete" not in report["blockers"]


def test_build_report_accepts_required_display_catalog_coverage_for_supplementary_figure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _write_time_to_event_direct_migration_surface(quest_root, include_f5=True)

    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    reporting_contract_payload = json.loads(reporting_contract_path.read_text(encoding="utf-8"))
    for item in reporting_contract_payload.get("display_shell_plan", []):
        if item.get("catalog_id") == "F5":
            item["catalog_id"] = "S1"
    reporting_contract_path.write_text(
        json.dumps(reporting_contract_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog_payload = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog_payload.setdefault("figures", []).append(
        {
            "figure_id": "S1",
            "paper_role": "supplementary",
            "manuscript_status": "locked_supplementary_evidence",
            "template_id": "cohort_flow_figure",
            "renderer_family": "python",
            "input_schema_id": "cohort_flow_shell_inputs_v1",
            "qc_profile": "publication_illustration_flow",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-05T00:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_illustration_flow",
                "layout_sidecar_path": "paper/figures/generated/S1.layout.json",
                "audit_classes": [],
                "issues": [],
                "readability_findings": [],
                "revision_note": "",
            },
            "title": "Supplementary cohort assembly overview",
            "caption": "Supplementary cohort accounting for the shared analytic population.",
            "export_paths": [
                "paper/figures/generated/S1.svg",
                "paper/figures/generated/S1.png",
            ],
            "source_paths": [
                "paper/figures/generated/S1.layout.json",
            ],
            "claim_ids": [],
        }
    )
    figure_catalog_path.write_text(
        json.dumps(figure_catalog_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "required_display_catalog_coverage_incomplete" not in report["blockers"]


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


def test_build_report_blocks_analysis_plane_jargon_on_manuscript_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    draft_path = paper_root / "draft.md"
    draft_text = draft_path.read_text(encoding="utf-8")
    draft_path.write_text(
        draft_text.replace(
            "We assessed whether an extended preoperative model could improve residual-risk estimation.",
            (
                "We assessed whether support mismatch and risk compression explained the transported score, "
                "with self-quantile summaries retained as the main manuscript route."
            ),
        ),
        encoding="utf-8",
    )
    narrative_path = paper_root / "results_narrative_map.json"
    narrative_payload = json.loads(narrative_path.read_text(encoding="utf-8"))
    narrative_payload["sections"][0]["direct_answer"] = (
        "Residual ordering signal persisted after support mismatch and risk compression were observed."
    )
    narrative_path.write_text(json.dumps(narrative_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "analysis_plane_jargon_present_on_manuscript_surface" in report["blockers"]
    assert any(hit["pattern_id"] == "support_mismatch" for hit in report["top_hits"])
    assert any(hit["pattern_id"] == "risk_compression" for hit in report["top_hits"])


def test_build_report_accepts_medical_publication_native_terms_on_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    draft_path = paper_root / "draft.md"
    draft_text = draft_path.read_text(encoding="utf-8")
    draft_path.write_text(
        draft_text.replace(
            "We assessed whether an extended preoperative model could improve residual-risk estimation.",
            (
                "We assessed external validation performance by focusing on discrimination, calibration, "
                "clinical utility, and transportability."
            ),
        ),
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "analysis_plane_jargon_present_on_manuscript_surface" not in report["blockers"]


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
            "renderer_family": "r_ggplot2",
            "selection_rationale": "The evidence plot should stay on the audited R stack.",
            "fallback_on_failure": True,
            "failure_action": "block_and_fix_environment",
        },
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "figure_semantics_manifest_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"] if hit["pattern_id"] == "figure_semantics_manifest")
    assert "fallback_on_failure" in excerpts


def test_build_report_blocks_when_figure_catalog_breaks_renderer_contract_alignment(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"][0]["template_id"] = "pr_curve_binary"
    figure_catalog_path.write_text(json.dumps(figure_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "figure_semantics_manifest_missing_or_incomplete" in report["blockers"]
    assert any(hit["pattern_id"] == "figure_semantics_renderer_contract_mismatch" for hit in report["top_hits"])


def test_build_report_allows_submission_companion_renderer_contract_in_figure_semantics_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )

    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"].append(
        {
            "figure_id": "GA1",
            "template_id": "submission_graphical_abstract",
            "renderer_family": "python",
            "paper_role": "submission_companion",
            "input_schema_id": "submission_graphical_abstract_inputs_v1",
            "qc_profile": "submission_graphical_abstract",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-05T00:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "submission_graphical_abstract",
                "layout_sidecar_path": "paper/figures/generated/GA1.layout.json",
                "audit_classes": [],
                "issues": [],
                "failure_reason": "",
                "readability_findings": [],
                "revision_note": "",
            },
            "title": "Submission graphical abstract",
            "caption": "Graphical abstract summarizes the cohort, primary result, and applicability boundary.",
            "export_paths": ["paper/figures/generated/GA1.svg", "paper/figures/generated/GA1.png"],
        }
    )
    figure_catalog_path.write_text(json.dumps(figure_catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    figure_semantics_path = paper_root / "figure_semantics_manifest.json"
    figure_semantics = json.loads(figure_semantics_path.read_text(encoding="utf-8"))
    figure_semantics["figures"].append(
        {
            "figure_id": "GA1",
            "story_role": "submission-facing study synopsis",
            "research_question": "How should the submission companion summarize the audited study surface without adding new evidence?",
            "direct_message": "The graphical abstract compresses audited cohort, endpoint, and boundary information into a submission-facing synopsis.",
            "clinical_implication": "Editors and reviewers can see the main audited boundary conditions before reading the full text.",
            "interpretation_boundary": "The graphical abstract is a submission companion and does not add new evidence beyond the audited manuscript surface.",
            "panel_messages": [
                {"panel_id": "A", "message": "Panel A summarizes the cohort and split."},
                {"panel_id": "B", "message": "Panel B summarizes the primary 5-year endpoint."},
            ],
            "legend_glossary": [
                {"term": "submission companion", "explanation": "A manuscript-adjacent summary artifact for editorial review."},
            ],
            "threshold_semantics": "Any displayed thresholds summarize audited evidence and do not introduce new decision cut-offs.",
            "stratification_basis": "The companion mirrors the audited paper-owned displays and tables.",
            "recommendation_boundary": "No new recommendation claim is introduced by the submission companion.",
            "renderer_contract": {
                "figure_semantics": "submission_companion",
                "renderer_family": "python",
                "template_id": "submission_graphical_abstract",
                "selection_rationale": "The submission graphical abstract must stay on the audited illustration shell so the manuscript-facing summary remains deterministic.",
                "layout_qc_profile": "submission_graphical_abstract",
                "required_exports": ["png", "svg"],
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        }
    )
    figure_semantics_path.write_text(json.dumps(figure_semantics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "figure_semantics_manifest_missing_or_incomplete" not in report["blockers"]


def test_build_report_blocks_when_catalog_entry_missing_template_metadata(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    figure_catalog_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "figures" / "figure_catalog.json"
    )
    payload = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    payload["figures"][0].pop("template_id", None)
    figure_catalog_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "figure_catalog_missing_or_incomplete" in report["blockers"]
    excerpts = " ".join(hit["excerpt"] for hit in report["top_hits"] if hit["pattern_id"] == "figure_catalog")
    assert "template_id" in excerpts

def test_build_report_blocks_when_table3_markdown_contains_forbidden_term(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table3_path = paper_root / "tables" / "T3_interpretation.md"
    table3_path.parent.mkdir(parents=True, exist_ok=True)
    table3_path.write_text(
        "| Clinical Item | Interpretation |\n| --- | --- |\n| High risk | deployment-facing follow-up recommendation |\n",
        encoding="utf-8",
    )
    payload = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    payload["tables"].append(
        {
            "table_id": "T3",
            "table_shell_id": full_id("table3_clinical_interpretation_summary"),
            "input_schema_id": "clinical_interpretation_summary_v1",
            "qc_profile": "publication_table_interpretation",
            "qc_result": {"status": "pass", "issues": []},
            "title": "Clinical interpretation summary",
            "caption": "Clinical interpretation anchors.",
            "paper_role": "supplementary",
            "asset_paths": ["paper/tables/T3_interpretation.md"],
        }
    )
    dump_json(table_catalog_path, payload)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terms_present" in report["blockers"]
    assert any(hit["path"].endswith("T3_interpretation.md") for hit in report["top_hits"])
    assert any(hit["phrase"] == "deployment-facing" for hit in report["top_hits"])


def test_build_report_does_not_scan_non_table3_markdown_body(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table1_path = paper_root / "tables" / "T1.md"
    table1_path.parent.mkdir(parents=True, exist_ok=True)
    table1_path.write_text(
        "| Characteristic | Value |\n| --- | --- |\n| Follow-up | deployment-facing summary |\n",
        encoding="utf-8",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["top_hits"] == []


def test_build_report_does_not_scan_non_markdown_table3_assets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table3_path = paper_root / "tables" / "T3_interpretation.md"
    table3_json_path = paper_root / "tables" / "T3_sidecar.json"
    table3_path.parent.mkdir(parents=True, exist_ok=True)
    table3_path.write_text(
        "| Clinical Item | Interpretation |\n| --- | --- |\n| High risk | Close endocrine follow-up |\n",
        encoding="utf-8",
    )
    table3_json_path.write_text(
        json.dumps({"note": "deployment-facing debug artifact"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    payload = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    payload["tables"].append(
        {
            "table_id": "T3",
            "table_shell_id": "table3_clinical_interpretation_summary",
            "input_schema_id": "clinical_interpretation_summary_v1",
            "qc_profile": "publication_table_interpretation",
            "qc_result": {"status": "pass", "issues": []},
            "title": "Clinical interpretation summary",
            "caption": "Clinical interpretation anchors.",
            "paper_role": "supplementary",
            "asset_paths": ["paper/tables/T3_interpretation.md", "paper/tables/T3_sidecar.json"],
        }
    )
    table_catalog_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["top_hits"] == []


def test_build_report_scans_only_table3_markdown_table_body(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table3_path = paper_root / "tables" / "T3_interpretation.md"
    table3_path.parent.mkdir(parents=True, exist_ok=True)
    table3_path.write_text(
        "# deployment-facing title\n\n| Clinical Item | Interpretation |\n| --- | --- |\n| High risk | Close endocrine follow-up |\n",
        encoding="utf-8",
    )
    payload = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    payload["tables"].append(
        {
            "table_id": "T3",
            "table_shell_id": "table3_clinical_interpretation_summary",
            "input_schema_id": "clinical_interpretation_summary_v1",
            "qc_profile": "publication_table_interpretation",
            "qc_result": {"status": "pass", "issues": []},
            "title": "Clinical interpretation summary",
            "caption": "Clinical interpretation anchors.",
            "paper_role": "supplementary",
            "asset_paths": ["paper/tables/T3_interpretation.md"],
        }
    )
    table_catalog_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["top_hits"] == []


def test_build_report_blocks_public_data_without_surface_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _attach_public_anchor_study_context(monkeypatch, module, tmp_path, quest_root)
    _inject_public_data_surface_mentions(quest_root)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "public_evidence_decisions_missing_or_incomplete" in report["blockers"]
    assert report["public_data_anchor_count"] == 2
    assert report["public_data_surface_reference_count"] >= 1
    assert any(hit["pattern_id"] == "paper_facing_public_data_reference" for hit in report["top_hits"])


def test_build_report_blocks_public_data_when_decisions_drop_from_manuscript(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _attach_public_anchor_study_context(monkeypatch, module, tmp_path, quest_root)
    _inject_public_data_surface_mentions(quest_root)
    _write_public_evidence_decisions(
        quest_root,
        [
            {
                "entry_id": "PE1",
                "dataset_ids": ["mapping-pituitary", "geo-gse169498"],
                "analysis_ids": ["A1"],
                "paper_surface_decision": "drop_from_manuscript",
                "decision_rationale": "Public datasets were retained for audit only and did not earn a manuscript-facing result.",
            }
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "paper_facing_public_data_without_earned_evidence" in report["blockers"]
    assert report["public_evidence_decision_count"] == 1
    assert report["public_evidence_earned_count"] == 0


def test_build_report_allows_public_data_after_appendix_earned_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
    )
    _attach_public_anchor_study_context(monkeypatch, module, tmp_path, quest_root)
    _inject_public_data_surface_mentions(quest_root)
    _write_public_evidence_decisions(
        quest_root,
        [
            {
                "entry_id": "PE1",
                "dataset_ids": ["mapping-pituitary", "geo-gse169498"],
                "analysis_ids": ["A1"],
                "paper_surface_decision": "appendix_earned",
                "decision_rationale": "The public datasets earned a constrained appendix role after a separate route-specific audit.",
                "result_statement": "Public MRI and omics anchors provide bounded appendix-only anatomy and biology context.",
                "linked_display_items": ["F4"],
                "linked_sections": ["discussion", "appendix"],
                "interpretation_boundary": "Appendix context only; no external validation or mechanistic claim.",
            }
        ],
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert report["public_evidence_decision_count"] == 1
    assert report["public_evidence_earned_count"] == 1
    assert "public_evidence_decisions_missing_or_incomplete" not in report["blockers"]
    assert "paper_facing_public_data_without_earned_evidence" not in report["blockers"]


def test_validate_figure_catalog_requires_real_qc_result_fields() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_figure_catalog(
        {
            "figures": [
                {
                    "figure_id": "F8",
                    "template_id": "umap_scatter_grouped",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "embedding_grouped_inputs_v1",
                    "qc_profile": "publication_embedding_scatter",
                    "qc_result": {"status": "pass"},
                    "export_paths": ["paper/figures/F8.png", "paper/figures/F8.pdf"],
                }
            ]
        }
    )

    assert "engine_id" in errors[0]


def test_validate_figure_catalog_blocks_readability_failures() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_figure_catalog(
        {
            "figures": [
                {
                    "figure_id": "F3",
                    "template_id": "time_to_event_risk_group_summary",
                    "renderer_family": "python",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_grouped_inputs_v1",
                    "qc_profile": "publication_survival_curve",
                    "qc_result": {
                        "status": "fail",
                        "checked_at": "2026-04-04T00:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_survival_curve",
                        "layout_sidecar_path": "paper/figures/generated/F3.layout.json",
                        "audit_classes": ["readability"],
                        "issues": [
                            {
                                "audit_class": "readability",
                                "rule_id": "risk_separation_not_readable",
                                "message": "survival groups are too compressed to convey the intended separation",
                            }
                        ],
                        "failure_reason": "risk_separation_not_readable",
                        "readability_findings": [
                            {
                                "audit_class": "readability",
                                "rule_id": "risk_separation_not_readable",
                                "message": "survival groups are too compressed to convey the intended separation",
                            }
                        ],
                        "revision_note": "",
                    },
                    "export_paths": ["paper/figures/F3.png", "paper/figures/F3.pdf"],
                }
            ]
        }
    )

    assert any("readability" in error for error in errors)


def test_validate_figure_catalog_blocks_failed_illustration_shell_qc() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_figure_catalog(
        {
            "figures": [
                {
                    "figure_id": "GA1",
                    "template_id": "submission_graphical_abstract",
                    "renderer_family": "python",
                    "paper_role": "submission_companion",
                    "input_schema_id": "submission_graphical_abstract_inputs_v1",
                    "qc_profile": "submission_graphical_abstract",
                    "qc_result": {
                        "status": "fail",
                        "checked_at": "2026-04-05T00:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "submission_graphical_abstract",
                        "layout_sidecar_path": "paper/figures/generated/GA1.layout.json",
                        "audit_classes": ["layout"],
                        "issues": [
                            {
                                "audit_class": "layout",
                                "rule_id": "panel_text_out_of_panel",
                                "message": "graphical-abstract panel text must stay within a panel",
                            }
                        ],
                        "failure_reason": "panel_text_out_of_panel",
                        "readability_findings": [],
                        "revision_note": "",
                    },
                    "export_paths": ["paper/figures/generated/GA1.svg", "paper/figures/generated/GA1.png"],
                }
            ]
        }
    )

    assert any("blocks publication" in error for error in errors)


def test_validate_figure_semantics_manifest_blocks_story_role_drift_for_setup_shell() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    base_payload = {
        "figure_id": "S1",
        "research_question": "How was the formal analysis cohort assembled before model fitting?",
        "direct_message": "The cohort-flow shell documents study assembly and exclusion logic for the audited analysis cohort.",
        "clinical_implication": "Supports transparent setup reporting before the manuscript turns to result evidence.",
        "interpretation_boundary": "Study setup only; it is not itself a result claim.",
        "panel_messages": [
            {
                "panel_id": "A",
                "message": "The figure traces screened, excluded, and analyzed patients.",
            }
        ],
        "legend_glossary": [
            {
                "term": "analysis cohort",
                "explanation": "Patients retained for the prespecified audited model analysis.",
            }
        ],
        "threshold_semantics": "Not applicable to the cohort-flow shell.",
        "stratification_basis": "Not applicable to the cohort-flow shell.",
        "recommendation_boundary": "No treatment recommendation is made from this setup figure.",
        "renderer_contract": {
            "figure_semantics": "illustration",
            "renderer_family": "python",
            "template_id": full_id("cohort_flow_figure"),
            "selection_rationale": "The registered cohort-flow shell preserves the audited study-setup surface.",
            "layout_qc_profile": "publication_illustration_flow",
            "required_exports": ["png", "svg"],
            "fallback_on_failure": False,
            "failure_action": "block_and_fix_environment",
        },
    }

    assert module.validate_figure_semantics_manifest(
        {"figures": [dict(base_payload, story_role="study_setup")]}
    ) == []

    errors = module.validate_figure_semantics_manifest(
        {"figures": [dict(base_payload, story_role="study_assembly_support")]}
    )

    assert any("canonical story role" in error for error in errors)
    assert any("study_setup" in error for error in errors)


def test_validate_figure_catalog_allows_supplementary_cohort_flow_shell() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    base_payload = {
        "figure_id": "S1",
        "template_id": "cohort_flow_figure",
        "renderer_family": "python",
        "input_schema_id": "cohort_flow_shell_inputs_v1",
        "qc_profile": "publication_illustration_flow",
        "qc_result": {
            "status": "pass",
            "checked_at": "2026-04-05T00:00:00+00:00",
            "engine_id": "display_layout_qc_v1",
            "qc_profile": "publication_illustration_flow",
            "layout_sidecar_path": "paper/figures/generated/S1.layout.json",
            "audit_classes": [],
            "issues": [],
            "readability_findings": [],
            "revision_note": "",
        },
        "export_paths": ["paper/figures/generated/S1.svg", "paper/figures/generated/S1.png"],
    }

    supplementary_errors = module.validate_figure_catalog(
        {"figures": [dict(base_payload, paper_role="supplementary")]}
    )
    main_text_errors = module.validate_figure_catalog(
        {"figures": [dict(base_payload, paper_role="main_text")]}
    )
    appendix_errors = module.validate_figure_catalog(
        {"figures": [dict(base_payload, paper_role="appendix")]}
    )

    assert supplementary_errors == []
    assert main_text_errors == []
    assert any("paper_role `appendix`" in error for error in appendix_errors)


def test_validate_table_catalog_accepts_md_only_second_stage_tables() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T2_summary.md"],
                },
                {
                    "table_id": "T3",
                    "table_shell_id": "table3_clinical_interpretation_summary",
                    "paper_role": "supplementary",
                    "input_schema_id": "clinical_interpretation_summary_v1",
                    "qc_profile": "publication_table_interpretation",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T3_summary.md"],
                },
            ]
        }
    )

    assert errors == []


def test_build_report_blocks_single_panel_label_without_layout_evidence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        generated_figure_text_override=(
            "<svg>"
            "<text x='24' y='32'>A</text>"
            "<text x='64' y='32'>Threshold-specific operating characteristics for the extended preoperative model</text>"
            "</svg>\n"
        ),
    )
    layout_sidecar_path = (
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "figures" / "generated" / "F4.layout.json"
    )
    dump_json(
        layout_sidecar_path,
        {
            "figure_id": "F4",
            "template_id": "roc_curve_binary",
            "renderer_family": "r_ggplot2",
            "qc_profile": "publication_evidence_curve",
            "status": "pass",
            "updated_at": "2026-04-18T14:00:00+00:00",
        },
    )

    state = module.build_surface_state(quest_root)
    report = module.build_surface_report(state)

    assert report["status"] == "blocked"
    assert "figure_layout_sidecar_missing_or_incomplete" in report["blockers"]
    pattern_ids = {hit["pattern_id"] for hit in report["top_hits"]}
    assert "figure_layout_sidecar_missing_publication_metrics" in pattern_ids
    assert "single_panel_figure_contains_panel_label" in pattern_ids


def test_validate_table_catalog_rejects_missing_md_export_for_second_stage_table() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T2_summary.csv"],
                }
            ]
        }
    )

    assert "missing required export formats" in errors[0]
    assert "md" in errors[0]


def test_validate_table_catalog_accepts_csv_and_md_anchor_generic_tables() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "performance_summary_table_generic",
                    "paper_role": "main_text",
                    "input_schema_id": "performance_summary_table_generic_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": [
                        "paper/tables/T2_performance_summary.csv",
                        "paper/tables/T2_performance_summary.md",
                    ],
                },
                {
                    "table_id": "T3",
                    "table_shell_id": "grouped_risk_event_summary_table",
                    "paper_role": "main_text",
                    "input_schema_id": "grouped_risk_event_summary_table_v1",
                    "qc_profile": "publication_table_interpretation",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": [
                        "paper/tables/T3_grouped_risk_summary.csv",
                        "paper/tables/T3_grouped_risk_summary.md",
                    ],
                },
            ]
        }
    )

    assert errors == []


def test_validate_table_catalog_rejects_missing_csv_for_anchor_generic_tables() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    errors = module.validate_table_catalog(
        {
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "performance_summary_table_generic",
                    "paper_role": "main_text",
                    "input_schema_id": "performance_summary_table_generic_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "asset_paths": ["paper/tables/T2_performance_summary.md"],
                }
            ]
        }
    )

    assert "missing required export formats" in errors[0]
    assert "csv" in errors[0]


def test_run_controller_stops_then_enqueues_medical_surface_message(tmp_path: Path, monkeypatch) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, medicalized=False, ama_defaults=False)
    stopped: list[tuple[str | None, str | None, str, str]] = []

    def fake_stop_quest(
        *,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        quest_id: str,
        source: str,
    ) -> dict:
        stopped.append((daemon_url, str(runtime_root) if runtime_root is not None else None, quest_id, source))
        return {"ok": True, "status": "stopped", "source": source}

    monkeypatch.setattr(module.managed_runtime_transport, "stop_quest", fake_stop_quest)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        daemon_url="http://127.0.0.1:20999",
    )

    assert module.managed_runtime_transport is module.med_deepscientist_transport
    assert stopped == [
        (
            "http://127.0.0.1:20999",
            str((quest_root.parent.parent).resolve()),
            "002-early-residual-risk",
            "codex-medical-publication-surface",
        )
    ]
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
    assert "evidence_ledger.json" in content
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
    stopped: list[tuple[str | None, str | None, str, str]] = []

    def fake_stop_quest(
        *,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        quest_id: str,
        source: str,
    ) -> dict:
        stopped.append((daemon_url, str(runtime_root) if runtime_root is not None else None, quest_id, source))
        return {"ok": True, "status": "stopped", "source": source}

    monkeypatch.setattr(module.managed_runtime_transport, "stop_quest", fake_stop_quest)

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


def test_build_surface_state_resolves_study_root_from_live_quest_paper(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "004-live-quest"
    paper_root = quest_root / "paper"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "004-live-quest",
            "status": "running",
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    study_root = workspace_root / "studies" / "004-study"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 004-study\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text(
        "schema_version: 1\n"
        "study_id: 004-study\n"
        "quest_id: 004-live-quest\n",
        encoding="utf-8",
    )

    state = module.build_surface_state(quest_root)

    assert state.study_root == study_root.resolve()


def test_build_surface_state_prefers_bundle_branch_over_drifted_projected_paper_line_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    drifted_paper_root = _paper_root_from_quest(quest_root)
    projected_paper_root = quest_root / "paper"
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    authoritative_paper_root.mkdir(parents=True, exist_ok=True)
    dump_json(
        authoritative_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    dump_json(
        projected_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "analysis/paper-drifted",
            "paper_root": str(drifted_paper_root.resolve()),
        },
    )

    state = module.build_surface_state(quest_root)

    assert state.paper_root == authoritative_paper_root.resolve()


def test_write_surface_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-04-03T04:20:00+00:00",
        "quest_id": quest_root.name,
        "run_id": "run-1",
        "status": "blocked",
        "recommended_action": "stop",
        "blockers": ["forbidden_tool_disclosure_in_caption"],
        "top_hits": [],
        "ama_defaults_present": True,
        "ama_csl_present": True,
        "ama_pdf_defaults_present": True,
        "paper_pdf_present": True,
        "draft_present": True,
        "review_manuscript_present": True,
        "figure_catalog_present": True,
        "figure_catalog_valid": True,
        "table_catalog_present": True,
        "table_catalog_valid": True,
        "methods_implementation_manifest_present": True,
        "methods_implementation_manifest_valid": True,
        "review_ledger_present": True,
        "review_ledger_valid": True,
        "results_narrative_map_present": True,
        "results_narrative_map_valid": True,
        "figure_semantics_manifest_present": True,
        "figure_semantics_manifest_valid": True,
        "evidence_ledger_present": True,
        "evidence_ledger_valid": True,
        "derived_analysis_manifest_present": True,
        "derived_analysis_manifest_valid": True,
        "reproducibility_supplement_present": True,
        "reproducibility_supplement_valid": True,
        "missing_data_policy_consistent": True,
        "endpoint_provenance_note_present": True,
        "endpoint_provenance_note_valid": True,
        "endpoint_provenance_note_applied": True,
        "forbidden_hit_count": 1,
        "undefined_methodology_label_hit_count": 0,
        "results_narration_hit_count": 0,
    }

    json_path, md_path = module.write_surface_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "medical_publication_surface"
    assert seen["timestamp"] == "2026-04-03T04:20:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
