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

def _render_python_center_transportability_governance_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    centers = list(display_payload.get("centers") or [])
    if not centers:
        raise RuntimeError(f"{template_id} requires non-empty centers")

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
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    derivation_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    validation_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    light_fill = str(palette.get("light") or "#f8fafc").strip() or "#f8fafc"
    summary_fill = str(palette.get("secondary_soft") or "#e2e8f0").strip() or "#e2e8f0"
    audit_color = str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed"
    primary_fill = str(palette.get("primary_soft") or "#eff6ff").strip() or "#eff6ff"
    neutral_text = "#334155"

    verdict_color_lookup = {
        "stable": derivation_color,
        "context_dependent": audit_color,
        "recalibration_required": audit_color,
        "insufficient_support": reference_color,
        "unstable": "#7f1d1d",
    }

    def _center_color(center_payload: dict[str, Any]) -> str:
        cohort_role = str(center_payload.get("cohort_role") or "").strip().casefold()
        if "derivation" in cohort_role or "train" in cohort_role:
            return derivation_color
        if "validation" in cohort_role:
            return validation_color
        return audit_color

    metric_values = [float(display_payload["metric_reference_value"])]
    for center in centers:
        metric_values.extend(
            (
                float(center["metric_lower"]),
                float(center["metric_estimate"]),
                float(center["metric_upper"]),
            )
        )
    x_min = min(metric_values)
    x_max = max(metric_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.03)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.010)
    marker_half_height = 0.085
    interval_half_height = 0.028
    reference_half_width = max((x_upper - x_lower) * 0.004, 0.0015)

    row_count = len(centers)
    figure_height = max(5.4, 1.02 * row_count + 2.5)
    fig, (metric_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(11.2, figure_height),
        gridspec_kw={"width_ratios": [2.15, 1.25]},
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

    metric_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("metric_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.23,
        font_size=axis_title_size,
        font_weight="bold",
    )
    metric_x_label_lines = _wrap_flow_text_to_width(
        str(display_payload.get("metric_x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.32,
        font_size=axis_title_size,
        font_weight="bold",
    )

    metric_axes.set_title(
        "\n".join(metric_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    metric_axes.set_xlabel(
        "\n".join(metric_x_label_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    metric_reference_value = float(display_payload["metric_reference_value"])
    metric_axes.axvline(metric_reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    metric_axes.set_xlim(x_lower, x_upper)
    metric_axes.set_ylim(-0.6, row_count - 0.4)
    metric_axes.invert_yaxis()
    metric_axes.set_yticks([])
    metric_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_text)
    metric_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(metric_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
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

    row_label_artists: list[Any] = []
    center_metrics_for_sidecar: list[dict[str, Any]] = []
    verdict_artists: list[Any] = []
    metrics_text_artists: list[Any] = []
    action_artists: list[Any] = []
    detail_artists: list[Any | None] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(metric_axes.transAxes, metric_axes.transData)
    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18

    for row_index, center in enumerate(centers):
        y_center = float(row_index)
        row_label_artists.append(
            metric_axes.text(
                -0.03,
                y_center,
                str(center["center_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color=neutral_text,
                clip_on=False,
            )
        )
        interval_color = _center_color(center)
        metric_axes.plot(
            [float(center["metric_lower"]), float(center["metric_upper"])],
            [y_center, y_center],
            color=interval_color,
            linewidth=2.2,
            solid_capstyle="round",
            zorder=3,
        )
        metric_axes.scatter(
            [float(center["metric_estimate"])],
            [y_center],
            s=marker_size**2,
            color=interval_color,
            edgecolors="white",
            linewidths=0.8,
            zorder=4,
        )

        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, y_center - 0.36),
            0.90,
            0.72,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            transform=summary_axes.transData,
            facecolor=primary_fill if row_index % 2 == 0 else light_fill,
            edgecolor=summary_fill,
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_lines = _wrap_flow_text_to_width(
            str(center["verdict"]).replace("_", " "),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        verdict_artist = summary_axes.text(
            0.08,
            y_center - 0.18,
            "\n".join(verdict_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color=verdict_color_lookup.get(str(center["verdict"]), neutral_text),
            zorder=2,
        )
        metrics_line = (
            f"n={int(center['support_count'])} | events={int(center['event_count'])} | "
            f"shift={float(center['max_shift']):.2f}\n"
            f"slope={float(center['slope']):.2f} | O:E={float(center['oe_ratio']):.2f}"
        )
        metrics_artist = summary_axes.text(
            0.08,
            y_center + 0.00,
            metrics_line,
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.0, 7.9),
            color=neutral_text,
            zorder=2,
        )
        action_lines = _wrap_flow_text_to_width(
            str(center["action"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 0.8, 8.1),
            font_weight="bold",
        )
        action_artist = summary_axes.text(
            0.08,
            y_center + 0.18,
            "\n".join(action_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 0.8, 8.1),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        detail_text = str(center.get("detail") or "").strip()
        if detail_text:
            detail_lines = _wrap_flow_text_to_width(
                detail_text,
                max_width_pt=summary_text_width_pt,
                font_size=max(tick_size - 1.2, 7.6),
                font_weight="normal",
            )
            detail_artist = summary_axes.text(
                0.08,
                y_center + 0.33,
                "\n".join(detail_lines),
                transform=summary_axes.transData,
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.2, 7.6),
                color="#64748b",
                zorder=2,
            )

        verdict_artists.append(verdict_artist)
        metrics_text_artists.append(metrics_artist)
        action_artists.append(action_artist)
        detail_artists.append(detail_artist)
        normalized_center = {
            "center_id": str(center["center_id"]),
            "center_label": str(center["center_label"]),
            "cohort_role": str(center["cohort_role"]),
            "support_count": int(center["support_count"]),
            "event_count": int(center["event_count"]),
            "metric_estimate": float(center["metric_estimate"]),
            "metric_lower": float(center["metric_lower"]),
            "metric_upper": float(center["metric_upper"]),
            "max_shift": float(center["max_shift"]),
            "slope": float(center["slope"]),
            "oe_ratio": float(center["oe_ratio"]),
            "verdict": str(center["verdict"]),
            "action": str(center["action"]),
        }
        if detail_text:
            normalized_center["detail"] = detail_text
        center_metrics_for_sidecar.append(normalized_center)

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.23, right=0.97, top=top_margin, bottom=0.18, wspace=0.18)
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

    panel_label_a = _add_panel_label(axes_item=metric_axes, label="A")
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
                bbox=metric_axes.title.get_window_extent(renderer=renderer),
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
                bbox=metric_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=metric_axes.get_window_extent(renderer=renderer),
            box_id="metric_panel",
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
            axes=metric_axes,
            figure=fig,
            x0=metric_reference_value - reference_half_width,
            y0=-0.5,
            x1=metric_reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_centers: list[dict[str, Any]] = []
    for row_index, center in enumerate(center_metrics_for_sidecar):
        center_id = str(center["center_id"])
        y_center = float(row_index)
        row_label_box_id = f"row_label_{center_id}"
        metric_box_id = f"metric_{center_id}"
        interval_box_id = f"ci_{center_id}"
        verdict_box_id = f"verdict_{center_id}"
        metrics_box_id = f"metrics_{center_id}"
        action_box_id = f"action_{center_id}"
        detail_box_id = ""

        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=row_label_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=row_label_box_id,
                    box_type="row_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=verdict_box_id,
                    box_type="verdict_value",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=metrics_text_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=metrics_box_id,
                    box_type="row_metric",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=action_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=action_box_id,
                    box_type="row_action",
                ),
                _data_box_to_layout_box(
                    axes=metric_axes,
                    figure=fig,
                    x0=float(center["metric_estimate"]) - marker_half_width,
                    y0=y_center - marker_half_height,
                    x1=float(center["metric_estimate"]) + marker_half_width,
                    y1=y_center + marker_half_height,
                    box_id=metric_box_id,
                    box_type="estimate_marker",
                ),
                _data_box_to_layout_box(
                    axes=metric_axes,
                    figure=fig,
                    x0=float(center["metric_lower"]),
                    y0=y_center - interval_half_height,
                    x1=float(center["metric_upper"]),
                    y1=y_center + interval_half_height,
                    box_id=interval_box_id,
                    box_type="ci_segment",
                ),
            ]
        )
        if detail_artists[row_index] is not None:
            detail_box_id = f"detail_{center_id}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                )
            )

        normalized_center = dict(center)
        normalized_center.update(
            {
                "label_box_id": row_label_box_id,
                "metric_box_id": metric_box_id,
                "interval_box_id": interval_box_id,
                "verdict_box_id": verdict_box_id,
                "metrics_box_id": metrics_box_id,
                "action_box_id": action_box_id,
            }
        )
        if detail_box_id:
            normalized_center["detail_box_id"] = detail_box_id
        normalized_centers.append(normalized_center)

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_family": str(display_payload.get("metric_family") or "").strip(),
                "metric_reference_value": metric_reference_value,
                "metric_panel": {
                    "panel_box_id": "metric_panel",
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
                "batch_shift_threshold": float(display_payload["batch_shift_threshold"]),
                "slope_acceptance_lower": float(display_payload["slope_acceptance_lower"]),
                "slope_acceptance_upper": float(display_payload["slope_acceptance_upper"]),
                "oe_ratio_acceptance_lower": float(display_payload["oe_ratio_acceptance_lower"]),
                "oe_ratio_acceptance_upper": float(display_payload["oe_ratio_acceptance_upper"]),
                "centers": normalized_centers,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

