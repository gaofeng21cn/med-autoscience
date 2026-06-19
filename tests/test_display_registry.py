from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

from med_autoscience import display_registry


CORE_PACK_ID = "fenggaolab.org.medical-display-core"
REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "display-packs" / CORE_PACK_ID / "templates"


def _full_id(short_id: str) -> str:
    return f"{CORE_PACK_ID}::{short_id}"


def _template_manifests() -> dict[str, dict[str, object]]:
    manifests: dict[str, dict[str, object]] = {}
    for path in sorted(TEMPLATE_ROOT.glob("*/template.toml")):
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
        manifests[str(payload["template_id"])] = payload
    return manifests


def _ids_for_kind(kind: str) -> set[str]:
    return {
        _full_id(template_id)
        for template_id, payload in _template_manifests().items()
        if payload["kind"] == kind
    }


def test_registry_exposes_current_display_surface_inventory() -> None:
    evidence_specs = display_registry.list_evidence_figure_specs()
    illustration_specs = display_registry.list_illustration_shell_specs()
    table_specs = display_registry.list_table_shell_specs()

    assert {item.template_id for item in evidence_specs} == _ids_for_kind("evidence_figure")
    assert {item.shell_id for item in illustration_specs} == _ids_for_kind("illustration_shell")
    assert {item.shell_id for item in table_specs} == _ids_for_kind("table_shell")
    assert len(evidence_specs) == 55
    assert len(illustration_specs) == 4
    assert len(table_specs) == 7


def test_all_current_evidence_templates_are_r_ggplot2_subprocess() -> None:
    evidence_specs = display_registry.list_evidence_figure_specs()

    assert evidence_specs
    assert {item.renderer_family for item in evidence_specs} == {"r_ggplot2"}
    assert all(item.required_exports == ("png", "pdf") for item in evidence_specs)


def test_current_materialization_surface_excludes_retired_python_evidence_schema_and_qc_profiles() -> None:
    from med_autoscience.controllers.display_surface_materialization.payload_loader import _VALIDATOR_BY_SCHEMA_ID
    from med_autoscience.display_layout_qc.router import QC_PROFILE_RUNNERS

    current_schema_ids = {
        item.input_schema_id
        for item in display_registry.list_evidence_figure_specs()
    }
    current_qc_profiles = {
        item.layout_qc_profile
        for item in display_registry.list_evidence_figure_specs()
    }
    current_qc_profiles.update(
        item.shell_qc_profile
        for item in display_registry.list_illustration_shell_specs()
    )
    current_qc_profiles.update(
        item.table_qc_profile
        for item in display_registry.list_table_shell_specs()
    )
    generic_output_profiles = {"publication_result_display", "publication_table_shell"}

    assert set(_VALIDATOR_BY_SCHEMA_ID) == current_schema_ids
    assert set(QC_PROFILE_RUNNERS) == current_qc_profiles | generic_output_profiles


@pytest.mark.parametrize(
    ("template_id", "expected_input_schema_id", "expected_qc_profile"),
    [
        ("roc_curve_binary", "binary_prediction_curve_inputs_v1", "publication_evidence_curve"),
        ("time_to_event_threshold_governance_panel", "time_to_event_threshold_governance_inputs_v1", "publication_time_to_event_threshold_governance_panel"),
        ("time_to_event_multihorizon_calibration_panel", "time_to_event_multihorizon_calibration_inputs_v1", "publication_time_to_event_multihorizon_calibration_panel"),
        ("time_to_event_landmark_performance_panel", "time_to_event_landmark_performance_inputs_v1", "publication_landmark_performance_panel"),
        ("celltype_signature_heatmap", "celltype_signature_heatmap_inputs_v1", "publication_celltype_signature_panel"),
        ("pathway_enrichment_dotplot_panel", "pathway_enrichment_dotplot_panel_inputs_v1", "publication_pathway_enrichment_dotplot_panel"),
        ("genomic_alteration_landscape_panel", "genomic_alteration_landscape_panel_inputs_v1", "publication_genomic_alteration_landscape_panel"),
        ("shap_summary_beeswarm", "shap_summary_inputs_v1", "publication_shap_summary"),
        ("shap_dependence_panel", "shap_dependence_panel_inputs_v1", "publication_shap_dependence_panel"),
        ("generalizability_subgroup_composite_panel", "generalizability_subgroup_composite_inputs_v1", "publication_generalizability_subgroup_composite_panel"),
        ("clinical_impact_curve_binary", "binary_prediction_curve_inputs_v1", "publication_evidence_curve"),
        ("risk_layering_monotonic_bars", "risk_layering_monotonic_inputs_v1", "publication_risk_layering_bars"),
    ],
)
def test_representative_evidence_templates_are_registered(
    template_id: str,
    expected_input_schema_id: str,
    expected_qc_profile: str,
) -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id(template_id))

    assert spec.template_id == _full_id(template_id)
    assert spec.renderer_family == "r_ggplot2"
    assert spec.input_schema_id == expected_input_schema_id
    assert spec.layout_qc_profile == expected_qc_profile


