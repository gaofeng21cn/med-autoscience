from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest

from med_autoscience import display_registry
from med_autoscience.display_pack_resolver import get_template_short_id

from tests.display_surface_materialization_cases.layout_sidecar_fixtures import (
    _minimal_layout_sidecar_for_template,
)
from tests.display_surface_materialization_cases.registry_id_helpers import (
    _ensure_output_parents,
)
from tests.display_surface_materialization_cases.shared import (
    use_current_scholarskills_display_pack,
)


@pytest.fixture(autouse=True)
def _fake_subprocess_display_renderer(monkeypatch):
    use_current_scholarskills_display_pack()
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
        request_short_template_id=None,
    ):
        assert dependency_environment is None or dependency_environment.get("status") == "prepared"
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_bytes(b"png")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        sidecar_template_id = template_manifest.template_id
        layout_sidecar_path.write_text(
            json.dumps(
                _minimal_layout_sidecar_for_template(full_template_id, display_payload=display_payload),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return {
            "status": "rendered",
            "figure_id": figure_id,
            "title": str(display_payload.get("title") or "").strip(),
            "caption": str(display_payload.get("caption") or "").strip(),
            "execution_mode": "subprocess",
            "renderer_family": template_manifest.renderer_family,
            "dependency_environment": dict(dependency_environment or {}),
        }

    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)
    yield
    display_registry._active_template_manifests.cache_clear()
    display_registry._active_registry_state.cache_clear()


from tests.display_surface_materialization_cases.registry_id_helpers import (
    dump_json,
    write_default_publication_display_contracts,
)
from tests.display_surface_materialization_cases.workspace_surface_fixtures import (
    build_display_surface_workspace,
)
from tests.display_surface_materialization_cases.contract_backed_registry_materialization import (
    test_materialize_display_surface_restores_contract_backed_and_shell_mapped_figures,
    test_materialize_display_surface_rejects_invalid_contract_backed_layout_sidecar,
)


def test_materialize_display_surface_preserves_all_workspace_evidence_template_owners(
    tmp_path,
    monkeypatch,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    materialize_module = importlib.import_module(
        "med_autoscience.controllers.display_surface_materialization.materialize"
    )

    def fake_subprocess_renderer(
        *,
        full_template_id,
        template_manifest,
        figure_id,
        output_png_path,
        output_pdf_path,
        layout_sidecar_path,
        **_kwargs,
    ):
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_bytes(b"png")
        output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        layout_sidecar = (
            _minimal_layout_sidecar_for_template(full_template_id)
            if get_template_short_id(full_template_id) == "cohort_flow_figure"
            else {
                "template_id": full_template_id,
                "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
                "layout_boxes": [],
                "panel_boxes": [],
                "guide_boxes": [],
                "metrics": {"renderer_family": template_manifest.renderer_family},
            }
        )
        layout_sidecar_path.write_text(
            json.dumps(layout_sidecar, ensure_ascii=False),
            encoding="utf-8",
        )
        return {"status": "rendered", "figure_id": figure_id}

    monkeypatch.setattr(materialize_module, "_run_subprocess_renderer", fake_subprocess_renderer)
    monkeypatch.setattr(
        materialize_module.display_layout_qc,
        "run_display_layout_qc",
        lambda *, qc_profile, layout_sidecar: {
            "status": "pass",
            "checked_at": "2026-07-11T00:00:00+00:00",
            "engine_id": "test_all_workspace_evidence_template_owners",
            "qc_profile": qc_profile,
            "issues": [],
            "audit_classes": [],
            "failure_reason": "",
            "readability_findings": [],
            "revision_note": "",
            "metrics": layout_sidecar.get("metrics") or {},
        },
    )
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)

    result = controller.materialize_display_surface(paper_root=paper_root)

    catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    active_by_id = {
        spec.template_id: spec
        for spec in display_registry.list_evidence_figure_specs()
    }
    specs = tuple(
        active_by_id[template_id]
        for template_id in display_registry._EVIDENCE_TEMPLATE_ORDER
    )
    figures_by_template_id = {
        figure["template_id"]: figure
        for figure in catalog["figures"]
        if figure.get("template_id") in {spec.template_id for spec in specs}
    }
    assert len(specs) == 38
    assert set(figures_by_template_id) == {spec.template_id for spec in specs}

    for spec in specs:
        figure = figures_by_template_id[spec.template_id]
        assert figure["renderer_family"] == spec.renderer_family
        assert figure["input_schema_id"] == spec.input_schema_id
        assert figure["qc_profile"] == spec.layout_qc_profile
        assert {Path(path).suffix.removeprefix(".") for path in figure["export_paths"]} == set(
            spec.required_exports
        )
        payload = json.loads((paper_root.parent / figure["source_paths"][0]).read_text(encoding="utf-8"))
        assert payload["input_schema_id"] == spec.input_schema_id
        assert spec.template_id in {item["template_id"] for item in payload["displays"]}
        sidecar = json.loads(
            (paper_root.parent / figure["qc_result"]["layout_sidecar_path"]).read_text(encoding="utf-8")
        )
        assert figure["qc_result"]["status"] == "pass"
        assert sidecar["template_id"] == spec.template_id

    receipt = result["visual_audit_receipt"]
    assert receipt["final_status"] == "clear"
    assert receipt["inspected_artifact_count"] == len(result["figures_materialized"])


def test_materialize_display_visual_audit_flags_dense_transition_heatmap_without_authority(
    tmp_path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    quality_contract = importlib.import_module("med_autoscience.publication_figure_quality_contract")
    paper_root = tmp_path / "paper"
    figure_root = paper_root / "figures" / "generated"
    figure_root.mkdir(parents=True)
    artifact_path = figure_root / "F3_site_held_out_stability_figure.png"
    artifact_path.write_bytes(b"PNG")
    sidecar_path = figure_root / "F3_site_held_out_stability_figure.layout.json"
    dump_json(
        sidecar_path,
        {
            "schema_version": 1,
            "template_id": "site_held_out_stability_figure",
            "metrics": {"transition_rows": [{} for _ in range(24)]},
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

    result = controller.materialize_display_visual_audit(paper_root=paper_root)

    receipt = quality_contract.load_figure_visual_audit_receipt(
        paper_root / "figure_visual_audit_receipt.json"
    )
    assert result["visual_audit_receipt"]["final_status"] == "findings_open"
    assert result["authority_boundary"]["writes_authority"] is False
    assert result["authority_boundary"]["writes_current_package"] is False
    assert not (paper_root.parent / "manuscript" / "current_package").exists()
    assert receipt["inspected_artifacts"][0]["artifact_sha256"] == hashlib.sha256(
        artifact_path.read_bytes()
    ).hexdigest()
    assert receipt["findings"][0]["figure_id"] == "F3"
    assert "transition heatmap" in receipt["findings"][0]["observed_issue"].lower()
