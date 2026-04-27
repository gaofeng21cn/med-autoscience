from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def build_sync_workspace(tmp_path: Path) -> Path:
    paper_root = tmp_path / "workspace" / "paper"
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
                    "display_id": "risk_layering",
                    "display_kind": "figure",
                    "requirement_key": "risk_layering_monotonic_bars",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/risk_layering.shell.json",
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
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "title": "Cohort flow",
            "steps": [
                {"step_id": "screened", "label": "Screened", "n": 100, "detail": "Consecutive"}
            ],
        },
    )
    dump_json(
        paper_root / "risk_layering_monotonic_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "risk_layering_monotonic_inputs_v1",
            "displays": [
                {
                    "display_id": "risk_layering",
                    "catalog_id": "F2",
                    "template_id": "risk_layering_monotonic_bars",
                    "title": "Risk layering",
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
            "groups": [{"group_id": "overall", "label": "Overall"}],
            "variables": [{"variable_id": "age", "label": "Age", "values": ["60"]}],
        },
    )
    dump_json(
        paper_root / "submission_graphical_abstract.json",
        {
            "schema_version": 1,
            "shell_id": "submission_graphical_abstract",
            "display_id": "submission_graphical_abstract",
            "catalog_id": "GA1",
            "paper_role": "submission_companion",
            "title": "Graphical abstract",
            "caption": "Summary",
            "panels": [],
        },
    )
    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "renderer_contract": {
                        "figure_semantics": "illustration",
                        "renderer_family": "html_svg",
                        "template_id": "cohort_flow_figure",
                        "layout_qc_profile": "legacy_flow_qc",
                        "required_exports": ["png", "svg"],
                        "fallback_on_failure": False,
                        "failure_action": "block_and_fix_environment",
                    },
                },
                {
                    "figure_id": "F2",
                    "renderer_contract": {
                        "figure_semantics": "evidence",
                        "renderer_family": "r_ggplot2",
                        "template_id": "risk_layering_monotonic_bars",
                        "layout_qc_profile": "legacy_evidence_qc",
                        "required_exports": ["png"],
                        "fallback_on_failure": False,
                        "failure_action": "block_and_fix_environment",
                    },
                },
            ],
        },
    )
    return paper_root


