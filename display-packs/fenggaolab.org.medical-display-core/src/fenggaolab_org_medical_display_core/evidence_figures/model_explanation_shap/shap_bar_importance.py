from __future__ import annotations

from pathlib import Path
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
    dump_json,
)

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

