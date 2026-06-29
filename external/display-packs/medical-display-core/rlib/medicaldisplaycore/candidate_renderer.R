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

candidate_panel_title <- function(payload, panel_id, fallback = "A", order_field = "panel_order") {
  panel_id <- trimws(as.character(panel_id %||% ""))
  panels <- payload[[order_field]] %|||% list()
  if (is.list(panels) && length(panels) > 0) {
    for (panel in panels) {
      current_id <- trimws(as.character(panel$panel_id %||% ""))
      if (nzchar(panel_id) && identical(current_id, panel_id)) {
        return(candidate_non_empty(panel$panel_title %||% panel$title %||% panel$panel_label, fallback))
      }
    }
  }
  candidate_non_empty(panel_id, fallback)
}

candidate_numeric <- function(value, fallback = 0) {
  if (is.null(value)) {
    return(as.numeric(fallback))
  }
  if (is.list(value)) {
    value <- unlist(value, recursive = TRUE, use.names = FALSE)
    if (length(value) < 1) {
      return(as.numeric(fallback))
    }
    value <- value[[1]]
  }
  numeric_value <- suppressWarnings(as.numeric(value))
  if (!is.finite(numeric_value)) as.numeric(fallback) else numeric_value
}

candidate_palette <- function(payload) {
  list(
    primary = style_color(payload, "model_curve", "primary", "#245A6B"),
    secondary = style_color(payload, "comparator_curve", "secondary", "#B89A6D"),
    reference = style_color(payload, "reference_line", "neutral", "#6B7280"),
    accent = style_color(payload, palette_key = "audit", fallback = "#8C4A5E"),
    light = style_color(payload, "highlight_band", "light", "#E7EEF2"),
    text = style_text_color(payload),
    grid = style_grid_color(payload),
    heatmap_low = style_color(payload, "heatmap_low", "heatmap_low", "#2166AC"),
    heatmap_mid = style_color(payload, "heatmap_mid", "heatmap_mid", "#FFFFFF"),
    heatmap_high = style_color(payload, "heatmap_high", "heatmap_high", "#B2182B"),
    volcano_up = style_color(payload, "volcano_up", "volcano_up", "#B2182B"),
    volcano_down = style_color(payload, "volcano_down", "volcano_down", "#2166AC"),
    volcano_background = style_color(payload, "volcano_background", "volcano_background", "#9CA3AF")
  )
}

candidate_theme <- function(payload) {
  palette <- candidate_palette(payload)
  theme_publication(payload) +
    theme(
      strip.background = element_rect(fill = palette$light, colour = NA),
      strip.text = element_text(face = "bold", colour = palette$text),
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
      panel = candidate_panel_title(payload, item$panel_id, candidate_non_empty(item$panel_label, "A")),
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
    geom_line(linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.2) * 0.42) +
    geom_abline(slope = 1, intercept = 0, colour = palette$reference, linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.5, linetype = "dashed") +
    facet_wrap(~panel, scales = "free_y") +
    scale_color_manual(
      values = style_series_palette(payload, unique(curve_df$label)),
      guide = publication_legend_guides(payload, curve_df$label)
    ) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate curve"),
      x = candidate_non_empty(payload$x_label, "Threshold / horizon"),
      y = candidate_non_empty(payload$y_label, "Metric")
    ) +
    candidate_theme(payload)
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
    geom_text(aes(label = sprintf("%.2f", value)), vjust = -0.35, size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.30, colour = palette$text) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate bar summary"),
      x = candidate_non_empty(payload$x_label, ""),
      y = candidate_non_empty(payload$y_label, "Value")
    ) +
    candidate_theme(payload) +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
}

