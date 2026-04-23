from __future__ import annotations

import math
from typing import Any

import matplotlib

from ....shared import _read_bool_override, _require_non_empty_string


def _prepare_render_state(*, template_id: str, display_payload: dict[str, Any]) -> dict[str, Any]:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    alteration_records = list(display_payload.get("alteration_records") or [])
    driver_gene_order = list(display_payload.get("driver_gene_order") or [])
    consequence_panel_order = list(display_payload.get("consequence_panel_order") or [])
    consequence_points = list(display_payload.get("consequence_points") or [])
    pathway_order = list(display_payload.get("pathway_order") or [])
    pathway_panel_order = list(display_payload.get("pathway_panel_order") or [])
    pathway_points = list(display_payload.get("pathway_points") or [])
    if (
        not gene_order
        or not sample_order
        or not annotation_tracks
        or not alteration_records
        or not driver_gene_order
        or not consequence_panel_order
        or not consequence_points
        or not pathway_order
        or not pathway_panel_order
        or not pathway_points
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, alteration_records, "
            "driver_gene_order, consequence_panel_order, consequence_points, pathway_order, pathway_panel_order, and pathway_points"
        )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#f7ebeb").strip() or "#f7ebeb"
    background_color = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"

    gene_labels = [str(item["label"]) for item in gene_order]
    driver_gene_labels = [str(item["label"]) for item in driver_gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    pathway_labels = [str(item["label"]) for item in pathway_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}
    pathway_index = {pathway_label: index for index, pathway_label in enumerate(pathway_labels)}

    alteration_lookup = {
        (str(item["sample_id"]), str(item["gene_label"])): {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "mutation_class": str(item.get("mutation_class") or "").strip(),
            "cnv_state": str(item.get("cnv_state") or "").strip(),
        }
        for item in alteration_records
    }
    burden_counts = {
        sample_id: sum(1 for gene_label in gene_labels if (sample_id, gene_label) in alteration_lookup)
        for sample_id in sample_ids
    }
    gene_altered_counts = {
        gene_label: sum(1 for sample_id in sample_ids if (sample_id, gene_label) in alteration_lookup)
        for gene_label in gene_labels
    }
    gene_altered_fractions = {
        gene_label: gene_altered_counts[gene_label] / float(len(sample_ids))
        for gene_label in gene_labels
    }

    mutation_color_map = {
        "missense": primary_color,
        "truncating": "#8b3a3a",
        "fusion": "#475569",
    }
    cnv_color_map = {
        "amplification": secondary_color,
        "gain": "#d97706",
        "loss": "#0f766e",
        "deep_loss": "#111827",
    }
    alteration_label_map = {
        "missense": "Missense",
        "truncating": "Truncating",
        "fusion": "Fusion",
        "amplification": "Amplification",
        "gain": "Gain",
        "loss": "Loss",
        "deep_loss": "Deep loss",
    }
    track_palette_cycle = (
        primary_soft,
        secondary_soft,
        contrast_soft,
        "#eef2ff",
        "#f8fafc",
        "#ecfccb",
    )
    track_fill_by_id: dict[str, dict[str, str]] = {}
    for track in annotation_tracks:
        category_labels = [str(item["category_label"]) for item in track["values"]]
        ordered_categories = list(dict.fromkeys(category_labels))
        track_fill_by_id[str(track["track_id"])] = {
            category_label: track_palette_cycle[index % len(track_palette_cycle)]
            for index, category_label in enumerate(ordered_categories)
        }

    consequence_panel_ids = [str(item["panel_id"]) for item in consequence_panel_order]
    consequence_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in consequence_panel_order}
    consequence_point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in consequence_panel_ids}
    for point in consequence_points:
        consequence_point_lookup[str(point["panel_id"])].append(point)

    pathway_panel_ids = [str(item["panel_id"]) for item in pathway_panel_order]
    pathway_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in pathway_panel_order}
    pathway_point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in pathway_panel_ids}
    for point in pathway_points:
        pathway_point_lookup[str(point["panel_id"])].append(point)

    effect_threshold = float(display_payload.get("effect_threshold") or 0.0)
    significance_threshold = float(display_payload.get("significance_threshold") or 0.0)
    all_effect_values = [float(item["effect_value"]) for item in consequence_points]
    all_significance_values = [float(item["significance_value"]) for item in consequence_points]
    x_limit_core = max(max(abs(value) for value in all_effect_values), effect_threshold, 1e-6)
    x_padding = max(x_limit_core * 0.18, 0.20)
    x_limit_abs = x_limit_core + x_padding
    y_limit_top = max(max(all_significance_values), significance_threshold) * 1.12 + 0.25
    y_limit_top = max(y_limit_top, significance_threshold + 0.50)

    pathway_x_values = [float(item["x_value"]) for item in pathway_points]
    pathway_effect_values = [float(item["effect_value"]) for item in pathway_points]
    pathway_size_values = [float(item["size_value"]) for item in pathway_points]
    pathway_x_min = min(pathway_x_values)
    pathway_x_max = max(pathway_x_values)
    pathway_x_span = max(pathway_x_max - pathway_x_min, 1e-6)
    pathway_x_padding = max(pathway_x_span * 0.08, 0.12)
    pathway_size_min = min(pathway_size_values)
    pathway_size_max = max(pathway_size_values)
    pathway_max_abs_effect = max(max(abs(value) for value in pathway_effect_values), 1e-6)
    if any(value < 0.0 for value in pathway_effect_values) and any(value > 0.0 for value in pathway_effect_values):
        pathway_color_norm: matplotlib.colors.Normalize = matplotlib.colors.TwoSlopeNorm(
            vmin=-pathway_max_abs_effect,
            vcenter=0.0,
            vmax=pathway_max_abs_effect,
        )
    else:
        min_effect = min(pathway_effect_values)
        max_effect = max(pathway_effect_values)
        if math.isclose(min_effect, max_effect, rel_tol=1e-9, abs_tol=1e-9):
            min_effect -= 1.0
            max_effect += 1.0
        pathway_color_norm = matplotlib.colors.Normalize(vmin=min_effect, vmax=max_effect)
    pathway_effect_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "pathway_integrated_composite",
        [primary_color, "#f8fafc", secondary_color],
    )

    def pathway_marker_size(size_value: float) -> float:
        if math.isclose(pathway_size_min, pathway_size_max, rel_tol=1e-9, abs_tol=1e-9):
            return 200.0
        normalized = (size_value - pathway_size_min) / (pathway_size_max - pathway_size_min)
        return 110.0 + normalized * 250.0

    return {
        "annotation_tracks": annotation_tracks,
        "alteration_label_map": alteration_label_map,
        "alteration_lookup": alteration_lookup,
        "axis_title_size": axis_title_size,
        "background_color": background_color,
        "burden_counts": burden_counts,
        "cnv_color_map": cnv_color_map,
        "consequence_panel_ids": consequence_panel_ids,
        "consequence_point_lookup": consequence_point_lookup,
        "consequence_title_lookup": consequence_title_lookup,
        "contrast_soft": contrast_soft,
        "display_payload": display_payload,
        "driver_gene_labels": driver_gene_labels,
        "effect_threshold": effect_threshold,
        "gene_altered_fractions": gene_altered_fractions,
        "gene_index": gene_index,
        "gene_labels": gene_labels,
        "light_fill": light_fill,
        "mutation_color_map": mutation_color_map,
        "neutral_color": neutral_color,
        "panel_label_size": panel_label_size,
        "pathway_color_norm": pathway_color_norm,
        "pathway_effect_cmap": pathway_effect_cmap,
        "pathway_index": pathway_index,
        "pathway_labels": pathway_labels,
        "pathway_marker_size": pathway_marker_size,
        "pathway_panel_ids": pathway_panel_ids,
        "pathway_point_lookup": pathway_point_lookup,
        "pathway_size_max": pathway_size_max,
        "pathway_size_min": pathway_size_min,
        "pathway_title_lookup": pathway_title_lookup,
        "pathway_x_max": pathway_x_max,
        "pathway_x_min": pathway_x_min,
        "pathway_x_padding": pathway_x_padding,
        "primary_color": primary_color,
        "sample_ids": sample_ids,
        "sample_index": sample_index,
        "secondary_color": secondary_color,
        "show_figure_title": show_figure_title,
        "significance_threshold": significance_threshold,
        "tick_size": tick_size,
        "title_size": title_size,
        "track_fill_by_id": track_fill_by_id,
        "x_limit_abs": x_limit_abs,
        "y_limit_top": y_limit_top,
    }
