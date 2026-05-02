from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from ..shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _require_non_negative_int,
    _require_numeric_value,
    _wrap_figure_title_to_width,
    dump_json,
)

TEXT_COLOR = "#383735"
GRID_COLOR = "#D8D1C7"
MIST_STONE = "#8A9199"
SAGE_CLAY = "#7F8F84"
SAGE_SOFT = "#B7A99A"
DUST_ROSE = "#B88C8C"
MIST_LIGHT = "#F3EEE8"
SAGE_LIGHT = "#E7E1D6"
NA_COLOR = "#EFE9E1"

_GAP_FIELDS: tuple[tuple[str, str], ...] = (
    ("severe_glycemia_low_intensity_gap_rate", "Severe glycemia\nlow-intensity"),
    ("uncontrolled_glycemia_no_drug_gap_rate", "Uncontrolled glycemia\nno drug"),
    ("hypertension_no_antihypertensive_gap_rate", "Hypertension\nno antihypertensive"),
    ("dyslipidemia_no_lipid_lowering_gap_rate", "Dyslipidemia\nno lipid-lowering"),
)
_GAP_COUNT_FIELDS: tuple[tuple[str, str], ...] = (
    ("severe_glycemia_low_intensity_gap_patients", "Severe glycemia\nlow-intensity"),
    ("uncontrolled_glycemia_no_drug_gap_patients", "Uncontrolled glycemia\nno drug"),
    ("hypertension_no_antihypertensive_gap_patients", "Hypertension\nno antihypertensive"),
    ("dyslipidemia_no_lipid_lowering_gap_patients", "Dyslipidemia\nno lipid-lowering"),
)
_F4_PANEL_COLORS: tuple[str, ...] = (DUST_ROSE, MIST_STONE, SAGE_CLAY, SAGE_SOFT)


def _coerce_probability(value: object, *, label: str) -> float | None:
    if value is None:
        return None
    numeric = _require_numeric_value(value, label=label)
    if numeric < 0.0 or numeric > 1.0:
        raise ValueError(f"{label} must be between 0 and 1")
    return numeric


def _collect_render_context(display_payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    layout_override = dict(render_context.get("layout_override") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    return typography, palette, layout_override, style_roles


def _normalize_colors(style_roles: dict[str, Any], palette: dict[str, Any]) -> dict[str, str]:
    primary = str(style_roles.get("model_curve") or SAGE_CLAY).strip() or SAGE_CLAY
    secondary = str(style_roles.get("comparator_curve") or MIST_STONE).strip() or MIST_STONE
    accent = str(style_roles.get("highlight_fill") or DUST_ROSE).strip() or DUST_ROSE
    primary_soft = str(palette.get("primary_soft") or MIST_LIGHT).strip() or MIST_LIGHT
    secondary_soft = str(palette.get("secondary_soft") or SAGE_LIGHT).strip() or SAGE_LIGHT
    return {
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "primary_soft": primary_soft,
        "secondary_soft": secondary_soft,
    }


def _figure_title(
    *,
    figure: plt.Figure,
    display_payload: dict[str, Any],
    title_size: float,
    show_figure_title: bool,
) -> tuple[Any | None, int]:
    if not show_figure_title:
        return None, 0
    title_text = str(display_payload.get("title") or "").strip()
    if not title_text:
        return None, 0
    wrapped_title, title_line_count = _wrap_figure_title_to_width(
        title_text,
        max_width_pt=figure.get_figwidth() * 72.0 * 0.92,
        font_size=title_size,
    )
    title_artist = figure.suptitle(
        wrapped_title,
        fontsize=title_size,
        fontweight="bold",
        color="#13293d",
        y=0.985,
    )
    return title_artist, title_line_count


def _panel_label_artist(*, axes, label: str, panel_label_size: float):
    return axes.text(
        -0.10,
        1.04,
        label,
        transform=axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color="#2F3437",
        va="bottom",
    )


def _append_text_box(*, layout_boxes: list[dict[str, Any]], figure: plt.Figure, renderer, artist, box_id: str, box_type: str) -> None:
    text = getattr(artist, "get_text", lambda: "")()
    if isinstance(text, str) and not text.strip():
        return
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=figure,
            bbox=artist.get_window_extent(renderer=renderer),
            box_id=box_id,
            box_type=box_type,
        )
    )