def test_local_architecture_overview_figure_alias_resolves_to_risk_layering_template() -> None:
    spec = display_registry.get_evidence_figure_spec("local_architecture_overview_figure")

    assert spec.template_id == _full_id("risk_layering_monotonic_bars")
    assert spec.input_schema_id == "risk_layering_monotonic_inputs_v1"
    assert display_registry.is_evidence_figure_template("local_architecture_overview_figure")


def test_retired_python_evidence_templates_are_not_registered() -> None:
    retired_template_ids = {
        "phenotype_gap_structure_figure",
        "single_cell_atlas_overview_panel",
        "atlas_spatial_bridge_panel",
        "spatial_niche_map_panel",
        "trajectory_progression_panel",
        "shap_grouped_local_explanation_panel",
        "shap_grouped_decision_path_panel",
        "shap_multigroup_decision_path_panel",
        "partial_dependence_ice_panel",
        "partial_dependence_interaction_contour_panel",
        "accumulated_local_effects_panel",
        "feature_response_support_domain_panel",
        "multicenter_generalizability_overview",
        "baseline_missingness_qc_panel",
        "center_coverage_batch_transportability_panel",
        "transportability_recalibration_governance_panel",
    }

    for template_id in retired_template_ids:
        assert not display_registry.is_evidence_figure_template(template_id)
        with pytest.raises(ValueError, match="unknown evidence figure template"):
            display_registry.get_evidence_figure_spec(_full_id(template_id))


@pytest.mark.parametrize(
    ("shell_id", "expected_input_schema_id", "expected_qc_profile"),
    [
        ("cohort_flow_figure", "cohort_flow_shell_inputs_v1", "publication_illustration_flow"),
        ("submission_graphical_abstract", "submission_graphical_abstract_inputs_v1", "submission_graphical_abstract"),
        ("workflow_fact_sheet_panel", "workflow_fact_sheet_panel_inputs_v1", "publication_workflow_fact_sheet_panel"),
        ("design_evidence_composite_shell", "design_evidence_composite_shell_inputs_v1", "publication_design_evidence_composite_shell"),
    ],
)
def test_illustration_shells_allow_python_composition(
    shell_id: str,
    expected_input_schema_id: str,
    expected_qc_profile: str,
) -> None:
    spec = display_registry.get_illustration_shell_spec(_full_id(shell_id))

    assert spec.shell_id == _full_id(shell_id)
    assert "H" in spec.paper_family_ids
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == expected_input_schema_id
    assert spec.shell_qc_profile == expected_qc_profile


@pytest.mark.parametrize(
    ("table_id", "expected_input_schema_id"),
    [
        ("table1_baseline_characteristics", "baseline_characteristics_schema_v1"),
        ("table2_time_to_event_performance_summary", "time_to_event_performance_summary_v1"),
        ("table3_clinical_interpretation_summary", "clinical_interpretation_summary_v1"),
        ("performance_summary_table_generic", "performance_summary_table_generic_v1"),
        ("grouped_risk_event_summary_table", "grouped_risk_event_summary_table_v1"),
    ],
)
def test_table_shells_are_registered(table_id: str, expected_input_schema_id: str) -> None:
    spec = display_registry.get_table_shell_spec(_full_id(table_id))

    assert spec.shell_id == _full_id(table_id)
    assert spec.input_schema_id == expected_input_schema_id
    assert spec.required_exports


def test_registry_exposes_pack_manifest_paper_proven_truth() -> None:
    evidence_spec = display_registry.get_evidence_figure_spec(_full_id("time_to_event_decision_curve"))
    shell_spec = display_registry.get_illustration_shell_spec(_full_id("submission_graphical_abstract"))
    table_spec = display_registry.get_table_shell_spec(_full_id("table2_time_to_event_performance_summary"))

    assert evidence_spec.paper_proven is True
    assert shell_spec.paper_proven is True
    assert table_spec.paper_proven is False


def test_resolve_display_registry_rejects_unknown_template() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    with pytest.raises(ValueError, match="unknown evidence figure template"):
        module.get_evidence_figure_spec("unknown_template")