def test_sync_display_pack_surface_canonicalizes_source_truth(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_pack_surface_sync")
    paper_root = build_sync_workspace(tmp_path)

    result = module.sync_display_pack_surface(paper_root=paper_root)

    assert result["status"] == "synced"
    assert result["updated_files"] == [
        "paper/baseline_characteristics_schema.json",
        "paper/cohort_flow.json",
        "paper/figure_semantics_manifest.json",
        "paper/risk_layering_monotonic_inputs.json",
        "paper/submission_graphical_abstract.json",
    ]
    cohort_flow = load_json(paper_root / "cohort_flow.json")
    assert cohort_flow["shell_id"] == "fenggaolab.org.medical-display-core::cohort_flow_figure"
    evidence_payload = load_json(paper_root / "risk_layering_monotonic_inputs.json")
    assert evidence_payload["displays"][0]["template_id"] == (
        "fenggaolab.org.medical-display-core::risk_layering_monotonic_bars"
    )
    table_payload = load_json(paper_root / "baseline_characteristics_schema.json")
    assert table_payload["table_shell_id"] == (
        "fenggaolab.org.medical-display-core::table1_baseline_characteristics"
    )
    graphical_abstract = load_json(paper_root / "submission_graphical_abstract.json")
    assert graphical_abstract["shell_id"] == (
        "fenggaolab.org.medical-display-core::submission_graphical_abstract"
    )
    figure_semantics = load_json(paper_root / "figure_semantics_manifest.json")
    cohort_flow_contract = figure_semantics["figures"][0]["renderer_contract"]
    assert cohort_flow_contract["template_id"] == "fenggaolab.org.medical-display-core::cohort_flow_figure"
    assert cohort_flow_contract["renderer_family"] == "python"
    assert cohort_flow_contract["layout_qc_profile"] == "publication_illustration_flow"
    assert cohort_flow_contract["required_exports"] == ["png", "svg", "pdf"]
    risk_layering_contract = figure_semantics["figures"][1]["renderer_contract"]
    assert risk_layering_contract["template_id"] == "fenggaolab.org.medical-display-core::risk_layering_monotonic_bars"
    assert risk_layering_contract["renderer_family"] == "python"
    assert risk_layering_contract["layout_qc_profile"] == "publication_risk_layering_bars"
    assert risk_layering_contract["required_exports"] == ["png", "pdf"]


def test_sync_display_pack_surface_resolves_contract_backed_figure_registry(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_pack_surface_sync")
    paper_root = build_sync_workspace(tmp_path)

    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    dump_json(
        reporting_contract_path,
        {
            "schema_version": 1,
            "display_shell_plan": [
                {
                    "display_id": "figure1_local_architecture",
                    "display_kind": "figure",
                    "requirement_key": "local_architecture_overview_figure",
                    "catalog_id": "FLOCAL",
                }
            ],
        },
    )
    registry = load_json(paper_root / "display_registry.json")
    assert isinstance(registry, dict)
    registry["displays"].append(
        {
            "display_id": "figure1_local_architecture",
            "display_kind": "figure",
            "requirement_key": "figure1_local_architecture",
            "catalog_id": "FLOCAL",
            "shell_path": "paper/figures/figure1_local_architecture.shell.json",
        }
    )
    dump_json(paper_root / "display_registry.json", registry)
    dump_json(
        paper_root / "figures" / "figure1_local_architecture.shell.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/figures/figure1_local_architecture.contract.json",
            "display_id": "figure1_local_architecture",
            "display_kind": "figure",
            "requirement_key": "figure1_local_architecture_contract",
            "catalog_id": "FLOCAL",
        },
    )
    dump_json(
        paper_root / "figures" / "figure1_local_architecture.contract.json",
        {
            "schema_version": 1,
            "figure_id": "FLOCAL",
            "display_id": "figure1_local_architecture",
            "paper_role": "main_text",
            "title": "Local architecture overview",
        },
    )
    figure_semantics = load_json(paper_root / "figure_semantics_manifest.json")
    assert isinstance(figure_semantics, dict)
    figure_semantics["figures"].append(
        {
            "figure_id": "FLOCAL",
            "renderer_contract": {
                "figure_semantics": "evidence",
                "renderer_family": "legacy_renderer",
                "template_id": "figure1_local_architecture_contract",
                "layout_qc_profile": "legacy_local_architecture_qc",
                "required_exports": ["png"],
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        }
    )
    dump_json(paper_root / "figure_semantics_manifest.json", figure_semantics)

    result = module.sync_display_pack_surface(paper_root=paper_root)

    assert "paper/figure_semantics_manifest.json" in result["updated_files"]
    updated_semantics = load_json(paper_root / "figure_semantics_manifest.json")
    updated_contract = updated_semantics["figures"][2]["renderer_contract"]
    assert updated_contract["template_id"] == "fenggaolab.org.medical-display-core::risk_layering_monotonic_bars"
    assert updated_contract["renderer_family"] == "python"
    assert updated_contract["layout_qc_profile"] == "publication_risk_layering_bars"
    assert updated_contract["required_exports"] == ["png", "pdf"]


def test_sync_display_pack_surface_resolves_table_requirement_from_shell(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_pack_surface_sync")
    paper_root = build_sync_workspace(tmp_path)

    registry = load_json(paper_root / "display_registry.json")
    assert isinstance(registry, dict)
    registry["displays"].append(
        {
            "display_id": "table2_key_metrics",
            "display_kind": "table",
            "requirement_key": "table2_key_metrics",
            "catalog_id": "T2",
            "shell_path": "paper/tables/table2_key_metrics.shell.json",
        }
    )
    dump_json(paper_root / "display_registry.json", registry)
    dump_json(
        paper_root / "tables" / "table2_key_metrics.shell.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "display_id": "table2_key_metrics",
            "display_kind": "table",
            "requirement_key": "performance_summary_table_generic",
            "catalog_id": "T2",
        },
    )
    dump_json(
        paper_root / "performance_summary_table_generic.json",
        {
            "schema_version": 1,
            "table_shell_id": "table2_key_metrics",
            "display_id": "table2_key_metrics",
            "title": "Key metrics",
            "columns": ["Metric", "Value"],
            "rows": [{"Metric": "AUC", "Value": "0.82"}],
        },
    )

    result = module.sync_display_pack_surface(paper_root=paper_root)

    assert "paper/performance_summary_table_generic.json" in result["updated_files"]
    table_payload = load_json(paper_root / "performance_summary_table_generic.json")
    assert table_payload["table_shell_id"] == "fenggaolab.org.medical-display-core::performance_summary_table_generic"


def test_cli_sync_display_pack_surface_emits_result_json(tmp_path: Path, capsys) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    paper_root = build_sync_workspace(tmp_path)

    exit_code = cli_module.main(["publication", "sync-display-pack", "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "synced"
    assert "paper/risk_layering_monotonic_inputs.json" in payload["updated_files"]
