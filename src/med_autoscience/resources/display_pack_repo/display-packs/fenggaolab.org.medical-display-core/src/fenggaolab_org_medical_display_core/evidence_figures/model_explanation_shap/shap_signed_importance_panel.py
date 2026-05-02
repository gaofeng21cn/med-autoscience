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
    dump_json,
)

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

