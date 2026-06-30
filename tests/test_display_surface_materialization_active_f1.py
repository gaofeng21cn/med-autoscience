from __future__ import annotations

import importlib
import json

import pytest

from tests.display_surface_materialization_cases.layout_sidecar_fixtures import (
    _minimal_layout_sidecar_for_template,
)
from tests.display_surface_materialization_cases.registry_id_helpers import (
    _ensure_output_parents,
)
from tests.display_surface_materialization_cases.shared import (
    Path,
    build_display_surface_workspace,
    dump_json,
    full_id,
    restrict_display_registry_to_display_ids,
)


@pytest.fixture(autouse=True)
def _fake_subprocess_display_renderer(monkeypatch):
    materialize_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.materialize")

    def fake_subprocess_renderer(
        *,
        full_template_id,
        template_manifest,
        runtime_template_root,
        pack_root,
        paper_root,
        figure_id,
        display_payload,
        output_png_path,
        output_pdf_path,
        layout_sidecar_path,
        dependency_environment=None,
    ):
        assert dependency_environment is None or dependency_environment.get("status") == "prepared"
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_bytes(b"png")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        return {
            "status": "rendered",
            "figure_id": figure_id,
            "execution_mode": "subprocess",
            "renderer_family": template_manifest.renderer_family,
            "dependency_environment": dict(dependency_environment or {}),
        }

    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)


def test_materialize_display_surface_preserves_active_display_pack_f1_exports(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    restrict_display_registry_to_display_ids(paper_root, "cohort_flow")

    generated_root = paper_root / "figures" / "generated"
    generated_root.mkdir(parents=True, exist_ok=True)
    active_png = generated_root / "F1.png"
    active_pdf = generated_root / "F1.pdf"
    active_layout = generated_root / "F1.layout.json"
    legacy_png = generated_root / "F1_cohort_flow.png"
    active_png.write_bytes(b"active-png")
    active_pdf.write_text("%PDF-1.4\n", encoding="utf-8")
    dump_json(active_layout, _minimal_layout_sidecar_for_template("cohort_flow_figure"))
    legacy_png.write_bytes(b"legacy-png")
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": full_id("cohort_flow_figure"),
                    "pack_id": "fenggaolab.org.medical-display-core",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "cohort_flow_shell_inputs_v1",
                    "qc_profile": "publication_illustration_flow",
                    "qc_result": {
                        "status": "pass",
                        "layout_sidecar_path": "paper/figures/generated/F1.layout.json",
                    },
                    "export_paths": [
                        "paper/figures/generated/F1.png",
                        "paper/figures/generated/F1.pdf",
                    ],
                    "rendered_artifact_refs": [
                        "paper/figures/generated/F1.png",
                        "paper/figures/generated/F1.pdf",
                        "paper/figures/generated/F1.layout.json",
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert "paper/figures/generated/F1.png" not in result["pruned_generated_paths"]
    assert active_png.exists()
    assert active_pdf.exists()
    assert active_layout.exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    f1 = figure_catalog["figures"][0]
    assert f1["export_paths"] == [
        "paper/figures/generated/F1.png",
        "paper/figures/generated/F1.pdf",
    ]
    assert f1["qc_result"]["layout_sidecar_path"] == "paper/figures/generated/F1.layout.json"
    assert not legacy_png.exists()
