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
    include_methods_manifest: bool | None = None,
    include_results_narrative_map: bool | None = None,
    figure_led_results: bool | None = None,
    include_reproducibility_supplement: bool | None = None,
    include_endpoint_provenance_note: bool | None = None,
    include_operational_method_labels: bool | None = None,
) -> Path:
    quest_root = tmp_path / "runtime" / "quests" / "002-early-residual-risk"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    paper_root = worktree_root / "paper"
    if include_methods_manifest is None:
        include_methods_manifest = medicalized
    if include_results_narrative_map is None:
        include_results_narrative_map = medicalized
    if figure_led_results is None:
        figure_led_results = not medicalized
    if include_reproducibility_supplement is None:
        include_reproducibility_supplement = medicalized
    if include_endpoint_provenance_note is None:
        include_endpoint_provenance_note = medicalized
    if include_operational_method_labels is None:
        include_operational_method_labels = medicalized

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
            "Publication-grade figure refinement is recommended with AutoFigure-Edit and deepscientist."
        )
        table_caption = "Baseline-comparable summary on the locked cohort."
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
                },
                "model_registry": [
                    {
                        "model_id": "M1",
                        "manuscript_name": "Extended preoperative model",
                        "family": "Gradient boosting classifier",
                        "inputs": ["clinical variables", "preoperative imaging descriptors"],
                        "target": "Early residual risk",
                    }
                ],
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
        dump_json(
            paper_root / "results_narrative_map.json",
            {
                "schema_version": 1,
                "sections": [
                    {
                        "section_id": "R1",
                        "section_title": "Primary performance and clinical utility",
                        "research_question": "Does the extended preoperative model improve early residual-risk assessment?",
                        "direct_answer": "Yes. The model improved discrimination, calibration, and decision-curve utility.",
                        "supporting_display_items": ["F1", "T1"],
                        "key_quantitative_findings": [
                            "Discrimination improved over the baseline clinical model.",
                            "Clinical utility gains persisted across decision thresholds."
                        ],
                        "clinical_meaning": "The model can support preoperative risk stratification rather than merely restating descriptive differences.",
                        "boundary": "The result supports prediction and utility, not causal inference.",
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
    assert "figure_table_led_results_narration_present" in report["blockers"]
    assert "manuscript_safe_reproducibility_supplement_missing_or_incomplete" in report["blockers"]
    assert "endpoint_provenance_note_missing_or_unapplied" in report["blockers"]
    assert "undefined_methodology_labels_present" in report["blockers"]
    assert report["ama_csl_present"] is False
    assert report["ama_pdf_defaults_present"] is False
    assert any(hit["phrase"] == "deployment-facing" for hit in report["top_hits"])
    assert any(hit["phrase"] == "AutoFigure-Edit" for hit in report["top_hits"])
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

    monkeypatch.setattr(module.mailbox, "post_quest_control", fake_post_quest_control)

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
    assert "AutoFigure-Edit" in content
    assert "AMA" in content
    assert "methods_implementation_manifest.json" in content
    assert "results_narrative_map.json" in content
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

    monkeypatch.setattr(module.mailbox, "post_quest_control", fake_post_quest_control)

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