candidate_plot_time_to_event_discrimination_calibration <- function(payload) {
  discrimination <- candidate_items(payload, c("discrimination_points"))
  if (length(discrimination) < 1) {
    discrimination <- list(list(label = "Model", c_index = 0.78))
  }
  discrim_df <- do.call(rbind, lapply(seq_along(discrimination), function(index) {
    item <- discrimination[[index]]
    data.frame(
      panel = candidate_non_empty(payload$panel_a_title, "Discrimination"),
      label = candidate_non_empty(item$label, sprintf("Model %d", index)),
      value = candidate_numeric(item$c_index, 0.75),
      stringsAsFactors = FALSE
    )
  }))
  calibration <- candidate_items(payload, c("calibration_summary"))
  if (length(calibration) < 1) {
    calibration <- list(list(group_label = "Low", predicted_risk_5y = 0.08, observed_risk_5y = 0.07))
  }
  calib_df <- do.call(rbind, lapply(seq_along(calibration), function(index) {
    item <- calibration[[index]]
    data.frame(
      panel = candidate_non_empty(payload$panel_b_title, "Calibration"),
      label = candidate_non_empty(item$group_label, sprintf("Group %d", index)),
      predicted = candidate_numeric(item$predicted_risk_5y, 0.05 * index),
      observed = candidate_numeric(item$observed_risk_5y, 0.05 * index),
      stringsAsFactors = FALSE
    )
  }))
  palette <- candidate_palette(payload)
  discrim_plot <- ggplot(discrim_df, aes(x = label, y = value)) +
    geom_col(fill = palette$primary, width = 0.62) +
    coord_cartesian(ylim = c(0, 1)) +
    labs(
      title = candidate_non_empty(payload$panel_a_title, "Discrimination"),
      x = candidate_non_empty(payload$discrimination_x_label, ""),
      y = "C-index"
    ) +
    candidate_theme(payload) +
    theme(axis.text.x = element_text(angle = 20, hjust = 1))
  calib_plot <- ggplot(calib_df, aes(x = predicted, y = observed, label = label)) +
    geom_abline(slope = 1, intercept = 0, colour = palette$reference, linetype = "dashed", linewidth = 0.45) +
    geom_point(colour = palette$secondary, size = 2.4) +
    geom_text(vjust = -0.6, size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.26, colour = palette$text) +
    coord_cartesian(xlim = c(0, 1), ylim = c(0, 1)) +
    labs(
      title = candidate_non_empty(payload$panel_b_title, "Calibration"),
      x = candidate_non_empty(payload$calibration_x_label, "Predicted risk"),
      y = candidate_non_empty(payload$calibration_y_label, "Observed risk")
    ) +
    candidate_theme(payload)
  patchwork::wrap_plots(list(discrim_plot, calib_plot), ncol = 2)
}

