from tests.display_surface_materialization_cases.shared import *


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
