from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _normalize_reference_line_to_device_space,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    dump_json,
)

def _render_python_time_to_event_decision_curve(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    series = list(display_payload.get("series") or [])
    if not series:
        raise RuntimeError(f"{template_id} requires non-empty series")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    treated_fraction_series = dict(display_payload.get("treated_fraction_series") or {})
    if not treated_fraction_series:
        raise RuntimeError(f"{template_id} requires treated_fraction_series")

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
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_legend = _read_bool_override(layout_override, "show_legend", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.8, 4.2))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=reference_color,
        )
    extra_series_palette = (
        str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("secondary") or comparator_color).strip() or comparator_color,
        str(palette.get("neutral") or reference_color).strip() or reference_color,
        str(palette.get("primary_soft") or model_color).strip() or model_color,
    )
    x_values = [float(value) for item in series for value in item["x"]]
    y_values = [float(value) for item in series for value in item["y"]]
    reference_line = display_payload.get("reference_line")
    if isinstance(reference_line, dict):
        x_values.extend(float(value) for value in reference_line.get("x", []))
        y_values.extend(float(value) for value in reference_line.get("y", []))
    highlight_band = layout_override.get("highlight_band")
    if isinstance(highlight_band, dict):
        xmin = highlight_band.get("xmin")
        xmax = highlight_band.get("xmax")
        if (
            isinstance(xmin, (int, float))
            and not isinstance(xmin, bool)
            and isinstance(xmax, (int, float))
            and not isinstance(xmax, bool)
            and float(xmin) < float(xmax)
        ):
            highlight_band_color = _require_non_empty_string(
                style_roles.get("highlight_band"),
                label=f"{template_id} render_context.style_roles.highlight_band",
            )
            left_axes.axvspan(float(xmin), float(xmax), color=highlight_band_color, alpha=0.22, zorder=0)
    for index, item in enumerate(series):
        label = str(item["label"])
        normalized_label = label.casefold()
        if "treat all" in normalized_label:
            line_color = comparator_color
        elif index == 0:
            line_color = model_color
        else:
            line_color = extra_series_palette[(index - 1) % len(extra_series_palette)]
        left_axes.plot(
            item["x"],
            item["y"],
            linewidth=2.0,
            color=line_color,
            label=label,
        )
    if isinstance(reference_line, dict):
        left_axes.plot(
            reference_line["x"],
            reference_line["y"],
            linewidth=1.0,
            linestyle="--",
            color=reference_color,
            label=str(reference_line.get("label") or ""),
        )
    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(y_values)
    y_max = max(y_values)
    x_padding = max((x_max - x_min) * 0.04, 0.01)
    y_padding = max((y_max - y_min) * 0.10, 0.02)
    left_axes.set_xlim(x_min - x_padding, x_max + x_padding)
    left_axes.set_ylim(y_min - y_padding, y_max + y_padding)
    left_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    left_axes.set_ylabel(str(display_payload.get("y_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    left_axes.set_title(str(display_payload.get("panel_a_title") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    _apply_publication_axes_style(left_axes)
    left_panel_label = left_axes.text(
        0.02,
        0.98,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=reference_color,
        ha="left",
        va="top",
    )

    right_x_values = [float(value) for value in treated_fraction_series["x"]]
    right_y_values = [float(value) for value in treated_fraction_series["y"]]
    right_axes.plot(
        treated_fraction_series["x"],
        treated_fraction_series["y"],
        linewidth=2.2,
        marker="o",
        markersize=4.8,
        color=model_color,
    )
    right_x_padding = max((max(right_x_values) - min(right_x_values)) * 0.04, 0.01)
    right_y_padding = max((max(right_y_values) - min(right_y_values)) * 0.10, 0.5)
    right_axes.set_xlim(min(right_x_values) - right_x_padding, max(right_x_values) + right_x_padding)
    right_axes.set_ylim(min(0.0, min(right_y_values) - right_y_padding), max(right_y_values) + right_y_padding)
    right_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    right_axes.set_ylabel(
        str(display_payload.get("treated_fraction_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    right_axes.set_title(str(display_payload.get("panel_b_title") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    right_axes.grid(axis="y", color="#e6edf2", linewidth=0.4)
    right_axes.grid(axis="x", visible=False)
    right_axes.spines["top"].set_visible(False)
    right_axes.spines["right"].set_visible(False)
    right_panel_label = right_axes.text(
        0.02,
        0.98,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=reference_color,
        ha="left",
        va="top",
    )

    handles, labels = left_axes.get_legend_handles_labels()
    legend_position = "none" if not show_legend else str(layout_override.get("legend_position") or "lower_center").strip().lower()
    legend = None
    if legend_position != "none":
        if legend_position == "right_bottom":
            legend = fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.98, 0.02), ncol=1, frameon=False)
        else:
            legend = fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=3, frameon=False)
    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        bottom=0.22 if show_legend else 0.12,
        top=0.82 if show_figure_title else 0.90,
        wspace=0.28,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    normalized_reference_line = _normalize_reference_line_to_device_space(
        reference_line=reference_line,
        axes=left_axes,
        figure=fig,
    )
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_left_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_right_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_A",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_B",
            box_type="panel_label",
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
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=left_axes.get_window_extent(renderer=renderer),
                    box_id="panel_left",
                    box_type="panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_axes.get_window_extent(renderer=renderer),
                    box_id="panel_right",
                    box_type="panel",
                ),
            ],
            "guide_boxes": []
            if legend is None
            else [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "series": series,
                "reference_line": normalized_reference_line,
                "treated_fraction_series": {
                    "label": str(treated_fraction_series["label"]),
                    "x": [float(value) for value in treated_fraction_series["x"]],
                    "y": [float(value) for value in treated_fraction_series["y"]],
                },
                "time_horizon_months": (
                    int(display_payload["time_horizon_months"])
                    if display_payload.get("time_horizon_months") is not None
                    else None
                ),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

