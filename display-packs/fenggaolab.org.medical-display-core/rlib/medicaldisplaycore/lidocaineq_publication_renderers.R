# Student-curated publication renderers adapted from LidocaineQ/Figure_Template.
# These are default lower-bound R/ggplot2 evidence seeds; MAS may still reshape
# them per paper while preserving statistical semantics and source refs.

lidocaine_non_empty <- function(value, fallback = "") {
  normalized <- trimws(as.character(value %||% ""))
  if (nzchar(normalized)) normalized else fallback
}

lidocaine_numeric <- function(value, fallback = 0) {
  if (is.null(value) || length(value) < 1) {
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
  if (is.finite(numeric_value)) numeric_value else as.numeric(fallback)
}

lidocaine_palette <- function(display_payload, labels) {
  style_series_palette(display_payload, unique(as.character(labels)))
}

lidocaine_publication_theme <- function(display_payload) {
  typography <- style_typography(display_payload)
  stroke <- style_stroke(display_payload)
  grid_spec <- style_grid(display_payload)
  text_color <- style_text_color(display_payload)
  grid_color <- style_grid_color(display_payload)
  axis_color <- style_color(display_payload, role_name = "axis_line", palette_key = "axis", fallback = text_color)
  font_family <- trimws(as.character(typography$font_family %||% "sans"))
  major_grid <- if (style_bool(grid_spec, "major", TRUE)) {
    element_line(
      colour = grid_color,
      linewidth = style_numeric(stroke, "grid_linewidth", 0.25),
      linetype = trimws(as.character(grid_spec$linetype %||% "solid"))
    )
  } else {
    element_blank()
  }
  base_size <- style_numeric(typography, "base_size", 11.0)
  theme_bw(
    base_size = base_size,
    base_family = font_family
  ) +
    theme(
      plot.title = element_text(
        face = "bold",
        colour = text_color,
        size = style_numeric(typography, "title_size", base_size + 1.5),
        margin = margin(b = 6, unit = "pt")
      ),
      plot.subtitle = element_text(
        colour = style_color(display_payload, role_name = "subtitle", palette_key = "muted", fallback = "#64748B"),
        size = style_numeric(typography, "subtitle_size", max(7.5, base_size - 1.0)),
        margin = margin(b = 8, unit = "pt")
      ),
      text = element_text(family = font_family, colour = text_color),
      axis.title = element_text(face = "bold"),
      axis.text = element_text(
        colour = text_color,
        size = style_numeric(typography, "tick_size", max(7.0, base_size - 1.8))
      ),
      axis.title.x = element_text(
        colour = text_color,
        size = style_numeric(typography, "axis_title_size", max(7.8, base_size - 0.5))
      ),
      axis.title.y = element_text(
        colour = text_color,
        size = style_numeric(typography, "axis_title_size", max(7.8, base_size - 0.5))
      ),
      legend.position = "bottom",
      legend.box = "horizontal",
      legend.title = element_blank(),
      legend.text = element_text(
        colour = text_color,
        size = style_numeric(typography, "legend_size", max(7.0, base_size - 2.0))
      ),
      legend.key = element_blank(),
      legend.background = element_blank(),
      legend.box.background = element_blank(),
      panel.grid.minor = element_blank(),
      panel.grid.major = major_grid,
      panel.border = element_rect(
        colour = axis_color,
        linewidth = style_numeric(stroke, "axis_linewidth", 0.45),
        fill = NA
      ),
      strip.background = element_rect(
        fill = style_color(display_payload, role_name = "highlight_band", palette_key = "light", fallback = "#EEF4F7"),
        colour = grid_color,
        linewidth = 0.4
      ),
      strip.text = element_text(face = "bold", colour = text_color),
      plot.background = element_rect(
        fill = style_color(display_payload, role_name = "figure_background", palette_key = "background", fallback = "#FFFFFF"),
        colour = NA
      ),
      panel.background = element_rect(
        fill = style_color(display_payload, role_name = "figure_background", palette_key = "background", fallback = "#FFFFFF"),
        colour = NA
      ),
      plot.margin = margin(9, 10, 8, 10, unit = "pt")
    )
}

lidocaine_wrap_label <- function(value, width = 68) {
  label <- lidocaine_non_empty(value)
  if (!nzchar(label)) {
    return("")
  }
  paste(strwrap(label, width = width), collapse = "\n")
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
      subtitle = lidocaine_wrap_label(display_payload$subtitle %||% display_payload$caption, 74),
      x = lidocaine_non_empty(display_payload$x_label, "Feature score"),
      y = lidocaine_non_empty(display_payload$y_label, "Outcome-associated score")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1)
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

build_baseline_table_dataframe <- function(display_payload) {
  rows <- display_payload$rows
  if (!is.list(rows) || length(rows) < 1) {
    stop("baseline table payload must contain rows")
  }
  table_df <- do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    data.frame(
      variable = lidocaine_non_empty(item$variable, sprintf("Variable %d", index)),
      level = lidocaine_non_empty(item$level),
      overall = lidocaine_non_empty(item$overall, "NA"),
      group_a = lidocaine_non_empty(item$group_a, "NA"),
      group_b = lidocaine_non_empty(item$group_b, "NA"),
      p_value = lidocaine_non_empty(item$p_value, ""),
      row_type = lidocaine_non_empty(item$row_type, "body"),
      stringsAsFactors = FALSE
    )
  }))
  table_df$display_variable <- ifelse(
    nzchar(table_df$level),
    paste0("  ", table_df$level),
    table_df$variable
  )
  table_df$row_index <- seq_len(nrow(table_df))
  table_df$y <- rev(table_df$row_index)
  table_df
}

