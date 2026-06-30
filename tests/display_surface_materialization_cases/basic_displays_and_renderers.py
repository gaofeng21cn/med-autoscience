import csv

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
            "guideline_linked_treatment_gap_burden_small_multiples",
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


def test_materialize_display_surface_uses_transportability_governance_template_for_f5(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "transportability_governance",
                    "display_kind": "figure",
                    "requirement_key": "center_transportability_governance_summary_panel",
                    "catalog_id": "F5",
                    "shell_path": "paper/figures/Figure5.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "center_transportability_governance_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "center_transportability_governance_summary_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "transportability_governance",
                    "template_id": full_id("center_transportability_governance_summary_panel"),
                    "title": "Transportability governance",
                    "caption": "Center-level transportability governance summary.",
                    "metric_family": "c_index",
                    "metric_panel_title": "Cohort discrimination",
                    "metric_x_label": "C-index",
                    "metric_reference_value": 0.74,
                    "batch_shift_threshold": 0.04,
                    "slope_acceptance_lower": 0.85,
                    "slope_acceptance_upper": 1.15,
                    "oe_ratio_acceptance_lower": 0.85,
                    "oe_ratio_acceptance_upper": 1.15,
                    "summary_panel_title": "Transportability action",
                    "centers": [
                        {
                            "center_id": "china",
                            "center_label": "China validation",
                            "cohort_role": "external_validation",
                            "support_count": 22800,
                            "event_count": 2180,
                            "metric_estimate": 0.74,
                            "metric_lower": 0.72,
                            "metric_upper": 0.76,
                            "max_shift": 0.03,
                            "slope": 0.96,
                            "oe_ratio": 1.02,
                            "verdict": "stable",
                            "action": "Proceed with monitoring",
                        },
                        {
                            "center_id": "us",
                            "center_label": "US transport",
                            "cohort_role": "transport_target",
                            "support_count": 16420,
                            "event_count": 1520,
                            "metric_estimate": 0.73,
                            "metric_lower": 0.71,
                            "metric_upper": 0.75,
                            "max_shift": 0.05,
                            "slope": 0.91,
                            "oe_ratio": 1.08,
                            "verdict": "monitor",
                            "action": "Monitor calibration drift",
                        },
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
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
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
    assert render_calls == [full_id("center_transportability_governance_summary_panel")]
    assert (paper_root / "figures" / "generated" / "F5_center_transportability_governance_summary_panel.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F5"]["template_id"] == full_id("center_transportability_governance_summary_panel")
    assert figures_by_id["F5"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F5"]["input_schema_id"] == "center_transportability_governance_summary_panel_inputs_v1"
    assert figures_by_id["F5"]["paper_role"] == "main_text"
    assert (
        figures_by_id["F5"]["source_renderer"]
        == "MAS/Transportability::center_transportability_governance_summary_panel"
    )
    assert (
        figures_by_id["F5"]["figure_purpose"]
        == "transportability_discrimination_plus_recalibration_governance_decision_matrix"
    )
    assert figures_by_id["F5"]["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"


def test_materialize_display_surface_reports_missing_evidence_payload_with_owner_route_context(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "transportability_governance",
                    "display_kind": "figure",
                    "requirement_key": "center_transportability_governance_summary_panel",
                    "catalog_id": "F5",
                    "shell_path": "paper/figures/Figure5.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})

    with pytest.raises(ValueError) as excinfo:
        module.materialize_display_surface(paper_root=paper_root)

    message = str(excinfo.value)
    assert "display_id=`transportability_governance`" in message
    assert "requirement_short_id=`center_transportability_governance_summary_panel`" in message
    assert "template_id=`fenggaolab.org.medical-display-core::center_transportability_governance_summary_panel`" in message
    assert "input_schema_id=`center_transportability_governance_summary_panel_inputs_v1`" in message
    assert "expected_input_path=" in message


def test_materialize_display_surface_uses_lookup_only_time_to_event_alias_specs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure2",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                },
                {
                    "display_id": "Figure3",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/Figure3.shell.json",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "time_to_event_discrimination_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure2",
                    "template_id": full_id("time_to_event_discrimination_calibration_panel"),
                    "title": "Time-to-event discrimination and calibration",
                    "caption": "Discrimination and calibration summary.",
                    "panel_a_title": "Discrimination",
                    "panel_b_title": "Calibration",
                    "discrimination_x_label": "Model",
                    "calibration_x_label": "Predicted 5-year risk",
                    "calibration_y_label": "Observed 5-year risk",
                    "discrimination_points": [
                        {"label": "Model", "c_index": 0.81},
                    ],
                    "calibration_summary": [
                        {
                            "group_label": "Low risk",
                            "group_order": 1,
                            "n": 80,
                            "events_5y": 5,
                            "predicted_risk_5y": 0.07,
                            "observed_risk_5y": 0.06,
                        },
                        {
                            "group_label": "High risk",
                            "group_order": 2,
                            "n": 60,
                            "events_5y": 18,
                            "predicted_risk_5y": 0.28,
                            "observed_risk_5y": 0.30,
                        },
                    ],
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_grouped_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure3",
                    "template_id": full_id("time_to_event_risk_group_summary"),
                    "title": "Risk-group summary",
                    "caption": "Risk-group event summary.",
                    "panel_a_title": "Risk gradient",
                    "panel_b_title": "Events",
                    "x_label": "Risk group",
                    "y_label": "5-year risk",
                    "event_count_y_label": "Events",
                    "risk_group_summaries": [
                        {
                            "label": "Low risk",
                            "sample_size": 80,
                            "events_5y": 5,
                            "mean_predicted_risk_5y": 0.07,
                            "observed_km_risk_5y": 0.06,
                        },
                        {
                            "label": "High risk",
                            "sample_size": 60,
                            "events_5y": 18,
                            "mean_predicted_risk_5y": 0.28,
                            "observed_km_risk_5y": 0.30,
                        },
                    ],
                }
            ],
        },
    )
    render_calls: list[tuple[str, str | None]] = []

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
        template_id = full_id(request_short_template_id or full_template_id.rsplit("::", 1)[-1])
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
        render_calls.append((full_template_id, request_short_template_id))
        return {"status": "rendered", "figure_id": figure_id}

    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")
    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [
        (full_id("time_dependent_roc_horizon"), "time_to_event_discrimination_calibration_panel"),
        (full_id("risk_layering_monotonic_bars"), "time_to_event_risk_group_summary"),
    ]
    assert (paper_root / "figures" / "generated" / "F2_time_to_event_discrimination_calibration_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F3_time_to_event_risk_group_summary.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F2"]["template_id"] == full_id("time_to_event_discrimination_calibration_panel")
    assert figures_by_id["F2"]["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert figures_by_id["F2"]["qc_result"]["status"] == "pass"
    assert figures_by_id["F2"]["source_renderer"] == "MAS/DisplayPack::time_to_event_discrimination_calibration_panel"
    assert figures_by_id["F2"]["figure_purpose"] == "time_to_event_discrimination_plus_calibration_summary"
    assert figures_by_id["F2"]["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"
    assert figures_by_id["F3"]["template_id"] == full_id("time_to_event_risk_group_summary")
    assert figures_by_id["F3"]["input_schema_id"] == "time_to_event_grouped_inputs_v1"
    assert figures_by_id["F3"]["qc_result"]["status"] == "pass"
    assert figures_by_id["F3"]["source_renderer"] == "MAS/DisplayPack::time_to_event_risk_group_summary"
    assert figures_by_id["F3"]["figure_purpose"] == "time_to_event_risk_group_gradient_plus_event_counts"
    assert figures_by_id["F3"]["rendered_title_policy"] == "figure_title_metadata_only_not_drawn_inside_plot"


def test_materialize_display_surface_writes_display_pack_lock(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    module.materialize_display_surface(paper_root=paper_root)

    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    assert lock_payload["schema_version"] == 2
    assert lock_payload["paper_config_present"] is False
    assert lock_payload["enabled_pack_ids"] == ["fenggaolab.org.medical-display-core"]
    assert lock_payload["enabled_packs"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert lock_payload["enabled_packs"][0]["requested_version"] == "0.1.0"
    assert lock_payload["enabled_packs"][0]["declared_in"] == "repo"

def test_materialize_display_surface_uses_paper_pack_override_and_writes_versioned_lock(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
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
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
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
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "all", "label": "All patients"},
            ],
            "variables": [
                {"variable_id": "age", "label": "Age, y", "values": ["61 (54-68)"]},
            ],
        },
    )

    (paper_root / "display_packs.toml").write_text(
        """
inherit_repo_defaults = true
enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "paper-external/display-packs/medical-display-core"
version = "0.2.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    pack_root = paper_root / "paper-external" / "display-packs" / "medical-display-core"
    (pack_root / "templates" / "table1_baseline_characteristics").mkdir(parents=True)
    (pack_root / "src" / "paper_override_display_core").mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                'version = "0.2.0"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
                'summary = "Paper-local override pack"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "templates" / "table1_baseline_characteristics" / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "table1_baseline_characteristics"',
                'full_template_id = "fenggaolab.org.medical-display-core::table1_baseline_characteristics"',
                'kind = "table_shell"',
                'display_name = "Baseline characteristics"',
                'paper_family_ids = ["H"]',
                'audit_family = "Publication Shells and Tables"',
                'renderer_family = "n/a"',
                'input_schema_ref = "table1_baseline_characteristics_inputs_v1"',
                'qc_profile_ref = "publication_table_shell"',
                'required_exports = ["md", "csv"]',
                'allowed_paper_roles = ["main_text", "supplementary"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "paper_override_display_core.table_shells:render_table_shell"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "src" / "paper_override_display_core" / "__init__.py").write_text("", encoding="utf-8")
    (pack_root / "src" / "paper_override_display_core" / "table_shells.py").write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "",
                "from pathlib import Path",
                "",
                "def render_table_shell(*, template_id: str, payload_path: Path, payload: dict[str, object], output_md_path: Path, output_csv_path: Path | None = None) -> dict[str, str]:",
                "    output_md_path.parent.mkdir(parents=True, exist_ok=True)",
                '    output_md_path.write_text("# Paper override baseline characteristics\\n\\n| Characteristic | Overall |\\n| --- | --- |\\n| Age | 60 |\\n", encoding="utf-8")',
                "    if output_csv_path is not None:",
                '        output_csv_path.write_text("Characteristic,Overall\\nAge,60\\n", encoding="utf-8")',
                '    return {"title": "Paper override baseline characteristics", "caption": "Paper-local override version."}',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert "Paper override baseline characteristics" in (
        paper_root / "tables" / "generated" / "T1_baseline_characteristics.md"
    ).read_text(encoding="utf-8")

    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    entry = lock_payload["enabled_packs"][0]
    assert lock_payload["paper_config_present"] is True
    assert entry["declared_in"] == "paper"
    assert entry["requested_version"] == "0.2.0"
    assert entry["version"] == "0.2.0"
    assert entry["source_path"] == "paper-external/display-packs/medical-display-core"

def test_materialize_display_surface_uses_catalog_ids_for_semantic_shell_display_ids(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _write_prepared_dependency_environment(paper_root)
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
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                    "shell_path": "paper/tables/baseline_characteristics.shell.json",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
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
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                }
            ],
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "all", "label": "All patients"},
            ],
            "variables": [
                {"variable_id": "age", "label": "Age, y", "values": ["61 (54-68)"]},
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    assert result["tables_materialized"] == ["T1"]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.pdf").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert table_catalog["tables"][0]["table_id"] == "T1"

def test_materialize_display_surface_defaults_study_setup_shells_to_supplementary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _write_prepared_dependency_environment(paper_root)
    write_default_publication_display_contracts(paper_root)
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
                    "catalog_id": "S1",
                    "shell_path": "paper/figures/cohort_flow.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "S1",
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["S1"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "S1"
    assert figure_catalog["figures"][0]["paper_role"] == "supplementary"

def test_materialize_display_surface_honors_registry_paper_role_for_study_setup_shells(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _write_prepared_dependency_environment(paper_root)
    write_default_publication_display_contracts(paper_root)
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
                    "paper_role": "main_text",
                    "shell_path": "paper/figures/cohort_flow.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert figure_catalog["figures"][0]["paper_role"] == "main_text"
