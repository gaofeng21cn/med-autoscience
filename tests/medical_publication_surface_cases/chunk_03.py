from .shared import *

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


def test_build_report_allows_leading_setup_section_when_later_sections_use_result_figures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    paper_root = tmp_path / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    dump_json(
        reporting_contract_path,
        {
            "status": "resolved",
            "display_shell_plan": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                    "story_role": "study_setup",
                },
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                    "story_role": "study_setup",
                },
            ],
            "recommended_main_text_figures": [
                {
                    "catalog_id": "F2",
                    "display_kind": "figure",
                    "story_role": "result_primary",
                    "narrative_purpose": "primary_result_surface",
                    "tier": "core",
                },
                {
                    "catalog_id": "F3",
                    "display_kind": "figure",
                    "story_role": "result_validation",
                    "narrative_purpose": "validation_surface",
                    "tier": "core",
                },
                {
                    "catalog_id": "F4",
                    "display_kind": "figure",
                    "story_role": "result_treatment",
                    "narrative_purpose": "treatment_surface",
                    "tier": "core",
                }
            ],
        },
    )
    narrative_path = paper_root / "results_narrative_map.json"
    narrative_payload = {
        "sections": [
            {"section_id": "cohort", "supporting_display_items": ["F1", "T1"]},
            {"section_id": "primary", "supporting_display_items": ["F2"]},
            {"section_id": "validation", "supporting_display_items": ["F3"]},
            {"section_id": "treatment", "supporting_display_items": ["F4"]},
        ]
    }
    narrative_path.write_text(json.dumps(narrative_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    display_story_roles = module.load_display_catalog_story_roles(reporting_contract_path)
    hits = module.inspect_results_display_surface_coverage(
        path=narrative_path,
        payload=narrative_payload,
        display_story_roles=display_story_roles,
    )

    assert display_story_roles == {
        "F1": "study_setup",
        "T1": "study_setup",
        "F2": "result_primary",
        "F3": "result_validation",
        "F4": "result_treatment",
    }
    assert hits == []


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
