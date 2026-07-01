from __future__ import annotations

import importlib
import hashlib
import json
from pathlib import Path
import subprocess

from tests.display_surface_materialization_cases.layout_sidecar_fixtures import _minimal_layout_sidecar_for_template
from tests.display_surface_materialization_cases.workspace_surface_fixtures import (
    _write_prepared_dependency_environment,
    build_display_surface_workspace as build_registered_display_surface_workspace,
    restrict_display_registry_to_display_ids,
)

DISPLAY_SURFACE_COMMAND = ("publication", "materialize-display-surface")
DISPLAY_VISUAL_AUDIT_COMMAND = ("publication", "materialize-display-visual-audit")


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
) -> None:
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_png_path.write_text(f"PNG:{template_id}:{display_payload['display_id']}", encoding="utf-8")
    output_pdf_path.write_text("%PDF", encoding="utf-8")
    if output_svg_path is not None:
        output_svg_path.write_text(f"<svg><title>{template_id}</title></svg>", encoding="utf-8")
    layout_sidecar_path.write_text(
        json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
        encoding="utf-8",
    )


def patch_evidence_figure_renderer(controller_module, monkeypatch) -> None:
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
        )
        return {"renderer": "test_fake_evidence_figure_renderer", "figure_id": figure_id}

    monkeypatch.setattr(
        materialize_module,
        "_render_evidence_figure_by_template_runtime",
        render_evidence_figure_by_template_runtime,
    )


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


def test_cli_materialize_display_surface_uses_subprocess_renderer_for_subprocess_evidence_template(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    subprocess_runtime = importlib.import_module("med_autoscience.display_pack_e2e_runtime")
    paper_root = build_registered_display_surface_workspace(tmp_path, include_extended_evidence=True)
    restrict_display_registry_to_display_ids(paper_root, "Figure14")
    expected_template_id = "generalizability_subgroup_composite_panel"

    def fake_run(argv, *, cwd, capture_output, text, check, timeout, env):
        request_path = Path(env["MAS_DISPLAY_RENDER_REQUEST"])
        request_payload = json.loads(request_path.read_text(encoding="utf-8"))
        display_payload = request_payload["display_payload"]
        template_id = request_payload["short_template_id"]
        Path(env["MAS_DISPLAY_OUTPUT_PNG"]).write_text(f"PNG:{template_id}", encoding="utf-8")
        Path(env["MAS_DISPLAY_OUTPUT_PDF"]).write_text("%PDF", encoding="utf-8")
        Path(env["MAS_DISPLAY_LAYOUT_SIDECAR"]).write_text(
            json.dumps(
                {
                    **_minimal_layout_sidecar_for_template(template_id),
                    "render_context": display_payload["render_context"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(argv, 0, stdout="rendered\n", stderr="")

    monkeypatch.setattr(subprocess_runtime.subprocess, "run", fake_run)

    exit_code = cli_module.main([*DISPLAY_SURFACE_COMMAND, "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    request_payload = json.loads(
        (
            paper_root
            / "build"
            / "display_pack_render_requests"
            / "F14.render_request.json"
        ).read_text(encoding="utf-8")
    )
    catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure = catalog["figures"][0]
    assert exit_code == 0
    assert payload["status"] == "materialized"
    assert payload["figures_materialized"] == ["F14"]
    assert request_payload["execution_mode"] == "subprocess"
    assert request_payload["short_template_id"] == expected_template_id
    assert figure["template_id"].endswith(f"::{expected_template_id}")
    assert figure["export_paths"] == [
        f"paper/figures/generated/F14_{expected_template_id}.png",
        f"paper/figures/generated/F14_{expected_template_id}.pdf",
    ]


def test_r_evidence_renderer_keeps_figure_titles_as_metadata_only() -> None:
    source_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.r_source")

    renderer_source = source_module._R_EVIDENCE_RENDERER_SOURCE

    assert "display_payload$title" not in renderer_source
    assert renderer_source.count("title = NULL") >= 1


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


def test_cli_materialize_display_surface_includes_full_registered_template_set(tmp_path, monkeypatch, capsys) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_registered_display_surface_workspace(tmp_path, include_extended_evidence=True)
    patch_evidence_figure_renderer(controller_module, monkeypatch)
    patch_layout_qc_pass(controller_module, monkeypatch)

    exit_code = cli_module.main([*DISPLAY_SURFACE_COMMAND, "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["figures_materialized"] == expected_catalog_ids(paper_root=paper_root, display_kind="figure")
    assert payload["tables_materialized"] == expected_catalog_ids(paper_root=paper_root, display_kind="table")
