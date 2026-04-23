from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, _require_probability_value, get_template_short_id
from .validation_tables import _validate_labeled_order_payload, _validate_panel_order_payload, _validate_sample_order_payload

def _validate_genomic_alteration_landscape_panel_display_payload(
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
    alteration_legend_title = _require_non_empty_string(
        payload.get("alteration_legend_title"),
        label=f"{path.name} display `{expected_display_id}` alteration_legend_title",
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

    alteration_records = payload.get("alteration_records")
    if not isinstance(alteration_records, list) or not alteration_records:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty alteration_records list")
    supported_mutation_classes = {"missense", "truncating", "fusion"}
    supported_cnv_states = {"amplification", "gain", "loss", "deep_loss"}
    normalized_alteration_records: list[dict[str, str]] = []
    observed_samples: set[str] = set()
    observed_genes: set[str] = set()
    seen_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(alteration_records):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` alteration_records[{index}] must be an object"
            )
        sample_id = _require_non_empty_string(
            item.get("sample_id"),
            label=f"{path.name} display `{expected_display_id}` alteration_records[{index}].sample_id",
        )
        if sample_id not in declared_sample_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` alteration_records[{index}].sample_id must match sample_order"
            )
        gene_label = _require_non_empty_string(
            item.get("gene_label"),
            label=f"{path.name} display `{expected_display_id}` alteration_records[{index}].gene_label",
        )
        if gene_label not in declared_gene_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` alteration_records[{index}].gene_label must match gene_order"
            )
        coordinate = (sample_id, gene_label)
        if coordinate in seen_coordinates:
            raise ValueError(f"{path.name} display `{expected_display_id}` must keep sample/gene coordinates unique")
        seen_coordinates.add(coordinate)

        normalized_record = {"sample_id": sample_id, "gene_label": gene_label}
        mutation_class = str(item.get("mutation_class") or "").strip()
        cnv_state = str(item.get("cnv_state") or "").strip()
        if not mutation_class and not cnv_state:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` alteration_records[{index}] must define mutation_class or cnv_state"
            )
        if mutation_class:
            if mutation_class not in supported_mutation_classes:
                supported = ", ".join(sorted(supported_mutation_classes))
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` alteration_records[{index}].mutation_class must be one of {supported}"
                )
            normalized_record["mutation_class"] = mutation_class
        if cnv_state:
            if cnv_state not in supported_cnv_states:
                supported = ", ".join(sorted(supported_cnv_states))
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` alteration_records[{index}].cnv_state must be one of {supported}"
                )
            normalized_record["cnv_state"] = cnv_state
        observed_samples.add(sample_id)
        observed_genes.add(gene_label)
        normalized_alteration_records.append(normalized_record)
    if observed_samples != declared_sample_ids:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` alteration_records sample_id values must match sample_order"
        )
    if observed_genes != declared_gene_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` alteration_records gene_label values must match gene_order"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "burden_axis_label": burden_axis_label,
        "frequency_axis_label": frequency_axis_label,
        "alteration_legend_title": alteration_legend_title,
        "gene_order": gene_order,
        "sample_order": sample_order,
        "annotation_tracks": normalized_tracks,
        "alteration_records": normalized_alteration_records,
    }

