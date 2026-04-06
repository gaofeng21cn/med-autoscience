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
    return tuple(
        spec.template_id
        for spec in display_registry.list_evidence_figure_specs()
        if spec.input_schema_id == input_schema_id
    )


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
            "time_to_event_grouped_inputs_v1",
            "time_to_event_discrimination_calibration_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="data_geometry",
        display_name="Data Geometry",
        template_ids=_template_ids_for_evidence_class("data_geometry"),
        input_schema_ids=("embedding_grouped_inputs_v1",),
    ),
    DisplaySchemaClass(
        class_id="matrix_pattern",
        display_name="Matrix Pattern",
        template_ids=_template_ids_for_evidence_class("matrix_pattern"),
        input_schema_ids=(
            "heatmap_group_comparison_inputs_v1",
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
        input_schema_ids=("shap_summary_inputs_v1",),
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
        input_schema_ids=("multicenter_generalizability_inputs_v1",),
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
        display_optional_fields=("paper_role", "reference_line"),
        collection_required_fields={"series": ("label", "x", "y")},
        collection_optional_fields={"series": ("annotation",), "reference_line": ("label",)},
        nested_collection_required_fields={"reference_line": ("x", "y")},
        additional_constraints=(
            "series_must_be_non_empty",
            "series_x_y_lengths_must_match",
            "series_values_must_be_finite",
            "reference_line_x_y_lengths_must_match_when_present",
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
        input_schema_id="binary_calibration_decision_curve_panel_inputs_v1",
        display_kind="evidence_figure",
        display_name="Binary Calibration and Decision Curve Panel",
        template_ids=("binary_calibration_decision_curve_panel",),
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
        template_ids=("model_complexity_audit_panel",),
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
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_discrimination_calibration_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Discrimination and Calibration Panel",
        template_ids=("time_to_event_discrimination_calibration_panel",),
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
            "calibration_callout_must_reference_group_label_when_present",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_decision_curve_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Decision Curves",
        template_ids=("time_to_event_decision_curve",),
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
        display_optional_fields=("paper_role", "reference_line"),
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
        input_schema_id="multicenter_generalizability_inputs_v1",
        display_kind="evidence_figure",
        display_name="Multicenter Generalizability Overview",
        template_ids=("multicenter_generalizability_overview",),
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
        input_schema_id="cohort_flow_shell_inputs_v1",
        display_kind="illustration_shell",
        display_name="Cohort Flow Figure",
        template_ids=("cohort_flow_figure",),
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
        template_ids=("submission_graphical_abstract",),
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
        template_ids=("table1_baseline_characteristics",),
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
        template_ids=("table2_time_to_event_performance_summary",),
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
        template_ids=("table3_clinical_interpretation_summary",),
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
        template_ids=("performance_summary_table_generic",),
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
        template_ids=("grouped_risk_event_summary_table",),
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
