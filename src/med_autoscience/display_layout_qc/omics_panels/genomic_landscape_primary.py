from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_legend_panel_overlap,
    _check_required_box_types,
    _issue,
    _require_numeric,
)

def _check_publication_oncoplot_mutation_landscape_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "subplot_y_axis_title", "panel_label")))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    required_panel_ids = ("panel_burden", "panel_annotations", "panel_matrix", "panel_frequency")
    for panel_id in required_panel_ids:
        if panel_id not in panel_boxes_by_id:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message=f"oncoplot mutation landscape requires `{panel_id}` panel box",
                    target=f"panel_boxes.{panel_id}",
                    observed=sorted(panel_boxes_by_id),
                )
            )

    label_box = layout_boxes_by_id.get("panel_label_A")
    burden_panel_box = panel_boxes_by_id.get("panel_burden")
    if label_box is None:
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="oncoplot mutation landscape requires panel_label_A",
                target="layout_boxes.panel_label_A",
            )
        )

    mutation_legend_title = str(sidecar.metrics.get("mutation_legend_title") or "").strip()
    if not mutation_legend_title:
        issues.append(
            _issue(
                rule_id="mutation_legend_title_missing",
                message="oncoplot mutation landscape requires a non-empty mutation_legend_title",
                target="metrics.mutation_legend_title",
            )
        )

    sample_payload = sidecar.metrics.get("sample_ids")
    if not isinstance(sample_payload, list) or not sample_payload:
        issues.append(
            _issue(
                rule_id="sample_ids_missing",
                message="oncoplot mutation landscape requires non-empty sample_ids metrics",
                target="metrics.sample_ids",
            )
        )
        return issues
    sample_ids = [str(item).strip() for item in sample_payload]
    if any(not item for item in sample_ids):
        issues.append(
            _issue(
                rule_id="sample_id_empty",
                message="sample_ids must be non-empty",
                target="metrics.sample_ids",
            )
        )
    if len(set(sample_ids)) != len(sample_ids):
        issues.append(
            _issue(
                rule_id="sample_ids_not_unique",
                message="sample_ids must be unique",
                target="metrics.sample_ids",
            )
        )
    declared_sample_ids = set(sample_ids)

    gene_payload = sidecar.metrics.get("gene_labels")
    if not isinstance(gene_payload, list) or not gene_payload:
        issues.append(
            _issue(
                rule_id="gene_labels_missing",
                message="oncoplot mutation landscape requires non-empty gene_labels metrics",
                target="metrics.gene_labels",
            )
        )
        return issues
    gene_labels = [str(item).strip() for item in gene_payload]
    if any(not item for item in gene_labels):
        issues.append(
            _issue(
                rule_id="gene_label_empty",
                message="gene_labels must be non-empty",
                target="metrics.gene_labels",
            )
        )
    if len(set(gene_labels)) != len(gene_labels):
        issues.append(
            _issue(
                rule_id="gene_labels_not_unique",
                message="gene_labels must be unique",
                target="metrics.gene_labels",
            )
        )
    declared_gene_labels = set(gene_labels)

    supported_alteration_classes = {"missense", "truncating", "amplification", "fusion"}

    sample_burdens = sidecar.metrics.get("sample_burdens")
    if not isinstance(sample_burdens, list) or not sample_burdens:
        issues.append(
            _issue(
                rule_id="sample_burdens_missing",
                message="oncoplot mutation landscape requires non-empty sample_burdens metrics",
                target="metrics.sample_burdens",
            )
        )
    else:
        observed_burden_samples: set[str] = set()
        for index, item in enumerate(sample_burdens):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.sample_burdens[{index}] must be an object")
            sample_id = str(item.get("sample_id") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="sample_burden_sample_unknown",
                        message="sample_burdens must stay inside declared sample_ids",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if sample_id in observed_burden_samples:
                issues.append(
                    _issue(
                        rule_id="sample_burden_duplicate",
                        message="sample_burdens must cover each declared sample exactly once",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            observed_burden_samples.add(sample_id)
            _require_numeric(
                item.get("altered_gene_count"),
                label=f"layout_sidecar.metrics.sample_burdens[{index}].altered_gene_count",
            )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="sample_burden_box_missing",
                        message="sample_burdens bar_box_id must resolve to an existing layout box",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif burden_panel_box is not None and not _boxes_overlap(bar_box, burden_panel_box):
                issues.append(
                    _issue(
                        rule_id="sample_burden_out_of_panel",
                        message="sample burden bars must stay inside panel_burden",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, burden_panel_box.box_id),
                    )
                )
        if observed_burden_samples != declared_sample_ids:
            issues.append(
                _issue(
                    rule_id="sample_burden_coverage_mismatch",
                    message="sample_burdens must cover every declared sample exactly once",
                    target="metrics.sample_burdens",
                    observed=sorted(observed_burden_samples),
                    expected=sorted(declared_sample_ids),
                )
            )

    gene_frequencies = sidecar.metrics.get("gene_altered_frequencies")
    frequency_panel_box = panel_boxes_by_id.get("panel_frequency")
    if not isinstance(gene_frequencies, list) or not gene_frequencies:
        issues.append(
            _issue(
                rule_id="gene_altered_frequencies_missing",
                message="oncoplot mutation landscape requires non-empty gene_altered_frequencies metrics",
                target="metrics.gene_altered_frequencies",
            )
        )
    else:
        observed_frequency_genes: set[str] = set()
        for index, item in enumerate(gene_frequencies):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.gene_altered_frequencies[{index}] must be an object")
            gene_label = str(item.get("gene_label") or "").strip()
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_gene_unknown",
                        message="gene_altered_frequencies must stay inside declared gene_labels",
                        target=f"metrics.gene_altered_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            if gene_label in observed_frequency_genes:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_duplicate",
                        message="gene_altered_frequencies must cover each declared gene exactly once",
                        target=f"metrics.gene_altered_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            observed_frequency_genes.add(gene_label)
            altered_fraction = _require_numeric(
                item.get("altered_fraction"),
                label=f"layout_sidecar.metrics.gene_altered_frequencies[{index}].altered_fraction",
            )
            if altered_fraction < 0.0 or altered_fraction > 1.0:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_fraction_invalid",
                        message="altered_fraction must stay within [0, 1]",
                        target=f"metrics.gene_altered_frequencies[{index}].altered_fraction",
                        observed=altered_fraction,
                    )
                )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_box_missing",
                        message="gene_altered_frequencies bar_box_id must resolve to an existing layout box",
                        target=f"metrics.gene_altered_frequencies[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif frequency_panel_box is not None and not _boxes_overlap(bar_box, frequency_panel_box):
                issues.append(
                    _issue(
                        rule_id="gene_frequency_out_of_panel",
                        message="gene altered-frequency bars must stay inside panel_frequency",
                        target=f"metrics.gene_altered_frequencies[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, frequency_panel_box.box_id),
                    )
                )
        if observed_frequency_genes != declared_gene_labels:
            issues.append(
                _issue(
                    rule_id="gene_frequency_coverage_mismatch",
                    message="gene_altered_frequencies must cover every declared gene exactly once",
                    target="metrics.gene_altered_frequencies",
                    observed=sorted(observed_frequency_genes),
                    expected=sorted(declared_gene_labels),
                )
            )

    annotation_panel_box = panel_boxes_by_id.get("panel_annotations")
    annotation_tracks = sidecar.metrics.get("annotation_tracks")
    if not isinstance(annotation_tracks, list) or not annotation_tracks:
        issues.append(
            _issue(
                rule_id="annotation_tracks_missing",
                message="oncoplot mutation landscape requires non-empty annotation_tracks metrics",
                target="metrics.annotation_tracks",
            )
        )
    else:
        if len(annotation_tracks) > 3:
            issues.append(
                _issue(
                    rule_id="annotation_track_count_invalid",
                    message="oncoplot mutation landscape supports at most three annotation tracks",
                    target="metrics.annotation_tracks",
                    observed=len(annotation_tracks),
                )
            )
        seen_track_ids: set[str] = set()
        for index, track in enumerate(annotation_tracks):
            if not isinstance(track, dict):
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}] must be an object")
            track_id = str(track.get("track_id") or "").strip()
            if not track_id:
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}].track_id must be non-empty")
            if track_id in seen_track_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_id_not_unique",
                        message="annotation track ids must be unique",
                        target=f"metrics.annotation_tracks[{index}].track_id",
                        observed=track_id,
                    )
                )
            seen_track_ids.add(track_id)
            if not str(track.get("track_label") or "").strip():
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_invalid",
                        message="annotation track labels must be non-empty",
                        target=f"metrics.annotation_tracks[{index}].track_label",
                    )
                )
            track_label_box_id = str(track.get("track_label_box_id") or "").strip()
            track_label_box = layout_boxes_by_id.get(track_label_box_id)
            if track_label_box is None:
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_box_missing",
                        message="annotation track label box must resolve to an existing layout box",
                        target=f"metrics.annotation_tracks[{index}].track_label_box_id",
                        observed=track_label_box_id,
                    )
                )
            cells = track.get("cells")
            if not isinstance(cells, list) or not cells:
                issues.append(
                    _issue(
                        rule_id="annotation_track_cells_missing",
                        message="annotation track must expose non-empty cells metrics",
                        target=f"metrics.annotation_tracks[{index}].cells",
                    )
                )
                continue
            observed_track_samples: set[str] = set()
            for cell_index, cell in enumerate(cells):
                if not isinstance(cell, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.annotation_tracks[{index}].cells[{cell_index}] must be an object"
                    )
                sample_id = str(cell.get("sample_id") or "").strip()
                if sample_id not in declared_sample_ids:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_unknown",
                            message="annotation track cells must stay inside declared sample_ids",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                if sample_id in observed_track_samples:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_duplicate",
                            message="annotation track cells must cover each sample exactly once",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                observed_track_samples.add(sample_id)
                if not str(cell.get("category_label") or "").strip():
                    issues.append(
                        _issue(
                            rule_id="annotation_track_category_invalid",
                            message="annotation track category labels must be non-empty",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].category_label",
                        )
                    )
                box_id = str(cell.get("box_id") or "").strip()
                box = layout_boxes_by_id.get(box_id)
                if box is None:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_missing",
                            message="annotation track cell box_id must resolve to an existing layout box",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            observed=box_id,
                        )
                    )
                elif annotation_panel_box is not None and not _boxes_overlap(box, annotation_panel_box):
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_out_of_panel",
                            message="annotation track cells must stay inside panel_annotations",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            box_refs=(box.box_id, annotation_panel_box.box_id),
                        )
                    )
            if observed_track_samples != declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_coverage_mismatch",
                        message="each annotation track must cover every declared sample exactly once",
                        target=f"metrics.annotation_tracks[{index}].cells",
                        observed=sorted(observed_track_samples),
                        expected=sorted(declared_sample_ids),
                    )
                )

    matrix_panel_box = panel_boxes_by_id.get("panel_matrix")
    altered_cells = sidecar.metrics.get("altered_cells")
    if not isinstance(altered_cells, list) or not altered_cells:
        issues.append(
            _issue(
                rule_id="altered_cells_missing",
                message="oncoplot mutation landscape requires non-empty altered_cells metrics",
                target="metrics.altered_cells",
            )
        )
    else:
        observed_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(altered_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.altered_cells[{index}] must be an object")
            sample_id = str(cell.get("sample_id") or "").strip()
            gene_label = str(cell.get("gene_label") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="altered_cell_sample_unknown",
                        message="altered_cells sample ids must stay inside declared sample_ids",
                        target=f"metrics.altered_cells[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="altered_cell_gene_unknown",
                        message="altered_cells gene labels must stay inside declared gene_labels",
                        target=f"metrics.altered_cells[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            coordinate = (sample_id, gene_label)
            if coordinate in observed_coordinates:
                issues.append(
                    _issue(
                        rule_id="altered_cell_coordinate_duplicate",
                        message="altered_cells must keep sample/gene coordinates unique",
                        target=f"metrics.altered_cells[{index}]",
                        observed={"sample_id": sample_id, "gene_label": gene_label},
                    )
                )
            observed_coordinates.add(coordinate)
            alteration_class = str(cell.get("alteration_class") or "").strip()
            if alteration_class not in supported_alteration_classes:
                issues.append(
                    _issue(
                        rule_id="alteration_class_invalid",
                        message="altered_cells must use the supported alteration vocabulary",
                        target=f"metrics.altered_cells[{index}].alteration_class",
                        observed=alteration_class,
                    )
                )
            box_id = str(cell.get("box_id") or "").strip()
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="altered_cell_box_missing",
                        message="altered_cells box_id must resolve to an existing layout box",
                        target=f"metrics.altered_cells[{index}].box_id",
                        observed=box_id,
                    )
                )
            elif matrix_panel_box is not None and not _boxes_overlap(box, matrix_panel_box):
                issues.append(
                    _issue(
                        rule_id="altered_cell_box_out_of_panel",
                        message="altered mutation cells must stay inside panel_matrix",
                        target=f"metrics.altered_cells[{index}].box_id",
                        box_refs=(box.box_id, matrix_panel_box.box_id),
                    )
                )

    return issues

