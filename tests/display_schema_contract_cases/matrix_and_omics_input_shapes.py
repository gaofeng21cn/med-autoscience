from .shared import (
    annotations,
    _shared_base,
    _registry_id_helpers,
    _input_schema_fixtures,
    importlib,
    Path,
    _CORE_PACK_ID,
    _full_id,
    lru_cache,
    SimpleNamespace,
    _INPUT_SCHEMAS,
    _CLASS_IDS,
    _display_class_by_id,
    _load_schema_contract_fixture,
)

def test_schema_contract_tracks_matrix_and_omics_input_shapes() -> None:
    fx = _load_schema_contract_fixture()
    heatmap = fx.heatmap
    enrichment_dotplot = fx.enrichment_dotplot
    celltype_marker_dotplot = fx.celltype_marker_dotplot
    omics_volcano = fx.omics_volcano
    cnv_recurrence = fx.cnv_recurrence
    genomic_alteration_landscape = fx.genomic_alteration_landscape
    genomic_alteration_consequence = fx.genomic_alteration_consequence

    assert heatmap.template_ids == (_full_id("heatmap_group_comparison"),)
    assert heatmap.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "cells",
    )
    assert heatmap.collection_required_fields["cells"] == ("x", "y", "value")
    assert heatmap.additional_constraints == (
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
    )
    assert enrichment_dotplot.template_ids == (_full_id("pathway_enrichment_dotplot_panel"),)
    assert enrichment_dotplot.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "effect_scale_label",
        "size_scale_label",
        "panel_order",
        "pathway_order",
        "points",
    )
    assert enrichment_dotplot.display_optional_fields == ("paper_role",)
    assert enrichment_dotplot.collection_required_fields["panel_order"] == ("panel_id", "panel_title")
    assert enrichment_dotplot.collection_required_fields["pathway_order"] == ("label",)
    assert enrichment_dotplot.collection_required_fields["points"] == (
        "panel_id",
        "pathway_label",
        "x_value",
        "effect_value",
        "size_value",
    )
    assert enrichment_dotplot.additional_constraints == (
        "effect_scale_label_must_be_non_empty",
        "size_scale_label_must_be_non_empty",
        "panel_order_must_be_non_empty",
        "panel_order_count_must_be_at_most_two",
        "panel_ids_must_be_unique",
        "panel_titles_must_be_non_empty",
        "pathway_order_labels_must_be_unique",
        "points_must_be_non_empty",
        "point_panel_ids_must_match_declared_panels",
        "point_pathway_labels_must_match_declared_pathways",
        "point_x_values_must_be_finite",
        "point_effect_values_must_be_finite",
        "point_size_values_must_be_non_negative",
        "declared_panel_pathway_grid_must_be_complete_and_unique",
    )
    assert celltype_marker_dotplot.template_ids == (_full_id("celltype_marker_dotplot_panel"),)
    assert celltype_marker_dotplot.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "effect_scale_label",
        "size_scale_label",
        "panel_order",
        "celltype_order",
        "marker_order",
        "points",
    )
    assert celltype_marker_dotplot.display_optional_fields == ("paper_role",)
    assert celltype_marker_dotplot.collection_required_fields["panel_order"] == ("panel_id", "panel_title")
    assert celltype_marker_dotplot.collection_required_fields["celltype_order"] == ("label",)
    assert celltype_marker_dotplot.collection_required_fields["marker_order"] == ("label",)
    assert celltype_marker_dotplot.collection_required_fields["points"] == (
        "panel_id",
        "celltype_label",
        "marker_label",
        "effect_value",
        "size_value",
    )
    assert celltype_marker_dotplot.additional_constraints == (
        "effect_scale_label_must_be_non_empty",
        "size_scale_label_must_be_non_empty",
        "panel_order_must_be_non_empty",
        "panel_order_count_must_be_at_most_two",
        "panel_ids_must_be_unique",
        "panel_titles_must_be_non_empty",
        "celltype_order_labels_must_be_unique",
        "marker_order_labels_must_be_unique",
        "points_must_be_non_empty",
        "point_panel_ids_must_match_declared_panels",
        "point_celltype_labels_must_match_declared_celltypes",
        "point_marker_labels_must_match_declared_markers",
        "point_effect_values_must_be_finite",
        "point_size_values_must_be_non_negative",
        "declared_panel_celltype_marker_grid_must_be_complete_and_unique",
    )
    assert omics_volcano.template_ids == (_full_id("omics_volcano_panel"),)
    assert omics_volcano.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "legend_title",
        "effect_threshold",
        "significance_threshold",
        "panel_order",
        "points",
    )
    assert omics_volcano.display_optional_fields == ("paper_role",)
    assert omics_volcano.collection_required_fields["panel_order"] == ("panel_id", "panel_title")
    assert omics_volcano.collection_required_fields["points"] == (
        "panel_id",
        "feature_label",
        "effect_value",
        "significance_value",
        "regulation_class",
    )
    assert omics_volcano.collection_optional_fields["points"] == ("label_text",)
    assert omics_volcano.additional_constraints == (
        "legend_title_must_be_non_empty",
        "effect_threshold_must_be_positive",
        "significance_threshold_must_be_positive",
        "panel_order_must_be_non_empty",
        "panel_order_count_must_be_at_most_two",
        "panel_ids_must_be_unique",
        "panel_titles_must_be_non_empty",
        "points_must_be_non_empty",
        "point_panel_ids_must_match_declared_panels",
        "each_declared_panel_must_contain_points",
        "point_feature_labels_must_be_unique_within_panel",
        "point_effect_values_must_be_finite",
        "point_significance_values_must_be_non_negative",
        "point_regulation_classes_must_use_supported_vocabulary",
        "point_label_text_must_be_non_empty_when_present",
    )
    assert cnv_recurrence.template_ids == (_full_id("cnv_recurrence_summary_panel"),)
    assert cnv_recurrence.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "cnv_legend_title",
        "region_order",
        "sample_order",
        "annotation_tracks",
        "cnv_records",
    )
    assert cnv_recurrence.collection_required_fields == {
        "region_order": ("label",),
        "sample_order": ("sample_id",),
        "annotation_tracks": ("track_id", "track_label", "values"),
        "cnv_records": ("sample_id", "region_label", "cnv_state"),
    }
    assert cnv_recurrence.nested_collection_required_fields == {
        "annotation_tracks.values": ("sample_id", "category_label"),
    }
    assert cnv_recurrence.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "cnv_legend_title_must_be_non_empty",
        "region_order_must_be_non_empty",
        "region_order_labels_must_be_unique",
        "sample_order_must_be_non_empty",
        "sample_ids_must_be_unique",
        "annotation_tracks_must_be_non_empty",
        "annotation_track_count_must_be_at_most_three",
        "annotation_track_ids_must_be_unique",
        "annotation_track_labels_must_be_non_empty",
        "annotation_track_sample_coverage_must_match_declared_sample_order",
        "annotation_track_category_labels_must_be_non_empty",
        "cnv_records_must_be_non_empty",
        "cnv_sample_ids_must_match_declared_sample_order",
        "cnv_region_labels_must_match_declared_region_order",
        "cnv_sample_region_coordinates_must_be_unique",
        "cnv_state_must_be_supported",
    )
    assert genomic_alteration_landscape.template_ids == (_full_id("genomic_alteration_landscape_panel"),)
    assert genomic_alteration_landscape.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "alteration_legend_title",
        "gene_order",
        "sample_order",
        "annotation_tracks",
        "alteration_records",
    )
    assert genomic_alteration_landscape.collection_required_fields == {
        "gene_order": ("label",),
        "sample_order": ("sample_id",),
        "annotation_tracks": ("track_id", "track_label", "values"),
        "alteration_records": ("sample_id", "gene_label"),
    }
    assert genomic_alteration_landscape.nested_collection_required_fields == {
        "annotation_tracks.values": ("sample_id", "category_label"),
    }
    assert genomic_alteration_landscape.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "alteration_legend_title_must_be_non_empty",
        "gene_order_must_be_non_empty",
        "gene_order_labels_must_be_unique",
        "sample_order_must_be_non_empty",
        "sample_ids_must_be_unique",
        "annotation_tracks_must_be_non_empty",
        "annotation_track_count_must_be_at_most_three",
        "annotation_track_ids_must_be_unique",
        "annotation_track_labels_must_be_non_empty",
        "annotation_track_sample_coverage_must_match_declared_sample_order",
        "annotation_track_category_labels_must_be_non_empty",
        "alteration_records_must_be_non_empty",
        "alteration_sample_ids_must_match_declared_sample_order",
        "alteration_gene_labels_must_match_declared_gene_order",
        "alteration_sample_gene_coordinates_must_be_unique",
        "alteration_record_must_define_mutation_or_cnv",
        "mutation_class_must_be_supported_when_present",
        "cnv_state_must_be_supported_when_present",
    )
    assert genomic_alteration_consequence.template_ids == (_full_id("genomic_alteration_consequence_panel"),)
    assert genomic_alteration_consequence.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "alteration_legend_title",
        "gene_order",
        "sample_order",
        "annotation_tracks",
        "alteration_records",
        "consequence_x_label",
        "consequence_y_label",
        "consequence_legend_title",
        "effect_threshold",
        "significance_threshold",
        "driver_gene_order",
        "consequence_panel_order",
        "consequence_points",
    )
    assert genomic_alteration_consequence.display_optional_fields == ("paper_role",)
    assert genomic_alteration_consequence.collection_required_fields["gene_order"] == ("label",)
    assert genomic_alteration_consequence.collection_required_fields["sample_order"] == ("sample_id",)
    assert genomic_alteration_consequence.collection_required_fields["annotation_tracks"] == (
        "track_id",
        "track_label",
        "values",
    )
    assert genomic_alteration_consequence.nested_collection_required_fields["annotation_tracks.values"] == (
        "sample_id",
        "category_label",
    )
    assert genomic_alteration_consequence.collection_required_fields["alteration_records"] == ("sample_id", "gene_label")
    assert genomic_alteration_consequence.collection_required_fields["driver_gene_order"] == ("label",)
    assert genomic_alteration_consequence.collection_required_fields["consequence_panel_order"] == (
        "panel_id",
        "panel_title",
    )
    assert genomic_alteration_consequence.collection_required_fields["consequence_points"] == (
        "panel_id",
        "gene_label",
        "effect_value",
        "significance_value",
        "regulation_class",
    )
    assert genomic_alteration_consequence.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "alteration_legend_title_must_be_non_empty",
        "gene_order_must_be_non_empty",
        "gene_order_labels_must_be_unique",
        "sample_order_must_be_non_empty",
        "sample_ids_must_be_unique",
        "annotation_tracks_must_be_non_empty",
        "annotation_track_count_must_be_at_most_three",
        "annotation_track_ids_must_be_unique",
        "annotation_track_labels_must_be_non_empty",
        "annotation_track_sample_coverage_must_match_declared_sample_order",
        "annotation_track_category_labels_must_be_non_empty",
        "alteration_records_must_be_non_empty",
        "alteration_sample_ids_must_match_declared_sample_order",
        "alteration_gene_labels_must_match_declared_gene_order",
        "alteration_sample_gene_coordinates_must_be_unique",
        "alteration_record_must_define_mutation_or_cnv",
        "mutation_class_must_be_supported_when_present",
        "cnv_state_must_be_supported_when_present",
        "consequence_x_label_must_be_non_empty",
        "consequence_y_label_must_be_non_empty",
        "consequence_legend_title_must_be_non_empty",
        "effect_threshold_must_be_positive",
        "significance_threshold_must_be_positive",
        "driver_gene_order_must_be_non_empty",
        "driver_gene_labels_must_be_unique",
        "driver_gene_labels_must_be_subset_of_gene_order",
        "consequence_panel_order_must_be_non_empty",
        "consequence_panel_order_count_must_be_at_most_two",
        "consequence_panel_ids_must_be_unique",
        "consequence_panel_titles_must_be_non_empty",
        "consequence_points_must_be_non_empty",
        "consequence_point_panel_ids_must_match_declared_panels",
        "consequence_point_gene_labels_must_match_declared_driver_genes",
        "consequence_point_coordinates_must_be_complete_and_unique",
        "consequence_point_effect_values_must_be_finite",
        "consequence_point_significance_values_must_be_non_negative",
        "consequence_point_regulation_classes_must_use_supported_vocabulary",
    )