def _dump_sidecar(
    *,
    template_id: str,
    figure: plt.Figure,
    renderer,
    layout_boxes: list[dict[str, Any]],
    panel_boxes: list[dict[str, Any]],
    guide_boxes: list[dict[str, Any]],
    metrics: dict[str, Any],
    layout_sidecar_path: Path,
) -> None:
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": metrics,
        },
    )


def _render_python_phenotype_gap_structure_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    rows_payload = list(display_payload.get("rows") or [])
    if not rows_payload:
        raise RuntimeError(f"{template_id} requires non-empty rows")
    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    typography, palette, layout_override, style_roles = _collect_render_context(display_payload)
    colors = _normalize_colors(style_roles, palette)
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", True)

    normalized_rows: list[dict[str, Any]] = []
    labels: list[str] = []
    shares_pct: list[float] = []
    heatmap_rows: list[list[float]] = []
    for gap_key, _ in _GAP_FIELDS:
        heatmap_row: list[float] = []
        for row_index, row in enumerate(rows_payload):
            if not isinstance(row, dict):
                raise RuntimeError(f"{template_id} rows[{row_index}] must be an object")
            if gap_key == _GAP_FIELDS[0][0]:
                label = _require_non_empty_string(
                    row.get("phenotype_label"),
                    label=f"{template_id} rows[{row_index}].phenotype_label",
                )
                labels.append(label)
                share = _coerce_probability(
                    row.get("share_of_index_patients"),
                    label=f"{template_id} rows[{row_index}].share_of_index_patients",
                )
                if share is None:
                    raise RuntimeError(f"{template_id} rows[{row_index}].share_of_index_patients is required")
                shares_pct.append(share * 100.0)
                normalized_rows.append(
                    {
                        "phenotype_label": label,
                        "share_of_index_patients": share,
                    }
                )
            gap_value = _coerce_probability(
                row.get(gap_key),
                label=f"{template_id} rows[{row_index}].{gap_key}",
            )
            normalized_rows[row_index][gap_key] = gap_value
            heatmap_row.append(np.nan if gap_value is None else gap_value * 100.0)
        heatmap_rows.append(heatmap_row)

    heatmap = np.array(heatmap_rows, dtype=float)
    figure = plt.figure(figsize=(13.2, 6.4))
    figure.patch.set_facecolor("white")
    title_artist, title_line_count = _figure_title(
        figure=figure,
        display_payload=display_payload,
        title_size=title_size,
        show_figure_title=show_figure_title,
    )
    grid = figure.add_gridspec(1, 2, width_ratios=[0.90, 1.45], wspace=0.24)
    composition_axes = figure.add_subplot(grid[0, 0])
    gap_axes = figure.add_subplot(grid[0, 1])

    y_positions = np.arange(len(labels))
    composition_axes.barh(
        y_positions,
        shares_pct,
        color=colors["secondary"],
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    composition_axes.set_yticks(y_positions)
    composition_axes.set_yticklabels(labels)
    composition_axes.invert_yaxis()
    composition_axes.set_xlabel("Share of index cohort (%)", fontsize=axis_title_size, color="#13293d")
    composition_axes.set_ylabel("Phenotype", fontsize=axis_title_size, color="#13293d")
    composition_title_artist = composition_axes.set_title(
        str(display_payload.get("composition_panel_title") or "Phenotype composition").strip(),
        loc="left",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
    )
    composition_axes.xaxis.grid(True, linestyle="--", linewidth=0.7, color=GRID_COLOR, zorder=0)
    _apply_publication_axes_style(composition_axes)

    heatmap_cmap = LinearSegmentedColormap.from_list(
        "dpcc_gap_heatmap",
        [colors["primary_soft"], colors["secondary_soft"], colors["primary"]],
    )
    heatmap_cmap.set_bad(NA_COLOR)
    heatmap_image = gap_axes.imshow(heatmap, aspect="auto", cmap=heatmap_cmap, vmin=0.0, vmax=100.0)
    gap_axes.set_xticks(np.arange(len(labels)))
    gap_axes.set_xticklabels(labels, rotation=25, ha="right")
    gap_axes.set_yticks(np.arange(len(_GAP_FIELDS)))
    gap_axes.set_yticklabels([label for _, label in _GAP_FIELDS])
    gap_axes.set_title(
        str(display_payload.get("heatmap_panel_title") or "Within-phenotype gap rates").strip(),
        loc="left",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
    )
    for row_index in range(heatmap.shape[0]):
        for col_index in range(heatmap.shape[1]):
            value = heatmap[row_index, col_index]
            label = "NA" if np.isnan(value) else f"{value:.1f}%"
            gap_axes.text(col_index, row_index, label, ha="center", va="center", fontsize=max(tick_size - 1.5, 8.0), color=TEXT_COLOR)
    colorbar = figure.colorbar(heatmap_image, ax=gap_axes, fraction=0.046, pad=0.02)
    colorbar.set_label(
        str(display_payload.get("heatmap_scale_label") or "Gap rate (%)").strip() or "Gap rate (%)",
        fontsize=axis_title_size,
    )

    panel_a_artist = _panel_label_artist(axes=composition_axes, label="A", panel_label_size=panel_label_size)
    panel_b_artist = _panel_label_artist(axes=gap_axes, label="B", panel_label_size=panel_label_size)
    top_margin = 0.86 - 0.06 * max(title_line_count - 1, 0) if title_artist is not None else 0.92
    figure.subplots_adjust(left=0.08, right=0.96, top=max(0.72, top_margin), bottom=0.16, wspace=0.24)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    for artist, box_id, box_type in (
        (title_artist, "title", "title"),
        (panel_a_artist, "panel_label_A", "panel_label"),
        (panel_b_artist, "panel_label_B", "panel_label"),
        (composition_title_artist, "composition_panel_title", "subplot_title"),
        (gap_axes.title, "gap_heatmap_title", "subplot_title"),
        (composition_axes.xaxis.label, "composition_x_axis_title", "x_axis_title"),
        (composition_axes.yaxis.label, "composition_y_axis_title", "y_axis_title"),
        (colorbar.ax.yaxis.label, "gap_colorbar_title", "colorbar_title"),
    ):
        if artist is not None:
            _append_text_box(
                layout_boxes=layout_boxes,
                figure=figure,
                renderer=renderer,
                artist=artist,
                box_id=box_id,
                box_type=box_type,
            )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=composition_axes.get_window_extent(renderer=renderer),
            box_id="panel_composition",
            box_type="composition_panel",
        ),
        _bbox_to_layout_box(
            figure=figure,
            bbox=gap_axes.get_window_extent(renderer=renderer),
            box_id="panel_gap_heatmap",
            box_type="gap_heatmap_panel",
        ),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="gap_colorbar",
            box_type="colorbar",
        )
    ]
    _dump_sidecar(
        template_id=template_id,
        figure=figure,
        renderer=renderer,
        layout_boxes=layout_boxes,
        panel_boxes=panel_boxes,
        guide_boxes=guide_boxes,
        metrics={
            "rows": normalized_rows,
            "gap_labels": [label for _, label in _GAP_FIELDS],
        },
        layout_sidecar_path=layout_sidecar_path,
    )
    figure.savefig(output_png_path, format="png", dpi=320)
    figure.savefig(output_pdf_path, format="pdf")
    plt.close(figure)


