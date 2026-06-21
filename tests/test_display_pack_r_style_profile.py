from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def test_core_r_helper_consumes_publication_style_profile_tokens() -> None:
    assert shutil.which("Rscript") is not None
    repo_root = Path(__file__).resolve().parents[1]
    r_script = """
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/evidence_renderer.R")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/candidate_renderer.R")
payload <- list(
  title = "Probe",
  x_label = "x",
  y_label = "y",
  series = list(
    list(label = "Model", x = list(0, 1), y = list(0, 1)),
    list(label = "Comparator", x = list(0, 1), y = list(0, 0.8))
  ),
    reference_line = list(x = list(0, 1), y = list(0, 1)),
  render_context = list(
    style_profile_id = "probe",
    style_profile_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    palette = list(primary = "#123456", secondary = "#654321", neutral = "#999999", text = "#111111", grid = "#EEEEEE", heatmap_seq_low = "#F4F8FA", heatmap_seq_mid = "#9DD2D3", heatmap_seq_high = "#0B4F6C", heatmap_low = "#2B6CB0", heatmap_mid = "#F7F7F7", heatmap_high = "#B64342"),
    semantic_roles = list(model_curve = "primary", comparator_curve = "secondary", reference_line = "neutral", text = "text", grid_line = "grid", heatmap_seq_low = "heatmap_seq_low", heatmap_seq_mid = "heatmap_seq_mid", heatmap_seq_high = "heatmap_seq_high", heatmap_low = "heatmap_low", heatmap_mid = "heatmap_mid", heatmap_high = "heatmap_high"),
    style_roles = list(model_curve = "#123456", comparator_curve = "#654321", reference_line = "#999999", text = "#111111", grid_line = "#EEEEEE", heatmap_seq_low = "#F4F8FA", heatmap_seq_mid = "#9DD2D3", heatmap_seq_high = "#0B4F6C", heatmap_low = "#2B6CB0", heatmap_mid = "#F7F7F7", heatmap_high = "#B64342"),
    typography = list(font_family = "sans", base_size = 10, title_size = 13, axis_title_size = 11, tick_size = 9, legend_size = 7.2, colorbar_width = 5, colorbar_height = 42, colorbar_horizontal_width = 260, colorbar_horizontal_height = 6, colorbar_max_breaks = 8, colorbar_label_size = 5.6),
    stroke = list(primary_linewidth = 2.4, reference_linewidth = 1.2, grid_linewidth = 0.33),
    grid = list(major = TRUE, minor = FALSE, major_axis = "both", color = "#EEEEEE"),
    layout_override = list(output_width_in = 5, output_height_in = 5)
  )
)
plot <- build_evidence_plot("roc_curve_binary", payload)
built <- ggplot2::ggplot_build(plot)
all_colours <- unique(unlist(lapply(built$data, function(layer) layer$colour %||% character())))
stopifnot("#123456" %in% all_colours)
stopifnot("#999999" %in% all_colours)
theme_obj <- lidocaine_publication_theme(payload)
stopifnot(identical(theme_obj$plot.title$colour, "#111111"))
stopifnot(inherits(theme_obj$panel.border, "element_rect"))
stopifnot(isTRUE(abs(theme_obj$panel.border$linewidth - 0.45) < 1e-9))
layout <- build_layout_sidecar(plot, "roc_curve_binary", payload)
stopifnot(identical(layout$render_context$style_profile_id, "probe"))
stopifnot(identical(layout$style_profile$style_profile_sha256, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))
stopifnot(identical(layout$metrics$source_renderer, "LidocaineQ/Figure_Template::roc_auc"))
stopifnot(render_device_dimension(payload, "output_width_in", "MAS_DISPLAY_OUTPUT_WIDTH_IN", 7.2) == 5)
stopifnot(render_device_dimension(payload, "output_height_in", "MAS_DISPLAY_OUTPUT_HEIGHT_IN", 5.0) == 5)
candidate_plot <- build_candidate_evidence_plot("time_to_event_decision_curve", payload)
candidate_built <- ggplot2::ggplot_build(candidate_plot)
stopifnot("#123456" %in% candidate_built$data[[1]]$colour)
calibration_payload <- payload
calibration_payload$points <- list(
  list(predicted = 0.05, observed = 0.04, lower = 0.01, upper = 0.10),
  list(predicted = 0.25, observed = 0.27, lower = 0.18, upper = 0.34),
  list(predicted = 0.50, observed = 0.48, lower = 0.39, upper = 0.58),
  list(predicted = 0.75, observed = 0.77, lower = 0.67, upper = 0.85)
)
calibration_plot <- build_evidence_plot("calibration_curve_binary", calibration_payload)
calibration_built <- ggplot2::ggplot_build(calibration_plot)
calibration_colours <- unique(unlist(lapply(calibration_built$data, function(layer) layer$colour %||% character())))
calibration_fills <- unique(unlist(lapply(calibration_built$data, function(layer) layer$fill %||% character())))
stopifnot("#123456" %in% calibration_fills)
stopifnot("#654321" %in% calibration_colours)
calibration_layout <- build_layout_sidecar(calibration_plot, "calibration_curve_binary", calibration_payload)
stopifnot(identical(calibration_layout$metrics$source_renderer, "LidocaineQ/Figure_Template::calibration_curve_binary"))
time_roc_plot <- build_evidence_plot("time_dependent_roc_horizon", payload)
time_roc_layout <- build_layout_sidecar(time_roc_plot, "time_dependent_roc_horizon", payload)
stopifnot(identical(time_roc_layout$metrics$source_renderer, "LidocaineQ/Figure_Template::time_dependent_roc_horizon"))
heatmap_payload <- payload
heatmap_payload$cells <- list(
  list(x = "A", y = "Row 1", value = 0.10),
  list(x = "B", y = "Row 1", value = 0.45),
  list(x = "A", y = "Row 2", value = 0.70),
  list(x = "B", y = "Row 2", value = 0.95)
)
heatmap_payload$column_order <- list(list(label = "A"), list(label = "B"))
heatmap_payload$row_order <- list(list(label = "Row 1"), list(label = "Row 2"))
heatmap_plot <- build_evidence_plot("heatmap_group_comparison", heatmap_payload)
heatmap_built <- ggplot2::ggplot_build(heatmap_plot)
fill_scales <- Filter(function(scale) "fill" %in% scale$aesthetics, heatmap_built$plot$scales$scales)
stopifnot(length(fill_scales) == 1)
stopifnot(!("#B64342" %in% heatmap_built$data[[1]]$fill))
heatmap_layout <- build_layout_sidecar(heatmap_plot, "heatmap_group_comparison", heatmap_payload)
stopifnot(identical(heatmap_layout$metrics$source_renderer, "LidocaineQ/Figure_Template::heatmap"))
stopifnot(any(vapply(heatmap_layout$guide_boxes, function(item) identical(item$box_type, "colorbar"), logical(1))))
breaks <- continuous_scale_breaks(c(0.10, 0.45, 0.70, 0.95), max_breaks = 3)
stopifnot(length(breaks) <= 3)
crowded_breaks <- continuous_scale_breaks(c(0.55, 0.60, 0.65, 0.70, 0.75, 0.80), max_breaks = 8)
stopifnot(length(crowded_breaks) <= 3)
heatmap_components <- heatmap_scale_components(heatmap_payload, c(0.55, 0.60, 0.65, 0.70, 0.75, 0.80), name = "Alteration fraction")
stopifnot(length(heatmap_components$breaks) <= 3)
guide <- publication_colorbar_guide(payload, title = "Score", bar_orientation = "horizontal")
stopifnot(!is.null(guide))
stopifnot(as.numeric(guide$barwidth) >= 260)
stopifnot(as.numeric(guide$barheight) >= 6)
colorbar_theme <- theme_publication_colorbar(payload)
stopifnot(identical(as.numeric(colorbar_theme$legend.text$size), 5.6))
stopifnot(as.numeric(colorbar_theme$legend.spacing.x) >= 8)
stopifnot(publication_legend_guides(payload, c("a", "b", "c", "d"))$nrow == 2)
stopifnot(publication_legend_guides(payload, c("a", "b", "c", "d", "e", "f", "g"))$nrow == 3)
"""

    result = subprocess.run(
        ["Rscript", "-e", r_script],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr


def test_lidocaineq_source_renderers_cover_existing_same_type_templates() -> None:
    assert shutil.which("Rscript") is not None
    repo_root = Path(__file__).resolve().parents[1]
    r_script = r"""
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/evidence_renderer.R")
payload <- list(
  title = "Probe",
  x_label = "x",
  y_label = "y",
  render_context = list(
    style_profile_id = "probe",
    style_profile_sha256 = paste(rep("b", 64), collapse = ""),
    palette = list(primary = "#245A6B", secondary = "#8B3A3A", tertiary = "#D8A24A", quaternary = "#2A9D8F", violet = "#6D5BD0", neutral = "#13293D", neutral_mid = "#64748B", neutral_light = "#B7C4CC", light = "#EEF4F7", text = "#13293D", axis = "#13293D", grid = "#E6EDF2", background = "#FFFFFF", muted = "#64748B", heatmap_seq_low = "#EEF4F7", heatmap_seq_mid = "#86BCC2", heatmap_seq_high = "#245A6B", heatmap_low = "#2166AC", heatmap_mid = "#F7F7F7", heatmap_high = "#B2182B", volcano_up = "#B2182B", volcano_down = "#2166AC", volcano_background = "#B7C4CC"),
    semantic_roles = list(model_curve = "primary", comparator_curve = "secondary", reference_line = "neutral_mid", highlight_band = "light", text = "text", axis_line = "axis", grid_line = "grid", figure_background = "background", series_1 = "primary", series_2 = "secondary", series_3 = "tertiary", series_4 = "quaternary", series_5 = "violet", series_6 = "neutral_mid", heatmap_low = "heatmap_low", heatmap_mid = "heatmap_mid", heatmap_high = "heatmap_high", heatmap_seq_low = "heatmap_seq_low", heatmap_seq_mid = "heatmap_seq_mid", heatmap_seq_high = "heatmap_seq_high", volcano_up = "volcano_up", volcano_down = "volcano_down", volcano_background = "volcano_background"),
    style_roles = list(model_curve = "#245A6B", comparator_curve = "#8B3A3A", reference_line = "#64748B", text = "#13293D", axis_line = "#13293D", grid_line = "#E6EDF2", heatmap_seq_low = "#EEF4F7", heatmap_seq_mid = "#86BCC2", heatmap_seq_high = "#245A6B", heatmap_low = "#2166AC", heatmap_mid = "#F7F7F7", heatmap_high = "#B2182B", volcano_up = "#B2182B", volcano_down = "#2166AC", volcano_background = "#B7C4CC"),
    typography = list(font_family = "sans", base_size = 11, title_size = 12.5, subtitle_size = 9.5, axis_title_size = 10.5, tick_size = 9.2, legend_size = 9, colorbar_width = 5, colorbar_height = 42, colorbar_horizontal_width = 260, colorbar_horizontal_height = 6, colorbar_max_breaks = 3, colorbar_label_size = 5.6),
    stroke = list(axis_linewidth = 0.45, primary_linewidth = 2.0, reference_linewidth = 0.9, grid_linewidth = 0.25, marker_size = 3.4),
    grid = list(major = TRUE, minor = FALSE, major_axis = "both", color = "#E6EDF2"),
    layout_override = list(output_width_in = 5, output_height_in = 5)
  )
)
probe_plot <- ggplot2::ggplot(data.frame(x = c(0, 1), y = c(0, 1)), ggplot2::aes(x, y)) + ggplot2::geom_line()
expected <- list(
  roc_curve_binary = "LidocaineQ/Figure_Template::roc_auc",
  time_dependent_roc_horizon = "LidocaineQ/Figure_Template::time_dependent_roc_horizon",
  calibration_curve_binary = "LidocaineQ/Figure_Template::calibration_curve_binary",
  pr_curve_binary = "LidocaineQ/Figure_Template::pr_curve_binary",
  decision_curve_binary = "LidocaineQ/Figure_Template::decision_curve_binary",
  time_to_event_decision_curve = "LidocaineQ/Figure_Template::time_to_event_decision_curve",
  time_to_event_multihorizon_calibration_panel = "LidocaineQ/Figure_Template::time_to_event_multihorizon_calibration_panel",
  kaplan_meier_grouped = "LidocaineQ/Figure_Template::survival_km",
  cumulative_incidence_grouped = "LidocaineQ/Figure_Template::cumulative_incidence_grouped",
  forest_effect_main = "LidocaineQ/Figure_Template::forest_cox",
  heatmap_group_comparison = "LidocaineQ/Figure_Template::heatmap",
  confusion_matrix_heatmap_binary = "LidocaineQ/Figure_Template::confusion_matrix_heatmap_binary",
  coefficient_path_panel = "LidocaineQ/Figure_Template::coefficient_path_panel",
  generalizability_subgroup_composite_panel = "LidocaineQ/Figure_Template::generalizability_subgroup_composite_panel",
  pathway_enrichment_dotplot_panel = "LidocaineQ/Figure_Template::gsea_enrichment",
  celltype_marker_dotplot_panel = "LidocaineQ/Figure_Template::celltype_marker_dotplot_panel",
  omics_volcano_panel = "LidocaineQ/Figure_Template::volcano_deg",
  genomic_alteration_landscape_panel = "LidocaineQ/Figure_Template::oncoplot_mutation",
  cnv_recurrence_summary_panel = "LidocaineQ/Figure_Template::cnv_recurrence_summary_panel",
  genomic_alteration_consequence_panel = "LidocaineQ/Figure_Template::genomic_alteration_consequence_panel",
  shap_summary_beeswarm = "LidocaineQ/Figure_Template::shap_summary_beeswarm",
  shap_dependence_panel = "LidocaineQ/Figure_Template::shap_dependence_panel",
  shap_waterfall_local_explanation_panel = "LidocaineQ/Figure_Template::shap_waterfall_local_explanation_panel",
  model_complexity_audit_panel = "LidocaineQ/Figure_Template::model_complexity_audit_panel",
  distribution_violin_box = "LidocaineQ/Figure_Template::violin_box",
  composition_stacked_bar = "LidocaineQ/Figure_Template::bar_stacked",
  correlation_scatter = "LidocaineQ/Figure_Template::scatter_correlation",
  alluvial_transition = "LidocaineQ/Figure_Template::sankey_alluvial",
  radar_profile = "LidocaineQ/Figure_Template::radar",
  waterfall_response = "LidocaineQ/Figure_Template::waterfall",
  table1_baseline_characteristics = "LidocaineQ/Figure_Template::baseline_table"
)
for (template_id in names(expected)) {
  layout <- build_layout_sidecar(probe_plot, template_id, payload)
  stopifnot(identical(layout$metrics$source_renderer, expected[[template_id]]))
}
table_payload <- payload
table_payload$rows <- list(
  list(variable = "Age, years", overall = "63.4 (11.2)", group_a = "61.8 (10.9)", group_b = "65.0 (11.3)", p_value = "0.021"),
  list(variable = "Female sex", overall = "118 (46.1)", group_a = "61 (47.7)", group_b = "57 (44.5)", p_value = "0.706"),
  list(variable = "Stage", level = "I-II", overall = "142 (55.5)", group_a = "82 (64.1)", group_b = "60 (46.9)", p_value = "")
)
table_plot <- build_evidence_plot("table1_baseline_characteristics", table_payload)
table_layout <- build_layout_sidecar(table_plot, "table1_baseline_characteristics", table_payload)
stopifnot(identical(table_layout$metrics$source_renderer, "LidocaineQ/Figure_Template::baseline_table"))
"""

    result = subprocess.run(
        ["Rscript", "-e", r_script],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