candidate_plot_time_to_event_risk_group_summary <- function(payload) {
  summaries <- candidate_items(payload, c("risk_group_summaries"))
  if (length(summaries) < 1) {
    summaries <- list(
      list(label = "Low risk", sample_size = 100, events_5y = 5, mean_predicted_risk_5y = 0.06, observed_km_risk_5y = 0.05),
      list(label = "High risk", sample_size = 80, events_5y = 22, mean_predicted_risk_5y = 0.28, observed_km_risk_5y = 0.31)
    )
  }
  risk_df <- do.call(rbind, lapply(seq_along(summaries), function(index) {
    item <- summaries[[index]]
    data.frame(
      label = candidate_non_empty(item$label, sprintf("Risk %d", index)),
      predicted = candidate_numeric(item$mean_predicted_risk_5y, 0.05 * index),
      observed = candidate_numeric(item$observed_km_risk_5y, 0.05 * index),
      events = candidate_numeric(item$events_5y, index),
      stringsAsFactors = FALSE
    )
  }))
  risk_df$label <- factor(risk_df$label, levels = risk_df$label)
  palette <- candidate_palette(payload)
  risk_plot <- ggplot(risk_df, aes(x = label)) +
    geom_col(aes(y = predicted), fill = palette$primary, width = 0.60, alpha = 0.84) +
    geom_point(aes(y = observed), colour = palette$secondary, size = 2.4) +
    coord_cartesian(ylim = c(0, max(1, max(c(risk_df$predicted, risk_df$observed), na.rm = TRUE) * 1.15))) +
    labs(
      title = candidate_non_empty(payload$panel_a_title, "Predicted and observed risk"),
      x = candidate_non_empty(payload$x_label, ""),
      y = candidate_non_empty(payload$y_label, "5-year risk")
    ) +
    candidate_theme(payload) +
    theme(axis.text.x = element_text(angle = 20, hjust = 1))
  event_plot <- ggplot(risk_df, aes(x = label, y = events)) +
    geom_col(fill = palette$secondary, width = 0.60, alpha = 0.88) +
    labs(
      title = candidate_non_empty(payload$panel_b_title, "Events by risk group"),
      x = candidate_non_empty(payload$x_label, ""),
      y = candidate_non_empty(payload$event_count_y_label, "Events")
    ) +
    candidate_theme(payload) +
    theme(axis.text.x = element_text(angle = 20, hjust = 1))
  patchwork::wrap_plots(list(risk_plot, event_plot), ncol = 2)
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
    geom_vline(xintercept = 1, colour = palette$reference, linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.6, linetype = "dashed") +
    geom_segment(aes(x = lower, xend = upper, y = label, yend = label), linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.2) * 0.38, colour = palette$primary) +
    geom_point(size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.60, colour = palette$primary) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate effect estimates"),
      x = candidate_non_empty(payload$x_label, "Effect estimate"),
      y = ""
    ) +
    candidate_theme(payload)
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
  palette <- candidate_palette(payload)
  matrix_df$text_colour <- heatmap_text_colours(payload, matrix_df$value)
  ggplot(matrix_df, aes(x = x, y = y, fill = value)) +
    geom_tile(colour = "white", linewidth = 0.45) +
    geom_text(aes(label = sprintf("%.2f", value), colour = text_colour), size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.28, show.legend = FALSE) +
    scale_colour_identity() +
    heatmap_fill_scale(payload, matrix_df$value) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate matrix"),
      x = candidate_non_empty(payload$x_label %||% payload$heatmap_x_label, ""),
      y = candidate_non_empty(payload$y_label %||% payload$heatmap_y_label, "")
    ) +
    candidate_theme(payload) +
    theme_publication_colorbar(payload) +
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
    x_numeric <- item$x_value %||% item$feature_value
    size_value <- abs(candidate_numeric(item$size %||% item$size_value %||% item$support_n %||% item$count, 8))
    data.frame(
      x = if (!is.null(x_numeric)) candidate_numeric(x_numeric, index) else candidate_non_empty(item$x %||% item$celltype_label %||% item$panel_id %||% item$cohort_label, sprintf("X%d", index)),
      y = candidate_non_empty(item$y %||% item$marker_label %||% item$feature_label %||% item$pathway_label %||% item$program_label, sprintf("Y%d", index)),
      value = candidate_numeric(item$value %||% item$effect_value %||% item$mean_abs_shap %||% item$score, 0),
      size = size_value,
      x_is_numeric = !is.null(x_numeric),
      stringsAsFactors = FALSE
    )
  })
  dot_df <- do.call(rbind, frames)
  if (!all(dot_df$x_is_numeric)) {
    dot_df$x <- factor(dot_df$x, levels = unique(dot_df$x))
  } else {
    dot_df$x <- as.numeric(dot_df$x)
  }
  dot_df$y <- factor(dot_df$y, levels = rev(unique(dot_df$y)))
  dot_df
}

