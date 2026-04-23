from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_legend_panel_overlap,
    _check_required_box_types,
    _issue,
    _point_within_box,
    _require_non_empty_text,
    _require_numeric,
)

def _check_publication_genomic_alteration_landscape_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
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
                    message=f"genomic alteration landscape requires `{panel_id}` panel box",
                    target=f"panel_boxes.{panel_id}",
                    observed=sorted(panel_boxes_by_id),
                )
            )

    if layout_boxes_by_id.get("panel_label_A") is None:
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="genomic alteration landscape requires panel_label_A",
                target="layout_boxes.panel_label_A",
            )
        )

    alteration_legend_title = str(sidecar.metrics.get("alteration_legend_title") or "").strip()
    if not alteration_legend_title:
        issues.append(
            _issue(
                rule_id="alteration_legend_title_missing",
                message="genomic alteration landscape requires a non-empty alteration_legend_title",
                target="metrics.alteration_legend_title",
            )
        )

    sample_payload = sidecar.metrics.get("sample_ids")
    if not isinstance(sample_payload, list) or not sample_payload:
        issues.append(
            _issue(
                rule_id="sample_ids_missing",
                message="genomic alteration landscape requires non-empty sample_ids metrics",
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
                message="genomic alteration landscape requires non-empty gene_labels metrics",
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

    burden_panel_box = panel_boxes_by_id.get("panel_burden")
    sample_burdens = sidecar.metrics.get("sample_burdens")
    if not isinstance(sample_burdens, list) or not sample_burdens:
        issues.append(
            _issue(
                rule_id="sample_burdens_missing",
                message="genomic alteration landscape requires non-empty sample_burdens metrics",
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

    frequency_panel_box = panel_boxes_by_id.get("panel_frequency")
    gene_frequencies = sidecar.metrics.get("gene_alteration_frequencies")
    if not isinstance(gene_frequencies, list) or not gene_frequencies:
        issues.append(
            _issue(
                rule_id="gene_alteration_frequencies_missing",
                message="genomic alteration landscape requires non-empty gene_alteration_frequencies metrics",
                target="metrics.gene_alteration_frequencies",
            )
        )
    else:
        observed_frequency_genes: set[str] = set()
        for index, item in enumerate(gene_frequencies):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.gene_alteration_frequencies[{index}] must be an object")
            gene_label = str(item.get("gene_label") or "").strip()
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_gene_unknown",
                        message="gene_alteration_frequencies must stay inside declared gene_labels",
                        target=f"metrics.gene_alteration_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            if gene_label in observed_frequency_genes:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_duplicate",
                        message="gene_alteration_frequencies must cover each declared gene exactly once",
                        target=f"metrics.gene_alteration_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            observed_frequency_genes.add(gene_label)
            altered_fraction = _require_numeric(
                item.get("altered_fraction"),
                label=f"layout_sidecar.metrics.gene_alteration_frequencies[{index}].altered_fraction",
            )
            if altered_fraction < 0.0 or altered_fraction > 1.0:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_fraction_invalid",
                        message="altered_fraction must stay within [0, 1]",
                        target=f"metrics.gene_alteration_frequencies[{index}].altered_fraction",
                        observed=altered_fraction,
                    )
                )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_box_missing",
                        message="gene_alteration_frequencies bar_box_id must resolve to an existing layout box",
                        target=f"metrics.gene_alteration_frequencies[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif frequency_panel_box is not None and not _boxes_overlap(bar_box, frequency_panel_box):
                issues.append(
                    _issue(
                        rule_id="gene_frequency_out_of_panel",
                        message="gene alteration-frequency bars must stay inside panel_frequency",
                        target=f"metrics.gene_alteration_frequencies[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, frequency_panel_box.box_id),
                    )
                )
        if observed_frequency_genes != declared_gene_labels:
            issues.append(
                _issue(
                    rule_id="gene_frequency_coverage_mismatch",
                    message="gene_alteration_frequencies must cover every declared gene exactly once",
                    target="metrics.gene_alteration_frequencies",
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
                message="genomic alteration landscape requires non-empty annotation_tracks metrics",
                target="metrics.annotation_tracks",
            )
        )
    else:
        if len(annotation_tracks) > 3:
            issues.append(
                _issue(
                    rule_id="annotation_track_count_invalid",
                    message="genomic alteration landscape supports at most three annotation tracks",
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
    alteration_cells = sidecar.metrics.get("alteration_cells")
    if not isinstance(alteration_cells, list) or not alteration_cells:
        issues.append(
            _issue(
                rule_id="alteration_cells_missing",
                message="genomic alteration landscape requires non-empty alteration_cells metrics",
                target="metrics.alteration_cells",
            )
        )
    else:
        supported_mutation_classes = {"missense", "truncating", "fusion"}
        supported_cnv_states = {"amplification", "gain", "loss", "deep_loss"}
        observed_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(alteration_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.alteration_cells[{index}] must be an object")
            sample_id = str(cell.get("sample_id") or "").strip()
            gene_label = str(cell.get("gene_label") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_sample_unknown",
                        message="alteration_cells sample ids must stay inside declared sample_ids",
                        target=f"metrics.alteration_cells[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_gene_unknown",
                        message="alteration_cells gene labels must stay inside declared gene_labels",
                        target=f"metrics.alteration_cells[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            coordinate = (sample_id, gene_label)
            if coordinate in observed_coordinates:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_coordinate_duplicate",
                        message="alteration_cells must keep sample/gene coordinates unique",
                        target=f"metrics.alteration_cells[{index}]",
                        observed={"sample_id": sample_id, "gene_label": gene_label},
                    )
                )
            observed_coordinates.add(coordinate)

            mutation_class = str(cell.get("mutation_class") or "").strip()
            cnv_state = str(cell.get("cnv_state") or "").strip()
            if not mutation_class and not cnv_state:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_state_missing",
                        message="alteration_cells must define mutation_class or cnv_state",
                        target=f"metrics.alteration_cells[{index}]",
                    )
                )
            if mutation_class and mutation_class not in supported_mutation_classes:
                issues.append(
                    _issue(
                        rule_id="mutation_class_invalid",
                        message="alteration_cells mutation_class must use the supported mutation vocabulary",
                        target=f"metrics.alteration_cells[{index}].mutation_class",
                        observed=mutation_class,
                    )
                )
            if cnv_state and cnv_state not in supported_cnv_states:
                issues.append(
                    _issue(
                        rule_id="cnv_state_invalid",
                        message="alteration_cells cnv_state must use the supported cnv vocabulary",
                        target=f"metrics.alteration_cells[{index}].cnv_state",
                        observed=cnv_state,
                    )
                )
            box_id = str(cell.get("box_id") or "").strip()
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_box_missing",
                        message="alteration_cells box_id must resolve to an existing layout box",
                        target=f"metrics.alteration_cells[{index}].box_id",
                        observed=box_id,
                    )
                )
            elif matrix_panel_box is not None and not _boxes_overlap(box, matrix_panel_box):
                issues.append(
                    _issue(
                        rule_id="alteration_cell_box_out_of_panel",
                        message="alteration cells must stay inside panel_matrix",
                        target=f"metrics.alteration_cells[{index}].box_id",
                        box_refs=(box.box_id, matrix_panel_box.box_id),
                    )
                )
            overlay_box_id = str(cell.get("overlay_box_id") or "").strip()
            if overlay_box_id:
                overlay_box = layout_boxes_by_id.get(overlay_box_id)
                if overlay_box is None:
                    issues.append(
                        _issue(
                            rule_id="alteration_overlay_box_missing",
                            message="overlay_box_id must resolve to an existing layout box",
                            target=f"metrics.alteration_cells[{index}].overlay_box_id",
                            observed=overlay_box_id,
                        )
                    )
                else:
                    if matrix_panel_box is not None and not _boxes_overlap(overlay_box, matrix_panel_box):
                        issues.append(
                            _issue(
                                rule_id="alteration_overlay_out_of_panel",
                                message="alteration overlays must stay inside panel_matrix",
                                target=f"metrics.alteration_cells[{index}].overlay_box_id",
                                box_refs=(overlay_box.box_id, matrix_panel_box.box_id),
                            )
                        )
                    if box is not None and not _boxes_overlap(overlay_box, box):
                        issues.append(
                            _issue(
                                rule_id="alteration_overlay_detached",
                                message="alteration overlays must stay attached to their parent alteration cell",
                                target=f"metrics.alteration_cells[{index}].overlay_box_id",
                                box_refs=(overlay_box.box_id, box.box_id),
                            )
                        )

    return issues

