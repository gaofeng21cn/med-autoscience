from tests.display_surface_materialization_cases.shared import *


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
