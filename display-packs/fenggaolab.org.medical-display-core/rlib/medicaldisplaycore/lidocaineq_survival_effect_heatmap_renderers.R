# LidocaineQ/Figure_Template survival, effect-estimate, and matrix baselines.

lidocaine_survival_dataframe <- function(groups_payload, value_name = "survival") {
  if (!is.list(groups_payload) || length(groups_payload) < 1) {
    stop("groups must contain at least one time-to-event series")
  }
  do.call(rbind, lapply(seq_along(groups_payload), function(index) {
    item <- groups_payload[[index]]
    times <- as_numeric_vector(item$times, sprintf("groups[%d].times", index))
    values <- as_numeric_vector(item$values, sprintf("groups[%d].values", index))
    if (length(times) != length(values)) {
      stop(sprintf("groups[%d].times and groups[%d].values must have the same length", index, index))
    }
    data.frame(
      time = times,
      value = values,
      group = lidocaine_non_empty(item$label, sprintf("Group %d", index)),
      stringsAsFactors = FALSE
    )
  }))
}

lidocaine_risk_table_dataframe <- function(display_payload, times) {
  risk_table <- display_payload$risk_table
  if (!is.list(risk_table) || length(risk_table) < 1) {
    return(NULL)
  }
  risk_df <- do.call(rbind, lapply(seq_along(risk_table), function(index) {
    row <- risk_table[[index]]
    row_times <- as_numeric_vector(row$times, sprintf("risk_table[%d].times", index))
    counts <- row$at_risk %||% row$counts
    if (!is.list(counts) || length(counts) != length(row_times)) {
      stop(sprintf("risk_table[%d].at_risk must match times length", index))
    }
    data.frame(
      time = row_times,
      n_risk = vapply(counts, function(value) lidocaine_numeric(value, NA), numeric(1)),
      group = lidocaine_non_empty(row$label %||% row$group_label, sprintf("Group %d", index)),
      stringsAsFactors = FALSE
    )
  }))
  risk_df <- risk_df[risk_df$time %in% times, , drop = FALSE]
  risk_df$hjust <- ifelse(risk_df$time <= min(times), 0, ifelse(risk_df$time >= max(times), 1, 0.5))
  risk_df
}

