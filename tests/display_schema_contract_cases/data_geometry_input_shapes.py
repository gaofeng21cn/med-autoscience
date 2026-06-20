from .shared import *


def test_schema_contract_tracks_current_data_geometry_input_shapes() -> None:
    fx = _load_schema_contract_fixture()
    module = fx.module
    binary = fx.binary
    dimensionality_reduction = fx.dimensionality_reduction
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert binary.template_ids == (
        _full_id("roc_curve_binary"),
        _full_id("pr_curve_binary"),
        _full_id("calibration_curve_binary"),
        _full_id("decision_curve_binary"),
        _full_id("time_dependent_roc_horizon"),
    )
    assert dimensionality_reduction.template_ids == (
        _full_id("pca_scatter_grouped"),
        _full_id("tsne_scatter_grouped"),
        _full_id("umap_scatter_grouped"),
    )
    assert dimensionality_reduction.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "embedding_input_mode",
        "feature_matrix",
    )
    assert dimensionality_reduction.collection_required_fields["feature_matrix"] == (
        "sample_id",
        "group",
        "features",
    )
    assert "default_current_templates_compute_embedding_from_feature_matrix" in dimensionality_reduction.additional_constraints
    assert "tsne_requires_Rtsne_backend" in dimensionality_reduction.additional_constraints
    assert "umap_requires_uwot_backend" in dimensionality_reduction.additional_constraints
    assert data_geometry_class.template_ids == (
        _full_id("pca_scatter_grouped"),
        _full_id("tsne_scatter_grouped"),
        _full_id("umap_scatter_grouped"),
        _full_id("omics_volcano_panel"),
    )
    assert data_geometry_class.input_schema_ids == (
        "dimensionality_reduction_inputs_v1",
        "omics_volcano_panel_inputs_v1",
    )
