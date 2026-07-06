import csv
import os

from .shared import *

def test_normalize_figure_catalog_id_accepts_supplementary_short_form() -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")

    assert module._normalize_figure_catalog_id("S1") == "S1"
    assert module._normalize_figure_catalog_id("FS1") == "S1"
    assert module._normalize_figure_catalog_id("SupplementaryFigureS1") == "S1"

def test_materialize_display_surface_generates_official_shell_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.pdf").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv").exists()

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert figure_catalog["figures"][0]["template_id"] == full_id("cohort_flow_figure")
    assert figure_catalog["figures"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figure_catalog["figures"][0]["renderer_family"] == "r_ggplot2"
    assert figure_catalog["figures"][0]["paper_role"] == "main_text"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert table_catalog["tables"][0]["table_id"] == "T1"
    assert table_catalog["tables"][0]["table_shell_id"] == full_id("table1_baseline_characteristics")
    assert table_catalog["tables"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert table_catalog["tables"][0]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_preserves_table_claim_bindings_from_claim_evidence_map(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    restrict_display_registry_to_display_ids(paper_root, "Table1")
    dump_json(
        paper_root / "claim_evidence_map.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "display_bindings": ["T1"],
                },
                {
                    "claim_id": "C2",
                    "display_refs": ["T1"],
                },
                {
                    "claim_id": "C3",
                    "table_bindings": ["T1"],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {entry["table_id"]: entry for entry in table_catalog["tables"]}
    assert tables_by_id["T1"]["claim_ids"] == ["C1", "C2", "C3"]

def test_materialize_display_surface_preserves_optional_table1_p_values(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    table_payload = json.loads((paper_root / "baseline_characteristics_schema.json").read_text(encoding="utf-8"))
    table_payload["variables"][0]["p_value"] = "0.009"
    table_payload["variables"][1]["p_value"] = "<0.001"
    dump_json(paper_root / "baseline_characteristics_schema.json", table_payload)

    module.materialize_display_surface(paper_root=paper_root)

    csv_rows = list(csv.reader((paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv").open()))
    markdown = (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").read_text(encoding="utf-8")

    assert csv_rows[0] == [
        "Characteristic",
        "Overall (n=128)",
        "Low risk (n=73)",
        "High risk (n=55)",
        "P value",
    ]
    assert csv_rows[1][-1] == "0.009"
    assert csv_rows[2][-1] == "<0.001"
    assert "| Characteristic | Overall (n=128) | Low risk (n=73) | High risk (n=55) | P value |" in markdown
    assert "| Age, median (IQR) | 52 (44-61) | 49 (42-56) | 58 (50-66) | 0.009 |" in markdown

def test_materialize_display_surface_generates_dpcc_compact_table_shells(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "phenotype_gap_summary",
                    "display_kind": "table",
                    "requirement_key": "table2_phenotype_gap_summary",
                    "catalog_id": "T2",
                    "shell_path": "paper/tables/phenotype_gap_summary.shell.json",
                },
                {
                    "display_id": "transition_site_support_summary",
                    "display_kind": "table",
                    "requirement_key": "table3_transition_site_support_summary",
                    "catalog_id": "T3",
                    "shell_path": "paper/tables/transition_site_support_summary.shell.json",
                },
            ],
        },
    )
    dump_json(
        paper_root / "phenotype_gap_summary_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table2_phenotype_gap_summary",
            "display_id": "phenotype_gap_summary",
            "group_columns": ["Phenotype"],
            "variables": ["Index patients", "Mean HbA1c"],
        },
    )
    dump_json(
        paper_root / "transition_site_support_summary_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table3_transition_site_support_summary",
            "display_id": "transition_site_support_summary",
            "group_columns": ["Section", "Metric"],
            "variables": ["Value"],
        },
    )
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables" / "T2_phenotype_gap_summary.csv").write_text(
        "Phenotype,Index patients,Mean HbA1c\n"
        "Glycemic-dominant diabetes,104029,8.04\n",
        encoding="utf-8",
    )
    (paper_root / "tables" / "T3_transition_site_support_summary.csv").write_text(
        "Section,Metric,Value\n"
        "Transition support,Same-phenotype stability,45.45%\n",
        encoding="utf-8",
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["tables_materialized"] == ["T2", "T3"]
    t2_csv_rows = list(csv.reader((paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.csv").open()))
    t3_csv_rows = list(
        csv.reader((paper_root / "tables" / "generated" / "T3_transition_site_support_summary.csv").open())
    )
    assert t2_csv_rows == [
        ["Phenotype", "Measure", "Value"],
        ["Glycemic-dominant diabetes", "Index patients", "104029"],
        ["Glycemic-dominant diabetes", "Mean HbA1c", "8.04"],
    ]
    assert t3_csv_rows == [
        ["Section", "Metric", "Measure", "Value"],
        ["Transition support", "Same-phenotype stability", "Value", "45.45%"],
    ]
    t2_markdown = (paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.md").read_text(encoding="utf-8")
    assert "| Phenotype | Measure | Value |" in t2_markdown
    assert "Index patients" in t2_markdown

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {entry["table_id"]: entry for entry in table_catalog["tables"]}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("table2_phenotype_gap_summary")
    assert tables_by_id["T2"]["asset_paths"] == [
        "paper/tables/generated/T2_phenotype_gap_summary.csv",
        "paper/tables/generated/T2_phenotype_gap_summary.md",
    ]
    assert tables_by_id["T2"]["render_result"]["table_layout_policy"] == (
        "long_measure_value_table_to_avoid_pdf_header_overlap"
    )
    assert tables_by_id["T3"]["table_shell_id"] == full_id("table3_transition_site_support_summary")
    assert json.loads((paper_root / "phenotype_gap_summary_schema.json").read_text(encoding="utf-8"))[
        "table_shell_id"
    ] == full_id("table2_phenotype_gap_summary")
    assert json.loads((paper_root / "transition_site_support_summary_schema.json").read_text(encoding="utf-8"))[
        "table_shell_id"
    ] == full_id("table3_transition_site_support_summary")


def test_materialize_display_surface_preserves_dpcc_current_markdown_tables_over_stale_payloads(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                    "shell_path": "paper/tables/baseline_characteristics.shell.json",
                },
                {
                    "display_id": "phenotype_gap_summary",
                    "display_kind": "table",
                    "requirement_key": "table2_phenotype_gap_summary",
                    "catalog_id": "T2",
                    "shell_path": "paper/tables/phenotype_gap_summary.shell.json",
                },
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "baseline_characteristics.shell.json",
        {
            "schema_version": 1,
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
    )
    dump_json(
        paper_root / "tables" / "phenotype_gap_summary.shell.json",
        {
            "schema_version": 1,
            "display_id": "phenotype_gap_summary",
            "display_kind": "table",
            "requirement_key": "table2_phenotype_gap_summary",
            "catalog_id": "T2",
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "groups": [{"group_id": "overall", "label": "Overall (n=692702)"}],
            "variables": [
                {
                    "variable_id": "index",
                    "label": "Index patients",
                    "values": ["692,702"],
                }
            ],
        },
    )
    dump_json(
        paper_root / "phenotype_gap_summary_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table2_phenotype_gap_summary",
            "display_id": "phenotype_gap_summary",
            "group_columns": ["Phenotype"],
            "variables": ["Index patients", "No-drug gap"],
        },
    )
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables" / "T2_phenotype_gap_summary.csv").write_text(
        "Phenotype,Index patients,No-drug gap\n"
        "Glycemic-dominant diabetes,104029,86.11%\n",
        encoding="utf-8",
    )
    (paper_root / "tables" / "T1_baseline_characteristics.md").write_text(
        "# Baseline characteristics\n\n"
        "| Characteristic | Measure | Value |\n"
        "| --- | --- | --- |\n"
        "| Cohort definition - Index patients | Index patients | 692,842 |\n",
        encoding="utf-8",
    )
    (paper_root / "tables" / "T2_phenotype_gap_summary.md").write_text(
        "# Phenotype-level clinical characteristics and treatment-gap rates\n\n"
        "| Phenotype | Measure | Value |\n"
        "| --- | --- | --- |\n"
        "| Glycemic-dominant diabetes | Index patients | 104,508 |\n"
        "| Glycemic-dominant diabetes | No-drug gap | 46.9% |\n",
        encoding="utf-8",
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    generated_t1 = (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").read_text(
        encoding="utf-8"
    )
    generated_t2 = (paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.md").read_text(encoding="utf-8")
    t1_csv_rows = list(csv.reader((paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv").open()))
    t2_csv_rows = list(csv.reader((paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.csv").open()))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {entry["table_id"]: entry for entry in table_catalog["tables"]}

    assert "692,842" in generated_t1
    assert "692,702" not in generated_t1
    assert "104,508" in generated_t2
    assert "86.11%" not in generated_t2
    assert t1_csv_rows[-1] == ["Cohort definition - Index patients", "Index patients", "692,842"]
    assert t2_csv_rows[-1] == ["Glycemic-dominant diabetes", "No-drug gap", "46.9%"]
    assert tables_by_id["T1"]["source_paths"] == ["paper/tables/T1_baseline_characteristics.md"]
    assert tables_by_id["T2"]["source_paths"] == ["paper/tables/T2_phenotype_gap_summary.md"]
    assert tables_by_id["T1"]["render_result"]["table_layout_policy"] == "pre_materialized_markdown_owner_surface"
    assert tables_by_id["T2"]["render_result"]["table_layout_policy"] == "pre_materialized_markdown_owner_surface"


def test_materialize_display_surface_preserves_dpcc_medication_capture_t3(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T3",
                    "table_shell_id": full_id("table3_transition_site_support_summary"),
                    "pack_id": "fenggaolab.org.medical-display-core",
                    "paper_role": "main_text",
                    "input_schema_id": "transition_site_support_summary_schema_v1",
                    "title": "Medication-capture sensitivity analysis of recorded mismatch signals",
                    "caption": "Overall and medication-field-present summaries for the core recorded mismatch indicators.",
                    "asset_paths": ["paper/tables/generated/T3_medication_capture_sensitivity.md"],
                    "source_paths": ["paper/tables/generated/T3_medication_capture_sensitivity.md"],
                },
                {
                    "table_id": "S6",
                    "paper_role": "supplementary",
                    "title": "Transition stability and site-level support summary",
                    "caption": "Transition stability and site-level support summaries moved to the supplementary material.",
                    "asset_paths": ["paper/tables/generated/S6_transition_site_support_summary.md"],
                    "source_paths": ["paper/tables/generated/S6_transition_site_support_summary.md"],
                },
            ],
        },
    )
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "transition_site_support_summary",
                    "display_kind": "table",
                    "requirement_key": "table3_transition_site_support_summary",
                    "catalog_id": "T3",
                    "shell_path": "paper/tables/transition_site_support_summary.shell.json",
                },
            ],
        },
    )
    dump_json(
        paper_root / "transition_site_support_summary_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table3_transition_site_support_summary",
            "display_id": "transition_site_support_summary",
            "group_columns": ["Section", "Metric"],
            "variables": ["Value"],
        },
    )
    (paper_root / "tables" / "generated").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables" / "generated" / "T3_medication_capture_sensitivity.md").write_text(
        "# Medication-capture sensitivity analysis\n\n"
        "| Indicator | Overall recorded mismatch | Medication-field-present mismatch |\n"
        "| --- | --- | --- |\n"
        "| Severe glycemia low-intensity gap | 200,306 of 342,025 (58.6%) | 156,219 of 186,347 (83.8%) |\n",
        encoding="utf-8",
    )
    (paper_root / "tables" / "generated" / "S6_transition_site_support_summary.md").write_text(
        "# Transition stability and site-level support\n\n"
        "| Section | Metric | Value |\n| --- | --- | --- |\n| Transition support | Same-phenotype stability | 45.45% |\n",
        encoding="utf-8",
    )
    (paper_root / "tables" / "T3_transition_site_support_summary.csv").write_text(
        "Section,Metric,Value\nTransition support,Same-phenotype stability,45.45%\n",
        encoding="utf-8",
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["tables_materialized"] == ["T3"]
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {entry["table_id"]: entry for entry in table_catalog["tables"]}
    assert tables_by_id["T3"]["title"] == "Medication-capture sensitivity analysis of recorded mismatch signals"
    assert tables_by_id["T3"]["asset_paths"] == ["paper/tables/generated/T3_medication_capture_sensitivity.md"]
    assert (paper_root / "tables" / "generated" / "S6_transition_site_support_summary.md").exists()

def test_materialize_display_surface_hydrates_current_body_display_sources(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    study_root = tmp_path / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    current_body_paper_root = (
        study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper"
    )
    write_default_publication_display_contracts(paper_root)
    _write_prepared_dependency_environment(paper_root)
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/cohort_flow.shell.json",
                },
                {
                    "display_id": "phenotype_gap_summary",
                    "display_kind": "table",
                    "requirement_key": "table2_phenotype_gap_summary",
                    "catalog_id": "T2",
                    "shell_path": "paper/tables/phenotype_gap_summary.shell.json",
                },
            ],
        },
    )
    dump_json(
        current_body_paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "title": "Study population and data flow",
            "steps": [
                {"step_id": "source", "label": "Source records", "n": 120, "detail": "Routine primary care"},
                {"step_id": "analysis", "label": "Analysis cohort", "n": 100, "detail": "Eligible adults"},
            ],
        },
    )
    dump_json(
        current_body_paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
    )
    dump_json(
        current_body_paper_root / "phenotype_gap_summary_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table2_phenotype_gap_summary",
            "display_id": "phenotype_gap_summary",
            "catalog_id": "T2",
            "group_columns": ["Phenotype"],
            "variables": ["Index patients", "Mean HbA1c"],
        },
    )
    dump_json(
        current_body_paper_root / "tables" / "phenotype_gap_summary.shell.json",
        {
            "schema_version": 1,
            "display_id": "phenotype_gap_summary",
            "display_kind": "table",
            "requirement_key": "table2_phenotype_gap_summary",
            "catalog_id": "T2",
        },
    )
    (current_body_paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (current_body_paper_root / "tables" / "T2_phenotype_gap_summary.csv").write_text(
        "Phenotype,Index patients,Mean HbA1c\n"
        "Glycemic-dominant diabetes,104029,8.04\n",
        encoding="utf-8",
    )
    dump_json(
        current_body_paper_root / "build" / "dependency_environment_receipt.json",
        {
            "schema_version": 1,
            "status": "prepared",
            "failure_class": "",
            "lock_ref": "paper/build/dependency_environment_lock.json",
            "run_context_ref": "paper/build/dependency_run_context.json",
        },
    )

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["source_hydration"]["status"] == "hydrated"
    assert result["source_hydration"]["missing_required_source_files"] == []
    assert "paper/cohort_flow.json" in result["source_hydration"]["hydrated_files"]
    assert "paper/build/dependency_environment_receipt.json" in result["source_hydration"]["hydrated_files"]
    assert "paper/phenotype_gap_summary_schema.json" in result["source_hydration"]["hydrated_files"]
    assert "paper/tables/T2_phenotype_gap_summary.csv" in result["source_hydration"]["hydrated_files"]
    assert (paper_root / "cohort_flow.json").exists()
    assert (paper_root / "figures" / "cohort_flow.shell.json").exists()
    assert (paper_root / "phenotype_gap_summary_schema.json").exists()
    assert (paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.csv").exists()
    assert result["figures_materialized"] == ["F1"]
    assert result["tables_materialized"] == ["T2"]

def test_materialize_display_surface_preserves_newer_target_sources_over_stale_current_body(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    study_root = tmp_path / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    current_body_paper_root = (
        study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper"
    )
    write_default_publication_display_contracts(paper_root)
    _write_prepared_dependency_environment(paper_root)
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/cohort_flow.shell.json",
                }
            ],
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "title": "Current target cohort",
            "steps": [
                {"step_id": "source", "label": "Current source", "n": 220, "detail": "Current paper source"},
                {"step_id": "analysis", "label": "Current analysis", "n": 200, "detail": "Current cohort"},
            ],
        },
    )
    dump_json(
        current_body_paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "title": "Stale current-body cohort",
            "steps": [
                {"step_id": "source", "label": "Stale source", "n": 120, "detail": "Stale paper source"},
                {"step_id": "analysis", "label": "Stale analysis", "n": 100, "detail": "Stale cohort"},
            ],
        },
    )
    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {"figure_id": "F1", "title": "Current target semantics", "renderer_contract": {}}
            ],
        },
    )
    dump_json(
        current_body_paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {"figure_id": "F1", "title": "Stale current-body semantics", "renderer_contract": {}}
            ],
        },
    )
    dump_json(
        current_body_paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
    )
    for stale_path in (
        current_body_paper_root / "cohort_flow.json",
        current_body_paper_root / "figure_semantics_manifest.json",
    ):
        os.utime(stale_path, (1000, 1000))
    for current_path in (
        paper_root / "cohort_flow.json",
        paper_root / "figure_semantics_manifest.json",
    ):
        os.utime(current_path, (2000, 2000))

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    cohort_flow = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    semantics = json.loads((paper_root / "figure_semantics_manifest.json").read_text(encoding="utf-8"))
    preserved_sources = set(result["source_hydration"]["preserved_current_sources"])
    assert cohort_flow["steps"][-1]["n"] == 200
    assert semantics["figures"][0]["title"] == "Current target semantics"
    assert "paper/cohort_flow.json" in preserved_sources
    assert "paper/figure_semantics_manifest.json" in preserved_sources
    assert "paper/cohort_flow.json" not in result["source_hydration"]["hydrated_files"]
    assert "paper/figure_semantics_manifest.json" not in result["source_hydration"]["hydrated_files"]

