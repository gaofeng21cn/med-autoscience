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
        input_schema_ids=("binary_prediction_curve_inputs_v1", "time_to_event_decision_curve_inputs_v1"),
    ),
    DisplaySchemaClass(
        class_id="time_to_event",
        display_name="Time-to-Event",
        template_ids=_template_ids_for_evidence_class("time_to_event"),
        input_schema_ids=(
            "binary_prediction_curve_inputs_v1",
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
            "baseline_characteristics_schema_v1",
            "time_to_event_performance_summary_v1",
            "clinical_interpretation_summary_v1",
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
        input_schema_id="time_to_event_grouped_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Grouped Curves",
        template_ids=_template_ids_for_input_schema("time_to_event_grouped_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "y_label", "groups"),
        display_optional_fields=("paper_role", "annotation"),
        collection_required_fields={"groups": ("label", "times", "values")},
        additional_constraints=(
            "groups_must_be_non_empty",
            "group_times_values_lengths_must_match",
            "group_values_must_be_finite",
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
            "discrimination_x_label",
            "discrimination_y_label",
            "calibration_x_label",
            "calibration_y_label",
            "discrimination_series",
            "calibration_groups",
        ),
        display_optional_fields=("paper_role", "discrimination_reference_line", "calibration_reference_line"),
        collection_required_fields={
            "discrimination_series": ("label", "x", "y"),
            "calibration_groups": ("label", "times", "values"),
        },
        collection_optional_fields={
            "discrimination_series": ("annotation",),
            "discrimination_reference_line": ("label",),
            "calibration_reference_line": ("label",),
        },
        nested_collection_required_fields={
            "discrimination_reference_line": ("x", "y"),
            "calibration_reference_line": ("x", "y"),
        },
        additional_constraints=(
            "discrimination_series_must_be_non_empty",
            "discrimination_series_x_y_lengths_must_match",
            "calibration_groups_must_be_non_empty",
            "calibration_group_times_values_lengths_must_match",
            "calibration_values_must_be_finite",
        ),
    ),
    InputSchemaContract(
        input_schema_id="time_to_event_decision_curve_inputs_v1",
        display_kind="evidence_figure",
        display_name="Time-to-Event Decision Curves",
        template_ids=("time_to_event_decision_curve",),
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
        display_required_fields=("display_id", "template_id", "title", "caption", "x_label", "centers"),
        display_optional_fields=("paper_role", "reference_line"),
        collection_required_fields={"centers": ("center_label", "sample_size", "estimate", "lower", "upper")},
        additional_constraints=(
            "centers_must_be_non_empty",
            "center_labels_must_be_unique",
            "sample_size_must_be_positive",
            "effect_interval_must_bound_estimate",
        ),
    ),
    InputSchemaContract(
        input_schema_id="cohort_flow_shell_inputs_v1",
        display_kind="illustration_shell",
        display_name="Cohort Flow Figure",
        template_ids=("cohort_flow_figure",),
        required_top_level_fields=("schema_version", "shell_id", "display_id", "title", "steps"),
        optional_top_level_fields=("caption",),
        collection_required_fields={"steps": ("step_id", "label", "n")},
        collection_optional_fields={"steps": ("detail",)},
        additional_constraints=(
            "steps_must_be_non_empty",
            "step_label_must_be_non_empty",
            "step_n_must_be_integer",
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