def _check_publication_genomic_alteration_consequence_panel(
    sidecar: LayoutSidecar,
    *,
    max_panel_count: int = 2,
    required_panel_ids: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    issues = _check_publication_genomic_alteration_landscape_panel(sidecar)
    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_boxes_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    legend_boxes = [box for box in sidecar.guide_boxes if box.box_type == "legend"]
    if len(legend_boxes) < 2:
        issues.append(
            _issue(
                rule_id="legend_count_invalid",
                message="genomic alteration consequence panel requires separate alteration and consequence legends",
                target="guide_boxes",
                observed=len(legend_boxes),
                expected=">= 2",
            )
        )

    consequence_legend_title = str(sidecar.metrics.get("consequence_legend_title") or "").strip()
    if not consequence_legend_title:
        issues.append(
            _issue(
                rule_id="consequence_legend_title_missing",
                message="genomic alteration consequence panel requires a non-empty consequence_legend_title",
                target="metrics.consequence_legend_title",
            )
        )

    effect_threshold = _require_numeric(sidecar.metrics.get("effect_threshold"), label="layout_sidecar.metrics.effect_threshold")
    if effect_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="effect_threshold_invalid",
                message="effect_threshold must be positive",
                target="metrics.effect_threshold",
                observed=effect_threshold,
            )
        )
    significance_threshold = _require_numeric(
        sidecar.metrics.get("significance_threshold"),
        label="layout_sidecar.metrics.significance_threshold",
    )
    if significance_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="significance_threshold_invalid",
                message="significance_threshold must be positive",
                target="metrics.significance_threshold",
                observed=significance_threshold,
            )
        )

    gene_payload = sidecar.metrics.get("gene_labels")
    declared_gene_labels = {
        str(item).strip()
        for item in gene_payload
        if isinstance(gene_payload, list) and str(item).strip()
    }
    driver_gene_payload = sidecar.metrics.get("driver_gene_labels")
    if not isinstance(driver_gene_payload, list) or not driver_gene_payload:
        issues.append(
            _issue(
                rule_id="driver_gene_labels_missing",
                message="genomic alteration consequence panel requires non-empty driver_gene_labels metrics",
                target="metrics.driver_gene_labels",
            )
        )
        return issues
    driver_gene_labels = [str(item).strip() for item in driver_gene_payload]
    if any(not item for item in driver_gene_labels):
        issues.append(
            _issue(
                rule_id="driver_gene_label_invalid",
                message="driver_gene_labels must be non-empty",
                target="metrics.driver_gene_labels",
            )
        )
    if len(set(driver_gene_labels)) != len(driver_gene_labels):
        issues.append(
            _issue(
                rule_id="driver_gene_labels_not_unique",
                message="driver_gene_labels must be unique",
                target="metrics.driver_gene_labels",
            )
        )
    if declared_gene_labels and not set(driver_gene_labels).issubset(declared_gene_labels):
        issues.append(
            _issue(
                rule_id="driver_gene_labels_outside_gene_order",
                message="driver_gene_labels must stay inside gene_labels",
                target="metrics.driver_gene_labels",
                observed=sorted(set(driver_gene_labels) - declared_gene_labels),
            )
        )

    consequence_panels = sidecar.metrics.get("consequence_panels")
    if not isinstance(consequence_panels, list) or not consequence_panels:
        issues.append(
            _issue(
                rule_id="consequence_panels_missing",
                message="genomic alteration consequence panel requires non-empty consequence_panels metrics",
                target="metrics.consequence_panels",
            )
        )
        return issues
    if len(consequence_panels) > max_panel_count:
        issues.append(
            _issue(
                rule_id="consequence_panel_count_invalid",
                message=f"genomic alteration consequence panel supports at most {max_panel_count} consequence panels",
                target="metrics.consequence_panels",
                observed=len(consequence_panels),
            )
        )

    supported_regulation_classes = {"upregulated", "downregulated", "background"}
    seen_panel_ids: set[str] = set()
    expected_coordinates: set[tuple[str, str]] = set()
    observed_coordinates: set[tuple[str, str]] = set()

    for panel_index, payload in enumerate(consequence_panels):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.consequence_panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_text(
            payload.get("panel_id"),
            label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="consequence_panel_id_not_unique",
                    message="consequence panel ids must be unique",
                    target=f"metrics.consequence_panels[{panel_index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)
        expected_coordinates.update((panel_id, gene_label) for gene_label in driver_gene_labels)

        panel_box_id = _require_non_empty_text(
            payload.get("panel_box_id"),
            label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].panel_box_id",
        )
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="consequence_panel_box_missing",
                    message="panel_box_id must resolve to an existing consequence panel box",
                    target=f"metrics.consequence_panels[{panel_index}].panel_box_id",
                    observed=panel_box_id,
                )
            )

        panel_label_box_id = _require_non_empty_text(
            payload.get("panel_label_box_id"),
            label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].panel_label_box_id",
        )
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="consequence_panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.consequence_panels[{panel_index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="consequence_panel_label_anchor_drift",
                    message="consequence panel label must stay anchored inside its panel",
                    target=f"metrics.consequence_panels[{panel_index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )

        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].{field_name}",
            )
            if box_id not in layout_boxes_by_id:
                issues.append(
                    _issue(
                        rule_id="consequence_layout_box_missing",
                        message=f"{field_name} must resolve to an existing layout box",
                        target=f"metrics.consequence_panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )

        threshold_pairs = (
            ("effect_threshold_left_box_id", "consequence_threshold_box_missing", "consequence_threshold_outside_panel"),
            ("effect_threshold_right_box_id", "consequence_threshold_box_missing", "consequence_threshold_outside_panel"),
            (
                "significance_threshold_box_id",
                "consequence_significance_box_missing",
                "consequence_significance_outside_panel",
            ),
        )
        for field_name, missing_rule_id, outside_rule_id in threshold_pairs:
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].{field_name}",
            )
            threshold_box = guide_boxes_by_id.get(box_id)
            if threshold_box is None:
                issues.append(
                    _issue(
                        rule_id=missing_rule_id,
                        message=f"{field_name} must resolve to an existing guide box",
                        target=f"metrics.consequence_panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )
                continue
            if panel_box is not None and not _box_within_box(threshold_box, panel_box):
                issues.append(
                    _issue(
                        rule_id=outside_rule_id,
                        message=f"{field_name} must stay within its consequence panel",
                        target=f"guide_boxes.{threshold_box.box_id}",
                        box_refs=(threshold_box.box_id, panel_box.box_id),
                    )
                )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="consequence_points_missing",
                    message="every consequence panel must expose non-empty points metrics",
                    target=f"metrics.consequence_panels[{panel_index}].points",
                )
            )
            continue

        seen_panel_gene_labels: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}] must be an object"
                )
            gene_label = _require_non_empty_text(
                point.get("gene_label"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].gene_label",
            )
            if gene_label in seen_panel_gene_labels:
                issues.append(
                    _issue(
                        rule_id="consequence_point_gene_label_duplicate",
                        message="gene_label must be unique within each consequence panel",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].gene_label",
                        observed=gene_label,
                    )
                )
            seen_panel_gene_labels.add(gene_label)
            observed_coordinates.add((panel_id, gene_label))
            if gene_label not in set(driver_gene_labels):
                issues.append(
                    _issue(
                        rule_id="consequence_point_gene_unknown",
                        message="consequence points must stay inside declared driver_gene_labels",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].gene_label",
                        observed=gene_label,
                    )
                )
            point_x = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].x",
            )
            point_y = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].effect_value",
            )
            significance_value = _require_numeric(
                point.get("significance_value"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].significance_value",
            )
            if significance_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="consequence_significance_value_negative",
                        message="consequence significance_value must be non-negative",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].significance_value",
                        observed=significance_value,
                    )
                )
            regulation_class = _require_non_empty_text(
                point.get("regulation_class"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].regulation_class",
            )
            if regulation_class not in supported_regulation_classes:
                issues.append(
                    _issue(
                        rule_id="consequence_regulation_class_invalid",
                        message="consequence regulation_class must use the supported vocabulary",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].regulation_class",
                        observed=regulation_class,
                        expected=sorted(supported_regulation_classes),
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=point_x, y=point_y):
                issues.append(
                    _issue(
                        rule_id="consequence_point_outside_panel",
                        message="consequence point coordinates must stay within the panel bounds",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )

            point_box_id = _require_non_empty_text(
                point.get("point_box_id"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].point_box_id",
            )
            point_box = layout_boxes_by_id.get(point_box_id)
            if point_box is None:
                issues.append(
                    _issue(
                        rule_id="consequence_point_box_missing",
                        message="point_box_id must resolve to an existing layout box",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].point_box_id",
                        observed=point_box_id,
                    )
                )
            elif panel_box is not None and not _box_within_box(point_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="consequence_point_box_outside_panel",
                        message="consequence point boxes must stay within the panel bounds",
                        target=f"layout_boxes.{point_box.box_id}",
                        box_refs=(point_box.box_id, panel_box.box_id),
                    )
                )

            label_box_id = str(point.get("label_box_id") or "").strip()
            if label_box_id:
                label_box = layout_boxes_by_id.get(label_box_id)
                if label_box is None:
                    issues.append(
                        _issue(
                            rule_id="consequence_label_box_missing",
                            message="label_box_id must resolve to an existing layout box",
                            target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].label_box_id",
                            observed=label_box_id,
                        )
                    )
                elif panel_box is not None and not _box_within_box(label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="consequence_label_box_outside_panel",
                            message="consequence label boxes must stay within the panel bounds",
                            target=f"layout_boxes.{label_box.box_id}",
                            box_refs=(label_box.box_id, panel_box.box_id),
                        )
                    )

    if observed_coordinates != expected_coordinates:
        issues.append(
            _issue(
                rule_id="consequence_point_coverage_mismatch",
                message="consequence points must cover every declared panel/driver gene coordinate exactly once",
                target="metrics.consequence_panels",
                observed=sorted(observed_coordinates),
                expected=sorted(expected_coordinates),
            )
        )

    if required_panel_ids is not None and seen_panel_ids != set(required_panel_ids):
        issues.append(
            _issue(
                rule_id="consequence_panel_ids_invalid",
                message="consequence panel ids must match the declared multiomic layer vocabulary",
                target="metrics.consequence_panels",
                observed=sorted(seen_panel_ids),
                expected=sorted(required_panel_ids),
            )
        )

    return issues
