from __future__ import annotations

from .core import InputSchemaContract, _template_ids_for_input_schema


_INPUT_SCHEMA_CONTRACTS_STRATIFIED_DISPLAY: tuple[InputSchemaContract, ...] = (
    InputSchemaContract(
        input_schema_id="stratified_mismatch_matrix_inputs_v1",
        display_kind="evidence_figure",
        display_name="Stratified Group Composition and Mismatch Matrix",
        template_ids=_template_ids_for_input_schema("stratified_mismatch_matrix_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "metric_definitions",
            "rows",
        ),
        display_optional_fields=(
            "paper_role",
            "caption",
            "composition_panel_title",
            "composition_axis_label",
            "heatmap_panel_title",
            "heatmap_scale_label",
        ),
        collection_required_fields={
            "metric_definitions": ("metric_id", "metric_label"),
            "rows": ("group_label", "group_share", "metrics"),
        },
        nested_collection_required_fields={
            "rows.metrics": ("metric_id", "value"),
        },
        additional_constraints=(
            "metric_ids_must_be_unique",
            "each_row_must_supply_each_declared_metric_exactly_once",
            "group_share_must_be_probability",
            "mismatch_values_must_be_probability_or_null_when_not_applicable",
            "figure_title_is_metadata_not_required_inside_rendered_plot",
        ),
    ),
    InputSchemaContract(
        input_schema_id="transition_support_matrix_inputs_v1",
        display_kind="evidence_figure",
        display_name="State Transition and Held-Out Support Matrix",
        template_ids=_template_ids_for_input_schema("transition_support_matrix_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "transition_rows",
            "support_rows",
        ),
        display_optional_fields=(
            "paper_role",
            "caption",
            "transition_panel_title",
            "support_panel_title",
            "heatmap_scale_label",
            "source_axis_label",
            "target_axis_label",
            "support_axis_label",
        ),
        collection_required_fields={
            "transition_rows": (
                "source_group_label",
                "target_group_label",
                "unit_count",
                "transition_share",
            ),
            "support_rows": ("support_label", "unit_count", "support_share"),
        },
        additional_constraints=(
            "transition_and_support_counts_must_be_non_negative",
            "transition_and_support_shares_must_be_probability",
            "figure_title_is_metadata_not_required_inside_rendered_plot",
        ),
    ),
    InputSchemaContract(
        input_schema_id="stratified_mismatch_burden_inputs_v1",
        display_kind="evidence_figure",
        display_name="Stratified Indicator Mismatch Burden",
        template_ids=_template_ids_for_input_schema("stratified_mismatch_burden_inputs_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=(
            "display_id",
            "template_id",
            "title",
            "metric_definitions",
            "rows",
        ),
        display_optional_fields=("paper_role", "caption", "x_label", "y_label", "annotation"),
        collection_required_fields={
            "metric_definitions": ("metric_id", "metric_label"),
            "rows": ("group_label", "group_size", "metrics"),
        },
        nested_collection_required_fields={
            "rows.metrics": ("metric_id", "event_count", "denominator"),
        },
        nested_collection_optional_fields={
            "rows.metrics": ("rate",),
        },
        additional_constraints=(
            "one_to_four_metric_definitions_are_supported",
            "metric_ids_must_be_unique",
            "each_row_must_supply_each_declared_metric_exactly_once",
            "event_count_must_not_exceed_denominator",
            "denominator_must_not_exceed_group_size",
            "explicit_rate_must_equal_event_count_over_denominator_within_tolerance",
            "figure_title_is_metadata_not_required_inside_rendered_plot",
        ),
    ),
)