plot_lidocaine_kaplan_meier <- function(display_payload) {
  suppressPackageStartupMessages({library(patchwork)})
  curve_df <- lidocaine_survival_dataframe(display_payload$groups)
  group_levels <- unique(curve_df$group)
  curve_df$group <- factor(curve_df$group, levels = group_levels)
  max_time <- max(curve_df$time, na.rm = TRUE)
  if (!is.finite(max_time) || max_time <= 0) {
    stop("survival times must include a positive maximum")
  }
  times <- sort(unique(curve_df$time))
  if (length(times) > 6) {
    times <- pretty(range(curve_df$time), n = 5)
    times <- times[times >= 0 & times <= max_time]
  }
  risk_df <- lidocaine_risk_table_dataframe(display_payload, times)
  palette_values <- lidocaine_palette(display_payload, group_levels)
  p_curve <- ggplot(curve_df, aes(time, value, colour = group)) +
    geom_step(linewidth = 0.75, direction = "hv") +
    geom_point(size = 1.25) +
    scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, group_levels)) +
    scale_x_continuous(breaks = times, limits = c(0, max_time), expand = c(0, 0)) +
    scale_y_continuous(limits = c(max(0, min(curve_df$value, na.rm = TRUE) - 0.08), 1.01), expand = c(0, 0)) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Kaplan-Meier curve with risk table"),
      subtitle = lidocaine_curve_subtitle(display_payload, "No. at risk"),
      x = NULL,
      y = lidocaine_non_empty(display_payload$y_label, "Survival probability")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(
      aspect.ratio = 0.78,
      axis.text.x = element_blank(),
      axis.ticks.x = element_blank(),
      axis.title.x = element_blank(),
      plot.margin = margin(1, 2, 0, 2)
    )
  annotation <- lidocaine_non_empty(display_payload$annotation)
  if (nzchar(annotation)) {
    p_curve <- p_curve + annotate(
      "text",
      x = max_time,
      y = min(curve_df$value, na.rm = TRUE) + 0.06,
      hjust = 1,
      label = annotation,
      colour = style_text_color(display_payload),
      size = style_numeric(style_typography(display_payload), "tick_size", 8.0) * 0.35
    )
  }
  if (is.null(risk_df) || nrow(risk_df) < 1) {
    return(p_curve + labs(x = lidocaine_non_empty(display_payload$x_label, "Time (months)")))
  }
  risk_df$group <- factor(risk_df$group, levels = group_levels)
  p_risk <- ggplot(risk_df, aes(time, group)) +
    geom_text(aes(label = n_risk, colour = group, hjust = hjust), size = 2.55, fontface = "bold") +
    scale_colour_manual(values = palette_values) +
    scale_x_continuous(breaks = times, limits = c(0, max_time), expand = expansion(mult = c(0, 0.02))) +
    labs(x = lidocaine_non_empty(display_payload$x_label, "Time (months)"), y = lidocaine_non_empty(display_payload$risk_table_title, "No. at risk")) +
    lidocaine_publication_theme(display_payload) +
    theme(
      legend.position = "none",
      panel.grid.major.y = element_blank(),
      panel.grid.minor = element_blank(),
      axis.title.y = element_text(size = 8, angle = 0, vjust = 0.5, margin = margin(r = 14)),
      axis.text.y = element_text(face = "bold", colour = style_text_color(display_payload), margin = margin(r = 8)),
      axis.ticks.y = element_blank(),
      plot.title = element_blank(),
      plot.subtitle = element_blank(),
      plot.margin = margin(0, 2, 1, 2)
    )
  p_curve / patchwork::plot_spacer() / p_risk + patchwork::plot_layout(heights = c(0.60, 0.10, 0.30))
}

plot_lidocaine_cumulative_incidence <- function(display_payload) {
  curve_df <- lidocaine_survival_dataframe(display_payload$groups, value_name = "incidence")
  group_levels <- unique(curve_df$group)
  palette_values <- lidocaine_palette(display_payload, group_levels)
  max_time <- max(curve_df$time, na.rm = TRUE)
  ggplot(curve_df, aes(time, value, colour = group)) +
    geom_step(linewidth = 0.90, direction = "hv") +
    scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, group_levels)) +
    scale_x_continuous(breaks = pretty(c(0, max_time), n = 5), limits = c(0, max_time), expand = c(0, 0)) +
    scale_y_continuous(limits = c(0, min(1, max(curve_df$value, na.rm = TRUE) * 1.15)), labels = function(x) paste0(round(x * 100), "%"), expand = c(0, 0)) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Cumulative incidence curve"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Grouped time-to-event incidence"),
      x = lidocaine_non_empty(display_payload$x_label, "Time, months"),
      y = lidocaine_non_empty(display_payload$y_label, "Cumulative incidence")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1)
}

plot_lidocaine_forest <- function(display_payload) {
  forest_df <- build_forest_dataframe(display_payload$rows)
  forest_df$p_value <- vapply(display_payload$rows, function(row) lidocaine_non_empty(row$p %||% row$p_value %||% row$q_value), character(1))
  reference_value <- lidocaine_numeric(display_payload$reference_value, 1.0)
  x_max <- max(c(forest_df$upper, reference_value), na.rm = TRUE)
  label_x <- x_max * 1.18
  ggplot(forest_df, aes(estimate, label)) +
    geom_vline(xintercept = reference_value, linetype = "dashed", linewidth = 0.55, colour = style_color(display_payload, "reference_line", "muted", "#64748B")) +
    geom_errorbar(aes(xmin = lower, xmax = upper), orientation = "y", width = 0.18, linewidth = 0.75, colour = style_color(display_payload, "model_curve", "primary", "#245A6B")) +
    geom_point(size = 2.4, colour = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A")) +
    geom_text(
      data = forest_df[nzchar(forest_df$p_value), , drop = FALSE],
      aes(label = paste0("P=", p_value), x = label_x),
      hjust = 0,
      size = 3.0,
      colour = style_text_color(display_payload)
    ) +
    scale_x_log10(limits = c(max(0.1, min(forest_df$lower, na.rm = TRUE) * 0.75), label_x * 1.25)) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Forest plot"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Effect estimates with 95% CI"),
      x = lidocaine_non_empty(display_payload$x_label, "Effect estimate (log scale)"),
      y = NULL
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1)
}