plot_lidocaine_baseline_table <- function(display_payload) {
  suppressPackageStartupMessages({
    library(gridExtra)
    library(grid)
  })
  table_df <- build_baseline_table_dataframe(display_payload)
  table_for_grob <- data.frame(
    Characteristic = table_df$display_variable,
    Overall = table_df$overall,
    GroupA = table_df$group_a,
    GroupB = table_df$group_b,
    P = table_df$p_value,
    check.names = FALSE,
    stringsAsFactors = FALSE
  )
  section_rows <- table_df$row_type == "section"
  if (any(section_rows)) {
    table_for_grob[section_rows, c("Overall", "GroupA", "GroupB")] <- ""
  }
  names(table_for_grob) <- c(
    "Characteristic",
    lidocaine_non_empty(display_payload$overall_header, "Overall"),
    lidocaine_non_empty(display_payload$group_a_header, "Group A"),
    lidocaine_non_empty(display_payload$group_b_header, "Group B"),
    lidocaine_non_empty(display_payload$p_header, "P")
  )
  row_fills <- rep(
    c(
      style_color(display_payload, "figure_background", "background", "#FFFFFF"),
      style_color(display_payload, "highlight_band", "light", "#EEF4F7")
    ),
    length.out = nrow(table_for_grob)
  )
  row_fills[section_rows] <- style_color(display_payload, "highlight_band", "light", "#EEF4F7")
  table_theme <- gridExtra::ttheme_minimal(
    base_size = style_numeric(style_typography(display_payload), "tick_size", 8.8),
    padding = grid::unit(c(3.0, 4.0), "pt"),
    core = list(
      fg_params = list(col = style_text_color(display_payload), hjust = 0.5, x = 0.5),
      bg_params = list(
        fill = row_fills,
        col = "white"
      )
    ),
    colhead = list(
      fg_params = list(fontface = "bold", col = "white", hjust = 0.5, x = 0.5),
      bg_params = list(fill = style_color(display_payload, "model_curve", "primary", "#245A6B"), col = "white")
    )
  )
  table_grob <- gridExtra::tableGrob(table_for_grob, rows = NULL, theme = table_theme)
  table_grob$widths <- grid::unit(c(0.34, 0.18, 0.18, 0.18, 0.12), "npc")
  table_grob$heights <- grid::unit(rep(1 / length(table_grob$heights), length(table_grob$heights)), "npc")
  title_grob <- grid::textGrob(
    lidocaine_non_empty(display_payload$title, "Baseline characteristics table"),
    x = 0.02,
    hjust = 0,
    gp = grid::gpar(
      fontface = "bold",
      fontsize = style_numeric(style_typography(display_payload), "title_size", 12.0) * 0.84,
      col = style_text_color(display_payload)
    )
  )
  subtitle <- lidocaine_curve_subtitle(display_payload, "Publication Table 1 preview")
  subtitle_grob <- grid::textGrob(
    lidocaine_wrap_label(subtitle, 82),
    x = 0.02,
    hjust = 0,
    gp = grid::gpar(
      fontsize = style_numeric(style_typography(display_payload), "subtitle_size", 8.4) * 0.82,
      col = style_color(display_payload, role_name = "subtitle", palette_key = "muted", fallback = "#64748B")
    )
  )
  arranged <- gridExtra::arrangeGrob(title_grob, subtitle_grob, table_grob, heights = c(0.085, 0.055, 0.860))
  gridExtra::arrangeGrob(arranged, padding = grid::unit(7, "pt"))
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

plot_alluvial_transition <- function(display_payload) {
  flow_df <- build_alluvial_transition_dataframe(display_payload)
  if (!requireNamespace("ggalluvial", quietly = TRUE)) {
    stop("alluvial_transition requires OPL-prepared dependency package `ggalluvial`")
  }
  flow_df$source <- factor(flow_df$source, levels = unique(flow_df$source))
  target_levels <- sort(unique(as.character(flow_df$target)))
  flow_df$target <- factor(flow_df$target, levels = target_levels)
  palette_values <- lidocaine_palette(display_payload, target_levels)
  ggplot(flow_df, aes(axis1 = source, axis2 = target, y = value)) +
    ggalluvial::geom_alluvium(aes(fill = target), width = 0.18, alpha = 0.88, knot.pos = 0.42) +
    ggalluvial::geom_stratum(
      width = 0.18,
      fill = style_color(display_payload, "figure_background", "background", "#FFFFFF"),
      colour = style_grid_color(display_payload),
      linewidth = 0.24
    ) +
    ggalluvial::stat_stratum(
      geom = "text",
      aes(label = after_stat(stratum)),
      size = style_numeric(style_typography(display_payload), "tick_size", 8.0) * 0.34,
      colour = style_text_color(display_payload)
    ) +
    scale_fill_manual(
      values = palette_values,
      breaks = target_levels,
      guide = publication_legend_guides(display_payload, target_levels)
    ) +
    scale_x_discrete(
      limits = c(
        lidocaine_non_empty(display_payload$source_axis_label, "Baseline state"),
        lidocaine_non_empty(display_payload$target_axis_label, "Follow-up state")
      ),
      expand = c(0.035, 0.035)
    ) +
    labs(
      title = lidocaine_non_empty(display_payload$title),
      subtitle = lidocaine_wrap_label(display_payload$subtitle %||% display_payload$caption, 72),
      x = NULL,
      y = NULL
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(
      legend.position = "top",
      legend.justification = "center",
      legend.box = "horizontal",
      axis.text.x = element_text(
        colour = style_text_color(display_payload),
        size = style_numeric(style_typography(display_payload), "axis_title_size", 9.0) * 0.88,
        margin = margin(t = 8, unit = "pt")
      ),
      axis.text.y = element_blank(),
      axis.ticks = element_blank(),
      axis.line = element_blank(),
      axis.title = element_blank(),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),
      panel.border = element_blank(),
      plot.margin = margin(8, 32, 18, 32, unit = "pt")
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
    roc_curve_binary = list(source_renderer = "LidocaineQ/Figure_Template::roc_auc", series = display_payload$series, reference_line = display_payload$reference_line),
    time_dependent_roc_horizon = list(source_renderer = "LidocaineQ/Figure_Template::time_dependent_roc_horizon", series = display_payload$series, reference_line = display_payload$reference_line),
    calibration_curve_binary = list(source_renderer = "LidocaineQ/Figure_Template::calibration_curve_binary", series = display_payload$series, points = display_payload$points %||% list()),
    pr_curve_binary = list(source_renderer = "LidocaineQ/Figure_Template::pr_curve_binary", series = display_payload$series, reference_line = display_payload$reference_line),
    decision_curve_binary = list(source_renderer = "LidocaineQ/Figure_Template::decision_curve_binary", series = display_payload$series, reference_line = display_payload$reference_line),
    time_to_event_decision_curve = list(source_renderer = "LidocaineQ/Figure_Template::time_to_event_decision_curve", series = display_payload$series, reference_line = display_payload$reference_line),
    time_to_event_multihorizon_calibration_panel = list(source_renderer = "LidocaineQ/Figure_Template::time_to_event_multihorizon_calibration_panel", panels = display_payload$panels %||% list()),
    risk_layering_monotonic_bars = list(source_renderer = "LidocaineQ/Figure_Template::risk_layering_monotonic_bars", risk_group_summaries = display_payload$risk_group_summaries %||% list(), left_bars = display_payload$left_bars %||% list(), right_bars = display_payload$right_bars %||% list()),
    kaplan_meier_grouped = list(source_renderer = "LidocaineQ/Figure_Template::survival_km", groups = display_payload$groups, risk_table = display_payload$risk_table %||% list()),
    cumulative_incidence_grouped = list(source_renderer = "LidocaineQ/Figure_Template::cumulative_incidence_grouped", groups = display_payload$groups),
    pca_scatter_grouped = list(source_renderer = "LidocaineQ/Figure_Template::embedding_umap_tsne", embedding_input_mode = display_payload$embedding_input_mode %||% ""),
    tsne_scatter_grouped = list(source_renderer = "LidocaineQ/Figure_Template::embedding_umap_tsne", embedding_input_mode = display_payload$embedding_input_mode %||% ""),
    umap_scatter_grouped = list(source_renderer = "LidocaineQ/Figure_Template::embedding_umap_tsne", embedding_input_mode = display_payload$embedding_input_mode %||% ""),
    forest_effect_main = list(source_renderer = "LidocaineQ/Figure_Template::forest_cox", rows = display_payload$rows),
    heatmap_group_comparison = list(source_renderer = "LidocaineQ/Figure_Template::heatmap", cells = display_payload$cells),
    confusion_matrix_heatmap_binary = list(source_renderer = "LidocaineQ/Figure_Template::confusion_matrix_heatmap_binary", cells = display_payload$cells),
    coefficient_path_panel = list(source_renderer = "LidocaineQ/Figure_Template::coefficient_path_panel", path_points = length(display_payload$path_points %||% display_payload$coefficient_path %||% display_payload$coefficient_points %||% list())),
    generalizability_subgroup_composite_panel = list(source_renderer = "LidocaineQ/Figure_Template::generalizability_subgroup_composite_panel", overview_rows = display_payload$overview_rows %||% list(), subgroup_rows = display_payload$subgroup_rows %||% list()),
    pathway_enrichment_dotplot_panel = list(source_renderer = "LidocaineQ/Figure_Template::gsea_enrichment", points = display_payload$points %||% list()),
    celltype_marker_dotplot_panel = list(source_renderer = "LidocaineQ/Figure_Template::celltype_marker_dotplot_panel", points = display_payload$points %||% list()),
    omics_volcano_panel = list(source_renderer = "LidocaineQ/Figure_Template::volcano_deg", points = display_payload$points %||% list()),
    genomic_alteration_landscape_panel = list(source_renderer = "LidocaineQ/Figure_Template::oncoplot_mutation", alteration_records = display_payload$alteration_records %||% list()),
    cnv_recurrence_summary_panel = list(source_renderer = "LidocaineQ/Figure_Template::cnv_recurrence_summary_panel", cnv_records = display_payload$cnv_records %||% list()),
    genomic_alteration_consequence_panel = list(source_renderer = "LidocaineQ/Figure_Template::genomic_alteration_consequence_panel", consequence_points = display_payload$consequence_points %||% display_payload$points %||% list()),
    shap_summary_beeswarm = list(source_renderer = "LidocaineQ/Figure_Template::shap_summary_beeswarm", rows = display_payload$rows %||% list()),
    shap_dependence_panel = list(source_renderer = "LidocaineQ/Figure_Template::shap_dependence_panel", panels = display_payload$panels %||% list()),
    shap_waterfall_local_explanation_panel = list(source_renderer = "LidocaineQ/Figure_Template::shap_waterfall_local_explanation_panel", panels = display_payload$panels %||% list()),
    model_complexity_audit_panel = list(source_renderer = "LidocaineQ/Figure_Template::model_complexity_audit_panel", metric_panels = display_payload$metric_panels %||% list(), audit_panels = display_payload$audit_panels %||% list()),
    distribution_violin_box = list(source_renderer = "LidocaineQ/Figure_Template::violin_box", records = length(display_payload$values %||% list())),
    composition_stacked_bar = list(source_renderer = "LidocaineQ/Figure_Template::bar_stacked", segments = length(display_payload$segments %||% list())),
    correlation_scatter = list(source_renderer = "LidocaineQ/Figure_Template::scatter_correlation", points = length(display_payload$points %||% list()), annotation = lidocaine_non_empty(display_payload$annotation)),
    alluvial_transition = list(source_renderer = "LidocaineQ/Figure_Template::sankey_alluvial", flows = length(display_payload$flows %||% list())),
    radar_profile = list(source_renderer = "LidocaineQ/Figure_Template::radar", profiles = length(display_payload$profiles %||% list()), axes = length(display_payload$axes %||% list())),
    waterfall_response = list(source_renderer = "LidocaineQ/Figure_Template::waterfall", bars = length(display_payload$bars %||% list())),
    table1_baseline_characteristics = list(source_renderer = "LidocaineQ/Figure_Template::baseline_table", rows = length(display_payload$rows %||% list())),
    NULL
  )
}

build_lidocaineq_evidence_plot <- function(template_id, payload) {
  switch(
    template_id,
    roc_curve_binary = plot_lidocaine_roc_curve(payload, template_id = template_id),
    time_dependent_roc_horizon = plot_lidocaine_roc_curve(payload, template_id = template_id),
    calibration_curve_binary = plot_lidocaine_calibration_curve(payload),
    pr_curve_binary = plot_lidocaine_pr_curve(payload),
    decision_curve_binary = plot_lidocaine_decision_curve(payload, title_fallback = "Decision curve"),
    time_to_event_decision_curve = plot_lidocaine_decision_curve(payload, title_fallback = "Decision curve"),
    time_to_event_multihorizon_calibration_panel = plot_lidocaine_multihorizon_calibration(payload),
    risk_layering_monotonic_bars = plot_lidocaine_risk_layering(payload),
    kaplan_meier_grouped = plot_lidocaine_kaplan_meier(payload),
    cumulative_incidence_grouped = plot_lidocaine_cumulative_incidence(payload),
    forest_effect_main = plot_lidocaine_forest(payload),
    heatmap_group_comparison = plot_lidocaine_heatmap(payload),
    confusion_matrix_heatmap_binary = plot_lidocaine_confusion_matrix(payload),
    coefficient_path_panel = plot_lidocaine_coefficient_path(payload),
    generalizability_subgroup_composite_panel = plot_lidocaine_generalizability(payload),
    pathway_enrichment_dotplot_panel = plot_lidocaine_pathway_enrichment(payload),
    celltype_marker_dotplot_panel = plot_lidocaine_celltype_marker_dotplot(payload),
    omics_volcano_panel = plot_lidocaine_volcano(payload),
    genomic_alteration_landscape_panel = plot_lidocaine_genomic_landscape(payload),
    cnv_recurrence_summary_panel = plot_lidocaine_cnv_recurrence(payload),
    genomic_alteration_consequence_panel = plot_lidocaine_genomic_consequence(payload),
    shap_summary_beeswarm = plot_lidocaine_shap_summary(payload),
    shap_dependence_panel = plot_lidocaine_shap_dependence(payload),
    shap_waterfall_local_explanation_panel = plot_lidocaine_shap_waterfall(payload),
    model_complexity_audit_panel = plot_lidocaine_model_complexity(payload),
    distribution_violin_box = plot_distribution_violin_box(payload),
    composition_stacked_bar = plot_composition_stacked_bar(payload),
    correlation_scatter = plot_correlation_scatter(payload),
    alluvial_transition = plot_alluvial_transition(payload),
    radar_profile = plot_radar_profile(payload),
    waterfall_response = plot_waterfall_response(payload),
    table1_baseline_characteristics = plot_lidocaine_baseline_table(payload),
    NULL
  )
}