def test_materialize_display_surface_replaces_legacy_catalog_entries_with_matching_catalog_id(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "catalog_id": "F1",
                    "display_id": "cohort_flow",
                    "title": "Legacy cohort flow entry",
                    "png_path": "paper/figures/F1_cohort_flow.png",
                    "json_path": "paper/cohort_flow.json",
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
                    "catalog_id": "T1",
                    "display_id": "baseline_characteristics",
                    "title": "Legacy baseline table entry",
                    "markdown_path": "paper/tables/T1_baseline_characteristics.md",
                    "json_path": "paper/baseline_characteristics_schema.json",
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert len(figure_catalog["figures"]) == 1
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert all("figure_id" in item for item in figure_catalog["figures"])
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert len(table_catalog["tables"]) == 1
    assert table_catalog["tables"][0]["table_id"] == "T1"
    assert all("table_id" in item for item in table_catalog["tables"])

def test_materialize_display_surface_materializes_catalog_only_cohort_flow_figure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    display_registry_payload = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))
    display_registry_payload["displays"] = [
        item
        for item in display_registry_payload["displays"]
        if item.get("display_id") != "Figure1" and item.get("requirement_key") != "cohort_flow_figure"
    ]
    dump_json(paper_root / "display_registry.json", display_registry_payload)

    cohort_flow_payload = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    cohort_flow_payload["display_id"] = "cohort_flow"
    dump_json(paper_root / "cohort_flow.json", cohort_flow_payload)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "S1",
                    "display_id": "cohort_flow",
                    "template_id": full_id("cohort_flow_figure"),
                    "renderer_family": "python",
                    "input_schema_id": "cohort_flow_shell_inputs_v1",
                    "title": "Legacy cohort flow entry",
                    "export_paths": [
                        "paper/figures/generated/F1_cohort_flow.svg",
                        "paper/figures/generated/F1_cohort_flow.png",
                    ],
                    "source_paths": ["paper/cohort_flow.json"],
                }
            ],
        },
    )

    render_calls: list[str] = []

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
        request_short_template_id: str | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        sidecar_template_id = full_id(request_short_template_id or full_template_id.rsplit("::", 1)[-1])
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(sidecar_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(full_template_id)
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["S1"]
    assert render_calls == [full_id("cohort_flow_figure")]
    assert (paper_root / "figures" / "generated" / "S1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "S1_cohort_flow.pdf").exists()

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert len(figure_catalog["figures"]) == 1
    assert figure_catalog["figures"][0]["figure_id"] == "S1"
    assert figure_catalog["figures"][0]["template_id"] == full_id("cohort_flow_figure")
    assert figure_catalog["figures"][0]["input_schema_id"] == "cohort_flow_shell_inputs_v1"
    assert figure_catalog["figures"][0]["paper_role"] == "supplementary"
    assert figure_catalog["figures"][0]["export_paths"] == [
        "paper/figures/generated/S1_cohort_flow.png",
        "paper/figures/generated/S1_cohort_flow.pdf",
    ]


def test_materialize_display_surface_promotes_dpcc_figures_to_purpose_first_r_templates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dpcc_displays = [
        (
            "F2",
            "phenotype_gap_structure",
            "phenotype_gap_structure_figure",
            "dpcc_phenotype_gap_structure_v1",
            "dpcc_phenotype_gap_structure.json",
            {
                "rows": [
                    {
                        "phenotype_label": "Glycemic-dominant diabetes",
                        "share_of_index_patients": 0.34,
                        "severe_glycemia_low_intensity_gap_rate": 0.72,
                        "uncontrolled_glycemia_no_drug_gap_rate": 0.48,
                        "hypertension_no_antihypertensive_gap_rate": 0.58,
                        "dyslipidemia_no_lipid_lowering_gap_rate": 0.66,
                    },
                    {
                        "phenotype_label": "Lower-burden diabetes",
                        "share_of_index_patients": 0.66,
                        "severe_glycemia_low_intensity_gap_rate": None,
                        "uncontrolled_glycemia_no_drug_gap_rate": None,
                        "hypertension_no_antihypertensive_gap_rate": None,
                        "dyslipidemia_no_lipid_lowering_gap_rate": None,
                    },
                ],
            },
        ),
        (
            "F3",
            "site_held_out_stability",
            "site_held_out_stability_figure",
            "dpcc_transition_site_support_v1",
            "dpcc_transition_site_support.json",
            {
                "transition_rows": [
                    {
                        "source_phenotype_label": "Glycemic-dominant diabetes",
                        "target_phenotype_label": "Glycemic-dominant diabetes",
                        "patient_count": 420,
                        "share_of_transition_patients": 0.46,
                    },
                    {
                        "source_phenotype_label": "Lower-burden diabetes",
                        "target_phenotype_label": "Glycemic-dominant diabetes",
                        "patient_count": 180,
                        "share_of_transition_patients": 0.20,
                    },
                ],
                "site_fold_rows": [
                    {"fold_id": "site_fold_1", "index_patients": 320, "share_of_index_patients": 0.54},
                    {"fold_id": "site_fold_2", "index_patients": 280, "share_of_index_patients": 0.46},
                ],
                "visit_coverage": 0.82,
                "eligible_site_count": 2,
            },
        ),
        (
            "F4",
            "treatment_gap_alignment",
            "treatment_gap_alignment_figure",
            "dpcc_treatment_gap_alignment_v1",
            "dpcc_treatment_gap_alignment.json",
            {
                "rows": [
                    {
                        "phenotype_label": "Glycemic-dominant diabetes",
                        "index_patients": 1000,
                        "severe_glycemia_low_intensity_gap_patients": 720,
                        "uncontrolled_glycemia_no_drug_gap_patients": 480,
                        "hypertension_no_antihypertensive_gap_patients": 580,
                        "dyslipidemia_no_lipid_lowering_gap_patients": 660,
                    },
                    {
                        "phenotype_label": "Lower-burden diabetes",
                        "index_patients": 800,
                        "severe_glycemia_low_intensity_gap_patients": 0,
                        "uncontrolled_glycemia_no_drug_gap_patients": 0,
                        "hypertension_no_antihypertensive_gap_patients": 0,
                        "dyslipidemia_no_lipid_lowering_gap_patients": 0,
                    },
                ],
            },
        ),
    ]
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": display_id,
                    "display_kind": "figure",
                    "requirement_key": requirement_key,
                    "catalog_id": figure_id,
                    "shell_path": f"paper/figures/{display_id}.shell.json",
                }
                for figure_id, display_id, requirement_key, _, _, _ in dpcc_displays
            ],
        },
    )
    for figure_id, display_id, requirement_key, schema_id, filename, display_payload in dpcc_displays:
        spec = display_registry.get_evidence_figure_spec(requirement_key)
        assert spec.renderer_family == "r_ggplot2"
        assert spec.input_schema_id == schema_id
        assert spec.template_id == full_id(requirement_key)
        dump_json(
            paper_root / "figures" / f"{display_id}.shell.json",
            {
                "schema_version": 1,
                "display_id": display_id,
                "display_kind": "figure",
                "requirement_key": requirement_key,
                "catalog_id": figure_id,
            },
        )
        dump_json(
            paper_root / filename,
            {
                "schema_version": 1,
                "input_schema_id": schema_id,
                "displays": [
                    {
                        "display_id": display_id,
                        "template_id": full_id(requirement_key),
                        "title": f"{display_id} purpose-first evidence",
                        **display_payload,
                    }
                ],
            },
        )

    render_calls: list[str] = []

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
        request_short_template_id: str | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        sidecar_template_id = full_id(request_short_template_id or full_template_id.rsplit("::", 1)[-1])
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(sidecar_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(full_template_id)
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F2", "F3", "F4"]
    assert render_calls == [full_id(item[2]) for item in dpcc_displays]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {entry["figure_id"]: entry for entry in figure_catalog["figures"]}
    for figure_id, display_id, requirement_key, schema_id, _, _ in dpcc_displays:
        entry = figures_by_id[figure_id]
        assert entry["template_id"] == full_id(requirement_key)
        assert entry["renderer_family"] == "r_ggplot2"
        assert entry["input_schema_id"] == schema_id
        assert entry["qc_result"]["status"] == "pass"
        assert entry["source_renderer"] == f"MAS/DPCC::{requirement_key}"
        assert entry["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"
        assert entry["figure_purpose"] in {
            "phenotype_composition_plus_treatment_gap_matrix",
            "phenotype_transition_stability_plus_site_held_out_support",
            "recorded_treatment_review_gap_burden_small_multiples",
        }
        assert entry["export_paths"] == [
            f"paper/figures/generated/{figure_id}_{requirement_key}.png",
            f"paper/figures/generated/{figure_id}_{requirement_key}.pdf",
        ]

def test_materialize_display_surface_does_not_reference_stale_subprocess_svg(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    stale_svg_path = paper_root / "figures" / "generated" / "F1_cohort_flow.svg"
    stale_svg_path.parent.mkdir(parents=True, exist_ok=True)
    stale_svg_path.write_text("<svg><text>stale</text></svg>\n", encoding="utf-8")

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    module.materialize_display_surface(paper_root=paper_root)

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    entry = next(item for item in figure_catalog["figures"] if item["figure_id"] == "F1")
    assert entry["export_paths"] == [
        "paper/figures/generated/F1_cohort_flow.png",
        "paper/figures/generated/F1_cohort_flow.pdf",
    ]
    assert not stale_svg_path.exists()

def test_materialize_display_surface_uses_pack_runtime_for_cohort_flow_shell(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    render_calls: list[str] = []

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(full_template_id)
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("cohort_flow_figure")]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.pdf").exists()

def test_materialize_display_surface_syncs_figure_semantics_renderer_contract(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": {
                "F1": {
                    "figure_id": "F1",
                    "title": "Cohort flow",
                    "renderer_contract": {
                        "renderer": "python",
                        "allowed_renderers": ["python", "r_ggplot2"],
                        "template_id": "F1",
                        "layout_qc_profile": "F1",
                        "fallback_on_failure": False,
                        "failure_action": "block_and_fix_environment",
                    },
                },
            },
        },
    )

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        dependency_environment: dict[str, object] | None = None,
    ) -> dict[str, object]:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert "paper/figure_semantics_manifest.json" in result["display_pack_surface_sync"]["updated_files"]
    figure_semantics = json.loads((paper_root / "figure_semantics_manifest.json").read_text(encoding="utf-8"))
    renderer_contract = figure_semantics["figures"]["F1"]["renderer_contract"]
    assert renderer_contract["template_id"] == full_id("cohort_flow_figure")
    assert renderer_contract["layout_qc_profile"] == "publication_illustration_flow"
    assert renderer_contract["renderer_family"] == "r_ggplot2"
    assert renderer_contract["renderer"] == "r_ggplot2"
    assert renderer_contract["required_exports"] == ["png", "pdf"]

