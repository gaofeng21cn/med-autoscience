from .shared import *


def test_schema_contract_tracks_current_data_geometry_input_shapes() -> None:
    fx = _load_schema_contract_fixture()
    module = fx.module
    binary = fx.binary
    embedding = fx.embedding
    celltype_signature = fx.celltype_signature
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert binary.template_ids == (
        _full_id("roc_curve_binary"),
        _full_id("pr_curve_binary"),
        _full_id("calibration_curve_binary"),
        _full_id("decision_curve_binary"),
        _full_id("clinical_impact_curve_binary"),
        _full_id("time_dependent_roc_horizon"),
    )
    assert embedding.template_ids == (
        _full_id("umap_scatter_grouped"),
        _full_id("pca_scatter_grouped"),
        _full_id("phate_scatter_grouped"),
        _full_id("tsne_scatter_grouped"),
        _full_id("diffusion_map_scatter_grouped"),
    )
    assert celltype_signature.template_ids == (_full_id("celltype_signature_heatmap"),)
    assert celltype_signature.display_required_fields == (
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
    )
    assert celltype_signature.collection_required_fields["embedding_points"] == ("x", "y", "group")
    assert celltype_signature.collection_required_fields["cells"] == ("x", "y", "value")
    assert "declared_column_labels_must_match_embedding_groups" in celltype_signature.additional_constraints
    assert data_geometry_class.template_ids == (
        _full_id("umap_scatter_grouped"),
        _full_id("pca_scatter_grouped"),
        _full_id("phate_scatter_grouped"),
        _full_id("tsne_scatter_grouped"),
        _full_id("diffusion_map_scatter_grouped"),
        _full_id("celltype_signature_heatmap"),
        _full_id("omics_volcano_panel"),
    )
    assert data_geometry_class.input_schema_ids == (
        "embedding_grouped_inputs_v1",
        "celltype_signature_heatmap_inputs_v1",
        "omics_volcano_panel_inputs_v1",
    )