candidate_plot_dot <- function(payload) {
  dot_df <- candidate_dot_df(payload)
  ggplot(dot_df, aes(x = x, y = y, colour = value, size = size)) +
    geom_point(alpha = 0.88) +
    heatmap_colour_scale(payload, dot_df$value, name = candidate_non_empty(payload$effect_scale_label, "Effect")) +
    scale_size_continuous(
      range = c(2.2, 8.5),
      name = candidate_non_empty(payload$size_scale_label, "Support"),
      breaks = continuous_scale_breaks(dot_df$size, max_breaks = 3)
    ) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate dot plot"),
      x = candidate_non_empty(payload$x_label, ""),
      y = candidate_non_empty(payload$y_label, "")
    ) +
    candidate_theme(payload) +
    theme_publication_colorbar(payload) +
    guides(size = guide_legend(nrow = 1, byrow = TRUE)) +
    theme(
      axis.text.x = element_text(angle = if (all(dot_df$x_is_numeric)) 0 else 25, hjust = if (all(dot_df$x_is_numeric)) 0.5 else 1),
      legend.box = "vertical",
      legend.spacing.y = unit(3, "pt"),
      panel.grid.major.x = if (all(dot_df$x_is_numeric)) element_line(colour = candidate_palette(payload)$grid, linewidth = 0.18) else element_blank()
    )
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
    explicit_label <- item$label_text
    feature_label <- if (!is.null(explicit_label)) {
      trimws(as.character(explicit_label))
    } else {
      candidate_non_empty(item$feature_label, sprintf("Feature %d", index))
    }
    data.frame(
      panel = candidate_panel_title(payload, item$panel_id, "A"),
      feature = feature_label,
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
  palette <- candidate_palette(payload)
  label_df <- volcano_df[nzchar(volcano_df$feature) & volcano_df$significance >= quantile(volcano_df$significance, 0.70, na.rm = TRUE), , drop = FALSE]
  x_range <- range(volcano_df$effect, na.rm = TRUE)
  x_span <- max(0.1, diff(x_range))
  if (nrow(label_df) > 0) {
    label_df$label_x <- label_df$effect + ifelse(label_df$effect < 0, -x_span * 0.025, x_span * 0.025)
    label_df$label_hjust <- ifelse(label_df$effect < 0, 1, 0)
  }
  ggplot(volcano_df, aes(x = effect, y = significance, colour = class)) +
    geom_point(size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.58, alpha = 0.86) +
    geom_vline(xintercept = c(-abs(candidate_numeric(payload$effect_threshold, 1)), abs(candidate_numeric(payload$effect_threshold, 1))), colour = palette$reference, linetype = "dashed", linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.5) +
    geom_hline(yintercept = candidate_numeric(payload$significance_threshold, 1.3), colour = palette$reference, linetype = "dashed", linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.5) +
    geom_text(
      data = label_df,
      aes(x = label_x, label = feature, hjust = label_hjust),
      show.legend = FALSE,
      size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.30,
      vjust = -0.55,
      colour = palette$text
    ) +
    facet_wrap(~panel) +
    scale_color_manual(
      values = c(upregulated = palette$volcano_up, downregulated = palette$volcano_down, background = palette$volcano_background),
      guide = publication_legend_guides(payload, volcano_df$class)
    ) +
    coord_cartesian(xlim = c(x_range[[1]] - x_span * 0.12, x_range[[2]] + x_span * 0.16), clip = "off") +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate volcano"),
      x = candidate_non_empty(payload$x_label, "Effect"),
      y = candidate_non_empty(payload$y_label, "Significance")
    ) +
    candidate_theme(payload) +
    theme(plot.margin = margin(9, 20, 9, 20))
}

.candidate_renderer_source_file <- NULL
for (.frame_index in rev(seq_len(sys.nframe()))) {
  .frame_file <- sys.frame(.frame_index)$ofile
  if (!is.null(.frame_file) && identical(basename(.frame_file), "candidate_renderer.R")) {
    .candidate_renderer_source_file <- .frame_file
    break
  }
}
.candidate_publication_renderer_path <- if (!is.null(.candidate_renderer_source_file)) {
  file.path(dirname(normalizePath(.candidate_renderer_source_file, mustWork = TRUE)), "candidate_publication_renderers.R")
} else {
  file.path("candidate_publication_renderers.R")
}
source(.candidate_publication_renderer_path, local = environment())
rm(.candidate_renderer_source_file, .candidate_publication_renderer_path, .frame_index, .frame_file)

build_candidate_evidence_plot <- function(template_id, payload) {
  switch(
    template_id,
    time_to_event_discrimination_calibration_panel = candidate_plot_time_to_event_discrimination_calibration(payload),
    time_to_event_decision_curve = candidate_plot_time_to_event_decision_curve(payload),
    time_to_event_multihorizon_calibration_panel = candidate_plot_multihorizon_calibration(payload),
    time_to_event_risk_group_summary = candidate_plot_time_to_event_risk_group_summary(payload),
    risk_layering_monotonic_bars = candidate_plot_risk_layering(payload),
    generalizability_subgroup_composite_panel = candidate_plot_generalizability(payload),
    coefficient_path_panel = candidate_plot_coefficient_path(payload),
    celltype_marker_dotplot_panel = candidate_plot_dot(payload),
    pathway_enrichment_dotplot_panel = candidate_plot_dot(payload),
    cnv_recurrence_summary_panel = candidate_plot_cnv_recurrence(payload),
    genomic_alteration_landscape_panel = candidate_plot_alteration_landscape(payload),
    genomic_alteration_consequence_panel = candidate_plot_genomic_consequence(payload),
    omics_volcano_panel = candidate_plot_volcano(payload),
    shap_summary_beeswarm = candidate_plot_shap(payload, mode = "beeswarm"),
    shap_dependence_panel = candidate_plot_shap_dependence(payload),
    shap_waterfall_local_explanation_panel = candidate_plot_shap_waterfall(payload),
    model_complexity_audit_panel = candidate_plot_model_complexity_audit(payload),
    stop(sprintf("unsupported R candidate evidence template `%s`", template_id))
  )
}

