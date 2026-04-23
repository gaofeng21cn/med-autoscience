from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_numeric_value
from .validation_tables import _validate_labeled_order_payload, _validate_panel_order_payload, _validate_sample_order_payload

def _validate_pathway_enrichment_dotplot_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    panel_order = _validate_panel_order_payload(
        path=path,
        payload=payload.get("panel_order"),
        label=f"display `{expected_display_id}` panel_order",
    )
    pathway_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("pathway_order"),
        label=f"display `{expected_display_id}` pathway_order",
    )
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty points list")

    declared_panel_ids = {item["panel_id"] for item in panel_order}
    declared_pathway_labels = {item["label"] for item in pathway_order}
    expected_coordinates = {
        (panel["panel_id"], pathway["label"]) for panel in panel_order for pathway in pathway_order
    }
    observed_coordinates: set[tuple[str, str]] = set()
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].panel_id",
        )
        if panel_id not in declared_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}].panel_id must match panel_order")
        pathway_label = _require_non_empty_string(
            item.get("pathway_label"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].pathway_label",
        )
        if pathway_label not in declared_pathway_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].pathway_label must match pathway_order"
            )
        coordinate = (panel_id, pathway_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared panel/pathway coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        size_value = _require_numeric_value(
            item.get("size_value"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].size_value",
        )
        if size_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].size_value must be non-negative"
            )
        normalized_points.append(
            {
                "panel_id": panel_id,
                "pathway_label": pathway_label,
                "x_value": _require_numeric_value(
                    item.get("x_value"),
                    label=f"{path.name} display `{expected_display_id}` points[{index}].x_value",
                ),
                "effect_value": _require_numeric_value(
                    item.get("effect_value"),
                    label=f"{path.name} display `{expected_display_id}` points[{index}].effect_value",
                ),
                "size_value": size_value,
            }
        )
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared panel/pathway coordinate exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "effect_scale_label": _require_non_empty_string(
            payload.get("effect_scale_label"),
            label=f"{path.name} display `{expected_display_id}` effect_scale_label",
        ),
        "size_scale_label": _require_non_empty_string(
            payload.get("size_scale_label"),
            label=f"{path.name} display `{expected_display_id}` size_scale_label",
        ),
        "panel_order": panel_order,
        "pathway_order": pathway_order,
        "points": normalized_points,
    }

def _validate_celltype_marker_dotplot_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    panel_order = _validate_panel_order_payload(
        path=path,
        payload=payload.get("panel_order"),
        label=f"display `{expected_display_id}` panel_order",
    )
    celltype_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("celltype_order"),
        label=f"display `{expected_display_id}` celltype_order",
    )
    marker_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("marker_order"),
        label=f"display `{expected_display_id}` marker_order",
    )
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty points list")

    declared_panel_ids = {item["panel_id"] for item in panel_order}
    declared_celltype_labels = {item["label"] for item in celltype_order}
    declared_marker_labels = {item["label"] for item in marker_order}
    expected_coordinates = {
        (panel["panel_id"], celltype["label"], marker["label"])
        for panel in panel_order
        for celltype in celltype_order
        for marker in marker_order
    }
    observed_coordinates: set[tuple[str, str, str]] = set()
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].panel_id",
        )
        if panel_id not in declared_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}].panel_id must match panel_order")
        celltype_label = _require_non_empty_string(
            item.get("celltype_label"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].celltype_label",
        )
        if celltype_label not in declared_celltype_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].celltype_label must match celltype_order"
            )
        marker_label = _require_non_empty_string(
            item.get("marker_label"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].marker_label",
        )
        if marker_label not in declared_marker_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].marker_label must match marker_order"
            )
        coordinate = (panel_id, celltype_label, marker_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared panel/celltype/marker coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        size_value = _require_numeric_value(
            item.get("size_value"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].size_value",
        )
        if size_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].size_value must be non-negative"
            )
        normalized_points.append(
            {
                "panel_id": panel_id,
                "celltype_label": celltype_label,
                "marker_label": marker_label,
                "effect_value": _require_numeric_value(
                    item.get("effect_value"),
                    label=f"{path.name} display `{expected_display_id}` points[{index}].effect_value",
                ),
                "size_value": size_value,
            }
        )
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared panel/celltype/marker coordinate exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "effect_scale_label": _require_non_empty_string(
            payload.get("effect_scale_label"),
            label=f"{path.name} display `{expected_display_id}` effect_scale_label",
        ),
        "size_scale_label": _require_non_empty_string(
            payload.get("size_scale_label"),
            label=f"{path.name} display `{expected_display_id}` size_scale_label",
        ),
        "panel_order": panel_order,
        "celltype_order": celltype_order,
        "marker_order": marker_order,
        "points": normalized_points,
    }

