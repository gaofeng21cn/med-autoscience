from __future__ import annotations

import importlib

import pytest

from med_autoscience import display_registry


CORE_PACK_ID = "fenggaolab.org.medical-display-core"


def _full_id(short_id: str) -> str:
    return f"{CORE_PACK_ID}::{short_id}"


RETIRED_PYTHON_EVIDENCE_TEMPLATES = (
    "phenotype_gap_structure_figure",
    "practical_factor_dot_figure",
    "preferred_class_sensitivity_figure",
    "single_cell_atlas_overview_panel",
    "atlas_spatial_bridge_panel",
    "spatial_niche_map_panel",
    "trajectory_progression_panel",
    "atlas_spatial_trajectory_storyboard_panel",
    "atlas_spatial_trajectory_density_coverage_panel",
    "atlas_spatial_trajectory_context_support_panel",
    "atlas_spatial_trajectory_multimanifold_context_support_panel",
    "site_held_out_stability_figure",
    "treatment_gap_alignment_figure",
    "treatment_shift_alignment_figure",
    "shap_grouped_local_explanation_panel",
    "shap_grouped_decision_path_panel",
    "shap_multigroup_decision_path_panel",
    "shap_signed_importance_panel",
    "partial_dependence_ice_panel",
    "partial_dependence_interaction_contour_panel",
    "partial_dependence_interaction_slice_panel",
    "partial_dependence_subgroup_comparison_panel",
    "accumulated_local_effects_panel",
    "feature_response_support_domain_panel",
    "shap_grouped_local_support_domain_panel",
    "shap_multigroup_decision_path_support_domain_panel",
    "shap_signed_importance_local_support_domain_panel",
    "multicenter_generalizability_overview",
    "center_transportability_governance_summary_panel",
    "baseline_missingness_qc_panel",
    "center_coverage_batch_transportability_panel",
    "transportability_recalibration_governance_panel",
)


RETIRED_PYTHON_EVIDENCE_SCHEMA_IDS = (
    "shap_grouped_local_explanation_panel_inputs_v1",
    "shap_grouped_decision_path_panel_inputs_v1",
    "shap_multigroup_decision_path_panel_inputs_v1",
    "shap_signed_importance_panel_inputs_v1",
    "partial_dependence_ice_panel_inputs_v1",
    "partial_dependence_interaction_contour_panel_inputs_v1",
    "partial_dependence_interaction_slice_panel_inputs_v1",
    "partial_dependence_subgroup_comparison_panel_inputs_v1",
    "accumulated_local_effects_panel_inputs_v1",
    "feature_response_support_domain_panel_inputs_v1",
    "shap_grouped_local_support_domain_panel_inputs_v1",
    "shap_multigroup_decision_path_support_domain_panel_inputs_v1",
    "shap_signed_importance_local_support_domain_panel_inputs_v1",
    "multicenter_generalizability_inputs_v1",
    "center_transportability_governance_summary_panel_inputs_v1",
    "baseline_missingness_qc_panel_inputs_v1",
    "center_coverage_batch_transportability_panel_inputs_v1",
    "transportability_recalibration_governance_panel_inputs_v1",
)


RETIRED_PYTHON_EVIDENCE_QC_PROFILES = (
    "publication_shap_grouped_local_explanation_panel",
    "publication_shap_grouped_decision_path_panel",
    "publication_shap_multigroup_decision_path_panel",
    "publication_shap_signed_importance_panel",
    "publication_partial_dependence_ice_panel",
    "publication_partial_dependence_interaction_contour_panel",
    "publication_partial_dependence_interaction_slice_panel",
    "publication_partial_dependence_subgroup_comparison_panel",
    "publication_accumulated_local_effects_panel",
    "publication_feature_response_support_domain_panel",
    "publication_shap_grouped_local_support_domain_panel",
    "publication_shap_multigroup_decision_path_support_domain_panel",
    "publication_shap_signed_importance_local_support_domain_panel",
    "publication_multicenter_overview",
    "publication_center_transportability_governance_summary_panel",
    "publication_baseline_missingness_qc_panel",
    "publication_center_coverage_batch_transportability_panel",
    "publication_transportability_recalibration_governance_panel",
)


@pytest.mark.parametrize("template_id", RETIRED_PYTHON_EVIDENCE_TEMPLATES)
def test_retired_python_evidence_templates_are_not_current_registry_entries(template_id: str) -> None:
    assert not display_registry.is_evidence_figure_template(template_id)
    assert not display_registry.is_illustration_shell(template_id)
    with pytest.raises(ValueError, match="unknown evidence figure template"):
        display_registry.get_evidence_figure_spec(_full_id(template_id))
    with pytest.raises(ValueError, match="unknown illustration shell"):
        display_registry.get_illustration_shell_spec(_full_id(template_id))


def test_retired_python_evidence_validators_are_not_current_materialization_validators() -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization.payload_loader")
    source_contract = importlib.import_module("med_autoscience.display_source_contract")

    assert not (set(RETIRED_PYTHON_EVIDENCE_SCHEMA_IDS) & set(module._VALIDATOR_BY_SCHEMA_ID))
    assert not (set(RETIRED_PYTHON_EVIDENCE_SCHEMA_IDS) & set(source_contract.INPUT_FILENAME_BY_SCHEMA_ID))


@pytest.mark.parametrize("qc_profile", RETIRED_PYTHON_EVIDENCE_QC_PROFILES)
def test_retired_python_evidence_qc_profiles_are_unsupported(qc_profile: str) -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    with pytest.raises(ValueError, match="unsupported qc_profile"):
        module.run_display_layout_qc(
            qc_profile=qc_profile,
            layout_sidecar={
                "template_id": "retired_python_evidence",
                "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
                "layout_boxes": [],
                "panel_boxes": [],
                "guide_boxes": [],
                "metrics": {},
            },
        )
