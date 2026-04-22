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

