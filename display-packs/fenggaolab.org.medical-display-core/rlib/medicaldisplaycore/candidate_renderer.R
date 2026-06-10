`%|||%` <- function(left, right) {
  if (is.null(left) || length(left) == 0) right else left
}

candidate_non_empty <- function(value, fallback) {
  text <- trimws(as.character(value %||% ""))
  if (nzchar(text)) text else fallback
}

candidate_items <- function(payload, fields) {
  for (field_name in fields) {
    value <- payload[[field_name]]
    if (is.list(value) && length(value) > 0) {
      return(value)
    }
  }
  list()
}

candidate_numeric <- function(value, fallback = 0) {
  if (is.null(value)) {
    return(as.numeric(fallback))
  }
  numeric_value <- suppressWarnings(as.numeric(value))
  if (!is.finite(numeric_value)) as.numeric(fallback) else numeric_value
}

candidate_palette <- function(payload) {
  render_context <- payload$render_context %||% list()
  style_roles <- render_context$style_roles %||% list()
  list(
    primary = candidate_non_empty(style_roles$model_curve, "#245A6B"),
    secondary = candidate_non_empty(style_roles$comparator_curve, "#B89A6D"),
    reference = candidate_non_empty(style_roles$reference_line, "#6B7280"),
    accent = "#8C4A5E",
    light = "#E7EEF2"
  )
}

candidate_theme <- function() {
  theme_publication() +
    theme(
      strip.background = element_rect(fill = "#e8eef2", colour = NA),
      strip.text = element_text(face = "bold", colour = "#13293d"),
      plot.margin = margin(10, 12, 10, 12)
    )
}

candidate_curve_df <- function(payload, series_fields = c("series", "decision_series", "calibration_series")) {
  series <- candidate_items(payload, series_fields)
  if (length(series) < 1) {
    panels <- candidate_items(payload, c("panels"))
    series <- unlist(lapply(panels, function(panel) candidate_items(panel, series_fields)), recursive = FALSE)
  }
  if (length(series) < 1) {
    series <- list(list(label = "Candidate", x = c(0, 0.5, 1), y = c(0, 0.6, 1)))
  }
  frames <- lapply(seq_along(series), function(index) {
    item <- series[[index]]
    x <- unlist(item$x %|||% c(0, 0.5, 1))
    y <- unlist(item$y %|||% c(0, 0.6, 1))
    if (length(x) != length(y)) {
      count <- min(length(x), length(y))
      x <- x[seq_len(count)]
      y <- y[seq_len(count)]
    }
    data.frame(
      panel = candidate_non_empty(item$panel_label %||% item$panel_id, "A"),
      label = candidate_non_empty(item$label, sprintf("Series %d", index)),
      x = as.numeric(x),
      y = as.numeric(y),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, frames)
}

candidate_plot_curve <- function(payload) {
  curve_df <- candidate_curve_df(payload)
  palette <- candidate_palette(payload)
  ggplot(curve_df, aes(x = x, y = y, colour = label)) +
    geom_line(linewidth = 0.9) +
    geom_abline(slope = 1, intercept = 0, colour = palette$reference, linewidth = 0.5, linetype = "dashed") +
    facet_wrap(~panel, scales = "free_y") +
    scale_color_lancet() +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate curve"),
      x = candidate_non_empty(payload$x_label, "Threshold / horizon"),
      y = candidate_non_empty(payload$y_label, "Metric")
    ) +
    candidate_theme()
}

candidate_bar_df <- function(payload) {
  bars <- candidate_items(
    payload,
    c("bars", "left_bars", "right_bars", "risk_group_summaries", "summary_cards", "threshold_summaries")
  )
  if (length(bars) < 1 && !is.null(payload$panels)) {
    bars <- unlist(lapply(payload$panels, function(panel) candidate_items(panel, c("bars", "rows"))), recursive = FALSE)
  }
  if (length(bars) < 1) {
    bars <- list(
      list(label = "Low", value = 0.25),
      list(label = "Middle", value = 0.50),
      list(label = "High", value = 0.75)
    )
  }
  frames <- lapply(seq_along(bars), function(index) {
    item <- bars[[index]]
    label <- candidate_non_empty(
      item$label %||% item$group_label %||% item$feature %||% item$metric_label %||% item$title,
      sprintf("Item %d", index)
    )
    value <- candidate_numeric(
      item$value %||% item$mean_predicted_risk_5y %||% item$observed_km_risk_5y %||% item$events_5y %||% item$support_n,
      index
    )
    data.frame(label = label, value = value, stringsAsFactors = FALSE)
  })
  bar_df <- do.call(rbind, frames)
  bar_df$label <- factor(bar_df$label, levels = bar_df$label)
  bar_df
}

candidate_plot_bars <- function(payload) {
  bar_df <- candidate_bar_df(payload)
  palette <- candidate_palette(payload)
  ggplot(bar_df, aes(x = label, y = value)) +
    geom_col(fill = palette$primary, width = 0.62) +
    geom_text(aes(label = sprintf("%.2f", value)), vjust = -0.35, size = 3.0, colour = "#13293d") +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate bar summary"),
      x = candidate_non_empty(payload$x_label, ""),
      y = candidate_non_empty(payload$y_label, "Value")
    ) +
    candidate_theme() +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
}

