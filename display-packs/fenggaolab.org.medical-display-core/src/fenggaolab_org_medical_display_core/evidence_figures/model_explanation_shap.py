from __future__ import annotations

from pathlib import Path
import re
import textwrap
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ..shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _build_python_shap_layout_sidecar,
    _centered_offsets,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_model_complexity_audit_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    metric_panels = list(display_payload.get("metric_panels") or [])
    audit_panels = list(display_payload.get("audit_panels") or [])
    if not metric_panels or not audit_panels:
        raise RuntimeError(f"{template_id} requires non-empty metric_panels and audit_panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = float(stroke.get("marker_size") or 4.5)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_subplot_titles = _read_bool_override(layout_override, "show_subplot_titles", True)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    metric_fill = str(palette.get("primary_soft") or "#EEF3F1").strip() or "#EEF3F1"
    audit_fill = str(palette.get("secondary_soft") or "#F4EFE8").strip() or "#F4EFE8"

    max_row_count = max(
        max((len(panel.get("rows") or []) for panel in metric_panels), default=1),
        max((len(panel.get("rows") or []) for panel in audit_panels), default=1),
    )
    figure_height = max(7.8, 0.52 * max_row_count + 3.6)
    fig = plt.figure(figsize=(12.4, figure_height))
    fig.patch.set_facecolor("white")
    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.86,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    outer = fig.add_gridspec(1, 2, width_ratios=[1.06, 0.94], wspace=0.60)
    left_grid = outer[0, 0].subgridspec(
        len(metric_panels),
        1,
        hspace=0.70,
        height_ratios=[max(1, len(panel.get("rows") or [])) for panel in metric_panels],
    )
    right_grid = outer[0, 1].subgridspec(
        len(audit_panels),
        1,
        hspace=0.42,
        height_ratios=[max(1, len(panel.get("rows") or [])) for panel in audit_panels],
    )
    metric_axes = [fig.add_subplot(left_grid[index, 0]) for index in range(len(metric_panels))]
    audit_axes = [fig.add_subplot(right_grid[index, 0]) for index in range(len(audit_panels))]

    metric_title_artists: list[Any] = []
    audit_title_artists: list[Any] = []
    metric_reference_artists: list[Any] = []
    audit_reference_artists: list[Any] = []
    metric_marker_specs: list[tuple[Any, float, float]] = []
    audit_bar_artists: list[Any] = []

    def _panel_limits(rows: list[dict[str, Any]], *, reference_value: float | None) -> tuple[float, float]:
        values = [float(item["value"]) for item in rows]
        if reference_value is not None:
            values.append(float(reference_value))
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum
        padding = max(span * 0.14, 0.03 if maximum <= 1.5 else 0.12)
        if minimum >= 0.0:
            lower = max(0.0, minimum - padding)
        else:
            lower = minimum - padding
        upper = maximum + padding
        if upper <= lower:
            upper = lower + 1.0
        return lower, upper

    for panel_index, (axes, panel) in enumerate(zip(metric_axes, metric_panels, strict=True), start=1):
        rows = list(panel["rows"])
        values = [float(item["value"]) for item in rows]
        row_positions = list(range(len(rows)))
        lower_limit, upper_limit = _panel_limits(rows, reference_value=panel.get("reference_value"))
        if panel.get("reference_value") is not None:
            reference_artist = axes.axvline(
                float(panel["reference_value"]),
                color=reference_color,
                linewidth=1.0,
                linestyle="--",
                zorder=1,
            )
            metric_reference_artists.append(reference_artist)
        scatter_artist = axes.scatter(
            values,
            row_positions,
            s=max(marker_size, 4.2) ** 2,
            color=model_color,
            edgecolors="white",
            linewidths=0.8,
            zorder=3,
        )
        axes.hlines(
            row_positions,
            [lower_limit] * len(row_positions),
            values,
            color=matplotlib.colors.to_rgba(metric_fill, alpha=0.95),
            linewidth=2.1,
            zorder=2,
        )
        axes.set_xlim(lower_limit, upper_limit)
        axes.set_ylim(-0.6, len(rows) - 0.4)
        axes.set_yticks(row_positions)
        axes.set_yticklabels([str(item["label"]) for item in rows], fontsize=max(tick_size - 1.2, 8.2))
        axes.invert_yaxis()
        axes.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        panel_title_artist = None
        if show_subplot_titles:
            panel_title_artist = axes.set_title(
                str(panel["title"]),
                fontsize=axis_title_size,
                fontweight="bold",
                color="#334155",
                pad=8,
            )
        metric_title_artists.append(panel_title_artist)
        axes.text(
            -0.11,
            1.04,
            str(panel["panel_label"]),
            transform=axes.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#2F3437",
            va="bottom",
        )
        axes.tick_params(axis="x", labelsize=tick_size)
        axes.tick_params(axis="y", length=0, pad=6)
        _apply_publication_axes_style(axes)
        axes.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")
        x_radius = max((upper_limit - lower_limit) * 0.018, 0.01)
        for value, row_position in zip(values, row_positions, strict=True):
            metric_marker_specs.append((axes, float(value), float(row_position)))
        _ = scatter_artist

    for panel_index, (axes, panel) in enumerate(zip(audit_axes, audit_panels, strict=True), start=1):
        rows = list(panel["rows"])
        values = [float(item["value"]) for item in rows]
        row_positions = list(range(len(rows)))
        lower_limit, upper_limit = _panel_limits(rows, reference_value=panel.get("reference_value"))
        left_edge = 0.0 if lower_limit >= 0.0 else lower_limit
        bar_artists = axes.barh(
            row_positions,
            [value - left_edge for value in values],
            left=left_edge,
            height=0.66,
            color=matplotlib.colors.to_rgba(audit_fill, alpha=0.96),
            edgecolor=comparator_color,
            linewidth=1.0,
            zorder=2,
        )
        audit_bar_artists.extend(list(bar_artists))
        if panel.get("reference_value") is not None:
            reference_artist = axes.axvline(
                float(panel["reference_value"]),
                color=reference_color,
                linewidth=1.0,
                linestyle="--",
                zorder=1,
            )
            audit_reference_artists.append(reference_artist)
        axes.set_xlim(lower_limit, upper_limit)
        axes.set_ylim(-0.6, len(rows) - 0.4)
        axes.set_yticks(row_positions)
        axes.set_yticklabels([str(item["label"]) for item in rows], fontsize=max(tick_size - 1.2, 8.2))
        axes.invert_yaxis()
        axes.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        panel_title_artist = None
        if show_subplot_titles:
            panel_title_artist = axes.set_title(
                str(panel["title"]),
                fontsize=axis_title_size,
                fontweight="bold",
                color="#334155",
                pad=8,
            )
        audit_title_artists.append(panel_title_artist)
        axes.text(
            -0.11,
            1.04,
            str(panel["panel_label"]),
            transform=axes.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#2F3437",
            va="bottom",
        )
        axes.tick_params(axis="x", labelsize=tick_size)
        axes.tick_params(axis="y", length=0, pad=6)
        _apply_publication_axes_style(axes)
        axes.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")

    top_value = 0.91 - 0.05 * max(title_line_count - 1, 0)
    top_margin = max(0.76, top_value) if show_figure_title else 0.95
    if not show_subplot_titles:
        top_margin = min(0.97, top_margin + 0.01)
    fig.subplots_adjust(left=0.28, right=0.98, top=top_margin, bottom=0.07)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []

    for index, (axes, title_artist_item) in enumerate(zip(metric_axes, metric_title_artists, strict=True), start=1):
        if title_artist_item is not None:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=title_artist_item.get_window_extent(renderer=renderer),
                    box_id=f"metric_panel_title_{index}",
                    box_type="subplot_title",
                )
            )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"metric_panel_x_axis_title_{index}",
                box_type="subplot_x_axis_title",
            )
        )
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=f"metric_panel_{index}",
                box_type="metric_panel",
            )
        )
    for index, (axes, title_artist_item) in enumerate(zip(audit_axes, audit_title_artists, strict=True), start=1):
        if title_artist_item is not None:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=title_artist_item.get_window_extent(renderer=renderer),
                    box_id=f"audit_panel_title_{index}",
                    box_type="subplot_title",
                )
            )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"audit_panel_x_axis_title_{index}",
                box_type="subplot_x_axis_title",
            )
        )
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=f"audit_panel_{index}",
                box_type="audit_panel",
            )
        )

    marker_index = 1
    for axes, panel in zip(metric_axes, metric_panels, strict=True):
        lower_limit, upper_limit = axes.get_xlim()
        x_radius = max((upper_limit - lower_limit) * 0.018, 0.01)
        for row_position, row in enumerate(panel["rows"]):
            value = float(row["value"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes,
                    figure=fig,
                    x0=value - x_radius,
                    y0=float(row_position) - 0.18,
                    x1=value + x_radius,
                    y1=float(row_position) + 0.18,
                    box_id=f"metric_marker_{marker_index}",
                    box_type="metric_marker",
                )
            )
            marker_index += 1

    for index, artist in enumerate(audit_bar_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"audit_bar_{index}",
                box_type="audit_bar",
            )
        )

    for index, artist in enumerate([*metric_reference_artists, *audit_reference_artists], start=1):
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"reference_line_{index}",
                box_type="reference_line",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_panels": metric_panels,
                "audit_panels": audit_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_summary_beeswarm(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    rows = list(display_payload.get("rows") or [])
    if not rows:
        raise RuntimeError("shap_summary_beeswarm requires non-empty rows")
    render_context = dict(display_payload.get("render_context") or {})
    layout_override = dict(render_context.get("layout_override") or {})
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    figure_height = max(4.8, 0.85 * len(rows) + 1.4)
    fig, ax = plt.subplots(figsize=(7.2, figure_height))
    fig.patch.set_facecolor("white")

    feature_values = [point["feature_value"] for row in rows for point in row["points"]]
    min_value = min(feature_values)
    max_value = max(feature_values)
    if max_value == min_value:
        max_value = min_value + 1.0
    norm = matplotlib.colors.Normalize(vmin=min_value, vmax=max_value)
    cmap = plt.get_cmap("coolwarm")
    point_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        ordered_points = sorted(row["points"], key=lambda item: float(item["shap_value"]))
        offsets = _centered_offsets(len(ordered_points))
        for point_index, point in enumerate(ordered_points):
            row_position = row_index + offsets[point_index]
            ax.scatter(
                point["shap_value"],
                row_position,
                s=42,
                c=[cmap(norm(point["feature_value"]))],
                edgecolors="white",
                linewidths=0.35,
                alpha=0.95,
            )
            point_rows.append(
                {
                    "feature": str(row["feature"]),
                    "row_position": row_position,
                    "shap_value": float(point["shap_value"]),
                }
            )

    ax.axvline(0.0, color="#6b7280", linewidth=0.8, linestyle="--")
    ax.set_yticks(list(range(len(rows))))
    ax.set_yticklabels([str(row["feature"]) for row in rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    ax.set_ylabel("")
    if show_figure_title:
        ax.set_title(str(display_payload.get("title") or "").strip(), fontsize=12.5, fontweight="bold", color="#13293d")
    _apply_publication_axes_style(ax)

    scalar_mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(scalar_mappable, ax=ax, pad=0.02)
    colorbar.set_label("Feature value", fontsize=10, color="#13293d")

    fig.tight_layout()
    fig.canvas.draw()
    dump_json(
        layout_sidecar_path,
        _build_python_shap_layout_sidecar(
            figure=fig,
            axes=ax,
            colorbar=colorbar,
            rows=rows,
            point_rows=point_rows,
            template_id=template_id,
        ),
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_bar_importance(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    bars = list(display_payload.get("bars") or [])
    if not bars:
        raise RuntimeError("shap_bar_importance requires non-empty bars")
    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    figure_height = max(4.6, 0.55 * len(bars) + 1.6)
    fig, ax = plt.subplots(figsize=(7.4, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.98,
        )

    values = [float(item["importance_value"]) for item in bars]
    row_positions = list(range(len(bars)))
    max_value = max(values)
    x_padding = max(max_value * 0.18, 0.02)
    x_limit = max_value + x_padding
    bar_artists = ax.barh(
        row_positions,
        values,
        height=0.58,
        color=matplotlib.colors.to_rgba(model_color, alpha=0.92),
        edgecolor=comparator_color,
        linewidth=0.9,
        zorder=2,
    )
    value_label_artists: list[Any] = []
    value_label_padding = max(x_limit * 0.02, 0.015)
    for row_position, value in zip(row_positions, values, strict=True):
        value_label_artists.append(
            ax.text(
                value + value_label_padding,
                row_position,
                f"{value:.3f}",
                fontsize=max(tick_size - 0.6, 8.4),
                color="#334155",
                va="center",
                ha="left",
            )
        )

    ax.set_xlim(0.0, x_limit + value_label_padding * 3.0)
    ax.set_ylim(-0.6, len(bars) - 0.4)
    ax.set_yticks(row_positions)
    ax.set_yticklabels([str(item["feature"]) for item in bars], fontsize=max(tick_size - 0.3, 8.6))
    ax.invert_yaxis()
    ax.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color="#13293d")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=tick_size)
    ax.tick_params(axis="y", length=0, pad=8)
    _apply_publication_axes_style(ax)
    ax.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")

    fig.subplots_adjust(left=0.30, right=0.97, top=0.90 if show_figure_title else 0.95, bottom=0.14)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        )
    )
    feature_label_ids: list[str] = []
    for index, label_artist in enumerate(ax.get_yticklabels(), start=1):
        feature_label_id = f"feature_label_{index}"
        feature_label_ids.append(feature_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=feature_label_id,
                box_type="feature_label",
            )
        )
    bar_ids: list[str] = []
    for index, artist in enumerate(bar_artists, start=1):
        bar_id = f"importance_bar_{index}"
        bar_ids.append(bar_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=bar_id,
                box_type="importance_bar",
            )
        )
    value_label_ids: list[str] = []
    for index, label_artist in enumerate(value_label_artists, start=1):
        value_label_id = f"value_label_{index}"
        value_label_ids.append(value_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=value_label_id,
                box_type="value_label",
            )
        )

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [panel_box],
            "guide_boxes": [],
            "metrics": {
                "bars": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "importance_value": float(item["importance_value"]),
                        "bar_box_id": bar_ids[index],
                        "feature_label_box_id": feature_label_ids[index],
                        "value_label_box_id": value_label_ids[index],
                    }
                    for index, item in enumerate(bars)
                ]
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_signed_importance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    bars = list(display_payload.get("bars") or [])
    if not bars:
        raise RuntimeError("shap_signed_importance_panel requires non-empty bars")
    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    zero_line_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    signed_values = [float(item["signed_importance_value"]) for item in bars]
    row_positions = list(range(len(bars)))
    max_abs_value = max(abs(value) for value in signed_values)
    x_padding = max(max_abs_value * 0.18, 0.02)
    core_limit = max_abs_value + x_padding
    label_padding = max(core_limit * 0.03, 0.018)
    axis_limit = core_limit + label_padding * 3.2

    figure_height = max(4.8, 0.58 * len(bars) + 2.0)
    fig, ax = plt.subplots(figsize=(7.8, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.98,
        )

    bar_artists: list[Any] = []
    value_label_artists: list[Any] = []
    for row_position, signed_value in zip(row_positions, signed_values, strict=True):
        color = positive_color if signed_value > 0.0 else negative_color
        bar_artists.append(
            ax.barh(
                row_position,
                signed_value,
                height=0.58,
                color=matplotlib.colors.to_rgba(color, alpha=0.92),
                edgecolor=color,
                linewidth=0.9,
                zorder=3,
            )[0]
        )
        value_label_artists.append(
            ax.text(
                signed_value + (label_padding if signed_value > 0.0 else -label_padding),
                row_position,
                f"{signed_value:+.3f}",
                fontsize=max(tick_size - 0.6, 8.4),
                color="#334155",
                va="center",
                ha="left" if signed_value > 0.0 else "right",
            )
        )

    ax.axvline(0.0, color=zero_line_color, linewidth=1.1, linestyle="--", zorder=1)
    ax.set_xlim(-axis_limit, axis_limit)
    ax.set_ylim(-0.6, len(bars) - 0.4)
    ax.set_yticks(row_positions)
    ax.set_yticklabels([str(item["feature"]) for item in bars], fontsize=max(tick_size - 0.3, 8.6))
    ax.invert_yaxis()
    ax.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=tick_size)
    ax.tick_params(axis="y", length=0, pad=8)
    _apply_publication_axes_style(ax)
    ax.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")

    negative_direction_artist = ax.text(
        0.18,
        1.03,
        str(display_payload.get("negative_label") or "").strip(),
        transform=ax.transAxes,
        fontsize=max(tick_size - 0.3, 8.8),
        color=negative_color,
        fontweight="bold",
        ha="center",
        va="bottom",
    )
    positive_direction_artist = ax.text(
        0.82,
        1.03,
        str(display_payload.get("positive_label") or "").strip(),
        transform=ax.transAxes,
        fontsize=max(tick_size - 0.3, 8.8),
        color=positive_color,
        fontweight="bold",
        ha="center",
        va="bottom",
    )

    fig.subplots_adjust(left=0.30, right=0.97, top=0.88 if show_figure_title else 0.93, bottom=0.14)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=negative_direction_artist.get_window_extent(renderer=renderer),
                box_id="negative_direction_label",
                box_type="negative_direction_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=positive_direction_artist.get_window_extent(renderer=renderer),
                box_id="positive_direction_label",
                box_type="positive_direction_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="x_axis_title",
            ),
        ]
    )

    feature_label_ids: list[str] = []
    for index, label_artist in enumerate(ax.get_yticklabels(), start=1):
        feature_label_id = f"feature_label_{index}"
        feature_label_ids.append(feature_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=feature_label_id,
                box_type="feature_label",
            )
        )
    bar_ids: list[str] = []
    for index, artist in enumerate(bar_artists, start=1):
        bar_id = f"importance_bar_{index}"
        bar_ids.append(bar_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=bar_id,
                box_type="importance_bar",
            )
        )
    value_label_ids: list[str] = []
    for index, label_artist in enumerate(value_label_artists, start=1):
        value_label_id = f"value_label_{index}"
        value_label_ids.append(value_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=value_label_id,
                box_type="value_label",
            )
        )

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )
    zero_line_half_width = max(core_limit * 0.008, 0.0025)
    zero_line_box = _data_box_to_layout_box(
        axes=ax,
        figure=fig,
        x0=-zero_line_half_width,
        y0=-0.55,
        x1=zero_line_half_width,
        y1=len(bars) - 0.45,
        box_id="zero_line",
        box_type="zero_line",
    )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [panel_box],
            "guide_boxes": [zero_line_box],
            "metrics": {
                "bars": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "direction": "positive" if float(item["signed_importance_value"]) > 0.0 else "negative",
                        "signed_importance_value": float(item["signed_importance_value"]),
                        "bar_box_id": bar_ids[index],
                        "feature_label_box_id": feature_label_ids[index],
                        "value_label_box_id": value_label_ids[index],
                    }
                    for index, item in enumerate(bars)
                ]
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_multicohort_importance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError("shap_multicohort_importance_panel requires non-empty panels")

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    max_bar_count = max(len(list(panel.get("bars") or [])) for panel in panels)
    max_value = max(float(bar["importance_value"]) for panel in panels for bar in panel["bars"])
    x_padding = max(max_value * 0.18, 0.02)
    core_limit = max_value + x_padding
    label_padding = max(core_limit * 0.03, 0.015)
    axis_limit = core_limit + label_padding * 3.0

    figure_width = max(7.8, 4.4 * len(panels) + 0.6)
    figure_height = max(4.6, 0.55 * max_bar_count + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, figure_height), sharey=False)
    axes_list = list(axes.flat) if hasattr(axes, "flat") else [axes]
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(
        left=0.12,
        right=0.98,
        top=0.84 if show_figure_title else 0.90,
        bottom=0.16,
        wspace=0.48,
    )

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.98,
        )

    panel_metrics: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []

    for axis_index, (ax, panel) in enumerate(zip(axes_list, panels, strict=True)):
        bars = list(panel["bars"])
        panel_label = str(panel["panel_label"])
        row_positions = list(range(len(bars)))
        values = [float(item["importance_value"]) for item in bars]

        bar_artists = ax.barh(
            row_positions,
            values,
            height=0.58,
            color=matplotlib.colors.to_rgba(model_color, alpha=0.92),
            edgecolor=comparator_color,
            linewidth=0.9,
            zorder=2,
        )
        value_label_artists: list[Any] = []
        for row_position, value in zip(row_positions, values, strict=True):
            value_label_artists.append(
                ax.text(
                    value + label_padding,
                    row_position,
                    f"{value:.3f}",
                    fontsize=max(tick_size - 0.6, 8.4),
                    color="#334155",
                    va="center",
                    ha="left",
                )
            )

        ax.set_xlim(0.0, axis_limit)
        ax.set_ylim(-0.6, len(bars) - 0.4)
        ax.set_yticks(row_positions)
        ax.set_yticklabels([str(item["feature"]) for item in bars], fontsize=max(tick_size - 0.3, 8.6))
        ax.invert_yaxis()
        ax.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        ax.set_ylabel("")
        ax.tick_params(axis="x", labelsize=tick_size)
        ax.tick_params(axis="y", length=0, pad=8)
        if axis_index:
            ax.tick_params(axis="y", pad=10)
        _apply_publication_axes_style(ax)
        ax.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")
        ax.set_title(str(panel["title"]), fontsize=max(tick_size + 0.2, 10.2), color="#13293d", pad=10.0)

        panel_label_artist = ax.text(
            0.01,
            0.99,
            panel_label,
            transform=ax.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#13293d",
            ha="left",
            va="top",
        )

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_label}",
                box_type="panel_label",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.title.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_label}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"x_axis_title_{panel_label}",
                box_type="subplot_x_axis_title",
            )
        )

        feature_label_ids: list[str] = []
        for row_index, label_artist in enumerate(ax.get_yticklabels(), start=1):
            feature_label_id = f"feature_label_{panel_label}_{row_index}"
            feature_label_ids.append(feature_label_id)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=feature_label_id,
                    box_type="feature_label",
                )
            )

        bar_ids: list[str] = []
        for row_index, artist in enumerate(bar_artists, start=1):
            bar_id = f"importance_bar_{panel_label}_{row_index}"
            bar_ids.append(bar_id)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=artist.get_window_extent(renderer=renderer),
                    box_id=bar_id,
                    box_type="importance_bar",
                )
            )

        value_label_ids: list[str] = []
        for row_index, label_artist in enumerate(value_label_artists, start=1):
            value_label_id = f"value_label_{panel_label}_{row_index}"
            value_label_ids.append(value_label_id)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=value_label_id,
                    box_type="value_label",
                )
            )

        panel_box_id = f"panel_{panel_label}"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.get_window_extent(renderer=renderer),
                box_id=panel_box_id,
                box_type="panel",
            )
        )
        panel_metrics.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_label,
                "title": str(panel["title"]),
                "cohort_label": str(panel["cohort_label"]),
                "panel_box_id": panel_box_id,
                "panel_label_box_id": f"panel_label_{panel_label}",
                "panel_title_box_id": f"panel_title_{panel_label}",
                "x_axis_title_box_id": f"x_axis_title_{panel_label}",
                "bars": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "importance_value": float(item["importance_value"]),
                        "bar_box_id": bar_ids[row_index],
                        "feature_label_box_id": feature_label_ids[row_index],
                        "value_label_box_id": value_label_ids[row_index],
                    }
                    for row_index, item in enumerate(bars)
                ],
            }
        )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [],
            "metrics": {
                "panels": panel_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_dependence_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = float(stroke.get("marker_size") or 4.5)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    interaction_values = [float(point["interaction_value"]) for panel in panels for point in panel["points"]]
    interaction_min = min(interaction_values)
    interaction_max = max(interaction_values)
    if interaction_max <= interaction_min:
        interaction_max = interaction_min + 1.0
    color_norm = matplotlib.colors.Normalize(vmin=interaction_min, vmax=interaction_max)
    cmap = plt.get_cmap("coolwarm")

    shap_values = [float(point["shap_value"]) for panel in panels for point in panel["points"]]
    y_min = min(min(shap_values), 0.0)
    y_max = max(max(shap_values), 0.0)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.16, 0.08)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding
    if y_upper <= y_lower:
        y_upper = y_lower + 0.25

    figure_width = max(8.8, 3.7 * len(panels) + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 4.9), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    panel_title_artists: list[Any] = []
    for axes_item, panel in zip(axes_list, panels, strict=True):
        feature_values = [float(point["feature_value"]) for point in panel["points"]]
        x_min = min(feature_values)
        x_max = max(feature_values)
        x_span = x_max - x_min
        if x_span <= 0.0:
            x_padding = max(abs(x_min) * 0.15, 1.0)
        else:
            x_padding = max(x_span * 0.14, x_span * 0.06)
        axes_item.scatter(
            feature_values,
            [float(point["shap_value"]) for point in panel["points"]],
            c=[float(point["interaction_value"]) for point in panel["points"]],
            cmap=cmap,
            norm=color_norm,
            s=marker_size**2,
            alpha=0.94,
            edgecolors="white",
            linewidths=0.5,
            zorder=3,
        )
        axes_item.axhline(0.0, color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.set_xlim(x_min - x_padding, x_max + x_padding)
        axes_item.set_ylim(y_lower, y_upper)
        axes_item.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="both", labelsize=tick_size, colors="#2F3437")
        axes_item.grid(axis="both", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)
        panel_title_artists.append(axes_item.title)

    top_margin = 0.78 if show_figure_title else 0.86
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.11, right=0.88, top=top_margin, bottom=0.22, wspace=0.26)

    y_axis_title_artist = fig.text(
        0.035,
        0.51,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    scalar_mappable = plt.cm.ScalarMappable(norm=color_norm, cmap=cmap)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(scalar_mappable, ax=axes_list, fraction=0.048, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("colorbar_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        color="#13293d",
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.4), colors="#2F3437")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=axes_item, label=str(panel["panel_label"]))
        for axes_item, panel in zip(axes_list, panels, strict=True)
    ]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="subplot_y_axis_title",
        )
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        )
    ]
    normalized_panels: list[dict[str, Any]] = []

    for axes_item, panel_title_artist, panel_label_artist, panel in zip(
        axes_list,
        panel_title_artists,
        panel_label_artists,
        panels,
        strict=True,
    ):
        panel_token = str(panel["panel_label"])
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_title_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
            ]
        )
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=f"panel_{panel_token}",
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        x_lower, x_upper = axes_item.get_xlim()
        y_thickness = max((axes_item.get_ylim()[1] - axes_item.get_ylim()[0]) * 0.012, 0.01)
        zero_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(x_lower),
            y0=-y_thickness / 2.0,
            x1=float(x_upper),
            y1=y_thickness / 2.0,
            box_id=f"zero_line_{panel_token}",
            box_type="zero_line",
        )
        zero_line_box["x0"] = float(panel_box["x0"])
        zero_line_box["x1"] = float(panel_box["x1"])
        zero_line_box["y0"] = max(float(panel_box["y0"]), float(zero_line_box["y0"]))
        zero_line_box["y1"] = min(float(panel_box["y1"]), float(zero_line_box["y1"]))
        guide_boxes.append(
            zero_line_box
        )

        normalized_points: list[dict[str, Any]] = []
        for point in panel["points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(point["feature_value"]),
                y=float(point["shap_value"]),
            )
            normalized_points.append(
                {
                    "feature_value": float(point["feature_value"]),
                    "shap_value": float(point["shap_value"]),
                    "interaction_value": float(point["interaction_value"]),
                    "x": point_x,
                    "y": point_y,
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "interaction_feature": str(panel["interaction_feature"]),
                "points": normalized_points,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "colorbar_label": str(display_payload.get("colorbar_label") or "").strip(),
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_waterfall_local_explanation_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    all_values: list[float] = []
    max_contribution_count = 0
    for panel in panels:
        baseline_value = float(panel["baseline_value"])
        predicted_value = float(panel["predicted_value"])
        running_value = baseline_value
        normalized_contributions: list[dict[str, Any]] = []
        raw_contributions = list(panel["contributions"])
        for contribution_index, contribution in enumerate(raw_contributions):
            shap_value = float(contribution["shap_value"])
            start_value = running_value
            end_value = running_value + shap_value
            if contribution_index == len(raw_contributions) - 1:
                end_value = predicted_value
            normalized_contributions.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution.get("feature_value_text") or "").strip(),
                    "shap_value": shap_value,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )
            running_value = end_value
            all_values.extend((start_value, end_value))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )
        all_values.extend((baseline_value, predicted_value))
        max_contribution_count = max(max_contribution_count, len(normalized_contributions))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.12, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    x_marker_half_width = max(x_span * 0.004, 0.0025)

    figure_width = max(8.8, 3.7 * len(normalized_panels) + 1.7)
    figure_height = max(4.8, 0.62 * max_contribution_count + 2.2)
    fig, axes = plt.subplots(1, len(normalized_panels), figsize=(figure_width, figure_height), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, normalized_panels, strict=True):
        contributions = list(panel["contributions"])
        row_positions = list(range(len(contributions)))
        feature_labels = [
            (
                f"{item['feature']} = {item['feature_value_text']}"
                if item["feature_value_text"]
                else str(item["feature"])
            )
            for item in contributions
        ]
        bar_artists: list[Any] = []
        value_label_artists: list[Any] = []
        for row_index, contribution in enumerate(contributions):
            start_value = float(contribution["start_value"])
            end_value = float(contribution["end_value"])
            shap_value = float(contribution["shap_value"])
            left_value = min(start_value, end_value)
            bar_width = abs(end_value - start_value)
            bar_artist = axes_item.barh(
                row_index,
                bar_width,
                left=left_value,
                height=0.6,
                color=matplotlib.colors.to_rgba(positive_color if shap_value > 0 else negative_color, alpha=0.92),
                edgecolor=positive_color if shap_value > 0 else negative_color,
                linewidth=0.95,
                zorder=3,
            )[0]
            bar_artists.append(bar_artist)
            value_label_artists.append(
                axes_item.annotate(
                    f"{shap_value:+.2f}",
                    xy=(end_value, row_index),
                    xytext=(6 if shap_value > 0 else -6, 0),
                    textcoords="offset points",
                    ha="left" if shap_value > 0 else "right",
                    va="center",
                    fontsize=max(tick_size - 0.7, 8.2),
                    color="#13293d",
                )
            )

        axes_item.axvline(float(panel["baseline_value"]), color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.axvline(float(panel["predicted_value"]), color="#13293d", linewidth=1.1, linestyle="-", zorder=1)
        axes_item.set_xlim(x_lower, x_upper)
        axes_item.set_ylim(-1.1, len(contributions) - 0.4)
        axes_item.set_yticks(row_positions)
        axes_item.set_yticklabels(feature_labels, fontsize=max(tick_size - 0.6, 8.4))
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.tick_params(axis="y", length=0, pad=6)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)
        case_label_artist = axes_item.text(
            0.16,
            0.965,
            str(panel["case_label"]),
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.4, 8.8),
            color="#475569",
            ha="left",
            va="top",
        )
        baseline_label_artist = axes_item.text(
            0.02,
            0.885,
            f"Baseline {float(panel['baseline_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#475569",
            ha="left",
            va="top",
        )
        prediction_label_artist = axes_item.text(
            0.98,
            0.885,
            f"Prediction {float(panel['predicted_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#13293d",
            ha="right",
            va="top",
        )
        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "bar_artists": bar_artists,
                "value_label_artists": value_label_artists,
                "case_label_artist": case_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.94, top=top_margin, bottom=0.18, wspace=0.30)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            max(0.01, panel_x0 - x_padding * 1.3),
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in panel_records
    ]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_layout_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["panel_title_artist"].get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["case_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"case_label_{panel_token}",
                    box_type="case_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["baseline_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"baseline_label_{panel_token}",
                    box_type="baseline_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"prediction_label_{panel_token}",
                    box_type="prediction_label",
                ),
            ]
        )

        feature_label_box_ids: list[str] = []
        for label_index, tick_label in enumerate(axes_item.get_yticklabels(), start=1):
            if not str(tick_label.get_text() or "").strip():
                continue
            box_id = f"feature_label_{panel_token}_{label_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=tick_label.get_window_extent(renderer=renderer),
                    box_id=box_id,
                    box_type="feature_label",
                )
            )
            feature_label_box_ids.append(box_id)

        contribution_metrics: list[dict[str, Any]] = []
        for contribution_index, (contribution, bar_artist, value_label_artist) in enumerate(
            zip(
                panel["contributions"],
                record["bar_artists"],
                record["value_label_artists"],
                strict=True,
            ),
            start=1,
        ):
            bar_box_id = f"contribution_bar_{panel_token}_{contribution_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=bar_artist.get_window_extent(renderer=renderer),
                    box_id=bar_box_id,
                    box_type="contribution_bar",
                )
            )
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=value_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"contribution_label_{panel_token}_{contribution_index}",
                    box_type="contribution_label",
                )
            )
            contribution_metrics.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution["feature_value_text"]),
                    "shap_value": float(contribution["shap_value"]),
                    "start_value": float(contribution["start_value"]),
                    "end_value": float(contribution["end_value"]),
                    "bar_box_id": bar_box_id,
                    "label_box_id": feature_label_box_ids[contribution_index - 1],
                }
            )

        marker_y0 = -0.95
        marker_y1 = len(panel["contributions"]) - 0.45
        baseline_marker_box_id = f"baseline_marker_{panel_token}"
        prediction_marker_box_id = f"prediction_marker_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["baseline_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["baseline_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=baseline_marker_box_id,
                box_type="baseline_marker",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["predicted_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["predicted_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        normalized_layout_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "baseline_marker_box_id": baseline_marker_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "contributions": contribution_metrics,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "panels": normalized_layout_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_force_like_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    all_values: list[float] = []
    max_contribution_count = 0
    for panel in panels:
        baseline_value = float(panel["baseline_value"])
        predicted_value = float(panel["predicted_value"])
        positive_cursor = baseline_value
        negative_cursor = baseline_value
        normalized_contributions: list[dict[str, Any]] = []
        for contribution in list(panel["contributions"]):
            shap_value = float(contribution["shap_value"])
            direction = "positive" if shap_value > 0 else "negative"
            if direction == "positive":
                start_value = positive_cursor
                end_value = positive_cursor + shap_value
                positive_cursor = end_value
            else:
                start_value = negative_cursor
                end_value = negative_cursor + shap_value
                negative_cursor = end_value
            normalized_contributions.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution.get("feature_value_text") or "").strip(),
                    "shap_value": shap_value,
                    "direction": direction,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )
            all_values.extend((start_value, end_value))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )
        all_values.extend((baseline_value, predicted_value))
        max_contribution_count = max(max_contribution_count, len(normalized_contributions))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.14, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    x_marker_half_width = max(x_span * 0.004, 0.0025)

    figure_width = max(8.8, 3.7 * len(normalized_panels) + 1.8)
    figure_height = max(4.9, 0.35 * max_contribution_count + 3.2)
    fig, axes = plt.subplots(1, len(normalized_panels), figsize=(figure_width, figure_height), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    positive_band = (0.49, 0.57)
    negative_band = (0.30, 0.38)
    marker_y0 = 0.20
    marker_y1 = 0.74

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, normalized_panels, strict=True):
        axes_item.set_xlim(x_lower, x_upper)
        axes_item.set_ylim(0.14, 0.84)
        axes_item.set_yticks([])
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)

        case_label_artist = axes_item.text(
            0.5,
            0.965,
            str(panel["case_label"]),
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.4, 8.8),
            color="#475569",
            ha="center",
            va="top",
        )
        baseline_label_artist = axes_item.text(
            0.02,
            0.885,
            f"Baseline {float(panel['baseline_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#475569",
            ha="left",
            va="top",
        )
        prediction_label_artist = axes_item.text(
            0.98,
            0.885,
            f"Prediction {float(panel['predicted_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#13293d",
            ha="right",
            va="top",
        )

        segment_artists: list[dict[str, Any]] = []
        label_artists: list[Any] = []
        for contribution in panel["contributions"]:
            direction = str(contribution["direction"])
            start_value = float(contribution["start_value"])
            end_value = float(contribution["end_value"])
            left_value = min(start_value, end_value)
            right_value = max(start_value, end_value)
            width = max(right_value - left_value, 1e-9)
            tip_width = min(max(x_span * 0.018, width * 0.22), width * 0.45)
            y0, y1 = positive_band if direction == "positive" else negative_band
            y_mid = (y0 + y1) / 2.0
            if direction == "positive":
                polygon_points = [
                    (left_value, y0),
                    (right_value - tip_width, y0),
                    (right_value, y_mid),
                    (right_value - tip_width, y1),
                    (left_value, y1),
                    (left_value + tip_width * 0.35, y_mid),
                ]
                face_color = matplotlib.colors.to_rgba(positive_color, alpha=0.92)
                edge_color = positive_color
            else:
                polygon_points = [
                    (right_value, y0),
                    (left_value + tip_width, y0),
                    (left_value, y_mid),
                    (left_value + tip_width, y1),
                    (right_value, y1),
                    (right_value - tip_width * 0.35, y_mid),
                ]
                face_color = matplotlib.colors.to_rgba(negative_color, alpha=0.92)
                edge_color = negative_color
            segment_artist = matplotlib.patches.Polygon(
                polygon_points,
                closed=True,
                facecolor=face_color,
                edgecolor=edge_color,
                linewidth=0.85,
                zorder=3,
            )
            axes_item.add_patch(segment_artist)
            segment_artists.append({"artist": segment_artist, "contribution": contribution})

            label_text = (
                f"{contribution['feature']} = {contribution['feature_value_text']}"
                if contribution["feature_value_text"]
                else str(contribution["feature"])
            )
            label_artists.append(
                axes_item.text(
                    (left_value + right_value) / 2.0,
                    y_mid,
                    textwrap.fill(label_text, width=16),
                    fontsize=max(tick_size - 1.6, 7.0),
                    color="white",
                    ha="center",
                    va="center",
                    zorder=4,
                )
            )

        axes_item.axvline(float(panel["baseline_value"]), color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.axvline(float(panel["predicted_value"]), color="#13293d", linewidth=1.15, linestyle="-", zorder=1)
        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "segment_artists": segment_artists,
                "label_artists": label_artists,
                "case_label_artist": case_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.10, right=0.95, top=top_margin, bottom=0.19, wspace=0.28)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in panel_records
    ]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_layout_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["panel_title_artist"].get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["case_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"case_label_{panel_token}",
                    box_type="case_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["baseline_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"baseline_label_{panel_token}",
                    box_type="baseline_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"prediction_label_{panel_token}",
                    box_type="prediction_label",
                ),
            ]
        )

        contribution_metrics: list[dict[str, Any]] = []
        for contribution_index, (segment_record, label_artist) in enumerate(
            zip(record["segment_artists"], record["label_artists"], strict=True),
            start=1,
        ):
            contribution = segment_record["contribution"]
            direction = str(contribution["direction"])
            segment_box_id = f"{direction}_force_segment_{panel_token}_{contribution_index}"
            label_box_id = f"force_label_{panel_token}_{contribution_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=segment_record["artist"].get_window_extent(renderer=renderer),
                    box_id=segment_box_id,
                    box_type=f"{direction}_force_segment",
                )
            )
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="force_feature_label",
                )
            )
            contribution_metrics.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution["feature_value_text"]),
                    "shap_value": float(contribution["shap_value"]),
                    "direction": direction,
                    "start_value": float(contribution["start_value"]),
                    "end_value": float(contribution["end_value"]),
                    "segment_box_id": segment_box_id,
                    "label_box_id": label_box_id,
                }
            )

        baseline_marker_box_id = f"baseline_marker_{panel_token}"
        prediction_marker_box_id = f"prediction_marker_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["baseline_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["baseline_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=baseline_marker_box_id,
                box_type="baseline_marker",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["predicted_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["predicted_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        normalized_layout_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "baseline_marker_box_id": baseline_marker_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "contributions": contribution_metrics,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "panels": normalized_layout_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_grouped_local_explanation_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    zero_line_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    max_abs_value = 0.0
    max_contribution_count = 0
    for panel in panels:
        contributions = []
        for contribution in panel["contributions"]:
            shap_value = float(contribution["shap_value"])
            max_abs_value = max(max_abs_value, abs(shap_value))
            contributions.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": shap_value,
                }
            )
        max_contribution_count = max(max_contribution_count, len(contributions))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "contributions": contributions,
            }
        )

    x_padding = max(max_abs_value * 0.20, 0.05)
    x_limit = max_abs_value + x_padding
    label_margin = max(x_limit * 0.06, 0.03)

    figure_width = max(8.8, 3.8 * len(normalized_panels) + 1.7)
    figure_height = max(4.8, 0.58 * max_contribution_count + 2.2)
    fig, axes = plt.subplots(1, len(normalized_panels), figsize=(figure_width, figure_height), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, normalized_panels, strict=True):
        contributions = list(panel["contributions"])
        row_positions = list(range(len(contributions)))
        values = [float(item["shap_value"]) for item in contributions]
        feature_labels = [str(item["feature"]) for item in contributions]
        colors = [
            matplotlib.colors.to_rgba(positive_color if value > 0 else negative_color, alpha=0.92)
            for value in values
        ]
        edge_colors = [positive_color if value > 0 else negative_color for value in values]

        bar_artists = axes_item.barh(
            row_positions,
            values,
            height=0.58,
            color=colors,
            edgecolor=edge_colors,
            linewidth=0.9,
            zorder=3,
        )
        value_label_artists: list[Any] = []
        for row_position, value in zip(row_positions, values, strict=True):
            text_x = value + label_margin if value > 0 else value - label_margin
            text_x = min(max(text_x, -x_limit + label_margin), x_limit - label_margin)
            value_label_artists.append(
                axes_item.text(
                    text_x,
                    row_position,
                    f"{value:+.2f}",
                    fontsize=max(tick_size - 0.6, 8.3),
                    color="#334155",
                    va="center",
                    ha="left" if value > 0 else "right",
                )
            )

        axes_item.axvline(0.0, color=zero_line_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit, x_limit)
        axes_item.set_ylim(-0.7, len(contributions) - 0.35)
        axes_item.set_yticks(row_positions)
        axes_item.set_yticklabels(feature_labels, fontsize=max(tick_size - 0.4, 8.5))
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.tick_params(axis="y", length=0, pad=8)
        _apply_publication_axes_style(axes_item)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")

        group_label_artist = axes_item.text(
            0.5,
            0.965,
            str(panel["group_label"]),
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.4, 8.8),
            color="#475569",
            ha="center",
            va="top",
        )
        baseline_label_artist = axes_item.text(
            0.02,
            0.885,
            f"Baseline {float(panel['baseline_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#475569",
            ha="left",
            va="top",
        )
        prediction_label_artist = axes_item.text(
            0.98,
            0.885,
            f"Prediction {float(panel['predicted_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#13293d",
            ha="right",
            va="top",
        )

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "bar_artists": list(bar_artists),
                "value_label_artists": value_label_artists,
                "group_label_artist": group_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.28, right=0.95, top=top_margin, bottom=0.18, wspace=0.32)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            max(0.01, panel_x0 - x_padding * 1.3),
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in panel_records
    ]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    layout_metrics_panels: list[dict[str, Any]] = []
    zero_line_half_width = max((x_limit * 2.0) * 0.004, 0.01)

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["panel_title_artist"].get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["group_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"group_label_{panel_token}",
                    box_type="group_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["baseline_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"baseline_label_{panel_token}",
                    box_type="baseline_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"prediction_label_{panel_token}",
                    box_type="prediction_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
            ]
        )

        feature_label_box_ids: list[str] = []
        for label_index, tick_label in enumerate(axes_item.get_yticklabels(), start=1):
            if not str(tick_label.get_text() or "").strip():
                continue
            box_id = f"feature_label_{panel_token}_{label_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=tick_label.get_window_extent(renderer=renderer),
                    box_id=box_id,
                    box_type="feature_label",
                )
            )
            feature_label_box_ids.append(box_id)

        contribution_metrics: list[dict[str, Any]] = []
        for contribution_index, (contribution, bar_artist, value_label_artist) in enumerate(
            zip(panel["contributions"], record["bar_artists"], record["value_label_artists"], strict=True),
            start=1,
        ):
            bar_box_id = f"contribution_bar_{panel_token}_{contribution_index}"
            value_label_box_id = f"value_label_{panel_token}_{contribution_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=bar_artist.get_window_extent(renderer=renderer),
                    box_id=bar_box_id,
                    box_type="contribution_bar",
                )
            )
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=value_label_artist.get_window_extent(renderer=renderer),
                    box_id=value_label_box_id,
                    box_type="value_label",
                )
            )
            contribution_metrics.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": float(contribution["shap_value"]),
                    "bar_box_id": bar_box_id,
                    "feature_label_box_id": feature_label_box_ids[contribution_index - 1],
                    "value_label_box_id": value_label_box_id,
                }
            )

        zero_line_box_id = f"zero_line_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=-zero_line_half_width,
                y0=-0.7,
                x1=zero_line_half_width,
                y1=len(panel["contributions"]) - 0.35,
                box_id=zero_line_box_id,
                box_type="zero_line",
            )
        )
        layout_metrics_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "zero_line_box_id": zero_line_box_id,
                "contributions": contribution_metrics,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "panels": layout_metrics_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_grouped_decision_path_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    groups = list(display_payload.get("groups") or [])
    if len(groups) != 2:
        raise RuntimeError(f"{template_id} requires exactly two groups")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    group_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
    ]
    baseline_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    feature_order = list(display_payload.get("feature_order") or [])
    if not feature_order:
        feature_order = [str(item["feature"]) for item in groups[0]["contributions"]]
    baseline_value = float(display_payload["baseline_value"])
    all_values = [baseline_value]
    for group in groups:
        all_values.append(float(group["predicted_value"]))
        for contribution in group["contributions"]:
            all_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    y_start = -0.55
    row_positions = list(range(len(feature_order)))
    y_lower = row_positions[-1] + 0.55
    y_upper = y_start - 0.25

    fig = plt.figure(figsize=(8.6, max(4.8, 2.9 + 0.35 * len(feature_order))))
    ax = fig.add_subplot(1, 1, 1)
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.86,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    ax.set_xlim(x_lower, x_upper)
    ax.set_ylim(y_lower, y_upper)
    ax.set_yticks(row_positions)
    ax.set_yticklabels(feature_order, fontsize=max(tick_size - 0.2, 8.6))
    ax.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_title(
        str(display_payload.get("panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    ax.tick_params(axis="y", length=0, pad=8, colors="#2F3437")
    ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    ax.grid(axis="y", visible=False)
    _apply_publication_axes_style(ax)

    ax.axvline(baseline_value, color=baseline_color, linewidth=1.1, linestyle="--", zorder=1)

    line_records: list[dict[str, Any]] = []
    legend_handles: list[Any] = []
    label_padding = max(x_span * 0.04, 0.03)
    for group, color in zip(groups, group_colors, strict=True):
        x_values = [baseline_value] + [float(item["end_value"]) for item in group["contributions"]]
        y_values = [y_start] + row_positions
        line_artist = ax.plot(
            x_values,
            y_values,
            color=color,
            linewidth=2.1,
            marker="o",
            markersize=4.8,
            markeredgecolor="white",
            markeredgewidth=0.6,
            zorder=3,
        )[0]
        prediction_x = x_values[-1]
        prediction_y = y_values[-1]
        prediction_marker_artist = ax.scatter(
            [prediction_x],
            [prediction_y],
            s=42,
            color=color,
            edgecolors="white",
            linewidths=0.7,
            zorder=4,
        )
        if prediction_x >= baseline_value:
            label_x = min(x_upper - label_padding * 0.3, prediction_x + label_padding)
            ha = "left"
        else:
            label_x = max(x_lower + label_padding * 0.3, prediction_x - label_padding)
            ha = "right"
        prediction_label_artist = ax.text(
            label_x,
            prediction_y,
            f"{float(group['predicted_value']):.2f}",
            fontsize=max(tick_size - 0.6, 8.2),
            color="#334155",
            ha=ha,
            va="center",
            zorder=4,
        )
        legend_handles.append(
            matplotlib.lines.Line2D(
                [0],
                [0],
                color=color,
                linewidth=2.1,
                marker="o",
                markersize=5.0,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=str(group["group_label"]),
            )
        )
        line_records.append(
            {
                "group": group,
                "line_artist": line_artist,
                "prediction_marker_artist": prediction_marker_artist,
                "prediction_label_artist": prediction_label_artist,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.89
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.58, top=top_margin, bottom=0.16)
    legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="center left",
        bbox_to_anchor=(0.66, 0.54),
        bbox_transform=fig.transFigure,
        frameon=True,
        framealpha=1.0,
        edgecolor="#d7dee7",
        fontsize=max(tick_size - 0.5, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.6),
    )
    legend.get_frame().set_facecolor("white")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel_decision_path",
        box_type="panel",
    )
    panel_boxes = [panel_box]
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.title.get_window_extent(renderer=renderer),
                box_id="panel_title",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="legend_title",
                box_type="legend_title",
            ),
        ]
    )

    feature_label_box_ids: list[str] = []
    for index, tick_label in enumerate(ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
        feature_label_box_ids.append(box_id)

    line_half_width = max((x_upper - x_lower) * 0.004, 0.003)
    marker_half_width = max((x_upper - x_lower) * 0.007, 0.004)
    marker_half_height = 0.10
    guide_boxes: list[dict[str, Any]] = [
        _data_box_to_layout_box(
            axes=ax,
            figure=fig,
            x0=baseline_value - line_half_width,
            y0=y_start,
            x1=baseline_value + line_half_width,
            y1=row_positions[-1],
            box_id="baseline_reference_line",
            box_type="baseline_reference_line",
        )
    ]

    metrics_groups: list[dict[str, Any]] = []
    for record in line_records:
        group = record["group"]
        group_token = re.sub(r"[^A-Za-z0-9]+", "_", str(group["group_id"])) or "group"
        line_box_id = f"decision_path_line_{group_token}"
        prediction_marker_box_id = f"prediction_marker_{group_token}"
        prediction_label_box_id = f"prediction_label_{group_token}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["line_artist"].get_window_extent(renderer=renderer),
                box_id=line_box_id,
                box_type="decision_path_line",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                box_id=prediction_label_box_id,
                box_type="prediction_label",
            )
        )
        prediction_x = float(group["contributions"][-1]["end_value"])
        prediction_y = row_positions[-1]
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=ax,
                figure=fig,
                x0=prediction_x - marker_half_width,
                y0=prediction_y - marker_half_height,
                x1=prediction_x + marker_half_width,
                y1=prediction_y + marker_half_height,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        metrics_groups.append(
            {
                "group_id": str(group["group_id"]),
                "group_label": str(group["group_label"]),
                "predicted_value": float(group["predicted_value"]),
                "line_box_id": line_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "prediction_label_box_id": prediction_label_box_id,
                "contributions": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "shap_value": float(item["shap_value"]),
                        "start_value": float(item["start_value"]),
                        "end_value": float(item["end_value"]),
                    }
                    for item in group["contributions"]
                ],
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": baseline_value,
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "feature_order": [str(item) for item in feature_order],
                "feature_label_box_ids": feature_label_box_ids,
                "groups": metrics_groups,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_multigroup_decision_path_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    groups = list(display_payload.get("groups") or [])
    if len(groups) != 3:
        raise RuntimeError(f"{template_id} requires exactly three groups")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    group_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("contrast") or palette.get("secondary") or "#2F5D8A").strip() or "#2F5D8A",
    ]
    baseline_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    feature_order = list(display_payload.get("feature_order") or [])
    if not feature_order:
        feature_order = [str(item["feature"]) for item in groups[0]["contributions"]]
    baseline_value = float(display_payload["baseline_value"])
    all_values = [baseline_value]
    for group in groups:
        all_values.append(float(group["predicted_value"]))
        for contribution in group["contributions"]:
            all_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    y_start = -0.55
    row_positions = list(range(len(feature_order)))
    y_lower = row_positions[-1] + 0.55
    y_upper = y_start - 0.25

    fig = plt.figure(figsize=(9.0, max(4.8, 2.9 + 0.35 * len(feature_order))))
    ax = fig.add_subplot(1, 1, 1)
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.82,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    ax.set_xlim(x_lower, x_upper)
    ax.set_ylim(y_lower, y_upper)
    ax.set_yticks(row_positions)
    ax.set_yticklabels(feature_order, fontsize=max(tick_size - 0.2, 8.6))
    ax.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_title(
        str(display_payload.get("panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    ax.tick_params(axis="y", length=0, pad=8, colors="#2F3437")
    ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    ax.grid(axis="y", visible=False)
    _apply_publication_axes_style(ax)

    ax.axvline(baseline_value, color=baseline_color, linewidth=1.1, linestyle="--", zorder=1)

    line_records: list[dict[str, Any]] = []
    legend_handles: list[Any] = []
    label_padding = max(x_span * 0.04, 0.03)
    for group, color in zip(groups, group_colors, strict=True):
        x_values = [baseline_value] + [float(item["end_value"]) for item in group["contributions"]]
        y_values = [y_start] + row_positions
        line_artist = ax.plot(
            x_values,
            y_values,
            color=color,
            linewidth=2.1,
            marker="o",
            markersize=4.8,
            markeredgecolor="white",
            markeredgewidth=0.6,
            zorder=3,
        )[0]
        prediction_x = x_values[-1]
        prediction_y = y_values[-1]
        prediction_marker_artist = ax.scatter(
            [prediction_x],
            [prediction_y],
            s=42,
            color=color,
            edgecolors="white",
            linewidths=0.7,
            zorder=4,
        )
        if prediction_x >= baseline_value:
            label_x = min(x_upper - label_padding * 0.3, prediction_x + label_padding)
            ha = "left"
        else:
            label_x = max(x_lower + label_padding * 0.3, prediction_x - label_padding)
            ha = "right"
        prediction_label_artist = ax.text(
            label_x,
            prediction_y,
            f"{float(group['predicted_value']):.2f}",
            fontsize=max(tick_size - 0.6, 8.2),
            color="#334155",
            ha=ha,
            va="center",
            zorder=4,
        )
        legend_handles.append(
            matplotlib.lines.Line2D(
                [0],
                [0],
                color=color,
                linewidth=2.1,
                marker="o",
                markersize=5.0,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=str(group["group_label"]),
            )
        )
        line_records.append(
            {
                "group": group,
                "line_artist": line_artist,
                "prediction_marker_artist": prediction_marker_artist,
                "prediction_label_artist": prediction_label_artist,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.89
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.56, top=top_margin, bottom=0.16)
    legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="center left",
        bbox_to_anchor=(0.64, 0.54),
        bbox_transform=fig.transFigure,
        frameon=True,
        framealpha=1.0,
        edgecolor="#d7dee7",
        fontsize=max(tick_size - 0.5, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.6),
    )
    legend.get_frame().set_facecolor("white")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel_decision_path",
        box_type="panel",
    )
    panel_boxes = [panel_box]
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.title.get_window_extent(renderer=renderer),
                box_id="panel_title",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="legend_title",
                box_type="legend_title",
            ),
        ]
    )

    feature_label_box_ids: list[str] = []
    for index, tick_label in enumerate(ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
        feature_label_box_ids.append(box_id)

    line_half_width = max((x_upper - x_lower) * 0.004, 0.003)
    marker_half_width = max((x_upper - x_lower) * 0.007, 0.004)
    marker_half_height = 0.10
    guide_boxes: list[dict[str, Any]] = [
        _data_box_to_layout_box(
            axes=ax,
            figure=fig,
            x0=baseline_value - line_half_width,
            y0=y_start,
            x1=baseline_value + line_half_width,
            y1=row_positions[-1],
            box_id="baseline_reference_line",
            box_type="baseline_reference_line",
        )
    ]

    metrics_groups: list[dict[str, Any]] = []
    for record in line_records:
        group = record["group"]
        group_token = re.sub(r"[^A-Za-z0-9]+", "_", str(group["group_id"])) or "group"
        line_box_id = f"decision_path_line_{group_token}"
        prediction_marker_box_id = f"prediction_marker_{group_token}"
        prediction_label_box_id = f"prediction_label_{group_token}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["line_artist"].get_window_extent(renderer=renderer),
                box_id=line_box_id,
                box_type="decision_path_line",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                box_id=prediction_label_box_id,
                box_type="prediction_label",
            )
        )
        prediction_x = float(group["contributions"][-1]["end_value"])
        prediction_y = row_positions[-1]
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=ax,
                figure=fig,
                x0=prediction_x - marker_half_width,
                y0=prediction_y - marker_half_height,
                x1=prediction_x + marker_half_width,
                y1=prediction_y + marker_half_height,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        metrics_groups.append(
            {
                "group_id": str(group["group_id"]),
                "group_label": str(group["group_label"]),
                "predicted_value": float(group["predicted_value"]),
                "line_box_id": line_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "prediction_label_box_id": prediction_label_box_id,
                "contributions": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "shap_value": float(item["shap_value"]),
                        "start_value": float(item["start_value"]),
                        "end_value": float(item["end_value"]),
                    }
                    for item in group["contributions"]
                ],
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": baseline_value,
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "feature_order": [str(item) for item in feature_order],
                "feature_label_box_ids": feature_label_box_ids,
                "groups": metrics_groups,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
