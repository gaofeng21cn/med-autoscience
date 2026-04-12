from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from med_autoscience import display_registry


def _freeze_mapping(mapping: Mapping[str, tuple[str, ...]] | None) -> Mapping[str, tuple[str, ...]]:
    frozen = {str(key): tuple(value) for key, value in (mapping or {}).items()}
    return MappingProxyType(frozen)


@dataclass(frozen=True)
class DisplaySchemaClass:
    class_id: str
    display_name: str
    template_ids: tuple[str, ...]
    input_schema_ids: tuple[str, ...]


@dataclass(frozen=True)
class InputSchemaContract:
    input_schema_id: str
    display_kind: str
    display_name: str
    template_ids: tuple[str, ...]
    required_top_level_fields: tuple[str, ...]
    optional_top_level_fields: tuple[str, ...] = ()
    display_required_fields: tuple[str, ...] = ()
    display_optional_fields: tuple[str, ...] = ()
    collection_required_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    collection_optional_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    nested_collection_required_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    nested_collection_optional_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    additional_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "collection_required_fields", _freeze_mapping(self.collection_required_fields))
        object.__setattr__(self, "collection_optional_fields", _freeze_mapping(self.collection_optional_fields))
        object.__setattr__(
            self,
            "nested_collection_required_fields",
            _freeze_mapping(self.nested_collection_required_fields),
        )
        object.__setattr__(
            self,
            "nested_collection_optional_fields",
            _freeze_mapping(self.nested_collection_optional_fields),
        )


def _template_ids_for_evidence_class(evidence_class: str) -> tuple[str, ...]:
    return tuple(
        spec.template_id
        for spec in display_registry.list_evidence_figure_specs()
        if spec.evidence_class == evidence_class
    )


def _template_ids_for_input_schema(input_schema_id: str) -> tuple[str, ...]:
    evidence_template_ids = tuple(
        spec.template_id
        for spec in display_registry.list_evidence_figure_specs()
        if spec.input_schema_id == input_schema_id
    )
    illustration_shell_ids = tuple(
        spec.shell_id
        for spec in display_registry.list_illustration_shell_specs()
        if spec.input_schema_id == input_schema_id
    )
    table_shell_ids = tuple(
        spec.shell_id
        for spec in display_registry.list_table_shell_specs()
        if spec.input_schema_id == input_schema_id
    )
    return evidence_template_ids + illustration_shell_ids + table_shell_ids