candidate_effect_df <- function(payload) {
  rows <- candidate_items(
    payload,
    c("rows", "effect_rows", "overview_rows", "subgroup_rows", "slice_estimates", "coefficient_rows", "modifiers")
  )
  if (length(rows) < 1 && !is.null(payload$panels)) {
    rows <- unlist(lapply(payload$panels, function(panel) candidate_items(panel, c("rows", "effect_rows"))), recursive = FALSE)
  }
  if (length(rows) < 1) {
    rows <- list(
      list(label = "Overall", estimate = 1.05, lower = 0.88, upper = 1.24),
      list(label = "Subgroup A", estimate = 0.92, lower = 0.74, upper = 1.10)
    )
  }
  frames <- lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    estimate <- candidate_numeric(item$estimate %||% item$effect_estimate %||% item$hazard_ratio %||% item$value, 1)
    lower <- candidate_numeric(item$lower %||% item$ci_lower, estimate - 0.12)
    upper <- candidate_numeric(item$upper %||% item$ci_upper, estimate + 0.12)
    data.frame(
      label = candidate_non_empty(item$label %||% item$term %||% item$subgroup_label, sprintf("Row %d", index)),
      estimate = estimate,
      lower = min(lower, estimate, upper),
      upper = max(lower, estimate, upper),
      stringsAsFactors = FALSE
    )
  })
  effect_df <- do.call(rbind, frames)
  effect_df$label <- factor(effect_df$label, levels = rev(effect_df$label))
  effect_df
}

candidate_plot_effect <- function(payload) {
  effect_df <- candidate_effect_df(payload)
  palette <- candidate_palette(payload)
  ggplot(effect_df, aes(y = label, x = estimate)) +
    geom_vline(xintercept = 1, colour = palette$reference, linewidth = 0.6, linetype = "dashed") +
    geom_segment(aes(x = lower, xend = upper, y = label, yend = label), linewidth = 0.8, colour = palette$primary) +
    geom_point(size = 2.7, colour = palette$primary) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate effect estimates"),
      x = candidate_non_empty(payload$x_label, "Effect estimate"),
      y = ""
    ) +
    candidate_theme()
}

candidate_matrix_df <- function(payload) {
  cells <- candidate_items(payload, c("cells", "support_cells", "annotation_tracks", "layer_supports"))
  if (length(cells) < 1) {
    cells <- list(
      list(x = "A", y = "Program 1", value = 0.65),
      list(x = "B", y = "Program 1", value = 0.22),
      list(x = "A", y = "Program 2", value = -0.15),
      list(x = "B", y = "Program 2", value = 0.48)
    )
  }
  frames <- lapply(seq_along(cells), function(index) {
    item <- cells[[index]]
    data.frame(
      x = candidate_non_empty(item$x %||% item$sample_id %||% item$celltype %||% item$layer_label, sprintf("X%d", index)),
      y = candidate_non_empty(item$y %||% item$gene %||% item$marker %||% item$program_label, sprintf("Y%d", index)),
      value = candidate_numeric(item$value %||% item$score %||% item$support_fraction %||% item$frequency, 0),
      stringsAsFactors = FALSE
    )
  })
  matrix_df <- do.call(rbind, frames)
  matrix_df$x <- factor(matrix_df$x, levels = unique(matrix_df$x))
  matrix_df$y <- factor(matrix_df$y, levels = rev(unique(matrix_df$y)))
  matrix_df
}

candidate_plot_matrix <- function(payload) {
  matrix_df <- candidate_matrix_df(payload)
  ggplot(matrix_df, aes(x = x, y = y, fill = value)) +
    geom_tile(colour = "white", linewidth = 0.45) +
    geom_text(aes(label = sprintf("%.2f", value)), size = 2.8, colour = "#13293d") +
    scale_fill_gradient2(low = "#2166ac", mid = "white", high = "#b2182b", midpoint = 0) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate matrix"),
      x = candidate_non_empty(payload$x_label %||% payload$heatmap_x_label, ""),
      y = candidate_non_empty(payload$y_label %||% payload$heatmap_y_label, "")
    ) +
    candidate_theme() +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
}