def _validate_oncoplot_mutation_landscape_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    burden_axis_label = _require_non_empty_string(
        payload.get("burden_axis_label"),
        label=f"{path.name} display `{expected_display_id}` burden_axis_label",
    )
    frequency_axis_label = _require_non_empty_string(
        payload.get("frequency_axis_label"),
        label=f"{path.name} display `{expected_display_id}` frequency_axis_label",
    )
    mutation_legend_title = _require_non_empty_string(
        payload.get("mutation_legend_title"),
        label=f"{path.name} display `{expected_display_id}` mutation_legend_title",
    )
    gene_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("gene_order"),
        label=f"display `{expected_display_id}` gene_order",
    )
    sample_order = _validate_sample_order_payload(
        path=path,
        payload=payload.get("sample_order"),
        label=f"display `{expected_display_id}` sample_order",
    )
    declared_gene_labels = {item["label"] for item in gene_order}
    declared_sample_ids = {item["sample_id"] for item in sample_order}

    annotation_tracks = payload.get("annotation_tracks")
    if not isinstance(annotation_tracks, list) or not annotation_tracks:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty annotation_tracks list")
    if len(annotation_tracks) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` annotation_tracks must contain at most three tracks")
    normalized_tracks: list[dict[str, Any]] = []
    seen_track_ids: set[str] = set()
    for index, track in enumerate(annotation_tracks):
        if not isinstance(track, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` annotation_tracks[{index}] must be an object")
        track_id = _require_non_empty_string(
            track.get("track_id"),
            label=f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].track_id",
        )
        if track_id in seen_track_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].track_id must be unique"
            )
        seen_track_ids.add(track_id)
        track_label = _require_non_empty_string(
            track.get("track_label"),
            label=f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].track_label",
        )
        values = track.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values must be a non-empty list"
            )
        normalized_values: list[dict[str, str]] = []
        seen_track_sample_ids: set[str] = set()
        for value_index, item in enumerate(values):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values[{value_index}] must be an object"
                )
            sample_id = _require_non_empty_string(
                item.get("sample_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"annotation_tracks[{index}].values[{value_index}].sample_id"
                ),
            )
            if sample_id not in declared_sample_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values[{value_index}].sample_id "
                    "must match sample_order"
                )
            if sample_id in seen_track_sample_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values must cover the declared sample_order exactly once"
                )
            seen_track_sample_ids.add(sample_id)
            normalized_values.append(
                {
                    "sample_id": sample_id,
                    "category_label": _require_non_empty_string(
                        item.get("category_label"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"annotation_tracks[{index}].values[{value_index}].category_label"
                        ),
                    ),
                }
            )
        if seen_track_sample_ids != declared_sample_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values must cover the declared sample_order exactly once"
            )
        normalized_tracks.append(
            {
                "track_id": track_id,
                "track_label": track_label,
                "values": normalized_values,
            }
        )

    mutation_records = payload.get("mutation_records")
    if not isinstance(mutation_records, list) or not mutation_records:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty mutation_records list")
    supported_alteration_classes = {"missense", "truncating", "amplification", "fusion"}
    normalized_mutation_records: list[dict[str, str]] = []
    observed_mutation_samples: set[str] = set()
    observed_mutation_genes: set[str] = set()
    seen_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(mutation_records):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` mutation_records[{index}] must be an object")
        sample_id = _require_non_empty_string(
            item.get("sample_id"),
            label=f"{path.name} display `{expected_display_id}` mutation_records[{index}].sample_id",
        )
        if sample_id not in declared_sample_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` mutation_records[{index}].sample_id must match sample_order"
            )
        gene_label = _require_non_empty_string(
            item.get("gene_label"),
            label=f"{path.name} display `{expected_display_id}` mutation_records[{index}].gene_label",
        )
        if gene_label not in declared_gene_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` mutation_records[{index}].gene_label must match gene_order"
            )
        coordinate = (sample_id, gene_label)
        if coordinate in seen_coordinates:
            raise ValueError(f"{path.name} display `{expected_display_id}` must keep sample/gene coordinates unique")
        seen_coordinates.add(coordinate)
        alteration_class = _require_non_empty_string(
            item.get("alteration_class"),
            label=f"{path.name} display `{expected_display_id}` mutation_records[{index}].alteration_class",
        )
        if alteration_class not in supported_alteration_classes:
            supported = ", ".join(sorted(supported_alteration_classes))
            raise ValueError(
                f"{path.name} display `{expected_display_id}` mutation_records[{index}].alteration_class must be one of {supported}"
            )
        observed_mutation_samples.add(sample_id)
        observed_mutation_genes.add(gene_label)
        normalized_mutation_records.append(
            {
                "sample_id": sample_id,
                "gene_label": gene_label,
                "alteration_class": alteration_class,
            }
        )
    if observed_mutation_samples != declared_sample_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` mutation_records sample_id values must match sample_order")
    if observed_mutation_genes != declared_gene_labels:
        raise ValueError(f"{path.name} display `{expected_display_id}` mutation_records gene_label values must match gene_order")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "burden_axis_label": burden_axis_label,
        "frequency_axis_label": frequency_axis_label,
        "mutation_legend_title": mutation_legend_title,
        "gene_order": gene_order,
        "sample_order": sample_order,
        "annotation_tracks": normalized_tracks,
        "mutation_records": normalized_mutation_records,
    }

