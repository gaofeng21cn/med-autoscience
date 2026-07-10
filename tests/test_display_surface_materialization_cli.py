from __future__ import annotations

import importlib
import hashlib
import json
from pathlib import Path

import pytest

from med_autoscience import display_registry

from tests.display_surface_materialization_cases.layout_sidecar_fixtures import _minimal_layout_sidecar_for_template
from tests.display_surface_materialization_cases.shared import (
    current_scholarskills_core_pack_root,
    use_current_scholarskills_display_pack,
)
from tests.display_surface_materialization_cases.workspace_surface_fixtures import (
    _write_prepared_dependency_environment,
    build_display_surface_workspace as build_registered_display_surface_workspace,
)

DISPLAY_SURFACE_COMMAND = ("publication", "materialize-display-surface")
DISPLAY_VISUAL_AUDIT_COMMAND = ("publication", "materialize-display-visual-audit")


@pytest.fixture(autouse=True)
def _use_current_scholarskills_display_pack(monkeypatch):
    use_current_scholarskills_display_pack(monkeypatch)
    yield
    display_registry._active_template_manifests.cache_clear()
    display_registry._active_registry_state.cache_clear()


def expected_catalog_ids(*, paper_root: Path, display_kind: str) -> list[str]:
    registry_payload = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))
    prefix_by_kind = {
        "figure": ("Figure", "F"),
        "table": ("Table", "T"),
    }
    display_prefix, catalog_prefix = prefix_by_kind[display_kind]
    return [
        str(item.get("display_id") or "").strip().replace(display_prefix, catalog_prefix, 1)
        for item in (registry_payload.get("displays") or [])
        if str(item.get("display_kind") or "").strip() == display_kind
    ]


