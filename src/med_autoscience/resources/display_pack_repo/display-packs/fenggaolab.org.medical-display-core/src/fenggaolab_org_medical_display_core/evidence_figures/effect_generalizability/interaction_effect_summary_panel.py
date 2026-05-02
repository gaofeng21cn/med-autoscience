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
    _wrap_flow_text_to_width,
    dump_json,
)

def _render_python_interaction_effect_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    modifiers = list(display_payload.get("modifiers") or [])
    if not modifiers:
        raise RuntimeError(f"{template_id} requires non-empty modifiers")

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
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.8))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

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
    light_fill = str(palette.get("light") or "#f8fafc").strip() or "#f8fafc"
    summary_fill = str(palette.get("secondary_soft") or "#e2e8f0").strip() or "#e2e8f0"

    reference_value = float(display_payload["reference_value"])
    all_x_values = [reference_value]
    for modifier in modifiers:
        all_x_values.extend(
            (
                float(modifier["lower"]),
                float(modifier["interaction_estimate"]),
                float(modifier["upper"]),
            )
        )
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.06)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    interval_half_height = 0.030
    marker_half_height = 0.095
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)

    row_count = len(modifiers)
    figure_height = max(4.9, 0.82 * row_count + 2.0)
    fig, (estimate_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(10.6, figure_height),
        gridspec_kw={"width_ratios": [2.70, 1.25]},
    )
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

    estimate_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("estimate_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.20,
        font_size=axis_title_size,
        font_weight="bold",
    )
    x_axis_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.36,
        font_size=axis_title_size,
        font_weight="bold",
    )

    estimate_axes.set_title(
        "\n".join(estimate_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    estimate_axes.set_xlabel(
        "\n".join(x_axis_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    estimate_axes.axvline(reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    estimate_axes.set_xlim(x_lower, x_upper)
    estimate_axes.set_ylim(-0.6, row_count - 0.4)
    estimate_axes.invert_yaxis()
    estimate_axes.set_yticks([])
    estimate_axes.tick_params(axis="x", labelsize=tick_size, colors="#334155")
    estimate_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(estimate_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    summary_axes.set_xlim(0.0, 1.0)
    summary_axes.set_ylim(-0.6, row_count - 0.4)
    summary_axes.invert_yaxis()
    summary_axes.set_xticks([])
    summary_axes.set_yticks([])
    for spine in summary_axes.spines.values():
        spine.set_visible(False)
    summary_axes.set_facecolor("white")

    verdict_color_lookup = {
        "credible": comparator_color,
        "suggestive": "#b45309",
        "uncertain": "#475569",
    }

    def _format_interaction_p_value(value: float) -> str:
        if value < 0.001:
            return "<0.001"
        return f"{value:.3f}"

    row_label_artists: list[Any] = []
    support_label_artists: list[Any] = []
    verdict_artists: list[Any] = []
    detail_artists: list[Any] = []
    normalized_modifier_records: list[dict[str, Any]] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(estimate_axes.transAxes, estimate_axes.transData)

    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    row_band_height = 0.56
    for row_index, modifier in enumerate(modifiers):
        y_center = float(row_index)
        row_label_artists.append(
            estimate_axes.text(
                -0.03,
                y_center,
                str(modifier["modifier_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color="#334155",
                clip_on=False,
            )
        )
        estimate_axes.plot(
            [float(modifier["lower"]), float(modifier["upper"])],
            [y_center, y_center],
            color=comparator_color,
            linewidth=2.1,
            solid_capstyle="round",
            zorder=3,
        )
        estimate_axes.scatter(
            [float(modifier["interaction_estimate"])],
            [y_center],
            s=marker_size**2,
            color=model_color,
            edgecolors="white",
            linewidths=0.8,
            zorder=4,
        )
        support_label_artists.append(
            estimate_axes.text(
                0.98,
                y_center,
                f"n={int(modifier['support_n'])}",
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 1.0, 7.8),
                color="#64748b",
                clip_on=False,
            )
        )

        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.04, y_center - row_band_height / 2.0),
            0.92,
            row_band_height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=summary_axes.transData,
            facecolor=light_fill,
            edgecolor=summary_fill,
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_artist = summary_axes.text(
            0.10,
            y_center - 0.10,
            str(modifier["verdict"]).replace("_", " ").title(),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.9, 9.0),
            fontweight="bold",
            color=verdict_color_lookup.get(str(modifier["verdict"]), "#13293d"),
            zorder=2,
        )
        detail_text = (
            f"{str(modifier['favored_group_label'])}; "
            f"Pinteraction={_format_interaction_p_value(float(modifier['interaction_p_value']))}"
        )
        detail_lines = _wrap_flow_text_to_width(
            detail_text,
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 1.0, 7.8),
            font_weight="normal",
        )
        detail_artist = summary_axes.text(
            0.10,
            y_center + 0.10,
            "\n".join(detail_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.0, 7.8),
            color="#64748b",
            zorder=2,
        )
        verdict_artists.append(verdict_artist)
        detail_artists.append(detail_artist)
        normalized_modifier_records.append(
            {
                "modifier_id": str(modifier["modifier_id"]),
                "modifier_label": str(modifier["modifier_label"]),
                "interaction_estimate": float(modifier["interaction_estimate"]),
                "lower": float(modifier["lower"]),
                "upper": float(modifier["upper"]),
                "plot_y": float(y_center),
                "support_n": int(modifier["support_n"]),
                "favored_group_label": str(modifier["favored_group_label"]),
                "interaction_p_value": float(modifier["interaction_p_value"]),
                "verdict": str(modifier["verdict"]),
                "detail": detail_text,
            }
        )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.74, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.23, right=0.97, top=top_margin, bottom=0.22, wspace=0.17)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.026, 0.009), 0.017)
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

    panel_label_a = _add_panel_label(axes_item=estimate_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=summary_axes, label="B")
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
                bbox=estimate_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=summary_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_b.get_window_extent(renderer=renderer),
                box_id="panel_label_B",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=estimate_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=estimate_axes.get_window_extent(renderer=renderer),
            box_id="estimate_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=estimate_axes,
            figure=fig,
            x0=reference_value - reference_half_width,
            y0=-0.5,
            x1=reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_modifiers: list[dict[str, Any]] = []
    for modifier, row_label_artist, support_label_artist, verdict_artist, detail_artist in zip(
        normalized_modifier_records,
        row_label_artists,
        support_label_artists,
        verdict_artists,
        detail_artists,
        strict=True,
    ):
        modifier_id = str(modifier["modifier_id"])
        row_label_box_id = f"modifier_label_{modifier_id}"
        support_label_box_id = f"modifier_support_{modifier_id}"
        marker_box_id = f"estimate_{modifier_id}"
        interval_box_id = f"ci_{modifier_id}"
        verdict_box_id = f"verdict_{modifier_id}"
        detail_box_id = f"detail_{modifier_id}"
        plot_y = float(modifier["plot_y"])
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=row_label_artist.get_window_extent(renderer=renderer),
                    box_id=row_label_box_id,
                    box_type="row_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=support_label_artist.get_window_extent(renderer=renderer),
                    box_id=support_label_box_id,
                    box_type="support_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_artist.get_window_extent(renderer=renderer),
                    box_id=verdict_box_id,
                    box_type="verdict_value",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artist.get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                ),
                _data_box_to_layout_box(
                    axes=estimate_axes,
                    figure=fig,
                    x0=float(modifier["interaction_estimate"]) - marker_half_width,
                    y0=plot_y - marker_half_height,
                    x1=float(modifier["interaction_estimate"]) + marker_half_width,
                    y1=plot_y + marker_half_height,
                    box_id=marker_box_id,
                    box_type="estimate_marker",
                ),
                _data_box_to_layout_box(
                    axes=estimate_axes,
                    figure=fig,
                    x0=float(modifier["lower"]),
                    y0=plot_y - interval_half_height,
                    x1=float(modifier["upper"]),
                    y1=plot_y + interval_half_height,
                    box_id=interval_box_id,
                    box_type="ci_segment",
                ),
            ]
        )
        normalized_modifiers.append(
            {
                "modifier_id": modifier_id,
                "modifier_label": str(modifier["modifier_label"]),
                "interaction_estimate": float(modifier["interaction_estimate"]),
                "lower": float(modifier["lower"]),
                "upper": float(modifier["upper"]),
                "support_n": int(modifier["support_n"]),
                "favored_group_label": str(modifier["favored_group_label"]),
                "interaction_p_value": float(modifier["interaction_p_value"]),
                "verdict": str(modifier["verdict"]),
                "detail": str(modifier["detail"]),
                "label_box_id": row_label_box_id,
                "support_label_box_id": support_label_box_id,
                "marker_box_id": marker_box_id,
                "interval_box_id": interval_box_id,
                "verdict_box_id": verdict_box_id,
                "detail_box_id": detail_box_id,
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
                "reference_value": reference_value,
                "estimate_panel": {
                    "panel_box_id": "estimate_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "modifiers": normalized_modifiers,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