def _render_python_site_held_out_stability_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    transition_rows = list(display_payload.get("transition_rows") or [])
    site_fold_rows = list(display_payload.get("site_fold_rows") or [])
    if not transition_rows:
        raise RuntimeError(f"{template_id} requires non-empty transition_rows")
    if not site_fold_rows:
        raise RuntimeError(f"{template_id} requires non-empty site_fold_rows")
    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    typography, palette, layout_override, style_roles = _collect_render_context(display_payload)
    colors = _normalize_colors(style_roles, palette)
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", True)

    phenotype_labels: list[str] = []
    normalized_transition_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(transition_rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"{template_id} transition_rows[{row_index}] must be an object")
        source_label = _require_non_empty_string(
            row.get("source_phenotype_label"),
            label=f"{template_id} transition_rows[{row_index}].source_phenotype_label",
        )
        target_label = _require_non_empty_string(
            row.get("target_phenotype_label"),
            label=f"{template_id} transition_rows[{row_index}].target_phenotype_label",
        )
        if source_label not in phenotype_labels:
            phenotype_labels.append(source_label)
        if target_label not in phenotype_labels:
            phenotype_labels.append(target_label)
        patient_count = _require_non_negative_int(
            row.get("patient_count"),
            label=f"{template_id} transition_rows[{row_index}].patient_count",
        )
        share = _coerce_probability(
            row.get("share_of_transition_patients"),
            label=f"{template_id} transition_rows[{row_index}].share_of_transition_patients",
        )
        if share is None:
            raise RuntimeError(f"{template_id} transition_rows[{row_index}].share_of_transition_patients is required")
        normalized_transition_rows.append(
            {
                "source_phenotype_label": source_label,
                "target_phenotype_label": target_label,
                "patient_count": patient_count,
                "share_of_transition_patients": share,
            }
        )

    matrix = np.zeros((len(phenotype_labels), len(phenotype_labels)), dtype=float)
    row_totals = {label: 0 for label in phenotype_labels}
    for row in normalized_transition_rows:
        source_index = phenotype_labels.index(str(row["source_phenotype_label"]))
        target_index = phenotype_labels.index(str(row["target_phenotype_label"]))
        patient_count = int(row["patient_count"])
        row_totals[str(row["source_phenotype_label"])] += patient_count
        matrix[source_index, target_index] += float(patient_count)
    for row_index, label in enumerate(phenotype_labels):
        if row_totals[label] > 0:
            matrix[row_index, :] = (matrix[row_index, :] / float(row_totals[label])) * 100.0

    normalized_site_rows: list[dict[str, Any]] = []
    fold_labels: list[str] = []
    fold_shares: list[float] = []
    for row_index, row in enumerate(site_fold_rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"{template_id} site_fold_rows[{row_index}] must be an object")
        fold_id = _require_non_empty_string(
            row.get("fold_id"),
            label=f"{template_id} site_fold_rows[{row_index}].fold_id",
        )
        index_patients = _require_non_negative_int(
            row.get("index_patients"),
            label=f"{template_id} site_fold_rows[{row_index}].index_patients",
        )
        share = _coerce_probability(
            row.get("share_of_index_patients"),
            label=f"{template_id} site_fold_rows[{row_index}].share_of_index_patients",
        )
        if share is None:
            raise RuntimeError(f"{template_id} site_fold_rows[{row_index}].share_of_index_patients is required")
        normalized_site_rows.append(
            {
                "fold_id": fold_id,
                "index_patients": index_patients,
                "share_of_index_patients": share,
            }
        )
        fold_labels.append(fold_id.replace("_", " ").title())
        fold_shares.append(share * 100.0)

    visit_coverage = _coerce_probability(display_payload.get("visit_coverage"), label=f"{template_id} visit_coverage")
    eligible_site_count = display_payload.get("eligible_site_count")
    if eligible_site_count is not None:
        eligible_site_count = _require_non_negative_int(
            eligible_site_count,
            label=f"{template_id} eligible_site_count",
        )

    figure = plt.figure(figsize=(13.2, 6.0))
    figure.patch.set_facecolor("white")
    title_artist, title_line_count = _figure_title(
        figure=figure,
        display_payload=display_payload,
        title_size=title_size,
        show_figure_title=show_figure_title,
    )
    grid = figure.add_gridspec(1, 2, width_ratios=[1.15, 0.85], wspace=0.24)
    transition_axes = figure.add_subplot(grid[0, 0])
    coverage_axes = figure.add_subplot(grid[0, 1])

    transition_cmap = LinearSegmentedColormap.from_list(
        "dpcc_transition_heatmap",
        [colors["primary_soft"], colors["secondary_soft"], colors["accent"]],
    )
    vmax = max(35.0, float(np.nanmax(matrix)) if matrix.size else 35.0)
    transition_image = transition_axes.imshow(matrix, cmap=transition_cmap, vmin=0.0, vmax=vmax)
    transition_axes.set_xticks(np.arange(len(phenotype_labels)))
    transition_axes.set_xticklabels(phenotype_labels, rotation=28, ha="right")
    transition_axes.set_yticks(np.arange(len(phenotype_labels)))
    transition_axes.set_yticklabels(phenotype_labels)
    transition_axes.set_xlabel("Target phenotype", fontsize=axis_title_size, color="#13293d")
    transition_axes.set_ylabel("Source phenotype", fontsize=axis_title_size, color="#13293d")
    transition_title_artist = transition_axes.set_title(
        str(display_payload.get("transition_panel_title") or "First-to-last transition share").strip(),
        loc="left",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
    )
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            transition_axes.text(
                col_index,
                row_index,
                f"{matrix[row_index, col_index]:.1f}%",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.5, 7.5),
                color=TEXT_COLOR,
            )
    colorbar = figure.colorbar(transition_image, ax=transition_axes, fraction=0.046, pad=0.02)
    colorbar.set_label("Row-normalized share (%)", fontsize=axis_title_size)

    coverage_axes.bar(
        np.arange(len(fold_labels)),
        fold_shares,
        color=colors["primary"],
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    coverage_axes.set_xticks(np.arange(len(fold_labels)))
    coverage_axes.set_xticklabels(fold_labels, rotation=28, ha="right")
    coverage_axes.set_xlabel("Deterministic held-out fold", fontsize=axis_title_size, color="#13293d")
    coverage_axes.set_ylabel("Index share (%)", fontsize=axis_title_size, color="#13293d")
    coverage_title_artist = coverage_axes.set_title(
        str(display_payload.get("coverage_panel_title") or "Held-out fold distribution").strip(),
        loc="left",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
    )
    coverage_axes.yaxis.grid(True, linestyle="--", linewidth=0.7, color=GRID_COLOR, zorder=0)
    _apply_publication_axes_style(coverage_axes)

    note_artist = None
    if eligible_site_count is not None and visit_coverage is not None:
        note_artist = coverage_axes.text(
            0.02,
            0.97,
            f"{eligible_site_count} sites; {visit_coverage * 100.0:.2f}% visit coverage",
            transform=coverage_axes.transAxes,
            ha="left",
            va="top",
            fontsize=max(tick_size - 0.5, 8.5),
            color=TEXT_COLOR,
        )

    panel_a_artist = _panel_label_artist(axes=transition_axes, label="A", panel_label_size=panel_label_size)
    panel_b_artist = _panel_label_artist(axes=coverage_axes, label="B", panel_label_size=panel_label_size)
    top_margin = 0.86 - 0.06 * max(title_line_count - 1, 0) if title_artist is not None else 0.92
    figure.subplots_adjust(left=0.08, right=0.96, top=max(0.72, top_margin), bottom=0.18, wspace=0.24)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    for artist, box_id, box_type in (
        (title_artist, "title", "title"),
        (panel_a_artist, "panel_label_A", "panel_label"),
        (panel_b_artist, "panel_label_B", "panel_label"),
        (transition_title_artist, "transition_panel_title", "subplot_title"),
        (coverage_title_artist, "site_support_panel_title", "subplot_title"),
        (transition_axes.xaxis.label, "transition_x_axis_title", "x_axis_title"),
        (transition_axes.yaxis.label, "transition_y_axis_title", "y_axis_title"),
        (coverage_axes.xaxis.label, "site_support_x_axis_title", "x_axis_title"),
        (coverage_axes.yaxis.label, "site_support_y_axis_title", "y_axis_title"),
        (colorbar.ax.yaxis.label, "transition_colorbar_title", "colorbar_title"),
        (note_artist, "site_support_note", "annotation_block"),
    ):
        if artist is not None:
            _append_text_box(
                layout_boxes=layout_boxes,
                figure=figure,
                renderer=renderer,
                artist=artist,
                box_id=box_id,
                box_type=box_type,
            )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=transition_axes.get_window_extent(renderer=renderer),
            box_id="panel_transition_heatmap",
            box_type="transition_heatmap_panel",
        ),
        _bbox_to_layout_box(
            figure=figure,
            bbox=coverage_axes.get_window_extent(renderer=renderer),
            box_id="panel_site_support",
            box_type="site_support_panel",
        ),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="transition_colorbar",
            box_type="colorbar",
        )
    ]
    metrics: dict[str, Any] = {
        "transition_rows": normalized_transition_rows,
        "site_fold_rows": normalized_site_rows,
    }
    if visit_coverage is not None:
        metrics["visit_coverage"] = visit_coverage
    if eligible_site_count is not None:
        metrics["eligible_site_count"] = eligible_site_count
    _dump_sidecar(
        template_id=template_id,
        figure=figure,
        renderer=renderer,
        layout_boxes=layout_boxes,
        panel_boxes=panel_boxes,
        guide_boxes=guide_boxes,
        metrics=metrics,
        layout_sidecar_path=layout_sidecar_path,
    )
    figure.savefig(output_png_path, format="png", dpi=320)
    figure.savefig(output_pdf_path, format="pdf")
    plt.close(figure)