plot_lidocaine_heatmap <- function(display_payload) {
  cells_payload <- display_payload$cells
  if (!is.list(cells_payload) || length(cells_payload) < 1) {
    stop("cells must contain at least one matrix entry")
  }
  column_order <- if (is.null(display_payload$column_order)) NULL else extract_label_vector(display_payload$column_order, "column_order")
  row_order <- if (is.null(display_payload$row_order)) NULL else extract_label_vector(display_payload$row_order, "row_order")
  heat_df <- build_heatmap_dataframe(cells_payload, column_order = column_order, row_order = row_order)
  heat_df$text_colour <- heatmap_text_colours(display_payload, heat_df$value)
  ggplot(heat_df, aes(x = x, y = y, fill = value)) +
    geom_tile(colour = "white", linewidth = 0.50) +
    heatmap_fill_scale(display_payload, heat_df$value, name = display_payload$metric_name %||% "Z-score") +
    labs(
      title = lidocaine_non_empty(display_payload$title, "ComplexHeatmap annotated matrix"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Annotated matrix pattern"),
      x = lidocaine_non_empty(display_payload$x_label),
      y = lidocaine_non_empty(display_payload$y_label)
    ) +
    lidocaine_publication_theme(display_payload) +
    theme_publication_colorbar(display_payload) +
    theme(axis.text.x = element_text(angle = 35, hjust = 1), aspect.ratio = 1)
}

plot_lidocaine_confusion_matrix <- function(display_payload) {
  cells_payload <- display_payload$cells
  if (!is.list(cells_payload) || length(cells_payload) < 1) {
    stop("cells must contain at least one matrix entry")
  }
  column_order <- if (is.null(display_payload$column_order)) NULL else extract_label_vector(display_payload$column_order, "column_order")
  row_order <- if (is.null(display_payload$row_order)) NULL else extract_label_vector(display_payload$row_order, "row_order")
  heat_df <- build_heatmap_dataframe(cells_payload, column_order = column_order, row_order = row_order)
  value_is_fraction <- max(abs(heat_df$value), na.rm = TRUE) <= 1.001
  heat_df$label <- if (value_is_fraction) sprintf("%.0f%%", heat_df$value * 100) else sprintf("%.0f", heat_df$value)
  ggplot(heat_df, aes(x = x, y = y, fill = value)) +
    geom_tile(colour = "white", linewidth = 0.80) +
    geom_text(aes(label = label), size = 6, fontface = "bold", colour = style_text_color(display_payload)) +
    scale_fill_gradient(
      low = style_color(display_payload, "heatmap_seq_low", "light", "#EEF4F7"),
      high = style_color(display_payload, "heatmap_seq_high", "primary", "#245A6B"),
      name = lidocaine_non_empty(display_payload$metric_name, if (value_is_fraction) "Proportion" else "N"),
      guide = publication_colorbar_guide(display_payload, title = lidocaine_non_empty(display_payload$metric_name, if (value_is_fraction) "Proportion" else "N"), bar_orientation = "horizontal")
    ) +
    coord_equal() +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Binary confusion matrix"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Fixed-threshold classification errors"),
      x = lidocaine_non_empty(display_payload$x_label, "Predicted label"),
      y = lidocaine_non_empty(display_payload$y_label, "True label")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme_publication_colorbar(display_payload)
}
