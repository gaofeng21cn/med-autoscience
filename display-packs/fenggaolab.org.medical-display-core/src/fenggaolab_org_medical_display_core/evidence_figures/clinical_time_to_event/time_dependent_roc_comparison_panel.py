from __future__ import annotations

from pathlib import Path
import re
import textwrap
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_time_dependent_roc_comparison_panel(
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
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

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
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    color_cycle = (
        str(palette.get("primary") or model_color).strip() or model_color,
        str(palette.get("secondary") or comparator_color).strip() or comparator_color,
        str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F",
    )

    panel_count = len(panels)
    figure_width = max(10.2, 4.25 * panel_count + 0.8)
    fig, axes = plt.subplots(1, panel_count, figsize=(figure_width, 4.8))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.90,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    x_axis_artist = fig.text(
        0.5,
        0.055,
        str(display_payload.get("x_label") or "").strip(),
        ha="center",
        va="center",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    y_axis_artist = fig.text(
        0.018,
        0.52,
        str(display_payload.get("y_label") or "").strip(),
        ha="center",
        va="center",
        rotation="vertical",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )

    panel_title_artists: list[Any] = []
    panel_label_artists: list[Any] = []
    panel_annotation_artists: list[Any] = []
    normalized_panels: list[dict[str, Any]] = []
    shared_legend_handles: list[Any] | None = None
    shared_legend_labels: list[str] | None = None

    for axes_index, (axes, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        series = list(panel.get("series") or [])
        if not series:
            raise RuntimeError(f"{template_id} panel {axes_index} requires non-empty series")

        normalized_series: list[dict[str, Any]] = []
        normalized_reference_line: dict[str, Any] | None = None
        reference_line = panel.get("reference_line")
        if isinstance(reference_line, dict):
            ref_x = [float(value) for value in reference_line.get("x") or []]
            ref_y = [float(value) for value in reference_line.get("y") or []]
            normalized_reference_line = {
                "label": str(reference_line.get("label") or "").strip(),
                "x": ref_x,
                "y": ref_y,
            }
            axes.plot(
                ref_x,
                ref_y,
                linewidth=1.2,
                color=reference_color,
                linestyle="--",
                label=str(reference_line.get("label") or "Chance"),
                zorder=1,
            )

        for series_index, series_item in enumerate(series):
            x_values = [float(value) for value in series_item["x"]]
            y_values = [float(value) for value in series_item["y"]]
            line_color = color_cycle[series_index % len(color_cycle)]
            axes.plot(
                x_values,
                y_values,
                linewidth=2.0,
                color=line_color,
                label=str(series_item["label"]),
                zorder=2 + series_index,
            )
            normalized_series.append(
                {
                    "label": str(series_item["label"]),
                    "x": x_values,
                    "y": y_values,
                    "annotation": str(series_item.get("annotation") or "").strip(),
                }
            )

        axes.set_xlim(0.0, 1.0)
        axes.set_ylim(0.0, 1.0)
        axes.set_title(
            textwrap.fill(str(panel.get("title") or "").strip(), width=28),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
            pad=10.0,
        )
        axes.tick_params(axis="both", labelsize=tick_size, colors="#2F3437")
        axes.grid(color="#E6EDF5", linewidth=0.8, linestyle=":")
        _apply_publication_axes_style(axes)

        panel_label = str(panel.get("panel_label") or "").strip()
        panel_label_artists.append(
            axes.text(
                0.02,
                0.98,
                panel_label,
                transform=axes.transAxes,
                fontsize=panel_label_size,
                fontweight="bold",
                color="#2F3437",
                ha="left",
                va="top",
            )
        )
        panel_title_artists.append(axes.title)

        annotation_lines = [str(panel.get("analysis_window_label") or "").strip()]
        if panel.get("time_horizon_months") is not None:
            annotation_lines.append(f"Horizon: {int(panel['time_horizon_months'])} months")
        annotation = str(panel.get("annotation") or "").strip()
        if annotation:
            annotation_lines.append(annotation)
        annotation_artist = axes.text(
            0.03,
            0.05,
            "\n".join(item for item in annotation_lines if item),
            transform=axes.transAxes,
            fontsize=max(tick_size - 0.6, 8.1),
            color=reference_color,
            ha="left",
            va="bottom",
        )
        panel_annotation_artists.append(annotation_artist)

        if shared_legend_handles is None:
            legend_handles, legend_labels = axes.get_legend_handles_labels()
            shared_legend_handles = list(legend_handles)
            shared_legend_labels = list(legend_labels)

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_label,
                "title": str(panel["title"]),
                "analysis_window_label": str(panel["analysis_window_label"]),
                "time_horizon_months": (
                    int(panel["time_horizon_months"]) if panel.get("time_horizon_months") is not None else None
                ),
                "annotation": annotation,
                "series": normalized_series,
                "reference_line": normalized_reference_line,
            }
        )

    top_margin = 0.80 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.07, right=0.99, top=top_margin, bottom=0.28, wspace=0.28)
    legend = None
    if shared_legend_handles and shared_legend_labels:
        legend = fig.legend(
            shared_legend_handles,
            shared_legend_labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.06),
            ncol=min(3, len(shared_legend_labels)),
            frameon=False,
            fontsize=max(tick_size - 1.2, 8.0),
            handlelength=2.2,
            columnspacing=1.3,
        )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=x_axis_artist.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
    ]
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

    panel_boxes: list[dict[str, Any]] = []
    for axes, panel, title_artist_item, label_artist_item, annotation_artist_item in zip(
        axes_list,
        normalized_panels,
        panel_title_artists,
        panel_label_artists,
        panel_annotation_artists,
        strict=True,
    ):
        panel_label_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_label_token}",
                box_type="panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_label_token}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_label_token}",
                box_type="panel_label",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=annotation_artist_item.get_window_extent(renderer=renderer),
                box_id=f"annotation_{panel_label_token}",
                box_type="annotation_text",
            )
        )

    guide_boxes: list[dict[str, Any]] = []
    if legend is not None:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend",
                box_type="legend",
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
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

