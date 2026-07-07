from __future__ import annotations

from .core import InputSchemaContract, _template_ids_for_input_schema

_INPUT_SCHEMA_CONTRACTS_DPCC_PRIMARY_CARE: tuple[InputSchemaContract, ...] = (
    InputSchemaContract(
        input_schema_id="dpcc_phenotype_gap_structure_v1",
        display_kind="evidence_figure",
        display_name="DPCC Phenotype Composition and Treatment-Gap Structure",
        template_ids=_template_ids_for_input_schema("dpcc_phenotype_gap_structure_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "rows"),
        display_optional_fields=(
            "paper_role",
            "caption",
            "composition_panel_title",
            "heatmap_panel_title",
            "heatmap_scale_label",
        ),
        collection_required_fields={
            "rows": (
                "phenotype_label",
                "share_of_index_patients",
                "severe_glycemia_low_intensity_gap_rate",
                "uncontrolled_glycemia_no_drug_gap_rate",
                "hypertension_no_antihypertensive_gap_rate",
                "dyslipidemia_no_lipid_lowering_gap_rate",
            ),
        },
        additional_constraints=(
            "purpose_first_layout_requires_composition_panel_and_gap_heatmap_panel",
            "share_of_index_patients_must_be_probability",
            "gap_rates_must_be_probability_or_null_when_gap_not_applicable",
            "figure_title_is_metadata_not_required_inside_rendered_plot",
        ),
    ),
    InputSchemaContract(
        input_schema_id="dpcc_transition_site_support_v1",
        display_kind="evidence_figure",
        display_name="DPCC Transition Stability and Site-Held-Out Support",
        template_ids=_template_ids_for_input_schema("dpcc_transition_site_support_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "transition_rows", "site_fold_rows"),
        display_optional_fields=(
            "paper_role",
            "caption",
            "transition_panel_title",
            "coverage_panel_title",
            "heatmap_scale_label",
            "visit_coverage",
            "eligible_site_count",
        ),
        collection_required_fields={
            "transition_rows": (
                "source_phenotype_label",
                "target_phenotype_label",
                "patient_count",
                "share_of_transition_patients",
            ),
            "site_fold_rows": ("fold_id", "index_patients", "share_of_index_patients"),
        },
        additional_constraints=(
            "purpose_first_layout_requires_transition_heatmap_panel_and_site_support_panel",
            "transition_patient_counts_must_be_non_negative",
            "transition_shares_must_be_probability",
            "site_support_shares_must_be_probability",
            "figure_title_is_metadata_not_required_inside_rendered_plot",
        ),
    ),
    InputSchemaContract(
        input_schema_id="dpcc_treatment_gap_alignment_v1",
        display_kind="evidence_figure",
        display_name="DPCC Guideline-Linked Treatment Gap Alignment",
        template_ids=_template_ids_for_input_schema("dpcc_treatment_gap_alignment_v1"),
        required_top_level_fields=("schema_version", "input_schema_id", "displays"),
        display_required_fields=("display_id", "template_id", "title", "rows"),
        display_optional_fields=("paper_role", "caption", "y_label", "annotation"),
        collection_required_fields={
            "rows": (
                "phenotype_label",
                "index_patients",
                "severe_glycemia_low_intensity_gap_patients",
                "uncontrolled_glycemia_no_drug_gap_patients",
                "hypertension_no_antihypertensive_gap_patients",
                "dyslipidemia_no_lipid_lowering_gap_patients",
            ),
        },
        additional_constraints=(
            "purpose_first_layout_requires_four_actual_gap_burden_panels",
            "gap_panels_must_show_patient_counts_not_decorative_axes",
            "gap_patient_counts_must_not_exceed_index_patients",
            "figure_title_is_metadata_not_required_inside_rendered_plot",
        ),
    ),
)
