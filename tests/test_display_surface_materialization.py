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


from tests.display_surface_materialization_cases.shared import *
from tests.display_surface_materialization_cases.basic_displays_and_renderers import *
from tests.display_surface_materialization_cases.cohort_flow_layout_materialization import *
from tests.display_surface_materialization_cases.contract_backed_registry_materialization import *