def _render_python_treatment_gap_alignment_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    rows_payload = list(display_payload.get("rows") or [])
    if not rows_payload:
        raise RuntimeError(f"{template_id} requires non-empty rows")
    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    typography, palette, layout_override, _style_roles = _collect_render_context(display_payload)
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", True)

    normalized_rows: list[dict[str, Any]] = []
    phenotype_labels: list[str] = []
    for row_index, row in enumerate(rows_payload):
        if not isinstance(row, dict):
            raise RuntimeError(f"{template_id} rows[{row_index}] must be an object")
        phenotype_label = _require_non_empty_string(
            row.get("phenotype_label"),
            label=f"{template_id} rows[{row_index}].phenotype_label",
        )
        index_patients = _require_non_negative_int(
            row.get("index_patients"),
            label=f"{template_id} rows[{row_index}].index_patients",
            allow_zero=False,
        )
        normalized_row: dict[str, Any] = {
            "phenotype_label": phenotype_label,
            "index_patients": index_patients,
        }
        phenotype_labels.append(phenotype_label)
        for field, _ in _GAP_COUNT_FIELDS:
            patient_count = _require_non_negative_int(
                row.get(field),
                label=f"{template_id} rows[{row_index}].{field}",
            )
            if patient_count > index_patients:
                raise RuntimeError(f"{template_id} rows[{row_index}].{field} must not exceed index_patients")
            normalized_row[field] = patient_count
        normalized_rows.append(normalized_row)

    figure, axes = plt.subplots(2, 2, figsize=(13.2, 8.2))
    figure.patch.set_facecolor("white")
    title_artist, title_line_count = _figure_title(
        figure=figure,
        display_payload=display_payload,
        title_size=title_size,
        show_figure_title=show_figure_title,
    )
    axes_flat = list(axes.flatten())
    panel_label_artists: list[Any] = []
    panel_title_artists: list[Any] = []
    panel_boxes: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    panel_metrics: list[dict[str, Any]] = []

    for index, (axis, (field, panel_title), color) in enumerate(zip(axes_flat, _GAP_COUNT_FIELDS, _F4_PANEL_COLORS, strict=True)):
        counts = [int(row[field]) for row in normalized_rows]
        x_positions = np.arange(len(phenotype_labels))
        bars = axis.bar(
            x_positions,
            counts,
            color=color,
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        if counts and max(counts) > 0:
            top_index = int(np.argmax(counts))
            bars[top_index].set_hatch("//")
        axis.set_xticks(x_positions)
        axis.set_xticklabels(phenotype_labels, rotation=28, ha="right")
        axis.set_ylabel("Patients", fontsize=axis_title_size, color="#13293d")
        panel_title_artist = axis.set_title(
            str(panel_title).strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
        )
        ymax = max(counts) * 1.18 if counts and max(counts) else 1.0
        axis.set_ylim(0.0, ymax)
        axis.yaxis.grid(True, linestyle="--", linewidth=0.7, color=GRID_COLOR, zorder=0)
        _apply_publication_axes_style(axis)
        label_artist = _panel_label_artist(
            axes=axis,
            label=chr(ord("A") + index),
            panel_label_size=panel_label_size,
        )
        panel_label_artists.append(label_artist)
        panel_title_artists.append(panel_title_artist)
        for bar, value in zip(bars, counts, strict=True):
            if value == 0:
                continue
            axis.text(
                float(bar.get_x()) + float(bar.get_width()) / 2.0,
                float(value) + max(max(counts) * 0.02, 1.0),
                f"{value:,}",
                ha="center",
                va="bottom",
                fontsize=max(tick_size - 1.5, 7.5),
                color=TEXT_COLOR,
                rotation=90,
            )
        panel_metrics.append(
            {
                "panel_id": chr(ord("A") + index),
                "gap_field": field,
                "gap_label": panel_title,
                "counts": [
                    {
                        "phenotype_label": phenotype_label,
                        "patient_count": patient_count,
                    }
                    for phenotype_label, patient_count in zip(phenotype_labels, counts, strict=True)
                ],
            }
        )

    top_margin = 0.90 - 0.05 * max(title_line_count - 1, 0) if title_artist is not None else 0.95
    figure.subplots_adjust(left=0.08, right=0.98, top=max(0.75, top_margin), bottom=0.14, wspace=0.24, hspace=0.30)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()

    if title_artist is not None:
        _append_text_box(
            layout_boxes=layout_boxes,
            figure=figure,
            renderer=renderer,
            artist=title_artist,
            box_id="title",
            box_type="title",
        )
    for index, axis in enumerate(axes_flat):
        _append_text_box(
            layout_boxes=layout_boxes,
            figure=figure,
            renderer=renderer,
            artist=panel_label_artists[index],
            box_id=f"panel_label_{chr(ord('A') + index)}",
            box_type="panel_label",
        )
        _append_text_box(
            layout_boxes=layout_boxes,
            figure=figure,
            renderer=renderer,
            artist=panel_title_artists[index],
            box_id=f"gap_count_title_{chr(ord('A') + index)}",
            box_type="subplot_title",
        )
        _append_text_box(
            layout_boxes=layout_boxes,
            figure=figure,
            renderer=renderer,
            artist=axis.yaxis.label,
            box_id=f"gap_count_y_axis_title_{chr(ord('A') + index)}",
            box_type="y_axis_title",
        )
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=axis.get_window_extent(renderer=renderer),
                box_id=f"panel_gap_count_{chr(ord('A') + index)}",
                box_type="gap_count_panel",
            )
        )

    _dump_sidecar(
        template_id=template_id,
        figure=figure,
        renderer=renderer,
        layout_boxes=layout_boxes,
        panel_boxes=panel_boxes,
        guide_boxes=[],
        metrics={
            "rows": normalized_rows,
            "panels": panel_metrics,
        },
        layout_sidecar_path=layout_sidecar_path,
    )
    figure.savefig(output_png_path, format="png", dpi=320)
    figure.savefig(output_pdf_path, format="pdf")
    plt.close(figure)


__all__ = [
    "_render_python_phenotype_gap_structure_figure",
    "_render_python_site_held_out_stability_figure",
    "_render_python_treatment_gap_alignment_figure",
]