candidate_box <- function(box_id, box_type, x0, y0, x1, y1) {
  list(
    box_id = box_id,
    box_type = box_type,
    x0 = as.numeric(x0),
    y0 = as.numeric(y0),
    x1 = as.numeric(x1),
    y1 = as.numeric(y1)
  )
}

candidate_panel_labels <- function(left_title = "A", right_title = "B") {
  list(
    candidate_box("panel_label_A", "panel_label", 0.10, 0.77, 0.13, 0.81),
    candidate_box("panel_label_B", "panel_label", 0.58, 0.77, 0.61, 0.81),
    candidate_box("panel_left_title", "panel_title", 0.15, 0.86, 0.42, 0.90),
    candidate_box("panel_right_title", "panel_title", 0.63, 0.86, 0.90, 0.90)
  )
}

candidate_two_panel_boxes <- function(left_type, right_type) {
  list(
    candidate_box("panel_left", left_type, 0.08, 0.20, 0.46, 0.82),
    candidate_box("panel_right", right_type, 0.56, 0.20, 0.94, 0.82)
  )
}

candidate_axis_boxes <- function(x_id = "x_axis_title", y_id = "y_axis_title") {
  list(
    candidate_box(x_id, "subplot_x_axis_title", 0.35, 0.09, 0.65, 0.13),
    candidate_box(y_id, "subplot_y_axis_title", 0.01, 0.42, 0.05, 0.62)
  )
}

candidate_risk_bar_boxes <- function(values, panel_box, prefix) {
  count <- max(1, length(values %|||% list()))
  lapply(seq_len(count), function(index) {
    y0 <- panel_box$y0 + 0.06 + (index - 1) * ((panel_box$y1 - panel_box$y0 - 0.16) / count)
    y1 <- y0 + max(0.03, (panel_box$y1 - panel_box$y0 - 0.22) / count)
    candidate_box(
      sprintf("%s_risk_bar_%d", prefix, index),
      "risk_bar",
      panel_box$x0 + 0.06,
      y0,
      panel_box$x1 - 0.04,
      min(panel_box$y1 - 0.04, y1)
    )
  })
}

candidate_risk_bar_values <- function(values) {
  lapply(values %|||% list(), function(item) {
    list(
      label = candidate_non_empty(item$label %||% item$group_label, ""),
      cases = as.integer(candidate_numeric(item$cases %||% item$sample_size %||% item$n, 0)),
      events = as.integer(candidate_numeric(item$events %||% item$events_5y, 0)),
      risk = candidate_numeric(item$risk %||% item$observed_km_risk_5y %||% item$mean_predicted_risk_5y, 0)
    )
  })
}

candidate_metric_marker_boxes <- function(values, panel_box, prefix, markers_per_value = 1) {
  count <- max(1, length(values %|||% list()))
  unlist(lapply(seq_len(count), function(index) {
    y <- panel_box$y0 + index * ((panel_box$y1 - panel_box$y0) / (count + 1))
    lapply(seq_len(markers_per_value), function(marker_index) {
      x <- panel_box$x0 + 0.10 + marker_index * 0.08
      candidate_box(
        sprintf("%s_marker_%d_%d", prefix, index, marker_index),
        "metric_marker",
        x,
        y - 0.012,
        min(panel_box$x1 - 0.02, x + 0.024),
        y + 0.012
      )
    })
  }), recursive = FALSE)
}