def _validate_genomic_alteration_consequence_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
    max_consequence_panels: int = 2,
) -> dict[str, Any]:
    normalized_payload = _validate_genomic_alteration_landscape_panel_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    consequence_x_label = _require_non_empty_string(
        payload.get("consequence_x_label"),
        label=f"{path.name} display `{expected_display_id}` consequence_x_label",
    )
    consequence_y_label = _require_non_empty_string(
        payload.get("consequence_y_label"),
        label=f"{path.name} display `{expected_display_id}` consequence_y_label",
    )
    consequence_legend_title = _require_non_empty_string(
        payload.get("consequence_legend_title"),
        label=f"{path.name} display `{expected_display_id}` consequence_legend_title",
    )
    effect_threshold = _require_numeric_value(
        payload.get("effect_threshold"),
        label=f"{path.name} display `{expected_display_id}` effect_threshold",
    )
    if effect_threshold <= 0.0:
        raise ValueError(f"{path.name} display `{expected_display_id}` effect_threshold must be positive")
    significance_threshold = _require_numeric_value(
        payload.get("significance_threshold"),
        label=f"{path.name} display `{expected_display_id}` significance_threshold",
    )
    if significance_threshold <= 0.0:
        raise ValueError(f"{path.name} display `{expected_display_id}` significance_threshold must be positive")

    driver_gene_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("driver_gene_order"),
        label=f"display `{expected_display_id}` driver_gene_order",
    )
    declared_gene_labels = {item["label"] for item in normalized_payload["gene_order"]}
    driver_gene_labels = {item["label"] for item in driver_gene_order}
    if not driver_gene_labels.issubset(declared_gene_labels):
        raise ValueError(f"{path.name} display `{expected_display_id}` driver_gene_order labels must stay inside gene_order")

    consequence_panel_order = _validate_panel_order_payload(
        path=path,
        payload=payload.get("consequence_panel_order"),
        label=f"display `{expected_display_id}` consequence_panel_order",
        max_panels=max_consequence_panels,
    )
    declared_panel_ids = {item["panel_id"] for item in consequence_panel_order}

    consequence_points = payload.get("consequence_points")
    if not isinstance(consequence_points, list) or not consequence_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty consequence_points list")
    supported_regulation_classes = {"upregulated", "downregulated", "background"}
    observed_coordinates: set[tuple[str, str]] = set()
    normalized_consequence_points: list[dict[str, Any]] = []
    for index, item in enumerate(consequence_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` consequence_points[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` consequence_points[{index}].panel_id",
        )
        if panel_id not in declared_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` consequence_points[{index}].panel_id must match consequence_panel_order"
            )
        gene_label = _require_non_empty_string(
            item.get("gene_label"),
            label=f"{path.name} display `{expected_display_id}` consequence_points[{index}].gene_label",
        )
        if gene_label not in driver_gene_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` consequence_points[{index}].gene_label must match driver_gene_order"
            )
        coordinate = (panel_id, gene_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared consequence panel/driver gene coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        effect_value = _require_numeric_value(
            item.get("effect_value"),
            label=f"{path.name} display `{expected_display_id}` consequence_points[{index}].effect_value",
        )
        significance_value = _require_numeric_value(
            item.get("significance_value"),
            label=f"{path.name} display `{expected_display_id}` consequence_points[{index}].significance_value",
        )
        if significance_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` consequence_points[{index}].significance_value must be non-negative"
            )
        regulation_class = _require_non_empty_string(
            item.get("regulation_class"),
            label=f"{path.name} display `{expected_display_id}` consequence_points[{index}].regulation_class",
        )
        if regulation_class not in supported_regulation_classes:
            supported_classes = ", ".join(("upregulated", "downregulated", "background"))
            raise ValueError(
                f"{path.name} display `{expected_display_id}` consequence_points[{index}].regulation_class must be one of {supported_classes}"
            )
        normalized_consequence_points.append(
            {
                "panel_id": panel_id,
                "gene_label": gene_label,
                "effect_value": effect_value,
                "significance_value": significance_value,
                "regulation_class": regulation_class,
            }
        )

    expected_coordinates = {
        (panel["panel_id"], driver_gene["label"])
        for panel in consequence_panel_order
        for driver_gene in driver_gene_order
    }
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared consequence panel/driver gene coordinate exactly once"
        )

    normalized_payload["consequence_x_label"] = consequence_x_label
    normalized_payload["consequence_y_label"] = consequence_y_label
    normalized_payload["consequence_legend_title"] = consequence_legend_title
    normalized_payload["effect_threshold"] = effect_threshold
    normalized_payload["significance_threshold"] = significance_threshold
    normalized_payload["driver_gene_order"] = driver_gene_order
    normalized_payload["consequence_panel_order"] = consequence_panel_order
    normalized_payload["consequence_points"] = normalized_consequence_points
    return normalized_payload

def _validate_genomic_alteration_multiomic_consequence_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized_payload = _validate_genomic_alteration_consequence_panel_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
        max_consequence_panels=3,
    )
    expected_panel_ids = {"proteome", "phosphoproteome", "glycoproteome"}
    declared_panel_ids = {str(item["panel_id"]) for item in normalized_payload["consequence_panel_order"]}
    if len(normalized_payload["consequence_panel_order"]) != 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` consequence_panel_order must contain exactly three panels")
    if declared_panel_ids != expected_panel_ids:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` consequence_panel_order panel_id values must be proteome, phosphoproteome, and glycoproteome"
        )
    return normalized_payload

def _validate_genomic_alteration_pathway_integrated_composite_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized_payload = _validate_genomic_alteration_multiomic_consequence_panel_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    pathway_x_label = _require_non_empty_string(
        payload.get("pathway_x_label"),
        label=f"{path.name} display `{expected_display_id}` pathway_x_label",
    )
    pathway_y_label = _require_non_empty_string(
        payload.get("pathway_y_label"),
        label=f"{path.name} display `{expected_display_id}` pathway_y_label",
    )
    pathway_effect_scale_label = _require_non_empty_string(
        payload.get("pathway_effect_scale_label"),
        label=f"{path.name} display `{expected_display_id}` pathway_effect_scale_label",
    )
    pathway_size_scale_label = _require_non_empty_string(
        payload.get("pathway_size_scale_label"),
        label=f"{path.name} display `{expected_display_id}` pathway_size_scale_label",
    )
    pathway_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("pathway_order"),
        label=f"display `{expected_display_id}` pathway_order",
    )
    pathway_panel_order = _validate_panel_order_payload(
        path=path,
        payload=payload.get("pathway_panel_order"),
        label=f"display `{expected_display_id}` pathway_panel_order",
        max_panels=3,
    )
    expected_panel_ids = {"proteome", "phosphoproteome", "glycoproteome"}
    declared_panel_ids = {str(item["panel_id"]) for item in pathway_panel_order}
    if len(pathway_panel_order) != 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` pathway_panel_order must contain exactly three panels")
    if declared_panel_ids != expected_panel_ids:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` pathway_panel_order panel_id values must be proteome, phosphoproteome, and glycoproteome"
        )

    declared_pathway_labels = {item["label"] for item in pathway_order}
    expected_coordinates = {
        (panel["panel_id"], pathway["label"])
        for panel in pathway_panel_order
        for pathway in pathway_order
    }
    pathway_points = payload.get("pathway_points")
    if not isinstance(pathway_points, list) or not pathway_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty pathway_points list")

    observed_coordinates: set[tuple[str, str]] = set()
    normalized_pathway_points: list[dict[str, Any]] = []
    for index, item in enumerate(pathway_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` pathway_points[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` pathway_points[{index}].panel_id",
        )
        if panel_id not in declared_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` pathway_points[{index}].panel_id must match pathway_panel_order"
            )
        pathway_label = _require_non_empty_string(
            item.get("pathway_label"),
            label=f"{path.name} display `{expected_display_id}` pathway_points[{index}].pathway_label",
        )
        if pathway_label not in declared_pathway_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` pathway_points[{index}].pathway_label must match pathway_order"
            )
        coordinate = (panel_id, pathway_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared pathway panel/pathway coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        size_value = _require_numeric_value(
            item.get("size_value"),
            label=f"{path.name} display `{expected_display_id}` pathway_points[{index}].size_value",
        )
        if size_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` pathway_points[{index}].size_value must be non-negative"
            )
        normalized_pathway_points.append(
            {
                "panel_id": panel_id,
                "pathway_label": pathway_label,
                "x_value": _require_numeric_value(
                    item.get("x_value"),
                    label=f"{path.name} display `{expected_display_id}` pathway_points[{index}].x_value",
                ),
                "effect_value": _require_numeric_value(
                    item.get("effect_value"),
                    label=f"{path.name} display `{expected_display_id}` pathway_points[{index}].effect_value",
                ),
                "size_value": size_value,
            }
        )
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared pathway panel/pathway coordinate exactly once"
        )

    normalized_payload["pathway_x_label"] = pathway_x_label
    normalized_payload["pathway_y_label"] = pathway_y_label
    normalized_payload["pathway_effect_scale_label"] = pathway_effect_scale_label
    normalized_payload["pathway_size_scale_label"] = pathway_size_scale_label
    normalized_payload["pathway_order"] = pathway_order
    normalized_payload["pathway_panel_order"] = pathway_panel_order
    normalized_payload["pathway_points"] = normalized_pathway_points
    return normalized_payload