def _validate_cnv_recurrence_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    burden_axis_label = _require_non_empty_string(
        payload.get("burden_axis_label"),
        label=f"{path.name} display `{expected_display_id}` burden_axis_label",
    )
    frequency_axis_label = _require_non_empty_string(
        payload.get("frequency_axis_label"),
        label=f"{path.name} display `{expected_display_id}` frequency_axis_label",
    )
    cnv_legend_title = _require_non_empty_string(
        payload.get("cnv_legend_title"),
        label=f"{path.name} display `{expected_display_id}` cnv_legend_title",
    )
    region_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("region_order"),
        label=f"display `{expected_display_id}` region_order",
    )
    sample_order = _validate_sample_order_payload(
        path=path,
        payload=payload.get("sample_order"),
        label=f"display `{expected_display_id}` sample_order",
    )
    declared_region_labels = {item["label"] for item in region_order}
    declared_sample_ids = {item["sample_id"] for item in sample_order}

    annotation_tracks = payload.get("annotation_tracks")
    if not isinstance(annotation_tracks, list) or not annotation_tracks:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty annotation_tracks list")
    if len(annotation_tracks) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` annotation_tracks must contain at most three tracks")
    normalized_tracks: list[dict[str, Any]] = []
    seen_track_ids: set[str] = set()
    for index, track in enumerate(annotation_tracks):
        if not isinstance(track, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` annotation_tracks[{index}] must be an object")
        track_id = _require_non_empty_string(
            track.get("track_id"),
            label=f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].track_id",
        )
        if track_id in seen_track_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].track_id must be unique"
            )
        seen_track_ids.add(track_id)
        track_label = _require_non_empty_string(
            track.get("track_label"),
            label=f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].track_label",
        )
        values = track.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values must be a non-empty list"
            )
        normalized_values: list[dict[str, str]] = []
        seen_track_sample_ids: set[str] = set()
        for value_index, item in enumerate(values):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values[{value_index}] must be an object"
                )
            sample_id = _require_non_empty_string(
                item.get("sample_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"annotation_tracks[{index}].values[{value_index}].sample_id"
                ),
            )
            if sample_id not in declared_sample_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values[{value_index}].sample_id "
                    "must match sample_order"
                )
            if sample_id in seen_track_sample_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values must cover the declared sample_order exactly once"
                )
            seen_track_sample_ids.add(sample_id)
            normalized_values.append(
                {
                    "sample_id": sample_id,
                    "category_label": _require_non_empty_string(
                        item.get("category_label"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"annotation_tracks[{index}].values[{value_index}].category_label"
                        ),
                    ),
                }
            )
        if seen_track_sample_ids != declared_sample_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` annotation_tracks[{index}].values must cover the declared sample_order exactly once"
            )
        normalized_tracks.append(
            {
                "track_id": track_id,
                "track_label": track_label,
                "values": normalized_values,
            }
        )

    cnv_records = payload.get("cnv_records")
    if not isinstance(cnv_records, list) or not cnv_records:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty cnv_records list")
    supported_cnv_states = {"amplification", "gain", "loss", "deep_loss"}
    normalized_cnv_records: list[dict[str, str]] = []
    observed_cnv_samples: set[str] = set()
    observed_cnv_regions: set[str] = set()
    seen_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(cnv_records):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` cnv_records[{index}] must be an object")
        sample_id = _require_non_empty_string(
            item.get("sample_id"),
            label=f"{path.name} display `{expected_display_id}` cnv_records[{index}].sample_id",
        )
        if sample_id not in declared_sample_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` cnv_records[{index}].sample_id must match sample_order"
            )
        region_label = _require_non_empty_string(
            item.get("region_label"),
            label=f"{path.name} display `{expected_display_id}` cnv_records[{index}].region_label",
        )
        if region_label not in declared_region_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` cnv_records[{index}].region_label must match region_order"
            )
        coordinate = (sample_id, region_label)
        if coordinate in seen_coordinates:
            raise ValueError(f"{path.name} display `{expected_display_id}` must keep sample/region coordinates unique")
        seen_coordinates.add(coordinate)
        cnv_state = _require_non_empty_string(
            item.get("cnv_state"),
            label=f"{path.name} display `{expected_display_id}` cnv_records[{index}].cnv_state",
        )
        if cnv_state not in supported_cnv_states:
            supported = ", ".join(sorted(supported_cnv_states))
            raise ValueError(
                f"{path.name} display `{expected_display_id}` cnv_records[{index}].cnv_state must be one of {supported}"
            )
        observed_cnv_samples.add(sample_id)
        observed_cnv_regions.add(region_label)
        normalized_cnv_records.append(
            {
                "sample_id": sample_id,
                "region_label": region_label,
                "cnv_state": cnv_state,
            }
        )
    if observed_cnv_samples != declared_sample_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` cnv_records sample_id values must match sample_order")
    if observed_cnv_regions != declared_region_labels:
        raise ValueError(f"{path.name} display `{expected_display_id}` cnv_records region_label values must match region_order")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "burden_axis_label": burden_axis_label,
        "frequency_axis_label": frequency_axis_label,
        "cnv_legend_title": cnv_legend_title,
        "region_order": region_order,
        "sample_order": sample_order,
        "annotation_tracks": normalized_tracks,
        "cnv_records": normalized_cnv_records,
    }


__all__ = [
    "_validate_pathway_enrichment_dotplot_panel_display_payload",
    "_validate_celltype_marker_dotplot_panel_display_payload",
    "_validate_oncoplot_mutation_landscape_panel_display_payload",
    "_validate_cnv_recurrence_summary_panel_display_payload",
]
