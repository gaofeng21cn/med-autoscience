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


from tests.display_surface_materialization_cases.shared import (
    annotations,
    _shared_base,
    _registry_id_helpers,
    _workspace_surface_fixtures,
    _layout_sidecar_fixtures,
    _illustration_payload_fixtures,
    _current_evidence_payload_fixtures,
    importlib,
    json,
    Path,
    re,
    sys,
    Any,
    plt,
    pytest,
    display_registry,
    get_template_short_id,
    full_id,
    dump_json,
    extract_svg_font_size,
    write_default_publication_display_contracts,
    restrict_display_registry_to_display_ids,
    build_display_surface_workspace,
    minimal_current_layout_sidecar,
    minimal_tail_layout_sidecar,
    _center_transportability_governance_display,
    _current_evidence_input_envelopes,
    _make_generalizability_subgroup_composite_panel_display,
)
from tests.display_surface_materialization_cases.basic_displays_and_renderers import (
    test_materialize_display_surface_preserves_optional_table1_p_values,
    test_materialize_display_surface_generates_dpcc_compact_table_shells,
    test_materialize_display_surface_preserves_dpcc_current_markdown_tables_over_stale_payloads,
    test_materialize_display_surface_preserves_dpcc_medication_capture_t3,
    test_materialize_display_surface_hydrates_current_body_display_sources,
    test_materialize_display_surface_preserves_newer_target_sources_over_stale_current_body,
    test_materialize_display_surface_replaces_legacy_catalog_entries_with_matching_catalog_id,
    test_materialize_display_surface_materializes_catalog_only_cohort_flow_figure,
    test_materialize_display_surface_promotes_dpcc_figures_to_purpose_first_r_templates,
)
from tests.display_surface_materialization_cases.cohort_flow_layout_materialization import (
    test_display_layout_qc_rejects_v2_participant_flow_with_prose_context_cards,
    test_display_layout_qc_rejects_v2_participant_flow_with_truncated_step_detail,
    test_display_layout_qc_rejects_low_information_v2_participant_flow,
    test_materialize_display_surface_renders_cohort_flow_with_exclusions_and_design_panels,
    test_materialize_display_surface_renders_exclusion_aware_cohort_flow_shell,
    test_materialize_display_surface_preserves_current_generated_cohort_flow_over_stale_current_body,
    test_materialize_display_surface_accepts_legacy_full_right_sidecar_role,
    test_materialize_display_surface_keeps_design_summary_inputs_out_of_figure_canvas,
    test_materialize_display_surface_normalizes_dense_participant_flow_sidecar,
    test_materialize_display_surface_renders_source_layer_accounting_without_sequential_spine,
    test_visual_audit_blocks_legacy_cohort_flow_sidecar_without_scholarskills_v2_policy,
)
from tests.display_surface_materialization_cases.contract_backed_registry_materialization import (
    test_materialize_display_surface_restores_contract_backed_and_shell_mapped_figures,
    test_materialize_display_surface_rejects_invalid_contract_backed_layout_sidecar,
)