candidate_multihorizon_metrics <- function(payload) {
  panels <- payload$panels %|||% list()
  panel_count <- max(1, length(panels))
  list(
    panels = lapply(seq_along(panels), function(index) {
      panel <- panels[[index]]
      panel_label <- candidate_non_empty(panel$panel_label, LETTERS[[index]])
      panel_x0 <- 0.08 + (index - 1) * (0.86 / panel_count)
      panel_x1 <- 0.08 + index * (0.86 / panel_count) - 0.04
      panel_y0 <- 0.20
      panel_y1 <- 0.82
      rows <- panel$calibration_summary %|||% list()
      row_count <- max(1, length(rows))
      list(
        panel_id = candidate_non_empty(panel$panel_id, ""),
        panel_label = panel_label,
        title = candidate_non_empty(panel$title, ""),
        time_horizon_months = as.integer(candidate_numeric(panel$time_horizon_months, 0)),
        calibration_summary = lapply(seq_along(rows), function(row_index) {
          row <- rows[[row_index]]
          y <- panel_y0 + (row_count - row_index + 1) * ((panel_y1 - panel_y0) / (row_count + 1))
          predicted <- candidate_numeric(row$predicted_risk, 0)
          observed <- candidate_numeric(row$observed_risk, predicted)
          x_max <- max(0.35, predicted, observed, 1e-6)
          predicted_x <- panel_x0 + (predicted / x_max) * (panel_x1 - panel_x0) * 0.82 + 0.04
          observed_x <- panel_x0 + (observed / x_max) * (panel_x1 - panel_x0) * 0.82 + 0.04
          c(
            row,
            list(
              predicted_x = max(panel_x0 + 0.02, min(panel_x1 - 0.02, predicted_x)),
              observed_x = max(panel_x0 + 0.02, min(panel_x1 - 0.02, observed_x)),
              y = y
            )
          )
        })
      )
    })
  )
}

candidate_generalizability_layout <- function(display_payload) {
  overview_rows <- display_payload$overview_rows %|||% list()
  subgroup_rows <- display_payload$subgroup_rows %|||% list()
  overview_count <- max(1, length(overview_rows))
  subgroup_count <- max(1, length(subgroup_rows))
  overview_panel <- candidate_box("overview_panel", "panel", 0.12, 0.18, 0.45, 0.80)
  subgroup_panel <- candidate_box("subgroup_panel", "panel", 0.58, 0.18, 0.88, 0.80)
  layout_boxes <- c(
    candidate_panel_labels(),
    list(
      candidate_box("x_axis_title_A", "subplot_x_axis_title", 0.20, 0.10, 0.32, 0.13),
      candidate_box("x_axis_title_B", "subplot_x_axis_title", 0.67, 0.10, 0.78, 0.13)
    )
  )
  overview_metrics <- lapply(seq_along(overview_rows), function(index) {
    row <- overview_rows[[index]]
    y <- overview_panel$y0 + (overview_count - index + 1) * ((overview_panel$y1 - overview_panel$y0) / (overview_count + 1))
    label_id <- sprintf("overview_row_label_%d", index)
    support_id <- sprintf("overview_support_label_%d", index)
    marker_id <- sprintf("overview_metric_marker_%d", index)
    layout_boxes <<- c(
      layout_boxes,
      list(
        candidate_box(label_id, "overview_row_label", 0.03, y - 0.02, 0.11, y + 0.02),
        candidate_box(support_id, "support_label", 0.37, y - 0.02, 0.44, y + 0.02),
        candidate_box(marker_id, "overview_metric_marker", 0.25 + index * 0.025, y - 0.02, 0.26 + index * 0.025, y + 0.02)
      )
    )
    c(
      row,
      list(
        label_box_id = label_id,
        support_label_box_id = support_id,
        metric_marker_box_id = marker_id
      )
    )
  })
  subgroup_metrics <- lapply(seq_along(subgroup_rows), function(index) {
    row <- subgroup_rows[[index]]
    y <- subgroup_panel$y0 + (subgroup_count - index + 1) * ((subgroup_panel$y1 - subgroup_panel$y0) / (subgroup_count + 1))
    label_id <- sprintf("subgroup_row_label_%d", index)
    estimate_id <- sprintf("subgroup_estimate_%d", index)
    ci_id <- sprintf("subgroup_ci_%d", index)
    estimate <- candidate_numeric(row$estimate, 0.5)
    lower <- candidate_numeric(row$lower, estimate - 0.05)
    upper <- candidate_numeric(row$upper, estimate + 0.05)
    x_min <- min(0.0, lower)
    x_max <- max(1.0, upper)
    scale_x <- function(value) {
      subgroup_panel$x0 + 0.04 + (value - x_min) / (x_max - x_min) * (subgroup_panel$x1 - subgroup_panel$x0 - 0.08)
    }
    lower_x <- max(subgroup_panel$x0 + 0.02, min(subgroup_panel$x1 - 0.02, scale_x(lower)))
    upper_x <- max(subgroup_panel$x0 + 0.02, min(subgroup_panel$x1 - 0.02, scale_x(upper)))
    estimate_x <- max(subgroup_panel$x0 + 0.02, min(subgroup_panel$x1 - 0.02, scale_x(estimate)))
    layout_boxes <<- c(
      layout_boxes,
      list(
        candidate_box(label_id, "subgroup_row_label", 0.46, y - 0.02, 0.56, y + 0.02),
        candidate_box(ci_id, "ci_segment", lower_x, y - 0.005, upper_x, y + 0.005),
        candidate_box(estimate_id, "estimate_marker", estimate_x - 0.005, y - 0.02, estimate_x + 0.005, y + 0.02)
      )
    )
    c(
      row,
      list(
        label_box_id = label_id,
        estimate_box_id = estimate_id,
        ci_box_id = ci_id
      )
    )
  })
  list(
    layout_boxes = layout_boxes,
    panel_boxes = list(overview_panel, subgroup_panel),
    guide_boxes = list(candidate_box("reference_line", "reference_line", 0.72, 0.18, 0.72, 0.80)),
    metrics = list(
      metric_family = candidate_non_empty(display_payload$metric_family, ""),
      overview_rows = overview_metrics,
      subgroup_rows = subgroup_metrics
    )
  )
}

