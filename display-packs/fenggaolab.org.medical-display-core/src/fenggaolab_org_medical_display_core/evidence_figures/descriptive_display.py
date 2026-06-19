from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ..shared_parts.common import dump_json
from ..shared_parts.geometry import _bbox_to_layout_box
from ..shared_parts.rendering import (
    _apply_publication_axes_style,
    _prepare_python_render_output_paths,
)


def _style_tokens(display_payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    render_context = dict(display_payload.get("render_context") or {})
    return (
        dict(render_context.get("palette") or {}),
        dict(render_context.get("style_roles") or {}),
        dict(render_context.get("typography") or {}),
        dict(render_context.get("stroke") or {}),
    )


def _role_color(
    *,
    palette: dict[str, Any],
    style_roles: dict[str, Any],
    role: str,
    palette_key: str,
    fallback: str,
) -> str:
    value = str(style_roles.get(role) or "").strip()
    if value.startswith("#"):
        return value
    if value:
        palette_value = str(palette.get(value) or "").strip()
        if palette_value:
            return palette_value
    return str(palette.get(palette_key) or fallback).strip() or fallback


def _normalize_descriptive_panels(template_id: str, display_payload: dict[str, Any]) -> list[dict[str, Any]]:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")
    normalized: list[dict[str, Any]] = []
    for panel_index, panel in enumerate(panels):
        if not isinstance(panel, dict):
            raise RuntimeError(f"{template_id} panels[{panel_index}] must be an object")
        marks = list(panel.get("marks") or [])
        if not marks:
            raise RuntimeError(f"{template_id} panels[{panel_index}].marks must be non-empty")
        normalized_marks: list[dict[str, Any]] = []
        for mark_index, mark in enumerate(marks):
            if not isinstance(mark, dict):
                raise RuntimeError(f"{template_id} panels[{panel_index}].marks[{mark_index}] must be an object")
            value = mark.get("value")
            comparison_value = mark.get("comparison_value")
            normalized_marks.append(
                {
                    "label": str(mark.get("label") or "").strip(),
                    "group": str(mark.get("group") or "").strip(),
                    "value": None if value is None else float(value),
                    "comparison_value": None if comparison_value is None else float(comparison_value),
                    "annotation": str(mark.get("annotation") or "").strip(),
                    "color": str(mark.get("color") or "").strip(),
                }
            )
        normalized.append(
            {
                "panel_id": str(panel.get("panel_id") or f"panel_{panel_index + 1}").strip(),
                "title": str(panel.get("title") or "").strip(),
                "x_label": str(panel.get("x_label") or display_payload.get("x_label") or "").strip(),
                "y_label": str(panel.get("y_label") or display_payload.get("y_label") or "").strip(),
                "annotation": str(panel.get("annotation") or "").strip(),
                "marks": normalized_marks,
            }
        )
    return normalized


def _render_python_descriptive_display_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
    output_svg_path: Path | None = None,
) -> None:
    normalized_panels = _normalize_descriptive_panels(template_id, display_payload)
    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
    if output_svg_path is not None:
        output_svg_path.parent.mkdir(parents=True, exist_ok=True)

    palette, style_roles, typography, stroke = _style_tokens(display_payload)
    primary_color = _role_color(
        palette=palette,
        style_roles=style_roles,
        role="model_curve",
        palette_key="primary",
        fallback="#0F4D92",
    )
    comparator_color = _role_color(
        palette=palette,
        style_roles=style_roles,
        role="comparator_curve",
        palette_key="secondary",
        fallback="#33B5A5",
    )
    reference_color = _role_color(
        palette=palette,
        style_roles=style_roles,
        role="reference_line",
        palette_key="neutral_mid",
        fallback="#767676",
    )
    text_color = str(palette.get("text") or "#272727").strip() or "#272727"

    title_size = float(typography.get("title_size") or 10.0)
    axis_title_size = float(typography.get("axis_title_size") or 9.0)
    tick_size = float(typography.get("tick_size") or 8.0)
    panel_label_size = float(typography.get("panel_label_size") or 9.2)
    marker_size = float(stroke.get("marker_size") or 3.4)

    panel_count = len(normalized_panels)
    ncols = 1 if panel_count == 1 else min(2, panel_count)
    nrows = (panel_count + ncols - 1) // ncols
    fig_width = max(5.8, 3.4 * ncols)
    fig_height = max(4.8, 3.0 * nrows + 0.8)
    fig, axes_raw = plt.subplots(nrows, ncols, figsize=(fig_width, fig_height), squeeze=False)
    axes = [axes_raw[row][col] for row in range(nrows) for col in range(ncols)]
    fig.patch.set_facecolor("white")

    title_artist = None
    title = str(display_payload.get("title") or "").strip()
    if title:
        title_artist = fig.suptitle(title, fontsize=title_size, fontweight="bold", color=text_color, y=0.985)

    panel_boxes: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    metrics_panels: list[dict[str, Any]] = []
    for panel_index, panel in enumerate(normalized_panels):
        axes_item = axes[panel_index]
        labels = [item["label"] or f"Item {index + 1}" for index, item in enumerate(panel["marks"])]
        values = [item["value"] for item in panel["marks"]]
        comparison_values = [item["comparison_value"] for item in panel["marks"]]
        has_comparator = any(value is not None for value in comparison_values)
        y_positions = list(range(len(labels)))
        primary_values = [0.0 if value is None else float(value) for value in values]
        bar_height = 0.34 if has_comparator else 0.58
        primary_y = [value - (bar_height / 2.0 if has_comparator else 0.0) for value in y_positions]
        primary_bars = axes_item.barh(
            primary_y,
            primary_values,
            height=bar_height,
            color=primary_color,
            edgecolor="white",
            linewidth=0.6,
            label="Current" if has_comparator else None,
            zorder=3,
        )
        comparator_bars = []
        if has_comparator:
            comparator_y = [value + bar_height / 2.0 for value in y_positions]
            comparator_values = [0.0 if value is None else float(value) for value in comparison_values]
            comparator_bars = axes_item.barh(
                comparator_y,
                comparator_values,
                height=bar_height,
                color=comparator_color,
                edgecolor="white",
                linewidth=0.6,
                label="Comparator",
                zorder=2,
            )
        axes_item.axvline(0.0, color=reference_color, linewidth=0.8, linestyle="--", zorder=1)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(labels, fontsize=tick_size)
        axes_item.invert_yaxis()
        axes_item.set_xlabel(panel["x_label"], fontsize=axis_title_size, color=text_color)
        axes_item.set_ylabel(panel["y_label"], fontsize=axis_title_size, color=text_color)
        axes_item.set_title(panel["title"], loc="left", fontsize=axis_title_size, fontweight="bold", color=text_color)
        axes_item.tick_params(axis="both", labelsize=tick_size, colors=text_color)
        axes_item.scatter(primary_values, primary_y, s=max(marker_size * 8.0, 16.0), color=primary_color, zorder=4)
        if has_comparator:
            axes_item.scatter(
                [0.0 if value is None else float(value) for value in comparison_values],
                [value + bar_height / 2.0 for value in y_positions],
                s=max(marker_size * 8.0, 16.0),
                color=comparator_color,
                zorder=4,
            )
            axes_item.legend(frameon=False, fontsize=max(tick_size - 0.5, 7.0), loc="lower right")
        for row_index, mark in enumerate(panel["marks"]):
            if mark["annotation"]:
                axes_item.text(
                    primary_values[row_index],
                    primary_y[row_index],
                    f"  {mark['annotation']}",
                    va="center",
                    ha="left",
                    fontsize=max(tick_size - 0.8, 7.0),
                    color=text_color,
                )
        axes_item.text(
            -0.12,
            1.05,
            chr(ord("A") + panel_index),
            transform=axes_item.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color=text_color,
            va="bottom",
        )
        _apply_publication_axes_style(axes_item)
        metrics_panels.append(
            {
                "panel_id": panel["panel_id"],
                "title": panel["title"],
                "mark_count": len(panel["marks"]),
                "has_comparison_values": has_comparator,
            }
        )

    for unused_axes in axes[panel_count:]:
        unused_axes.set_axis_off()

    fig.subplots_adjust(top=0.88 if title_artist is not None else 0.94, bottom=0.12, left=0.22, right=0.96, hspace=0.42, wspace=0.30)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    for panel_index, axes_item in enumerate(axes[:panel_count]):
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_index + 1}",
                box_type="panel",
            )
        )
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
                    box_id=f"panel_{panel_index + 1}_title",
                    box_type="subtitle",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"panel_{panel_index + 1}_x_axis_title",
                    box_type="x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.yaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"panel_{panel_index + 1}_y_axis_title",
                    box_type="y_axis_title",
                ),
            ]
        )

    fig.savefig(output_png_path, dpi=220)
    fig.savefig(output_pdf_path)
    if output_svg_path is not None:
        fig.savefig(output_svg_path)
    plt.close(fig)

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [],
            "metrics": {
                "display_id": str(display_payload.get("display_id") or "").strip(),
                "panel_count": panel_count,
                "panels": metrics_panels,
            },
        },
    )
