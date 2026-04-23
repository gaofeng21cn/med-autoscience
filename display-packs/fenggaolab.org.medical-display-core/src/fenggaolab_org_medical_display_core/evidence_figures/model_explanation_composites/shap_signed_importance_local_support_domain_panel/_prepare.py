from __future__ import annotations

from typing import Any

import matplotlib

from ....shared import _read_bool_override, _require_non_empty_string


def _prepare_shap_signed_importance_local_support_domain_data(
    *,
    template_id: str,
    display_payload: dict[str, Any],
) -> dict[str, Any]:
    importance_panel = dict(display_payload.get("importance_panel") or {})
    local_panel = dict(display_payload.get("local_panel") or {})
    support_panels = list(display_payload.get("support_panels") or [])
    if not importance_panel or not local_panel or len(support_panels) != 2:
        raise RuntimeError(
            f"{template_id} requires one importance_panel, one local_panel, and exactly two support_panels"
        )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    curve_color = negative_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_importance_bars = [
        {
            "rank": int(item["rank"]),
            "feature": str(item["feature"]),
            "signed_importance_value": float(item["signed_importance_value"]),
        }
        for item in list(importance_panel.get("bars") or [])
    ]
    if not normalized_importance_bars:
        raise RuntimeError(f"{template_id} importance_panel requires non-empty bars")

    raw_local_contributions = list(local_panel.get("contributions") or [])
    normalized_local_contributions: list[dict[str, Any]] = []
    local_running_value = float(local_panel["baseline_value"])
    for contribution_index, item in enumerate(raw_local_contributions):
        shap_value = float(item["shap_value"])
        start_value = local_running_value
        end_value = local_running_value + shap_value
        if contribution_index == len(raw_local_contributions) - 1:
            end_value = float(local_panel["predicted_value"])
        normalized_local_contributions.append(
            {
                "feature": str(item["feature"]),
                "feature_value_text": str(item.get("feature_value_text") or "").strip(),
                "shap_value": shap_value,
                "start_value": start_value,
                "end_value": end_value,
            }
        )
        local_running_value = end_value
    if not normalized_local_contributions:
        raise RuntimeError(f"{template_id} local_panel requires non-empty contributions")

    all_local_values = [float(local_panel["baseline_value"]), float(local_panel["predicted_value"])]
    for contribution in normalized_local_contributions:
        all_local_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))
    local_x_min = min(all_local_values)
    local_x_max = max(all_local_values)
    local_x_span = max(local_x_max - local_x_min, 1e-6)
    local_x_padding = max(local_x_span * 0.12, 0.05)
    local_x_lower = local_x_min - local_x_padding
    local_x_upper = local_x_max + local_x_padding
    local_marker_half_width = max(local_x_span * 0.004, 0.0025)

    normalized_support_panels: list[dict[str, Any]] = []
    all_curve_y: list[float] = []
    for panel in support_panels:
        curve_x = [float(value) for value in panel["response_curve"]["x"]]
        curve_y = [float(value) for value in panel["response_curve"]["y"]]
        all_curve_y.extend(curve_y)
        normalized_support_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "response_curve": {"x": curve_x, "y": curve_y},
                "support_segments": [
                    {
                        "segment_id": str(segment["segment_id"]),
                        "segment_label": str(segment["segment_label"]),
                        "support_kind": str(segment["support_kind"]),
                        "domain_start": float(segment["domain_start"]),
                        "domain_end": float(segment["domain_end"]),
                    }
                    for segment in panel["support_segments"]
                ],
            }
        )

    importance_values = [float(item["signed_importance_value"]) for item in normalized_importance_bars]
    importance_max_abs_value = max(abs(value) for value in importance_values)
    importance_padding = max(importance_max_abs_value * 0.18, 0.02)
    importance_core_limit = importance_max_abs_value + importance_padding
    importance_label_padding = max(importance_core_limit * 0.03, 0.018)
    importance_axis_limit = importance_core_limit + importance_label_padding * 3.2
    importance_zero_line_half_width = max(importance_core_limit * 0.008, 0.0025)

    curve_y_min = min(all_curve_y)
    curve_y_max = max(all_curve_y)
    curve_y_span = max(curve_y_max - curve_y_min, 1e-6)
    support_band_height = max(curve_y_span * 0.18, 0.06)
    support_band_gap = max(curve_y_span * 0.14, 0.05)
    band_y1 = curve_y_min - support_band_gap
    band_y0 = band_y1 - support_band_height
    curve_y_padding = max(curve_y_span * 0.18, 0.05)
    plot_y_lower = band_y0 - max(support_band_height * 0.40, 0.05)
    plot_y_upper = curve_y_max + curve_y_padding
    observed_fill = str(palette.get("primary") or curve_color).strip() or curve_color
    subgroup_fill = "#0f766e"
    bin_fill = "#b45309"
    extrapolation_fill = "#dc2626"
    support_style_map = {
        "observed_support": {
            "facecolor": matplotlib.colors.to_rgba(observed_fill, alpha=0.20),
            "edgecolor": observed_fill,
            "legend_label": "Observed support",
        },
        "subgroup_support": {
            "facecolor": matplotlib.colors.to_rgba(subgroup_fill, alpha=0.18),
            "edgecolor": subgroup_fill,
            "legend_label": "Subgroup support",
        },
        "bin_support": {
            "facecolor": matplotlib.colors.to_rgba(bin_fill, alpha=0.18),
            "edgecolor": bin_fill,
            "legend_label": "Bin support",
        },
        "extrapolation_warning": {
            "facecolor": matplotlib.colors.to_rgba(extrapolation_fill, alpha=0.14),
            "edgecolor": extrapolation_fill,
            "legend_label": "Extrapolation reminder",
        },
    }
    support_legend_labels = list(display_payload.get("support_legend_labels") or []) or [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]

    importance_panel_height = max(4.9, 0.58 * len(normalized_importance_bars) + 1.8)
    local_panel_height = max(4.9, 0.62 * len(normalized_local_contributions) + 2.0)
    top_row_height = max(importance_panel_height, local_panel_height)
    support_row_height = 3.9
    figure_height = top_row_height + support_row_height + 1.2
    figure_width = 11.8

    return {
        "axis_title_size": axis_title_size,
        "band_y0": band_y0,
        "band_y1": band_y1,
        "curve_color": curve_color,
        "importance_axis_limit": importance_axis_limit,
        "importance_panel": importance_panel,
        "importance_panel_height": importance_panel_height,
        "importance_zero_line_half_width": importance_zero_line_half_width,
        "local_marker_half_width": local_marker_half_width,
        "local_panel": local_panel,
        "local_panel_height": local_panel_height,
        "local_x_lower": local_x_lower,
        "local_x_upper": local_x_upper,
        "marker_size": marker_size,
        "negative_color": negative_color,
        "normalized_importance_bars": normalized_importance_bars,
        "normalized_local_contributions": normalized_local_contributions,
        "normalized_support_panels": normalized_support_panels,
        "panel_label_size": panel_label_size,
        "plot_y_lower": plot_y_lower,
        "plot_y_upper": plot_y_upper,
        "positive_color": positive_color,
        "reference_color": reference_color,
        "show_figure_title": show_figure_title,
        "support_band_height": support_band_height,
        "support_legend_labels": support_legend_labels,
        "support_row_height": support_row_height,
        "support_style_map": support_style_map,
        "tick_size": tick_size,
        "title_size": title_size,
        "top_row_height": top_row_height,
        "figure_height": figure_height,
        "figure_width": figure_width,
    }
