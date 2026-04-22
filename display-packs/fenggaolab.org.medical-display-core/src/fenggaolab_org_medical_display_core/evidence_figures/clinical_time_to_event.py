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
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _normalize_reference_line_collection_to_device_space,
    _normalize_reference_line_to_device_space,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
    dump_json,
    load_json,
)

def _render_python_risk_layering_monotonic_bars(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    left_bars = list(display_payload.get("left_bars") or [])
    right_bars = list(display_payload.get("right_bars") or [])
    if not left_bars or not right_bars:
        raise RuntimeError(f"{template_id} requires non-empty left_bars and right_bars")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
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
    reference_color = str(style_roles.get("reference_line") or "#6b7280").strip() or "#6b7280"
    comparator_fill = str(palette.get("secondary_soft") or "").strip() or comparator_color
    model_fill = str(palette.get("primary_soft") or "").strip() or model_color

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.2, 4.5), sharey=True)
    fig.patch.set_facecolor("white")
    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )
    wrapped_y_label, _ = _wrap_figure_title_to_width(
        str(display_payload.get("y_label") or "").strip(),
        max_width_pt=fig.get_figheight() * 72.0 * 0.72,
        font_size=axis_title_size,
    )

    max_risk_pct = max(
        max(float(item["risk"]) for item in left_bars),
        max(float(item["risk"]) for item in right_bars),
    ) * 100.0
    upper_margin = max(max_risk_pct * 0.18, 6.0)
    y_upper = max_risk_pct + upper_margin

    def _draw_panel(
        *,
        axes,
        bars_payload: list[dict[str, Any]],
        panel_title: str,
        x_label: str,
        fill_color: str,
        edge_color: str,
        panel_label: str,
    ) -> list[Any]:
        labels = [str(item["label"]) for item in bars_payload]
        risks = [float(item["risk"]) * 100.0 for item in bars_payload]
        bar_artists = axes.bar(
            labels,
            risks,
            width=0.64,
            color=matplotlib.colors.to_rgba(fill_color, alpha=0.88),
            edgecolor=edge_color,
            linewidth=1.2,
            zorder=3,
        )
        axes.set_ylim(0.0, y_upper)
        axes.set_xlabel(x_label, fontsize=axis_title_size, fontweight="bold", color="#13293d")
        if show_subplot_titles:
            axes.set_title(panel_title, fontsize=axis_title_size, fontweight="bold", color="#334155", pad=10)
        axes.tick_params(axis="x", labelsize=tick_size)
        axes.tick_params(axis="y", labelsize=tick_size)
        axes.axhline(0.0, color=reference_color, linewidth=0.8, zorder=1)
        _apply_publication_axes_style(axes)
        axes.grid(axis="y", color="#d8d1c7", linewidth=0.8, linestyle=":", zorder=0)
        axes.text(
            -0.09,
            1.04,
            panel_label,
            transform=axes.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#2F3437",
            va="bottom",
        )
        for index, (artist, bar_payload) in enumerate(zip(bar_artists, bars_payload, strict=True)):
            risk_pct = float(bar_payload["risk"]) * 100.0
            axes.text(
                float(artist.get_x()) + float(artist.get_width()) / 2.0,
                float(artist.get_height()) + upper_margin * 0.12,
                f"{risk_pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=max(tick_size - 1.0, 8.0),
                color=edge_color,
            )
        return list(bar_artists)

    left_bar_artists = _draw_panel(
        axes=left_axes,
        bars_payload=left_bars,
        panel_title=str(display_payload.get("left_panel_title") or "").strip(),
        x_label=str(display_payload.get("left_x_label") or "").strip(),
        fill_color=comparator_fill,
        edge_color=comparator_color,
        panel_label="A",
    )
    right_bar_artists = _draw_panel(
        axes=right_axes,
        bars_payload=right_bars,
        panel_title=str(display_payload.get("right_panel_title") or "").strip(),
        x_label=str(display_payload.get("right_x_label") or "").strip(),
        fill_color=model_fill,
        edge_color=model_color,
        panel_label="B",
    )
    left_axes.set_ylabel(
        wrapped_y_label,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )

    title_top = 0.83 - 0.08 * max(title_line_count - 1, 0)
    top_margin = max(0.68, title_top) if show_figure_title else 0.90
    if not show_subplot_titles:
        top_margin = min(0.94, top_margin + 0.02)
    fig.subplots_adjust(left=0.10, right=0.98, top=top_margin, bottom=0.20, wspace=0.18)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_x_axis_title",
            box_type="subplot_x_axis_title",
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
    for index, artist in enumerate(left_bar_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"left_risk_bar_{index}",
                box_type="risk_bar",
            )
        )
    for index, artist in enumerate(right_bar_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"right_risk_bar_{index}",
                box_type="risk_bar",
            )
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
            "guide_boxes": [],
            "metrics": {
                "left_bars": left_bars,
                "right_bars": right_bars,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_binary_calibration_decision_curve_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    calibration_series = list(display_payload.get("calibration_series") or [])
    decision_series = list(display_payload.get("decision_series") or [])
    decision_reference_lines = list(display_payload.get("decision_reference_lines") or [])
    decision_focus_window = dict(display_payload.get("decision_focus_window") or {})
    if not calibration_series or not decision_series or not decision_reference_lines:
        raise RuntimeError(
            f"{template_id} requires non-empty calibration_series, decision_series, and decision_reference_lines"
        )

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
    primary_linewidth = float(stroke.get("primary_linewidth") or 2.2)
    secondary_linewidth = float(stroke.get("secondary_linewidth") or 1.8)
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
    highlight_band_color = str(palette.get("light") or palette.get("secondary_soft") or "#E7E1D8").strip() or "#E7E1D8"
    fallback_palette = [
        str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F",
        str(palette.get("neutral") or "#7B8794").strip() or "#7B8794",
        str(palette.get("secondary") or "#B9AD9C").strip() or "#B9AD9C",
    ]

    def _series_color(index: int) -> str:
        if index == 0:
            return comparator_color
        if index == 1:
            return model_color
        return fallback_palette[(index - 2) % len(fallback_palette)]

    fig, (calibration_axes, decision_axes) = plt.subplots(1, 2, figsize=(10.8, 4.9))
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
            y=0.982,
        )

    calibration_title = None
    if show_subplot_titles:
        calibration_title = calibration_axes.set_title(
            "Calibration",
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10,
        )
    calibration_axes.text(
        -0.11,
        1.04,
        "A",
        transform=calibration_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color="#2F3437",
        va="bottom",
    )

    calibration_handles: list[Any] = []
    calibration_labels: list[str] = []
    for index, item in enumerate(calibration_series):
        (line_artist,) = calibration_axes.plot(
            item["x"],
            item["y"],
            linewidth=primary_linewidth if index == 1 else secondary_linewidth,
            marker="o",
            markersize=max(marker_size - 0.4, 3.6),
            color=_series_color(index),
            label=str(item["label"]),
            zorder=3,
        )
        calibration_handles.append(line_artist)
        calibration_labels.append(str(item["label"]))
    calibration_reference_line = display_payload.get("calibration_reference_line")
    if isinstance(calibration_reference_line, dict):
        (reference_artist,) = calibration_axes.plot(
            calibration_reference_line["x"],
            calibration_reference_line["y"],
            linewidth=1.1,
            linestyle="--",
            color=reference_color,
            label=str(calibration_reference_line.get("label") or ""),
            zorder=2,
        )
        calibration_handles.append(reference_artist)
        calibration_labels.append(str(calibration_reference_line.get("label") or ""))

    calibration_axis_window = display_payload.get("calibration_axis_window")
    if isinstance(calibration_axis_window, dict):
        calibration_x_lower = float(calibration_axis_window["xmin"])
        calibration_x_upper = float(calibration_axis_window["xmax"])
        calibration_y_lower = float(calibration_axis_window["ymin"])
        calibration_y_upper = float(calibration_axis_window["ymax"])
    else:
        calibration_x_values = [
            float(value) for item in calibration_series for value in item["x"]
        ] + [float(value) for value in (calibration_reference_line or {}).get("x", [])]
        calibration_y_values = [
            float(value) for item in calibration_series for value in item["y"]
        ] + [float(value) for value in (calibration_reference_line or {}).get("y", [])]
        calibration_x_lower = min(0.0, min(calibration_x_values, default=0.0))
        calibration_x_upper = max(1.0, max(calibration_x_values, default=1.0))
        calibration_y_lower = min(0.0, min(calibration_y_values, default=0.0))
        calibration_y_upper = max(1.0, max(calibration_y_values, default=1.0))
    calibration_axes.set_xlim(calibration_x_lower, calibration_x_upper)
    calibration_axes.set_ylim(calibration_y_lower, calibration_y_upper)
    calibration_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    calibration_axes.set_ylabel(
        str(display_payload.get("calibration_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    calibration_axes.tick_params(axis="both", labelsize=tick_size)
    _apply_publication_axes_style(calibration_axes)
    calibration_axes.grid(axis="both", color="#e6edf2", linewidth=0.45, linestyle=":")

    decision_title = None
    if show_subplot_titles:
        decision_title = decision_axes.set_title(
            "Decision curve",
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10,
        )
    decision_axes.text(
        -0.11,
        1.04,
        "B",
        transform=decision_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color="#2F3437",
        va="bottom",
    )

    focus_xmin = float(decision_focus_window["xmin"])
    focus_xmax = float(decision_focus_window["xmax"])
    decision_axes.axvspan(
        focus_xmin,
        focus_xmax,
        color=highlight_band_color,
        alpha=0.22,
        zorder=0,
    )

    decision_handles: list[Any] = []
    decision_labels: list[str] = []
    for reference_index, item in enumerate(decision_reference_lines):
        (line_artist,) = decision_axes.plot(
            item["x"],
            item["y"],
            linewidth=1.0,
            linestyle="--" if reference_index == 0 else "-.",
            color=reference_color,
            label=str(item["label"]),
            zorder=1,
        )
        decision_handles.append(line_artist)
        decision_labels.append(str(item["label"]))
    for index, item in enumerate(decision_series):
        (line_artist,) = decision_axes.plot(
            item["x"],
            item["y"],
            linewidth=primary_linewidth if index == 1 else secondary_linewidth,
            color=_series_color(index),
            label=str(item["label"]),
            zorder=3,
        )
        decision_handles.append(line_artist)
        decision_labels.append(str(item["label"]))

    decision_x_values = [float(value) for item in decision_series for value in item["x"]]
    decision_y_values = [float(value) for item in decision_series for value in item["y"]]
    decision_x_values.extend(float(value) for item in decision_reference_lines for value in item["x"])
    decision_y_values.extend(float(value) for item in decision_reference_lines for value in item["y"])
    decision_x_lower = min(focus_xmin, min(decision_x_values))
    decision_x_upper = max(focus_xmax, max(decision_x_values))
    decision_x_padding = max((decision_x_upper - decision_x_lower) * 0.03, 0.005)
    decision_y_lower = min(decision_y_values)
    decision_y_upper = max(decision_y_values)
    decision_y_padding = max((decision_y_upper - decision_y_lower) * 0.12, 0.01)
    decision_axes.set_xlim(decision_x_lower - decision_x_padding, decision_x_upper + decision_x_padding)
    decision_axes.set_ylim(decision_y_lower - decision_y_padding, decision_y_upper + decision_y_padding)
    decision_axes.set_xlabel(
        str(display_payload.get("decision_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    decision_axes.set_ylabel(
        str(display_payload.get("decision_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    decision_axes.tick_params(axis="both", labelsize=tick_size)
    _apply_publication_axes_style(decision_axes)
    decision_axes.grid(axis="both", color="#e6edf2", linewidth=0.45, linestyle=":")

    legend_handles: list[Any] = []
    legend_labels: list[str] = []
    for handle, label in [*zip(calibration_handles, calibration_labels, strict=True), *zip(decision_handles, decision_labels, strict=True)]:
        if label in legend_labels:
            continue
        legend_handles.append(handle)
        legend_labels.append(label)
    legend_columns = min(4, max(2, len(legend_labels)))
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=legend_columns,
        frameon=False,
        fontsize=max(tick_size - 0.5, 8.5),
        handlelength=2.4,
        columnspacing=1.3,
    )

    title_top = 0.84 - 0.06 * max(title_line_count - 1, 0)
    top_margin = max(0.70, title_top) if show_figure_title else 0.90
    if not show_subplot_titles:
        top_margin = min(0.94, top_margin + 0.02)
    fig.subplots_adjust(left=0.09, right=0.98, top=top_margin, bottom=0.23, wspace=0.22)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    resolved_calibration_xmin, resolved_calibration_xmax = (
        float(value) for value in calibration_axes.get_xlim()
    )
    resolved_calibration_ymin, resolved_calibration_ymax = (
        float(value) for value in calibration_axes.get_ylim()
    )

    decision_ymin, decision_ymax = decision_axes.get_ylim()
    focus_window_box = _data_box_to_layout_box(
        axes=decision_axes,
        figure=fig,
        x0=focus_xmin,
        y0=decision_ymin,
        x1=focus_xmax,
        y1=decision_ymax,
        box_id="decision_focus_window",
        box_type="focus_window",
    )
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=calibration_axes.xaxis.label.get_window_extent(renderer=renderer),
                    box_id="calibration_x_axis_title",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=calibration_axes.yaxis.label.get_window_extent(renderer=renderer),
                    box_id="calibration_y_axis_title",
                    box_type="subplot_y_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=decision_axes.xaxis.label.get_window_extent(renderer=renderer),
                    box_id="decision_x_axis_title",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=decision_axes.yaxis.label.get_window_extent(renderer=renderer),
                    box_id="decision_y_axis_title",
                    box_type="subplot_y_axis_title",
                ),
            ],
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=calibration_axes.get_window_extent(renderer=renderer),
                    box_id="calibration_panel",
                    box_type="calibration_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=decision_axes.get_window_extent(renderer=renderer),
                    box_id="decision_panel",
                    box_type="decision_panel",
                ),
            ],
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                ),
                focus_window_box,
            ],
            "metrics": {
                "calibration_axis_window": {
                    "xmin": resolved_calibration_xmin,
                    "xmax": resolved_calibration_xmax,
                    "ymin": resolved_calibration_ymin,
                    "ymax": resolved_calibration_ymax,
                },
                "calibration_series": calibration_series,
                "calibration_reference_line": _normalize_reference_line_to_device_space(
                    reference_line=calibration_reference_line,
                    axes=calibration_axes,
                    figure=fig,
                    clip_to_axes_window=True,
                ),
                "decision_series": decision_series,
                "decision_reference_lines": _normalize_reference_line_collection_to_device_space(
                    reference_lines=decision_reference_lines,
                    axes=decision_axes,
                    figure=fig,
                ),
                "decision_focus_window": {
                    "xmin": focus_xmin,
                    "xmax": focus_xmax,
                },
            },
        },
    )
    layout_boxes = load_json(layout_sidecar_path)["layout_boxes"]
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
    if calibration_title is not None:
        layout_boxes.insert(
            1 if title_artist is not None else 0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=calibration_title.get_window_extent(renderer=renderer),
                box_id="calibration_subplot_title",
                box_type="subplot_title",
            ),
        )
    if decision_title is not None:
        insert_index = 1 if title_artist is not None else 0
        if calibration_title is not None:
            insert_index += 1
        layout_boxes.insert(
            insert_index,
            _bbox_to_layout_box(
                figure=fig,
                bbox=decision_title.get_window_extent(renderer=renderer),
                box_id="decision_subplot_title",
                box_type="subplot_title",
            ),
        )
    sidecar_payload = load_json(layout_sidecar_path)
    sidecar_payload["layout_boxes"] = layout_boxes
    dump_json(layout_sidecar_path, sidecar_payload)
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

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