def _check_publication_cnv_recurrence_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "subplot_y_axis_title", "panel_label")))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    required_panel_ids = ("panel_burden", "panel_annotations", "panel_matrix", "panel_frequency")
    for panel_id in required_panel_ids:
        if panel_id not in panel_boxes_by_id:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message=f"cnv recurrence summary requires `{panel_id}` panel box",
                    target=f"panel_boxes.{panel_id}",
                    observed=sorted(panel_boxes_by_id),
                )
            )

    label_box = layout_boxes_by_id.get("panel_label_A")
    burden_panel_box = panel_boxes_by_id.get("panel_burden")
    if label_box is None:
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="cnv recurrence summary requires panel_label_A",
                target="layout_boxes.panel_label_A",
            )
        )

    cnv_legend_title = str(sidecar.metrics.get("cnv_legend_title") or "").strip()
    if not cnv_legend_title:
        issues.append(
            _issue(
                rule_id="cnv_legend_title_missing",
                message="cnv recurrence summary requires a non-empty cnv_legend_title",
                target="metrics.cnv_legend_title",
            )
        )

    sample_payload = sidecar.metrics.get("sample_ids")
    if not isinstance(sample_payload, list) or not sample_payload:
        issues.append(
            _issue(
                rule_id="sample_ids_missing",
                message="cnv recurrence summary requires non-empty sample_ids metrics",
                target="metrics.sample_ids",
            )
        )
        return issues
    sample_ids = [str(item).strip() for item in sample_payload]
    if any(not item for item in sample_ids):
        issues.append(
            _issue(
                rule_id="sample_id_empty",
                message="sample_ids must be non-empty",
                target="metrics.sample_ids",
            )
        )
    if len(set(sample_ids)) != len(sample_ids):
        issues.append(
            _issue(
                rule_id="sample_ids_not_unique",
                message="sample_ids must be unique",
                target="metrics.sample_ids",
            )
        )
    declared_sample_ids = set(sample_ids)

    region_payload = sidecar.metrics.get("region_labels")
    if not isinstance(region_payload, list) or not region_payload:
        issues.append(
            _issue(
                rule_id="region_labels_missing",
                message="cnv recurrence summary requires non-empty region_labels metrics",
                target="metrics.region_labels",
            )
        )
        return issues
    region_labels = [str(item).strip() for item in region_payload]
    if any(not item for item in region_labels):
        issues.append(
            _issue(
                rule_id="region_label_empty",
                message="region_labels must be non-empty",
                target="metrics.region_labels",
            )
        )
    if len(set(region_labels)) != len(region_labels):
        issues.append(
            _issue(
                rule_id="region_labels_not_unique",
                message="region_labels must be unique",
                target="metrics.region_labels",
            )
        )
    declared_region_labels = set(region_labels)

    supported_cnv_states = {"amplification", "gain", "loss", "deep_loss"}

    sample_burdens = sidecar.metrics.get("sample_burdens")
    if not isinstance(sample_burdens, list) or not sample_burdens:
        issues.append(
            _issue(
                rule_id="sample_burdens_missing",
                message="cnv recurrence summary requires non-empty sample_burdens metrics",
                target="metrics.sample_burdens",
            )
        )
    else:
        observed_burden_samples: set[str] = set()
        for index, item in enumerate(sample_burdens):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.sample_burdens[{index}] must be an object")
            sample_id = str(item.get("sample_id") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="sample_burden_sample_unknown",
                        message="sample_burdens must stay inside declared sample_ids",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if sample_id in observed_burden_samples:
                issues.append(
                    _issue(
                        rule_id="sample_burden_duplicate",
                        message="sample_burdens must cover each declared sample exactly once",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            observed_burden_samples.add(sample_id)
            _require_numeric(
                item.get("altered_region_count"),
                label=f"layout_sidecar.metrics.sample_burdens[{index}].altered_region_count",
            )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="sample_burden_box_missing",
                        message="sample_burdens bar_box_id must resolve to an existing layout box",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif burden_panel_box is not None and not _boxes_overlap(bar_box, burden_panel_box):
                issues.append(
                    _issue(
                        rule_id="sample_burden_out_of_panel",
                        message="sample burden bars must stay inside panel_burden",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, burden_panel_box.box_id),
                    )
                )
        if observed_burden_samples != declared_sample_ids:
            issues.append(
                _issue(
                    rule_id="sample_burden_coverage_mismatch",
                    message="sample_burdens must cover every declared sample exactly once",
                    target="metrics.sample_burdens",
                    observed=sorted(observed_burden_samples),
                    expected=sorted(declared_sample_ids),
                )
            )

    region_frequencies = sidecar.metrics.get("region_gain_loss_frequencies")
    frequency_panel_box = panel_boxes_by_id.get("panel_frequency")
    if not isinstance(region_frequencies, list) or not region_frequencies:
        issues.append(
            _issue(
                rule_id="region_gain_loss_frequencies_missing",
                message="cnv recurrence summary requires non-empty region_gain_loss_frequencies metrics",
                target="metrics.region_gain_loss_frequencies",
            )
        )
    else:
        observed_frequency_regions: set[str] = set()
        for index, item in enumerate(region_frequencies):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.region_gain_loss_frequencies[{index}] must be an object")
            region_label = str(item.get("region_label") or "").strip()
            if region_label not in declared_region_labels:
                issues.append(
                    _issue(
                        rule_id="region_frequency_region_unknown",
                        message="region_gain_loss_frequencies must stay inside declared region_labels",
                        target=f"metrics.region_gain_loss_frequencies[{index}].region_label",
                        observed=region_label,
                    )
                )
            if region_label in observed_frequency_regions:
                issues.append(
                    _issue(
                        rule_id="region_frequency_duplicate",
                        message="region_gain_loss_frequencies must cover each declared region exactly once",
                        target=f"metrics.region_gain_loss_frequencies[{index}].region_label",
                        observed=region_label,
                    )
                )
            observed_frequency_regions.add(region_label)
            for field_name in ("gain_fraction", "loss_fraction"):
                fraction_value = _require_numeric(
                    item.get(field_name),
                    label=f"layout_sidecar.metrics.region_gain_loss_frequencies[{index}].{field_name}",
                )
                if fraction_value < 0.0 or fraction_value > 1.0:
                    issues.append(
                        _issue(
                            rule_id="region_frequency_fraction_invalid",
                            message=f"{field_name} must stay within [0, 1]",
                            target=f"metrics.region_gain_loss_frequencies[{index}].{field_name}",
                            observed=fraction_value,
                        )
                    )
            for field_name in ("gain_bar_box_id", "loss_bar_box_id"):
                bar_box_id = str(item.get(field_name) or "").strip()
                bar_box = layout_boxes_by_id.get(bar_box_id)
                if bar_box is None:
                    issues.append(
                        _issue(
                            rule_id="region_frequency_box_missing",
                            message="region gain/loss bar boxes must resolve to existing layout boxes",
                            target=f"metrics.region_gain_loss_frequencies[{index}].{field_name}",
                            observed=bar_box_id,
                        )
                    )
                elif frequency_panel_box is not None and not _boxes_overlap(bar_box, frequency_panel_box):
                    issues.append(
                        _issue(
                            rule_id="region_frequency_out_of_panel",
                            message="region gain/loss frequency bars must stay inside panel_frequency",
                            target=f"metrics.region_gain_loss_frequencies[{index}].{field_name}",
                            box_refs=(bar_box.box_id, frequency_panel_box.box_id),
                        )
                    )
        if observed_frequency_regions != declared_region_labels:
            issues.append(
                _issue(
                    rule_id="region_frequency_coverage_mismatch",
                    message="region_gain_loss_frequencies must cover every declared region exactly once",
                    target="metrics.region_gain_loss_frequencies",
                    observed=sorted(observed_frequency_regions),
                    expected=sorted(declared_region_labels),
                )
            )

    annotation_panel_box = panel_boxes_by_id.get("panel_annotations")
    annotation_tracks = sidecar.metrics.get("annotation_tracks")
    if not isinstance(annotation_tracks, list) or not annotation_tracks:
        issues.append(
            _issue(
                rule_id="annotation_tracks_missing",
                message="cnv recurrence summary requires non-empty annotation_tracks metrics",
                target="metrics.annotation_tracks",
            )
        )
    else:
        if len(annotation_tracks) > 3:
            issues.append(
                _issue(
                    rule_id="annotation_track_count_invalid",
                    message="cnv recurrence summary supports at most three annotation tracks",
                    target="metrics.annotation_tracks",
                    observed=len(annotation_tracks),
                )
            )
        seen_track_ids: set[str] = set()
        for index, track in enumerate(annotation_tracks):
            if not isinstance(track, dict):
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}] must be an object")
            track_id = str(track.get("track_id") or "").strip()
            if not track_id:
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}].track_id must be non-empty")
            if track_id in seen_track_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_id_not_unique",
                        message="annotation track ids must be unique",
                        target=f"metrics.annotation_tracks[{index}].track_id",
                        observed=track_id,
                    )
                )
            seen_track_ids.add(track_id)
            if not str(track.get("track_label") or "").strip():
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_invalid",
                        message="annotation track labels must be non-empty",
                        target=f"metrics.annotation_tracks[{index}].track_label",
                    )
                )
            track_label_box_id = str(track.get("track_label_box_id") or "").strip()
            track_label_box = layout_boxes_by_id.get(track_label_box_id)
            if track_label_box is None:
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_box_missing",
                        message="annotation track label box must resolve to an existing layout box",
                        target=f"metrics.annotation_tracks[{index}].track_label_box_id",
                        observed=track_label_box_id,
                    )
                )
            cells = track.get("cells")
            if not isinstance(cells, list) or not cells:
                issues.append(
                    _issue(
                        rule_id="annotation_track_cells_missing",
                        message="annotation track must expose non-empty cells metrics",
                        target=f"metrics.annotation_tracks[{index}].cells",
                    )
                )
                continue
            observed_track_samples: set[str] = set()
            for cell_index, cell in enumerate(cells):
                if not isinstance(cell, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.annotation_tracks[{index}].cells[{cell_index}] must be an object"
                    )
                sample_id = str(cell.get("sample_id") or "").strip()
                if sample_id not in declared_sample_ids:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_unknown",
                            message="annotation track cells must stay inside declared sample_ids",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                if sample_id in observed_track_samples:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_duplicate",
                            message="annotation track cells must cover each sample exactly once",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                observed_track_samples.add(sample_id)
                if not str(cell.get("category_label") or "").strip():
                    issues.append(
                        _issue(
                            rule_id="annotation_track_category_invalid",
                            message="annotation track category labels must be non-empty",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].category_label",
                        )
                    )
                box_id = str(cell.get("box_id") or "").strip()
                box = layout_boxes_by_id.get(box_id)
                if box is None:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_missing",
                            message="annotation track cell box_id must resolve to an existing layout box",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            observed=box_id,
                        )
                    )
                elif annotation_panel_box is not None and not _boxes_overlap(box, annotation_panel_box):
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_out_of_panel",
                            message="annotation track cells must stay inside panel_annotations",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            box_refs=(box.box_id, annotation_panel_box.box_id),
                        )
                    )
            if observed_track_samples != declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_coverage_mismatch",
                        message="each annotation track must cover every declared sample exactly once",
                        target=f"metrics.annotation_tracks[{index}].cells",
                        observed=sorted(observed_track_samples),
                        expected=sorted(declared_sample_ids),
                    )
                )

    matrix_panel_box = panel_boxes_by_id.get("panel_matrix")
    cnv_cells = sidecar.metrics.get("cnv_cells")
    if not isinstance(cnv_cells, list) or not cnv_cells:
        issues.append(
            _issue(
                rule_id="cnv_cells_missing",
                message="cnv recurrence summary requires non-empty cnv_cells metrics",
                target="metrics.cnv_cells",
            )
        )
    else:
        observed_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(cnv_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.cnv_cells[{index}] must be an object")
            sample_id = str(cell.get("sample_id") or "").strip()
            region_label = str(cell.get("region_label") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_sample_unknown",
                        message="cnv_cells sample ids must stay inside declared sample_ids",
                        target=f"metrics.cnv_cells[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if region_label not in declared_region_labels:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_region_unknown",
                        message="cnv_cells region labels must stay inside declared region_labels",
                        target=f"metrics.cnv_cells[{index}].region_label",
                        observed=region_label,
                    )
                )
            coordinate = (sample_id, region_label)
            if coordinate in observed_coordinates:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_coordinate_duplicate",
                        message="cnv_cells must keep sample/region coordinates unique",
                        target=f"metrics.cnv_cells[{index}]",
                        observed={"sample_id": sample_id, "region_label": region_label},
                    )
                )
            observed_coordinates.add(coordinate)
            cnv_state = str(cell.get("cnv_state") or "").strip()
            if cnv_state not in supported_cnv_states:
                issues.append(
                    _issue(
                        rule_id="cnv_state_invalid",
                        message="cnv_cells must use the supported cnv_state vocabulary",
                        target=f"metrics.cnv_cells[{index}].cnv_state",
                        observed=cnv_state,
                    )
                )
            box_id = str(cell.get("box_id") or "").strip()
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_box_missing",
                        message="cnv_cells box_id must resolve to an existing layout box",
                        target=f"metrics.cnv_cells[{index}].box_id",
                        observed=box_id,
                    )
                )
            elif matrix_panel_box is not None and not _boxes_overlap(box, matrix_panel_box):
                issues.append(
                    _issue(
                        rule_id="cnv_cell_box_out_of_panel",
                        message="cnv cells must stay inside panel_matrix",
                        target=f"metrics.cnv_cells[{index}].box_id",
                        box_refs=(box.box_id, matrix_panel_box.box_id),
                    )
                )

    return issues