candidate_dot_df <- function(payload) {
  points <- candidate_items(payload, c("points", "programs"))
  if (length(points) < 1) {
    points <- list(
      list(x = "A", y = "Feature 1", value = 0.6, size = 20),
      list(x = "B", y = "Feature 2", value = 0.3, size = 10)
    )
  }
  frames <- lapply(seq_along(points), function(index) {
    item <- points[[index]]
    data.frame(
      x = candidate_non_empty(item$x %||% item$panel_id %||% item$pathway_label %||% item$cohort_label, sprintf("X%d", index)),
      y = candidate_non_empty(item$y %||% item$marker_label %||% item$feature_label %||% item$program_label, sprintf("Y%d", index)),
      value = candidate_numeric(item$value %||% item$effect_value %||% item$mean_abs_shap %||% item$score, 0),
      size = abs(candidate_numeric(item$size %||% item$support_n %||% item$count %||% item$feature_value, 8)) + 1,
      stringsAsFactors = FALSE
    )
  })
  dot_df <- do.call(rbind, frames)
  dot_df$x <- factor(dot_df$x, levels = unique(dot_df$x))
  dot_df$y <- factor(dot_df$y, levels = rev(unique(dot_df$y)))
  dot_df
}

candidate_plot_dot <- function(payload) {
  dot_df <- candidate_dot_df(payload)
  ggplot(dot_df, aes(x = x, y = y, colour = value, size = size)) +
    geom_point(alpha = 0.88) +
    scale_color_gradient2(low = "#2166ac", mid = "white", high = "#b2182b", midpoint = 0) +
    scale_size_continuous(range = c(2.2, 8.5)) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate dot plot"),
      x = candidate_non_empty(payload$x_label, ""),
      y = candidate_non_empty(payload$y_label, "")
    ) +
    candidate_theme() +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
}

candidate_volcano_df <- function(payload) {
  points <- candidate_items(payload, c("points"))
  if (length(points) < 1) {
    points <- list(
      list(feature_label = "A", effect_value = -1.2, significance_value = 2.8, regulation_class = "downregulated"),
      list(feature_label = "B", effect_value = 1.4, significance_value = 3.2, regulation_class = "upregulated")
    )
  }
  frames <- lapply(seq_along(points), function(index) {
    item <- points[[index]]
    data.frame(
      panel = candidate_non_empty(item$panel_id, "A"),
      feature = candidate_non_empty(item$feature_label %||% item$label_text, sprintf("Feature %d", index)),
      effect = candidate_numeric(item$effect_value %||% item$x, 0),
      significance = candidate_numeric(item$significance_value %||% item$y, 0),
      class = candidate_non_empty(item$regulation_class, "background"),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, frames)
}

candidate_plot_volcano <- function(payload) {
  volcano_df <- candidate_volcano_df(payload)
  ggplot(volcano_df, aes(x = effect, y = significance, colour = class)) +
    geom_point(size = 2.7, alpha = 0.88) +
    geom_vline(xintercept = c(-abs(candidate_numeric(payload$effect_threshold, 1)), abs(candidate_numeric(payload$effect_threshold, 1))), linetype = "dashed", linewidth = 0.5) +
    geom_hline(yintercept = candidate_numeric(payload$significance_threshold, 1.3), linetype = "dashed", linewidth = 0.5) +
    facet_wrap(~panel) +
    scale_color_manual(values = c(upregulated = "#b2182b", downregulated = "#2166ac", background = "#9ca3af")) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate volcano"),
      x = candidate_non_empty(payload$x_label, "Effect"),
      y = candidate_non_empty(payload$y_label, "Significance")
    ) +
    candidate_theme()
}

candidate_shap_rows <- function(payload) {
  rows <- candidate_items(payload, c("rows", "bars"))
  if (length(rows) < 1 && !is.null(payload$panels)) {
    rows <- unlist(lapply(payload$panels, function(panel) candidate_items(panel, c("rows", "bars"))), recursive = FALSE)
  }
  if (length(rows) < 1) {
    rows <- list(
      list(feature = "Age", value = 0.24, points = list(list(shap_value = -0.12, feature_value = 0.3), list(shap_value = 0.25, feature_value = 0.8))),
      list(feature = "Ki-67", value = 0.18, points = list(list(shap_value = -0.08, feature_value = 0.4), list(shap_value = 0.19, feature_value = 0.7)))
    )
  }
  rows
}

candidate_plot_shap <- function(payload, mode = "beeswarm") {
  rows <- candidate_shap_rows(payload)
  if (identical(mode, "bar")) {
    bar_payload <- list(
      bars = lapply(rows, function(row) list(label = row$feature %||% row$label, value = row$value %||% row$mean_abs_shap)),
      title = payload$title,
      x_label = payload$x_label,
      y_label = payload$y_label,
      render_context = payload$render_context
    )
    return(candidate_plot_bars(bar_payload) + coord_flip())
  }
  frames <- lapply(seq_along(rows), function(row_index) {
    row <- rows[[row_index]]
    points <- row$points %||% list(list(shap_value = row$value %||% row$mean_abs_shap %||% 0, feature_value = 0.5))
    do.call(rbind, lapply(seq_along(points), function(point_index) {
      point <- points[[point_index]]
      data.frame(
        feature = candidate_non_empty(row$feature %||% row$label, sprintf("Feature %d", row_index)),
        shap_value = candidate_numeric(point$shap_value %||% point$value, 0),
        feature_value = candidate_numeric(point$feature_value, point_index),
        stringsAsFactors = FALSE
      )
    }))
  })
  shap_df <- do.call(rbind, frames)
  shap_df$feature <- factor(shap_df$feature, levels = rev(unique(shap_df$feature)))
  ggplot(shap_df, aes(x = shap_value, y = feature, colour = feature_value)) +
    geom_vline(xintercept = 0, colour = "#6b7280", linewidth = 0.6, linetype = "dashed") +
    geom_point(size = 2.5, alpha = 0.9, position = position_jitter(height = 0.12, width = 0)) +
    scale_color_gradient2(low = "#2166ac", mid = "white", high = "#b2182b", midpoint = median(shap_df$feature_value)) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate SHAP summary"),
      x = candidate_non_empty(payload$x_label, "SHAP value"),
      y = ""
    ) +
    candidate_theme()
}

