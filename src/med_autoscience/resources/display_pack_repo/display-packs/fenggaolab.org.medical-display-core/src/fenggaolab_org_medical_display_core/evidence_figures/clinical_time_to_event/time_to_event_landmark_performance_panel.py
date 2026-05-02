from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _data_box_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_time_to_event_landmark_performance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    landmark_summaries = list(display_payload.get("landmark_summaries") or [])
    if not landmark_summaries:
        raise RuntimeError(f"{template_id} requires non-empty landmark_summaries")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    discrimination_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    error_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    calibration_color = str(palette.get("primary") or discrimination_color).strip() or discrimination_color
    discrimination_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    error_fill = str(palette.get("secondary_soft") or "#fee2e2").strip() or "#fee2e2"
    calibration_fill = str(palette.get("primary_soft") or "#dbeafe").strip() or "#dbeafe"

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(11.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.2, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    def _build_metric_rows(metric_key: str) -> list[dict[str, Any]]:
        normalized_rows: list[dict[str, Any]] = []
        for item in landmark_summaries:
            row = {
                "label": str(item["window_label"]),
                "analysis_window_label": str(item["analysis_window_label"]),
                "landmark_months": int(item["landmark_months"]),
                "prediction_months": int(item["prediction_months"]),
                "value": float(item[metric_key]),
            }
            annotation = str(item.get("annotation") or "").strip()
            if annotation:
                row["annotation"] = annotation
            normalized_rows.append(row)
        return normalized_rows

    metric_panels = [
        {
            "panel_id": "discrimination_panel",
            "panel_label": "A",
            "metric_kind": "c_index",
            "title": str(display_payload.get("discrimination_panel_title") or "").strip(),
            "x_label": str(display_payload.get("discrimination_x_label") or "").strip(),
            "rows": _build_metric_rows("c_index"),
        },
        {
            "panel_id": "error_panel",
            "panel_label": "B",
            "metric_kind": "brier_score",
            "title": str(display_payload.get("error_panel_title") or "").strip(),
            "x_label": str(display_payload.get("error_x_label") or "").strip(),
            "rows": _build_metric_rows("brier_score"),
        },
        {
            "panel_id": "calibration_panel",
            "panel_label": "C",
            "metric_kind": "calibration_slope",
            "title": str(display_payload.get("calibration_panel_title") or "").strip(),
            "x_label": str(display_payload.get("calibration_x_label") or "").strip(),
            "reference_value": 1.0,
            "rows": _build_metric_rows("calibration_slope"),
        },
    ]

    def _panel_limits(
        rows: list[dict[str, Any]],
        *,
        reference_value: float | None,
        clamp_probability: bool,
    ) -> tuple[float, float]:
        values = [float(item["value"]) for item in rows]
        if reference_value is not None:
            values.append(float(reference_value))
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum
        padding = max(span * 0.20, 0.035 if clamp_probability else 0.08)
        lower = minimum - padding
        upper = maximum + padding
        if clamp_probability:
            lower = max(0.0, lower)
            upper = min(1.0, upper)
        if upper <= lower:
            upper = lower + (0.10 if clamp_probability else 0.25)
        return lower, upper

    figure_height = max(4.8, 0.42 * len(landmark_summaries) + 3.4)
    fig, axes = plt.subplots(1, 3, figsize=(12.4, figure_height))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
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
    reference_specs: list[tuple[Any, float, int]] = []

    row_labels = [str(item["window_label"]) for item in landmark_summaries]
    row_positions = list(range(len(row_labels)))
    y_axis_title_artist = None
    panel_style = (
        (discrimination_color, discrimination_fill),
        (error_color, error_fill),
        (calibration_color, calibration_fill),
    )

    for panel_index, (axes_item, panel, style) in enumerate(zip(axes_list, metric_panels, panel_style, strict=True), start=1):
        line_color, fill_color = style
        rows = list(panel["rows"])
        values = [float(item["value"]) for item in rows]
        lower_limit, upper_limit = _panel_limits(
            rows,
            reference_value=float(panel["reference_value"]) if panel.get("reference_value") is not None else None,
            clamp_probability=str(panel["metric_kind"]) in {"c_index", "brier_score"},
        )

        if panel.get("reference_value") is not None:
            reference_specs.append((axes_item, float(panel["reference_value"]), len(rows)))
            axes_item.axvline(
                float(panel["reference_value"]),
                color=reference_color,
                linewidth=1.0,
                linestyle="--",
                zorder=1,
            )

        axes_item.hlines(
            row_positions,
            [lower_limit] * len(row_positions),
            values,
            color=matplotlib.colors.to_rgba(fill_color, alpha=0.96),
            linewidth=2.2,
            zorder=2,
        )
        axes_item.scatter(
            values,
            row_positions,
            s=marker_size**2,
            color=line_color,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )

        axes_item.set_xlim(lower_limit, upper_limit)
        axes_item.set_ylim(-0.6, len(rows) - 0.4)
        axes_item.set_yticks(row_positions)
        if panel_index == 1:
            axes_item.set_yticklabels(row_labels, fontsize=max(tick_size - 1.0, 8.2), color="#2F3437")
            axes_item.set_ylabel(
                "Landmark window",
                fontsize=axis_title_size,
                fontweight="bold",
                color="#13293d",
                labelpad=16,
            )
            y_axis_title_artist = axes_item.yaxis.label
        else:
            axes_item.set_yticklabels([""] * len(row_labels))
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        panel_title_artists.append(
            axes_item.set_title(
                str(panel["title"]),
                fontsize=axis_title_size,
                fontweight="bold",
                color="#334155",
                pad=10.0,
            )
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.tick_params(axis="y", length=0, pad=6 if panel_index == 1 else 0)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)

    top_margin = 0.78 if show_figure_title else 0.88
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.22, right=0.985, top=top_margin, bottom=0.20, wspace=0.28)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.030, 0.010), 0.018)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.2, 12.8),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=axes_list[0], label="A"),
        _add_panel_label(axes_item=axes_list[1], label="B"),
        _add_panel_label(axes_item=axes_list[2], label="C"),
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
    marker_index = 1

    for panel_index, (axes_item, panel_title_artist, panel_label_artist, panel) in enumerate(
        zip(axes_list, panel_title_artists, panel_label_artists, metric_panels, strict=True),
        start=1,
    ):
        panel_token = str(panel["panel_label"])
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_title_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_token}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"x_axis_title_{panel_token}",
                box_type="subplot_x_axis_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_token}",
                box_type="panel_label",
            )
        )
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_token}",
                box_type="metric_panel",
            )
        )
        lower_limit, upper_limit = axes_item.get_xlim()
        x_radius = max((upper_limit - lower_limit) * 0.018, 0.008)
        for row_position, row in enumerate(panel["rows"]):
            value = float(row["value"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
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

    if y_axis_title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="y_axis_title_A",
                box_type="subplot_y_axis_title",
            )
        )

    for index, (axes_item, reference_value, row_count) in enumerate(reference_specs, start=1):
        lower_limit, upper_limit = axes_item.get_xlim()
        x_radius = max((upper_limit - lower_limit) * 0.012, 0.006)
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=reference_value - x_radius,
                y0=-0.45,
                x1=reference_value + x_radius,
                y1=float(max(row_count - 1, 0)) + 0.45,
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
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