def dump_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_display_surface_workspace(tmp_path):
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure1",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "shell_path": "paper/figures/Figure1.shell.json",
                },
                {
                    "display_id": "Table1",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "shell_path": "paper/tables/Table1.shell.json",
                },
            ],
        },
    )
    dump_json(
        paper_root / "figures" / "Figure1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
        },
    )
    dump_json(
        paper_root / "tables" / "Table1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort flow",
            "steps": [
                {"step_id": "screened", "label": "Patients screened", "n": 186, "detail": "Consecutive cases"},
                {"step_id": "included", "label": "Included in analysis", "n": 128, "detail": "Primary cohort"},
            ],
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "Table1",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "overall", "label": "Overall (n=128)"},
                {"group_id": "high_risk", "label": "High risk (n=55)"},
            ],
            "variables": [
                {
                    "variable_id": "age",
                    "label": "Age, median (IQR)",
                    "values": ["52 (44-61)", "58 (50-66)"],
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    return paper_root


def fake_evidence_figure_renderer(
    *,
    template_id: str,
    display_payload: dict[str, object],
    output_png_path,
    output_pdf_path,
    layout_sidecar_path,
    output_svg_path=None,
    use_profile_sidecar: bool = True,
) -> None:
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_png_path.write_text(f"PNG:{template_id}:{display_payload['display_id']}", encoding="utf-8")
    output_pdf_path.write_text("%PDF", encoding="utf-8")
    if output_svg_path is not None:
        output_svg_path.write_text(f"<svg><title>{template_id}</title></svg>", encoding="utf-8")
    layout_sidecar = (
        _minimal_layout_sidecar_for_template(template_id)
        if use_profile_sidecar
        else {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [],
            "panel_boxes": [],
            "guide_boxes": [],
            "metrics": {"source_renderer": "test_fake_evidence_figure_renderer"},
        }
    )
    layout_sidecar_path.write_text(json.dumps(layout_sidecar, ensure_ascii=False), encoding="utf-8")


def patch_evidence_figure_renderer(
    controller_module,
    monkeypatch,
    *,
    use_profile_sidecar: bool = True,
) -> None:
    materialize_module = importlib.import_module(
        "med_autoscience.controllers.display_surface_materialization.materialize"
    )

    def render_evidence_figure_by_template_runtime(
        *,
        template_id: str,
        display_payload: dict[str, object],
        paper_root: Path,
        figure_id: str,
        output_png_path,
        output_pdf_path,
        layout_sidecar_path,
        output_svg_path=None,
    ) -> dict[str, object]:
        fake_evidence_figure_renderer(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
            output_svg_path=output_svg_path,
            use_profile_sidecar=use_profile_sidecar,
        )
        return {"renderer": "test_fake_evidence_figure_renderer", "figure_id": figure_id}

    monkeypatch.setattr(
        materialize_module,
        "_render_evidence_figure_by_template_runtime",
        render_evidence_figure_by_template_runtime,
    )


def test_dpcc_transition_heatmap_renderer_uses_sparse_percent_cell_labels() -> None:
    renderer_path = (
        current_scholarskills_core_pack_root()
        / "rlib"
        / "medicaldisplaycore"
        / "dpcc_primary_care_renderers.R"
    )
    renderer_source = renderer_path.read_text(encoding="utf-8")

    transition_renderer = renderer_source.split("dpcc_plot_transition_site_support <- function(payload) {", 1)[1]
    transition_renderer = transition_renderer.split("dpcc_plot_treatment_gap_alignment <- function(payload) {", 1)[0]
    assert "(n=%s)" not in transition_renderer
    assert "share_of_transition_patients >= 0.04" in transition_renderer
    assert 'transition_cell_label_policy = "major_share_percent_only_no_counts"' in renderer_source
    assert 'site_support_label_policy = "percent_only_counts_remain_in_table"' in renderer_source


def patch_layout_qc_pass(controller_module, monkeypatch) -> None:
    materialize_module = importlib.import_module(
        "med_autoscience.controllers.display_surface_materialization.materialize"
    )

    def run_display_layout_qc(*, qc_profile: str, layout_sidecar: dict[str, object]) -> dict[str, object]:
        return {
            "status": "pass",
            "checked_at": "2026-06-20T00:00:00+00:00",
            "engine_id": "test_layout_qc_pass",
            "qc_profile": qc_profile,
            "issues": [],
            "audit_classes": [],
            "failure_reason": "",
            "readability_findings": [],
            "revision_note": "",
            "metrics": layout_sidecar.get("metrics") or {},
        }

    monkeypatch.setattr(materialize_module.display_layout_qc, "run_display_layout_qc", run_display_layout_qc)


def test_cli_materialize_display_surface_emits_result_json(tmp_path, capsys) -> None:
    module = importlib.import_module("med_autoscience.cli")
    paper_root = build_display_surface_workspace(tmp_path)
    _write_prepared_dependency_environment(paper_root)

    exit_code = module.main([*DISPLAY_SURFACE_COMMAND, "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "materialized"
    assert payload["figures_materialized"] == ["F1"]
    assert payload["tables_materialized"] == ["T1"]


def test_cli_materialize_display_surface_includes_registered_evidence_figures(tmp_path, monkeypatch, capsys) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    quality_contract = importlib.import_module("med_autoscience.publication_figure_quality_contract")
    paper_root = build_registered_display_surface_workspace(tmp_path, include_evidence=True)
    patch_evidence_figure_renderer(controller_module, monkeypatch)

    exit_code = cli_module.main([*DISPLAY_SURFACE_COMMAND, "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    receipt_path = paper_root / "figure_visual_audit_receipt.json"
    receipt = quality_contract.load_figure_visual_audit_receipt(receipt_path)
    first_artifact = receipt["inspected_artifacts"][0]
    first_artifact_path = paper_root.parent / first_artifact["artifact_path"]
    assert exit_code == 0
    assert payload["figures_materialized"] == expected_catalog_ids(paper_root=paper_root, display_kind="figure")
    assert payload["tables_materialized"] == expected_catalog_ids(paper_root=paper_root, display_kind="table")
    assert payload["visual_audit_receipt"]["final_status"] == "clear"
    assert payload["visual_audit_receipt"]["inspected_artifact_count"] == len(payload["figures_materialized"])
    assert receipt["final_status"] == "clear"
    assert first_artifact["artifact_sha256"] == hashlib.sha256(first_artifact_path.read_bytes()).hexdigest()


def test_cli_materialize_display_visual_audit_refreshes_receipt_after_export(tmp_path, monkeypatch, capsys) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    quality_contract = importlib.import_module("med_autoscience.publication_figure_quality_contract")
    paper_root = build_registered_display_surface_workspace(tmp_path, include_evidence=True)
    patch_evidence_figure_renderer(controller_module, monkeypatch)

    assert cli_module.main([*DISPLAY_SURFACE_COMMAND, "--paper-root", str(paper_root)]) == 0
    capsys.readouterr()
    (paper_root / "submission_minimal").mkdir()
    (paper_root / "submission_minimal" / "paper.pdf").write_bytes(b"%PDF-1.4\n")

    exit_code = cli_module.main([*DISPLAY_VISUAL_AUDIT_COMMAND, "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    receipt = quality_contract.load_figure_visual_audit_receipt(paper_root / "figure_visual_audit_receipt.json")
    assert exit_code == 0
    assert payload["status"] == "visual_audit_receipt_materialized"
    assert payload["visual_audit_receipt"]["final_status"] == "clear"
    assert payload["visual_audit_receipt"]["inspected_artifact_count"] == len(receipt["inspected_artifacts"])
    assert payload["authority_boundary"]["writes_authority"] is False
    assert not (paper_root.parent / "manuscript" / "current_package").exists()


def test_cli_materialize_display_visual_audit_flags_dense_transition_heatmap_without_label_policy(
    tmp_path,
    capsys,
) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    quality_contract = importlib.import_module("med_autoscience.publication_figure_quality_contract")
    paper_root = tmp_path / "paper"
    figure_root = paper_root / "figures" / "generated"
    figure_root.mkdir(parents=True)
    (figure_root / "F3_site_held_out_stability_figure.png").write_bytes(b"PNG")
    dense_rows = [
        {
            "source_phenotype_label": f"Source {index // 6}",
            "target_phenotype_label": f"Target {index % 6}",
            "patient_count": 100 + index,
            "share_of_transition_patients": 0.02,
        }
        for index in range(36)
    ]
    dump_json(
        figure_root / "F3_site_held_out_stability_figure.layout.json",
        {
            "schema_version": 1,
            "template_id": "site_held_out_stability_figure",
            "metrics": {
                "source_renderer": "MAS/DPCC::site_held_out_stability_figure",
                "figure_purpose": "phenotype_transition_stability_plus_site_held_out_support",
                "rendered_title_policy": "figure_title_metadata_only_not_drawn_inside_plot",
                "transition_rows": dense_rows,
            },
        },
    )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F3",
                    "template_id": "fenggaolab.org.medical-display-core::site_held_out_stability_figure",
                    "export_paths": ["paper/figures/generated/F3_site_held_out_stability_figure.png"],
                    "qc_result": {
                        "layout_sidecar_path": "paper/figures/generated/F3_site_held_out_stability_figure.layout.json"
                    },
                }
            ],
        },
    )

    exit_code = cli_module.main([*DISPLAY_VISUAL_AUDIT_COMMAND, "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    receipt = quality_contract.load_figure_visual_audit_receipt(paper_root / "figure_visual_audit_receipt.json")
    assert exit_code == 0
    assert payload["visual_audit_receipt"]["final_status"] == "findings_open"
    assert receipt["final_status"] == "findings_open"
    assert receipt["findings"][0]["figure_id"] == "F3"
    assert "transition heatmap" in receipt["findings"][0]["observed_issue"]


def test_cli_materialize_display_surface_preserves_base_registered_template_owners(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_registered_display_surface_workspace(tmp_path, include_extended_evidence=True)
    patch_evidence_figure_renderer(controller_module, monkeypatch, use_profile_sidecar=False)
    patch_layout_qc_pass(controller_module, monkeypatch)

    exit_code = cli_module.main([*DISPLAY_SURFACE_COMMAND, "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    base_owner_ids = set(display_registry._EVIDENCE_TEMPLATE_ORDER)
    expected_specs = tuple(
        spec
        for spec in display_registry.list_evidence_figure_specs()
        if spec.template_id in base_owner_ids
    )
    figures_by_template_id = {
        figure["template_id"]: figure
        for figure in catalog["figures"]
        if figure.get("template_id") in base_owner_ids
    }

    assert exit_code == 0
    assert result["figures_materialized"] == expected_catalog_ids(paper_root=paper_root, display_kind="figure")
    assert {spec.template_id for spec in expected_specs} == base_owner_ids
    assert set(figures_by_template_id) == base_owner_ids

    for spec in expected_specs:
        figure = figures_by_template_id[spec.template_id]
        assert figure["pack_id"] == spec.template_id.split("::", 1)[0]
        assert figure["renderer_family"] == spec.renderer_family
        assert figure["input_schema_id"] == spec.input_schema_id
        assert figure["qc_profile"] == spec.layout_qc_profile
        assert figure["render_result"]["renderer"] == "test_fake_evidence_figure_renderer"
        assert {Path(path).suffix.removeprefix(".") for path in figure["export_paths"]} == set(
            spec.required_exports
        )

        payload_path = paper_root.parent / figure["source_paths"][0]
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        assert payload["input_schema_id"] == spec.input_schema_id
        assert spec.template_id in {item["template_id"] for item in payload["displays"]}

        qc_result = figure["qc_result"]
        assert qc_result["status"] == "pass"
        assert qc_result["qc_profile"] == spec.layout_qc_profile
        sidecar_path = paper_root.parent / qc_result["layout_sidecar_path"]
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert sidecar["template_id"] == spec.template_id