build_candidate_evidence_plot <- function(template_id, payload) {
  switch(
    template_id,
    binary_calibration_decision_curve_panel = candidate_plot_curve(payload),
    time_dependent_roc_comparison_panel = candidate_plot_curve(payload),
    time_to_event_decision_curve = candidate_plot_curve(payload),
    time_to_event_discrimination_calibration_panel = candidate_plot_curve(payload),
    time_to_event_landmark_performance_panel = candidate_plot_dot(payload),
    time_to_event_multihorizon_calibration_panel = candidate_plot_curve(payload),
    time_to_event_stratified_cumulative_incidence_panel = candidate_plot_curve(payload),
    time_to_event_risk_group_summary = candidate_plot_bars(payload),
    time_to_event_threshold_governance_panel = candidate_plot_dot(payload),
    risk_layering_monotonic_bars = candidate_plot_bars(payload),
    compact_effect_estimate_panel = candidate_plot_effect(payload),
    broader_heterogeneity_summary_panel = candidate_plot_effect(payload),
    interaction_effect_summary_panel = candidate_plot_effect(payload),
    generalizability_subgroup_composite_panel = candidate_plot_effect(payload),
    coefficient_path_panel = candidate_plot_dot(payload),
    celltype_marker_dotplot_panel = candidate_plot_dot(payload),
    pathway_enrichment_dotplot_panel = candidate_plot_dot(payload),
    genomic_program_governance_summary_panel = candidate_plot_dot(payload),
    celltype_signature_heatmap = candidate_plot_matrix(payload),
    cnv_recurrence_summary_panel = candidate_plot_matrix(payload),
    genomic_alteration_landscape_panel = candidate_plot_matrix(payload),
    genomic_alteration_consequence_panel = candidate_plot_matrix(payload),
    genomic_alteration_multiomic_consequence_panel = candidate_plot_matrix(payload),
    genomic_alteration_pathway_integrated_composite_panel = candidate_plot_matrix(payload),
    oncoplot_mutation_landscape_panel = candidate_plot_matrix(payload),
    omics_volcano_panel = candidate_plot_volcano(payload),
    shap_bar_importance = candidate_plot_shap(payload, mode = "bar"),
    shap_summary_beeswarm = candidate_plot_shap(payload, mode = "beeswarm"),
    shap_dependence_panel = candidate_plot_dot(payload),
    shap_force_like_summary_panel = candidate_plot_effect(payload),
    shap_multicohort_importance_panel = candidate_plot_shap(payload, mode = "bar"),
    shap_waterfall_local_explanation_panel = candidate_plot_effect(payload),
    model_complexity_audit_panel = candidate_plot_dot(payload),
    stop(sprintf("unsupported R candidate evidence template `%s`", template_id))
  )
}

build_candidate_metrics <- function(template_id, display_payload, panel_box) {
  renderer_role <- if (identical(Sys.getenv("MAS_DISPLAY_RENDERER_CANDIDATE_ONLY", unset = ""), "1")) {
    "comparison"
  } else {
    "default"
  }
  renderer_id <- if (identical(renderer_role, "comparison")) {
    "r_ggplot2_comparison_subprocess_v1"
  } else {
    "r_ggplot2_promoted_subprocess_v1"
  }
  list(
    renderer = renderer_id,
    renderer_family = "r_ggplot2",
    renderer_role = renderer_role,
    template_id = template_id,
    data_fields = sort(names(display_payload)),
    panel_box_present = !is.null(panel_box)
  )
}
