# Student-curated publication renderers adapted from LidocaineQ/Figure_Template.
# These are default lower-bound R/ggplot2 evidence seeds; MAS may still reshape
# them per paper while preserving statistical semantics and source refs.

lidocaine_non_empty <- function(value, fallback = "") {
  normalized <- trimws(as.character(value %||% ""))
  if (nzchar(normalized)) normalized else fallback
}

lidocaine_numeric <- function(value, fallback = 0) {
  numeric_value <- suppressWarnings(as.numeric(value))
  if (is.finite(numeric_value)) numeric_value else as.numeric(fallback)
}

lidocaine_palette <- function(display_payload, labels) {
  style_series_palette(display_payload, unique(as.character(labels)))
}

lidocaine_publication_theme <- function(display_payload) {
  theme_publication(display_payload) +
    theme(
      plot.title = element_text(
        face = "bold",
        colour = style_text_color(display_payload),
        size = style_numeric(style_typography(display_payload), "title_size", 11.5),
        margin = margin(b = 5, unit = "pt")
      ),
      axis.title = element_text(face = "bold"),
      legend.position = "bottom",
      legend.box = "horizontal",
      panel.grid.minor = element_blank()
    )
}

build_distribution_violin_box_dataframe <- function(display_payload) {
  values <- display_payload$values
  if (!is.list(values) || length(values) < 2) {
    stop("values must contain at least two distribution records")
  }
  distribution_df <- do.call(rbind, lapply(seq_along(values), function(index) {
    item <- values[[index]]
    data.frame(
      group = lidocaine_non_empty(item$group, sprintf("Group %d", index)),
      value = lidocaine_numeric(item$value, NA),
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(distribution_df$value))) {
    stop("values.value must be finite")
  }
  group_order <- display_payload$group_order
  if (is.list(group_order) && length(group_order) > 0) {
    levels <- extract_label_vector(group_order, "group_order")
  } else {
    levels <- unique(distribution_df$group)
  }
  distribution_df$group <- factor(distribution_df$group, levels = levels)
  distribution_df
}

plot_distribution_violin_box <- function(display_payload) {
  distribution_df <- build_distribution_violin_box_dataframe(display_payload)
  palette_values <- lidocaine_palette(display_payload, distribution_df$group)
  plot <- ggplot(distribution_df, aes(x = group, y = value, fill = group)) +
    geom_violin(
      width = 0.82,
      trim = FALSE,
      alpha = 0.72,
      colour = "white",
      linewidth = 0.35
    ) +
    geom_boxplot(
      width = 0.22,
      outlier.shape = NA,
      alpha = 0.92,
      colour = style_color(display_payload, "axis_line", "axis", "#13293D"),
      linewidth = 0.38
    ) +
    geom_point(
      position = position_jitter(width = 0.055, height = 0, seed = 12),
      size = style_numeric(style_stroke(display_payload), "marker_size", 3.4) * 0.34,
      alpha = 0.48,
      colour = style_color(display_payload, "series_6", "muted", "#64748B")
    ) +
    scale_fill_manual(values = palette_values, guide = "none") +
    labs(
      title = lidocaine_non_empty(display_payload$title),
      x = lidocaine_non_empty(display_payload$x_label),
      y = lidocaine_non_empty(display_payload$y_label, "Value")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(panel.grid.major.x = element_blank())
  annotation <- lidocaine_non_empty(display_payload$annotation)
  if (nzchar(annotation)) {
    y_top <- max(distribution_df$value, na.rm = TRUE)
    y_span <- diff(range(distribution_df$value, na.rm = TRUE))
    plot <- plot + annotate(
      "text",
      x = mean(seq_along(levels(distribution_df$group))),
      y = y_top + max(y_span * 0.08, 0.08),
      label = annotation,
      size = style_numeric(style_typography(display_payload), "tick_size", 8.0) * 0.35,
      colour = style_text_color(display_payload)
    )
  }
  plot
}

build_composition_stacked_bar_dataframe <- function(display_payload) {
  segments <- display_payload$segments
  if (!is.list(segments) || length(segments) < 1) {
    stop("segments must contain at least one composition segment")
  }
  composition_df <- do.call(rbind, lapply(seq_along(segments), function(index) {
    item <- segments[[index]]
    data.frame(
      group = lidocaine_non_empty(item$group, sprintf("Group %d", index)),
      category = lidocaine_non_empty(item$category, sprintf("Category %d", index)),
      value = lidocaine_numeric(item$value %||% item$proportion %||% item$count, NA),
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(composition_df$value))) {
    stop("segments.value must be finite")
  }
  group_order <- display_payload$group_order
  category_order <- display_payload$category_order
  composition_df$group <- factor(
    composition_df$group,
    levels = if (is.list(group_order) && length(group_order) > 0) extract_label_vector(group_order, "group_order") else unique(composition_df$group)
  )
  composition_df$category <- factor(
    composition_df$category,
    levels = if (is.list(category_order) && length(category_order) > 0) extract_label_vector(category_order, "category_order") else unique(composition_df$category)
  )
  composition_df
}

plot_composition_stacked_bar <- function(display_payload) {
  composition_df <- build_composition_stacked_bar_dataframe(display_payload)
  category_labels <- levels(composition_df$category)
  palette_values <- lidocaine_palette(display_payload, category_labels)
  total_by_group <- stats::aggregate(value ~ group, composition_df, sum)
  percent_scale <- max(total_by_group$value, na.rm = TRUE) <= 1.001
  ggplot(composition_df, aes(x = group, y = value, fill = category)) +
    geom_col(width = 0.68, colour = "white", linewidth = 0.38) +
    scale_fill_manual(
      values = palette_values,
      guide = publication_legend_guides(display_payload, category_labels)
    ) +
    scale_y_continuous(
      labels = if (percent_scale) function(x) paste0(round(x * 100), "%") else waiver(),
      expand = expansion(mult = c(0, 0.045))
    ) +
    labs(
      title = lidocaine_non_empty(display_payload$title),
      x = lidocaine_non_empty(display_payload$x_label),
      y = lidocaine_non_empty(display_payload$y_label, if (percent_scale) "Proportion" else "Count")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(panel.grid.major.x = element_blank())
}

build_correlation_scatter_dataframe <- function(display_payload) {
  points <- display_payload$points
  if (!is.list(points) || length(points) < 3) {
    stop("points must contain at least three observations")
  }
  scatter_df <- do.call(rbind, lapply(seq_along(points), function(index) {
    item <- points[[index]]
    data.frame(
      x = lidocaine_numeric(item$x, NA),
      y = lidocaine_numeric(item$y, NA),
      group = lidocaine_non_empty(item$group, "All"),
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(scatter_df$x)) || any(!is.finite(scatter_df$y))) {
    stop("points.x and points.y must be finite")
  }
  scatter_df
}

plot_correlation_scatter <- function(display_payload) {
  scatter_df <- build_correlation_scatter_dataframe(display_payload)
  palette_values <- lidocaine_palette(display_payload, scatter_df$group)
  plot <- ggplot(scatter_df, aes(x = x, y = y, colour = group)) +
    geom_point(
      size = style_numeric(style_stroke(display_payload), "marker_size", 3.4) * 0.48,
      alpha = 0.78
    ) +
    geom_smooth(
      method = "lm",
      formula = y ~ x,
      se = TRUE,
      linewidth = style_numeric(style_stroke(display_payload), "primary_linewidth", 2.0) * 0.34,
      alpha = 0.12
    ) +
    scale_colour_manual(
      values = palette_values,
      guide = publication_legend_guides(display_payload, scatter_df$group)
    ) +
    labs(
      title = lidocaine_non_empty(display_payload$title),
      x = lidocaine_non_empty(display_payload$x_label, "Feature score"),
      y = lidocaine_non_empty(display_payload$y_label, "Outcome-associated score")
    ) +
    lidocaine_publication_theme(display_payload)
  annotation <- lidocaine_non_empty(display_payload$annotation)
  if (nzchar(annotation)) {
    plot <- plot + annotate(
      "text",
      x = min(scatter_df$x, na.rm = TRUE),
      y = max(scatter_df$y, na.rm = TRUE),
      hjust = 0,
      vjust = 1,
      label = annotation,
      lineheight = 0.95,
      size = style_numeric(style_typography(display_payload), "tick_size", 8.0) * 0.34,
      colour = style_text_color(display_payload)
    )
  }
  plot
}

build_alluvial_transition_dataframe <- function(display_payload) {
  flows <- display_payload$flows
  if (!is.list(flows) || length(flows) < 1) {
    stop("flows must contain at least one transition")
  }
  flow_df <- do.call(rbind, lapply(seq_along(flows), function(index) {
    item <- flows[[index]]
    data.frame(
      source = lidocaine_non_empty(item$source, sprintf("Source %d", index)),
      target = lidocaine_non_empty(item$target, sprintf("Target %d", index)),
      value = lidocaine_numeric(item$value %||% item$n, NA),
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(flow_df$value)) || any(flow_df$value <= 0)) {
    stop("flows.value must contain positive finite values")
  }
  flow_df
}

build_alluvial_segment_dataframe <- function(flow_df, n_steps = 28) {
  source_totals <- stats::aggregate(value ~ source, flow_df, sum)
  source_totals <- source_totals[order(source_totals$source), , drop = FALSE]
  source_totals$start <- c(0, head(cumsum(source_totals$value), -1))
  source_offsets <- setNames(source_totals$start, source_totals$source)
  source_running <- source_offsets

  target_totals <- stats::aggregate(value ~ target, flow_df, sum)
  target_totals <- target_totals[order(target_totals$target), , drop = FALSE]
  target_totals$start <- c(0, head(cumsum(target_totals$value), -1))
  target_offsets <- setNames(target_totals$start, target_totals$target)
  target_running <- target_offsets

  paths <- list()
  for (index in seq_len(nrow(flow_df))) {
    row <- flow_df[index, ]
    source_bottom <- source_running[[row$source]]
    source_top <- source_bottom + row$value
    target_bottom <- target_running[[row$target]]
    target_top <- target_bottom + row$value
    source_running[[row$source]] <- source_top
    target_running[[row$target]] <- target_top
    x <- seq(0, 1, length.out = n_steps)
    smooth <- stats::plogis((x - 0.5) * 7)
    paths[[length(paths) + 1]] <- data.frame(
      flow_id = paste(row$source, row$target, index, sep = "::"),
      source = row$source,
      target = row$target,
      x = c(x, rev(x)),
      y = c(source_bottom + (target_bottom - source_bottom) * smooth, rev(source_top + (target_top - source_top) * smooth)),
      fill_label = row$target,
      stringsAsFactors = FALSE
    )
  }
  list(
    segments = do.call(rbind, paths),
    source_totals = source_totals,
    target_totals = target_totals,
    total = sum(flow_df$value)
  )
}

plot_alluvial_transition <- function(display_payload) {
  flow_df <- build_alluvial_transition_dataframe(display_payload)
  layout <- build_alluvial_segment_dataframe(flow_df)
  segment_df <- layout$segments
  palette_values <- lidocaine_palette(display_payload, segment_df$fill_label)
  source_labels <- data.frame(
    x = 0,
    y = layout$source_totals$start + layout$source_totals$value / 2,
    label = layout$source_totals$source,
    stringsAsFactors = FALSE
  )
  target_labels <- data.frame(
    x = 1,
    y = layout$target_totals$start + layout$target_totals$value / 2,
    label = layout$target_totals$target,
    stringsAsFactors = FALSE
  )
  axis_labels <- data.frame(
    x = c(0, 1),
    y = rep(layout$total * 1.04, 2),
    label = c(
      lidocaine_non_empty(display_payload$source_axis_label, "Baseline state"),
      lidocaine_non_empty(display_payload$target_axis_label, "Follow-up state")
    ),
    stringsAsFactors = FALSE
  )
  ggplot(segment_df, aes(x = x, y = y, group = flow_id, fill = fill_label)) +
    geom_polygon(alpha = 0.82, colour = "white", linewidth = 0.22) +
    geom_rect(
      data = layout$source_totals,
      aes(xmin = -0.055, xmax = 0.055, ymin = start, ymax = start + value),
      inherit.aes = FALSE,
      fill = "white",
      colour = style_color(display_payload, "axis_line", "axis", "#13293D"),
      linewidth = 0.34
    ) +
    geom_rect(
      data = layout$target_totals,
      aes(xmin = 0.945, xmax = 1.055, ymin = start, ymax = start + value),
      inherit.aes = FALSE,
      fill = "white",
      colour = style_color(display_payload, "axis_line", "axis", "#13293D"),
      linewidth = 0.34
    ) +
    geom_text(
      data = rbind(source_labels, target_labels),
      aes(x = x, y = y, label = label),
      inherit.aes = FALSE,
      size = style_numeric(style_typography(display_payload), "tick_size", 8.0) * 0.33,
      colour = style_text_color(display_payload)
    ) +
    geom_text(
      data = axis_labels,
      aes(x = x, y = y, label = label),
      inherit.aes = FALSE,
      fontface = "bold",
      size = style_numeric(style_typography(display_payload), "axis_title_size", 9.0) * 0.34,
      colour = style_text_color(display_payload)
    ) +
    scale_fill_manual(values = palette_values, guide = "none") +
    coord_cartesian(xlim = c(-0.15, 1.15), ylim = c(0, layout$total * 1.11), expand = FALSE, clip = "off") +
    labs(title = lidocaine_non_empty(display_payload$title), x = NULL, y = NULL) +
    lidocaine_publication_theme(display_payload) +
    theme(
      axis.text = element_blank(),
      axis.ticks = element_blank(),
      axis.line = element_blank(),
      axis.title = element_blank(),
      panel.grid = element_blank(),
      plot.margin = margin(12, 16, 12, 16, unit = "pt")
    )
}

build_radar_profile_dataframe <- function(display_payload) {
  profiles <- display_payload$profiles
  axes <- display_payload$axes
  if (!is.list(profiles) || length(profiles) < 1) {
    stop("profiles must contain at least one profile")
  }
  if (!is.list(axes) || length(axes) < 3) {
    stop("axes must contain at least three labels")
  }
  axis_labels <- extract_label_vector(axes, "axes")
  profile_df <- do.call(rbind, lapply(seq_along(profiles), function(profile_index) {
    profile <- profiles[[profile_index]]
    values <- profile$values
    if (!is.list(values) || length(values) != length(axis_labels)) {
      stop(sprintf("profiles[%d].values must match axes length", profile_index))
    }
    data.frame(
      profile = lidocaine_non_empty(profile$label, sprintf("Profile %d", profile_index)),
      axis = axis_labels,
      value = vapply(values, function(item) lidocaine_numeric(item, NA), numeric(1)),
      axis_index = seq_along(axis_labels),
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(profile_df$value))) {
    stop("profiles.values must be finite")
  }
  profile_df
}

plot_radar_profile <- function(display_payload) {
  radar_df <- build_radar_profile_dataframe(display_payload)
  axis_count <- length(unique(radar_df$axis))
  close_df <- do.call(rbind, lapply(split(radar_df, radar_df$profile), function(frame) {
    rbind(frame, frame[1, , drop = FALSE])
  }))
  close_df$angle <- 2 * pi * (close_df$axis_index - 1) / axis_count
  close_df$x <- close_df$value * sin(close_df$angle)
  close_df$y <- close_df$value * cos(close_df$angle)
  label_df <- unique(radar_df[, c("axis", "axis_index"), drop = FALSE])
  label_df$angle <- 2 * pi * (label_df$axis_index - 1) / axis_count
  label_df$x <- 1.12 * sin(label_df$angle)
  label_df$y <- 1.12 * cos(label_df$angle)
  grid_df <- do.call(rbind, lapply(c(0.25, 0.5, 0.75, 1.0), function(radius) {
    angles <- seq(0, 2 * pi, length.out = 121)
    data.frame(radius = radius, x = radius * sin(angles), y = radius * cos(angles))
  }))
  palette_values <- lidocaine_palette(display_payload, close_df$profile)
  ggplot() +
    geom_path(data = grid_df, aes(x = x, y = y, group = radius), colour = style_grid_color(display_payload), linewidth = 0.22) +
    geom_segment(
      data = label_df,
      aes(x = 0, y = 0, xend = 0.98 * sin(angle), yend = 0.98 * cos(angle)),
      colour = style_grid_color(display_payload),
      linewidth = 0.22
    ) +
    geom_polygon(data = close_df, aes(x = x, y = y, group = profile, fill = profile), alpha = 0.13, colour = NA) +
    geom_path(data = close_df, aes(x = x, y = y, colour = profile), linewidth = 0.68) +
    geom_point(data = radar_df, aes(x = value * sin(2 * pi * (axis_index - 1) / axis_count), y = value * cos(2 * pi * (axis_index - 1) / axis_count), colour = profile), size = 1.5) +
    geom_text(
      data = label_df,
      aes(x = x, y = y, label = axis),
      size = style_numeric(style_typography(display_payload), "tick_size", 8.0) * 0.31,
      colour = style_text_color(display_payload),
      lineheight = 0.92
    ) +
    scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, close_df$profile)) +
    scale_fill_manual(values = palette_values, guide = "none") +
    coord_equal(xlim = c(-1.25, 1.25), ylim = c(-1.18, 1.22), expand = FALSE, clip = "off") +
    labs(title = lidocaine_non_empty(display_payload$title), x = NULL, y = NULL) +
    lidocaine_publication_theme(display_payload) +
    theme(
      axis.text = element_blank(),
      axis.ticks = element_blank(),
      axis.line = element_blank(),
      axis.title = element_blank(),
      panel.grid = element_blank(),
      plot.margin = margin(14, 16, 14, 16, unit = "pt")
    )
}

build_waterfall_response_dataframe <- function(display_payload) {
  bars <- display_payload$bars
  if (!is.list(bars) || length(bars) < 1) {
    stop("bars must contain at least one patient response record")
  }
  waterfall_df <- do.call(rbind, lapply(seq_along(bars), function(index) {
    item <- bars[[index]]
    data.frame(
      sample = lidocaine_non_empty(item$sample %||% item$patient_id, sprintf("P%02d", index)),
      value = lidocaine_numeric(item$value %||% item$percent_change, NA),
      response = lidocaine_non_empty(item$response %||% item$response_class, "Stable"),
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(waterfall_df$value))) {
    stop("bars.value must be finite")
  }
  waterfall_df <- waterfall_df[order(waterfall_df$value), , drop = FALSE]
  waterfall_df$sample <- factor(waterfall_df$sample, levels = waterfall_df$sample)
  waterfall_df
}

plot_waterfall_response <- function(display_payload) {
  waterfall_df <- build_waterfall_response_dataframe(display_payload)
  response_labels <- unique(waterfall_df$response)
  response_palette <- style_series_palette(display_payload, response_labels)
  named_defaults <- c(
    Response = style_color(display_payload, "model_curve", "primary", "#245A6B"),
    Stable = style_color(display_payload, "series_3", "accent", "#D8A24A"),
    Progression = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A"),
    `Partial response` = style_color(display_payload, "model_curve", "primary", "#245A6B"),
    `Progressive disease` = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A")
  )
  response_palette[names(named_defaults)] <- named_defaults[names(named_defaults)]
  response_palette <- response_palette[intersect(names(response_palette), response_labels)]
  plot <- ggplot(waterfall_df, aes(x = sample, y = value, fill = response)) +
    geom_col(width = 0.82, colour = "white", linewidth = 0.16) +
    geom_hline(
      yintercept = 0,
      colour = style_color(display_payload, "axis_line", "axis", "#13293D"),
      linewidth = 0.38
    ) +
    scale_fill_manual(values = response_palette, guide = publication_legend_guides(display_payload, response_labels)) +
    labs(
      title = lidocaine_non_empty(display_payload$title),
      x = lidocaine_non_empty(display_payload$x_label, "Patients ordered by response"),
      y = lidocaine_non_empty(display_payload$y_label, "Change from baseline (%)")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(
      axis.text.x = element_blank(),
      axis.ticks.x = element_blank(),
      panel.grid.major.x = element_blank()
    )
  thresholds <- display_payload$thresholds %||% list()
  if (is.list(thresholds) && length(thresholds) > 0) {
    for (threshold in thresholds) {
      plot <- plot + geom_hline(
        yintercept = lidocaine_numeric(threshold$value, 0),
        linetype = "dashed",
        colour = style_color(display_payload, "reference_line", "muted", "#64748B"),
        linewidth = 0.28
      )
    }
  }
  plot
}

build_lidocaineq_metrics <- function(template_id, display_payload, panel_box) {
  switch(
    template_id,
    distribution_violin_box = list(records = length(display_payload$values %||% list())),
    composition_stacked_bar = list(segments = length(display_payload$segments %||% list())),
    correlation_scatter = list(points = length(display_payload$points %||% list()), annotation = lidocaine_non_empty(display_payload$annotation)),
    alluvial_transition = list(flows = length(display_payload$flows %||% list())),
    radar_profile = list(profiles = length(display_payload$profiles %||% list()), axes = length(display_payload$axes %||% list())),
    waterfall_response = list(bars = length(display_payload$bars %||% list())),
    NULL
  )
}

build_lidocaineq_evidence_plot <- function(template_id, payload) {
  switch(
    template_id,
    distribution_violin_box = plot_distribution_violin_box(payload),
    composition_stacked_bar = plot_composition_stacked_bar(payload),
    correlation_scatter = plot_correlation_scatter(payload),
    alluvial_transition = plot_alluvial_transition(payload),
    radar_profile = plot_radar_profile(payload),
    waterfall_response = plot_waterfall_response(payload),
    NULL
  )
}