candidate_metrics_with_renderer <- function(template_id, display_payload, base_panel_box, metrics) {
  c(build_candidate_metrics(template_id, display_payload, base_panel_box), metrics)
}

build_candidate_layout_override <- function(template_id, display_payload, base_panel_box = NULL, base_guide_box = NULL) {
  if (identical(template_id, "time_to_event_discrimination_calibration_panel")) {
    panels <- candidate_two_panel_boxes("panel", "panel")
    return(list(
      layout_boxes = c(
        candidate_panel_labels(
          candidate_non_empty(display_payload$panel_a_title, "Discrimination"),
          candidate_non_empty(display_payload$panel_b_title, "Calibration")
        ),
        list(
          candidate_box("panel_left_x_axis_title", "subplot_x_axis_title", 0.18, 0.09, 0.40, 0.13),
          candidate_box("panel_left_y_axis_title", "subplot_y_axis_title", 0.01, 0.40, 0.05, 0.62),
          candidate_box("calibration_x_axis_title", "subplot_x_axis_title", 0.62, 0.09, 0.86, 0.13),
          candidate_box("calibration_y_axis_title", "subplot_y_axis_title", 0.50, 0.40, 0.54, 0.62)
        ),
        candidate_metric_marker_boxes(display_payload$discrimination_points, panels[[1]], "discrimination", 1),
        candidate_metric_marker_boxes(display_payload$calibration_summary, panels[[2]], "calibration", 2)
      ),
      panel_boxes = panels,
      guide_boxes = list(candidate_box("legend", "legend", 0.24, 0.06, 0.76, 0.13)),
      metrics = candidate_metrics_with_renderer(
        template_id,
        display_payload,
        base_panel_box,
        list(
          discrimination_points = display_payload$discrimination_points %|||% list(),
          calibration_summary = display_payload$calibration_summary %|||% list(),
          calibration_callout = display_payload$calibration_callout %||% NULL,
          series = list(list(label = "C-index", x = c(0, 1), y = c(0.5, 0.5))),
          reference_line = list(x = c(0, 1), y = c(0.5, 0.5))
        )
      )
    ))
  }
  if (identical(template_id, "time_to_event_decision_curve")) {
    return(list(
      layout_boxes = c(candidate_panel_labels(), candidate_axis_boxes()),
      panel_boxes = candidate_two_panel_boxes("decision_curve_panel", "treated_fraction_panel"),
      guide_boxes = list(candidate_box("legend", "legend", 0.24, 0.06, 0.76, 0.13)),
      metrics = candidate_metrics_with_renderer(
        template_id,
        display_payload,
        base_panel_box,
        list(
          series = display_payload$series %|||% list(),
          reference_line = display_payload$reference_line %|||% list(),
          treated_fraction_series = display_payload$treated_fraction_series %|||% list()
        )
      )
    ))
  }
  if (identical(template_id, "risk_layering_monotonic_bars")) {
    panels <- candidate_two_panel_boxes("panel", "panel")
    return(list(
      layout_boxes = c(
        candidate_panel_labels(),
        list(candidate_box("risk_y_axis_title", "y_axis_title", 0.01, 0.42, 0.05, 0.62)),
        candidate_risk_bar_boxes(display_payload$left_bars, panels[[1]], "predicted"),
        candidate_risk_bar_boxes(display_payload$right_bars, panels[[2]], "observed")
      ),
      panel_boxes = panels,
      guide_boxes = list(),
      metrics = candidate_metrics_with_renderer(
        template_id,
        display_payload,
        base_panel_box,
        list(
          left_bars = candidate_risk_bar_values(display_payload$left_bars),
          right_bars = candidate_risk_bar_values(display_payload$right_bars)
        )
      )
    ))
  }
  if (identical(template_id, "time_to_event_risk_group_summary")) {
    panels <- candidate_two_panel_boxes("panel", "panel")
    return(list(
      layout_boxes = c(
        candidate_panel_labels(
          candidate_non_empty(display_payload$panel_a_title, "Risk gradient"),
          candidate_non_empty(display_payload$panel_b_title, "Event counts")
        ),
        list(
          candidate_box("x_axis_title", "x_axis_title", 0.18, 0.09, 0.40, 0.13),
          candidate_box("y_axis_title", "y_axis_title", 0.01, 0.40, 0.05, 0.62),
          candidate_box("panel_right_x_axis_title", "subplot_x_axis_title", 0.62, 0.09, 0.86, 0.13),
          candidate_box("panel_right_y_axis_title", "subplot_y_axis_title", 0.50, 0.40, 0.54, 0.62)
        ),
        candidate_risk_bar_boxes(display_payload$risk_group_summaries, panels[[1]], "predicted"),
        candidate_risk_bar_boxes(display_payload$risk_group_summaries, panels[[2]], "observed")
      ),
      panel_boxes = panels,
      guide_boxes = list(),
      metrics = candidate_metrics_with_renderer(
        template_id,
        display_payload,
        base_panel_box,
        list(
          risk_group_summaries = display_payload$risk_group_summaries %|||% list()
        )
      )
    ))
  }
  if (identical(template_id, "time_to_event_multihorizon_calibration_panel")) {
    panels <- display_payload$panels %|||% list()
    panel_count <- max(1, length(panels))
    panel_boxes <- lapply(seq_len(panel_count), function(index) {
      left <- 0.08 + (index - 1) * (0.86 / panel_count)
      right <- 0.08 + index * (0.86 / panel_count) - 0.04
      panel <- panels[[index]]
      panel_label <- candidate_non_empty(panel$panel_label, LETTERS[[index]])
      candidate_box(sprintf("panel_%s", panel_label), "calibration_panel", left, 0.20, right, 0.82)
    })
    layout_boxes <- c(
      list(candidate_box("x_axis_title", "subplot_x_axis_title", 0.34, 0.08, 0.58, 0.12)),
      unlist(
        lapply(seq_len(panel_count), function(index) {
          panel <- panels[[index]]
          panel_box <- panel_boxes[[index]]
          panel_label <- candidate_non_empty(panel$panel_label, LETTERS[[index]])
          list(
            candidate_box(sprintf("panel_label_%s", panel_label), "panel_label", panel_box$x0 + 0.02, 0.77, panel_box$x0 + 0.05, 0.81),
            candidate_box(sprintf("panel_title_%s", panel_label), "panel_title", panel_box$x0 + 0.06, 0.86, panel_box$x1 - 0.04, 0.90)
          )
        }),
        recursive = FALSE
      )
    )
    return(list(
      layout_boxes = layout_boxes,
      panel_boxes = panel_boxes,
      guide_boxes = list(candidate_box("legend", "legend", 0.24, 0.06, 0.76, 0.13)),
      metrics = candidate_metrics_with_renderer(
        template_id,
        display_payload,
        base_panel_box,
        candidate_multihorizon_metrics(display_payload)
      )
    ))
  }
  if (identical(template_id, "generalizability_subgroup_composite_panel")) {
    override <- candidate_generalizability_layout(display_payload)
    override$metrics <- candidate_metrics_with_renderer(
      template_id,
      display_payload,
      base_panel_box,
      override$metrics
    )
    return(override)
  }
  NULL
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