def _validate_genomic_program_governance_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    expected_layer_ids = ("alteration", "proteome", "phosphoproteome", "glycoproteome", "pathway")
    supported_priority_bands = {"high_priority", "monitor", "watchlist"}
    supported_verdicts = {"convergent", "layer_specific", "context_dependent", "insufficient_support"}

    layer_order_payload = payload.get("layer_order")
    if not isinstance(layer_order_payload, list) or not layer_order_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty layer_order list")
    if len(layer_order_payload) != len(expected_layer_ids):
        raise ValueError(f"{path.name} display `{expected_display_id}` layer_order must contain exactly five layers")
    normalized_layer_order: list[dict[str, str]] = []
    observed_layer_ids: list[str] = []
    for layer_index, layer_payload in enumerate(layer_order_payload):
        if not isinstance(layer_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` layer_order[{layer_index}] must be an object")
        layer_id = _require_non_empty_string(
            layer_payload.get("layer_id"),
            label=f"{path.name} display `{expected_display_id}` layer_order[{layer_index}].layer_id",
        )
        layer_label = _require_non_empty_string(
            layer_payload.get("layer_label"),
            label=f"{path.name} display `{expected_display_id}` layer_order[{layer_index}].layer_label",
        )
        observed_layer_ids.append(layer_id)
        normalized_layer_order.append({"layer_id": layer_id, "layer_label": layer_label})
    if tuple(observed_layer_ids) != expected_layer_ids:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` layer_order layer_id values must be alteration, proteome, phosphoproteome, glycoproteome, and pathway"
        )

    programs_payload = payload.get("programs")
    if not isinstance(programs_payload, list) or not programs_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty programs list")

    normalized_programs: list[dict[str, Any]] = []
    seen_program_ids: set[str] = set()
    seen_program_labels: set[str] = set()
    observed_priority_ranks: list[int] = []
    declared_layer_id_set = set(expected_layer_ids)
    for program_index, program_payload in enumerate(programs_payload):
        if not isinstance(program_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` programs[{program_index}] must be an object")
        program_id = _require_non_empty_string(
            program_payload.get("program_id"),
            label=f"{path.name} display `{expected_display_id}` programs[{program_index}].program_id",
        )
        if program_id in seen_program_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` programs[{program_index}].program_id must be unique"
            )
        seen_program_ids.add(program_id)
        program_label = _require_non_empty_string(
            program_payload.get("program_label"),
            label=f"{path.name} display `{expected_display_id}` programs[{program_index}].program_label",
        )
        if program_label in seen_program_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` programs[{program_index}].program_label must be unique"
            )
        seen_program_labels.add(program_label)
        pathway_hit_count = _require_non_negative_int(
            program_payload.get("pathway_hit_count"),
            label=f"{path.name} display `{expected_display_id}` programs[{program_index}].pathway_hit_count",
            allow_zero=False,
        )
        priority_rank = _require_non_negative_int(
            program_payload.get("priority_rank"),
            label=f"{path.name} display `{expected_display_id}` programs[{program_index}].priority_rank",
            allow_zero=False,
        )
        observed_priority_ranks.append(priority_rank)
        priority_band = _require_non_empty_string(
            program_payload.get("priority_band"),
            label=f"{path.name} display `{expected_display_id}` programs[{program_index}].priority_band",
        )
        if priority_band not in supported_priority_bands:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` programs[{program_index}].priority_band must be one of {sorted(supported_priority_bands)}"
            )
        verdict = _require_non_empty_string(
            program_payload.get("verdict"),
            label=f"{path.name} display `{expected_display_id}` programs[{program_index}].verdict",
        )
        if verdict not in supported_verdicts:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` programs[{program_index}].verdict must be one of {sorted(supported_verdicts)}"
            )

        layer_supports_payload = program_payload.get("layer_supports")
        if not isinstance(layer_supports_payload, list) or not layer_supports_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` programs[{program_index}] must contain a non-empty layer_supports list"
            )
        observed_program_layer_ids: set[str] = set()
        normalized_layer_supports: list[dict[str, Any]] = []
        for support_index, support_payload in enumerate(layer_supports_payload):
            if not isinstance(support_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` programs[{program_index}].layer_supports[{support_index}] must be an object"
                )
            layer_id = _require_non_empty_string(
                support_payload.get("layer_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` programs[{program_index}]."
                    f"layer_supports[{support_index}].layer_id"
                ),
            )
            if layer_id not in declared_layer_id_set:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` programs[{program_index}].layer_supports[{support_index}].layer_id must match layer_order"
                )
            if layer_id in observed_program_layer_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` programs[{program_index}] layer_supports must cover the declared layer_order exactly once"
                )
            observed_program_layer_ids.add(layer_id)
            normalized_layer_supports.append(
                {
                    "layer_id": layer_id,
                    "effect_value": _require_numeric_value(
                        support_payload.get("effect_value"),
                        label=(
                            f"{path.name} display `{expected_display_id}` programs[{program_index}]."
                            f"layer_supports[{support_index}].effect_value"
                        ),
                    ),
                    "support_fraction": _require_probability_value(
                        support_payload.get("support_fraction"),
                        label=(
                            f"{path.name} display `{expected_display_id}` programs[{program_index}]."
                            f"layer_supports[{support_index}].support_fraction"
                        ),
                    ),
                }
            )
        if observed_program_layer_ids != declared_layer_id_set:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` programs[{program_index}] layer_supports must cover the declared layer_order exactly once"
            )

        normalized_program = {
            "program_id": program_id,
            "program_label": program_label,
            "lead_driver_label": _require_non_empty_string(
                program_payload.get("lead_driver_label"),
                label=f"{path.name} display `{expected_display_id}` programs[{program_index}].lead_driver_label",
            ),
            "dominant_pathway_label": _require_non_empty_string(
                program_payload.get("dominant_pathway_label"),
                label=f"{path.name} display `{expected_display_id}` programs[{program_index}].dominant_pathway_label",
            ),
            "pathway_hit_count": pathway_hit_count,
            "priority_rank": priority_rank,
            "priority_band": priority_band,
            "verdict": verdict,
            "action": _require_non_empty_string(
                program_payload.get("action"),
                label=f"{path.name} display `{expected_display_id}` programs[{program_index}].action",
            ),
            "layer_supports": normalized_layer_supports,
        }
        detail_text = str(program_payload.get("detail") or "").strip()
        if program_payload.get("detail") is not None and not detail_text:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` programs[{program_index}].detail must be non-empty when present"
            )
        if detail_text:
            normalized_program["detail"] = detail_text
        normalized_programs.append(normalized_program)

    if observed_priority_ranks != sorted(observed_priority_ranks) or len(set(observed_priority_ranks)) != len(
        observed_priority_ranks
    ):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` program priority_rank values must be strictly increasing"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title"),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "evidence_panel_title": _require_non_empty_string(
            payload.get("evidence_panel_title"),
            label=f"{path.name} display `{expected_display_id}` evidence_panel_title",
        ),
        "summary_panel_title": _require_non_empty_string(
            payload.get("summary_panel_title"),
            label=f"{path.name} display `{expected_display_id}` summary_panel_title",
        ),
        "effect_scale_label": _require_non_empty_string(
            payload.get("effect_scale_label"),
            label=f"{path.name} display `{expected_display_id}` effect_scale_label",
        ),
        "support_scale_label": _require_non_empty_string(
            payload.get("support_scale_label"),
            label=f"{path.name} display `{expected_display_id}` support_scale_label",
        ),
        "layer_order": normalized_layer_order,
        "programs": normalized_programs,
    }

def _validate_omics_volcano_panel_display_payload(
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
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
    )
    effect_threshold = _require_numeric_value(
        payload.get("effect_threshold"),
        label=f"{path.name} display `{expected_display_id}` effect_threshold",
    )
    if effect_threshold <= 0.0:
        raise ValueError(f"{path.name} display `{expected_display_id}` effect_threshold must be positive")
    significance_threshold = _require_numeric_value(
        payload.get("significance_threshold"),
        label=f"{path.name} display `{expected_display_id}` significance_threshold",
    )
    if significance_threshold <= 0.0:
        raise ValueError(f"{path.name} display `{expected_display_id}` significance_threshold must be positive")
    panel_order = _validate_panel_order_payload(
        path=path,
        payload=payload.get("panel_order"),
        label=f"display `{expected_display_id}` panel_order",
    )
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty points list")

    declared_panel_ids = {item["panel_id"] for item in panel_order}
    panel_point_counts = {panel_id: 0 for panel_id in declared_panel_ids}
    feature_labels_by_panel = {panel_id: set() for panel_id in declared_panel_ids}
    supported_regulation_classes = {"upregulated", "downregulated", "background"}
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
        feature_label = _require_non_empty_string(
            item.get("feature_label"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].feature_label",
        )
        if feature_label in feature_labels_by_panel[panel_id]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].feature_label must be unique within its panel"
            )
        feature_labels_by_panel[panel_id].add(feature_label)
        effect_value = _require_numeric_value(
            item.get("effect_value"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].effect_value",
        )
        significance_value = _require_numeric_value(
            item.get("significance_value"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].significance_value",
        )
        if significance_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].significance_value must be non-negative"
            )
        regulation_class = _require_non_empty_string(
            item.get("regulation_class"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].regulation_class",
        )
        if regulation_class not in supported_regulation_classes:
            supported_classes = ", ".join(("upregulated", "downregulated", "background"))
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].regulation_class must be one of {supported_classes}"
            )
        label_text = str(item.get("label_text") or "").strip()
        if "label_text" in item and not label_text:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].label_text must be non-empty when present"
            )
        normalized_point = {
            "panel_id": panel_id,
            "feature_label": feature_label,
            "effect_value": effect_value,
            "significance_value": significance_value,
            "regulation_class": regulation_class,
        }
        if label_text:
            normalized_point["label_text"] = label_text
        normalized_points.append(normalized_point)
        panel_point_counts[panel_id] += 1

    for panel_id, point_count in panel_point_counts.items():
        if point_count > 0:
            continue
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain at least one point for panel `{panel_id}`")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "legend_title": legend_title,
        "effect_threshold": effect_threshold,
        "significance_threshold": significance_threshold,
        "panel_order": panel_order,
        "points": normalized_points,
    }


__all__ = [
    "_validate_genomic_alteration_landscape_panel_display_payload",
    "_validate_genomic_alteration_consequence_panel_display_payload",
    "_validate_genomic_alteration_multiomic_consequence_panel_display_payload",
    "_validate_genomic_alteration_pathway_integrated_composite_panel_display_payload",
    "_validate_genomic_program_governance_summary_panel_display_payload",
    "_validate_omics_volcano_panel_display_payload",
]