_DISPLAY_SCHEMA_CLASSES: tuple[DisplaySchemaClass, ...] = (
    DisplaySchemaClass(
        class_id="prediction_performance",
        display_name="Prediction Performance",
        template_ids=_template_ids_for_evidence_class("prediction_performance"),
        input_schema_ids=("binary_prediction_curve_inputs_v1",),
    ),
    DisplaySchemaClass(
        class_id="clinical_utility",
        display_name="Clinical Utility",
        template_ids=_template_ids_for_evidence_class("clinical_utility"),
        input_schema_ids=(
            "binary_prediction_curve_inputs_v1",
            "time_to_event_decision_curve_inputs_v1",
            "time_to_event_threshold_governance_inputs_v1",
            "binary_calibration_decision_curve_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="time_to_event",
        display_name="Time-to-Event",
        template_ids=_template_ids_for_evidence_class("time_to_event"),
        input_schema_ids=(
            "binary_prediction_curve_inputs_v1",
            "risk_layering_monotonic_inputs_v1",
            "time_dependent_roc_comparison_inputs_v1",
            "time_to_event_landmark_performance_inputs_v1",
            "time_to_event_multihorizon_calibration_inputs_v1",
            "time_to_event_grouped_inputs_v1",
            "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "time_to_event_discrimination_calibration_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="data_geometry",
        display_name="Data Geometry",
        template_ids=_template_ids_for_evidence_class("data_geometry"),
        input_schema_ids=(
            "embedding_grouped_inputs_v1",
            "celltype_signature_heatmap_inputs_v1",
            "single_cell_atlas_overview_inputs_v1",
            "spatial_niche_map_inputs_v1",
            "trajectory_progression_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="matrix_pattern",
        display_name="Matrix Pattern",
        template_ids=_template_ids_for_evidence_class("matrix_pattern"),
        input_schema_ids=(
            "heatmap_group_comparison_inputs_v1",
            "performance_heatmap_inputs_v1",
            "correlation_heatmap_inputs_v1",
            "clustered_heatmap_inputs_v1",
            "gsva_ssgsea_heatmap_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="effect_estimate",
        display_name="Effect Estimate",
        template_ids=_template_ids_for_evidence_class("effect_estimate"),
        input_schema_ids=("forest_effect_inputs_v1",),
    ),
    DisplaySchemaClass(
        class_id="model_explanation",
        display_name="Model Explanation",
        template_ids=_template_ids_for_evidence_class("model_explanation"),
        input_schema_ids=(
            "shap_summary_inputs_v1",
            "shap_bar_importance_inputs_v1",
            "shap_dependence_panel_inputs_v1",
            "shap_waterfall_local_explanation_panel_inputs_v1",
            "shap_force_like_summary_panel_inputs_v1",
            "partial_dependence_ice_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="model_audit",
        display_name="Model Audit",
        template_ids=_template_ids_for_evidence_class("model_audit"),
        input_schema_ids=("model_complexity_audit_panel_inputs_v1",),
    ),
    DisplaySchemaClass(
        class_id="generalizability",
        display_name="Generalizability",
        template_ids=_template_ids_for_evidence_class("generalizability"),
        input_schema_ids=(
            "multicenter_generalizability_inputs_v1",
            "generalizability_subgroup_composite_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="publication_shells_and_tables",
        display_name="Publication Shells and Tables",
        template_ids=tuple(
            [item.shell_id for item in display_registry.list_illustration_shell_specs()]
            + [item.shell_id for item in display_registry.list_table_shell_specs()]
        ),
        input_schema_ids=(
            "cohort_flow_shell_inputs_v1",
            "submission_graphical_abstract_inputs_v1",
            "baseline_characteristics_schema_v1",
            "time_to_event_performance_summary_v1",
            "clinical_interpretation_summary_v1",
            "performance_summary_table_generic_v1",
            "grouped_risk_event_summary_table_v1",
        ),
    ),
)


_INPUT_SCHEMA_CONTRACTS: tuple[InputSchemaContract, ...] = (
    InputSchemaContract(
        input_schema_id="binary_prediction_curve_inputs_v1",
        display_kind="evidence_figure",
        display_name="Binary Prediction Curves",
        template_ids=_template_ids_for_input_schema("binary_prediction_curve_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label", "series"),
        display_optional_fields=("paper_role", "reference_line", "time_horizon_months"),
        collection_required_fields={"series": ("label", "x", "y")},
        collection_optional_fields={"series": ("annotation",), "reference_line": ("label",)},
        nested_collection_required_fields={"reference_line": ("x", "y")},
        additional_constraints=(
            "series_must_be_non_empty",
            "series_x_y_lengths_must_match",
            "series_values_must_be_finite",
            "reference_line_x_y_lengths_must_match_when_present",
            "time_dependent_roc_horizon_requires_positive_time_horizon_months_when_selected",
        ),
    ),
    InputSchemaContract(
        input_schema_id="risk_layering_monotonic_inputs_v1",
        display_kind="evidence_figure",
        display_name="Monotonic Risk Layering Bars",
        template_ids=_template_ids_for_input_schema("risk_layering_monotonic_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "y_label",
            "left_panel_title",
            "left_x_label",
            "left_bars",
            "right_panel_title",
            "right_x_label",
            "right_bars",
        ),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "left_bars": ("label", "cases", "events", "risk"),
            "right_bars": ("label", "cases", "events", "risk"),
        },
        additional_constraints=(
            "left_bars_must_be_non_empty",
            "right_bars_must_be_non_empty",
            "bar_cases_must_be_positive",
            "bar_events_must_not_exceed_cases",
            "bar_risk_must_be_finite_probability",
            "bar_risk_must_match_events_over_cases",
            "left_bars_risk_must_be_monotonic_non_decreasing",
            "right_bars_risk_must_be_monotonic_non_decreasing",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_dependent_roc_comparison_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-Dependent ROC Comparison Panel",
        template_ids=_template_ids_for_input_schema("time_dependent_roc_comparison_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label", "panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "panels": ("panel_id", "panel_label", "title", "analysis_window_label", "series"),
        },
        collection_optional_fields={
            "panels": ("annotation", "time_horizon_months", "reference_line"),
        },
        nested_collection_required_fields={
            "panels.series": ("label", "x", "y"),
            "panels.reference_line": ("x", "y"),
        },
        nested_collection_optional_fields={
            "panels.reference_line": ("label",),
        },
        additional_constraints=(
            "time_dependent_roc_comparison_panels_must_be_non_empty",
            "panel_ids_must_be_unique",
            "panel_labels_must_be_unique",
            "panel_analysis_window_labels_must_be_non_empty",
            "panel_series_must_be_non_empty",
            "panel_series_labels_must_be_unique_within_panel",
            "panel_series_label_sets_must_match_across_panels",
            "panel_series_x_y_lengths_must_match",
            "panel_series_values_must_be_finite",
            "panel_reference_line_x_y_lengths_must_match_when_present",
            "panel_time_horizon_months_must_be_positive_when_present",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_landmark_performance_inputs_v1",
        display_kind="evidence_figure",
        display_name="Landmark Performance Summary Panel (Time-to-Event)",
        template_ids=_template_ids_for_input_schema("time_to_event_landmark_performance_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "discrimination_panel_title",
            "discrimination_x_label",
            "error_panel_title",
            "error_x_label",
            "calibration_panel_title",
            "calibration_x_label",
            "landmark_summaries",
        ),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "landmark_summaries": (
                "window_label",
                "analysis_window_label",
                "landmark_months",
                "prediction_months",
                "c_index",
                "brier_score",
                "calibration_slope",
            )
        },
        collection_optional_fields={"landmark_summaries": ("annotation",)},
        additional_constraints=(
            "landmark_summaries_must_be_non_empty",
            "window_labels_must_be_unique",
            "analysis_window_labels_must_be_unique",
            "landmark_months_must_be_positive",
            "prediction_months_must_be_positive",
            "prediction_months_must_exceed_landmark_months",
            "c_index_values_must_be_finite_probability",
            "brier_score_values_must_be_finite_probability",
            "calibration_slope_values_must_be_finite",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_multihorizon_calibration_inputs_v1",
        display_kind="evidence_figure",
        display_name="Multi-Horizon Grouped Calibration Panel (Time-to-Event)",
        template_ids=_template_ids_for_input_schema("time_to_event_multihorizon_calibration_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "panels": ("panel_id", "panel_label", "title", "time_horizon_months", "calibration_summary"),
        },
        nested_collection_required_fields={
            "panels.calibration_summary": ("group_label", "group_order", "n", "events", "predicted_risk", "observed_risk"),
        },
        additional_constraints=(
            "multihorizon_calibration_panels_must_be_non_empty",
            "panel_ids_must_be_unique",
            "panel_labels_must_be_unique",
            "panel_time_horizon_months_must_be_positive",
            "panel_time_horizon_months_must_be_strictly_increasing",
            "panel_calibration_summary_must_be_non_empty",
            "panel_group_order_must_be_strictly_increasing",
            "panel_group_risks_must_be_finite_probability",
            "panel_group_events_must_not_exceed_group_size",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_threshold_governance_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Threshold Governance Panel",
        template_ids=_template_ids_for_input_schema("time_to_event_threshold_governance_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "threshold_panel_title",
            "calibration_panel_title",
            "calibration_x_label",
            "threshold_summaries",
            "risk_group_summaries",
        ),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "threshold_summaries": (
                "threshold_label",
                "threshold",
                "sensitivity",
                "specificity",
                "net_benefit",
            ),
            "risk_group_summaries": (
                "group_label",
                "group_order",
                "n",
                "events",
                "predicted_risk",
                "observed_risk",
            ),
        },
        additional_constraints=(
            "threshold_summaries_must_be_non_empty",
            "threshold_labels_must_be_unique",
            "threshold_values_must_be_strictly_increasing_probability",
            "threshold_metrics_must_be_finite",
            "risk_group_summaries_must_be_non_empty",
            "risk_group_order_must_be_strictly_increasing",
            "risk_group_risks_must_be_finite_probability",
            "risk_group_events_must_not_exceed_group_size",
        ),
    ),
    InputSchemaContract(
        input_schema_id="binary_calibration_decision_curve_panel_inputs_v1",
        display_kind="evidence_figure",
        display_name="Binary Calibration and Decision Curve Panel",
        template_ids=_template_ids_for_input_schema("binary_calibration_decision_curve_panel_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "calibration_x_label",
            "calibration_y_label",
            "decision_x_label",
            "decision_y_label",
            "calibration_axis_window",
            "calibration_series",
            "decision_series",
            "decision_reference_lines",
            "decision_focus_window",
        ),
        display_optional_fields=("paper_role", "calibration_reference_line"),
        collection_required_fields={
            "calibration_series": ("label", "x", "y"),
            "decision_series": ("label", "x", "y"),
            "decision_reference_lines": ("label", "x", "y"),
        },
        collection_optional_fields={"calibration_reference_line": ("label",)},
        nested_collection_required_fields={
            "calibration_reference_line": ("x", "y"),
            "calibration_axis_window": ("xmin", "xmax", "ymin", "ymax"),
            "decision_focus_window": ("xmin", "xmax"),
        },
        additional_constraints=(
            "calibration_series_must_be_non_empty",
            "calibration_series_x_y_lengths_must_match",
            "decision_series_must_be_non_empty",
            "decision_series_x_y_lengths_must_match",
            "decision_reference_lines_must_be_non_empty",
            "decision_reference_lines_x_y_lengths_must_match",
            "calibration_axis_window_must_be_strictly_increasing",
            "decision_focus_window_must_be_strictly_increasing",
        ),
    ),
    InputSchemaContract(
        input_schema_id="model_complexity_audit_panel_inputs_v1",
        display_kind="evidence_figure",
        display_name="Model Complexity Audit Panel",
        template_ids=_template_ids_for_input_schema("model_complexity_audit_panel_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "metric_panels", "audit_panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "metric_panels": ("panel_id", "panel_label", "title", "x_label", "rows"),
            "audit_panels": ("panel_id", "panel_label", "title", "x_label", "rows"),
        },
        collection_optional_fields={
            "metric_panels": ("reference_value",),
            "audit_panels": ("reference_value",),
        },
        nested_collection_required_fields={
            "metric_panels.rows": ("label", "value"),
            "audit_panels.rows": ("label", "value"),
        },
        additional_constraints=(
            "metric_panels_must_be_non_empty",
            "audit_panels_must_be_non_empty",
            "panel_row_values_must_be_finite",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_grouped_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Grouped Curves",
        template_ids=_template_ids_for_input_schema("time_to_event_grouped_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label"),
        display_optional_fields=("paper_role", "annotation", "groups", "panel_a_title", "panel_b_title", "event_count_y_label"),
        collection_required_fields={"groups": ("label", "times", "values")},
        collection_optional_fields={
            "risk_group_summaries": (
                "label",
                "sample_size",
                "events_5y",
                "mean_predicted_risk_5y",
                "observed_km_risk_5y",
            )
        },
        additional_constraints=(
            "kaplan_meier_grouped_and_cumulative_incidence_grouped_require_non_empty_groups",
            "group_times_values_lengths_must_match_when_groups_present",
            "group_values_must_be_finite_when_groups_present",
            "time_to_event_risk_group_summary_requires_non_empty_risk_group_summaries_when_selected",
            "risk_group_summary_events_must_not_exceed_sample_size",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_stratified_cumulative_incidence_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Stratified Cumulative Incidence Panel",
        template_ids=_template_ids_for_input_schema("time_to_event_stratified_cumulative_incidence_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label", "panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "panels": ("panel_id", "panel_label", "title", "groups"),
        },
        collection_optional_fields={
            "panels": ("annotation",),
        },
        nested_collection_required_fields={
            "panels.groups": ("label", "times", "values"),
        },
        additional_constraints=(
            "stratified_cumulative_incidence_panels_must_be_non_empty",
            "panel_ids_must_be_unique",
            "panel_labels_must_be_unique",
            "panel_group_labels_must_be_unique_within_panel",
            "panel_group_times_values_lengths_must_match",
            "panel_group_times_must_be_strictly_increasing",
            "panel_group_values_must_be_finite_probability",
            "panel_group_values_must_be_monotonic_non_decreasing",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_discrimination_calibration_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Discrimination and Calibration Panel",
        template_ids=_template_ids_for_input_schema("time_to_event_discrimination_calibration_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "panel_a_title",
            "panel_b_title",
            "discrimination_x_label",
            "calibration_x_label",
            "calibration_y_label",
            "discrimination_points",
            "calibration_summary",
        ),
        display_optional_fields=("paper_role", "calibration_callout"),
        collection_required_fields={
            "discrimination_points": ("label", "c_index"),
            "calibration_summary": (
                "group_label",
                "group_order",
                "n",
                "events_5y",
                "predicted_risk_5y",
                "observed_risk_5y",
            ),
        },
        collection_optional_fields={
            "discrimination_points": ("annotation",),
        },
        nested_collection_required_fields={"calibration_callout": ("group_label", "predicted_risk_5y", "observed_risk_5y")},
        nested_collection_optional_fields={"calibration_callout": ("events_5y", "n")},
        additional_constraints=(
            "discrimination_points_must_be_non_empty",
            "discrimination_points_must_be_finite_c_index",
            "calibration_summary_must_be_non_empty",
            "calibration_group_order_must_be_strictly_increasing",
            "calibration_summary_risks_must_be_finite_probability",
            "calibration_summary_events_must_not_exceed_group_size",
            "calibration_callout_must_reference_group_label_when_present",
            "calibration_callout_must_match_referenced_group_when_present",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_decision_curve_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Decision Curves",
        template_ids=_template_ids_for_input_schema("time_to_event_decision_curve_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "panel_a_title",
            "panel_b_title",
            "x_label",
            "y_label",
            "treated_fraction_y_label",
            "series",
            "treated_fraction_series",
        ),
        display_optional_fields=("paper_role", "reference_line", "time_horizon_months"),
        collection_required_fields={
            "series": ("label", "x", "y"),
            "treated_fraction_series": ("label", "x", "y"),
        },
        collection_optional_fields={"series": ("annotation",), "reference_line": ("label",)},
        nested_collection_required_fields={"reference_line": ("x", "y")},
        additional_constraints=(
            "series_must_be_non_empty",
            "series_x_y_lengths_must_match",
            "series_values_must_be_finite",
            "reference_line_x_y_lengths_must_match_when_present",
            "treated_fraction_series_x_y_lengths_must_match",
            "treated_fraction_values_must_be_finite",
            "publication_style_profile_required_at_materialization",
            "display_override_contract_may_adjust_layout_without_changing_data",
            "time_horizon_months_must_be_positive_when_declared",
        ),
    ),
    InputSchemaContract(
        input_schema_id="embedding_grouped_inputs_v1",
        display_kind="evidence_figure",
        display_name="Grouped Embedding Scatter",
        template_ids=_template_ids_for_input_schema("embedding_grouped_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label", "points"),
        display_optional_fields=("paper_role",),
        collection_required_fields={"points": ("x", "y", "group")},
        additional_constraints=(
            "points_must_be_non_empty",
            "point_coordinates_must_be_finite",
            "point_group_must_be_non_empty",
        ),
    ),
    InputSchemaContract(
        input_schema_id="celltype_signature_heatmap_inputs_v1",
        display_kind="evidence_figure",
        display_name="Cell-Type Embedding and Signature Heatmap",
        template_ids=_template_ids_for_input_schema("celltype_signature_heatmap_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "embedding_panel_title",
            "embedding_x_label",
            "embedding_y_label",
            "embedding_points",
            "heatmap_panel_title",
            "heatmap_x_label",
            "heatmap_y_label",
            "score_method",
            "row_order",
            "column_order",
            "cells",
        ),
        display_optional_fields=("paper_role", "embedding_annotation", "heatmap_annotation"),
        collection_required_fields={
            "embedding_points": ("x", "y", "group"),
            "row_order": ("label",),
            "column_order": ("label",),
            "cells": ("x", "y", "value"),
        },
        additional_constraints=(
            "embedding_points_must_be_non_empty",
            "embedding_point_coordinates_must_be_finite",
            "embedding_point_group_must_be_non_empty",
            "score_method_must_be_non_empty",
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
            "row_order_labels_must_be_unique",
            "column_order_labels_must_be_unique",
            "declared_row_labels_must_match_cell_rows",
            "declared_column_labels_must_match_cell_columns",
            "declared_column_labels_must_match_embedding_groups",
            "declared_heatmap_grid_must_be_complete_and_unique",
        ),
    ),
    InputSchemaContract(
        input_schema_id="single_cell_atlas_overview_inputs_v1",
        display_kind="evidence_figure",
        display_name="Single-Cell Atlas Overview Panel",
        template_ids=_template_ids_for_input_schema("single_cell_atlas_overview_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "embedding_panel_title",
            "embedding_x_label",
            "embedding_y_label",
            "embedding_points",
            "composition_panel_title",
            "composition_x_label",
            "composition_y_label",
            "composition_groups",
            "heatmap_panel_title",
            "heatmap_x_label",
            "heatmap_y_label",
            "score_method",
            "row_order",
            "column_order",
            "cells",
        ),
        display_optional_fields=("paper_role", "embedding_annotation", "composition_annotation", "heatmap_annotation"),
        collection_required_fields={
            "embedding_points": ("x", "y", "state_label"),
            "composition_groups": ("group_label", "group_order", "state_proportions"),
            "row_order": ("label",),
            "column_order": ("label",),
            "cells": ("x", "y", "value"),
        },
        collection_optional_fields={"embedding_points": ("group_label",)},
        nested_collection_required_fields={
            "composition_groups.state_proportions": ("state_label", "proportion"),
        },
        additional_constraints=(
            "embedding_points_must_be_non_empty",
            "embedding_point_coordinates_must_be_finite",
            "embedding_point_state_label_must_be_non_empty",
            "composition_groups_must_be_non_empty",
            "composition_group_labels_must_be_unique",
            "composition_group_order_must_be_strictly_increasing",
            "composition_group_state_proportions_must_be_non_empty",
            "composition_group_state_labels_must_match_declared_columns",
            "composition_group_proportions_must_be_finite_probability",
            "composition_group_proportions_must_sum_to_one",
            "score_method_must_be_non_empty",
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
            "row_order_labels_must_be_unique",
            "column_order_labels_must_be_unique",
            "declared_row_labels_must_match_cell_rows",
            "declared_column_labels_must_match_cell_columns",
            "declared_column_labels_must_match_embedding_states",
            "declared_heatmap_grid_must_be_complete_and_unique",
        ),
    ),
    InputSchemaContract(
        input_schema_id="spatial_niche_map_inputs_v1",
        display_kind="evidence_figure",
        display_name="Spatial Niche Map Panel",
        template_ids=_template_ids_for_input_schema("spatial_niche_map_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "spatial_panel_title",
            "spatial_x_label",
            "spatial_y_label",
            "spatial_points",
            "composition_panel_title",
            "composition_x_label",
            "composition_y_label",
            "composition_groups",
            "heatmap_panel_title",
            "heatmap_x_label",
            "heatmap_y_label",
            "score_method",
            "row_order",
            "column_order",
            "cells",
        ),
        display_optional_fields=("paper_role", "spatial_annotation", "composition_annotation", "heatmap_annotation"),
        collection_required_fields={
            "spatial_points": ("x", "y", "niche_label"),
            "composition_groups": ("group_label", "group_order", "niche_proportions"),
            "row_order": ("label",),
            "column_order": ("label",),
            "cells": ("x", "y", "value"),
        },
        collection_optional_fields={"spatial_points": ("region_label",)},
        nested_collection_required_fields={
            "composition_groups.niche_proportions": ("niche_label", "proportion"),
        },
        additional_constraints=(
            "spatial_points_must_be_non_empty",
            "spatial_point_coordinates_must_be_finite",
            "spatial_point_niche_label_must_be_non_empty",
            "composition_groups_must_be_non_empty",
            "composition_group_labels_must_be_unique",
            "composition_group_order_must_be_strictly_increasing",
            "composition_group_niche_proportions_must_be_non_empty",
            "composition_group_niche_labels_must_match_declared_columns",
            "composition_group_proportions_must_be_finite_probability",
            "composition_group_proportions_must_sum_to_one",
            "score_method_must_be_non_empty",
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
            "row_order_labels_must_be_unique",
            "column_order_labels_must_be_unique",
            "declared_row_labels_must_match_cell_rows",
            "declared_column_labels_must_match_cell_columns",
            "declared_column_labels_must_match_spatial_niches",
            "declared_heatmap_grid_must_be_complete_and_unique",
        ),
    ),
    InputSchemaContract(
        input_schema_id="trajectory_progression_inputs_v1",
        display_kind="evidence_figure",
        display_name="Trajectory Progression Panel",
        template_ids=_template_ids_for_input_schema("trajectory_progression_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "trajectory_panel_title",
            "trajectory_x_label",
            "trajectory_y_label",
            "trajectory_points",
            "composition_panel_title",
            "composition_x_label",
            "composition_y_label",
            "branch_order",
            "progression_bins",
            "heatmap_panel_title",
            "heatmap_x_label",
            "heatmap_y_label",
            "score_method",
            "row_order",
            "column_order",
            "cells",
        ),
        display_optional_fields=("paper_role", "trajectory_annotation", "composition_annotation", "heatmap_annotation"),
        collection_required_fields={
            "trajectory_points": ("x", "y", "branch_label", "state_label", "pseudotime"),
            "branch_order": ("label",),
            "progression_bins": ("bin_label", "bin_order", "pseudotime_start", "pseudotime_end", "branch_weights"),
            "row_order": ("label",),
            "column_order": ("label",),
            "cells": ("x", "y", "value"),
        },
        nested_collection_required_fields={
            "progression_bins.branch_weights": ("branch_label", "proportion"),
        },
        additional_constraints=(
            "trajectory_points_must_be_non_empty",
            "trajectory_point_coordinates_must_be_finite",
            "trajectory_point_branch_label_must_be_non_empty",
            "trajectory_point_state_label_must_be_non_empty",
            "trajectory_point_pseudotime_must_be_finite_probability",
            "branch_order_labels_must_be_unique",
            "branch_order_labels_must_match_trajectory_branches",
            "progression_bins_must_be_non_empty",
            "progression_bin_labels_must_be_unique",
            "progression_bin_order_must_be_strictly_increasing",
            "progression_bin_intervals_must_be_strictly_increasing",
            "progression_bin_branch_weights_must_be_non_empty",
            "progression_bin_branch_labels_must_match_declared_branch_order",
            "progression_bin_branch_weights_must_be_finite_probability",
            "progression_bin_branch_weights_must_sum_to_one",
            "score_method_must_be_non_empty",
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
            "row_order_labels_must_be_unique",
            "column_order_labels_must_be_unique",
            "declared_row_labels_must_match_cell_rows",
            "declared_column_labels_must_match_cell_columns",
            "declared_column_labels_must_match_progression_bins",
            "declared_heatmap_grid_must_be_complete_and_unique",
        ),
    ),
    InputSchemaContract(
        input_schema_id="heatmap_group_comparison_inputs_v1",
        display_kind="evidence_figure",
        display_name="Heatmap Group Comparison",
        template_ids=_template_ids_for_input_schema("heatmap_group_comparison_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label", "cells"),
        display_optional_fields=("paper_role",),
        collection_required_fields={"cells": ("x", "y", "value")},
        additional_constraints=(
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
        ),
    ),
    InputSchemaContract(
        input_schema_id="performance_heatmap_inputs_v1",
        display_kind="evidence_figure",
        display_name="Performance Heatmap",
        template_ids=_template_ids_for_input_schema("performance_heatmap_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "x_label",
            "y_label",
            "metric_name",
            "row_order",
            "column_order",
            "cells",
        ),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "row_order": ("label",),
            "column_order": ("label",),
            "cells": ("x", "y", "value"),
        },
        additional_constraints=(
            "metric_name_must_be_non_empty",
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
            "performance_values_must_be_finite_probability",
            "row_order_labels_must_be_unique",
            "column_order_labels_must_be_unique",
            "declared_row_labels_must_match_cell_rows",
            "declared_column_labels_must_match_cell_columns",
            "declared_heatmap_grid_must_be_complete_and_unique",
        ),
    ),
    InputSchemaContract(
        input_schema_id="correlation_heatmap_inputs_v1",
        display_kind="evidence_figure",
        display_name="Correlation Heatmap",
        template_ids=_template_ids_for_input_schema("correlation_heatmap_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label", "cells"),
        display_optional_fields=("paper_role",),
        collection_required_fields={"cells": ("x", "y", "value")},
        additional_constraints=(
            "matrix_must_be_square",
            "matrix_must_include_diagonal",
            "matrix_must_be_symmetric",
        ),
    ),
    InputSchemaContract(
        input_schema_id="clustered_heatmap_inputs_v1",
        display_kind="evidence_figure",
        display_name="Clustered Heatmap",
        template_ids=_template_ids_for_input_schema("clustered_heatmap_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "x_label",
            "y_label",
            "row_order",
            "column_order",
            "cells",
        ),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "row_order": ("label",),
            "column_order": ("label",),
            "cells": ("x", "y", "value"),
        },
        additional_constraints=(
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
            "row_order_labels_must_be_unique",
            "column_order_labels_must_be_unique",
            "declared_row_labels_must_match_cell_rows",
            "declared_column_labels_must_match_cell_columns",
            "declared_heatmap_grid_must_be_complete_and_unique",
        ),
    ),
    InputSchemaContract(
        input_schema_id="gsva_ssgsea_heatmap_inputs_v1",
        display_kind="evidence_figure",
        display_name="GSVA/ssGSEA Heatmap",
        template_ids=_template_ids_for_input_schema("gsva_ssgsea_heatmap_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "x_label",
            "y_label",
            "score_method",
            "row_order",
            "column_order",
            "cells",
        ),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "row_order": ("label",),
            "column_order": ("label",),
            "cells": ("x", "y", "value"),
        },
        additional_constraints=(
            "score_method_must_be_non_empty",
            "cells_must_be_non_empty",
            "cell_coordinates_must_be_non_empty",
            "cell_values_must_be_finite",
            "row_order_labels_must_be_unique",
            "column_order_labels_must_be_unique",
            "declared_row_labels_must_match_cell_rows",
            "declared_column_labels_must_match_cell_columns",
            "declared_heatmap_grid_must_be_complete_and_unique",
        ),
    ),
    InputSchemaContract(
        input_schema_id="forest_effect_inputs_v1",
        display_kind="evidence_figure",
        display_name="Forest Effect Plot",
        template_ids=_template_ids_for_input_schema("forest_effect_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "reference_value", "rows"),
        display_optional_fields=("paper_role",),
        collection_required_fields={"rows": ("label", "estimate", "lower", "upper")},
        additional_constraints=(
            "rows_must_be_non_empty",
            "effect_interval_must_bound_estimate",
            "effect_values_must_be_finite",
        ),
    ),
    InputSchemaContract(
        input_schema_id="shap_summary_inputs_v1",
        display_kind="evidence_figure",
        display_name="SHAP Summary Beeswarm",
        template_ids=_template_ids_for_input_schema("shap_summary_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "rows"),
        display_optional_fields=("paper_role",),
        collection_required_fields={"rows": ("feature", "points")},
        nested_collection_required_fields={"rows.points": ("shap_value", "feature_value")},
        additional_constraints=(
            "rows_must_be_non_empty",
            "row_feature_must_be_non_empty",
            "row_points_must_be_non_empty",
            "shap_values_must_be_finite",
            "feature_values_must_be_finite",
        ),
    ),
    InputSchemaContract(
        input_schema_id="shap_bar_importance_inputs_v1",
        display_kind="evidence_figure",
        display_name="SHAP Bar Importance Panel",
        template_ids=_template_ids_for_input_schema("shap_bar_importance_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "bars"),
        display_optional_fields=("paper_role",),
        collection_required_fields={"bars": ("rank", "feature", "importance_value")},
        additional_constraints=(
            "bars_must_be_non_empty",
            "bar_features_must_be_unique",
            "bar_ranks_must_be_strictly_increasing",
            "bar_importance_values_must_be_non_negative_finite",
            "bar_importance_values_must_be_sorted_descending_by_rank",
        ),
    ),
    InputSchemaContract(
        input_schema_id="shap_dependence_panel_inputs_v1",
        display_kind="evidence_figure",
        display_name="SHAP Dependence Panel",
        template_ids=_template_ids_for_input_schema("shap_dependence_panel_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "y_label", "colorbar_label", "panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "panels": ("panel_id", "panel_label", "title", "x_label", "feature", "interaction_feature", "points"),
        },
        nested_collection_required_fields={
            "panels.points": ("feature_value", "shap_value", "interaction_value"),
        },
        additional_constraints=(
            "panels_must_be_non_empty",
            "panel_ids_must_be_unique",
            "panel_labels_must_be_unique",
            "panel_features_must_be_unique",
            "panel_points_must_be_non_empty",
            "panel_point_values_must_be_finite",
        ),
    ),
    InputSchemaContract(
        input_schema_id="shap_waterfall_local_explanation_panel_inputs_v1",
        display_kind="evidence_figure",
        display_name="SHAP Waterfall Local Explanation Panel",
        template_ids=_template_ids_for_input_schema("shap_waterfall_local_explanation_panel_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "panels": ("panel_id", "panel_label", "title", "case_label", "baseline_value", "predicted_value", "contributions"),
        },
        nested_collection_required_fields={"panels.contributions": ("feature", "shap_value")},
        nested_collection_optional_fields={"panels.contributions": ("feature_value_text",)},
        additional_constraints=(
            "panels_must_be_non_empty",
            "panel_count_must_not_exceed_three",
            "panel_ids_must_be_unique",
            "panel_labels_must_be_unique",
            "panel_case_labels_must_be_unique",
            "panel_values_must_be_finite",
            "panel_contributions_must_be_non_empty",
            "panel_contribution_features_must_be_unique_within_panel",
            "panel_contribution_values_must_be_finite_and_non_zero",
            "panel_prediction_value_must_equal_baseline_plus_contributions",
        ),
    ),
    InputSchemaContract(
        input_schema_id="shap_force_like_summary_panel_inputs_v1",
        display_kind="evidence_figure",
        display_name="SHAP Force-like Summary Panel",
        template_ids=_template_ids_for_input_schema("shap_force_like_summary_panel_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "panels": ("panel_id", "panel_label", "title", "case_label", "baseline_value", "predicted_value", "contributions"),
        },
        nested_collection_required_fields={"panels.contributions": ("feature", "shap_value")},
        nested_collection_optional_fields={"panels.contributions": ("feature_value_text",)},
        additional_constraints=(
            "panels_must_be_non_empty",
            "panel_count_must_not_exceed_three",
            "panel_ids_must_be_unique",
            "panel_labels_must_be_unique",
            "panel_case_labels_must_be_unique",
            "panel_values_must_be_finite",
            "panel_contributions_must_be_non_empty",
            "panel_contribution_features_must_be_unique_within_panel",
            "panel_contribution_values_must_be_finite_and_non_zero",
            "panel_prediction_value_must_equal_baseline_plus_contributions",
            "panel_contributions_must_be_sorted_by_absolute_magnitude_descending",
        ),
    ),
    InputSchemaContract(
        input_schema_id="partial_dependence_ice_panel_inputs_v1",
        display_kind="evidence_figure",
        display_name="Partial Dependence and ICE Panel",
        template_ids=_template_ids_for_input_schema("partial_dependence_ice_panel_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "y_label", "panels"),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "panels": (
                "panel_id",
                "panel_label",
                "title",
                "x_label",
                "feature",
                "reference_value",
                "reference_label",
                "pdp_curve",
                "ice_curves",
            ),
        },
        nested_collection_required_fields={
            "panels.pdp_curve": ("x", "y"),
            "panels.ice_curves": ("curve_id", "x", "y"),
        },
        additional_constraints=(
            "panels_must_be_non_empty",
            "panel_count_must_not_exceed_three",
            "panel_ids_must_be_unique",
            "panel_labels_must_be_unique",
            "panel_features_must_be_unique",
            "panel_reference_labels_must_be_non_empty",
            "panel_reference_values_must_be_finite",
            "panel_pdp_curve_must_have_matching_x_y_lengths",
            "panel_pdp_curve_x_must_be_strictly_increasing",
            "panel_pdp_curve_values_must_be_finite",
            "panel_ice_curves_must_be_non_empty",
            "panel_ice_curve_ids_must_be_unique_within_panel",
            "ice_curve_x_y_lengths_must_match",
            "ice_curve_x_grids_must_match_pdp_curve_x",
            "ice_curve_values_must_be_finite",
            "panel_reference_values_must_fall_within_pdp_curve_range",
        ),
    ),
    InputSchemaContract(
        input_schema_id="multicenter_generalizability_inputs_v1",
        display_kind="evidence_figure",
        display_name="Multicenter Generalizability Overview",
        template_ids=_template_ids_for_input_schema("multicenter_generalizability_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "overview_mode",
            "center_event_y_label",
            "coverage_y_label",
            "center_event_counts",
            "coverage_panels",
        ),
        display_optional_fields=("paper_role",),
        collection_required_fields={
            "center_event_counts": ("center_label", "split_bucket", "event_count"),
            "coverage_panels": ("panel_id", "title", "layout_role", "bars"),
        },
        nested_collection_required_fields={"coverage_panels.bars": ("label", "count")},
        additional_constraints=(
            "overview_mode_must_be_center_support_counts",
            "center_event_counts_must_be_non_empty",
            "center_event_counts_labels_must_be_unique",
            "center_event_counts_must_be_non_negative",
            "coverage_panels_must_be_non_empty",
            "coverage_panel_ids_must_be_unique",
            "coverage_panel_layout_roles_must_cover_wide_left_top_right_bottom_right",
            "coverage_panel_bars_must_be_non_empty",
            "coverage_panel_bars_must_be_non_negative",
        ),
    ),
    InputSchemaContract(
        input_schema_id="generalizability_subgroup_composite_inputs_v1",
        display_kind="evidence_figure",
        display_name="Generalizability and Subgroup Composite Panel",
        template_ids=_template_ids_for_input_schema("generalizability_subgroup_composite_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "caption",
            "metric_family",
            "primary_label",
            "overview_panel_title",
            "overview_x_label",
            "overview_rows",
            "subgroup_panel_title",
            "subgroup_x_label",
            "subgroup_reference_value",
            "subgroup_rows",
        ),
        display_optional_fields=("paper_role", "comparator_label"),
        collection_required_fields={
            "overview_rows": ("cohort_id", "cohort_label", "support_count", "metric_value"),
            "subgroup_rows": ("subgroup_id", "subgroup_label", "estimate", "lower", "upper"),
        },
        collection_optional_fields={
            "overview_rows": ("comparator_metric_value", "event_count"),
            "subgroup_rows": ("group_n",),
        },
        additional_constraints=(
            "metric_family_must_be_supported",
            "primary_label_must_be_non_empty",
            "overview_rows_must_be_non_empty",
            "overview_cohort_ids_must_be_unique",
            "overview_cohort_labels_must_be_unique",
            "overview_support_counts_must_be_non_negative",
            "overview_event_counts_must_be_non_negative_when_present",
            "overview_metric_values_must_be_finite",
            "overview_comparator_metric_values_must_be_finite_when_present",
            "overview_comparator_metric_values_must_be_present_for_all_rows_when_comparator_label_is_declared",
            "overview_comparator_metric_values_must_be_absent_without_comparator_label",
            "subgroup_reference_value_must_be_finite",
            "subgroup_rows_must_be_non_empty",
            "subgroup_ids_must_be_unique",
            "subgroup_labels_must_be_unique",
            "subgroup_values_must_be_finite",
            "subgroup_group_n_must_be_non_negative_when_present",
            "subgroup_rows_must_satisfy_lower_le_estimate_le_upper",
        ),
    ),
    InputSchemaContract(
        input_schema_id="cohort_flow_shell_inputs_v1",
        display_kind="illustration_shell",
        display_name="Cohort Flow Figure",
        template_ids=_template_ids_for_input_schema("cohort_flow_shell_inputs_v1"),
        required_top_level_fields=("schema_version", "shell_id", "display_id", "title", "steps"),
        optional_top_level_fields=("caption", "exclusions", "endpoint_inventory", "design_panels"),
        collection_required_fields={
            "steps": ("step_id", "label", "n"),
            "exclusions": ("exclusion_id", "from_step_id", "label", "n"),
            "endpoint_inventory": ("endpoint_id", "label", "event_n"),
            "design_panels": ("panel_id", "title", "layout_role", "lines"),
        },
        collection_optional_fields={
            "steps": ("detail",),
            "exclusions": ("detail",),
            "endpoint_inventory": ("detail",),
        },
        nested_collection_required_fields={"design_panels.lines": ("label",)},
        nested_collection_optional_fields={"design_panels.lines": ("detail",)},
        additional_constraints=(
            "steps_must_be_non_empty",
            "step_ids_must_be_unique",
            "step_label_must_be_non_empty",
            "step_n_must_be_integer",
            "exclusions_from_step_ids_must_reference_steps",
            "exclusion_ids_must_be_unique",
            "exclusion_n_must_be_integer",
            "endpoint_inventory_ids_must_be_unique",
            "endpoint_inventory_event_n_must_be_integer",
            "design_panel_ids_must_be_unique",
            "design_panel_layout_roles_must_be_supported_and_unique",
            "design_panel_lines_must_be_non_empty",
        ),
    ),
    InputSchemaContract(
        input_schema_id="submission_graphical_abstract_inputs_v1",
        display_kind="illustration_shell",
        display_name="Submission Graphical Abstract",
        template_ids=_template_ids_for_input_schema("submission_graphical_abstract_inputs_v1"),
        required_top_level_fields=("schema_version", "shell_id", "display_id", "catalog_id", "title", "caption", "panels"),
        optional_top_level_fields=("paper_role", "footer_pills"),
        collection_required_fields={"panels": ("panel_id", "panel_label", "title", "subtitle", "rows")},
        collection_optional_fields={"footer_pills": ("pill_id", "label", "style_role")},
        nested_collection_required_fields={
            "panels.rows": ("cards",),
            "panels.rows.cards": ("card_id", "title", "value"),
        },
        nested_collection_optional_fields={
            "panels.rows.cards": ("detail", "accent_role"),
            "footer_pills": ("panel_id",),
        },
        additional_constraints=(
            "graphical_abstract_panels_must_be_non_empty",
            "graphical_abstract_panel_ids_must_be_unique",
            "graphical_abstract_rows_must_be_non_empty",
            "graphical_abstract_cards_must_be_non_empty",
            "graphical_abstract_footer_pills_must_reference_known_panels_when_present",
        ),
    ),
    InputSchemaContract(
        input_schema_id="baseline_characteristics_schema_v1",
        display_kind="table_shell",
        display_name="Baseline Characteristics Table",
        template_ids=_template_ids_for_input_schema("baseline_characteristics_schema_v1"),
        required_top_level_fields=("schema_version", "table_shell_id", "display_id", "title", "groups", "variables"),
        optional_top_level_fields=("caption",),
        collection_required_fields={
            "groups": ("group_id", "label"),
            "variables": ("variable_id", "label", "values"),
        },
        additional_constraints=(
            "groups_must_be_non_empty",
            "variables_must_be_non_empty",
            "variable_values_length_must_match_groups",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_performance_summary_v1",
        display_kind="table_shell",
        display_name="Time-to-Event Performance Summary Table",
        template_ids=_template_ids_for_input_schema("time_to_event_performance_summary_v1"),
        required_top_level_fields=("schema_version", "table_shell_id", "display_id", "title", "columns", "rows"),
        optional_top_level_fields=("caption",),
        collection_required_fields={
            "columns": ("column_id", "label"),
            "rows": ("row_id", "label", "values"),
        },
        additional_constraints=(
            "columns_must_be_non_empty",
            "rows_must_be_non_empty",
            "row_values_length_must_match_columns",
        ),
    ),
    InputSchemaContract(
        input_schema_id="clinical_interpretation_summary_v1",
        display_kind="table_shell",
        display_name="Clinical Interpretation Summary Table",
        template_ids=_template_ids_for_input_schema("clinical_interpretation_summary_v1"),
        required_top_level_fields=("schema_version", "table_shell_id", "display_id", "title", "columns", "rows"),
        optional_top_level_fields=("caption",),
        collection_required_fields={
            "columns": ("column_id", "label"),
            "rows": ("row_id", "label", "values"),
        },
        additional_constraints=(
            "columns_must_be_non_empty",
            "rows_must_be_non_empty",
            "row_values_length_must_match_columns",
        ),
    ),
    InputSchemaContract(
        input_schema_id="performance_summary_table_generic_v1",
        display_kind="table_shell",
        display_name="Performance Summary Table (Generic)",
        template_ids=_template_ids_for_input_schema("performance_summary_table_generic_v1"),
        required_top_level_fields=("schema_version", "table_shell_id", "display_id", "title", "row_header_label", "columns", "rows"),
        optional_top_level_fields=("caption",),
        collection_required_fields={
            "columns": ("column_id", "label"),
            "rows": ("row_id", "label", "values"),
        },
        additional_constraints=(
            "row_header_label_must_be_non_empty",
            "columns_must_be_non_empty",
            "rows_must_be_non_empty",
            "row_values_length_must_match_columns",
        ),
    ),
    InputSchemaContract(
        input_schema_id="grouped_risk_event_summary_table_v1",
        display_kind="table_shell",
        display_name="Grouped Risk Event Summary Table",
        template_ids=_template_ids_for_input_schema("grouped_risk_event_summary_table_v1"),
        required_top_level_fields=(
            "schema_version",
            "table_shell_id",
            "display_id",
            "title",
            "surface_column_label",
            "stratum_column_label",
            "cases_column_label",
            "events_column_label",
            "risk_column_label",
            "rows",
        ),
        optional_top_level_fields=("caption",),
        collection_required_fields={
            "rows": ("row_id", "surface", "stratum", "cases", "events", "risk_display"),
        },
        additional_constraints=(
            "surface_column_label_must_be_non_empty",
            "stratum_column_label_must_be_non_empty",
            "cases_column_label_must_be_non_empty",
            "events_column_label_must_be_non_empty",
            "risk_column_label_must_be_non_empty",
            "rows_must_be_non_empty",
            "row_surface_must_be_non_empty",
            "row_stratum_must_be_non_empty",
            "row_cases_must_be_positive_integer",
            "row_events_must_be_integer_between_zero_and_cases",
            "row_risk_display_must_match_events_over_cases_percent_1dp",
        ),
    ),
)

_INPUT_SCHEMA_CONTRACT_BY_ID = {item.input_schema_id: item for item in _INPUT_SCHEMA_CONTRACTS}


def _registered_template_ids() -> set[str]:
    return {
        *(item.template_id for item in display_registry.list_evidence_figure_specs()),
        *(item.shell_id for item in display_registry.list_illustration_shell_specs()),
        *(item.shell_id for item in display_registry.list_table_shell_specs()),
    }


def _validate_contract_registry_alignment() -> None:
    covered_template_ids = {
        template_id
        for schema in _INPUT_SCHEMA_CONTRACTS
        for template_id in schema.template_ids
    }
    covered_template_ids.update(
        template_id
        for display_class in _DISPLAY_SCHEMA_CLASSES
        for template_id in display_class.template_ids
    )
    missing_template_ids = _registered_template_ids() - covered_template_ids
    if missing_template_ids:
        missing = ", ".join(sorted(missing_template_ids))
        raise RuntimeError(f"display schema contract does not cover registered templates: {missing}")


def list_display_schema_classes() -> tuple[DisplaySchemaClass, ...]:
    return _DISPLAY_SCHEMA_CLASSES


def list_input_schema_contracts() -> tuple[InputSchemaContract, ...]:
    return _INPUT_SCHEMA_CONTRACTS


def get_input_schema_contract(input_schema_id: str) -> InputSchemaContract:
    normalized = str(input_schema_id or "").strip()
    try:
        return _INPUT_SCHEMA_CONTRACT_BY_ID[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown input schema contract `{input_schema_id}`") from exc


_validate_contract_registry_alignment()