def _render_python_time_to_event_stratified_cumulative_incidence_panel(
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
        str(palette.get("neutral") or reference_color).strip() or reference_color,
    )

    panel_count = len(panels)
    figure_width = max(11.6, 3.85 * panel_count + 0.8)
    fig, axes = plt.subplots(1, panel_count, figsize=(figure_width, 4.9))
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
    panel_annotation_artists: list[Any | None] = []
    normalized_panels: list[dict[str, Any]] = []

    for axes_index, (axes, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        groups = list(panel.get("groups") or [])
        if not groups:
            raise RuntimeError(f"{template_id} panel {axes_index} requires non-empty groups")

        all_times = [float(value) for group in groups for value in group["times"]]
        all_values = [float(value) for group in groups for value in group["values"]]
        x_min = min(all_times)
        x_max = max(all_times)
        x_padding = max((x_max - x_min) * 0.06, 0.5 if x_max > x_min else 0.5)
        y_max = max(all_values)
        y_upper = min(1.0, max(0.12, y_max * 1.10 + 0.01))

        panel_groups: list[dict[str, Any]] = []
        for group_index, group in enumerate(groups):
            line_color = color_cycle[group_index % len(color_cycle)]
            times = [float(value) for value in group["times"]]
            values = [float(value) for value in group["values"]]
            axes.step(
                times,
                values,
                where="post",
                linewidth=2.0,
                color=line_color,
                label=str(group["label"]),
            )
            panel_groups.append(
                {
                    "label": str(group["label"]),
                    "times": times,
                    "values": values,
                }
            )

        axes.set_xlim(x_min, x_max + x_padding)
        axes.set_ylim(0.0, y_upper)
        axes.set_title(
            textwrap.fill(str(panel.get("title") or "").strip(), width=28),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10,
        )
        axes.tick_params(axis="both", labelsize=tick_size)
        axes.grid(axis="y", color="#e6edf2", linewidth=0.5, linestyle=":")
        axes.grid(axis="x", visible=False)
        _apply_publication_axes_style(axes)

        legend_columns = min(3, max(1, len(panel_groups)))
        axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.19),
            ncol=legend_columns,
            frameon=False,
            fontsize=max(tick_size - 1.2, 8.0),
            handlelength=2.2,
            columnspacing=1.3,
        )

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
        annotation_artist = None
        annotation = str(panel.get("annotation") or "").strip()
        if annotation:
            annotation_artist = axes.text(
                0.03,
                0.05,
                annotation,
                transform=axes.transAxes,
                fontsize=max(tick_size - 0.4, 8.2),
                color=reference_color,
                ha="left",
                va="bottom",
            )
        panel_annotation_artists.append(annotation_artist)
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_label,
                "title": str(panel["title"]),
                "annotation": annotation,
                "groups": panel_groups,
            }
        )

    top_margin = 0.80 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.07, right=0.99, top=top_margin, bottom=0.26, wspace=0.26)
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
        if annotation_artist_item is not None:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=annotation_artist_item.get_window_extent(renderer=renderer),
                    box_id=f"annotation_{panel_label_token}",
                    box_type="annotation_text",
                )
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
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_time_to_event_threshold_governance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    threshold_summaries = list(display_payload.get("threshold_summaries") or [])
    risk_group_summaries = list(display_payload.get("risk_group_summaries") or [])
    if not threshold_summaries or not risk_group_summaries:
        raise RuntimeError(f"{template_id} requires non-empty threshold_summaries and risk_group_summaries")

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

    observed_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    predicted_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    primary_color = str(palette.get("primary") or observed_color).strip() or observed_color
    threshold_fill = str(palette.get("primary_soft") or "#EAF2F5").strip() or "#EAF2F5"
    threshold_fill_alt = str(palette.get("secondary_soft") or "#F4EEE5").strip() or "#F4EEE5"
    grid_color = str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = max(float(stroke.get("marker_size") or 4.2), 3.8)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    figure_height = max(4.4, 3.2 + 0.34 * len(threshold_summaries))
    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(11.2, figure_height))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    left_axes.set_axis_off()
    left_axes.set_xlim(0.0, 1.0)
    left_axes.set_ylim(0.0, 1.0)
    left_axes.set_title(
        str(display_payload.get("threshold_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=12.0,
    )
    left_panel_label = left_axes.text(
        0.02,
        0.98,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    card_top = 0.82
    card_bottom = 0.10
    card_gap = 0.05
    card_x0 = 0.10
    card_x1 = 0.92
    available_height = card_top - card_bottom - card_gap * max(len(threshold_summaries) - 1, 0)
    card_height = available_height / max(len(threshold_summaries), 1)
    threshold_card_patches: list[tuple[str, Any]] = []
    for index, item in enumerate(threshold_summaries, start=1):
        y1 = card_top - (index - 1) * (card_height + card_gap)
        y0 = y1 - card_height
        fill_color = threshold_fill if index % 2 == 1 else threshold_fill_alt
        card_patch = matplotlib.patches.FancyBboxPatch(
            (card_x0, y0),
            card_x1 - card_x0,
            card_height,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            transform=left_axes.transAxes,
            linewidth=1.2,
            facecolor=fill_color,
            edgecolor=neutral_color,
        )
        left_axes.add_patch(card_patch)
        accent_patch = matplotlib.patches.Rectangle(
            (card_x0, y0),
            0.022,
            card_height,
            transform=left_axes.transAxes,
            linewidth=0,
            facecolor=primary_color if index % 2 == 1 else predicted_color,
        )
        left_axes.add_patch(accent_patch)
        left_axes.text(
            card_x0 + 0.05,
            y1 - card_height * 0.26,
            str(item["threshold_label"]),
            transform=left_axes.transAxes,
            fontsize=tick_size + 0.2,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x0 + 0.05,
            y1 - card_height * 0.49,
            f"Threshold {float(item['threshold']):.0%}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.1,
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x0 + 0.05,
            y0 + card_height * 0.26,
            f"Sens {float(item['sensitivity']):.0%} · Spec {float(item['specificity']):.0%}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.4,
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x1 - 0.04,
            y0 + card_height * 0.26,
            f"NB {float(item['net_benefit']):.3f}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.2,
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        threshold_card_patches.append((f"threshold_card_{index}", card_patch))

    right_axes.set_title(
        str(display_payload.get("calibration_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=12.0,
    )
    right_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    group_labels = [str(item["group_label"]) for item in risk_group_summaries]
    y_positions = [float(index) for index in range(1, len(risk_group_summaries) + 1)]
    predicted_risks = [float(item["predicted_risk"]) for item in risk_group_summaries]
    observed_risks = [float(item["observed_risk"]) for item in risk_group_summaries]
    x_upper = max(max(predicted_risks), max(observed_risks))
    x_upper = min(1.0, max(0.18, x_upper * 1.22 + 0.02))
    right_axes.set_xlim(0.0, x_upper)
    right_axes.set_ylim(0.5, len(risk_group_summaries) + 0.5)
    right_axes.set_yticks(y_positions)
    right_axes.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
    right_axes.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
    right_axes.tick_params(axis="x", labelsize=tick_size)
    right_axes.tick_params(axis="y", length=0, pad=7)
    right_axes.grid(axis="x", color=grid_color, linewidth=0.8, linestyle=":")
    right_axes.grid(axis="y", visible=False)
    _apply_publication_axes_style(right_axes)
    right_panel_label = right_axes.text(
        0.02,
        0.98,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    normalized_risk_group_summaries: list[dict[str, Any]] = []
    for index, (item, y_value, predicted_risk, observed_risk) in enumerate(
        zip(risk_group_summaries, y_positions, predicted_risks, observed_risks, strict=True),
        start=1,
    ):
        right_axes.hlines(
            y=y_value,
            xmin=min(predicted_risk, observed_risk),
            xmax=max(predicted_risk, observed_risk),
            color=neutral_color,
            linewidth=1.7,
            zorder=1,
        )
        right_axes.scatter(
            [predicted_risk],
            [y_value],
            s=marker_size * 18.0,
            color=predicted_color,
            label="Predicted" if index == 1 else None,
            zorder=3,
        )
        right_axes.scatter(
            [observed_risk],
            [y_value],
            s=marker_size * 18.0,
            color=observed_color,
            label="Observed" if index == 1 else None,
            zorder=4,
        )
        predicted_x, point_y = _data_point_to_figure_xy(
            axes=right_axes,
            figure=fig,
            x=predicted_risk,
            y=y_value,
        )
        observed_x, _ = _data_point_to_figure_xy(
            axes=right_axes,
            figure=fig,
            x=observed_risk,
            y=y_value,
        )
        normalized_risk_group_summaries.append(
            {
                "group_label": str(item["group_label"]),
                "group_order": int(item["group_order"]),
                "n": int(item["n"]),
                "events": int(item["events"]),
                "predicted_risk": predicted_risk,
                "observed_risk": observed_risk,
                "predicted_x": predicted_x,
                "observed_x": observed_x,
                "y": point_y,
            }
        )

    legend_handles, legend_labels = right_axes.get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.72, 0.03),
        ncol=min(2, max(1, len(legend_labels))),
        frameon=False,
        fontsize=tick_size - 0.2,
    )

    fig.subplots_adjust(
        left=0.07,
        right=0.98,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.18,
        wspace=0.20,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_title_A",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_title_B",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title_B",
            box_type="subplot_x_axis_title",
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
    normalized_threshold_summaries: list[dict[str, Any]] = []
    for index, (card_box_id, card_patch) in enumerate(threshold_card_patches):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=card_patch.get_window_extent(renderer=renderer),
                box_id=card_box_id,
                box_type="threshold_card",
            )
        )
        threshold_item = threshold_summaries[index]
        normalized_threshold_summaries.append(
            {
                "threshold_label": str(threshold_item["threshold_label"]),
                "threshold": float(threshold_item["threshold"]),
                "sensitivity": float(threshold_item["sensitivity"]),
                "specificity": float(threshold_item["specificity"]),
                "net_benefit": float(threshold_item["net_benefit"]),
                "card_box_id": card_box_id,
            }
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
                    box_id="threshold_panel",
                    box_type="threshold_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_axes.get_window_extent(renderer=renderer),
                    box_id="calibration_panel",
                    box_type="calibration_panel",
                ),
            ],
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "threshold_summaries": normalized_threshold_summaries,
                "risk_group_summaries": normalized_risk_group_summaries,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_time_to_event_multihorizon_calibration_panel(
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
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    observed_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    predicted_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    grid_color = str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = max(float(stroke.get("marker_size") or 4.2), 3.8)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    panel_count = len(panels)
    figure_width = max(9.8, 4.1 * panel_count + 0.8)
    fig, axes = plt.subplots(1, panel_count, figsize=(figure_width, 4.7))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )
    x_axis_artist = fig.text(
        0.5,
        0.06,
        str(display_payload.get("x_label") or "").strip(),
        ha="center",
        va="center",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    fig.subplots_adjust(
        left=0.08,
        right=0.99,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.20,
        wspace=0.28,
    )

    panel_label_artists: list[Any] = []
    panel_title_artists: list[Any] = []
    normalized_panels: list[dict[str, Any]] = []
    for axes_index, (axes_item, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        calibration_summary = list(panel.get("calibration_summary") or [])
        if not calibration_summary:
            raise RuntimeError(f"{template_id} panel {axes_index} requires non-empty calibration_summary")
        group_labels = [str(item["group_label"]) for item in calibration_summary]
        y_positions = [float(index) for index in range(1, len(calibration_summary) + 1)]
        predicted_risks = [float(item["predicted_risk"]) for item in calibration_summary]
        observed_risks = [float(item["observed_risk"]) for item in calibration_summary]
        x_upper = min(1.0, max(0.18, max(max(predicted_risks), max(observed_risks)) * 1.22 + 0.02))

        axes_item.set_xlim(0.0, x_upper)
        axes_item.set_ylim(0.5, len(calibration_summary) + 0.5)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
        axes_item.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
        axes_item.tick_params(axis="x", labelsize=tick_size)
        axes_item.tick_params(axis="y", length=0, pad=6)
        axes_item.grid(axis="x", color=grid_color, linewidth=0.8, linestyle=":")
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)
        axes_item.set_title(
            str(panel.get("title") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=12.0,
        )
        panel_label_artists.append(
            axes_item.text(
                0.02,
                0.98,
                str(panel.get("panel_label") or "").strip(),
                transform=axes_item.transAxes,
                fontsize=panel_label_size,
                fontweight="bold",
                color=neutral_color,
                ha="left",
                va="top",
            )
        )
        panel_title_artists.append(axes_item.title)

        normalized_summary: list[dict[str, Any]] = []
        for group_index, (item, y_value, predicted_risk, observed_risk) in enumerate(
            zip(calibration_summary, y_positions, predicted_risks, observed_risks, strict=True),
            start=1,
        ):
            axes_item.hlines(
                y=y_value,
                xmin=min(predicted_risk, observed_risk),
                xmax=max(predicted_risk, observed_risk),
                color=neutral_color,
                linewidth=1.7,
                zorder=1,
            )
            axes_item.scatter(
                [predicted_risk],
                [y_value],
                s=marker_size * 18.0,
                color=predicted_color,
                label="Predicted" if axes_index == 1 and group_index == 1 else None,
                zorder=3,
            )
            axes_item.scatter(
                [observed_risk],
                [y_value],
                s=marker_size * 18.0,
                color=observed_color,
                label="Observed" if axes_index == 1 and group_index == 1 else None,
                zorder=4,
            )
            predicted_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=predicted_risk,
                y=y_value,
            )
            observed_x, _ = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=observed_risk,
                y=y_value,
            )
            normalized_summary.append(
                {
                    "group_label": str(item["group_label"]),
                    "group_order": int(item["group_order"]),
                    "n": int(item["n"]),
                    "events": int(item["events"]),
                    "predicted_risk": predicted_risk,
                    "observed_risk": observed_risk,
                    "predicted_x": predicted_x,
                    "observed_x": observed_x,
                    "y": point_y,
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "time_horizon_months": int(panel["time_horizon_months"]),
                "calibration_summary": normalized_summary,
            }
        )

    legend_handles, legend_labels = axes_list[0].get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=min(2, max(1, len(legend_labels))),
        frameon=False,
        fontsize=tick_size - 0.2,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=x_axis_artist.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="subplot_x_axis_title",
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
    for axes_item, panel, title_artist_item, label_artist_item in zip(
        axes_list,
        normalized_panels,
        panel_title_artists,
        panel_label_artists,
        strict=True,
    ):
        panel_label_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_label_token}",
                box_type="calibration_panel",
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

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_time_to_event_risk_group_summary(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    risk_group_summaries = list(display_payload.get("risk_group_summaries") or [])
    if not risk_group_summaries:
        raise RuntimeError(f"{template_id} requires non-empty risk_group_summaries")

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
    observed_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    predicted_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    group_colors = (
        str(palette.get("light") or palette.get("secondary_soft") or predicted_color).strip() or predicted_color,
        str(palette.get("secondary") or predicted_color).strip() or predicted_color,
        str(palette.get("primary") or observed_color).strip() or observed_color,
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_legend = _read_bool_override(layout_override, "show_legend", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )
    x_positions = list(range(len(risk_group_summaries)))
    group_labels = [str(item["label"]) for item in risk_group_summaries]
    predicted_risk = [float(item["mean_predicted_risk_5y"]) * 100.0 for item in risk_group_summaries]
    observed_risk = [float(item["observed_km_risk_5y"]) * 100.0 for item in risk_group_summaries]
    event_counts = [int(item["events_5y"]) for item in risk_group_summaries]
    bar_width = 0.34

    left_axes.bar(
        [position - bar_width / 2.0 for position in x_positions],
        predicted_risk,
        width=bar_width,
        color=predicted_color,
        label="Predicted",
    )
    left_axes.bar(
        [position + bar_width / 2.0 for position in x_positions],
        observed_risk,
        width=bar_width,
        color=observed_color,
        label="Observed",
    )
    left_axes.set_xticks(x_positions)
    left_axes.set_xticklabels(group_labels)
    left_axes.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_title(
        str(display_payload.get("panel_a_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.grid(axis="y", color=str(palette.get("light") or "#E7E1D8"), linewidth=0.8, linestyle=":")
    left_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(left_axes)
    legend = None
    if show_legend:
        legend = fig.legend(
            *left_axes.get_legend_handles_labels(),
            loc="lower center",
            bbox_to_anchor=(0.28, 0.02),
            ncol=2,
            frameon=False,
        )
    left_panel_label = left_axes.text(
        0.02,
        0.98,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    right_axes.bar(
        x_positions,
        event_counts,
        width=0.58,
        color=[group_colors[index % len(group_colors)] for index in x_positions],
    )
    upper_margin = max(max(event_counts) * 0.08, 1.2)
    for index, value in enumerate(event_counts):
        right_axes.text(
            index,
            float(value) + upper_margin * 0.35,
            str(value),
            ha="center",
            va="bottom",
            fontsize=tick_size - 1.0,
            color=neutral_color,
        )
    right_axes.set_xticks(x_positions)
    right_axes.set_xticklabels(group_labels)
    right_axes.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("event_count_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_title(
        str(display_payload.get("panel_b_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylim(0.0, max(event_counts) + upper_margin)
    right_axes.grid(axis="y", color=str(palette.get("light") or "#E7E1D8"), linewidth=0.8, linestyle=":")
    right_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(right_axes)
    right_panel_label = right_axes.text(
        0.02,
        0.98,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.21 if show_legend else 0.12,
        wspace=0.26,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
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
                "risk_group_summaries": risk_group_summaries,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

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

def _render_python_time_to_event_discrimination_calibration_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    discrimination_points = list(display_payload.get("discrimination_points") or [])
    calibration_summary = list(display_payload.get("calibration_summary") or [])
    if not discrimination_points or not calibration_summary:
        raise RuntimeError(f"{template_id} requires non-empty discrimination_points and calibration_summary")

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
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    highlight_color = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    marker_size = max(float(stroke.get("marker_size") or 4.5), 3.8)
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.8, 4.3))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    c_index_values = [float(item["c_index"]) for item in discrimination_points]
    x_range = max(max(c_index_values) - min(c_index_values), 0.01)
    x_floor = max(0.0, min(c_index_values) - max(0.012, x_range * 0.8))
    x_ceiling = min(1.0, max(c_index_values) + max(0.012, x_range * 1.2))
    y_positions = list(range(len(discrimination_points)))[::-1]
    left_axes.set_xlim(x_floor, x_ceiling)
    left_axes.set_ylim(-0.5, len(discrimination_points) - 0.5)
    left_axes.set_yticks(y_positions)
    left_axes.set_yticklabels(
        [str(item["label"]) for item in discrimination_points],
        fontsize=tick_size,
        color=neutral_color,
    )
    discrimination_marker_boxes: list[dict[str, Any]] = []
    for y_position, item in zip(y_positions, discrimination_points, strict=True):
        label = str(item["label"])
        c_index = float(item["c_index"])
        point_color = comparator_color if "lasso" in label.casefold() else model_color
        left_axes.hlines(
            y=y_position,
            xmin=x_floor,
            xmax=c_index,
            linewidth=2.1,
            color=point_color,
            zorder=2,
        )
        left_axes.scatter([c_index], [y_position], s=(marker_size * 11.0), color=point_color, zorder=3)
        annotation_text = str(item.get("annotation") or f"{c_index:.3f}").strip()
        x_offset = max(x_range * 0.07, 0.0025)
        text_x = c_index + x_offset
        text_ha = "left"
        if text_x > x_ceiling - x_offset * 0.35:
            text_x = c_index - x_offset
            text_ha = "right"
        left_axes.text(
            text_x,
            y_position + 0.02,
            annotation_text,
            fontsize=tick_size - 0.2,
            color=neutral_color,
            va="center",
            ha=text_ha,
        )
        discrimination_marker_boxes.append(
            {
                "label": label,
                "c_index": c_index,
                "y": float(y_position),
            }
        )
    left_axes.set_xlabel(
        str(display_payload.get("discrimination_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        "Model",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_title(
        str(display_payload.get("panel_a_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.tick_params(axis="x", labelsize=tick_size)
    left_axes.tick_params(axis="y", length=0, pad=6)
    left_axes.grid(axis="y", visible=False)
    left_axes.grid(axis="x", color=highlight_color, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(left_axes)
    left_axes.text(
        -0.10,
        1.04,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
    )

    risk_deciles = [int(item["group_order"]) for item in calibration_summary]
    predicted_risk = [float(item["predicted_risk_5y"]) * 100.0 for item in calibration_summary]
    observed_risk = [float(item["observed_risk_5y"]) * 100.0 for item in calibration_summary]
    calibration_marker_boxes: list[dict[str, Any]] = []
    right_axes.plot(
        risk_deciles,
        predicted_risk,
        linewidth=2.2,
        marker="o",
        markersize=marker_size,
        color=comparator_color,
        label="Predicted",
        zorder=2,
    )
    right_axes.plot(
        risk_deciles,
        observed_risk,
        linewidth=2.2,
        marker="o",
        markersize=marker_size,
        color=model_color,
        label="Observed",
        zorder=3,
    )
    y_top = max(max(predicted_risk), max(observed_risk))
    right_axes.set_xlim(0.7, max(risk_deciles) + 0.3)
    right_axes.set_ylim(0.0, max(4.0, y_top * 1.18))
    right_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("calibration_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_title(
        str(display_payload.get("panel_b_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_xticks(risk_deciles)
    right_axes.set_xticklabels([str(item) for item in risk_deciles], fontsize=tick_size, color=neutral_color)
    right_axes.tick_params(axis="y", labelsize=tick_size)
    right_axes.grid(axis="y", color=highlight_color, linewidth=0.8, linestyle=":")
    right_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(right_axes)
    right_axes.text(
        -0.10,
        1.04,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
    )
    legend_handles, legend_labels = right_axes.get_legend_handles_labels()
    for group_order, predicted_value, observed_value in zip(risk_deciles, predicted_risk, observed_risk, strict=True):
        calibration_marker_boxes.append(
            {
                "group_order": group_order,
                "predicted_risk_pct": predicted_value,
                "observed_risk_pct": observed_value,
            }
        )

    calibration_callout = display_payload.get("calibration_callout")
    callout_artist = None
    if isinstance(calibration_callout, dict):
        callout_group_label = str(calibration_callout.get("group_label") or "").strip()
        callout_predicted = float(calibration_callout["predicted_risk_5y"]) * 100.0
        callout_observed = float(calibration_callout["observed_risk_5y"]) * 100.0
        callout_events = int(calibration_callout.get("events_5y") or 0)
        callout_n = int(calibration_callout.get("n") or 0)
        callout_lines = _wrap_flow_text_to_width(
            (
                f"{callout_group_label}: {callout_predicted:.2f}% predicted, "
                f"{callout_observed:.2f}% observed, {callout_events}/{callout_n} events"
            ),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.19,
            font_size=max(tick_size - 0.6, 8.6),
            font_weight="normal",
        )
        callout_artist = right_axes.text(
            0.03,
            0.88,
            "\n".join(callout_lines),
            transform=right_axes.transAxes,
            fontsize=max(tick_size - 0.6, 8.6),
            color=neutral_color,
            ha="left",
            va="top",
            bbox={
                "boxstyle": "round,pad=0.26,rounding_size=0.18",
                "facecolor": matplotlib.colors.to_rgba(highlight_color, alpha=0.94),
                "edgecolor": neutral_color,
                "linewidth": 0.9,
            },
        )

    fig.subplots_adjust(
        left=0.10,
        right=0.96,
        top=0.72 if show_figure_title else 0.78,
        bottom=0.24,
        wspace=0.28,
    )
    legend = fig.legend(
        legend_handles,
        legend_labels,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.50, 0.035),
        ncol=min(2, max(1, len(legend_labels))),
    )
    fig.canvas.draw()
    if callout_artist is not None:
        renderer = fig.canvas.get_renderer()
        right_panel_bbox = right_axes.get_window_extent(renderer=renderer)
        right_title_bbox = right_axes.title.get_window_extent(renderer=renderer)
        callout_bbox = callout_artist.get_window_extent(renderer=renderer)
        horizontal_padding_px = max(right_panel_bbox.width * 0.03, 10.0)
        vertical_padding_px = max(right_panel_bbox.height * 0.08, 12.0)
        target_x0_px = right_panel_bbox.x0 + horizontal_padding_px
        target_y1_px = min(right_panel_bbox.y1 - vertical_padding_px, right_title_bbox.y0 - vertical_padding_px)
        minimum_y1_px = right_panel_bbox.y0 + vertical_padding_px + callout_bbox.height
        target_y1_px = max(target_y1_px, minimum_y1_px)
        target_axes_x, target_axes_y = right_axes.transAxes.inverted().transform((target_x0_px, target_y1_px))
        callout_artist.set_position((float(target_axes_x), float(target_axes_y)))
        fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_y_axis_title",
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
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="calibration_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="calibration_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_right_title",
            box_type="panel_title",
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
    for index, marker in enumerate(discrimination_marker_boxes, start=1):
        marker_width = max((x_ceiling - x_floor) * 0.015, 0.002)
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=left_axes,
                figure=fig,
                x0=float(marker["c_index"]) - marker_width,
                y0=float(marker["y"]) - 0.14,
                x1=float(marker["c_index"]) + marker_width,
                y1=float(marker["y"]) + 0.14,
                box_id=f"discrimination_marker_{index}",
                box_type="metric_marker",
            )
        )
    for index, marker in enumerate(calibration_marker_boxes, start=1):
        marker_half_width = 0.14
        marker_half_height = max(y_top * 0.03, 0.18)
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=right_axes,
                figure=fig,
                x0=float(marker["group_order"]) - marker_half_width,
                y0=float(marker["predicted_risk_pct"]) - marker_half_height,
                x1=float(marker["group_order"]) + marker_half_width,
                y1=float(marker["predicted_risk_pct"]) + marker_half_height,
                box_id=f"predicted_marker_{index}",
                box_type="metric_marker",
            )
        )
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=right_axes,
                figure=fig,
                x0=float(marker["group_order"]) - marker_half_width,
                y0=float(marker["observed_risk_pct"]) - marker_half_height,
                x1=float(marker["group_order"]) + marker_half_width,
                y1=float(marker["observed_risk_pct"]) + marker_half_height,
                box_id=f"observed_marker_{index}",
                box_type="metric_marker",
            )
        )
    if callout_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=callout_artist.get_window_extent(renderer=renderer),
                box_id="annotation_callout",
                box_type="annotation_block",
            )
        )
    panel_boxes = [
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
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend",
            box_type="legend",
        )
    ]
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "discrimination_points": discrimination_points,
                "calibration_summary": calibration_summary,
                "calibration_callout": calibration_callout,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