def test_materialize_display_surface_uses_pack_runtime_for_r_evidence_template(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "roc_curve",
                    "display_kind": "figure",
                    "requirement_key": "roc_curve_binary",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "binary_prediction_curve_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "binary_prediction_curve_inputs_v1",
            "displays": [
                {
                    "display_id": "roc_curve",
                    "template_id": "roc_curve_binary",
                    "title": "ROC curve",
                    "caption": "Receiver operating characteristic curve.",
                    "x_label": "1 - Specificity",
                    "y_label": "Sensitivity",
                    "series": [
                        {
                            "label": "Model",
                            "x": [0.0, 0.2, 1.0],
                            "y": [0.0, 0.8, 1.0],
                        }
                    ],
                }
            ],
        },
    )
    render_calls: list[str] = []

    def fake_subprocess_renderer(
        *,
        full_template_id: str,
        template_manifest,
        runtime_template_root: Path,
        pack_root: Path,
        paper_root: Path,
        figure_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
        request_short_template_id: str | None = None,
    ) -> dict[str, object]:
        template_id = full_template_id
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        sidecar = _minimal_layout_sidecar_for_template(template_id)
        if request_short_template_id:
            sidecar["template_id"] = request_short_template_id
        layout_sidecar_path.write_text(
            json.dumps(sidecar, ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("roc_curve_binary")]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()
