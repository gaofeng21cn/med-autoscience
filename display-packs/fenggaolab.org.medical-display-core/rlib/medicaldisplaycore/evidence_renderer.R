suppressPackageStartupMessages({
  library(jsonlite)
  library(ggplot2)
  library(ggsci)
  library(grid)
})

`%||%` <- function(left, right) {
  if (is.null(left)) right else left
}

normalize_template_id <- function(value) {
  template_id <- trimws(as.character(value %||% ""))
  if (!nzchar(template_id)) {
    stop("template_id must be non-empty")
  }
  parts <- strsplit(template_id, "::", fixed = TRUE)[[1]]
  parts[[length(parts)]]
}

read_render_request <- function(request_path) {
  request <- fromJSON(request_path, simplifyVector = FALSE)
  if (is.null(request$display_payload)) {
    stop("render request must contain display_payload")
  }
  request
}

payload_from_request <- function(request) {
  display_payload <- request$display_payload
  data_payload <- display_payload$data_payload
  if (!is.null(data_payload) && is.list(data_payload)) {
    merged_payload <- display_payload
    for (field_name in names(data_payload)) {
      merged_payload[[field_name]] <- data_payload[[field_name]]
    }
    return(merged_payload)
  }
  display_payload
}

as_numeric_vector <- function(values, field_name) {
  if (!is.list(values) || length(values) < 2) {
    stop(sprintf("%s must contain at least two numeric values", field_name))
  }
  numeric_values <- vapply(values, function(item) {
    if (!is.numeric(item)) {
      stop(sprintf("%s must contain only numeric values", field_name))
    }
    as.numeric(item)
  }, numeric(1))
  numeric_values
}

render_context_from_payload <- function(display_payload) {
  display_payload$render_context %||% list()
}

style_palette <- function(display_payload) {
  render_context_from_payload(display_payload)$palette %||% list()
}

style_semantic_roles <- function(display_payload) {
  render_context_from_payload(display_payload)$semantic_roles %||% list()
}

style_roles <- function(display_payload) {
  render_context_from_payload(display_payload)$style_roles %||% list()
}

style_typography <- function(display_payload) {
  render_context_from_payload(display_payload)$typography %||% list()
}

style_stroke <- function(display_payload) {
  render_context_from_payload(display_payload)$stroke %||% list()
}

style_grid <- function(display_payload) {
  render_context_from_payload(display_payload)$grid %||% list()
}

style_numeric <- function(mapping, key, fallback) {
  value <- mapping[[key]]
  if (is.null(value)) {
    return(as.numeric(fallback))
  }
  numeric_value <- suppressWarnings(as.numeric(value))
  if (!is.finite(numeric_value)) as.numeric(fallback) else numeric_value
}

style_bool <- function(mapping, key, fallback) {
  value <- mapping[[key]]
  if (is.null(value)) {
    return(isTRUE(fallback))
  }
  if (is.logical(value)) {
    return(isTRUE(value))
  }
  normalized <- tolower(trimws(as.character(value)))
  if (normalized %in% c("true", "1", "yes", "on")) {
    return(TRUE)
  }
  if (normalized %in% c("false", "0", "no", "off")) {
    return(FALSE)
  }
  isTRUE(fallback)
}

style_color <- function(display_payload, role_name = NULL, palette_key = NULL, fallback = "#13293D") {
  roles <- style_roles(display_payload)
  semantic_roles <- style_semantic_roles(display_payload)
  palette <- style_palette(display_payload)
  candidates <- list()
  if (!is.null(role_name)) {
    candidates <- c(candidates, list(roles[[role_name]], semantic_roles[[role_name]]))
  }
  if (!is.null(palette_key)) {
    candidates <- c(candidates, list(palette_key))
  }
  for (candidate in candidates) {
    value <- trimws(as.character(candidate %||% ""))
    if (!nzchar(value)) {
      next
    }
    if (startsWith(value, "#")) {
      return(value)
    }
    palette_value <- trimws(as.character(palette[[value]] %||% ""))
    if (nzchar(palette_value)) {
      return(palette_value)
    }
  }
  fallback
}

style_text_color <- function(display_payload) {
  style_color(display_payload, role_name = "text", palette_key = "text", fallback = "#13293D")
}

style_grid_color <- function(display_payload) {
  grid_spec <- style_grid(display_payload)
  palette_key <- grid_spec$color %||% "grid"
  style_color(display_payload, role_name = "grid_line", palette_key = palette_key, fallback = "#E6EDF2")
}

style_series_palette <- function(display_payload, labels) {
  labels <- as.character(labels)
  if (length(labels) < 1) {
    return(character())
  }
  role_order <- c("model_curve", "comparator_curve", "reference_line", "highlight_band", "flow_primary_edge", "flow_secondary_edge")
  palette <- style_palette(display_payload)
  fallback_values <- c(
    style_color(display_payload, "model_curve", "primary", "#5F766B"),
    style_color(display_payload, "comparator_curve", "secondary", "#B9AD9C"),
    style_color(display_payload, "reference_line", "neutral", "#7B8794"),
    style_color(display_payload, "highlight_band", "light", "#E7E1D8"),
    style_color(display_payload, palette_key = "contrast", fallback = "#2F5D8A"),
    style_color(display_payload, palette_key = "audit", fallback = "#B57F7F")
  )
  values <- vapply(seq_along(labels), function(index) {
    role_name <- role_order[[((index - 1) %% length(role_order)) + 1]]
    if (index <= length(role_order)) {
      style_color(display_payload, role_name = role_name, fallback = fallback_values[[index]])
    } else {
      palette_values <- unlist(palette, use.names = FALSE)
      if (length(palette_values) > 0) {
        palette_values[[((index - 1) %% length(palette_values)) + 1]]
      } else {
        fallback_values[[((index - 1) %% length(fallback_values)) + 1]]
      }
    }
  }, character(1))
  stats::setNames(values, labels)
}

theme_publication <- function(display_payload = list()) {
  typography <- style_typography(display_payload)
  stroke <- style_stroke(display_payload)
  grid_spec <- style_grid(display_payload)
  font_family <- trimws(as.character(typography$font_family %||% "sans"))
  base_size <- style_numeric(typography, "base_size", 11.0)
  title_size <- style_numeric(typography, "title_size", 12.5)
  axis_title_size <- style_numeric(typography, "axis_title_size", 11.0)
  tick_size <- style_numeric(typography, "tick_size", 10.0)
  legend_size <- style_numeric(typography, "legend_size", tick_size)
  text_color <- style_text_color(display_payload)
  grid_linewidth <- style_numeric(stroke, "grid_linewidth", 0.25)
  grid_color <- style_grid_color(display_payload)
  major_axis <- tolower(trimws(as.character(grid_spec$major_axis %||% "both")))
  minor_axis <- tolower(trimws(as.character(grid_spec$minor_axis %||% "none")))
  major_grid <- if (style_bool(grid_spec, "major", TRUE)) {
    element_line(colour = grid_color, linewidth = grid_linewidth, linetype = trimws(as.character(grid_spec$linetype %||% "solid")))
  } else {
    element_blank()
  }
  minor_grid <- if (style_bool(grid_spec, "minor", FALSE)) {
    element_line(colour = grid_color, linewidth = grid_linewidth * 0.6, linetype = trimws(as.character(grid_spec$minor_linetype %||% grid_spec$linetype %||% "solid")))
  } else {
    element_blank()
  }
  theme_bw(base_size = base_size, base_family = font_family) +
    theme(
      text = element_text(family = font_family, colour = text_color),
      plot.title = element_text(face = "bold", colour = text_color, size = title_size),
      axis.title = element_text(face = "bold", colour = text_color, size = axis_title_size),
      axis.text = element_text(colour = text_color, size = tick_size),
      legend.text = element_text(size = legend_size, colour = text_color),
      legend.position = "bottom",
      legend.title = element_blank(),
      panel.grid.major.x = if (major_axis %in% c("x", "both", "all")) major_grid else element_blank(),
      panel.grid.major.y = if (major_axis %in% c("y", "both", "all")) major_grid else element_blank(),
      panel.grid.minor.x = if (minor_axis %in% c("x", "both", "all")) minor_grid else element_blank(),
      panel.grid.minor.y = if (minor_axis %in% c("y", "both", "all")) minor_grid else element_blank()
    )
}

build_curve_dataframe <- function(series_payload) {
  frames <- lapply(seq_along(series_payload), function(index) {
    item <- series_payload[[index]]
    x <- as_numeric_vector(item$x, sprintf("series[%d].x", index))
    y <- as_numeric_vector(item$y, sprintf("series[%d].y", index))
    if (length(x) != length(y)) {
      stop(sprintf("series[%d].x and series[%d].y must have the same length", index, index))
    }
    data.frame(
      label = rep(trimws(as.character(item$label %||% "")), length(x)),
      x = x,
      y = y,
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, frames)
}

build_reference_dataframe <- function(reference_line) {
  if (is.null(reference_line)) {
    return(NULL)
  }
  x <- as_numeric_vector(reference_line$x, "reference_line.x")
  y <- as_numeric_vector(reference_line$y, "reference_line.y")
  if (length(x) != length(y)) {
    stop("reference_line.x and reference_line.y must have the same length")
  }
  data.frame(x = x, y = y)
}

build_point_dataframe <- function(points_payload, x_field = "x", y_field = "y") {
  frames <- lapply(seq_along(points_payload), function(index) {
    item <- points_payload[[index]]
    data.frame(
      x = as.numeric(item[[x_field]]),
      y = as.numeric(item[[y_field]]),
      group = trimws(as.character(item$group %||% "")),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, frames)
}

extract_label_vector <- function(items_payload, field_name) {
  if (!is.list(items_payload) || length(items_payload) < 1) {
    stop(sprintf("%s must contain at least one labeled item", field_name))
  }
  labels <- vapply(seq_along(items_payload), function(index) {
    item <- items_payload[[index]]
    label <- trimws(as.character(item$label %||% ""))
    if (!nzchar(label)) {
      stop(sprintf("%s[%d].label must be non-empty", field_name, index))
    }
    label
  }, character(1))
  labels
}

build_heatmap_dataframe <- function(cells_payload, column_order = NULL, row_order = NULL) {
  frames <- lapply(seq_along(cells_payload), function(index) {
    item <- cells_payload[[index]]
    data.frame(
      x = trimws(as.character(item$x %||% "")),
      y = trimws(as.character(item$y %||% "")),
      value = as.numeric(item$value),
      stringsAsFactors = FALSE
    )
  })
  heat_df <- do.call(rbind, frames)
  x_levels <- if (is.null(column_order)) unique(heat_df$x) else column_order
  y_levels <- if (is.null(row_order)) rev(unique(heat_df$y)) else rev(row_order)
  heat_df$x <- factor(heat_df$x, levels = x_levels)
  heat_df$y <- factor(heat_df$y, levels = y_levels)
  heat_df
}

build_forest_dataframe <- function(rows_payload) {
  frames <- lapply(seq_along(rows_payload), function(index) {
    item <- rows_payload[[index]]
    data.frame(
      label = trimws(as.character(item$label %||% "")),
      estimate = as.numeric(item$estimate),
      lower = as.numeric(item$lower),
      upper = as.numeric(item$upper),
      stringsAsFactors = FALSE
    )
  })
  forest_df <- do.call(rbind, frames)
  forest_df$label <- factor(forest_df$label, levels = rev(forest_df$label))
  forest_df
}

plot_binary_curve <- function(display_payload) {
  series_payload <- display_payload$series
  if (!is.list(series_payload) || length(series_payload) < 1) {
    stop("series must contain at least one curve")
  }
  curve_df <- build_curve_dataframe(series_payload)
  reference_df <- build_reference_dataframe(display_payload$reference_line)
  plot <- ggplot(curve_df, aes(x = x, y = y, colour = label)) +
    geom_line(linewidth = style_numeric(style_stroke(display_payload), "primary_linewidth", 2.2) * 0.42) +
    coord_cartesian(xlim = c(0, 1), ylim = c(min(curve_df$y, 0), max(curve_df$y, 1))) +
    scale_color_manual(values = style_series_palette(display_payload, unique(curve_df$label))) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication(display_payload)
  if (!is.null(reference_df)) {
    plot <- plot + geom_line(
      data = reference_df,
      aes(x = x, y = y),
      inherit.aes = FALSE,
      colour = style_color(display_payload, "reference_line", "neutral", "#6B7280"),
      linewidth = style_numeric(style_stroke(display_payload), "reference_linewidth", 1.0) * 0.6,
      linetype = "dashed"
    )
  }
  plot
}

plot_kaplan_meier <- function(display_payload) {
  groups_payload <- display_payload$groups
  if (!is.list(groups_payload) || length(groups_payload) < 1) {
    stop("groups must contain at least one survival series")
  }
  frames <- lapply(seq_along(groups_payload), function(index) {
    item <- groups_payload[[index]]
    x <- as_numeric_vector(item$times, sprintf("groups[%d].times", index))
    y <- as_numeric_vector(item$values, sprintf("groups[%d].values", index))
    if (length(x) != length(y)) {
      stop(sprintf("groups[%d].times and groups[%d].values must have the same length", index, index))
    }
    data.frame(
      label = rep(trimws(as.character(item$label %||% "")), length(x)),
      x = x,
      y = y,
      stringsAsFactors = FALSE
    )
  })
  curve_df <- do.call(rbind, frames)
  plot <- ggplot(curve_df, aes(x = x, y = y, colour = label)) +
    geom_step(linewidth = style_numeric(style_stroke(display_payload), "primary_linewidth", 2.2) * 0.42, direction = "hv") +
    coord_cartesian(xlim = c(0, max(curve_df$x)), ylim = c(0, 1)) +
    scale_color_manual(values = style_series_palette(display_payload, unique(curve_df$label))) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication(display_payload)
  annotation <- trimws(as.character(display_payload$annotation %||% ""))
  if (nzchar(annotation)) {
    plot <- plot + annotate(
      "text",
      x = max(curve_df$x) * 0.98,
      y = 0.08,
      label = annotation,
      hjust = 1,
      vjust = 0,
      size = style_numeric(style_typography(display_payload), "tick_size", 10.0) * 0.33,
      colour = style_text_color(display_payload)
    )
  }
  plot
}

plot_embedding_scatter <- function(display_payload) {
  points_payload <- display_payload$points
  if (!is.list(points_payload) || length(points_payload) < 1) {
    stop("points must contain at least one observation")
  }
  point_df <- build_point_dataframe(points_payload)
  plot <- ggplot(point_df, aes(x = x, y = y, colour = group)) +
    geom_point(size = style_numeric(style_stroke(display_payload), "marker_size", 4.5) * 0.62, alpha = 0.9) +
    scale_color_manual(values = style_series_palette(display_payload, unique(point_df$group))) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication(display_payload)
  plot
}

plot_heatmap <- function(display_payload) {
  cells_payload <- display_payload$cells
  if (!is.list(cells_payload) || length(cells_payload) < 1) {
    stop("cells must contain at least one matrix entry")
  }
  column_order <- if (is.null(display_payload$column_order)) NULL else extract_label_vector(display_payload$column_order, "column_order")
  row_order <- if (is.null(display_payload$row_order)) NULL else extract_label_vector(display_payload$row_order, "row_order")
  heat_df <- build_heatmap_dataframe(cells_payload, column_order = column_order, row_order = row_order)
  plot <- ggplot(heat_df, aes(x = x, y = y, fill = value)) +
    geom_tile(colour = "white", linewidth = 0.5) +
    geom_text(aes(label = sprintf("%.2f", value)), size = style_numeric(style_typography(display_payload), "tick_size", 10.0) * 0.31, colour = style_text_color(display_payload)) +
    scale_fill_gradient2(
      low = style_color(display_payload, "heatmap_low", "heatmap_low", "#2166AC"),
      mid = style_color(display_payload, "heatmap_mid", "heatmap_mid", "#FFFFFF"),
      high = style_color(display_payload, "heatmap_high", "heatmap_high", "#B2182B"),
      midpoint = 0
    ) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication(display_payload) +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
  plot
}

plot_performance_heatmap <- function(display_payload) {
  cells_payload <- display_payload$cells
  if (!is.list(cells_payload) || length(cells_payload) < 1) {
    stop("cells must contain at least one matrix entry")
  }
  metric_name <- trimws(as.character(display_payload$metric_name %||% ""))
  if (!nzchar(metric_name)) {
    stop("metric_name must be non-empty")
  }
  column_order <- if (is.null(display_payload$column_order)) NULL else extract_label_vector(display_payload$column_order, "column_order")
  row_order <- if (is.null(display_payload$row_order)) NULL else extract_label_vector(display_payload$row_order, "row_order")
  heat_df <- build_heatmap_dataframe(cells_payload, column_order = column_order, row_order = row_order)
  plot <- ggplot(heat_df, aes(x = x, y = y, fill = value)) +
    geom_tile(colour = "white", linewidth = 0.5) +
    geom_text(aes(label = sprintf("%.2f", value)), size = style_numeric(style_typography(display_payload), "tick_size", 10.0) * 0.31, colour = style_text_color(display_payload)) +
    scale_fill_gradient2(
      low = style_color(display_payload, "heatmap_low", "heatmap_low", "#2166AC"),
      mid = style_color(display_payload, "heatmap_mid", "heatmap_mid", "#FFFFFF"),
      high = style_color(display_payload, "heatmap_high", "heatmap_high", "#B2182B"),
      midpoint = 0.5,
      limits = c(0, 1),
      name = metric_name
    ) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication(display_payload) +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
  plot
}

plot_confusion_matrix_heatmap <- function(display_payload) {
  cells_payload <- display_payload$cells
  if (!is.list(cells_payload) || length(cells_payload) < 1) {
    stop("cells must contain at least one matrix entry")
  }
  metric_name <- trimws(as.character(display_payload$metric_name %||% ""))
  if (!nzchar(metric_name)) {
    stop("metric_name must be non-empty")
  }
  normalization <- trimws(as.character(display_payload$normalization %||% ""))
  if (!normalization %in% c("row_fraction", "column_fraction", "overall_fraction")) {
    stop("normalization must be one of row_fraction, column_fraction, or overall_fraction")
  }
  column_order <- if (is.null(display_payload$column_order)) NULL else extract_label_vector(display_payload$column_order, "column_order")
  row_order <- if (is.null(display_payload$row_order)) NULL else extract_label_vector(display_payload$row_order, "row_order")
  heat_df <- build_heatmap_dataframe(cells_payload, column_order = column_order, row_order = row_order)
  plot <- ggplot(heat_df, aes(x = x, y = y, fill = value)) +
    geom_tile(colour = "white", linewidth = 0.7) +
    geom_text(aes(label = sprintf("%.0f%%", value * 100)), size = style_numeric(style_typography(display_payload), "axis_title_size", 11.0) * 0.38, colour = style_text_color(display_payload), fontface = "bold") +
    scale_fill_gradient(
      low = style_color(display_payload, "heatmap_mid", "heatmap_mid", "#F7FBFF"),
      high = style_color(display_payload, "heatmap_low", "heatmap_low", "#2166AC"),
      limits = c(0, 1),
      name = metric_name
    ) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication(display_payload) +
    theme(
      axis.text.x = element_text(angle = 0, hjust = 0.5),
      axis.text.y = element_text(face = "bold"),
      axis.text = element_text(face = "bold"),
      panel.grid.major = element_blank()
    )
  plot
}

plot_forest <- function(display_payload) {
  rows_payload <- display_payload$rows
  if (!is.list(rows_payload) || length(rows_payload) < 1) {
    stop("rows must contain at least one effect estimate")
  }
  forest_df <- build_forest_dataframe(rows_payload)
  reference_value <- as.numeric(display_payload$reference_value %||% 1.0)
  plot <- ggplot(forest_df, aes(y = label, x = estimate)) +
    geom_vline(xintercept = reference_value, colour = style_color(display_payload, "reference_line", "neutral", "#6B7280"), linewidth = style_numeric(style_stroke(display_payload), "reference_linewidth", 1.0) * 0.6, linetype = "dashed") +
    geom_segment(aes(x = lower, xend = upper, y = label, yend = label), linewidth = style_numeric(style_stroke(display_payload), "primary_linewidth", 2.2) * 0.42, colour = style_color(display_payload, "model_curve", "primary", "#1F4E79")) +
    geom_point(size = style_numeric(style_stroke(display_payload), "marker_size", 4.5) * 0.62, colour = style_color(display_payload, "model_curve", "primary", "#1F4E79")) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = ""
    ) +
    theme_publication(display_payload)
  plot
}

box_record <- function(box_id, box_type, x0, y0, x1, y1) {
  list(
    box_id = box_id,
    box_type = box_type,
    x0 = as.numeric(x0),
    y0 = as.numeric(y0),
    x1 = as.numeric(x1),
    y1 = as.numeric(y1)
  )
}

layout_box_from_indices <- function(widths, heights, left, right, top, bottom, box_id, box_type) {
  x0 <- if (left <= 1) 0 else sum(widths[seq_len(left - 1)])
  x1 <- sum(widths[seq_len(right)])
  y1 <- 1 - if (top <= 1) 0 else sum(heights[seq_len(top - 1)])
  y0 <- 1 - sum(heights[seq_len(bottom)])
  box_record(box_id, box_type, x0, y0, x1, y1)
}

find_layout_box <- function(gt, widths, heights, prefixes, box_id, box_type) {
  layout_names <- gt$layout$name
  layout_index <- integer(0)
  for (prefix in prefixes) {
    matches <- which(startsWith(layout_names, prefix))
    if (length(matches) > 0) {
      layout_index <- matches
      break
    }
  }
  if (length(layout_index) < 1) {
    return(NULL)
  }
  row <- gt$layout[layout_index[1], , drop = FALSE]
  layout_box_from_indices(widths, heights, row$l[[1]], row$r[[1]], row$t[[1]], row$b[[1]], box_id, box_type)
}

map_value_to_panel_x <- function(value, panel_box, x_min, x_max) {
  if (!is.finite(x_min) || !is.finite(x_max) || identical(x_min, x_max)) {
    return((panel_box$x0 + panel_box$x1) / 2)
  }
  span <- panel_box$x1 - panel_box$x0
  panel_box$x0 + ((value - x_min) / (x_max - x_min)) * span
}

map_row_to_panel_y <- function(row_index, row_count, panel_box) {
  row_height <- (panel_box$y1 - panel_box$y0) / max(row_count, 1)
  panel_box$y1 - ((row_index - 0.5) * row_height)
}

build_forest_layout <- function(display_payload, panel_box, axis_left_box) {
  rows <- display_payload$rows
  if (!is.list(rows) || length(rows) < 1) {
    return(list(layout_boxes = list(), guide_boxes = list(), metrics = list(rows = list())))
  }
  reference_value <- as.numeric(display_payload$reference_value %||% 1.0)
  lower_values <- vapply(rows, function(item) as.numeric(item$lower), numeric(1))
  estimate_values <- vapply(rows, function(item) as.numeric(item$estimate), numeric(1))
  upper_values <- vapply(rows, function(item) as.numeric(item$upper), numeric(1))
  x_min <- min(c(lower_values, estimate_values, upper_values, reference_value), na.rm = TRUE)
  x_max <- max(c(lower_values, estimate_values, upper_values, reference_value), na.rm = TRUE)
  if (identical(x_min, x_max)) {
    x_min <- x_min - 0.5
    x_max <- x_max + 0.5
  }
  row_count <- length(rows)
  label_box <- axis_left_box %||% box_record("axis_left", "axis_left", 0.02, panel_box$y0, max(0.03, panel_box$x0 - 0.04), panel_box$y1)
  row_height <- (panel_box$y1 - panel_box$y0) / max(row_count, 1) * 0.55
  layout_boxes <- list()
  metric_rows <- list()
  for (index in seq_along(rows)) {
    row <- rows[[index]]
    row_center <- map_row_to_panel_y(index, row_count, panel_box)
    lower_x <- map_value_to_panel_x(as.numeric(row$lower), panel_box, x_min, x_max)
    estimate_x <- map_value_to_panel_x(as.numeric(row$estimate), panel_box, x_min, x_max)
    upper_x <- map_value_to_panel_x(as.numeric(row$upper), panel_box, x_min, x_max)
    layout_boxes[[length(layout_boxes) + 1]] <- box_record(
      sprintf("row_label_%d", index),
      "row_label",
      label_box$x0,
      row_center - row_height / 2,
      label_box$x1,
      row_center + row_height / 2
    )
    layout_boxes[[length(layout_boxes) + 1]] <- box_record(
      sprintf("estimate_marker_%d", index),
      "estimate_marker",
      estimate_x - 0.01,
      row_center - row_height / 4,
      estimate_x + 0.01,
      row_center + row_height / 4
    )
    layout_boxes[[length(layout_boxes) + 1]] <- box_record(
      sprintf("ci_segment_%d", index),
      "ci_segment",
      lower_x,
      row_center,
      upper_x,
      row_center
    )
    metric_rows[[length(metric_rows) + 1]] <- list(
      row_id = trimws(as.character(row$label %||% sprintf("row_%d", index))),
      label = trimws(as.character(row$label %||% "")),
      lower = as.numeric(row$lower),
      estimate = as.numeric(row$estimate),
      upper = as.numeric(row$upper)
    )
  }
  reference_x <- map_value_to_panel_x(reference_value, panel_box, x_min, x_max)
  guide_boxes <- list(
    box_record("reference_line", "reference_line", reference_x, panel_box$y0, reference_x, panel_box$y1)
  )
  list(layout_boxes = layout_boxes, guide_boxes = guide_boxes, metrics = list(rows = metric_rows))
}

build_embedding_metrics <- function(display_payload, panel_box) {
  points <- display_payload$points
  if (is.null(panel_box) || !is.list(points) || length(points) < 1) {
    return(list(points = list()))
  }
  x_values <- vapply(points, function(item) as.numeric(item$x), numeric(1))
  y_values <- vapply(points, function(item) as.numeric(item$y), numeric(1))
  x_min <- min(x_values)
  x_max <- max(x_values)
  y_min <- min(y_values)
  y_max <- max(y_values)
  if (identical(x_min, x_max)) {
    x_min <- x_min - 0.5
    x_max <- x_max + 0.5
  }
  if (identical(y_min, y_max)) {
    y_min <- y_min - 0.5
    y_max <- y_max + 0.5
  }
  point_metrics <- lapply(points, function(item) {
    list(
      x = map_value_to_panel_x(as.numeric(item$x), panel_box, x_min, x_max),
      y = panel_box$y0 + ((as.numeric(item$y) - y_min) / (y_max - y_min)) * (panel_box$y1 - panel_box$y0),
      group = trimws(as.character(item$group %||% ""))
    )
  })
  list(points = point_metrics)
}

build_metrics <- function(template_id, display_payload, panel_box) {
  switch(
    template_id,
    roc_curve_binary = list(series = display_payload$series, reference_line = display_payload$reference_line),
    pr_curve_binary = list(series = display_payload$series, reference_line = display_payload$reference_line),
    calibration_curve_binary = list(series = display_payload$series, reference_line = display_payload$reference_line),
    decision_curve_binary = list(series = display_payload$series, reference_line = display_payload$reference_line),
    clinical_impact_curve_binary = list(series = display_payload$series, reference_line = display_payload$reference_line),
    time_dependent_roc_horizon = list(
      series = display_payload$series,
      reference_line = display_payload$reference_line,
      title = trimws(as.character(display_payload$title %||% "")),
      caption = trimws(as.character(display_payload$caption %||% "")),
      time_horizon_months = if (!is.null(display_payload$time_horizon_months)) as.integer(display_payload$time_horizon_months) else NULL
    ),
    kaplan_meier_grouped = list(
      groups = display_payload$groups,
      annotation = trimws(as.character(display_payload$annotation %||% ""))
    ),
    cumulative_incidence_grouped = list(
      groups = display_payload$groups,
      annotation = trimws(as.character(display_payload$annotation %||% ""))
    ),
    umap_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    pca_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    phate_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    tsne_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    diffusion_map_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    heatmap_group_comparison = list(metric_scope = "heatmap_group_comparison"),
    performance_heatmap = list(
      matrix_cells = display_payload$cells,
      metric_name = trimws(as.character(display_payload$metric_name %||% ""))
    ),
    confusion_matrix_heatmap_binary = list(
      matrix_cells = display_payload$cells,
      metric_name = trimws(as.character(display_payload$metric_name %||% "")),
      normalization = trimws(as.character(display_payload$normalization %||% ""))
    ),
    correlation_heatmap = list(matrix_cells = display_payload$cells),
    clustered_heatmap = list(matrix_cells = display_payload$cells),
    gsva_ssgsea_heatmap = list(
      matrix_cells = display_payload$cells,
      score_method = trimws(as.character(display_payload$score_method %||% ""))
    ),
    forest_effect_main = list(rows = display_payload$rows),
    subgroup_forest = list(rows = display_payload$rows),
    multivariable_forest = list(rows = display_payload$rows),
    if (exists("build_candidate_metrics", mode = "function")) {
      build_candidate_metrics(template_id, display_payload, panel_box)
    } else {
      list()
    }
  )
}

style_profile_sidecar <- function(display_payload) {
  render_context <- render_context_from_payload(display_payload)
  palette <- render_context$palette %||% list()
  list(
    style_profile_id = render_context$style_profile_id %||% "",
    style_profile_ref = render_context$style_profile_ref %||% "",
    style_profile_sha256 = render_context$style_profile_sha256 %||% "",
    journal_palette_ref = render_context$journal_palette_ref %||% "",
    palette_keys = names(palette),
    semantic_roles = render_context$semantic_roles %||% list(),
    typography = render_context$typography %||% list(),
    stroke = render_context$stroke %||% list(),
    grid = render_context$grid %||% list()
  )
}

build_layout_sidecar <- function(plot, template_id, display_payload) {
  tmp_pdf <- tempfile(fileext = ".pdf")
  grDevices::pdf(tmp_pdf, width = 7.2, height = 5.0)
  on.exit({
    grDevices::dev.off()
    unlink(tmp_pdf)
  }, add = TRUE)
  gt <- ggplotGrob(plot)
  grid::grid.newpage()
  grid::grid.draw(gt)
  grid::grid.force()
  widths <- grid::convertWidth(gt$widths, "npc", valueOnly = TRUE)
  heights <- grid::convertHeight(gt$heights, "npc", valueOnly = TRUE)
  title_box <- find_layout_box(gt, widths, heights, c("title"), "title", "title")
  x_axis_title_box <- find_layout_box(gt, widths, heights, c("xlab-b"), "x_axis_title", "x_axis_title")
  y_axis_title_box <- find_layout_box(gt, widths, heights, c("ylab-l"), "y_axis_title", "y_axis_title")
  panel_box <- find_layout_box(
    gt,
    widths,
    heights,
    c("panel"),
    "panel",
    if (template_id %in% c("heatmap_group_comparison", "performance_heatmap", "confusion_matrix_heatmap_binary", "correlation_heatmap", "clustered_heatmap", "gsva_ssgsea_heatmap")) "heatmap_tile_region" else "panel"
  )
  guide_box <- find_layout_box(
    gt,
    widths,
    heights,
    c("guide-box"),
    if (template_id %in% c("heatmap_group_comparison", "performance_heatmap", "confusion_matrix_heatmap_binary", "correlation_heatmap", "clustered_heatmap", "gsva_ssgsea_heatmap")) "colorbar" else "legend",
    if (template_id %in% c("heatmap_group_comparison", "performance_heatmap", "confusion_matrix_heatmap_binary", "correlation_heatmap", "clustered_heatmap", "gsva_ssgsea_heatmap")) "colorbar" else "legend"
  )
  axis_left_box <- find_layout_box(gt, widths, heights, c("axis-l"), "axis_left", "axis_left")
  layout_boxes <- Filter(Negate(is.null), list(title_box, x_axis_title_box, y_axis_title_box))
  guide_boxes <- Filter(Negate(is.null), list(guide_box))
  metrics <- build_metrics(template_id, display_payload, panel_box)
  if (template_id %in% c("forest_effect_main", "subgroup_forest", "multivariable_forest") && !is.null(panel_box)) {
    forest_layout <- build_forest_layout(display_payload, panel_box, axis_left_box)
    layout_boxes <- c(layout_boxes, forest_layout$layout_boxes)
    guide_boxes <- c(guide_boxes, forest_layout$guide_boxes)
    metrics <- forest_layout$metrics
  }
  list(
    template_id = template_id,
    device = list(x0 = 0.0, y0 = 0.0, x1 = 1.0, y1 = 1.0),
    layout_boxes = layout_boxes,
    panel_boxes = Filter(Negate(is.null), list(panel_box)),
    guide_boxes = guide_boxes,
    metrics = metrics,
    render_context = render_context_from_payload(display_payload),
    style_profile = style_profile_sidecar(display_payload)
  )
}

build_evidence_plot <- function(template_id, payload) {
  switch(
    template_id,
    roc_curve_binary = plot_binary_curve(payload),
    pr_curve_binary = plot_binary_curve(payload),
    calibration_curve_binary = plot_binary_curve(payload),
    decision_curve_binary = plot_binary_curve(payload),
    clinical_impact_curve_binary = plot_binary_curve(payload),
    time_dependent_roc_horizon = plot_binary_curve(payload),
    kaplan_meier_grouped = plot_kaplan_meier(payload),
    cumulative_incidence_grouped = plot_kaplan_meier(payload),
    umap_scatter_grouped = plot_embedding_scatter(payload),
    pca_scatter_grouped = plot_embedding_scatter(payload),
    phate_scatter_grouped = plot_embedding_scatter(payload),
    tsne_scatter_grouped = plot_embedding_scatter(payload),
    diffusion_map_scatter_grouped = plot_embedding_scatter(payload),
    heatmap_group_comparison = plot_heatmap(payload),
    performance_heatmap = plot_performance_heatmap(payload),
    confusion_matrix_heatmap_binary = plot_confusion_matrix_heatmap(payload),
    correlation_heatmap = plot_heatmap(payload),
    clustered_heatmap = plot_heatmap(payload),
    gsva_ssgsea_heatmap = plot_heatmap(payload),
    forest_effect_main = plot_forest(payload),
    subgroup_forest = plot_forest(payload),
    multivariable_forest = plot_forest(payload),
    if (exists("build_candidate_evidence_plot", mode = "function")) {
      build_candidate_evidence_plot(template_id, payload)
    } else {
      stop(sprintf("unsupported evidence template `%s`", template_id))
    }
  )
}

render_evidence_request <- function(request_path, expected_template_id = NULL) {
  request <- read_render_request(request_path)
  template_id <- normalize_template_id(request$short_template_id %||% request$template_id)
  if (!is.null(expected_template_id)) {
    expected <- normalize_template_id(expected_template_id)
    if (!identical(template_id, expected)) {
      stop(sprintf("render request template `%s` does not match expected template `%s`", template_id, expected))
    }
  }
  payload <- payload_from_request(request)
  output_png <- trimws(as.character(request$output_png_path %||% ""))
  output_pdf <- trimws(as.character(request$output_pdf_path %||% ""))
  output_layout <- trimws(as.character(request$layout_sidecar_path %||% ""))
  if (!nzchar(output_png) || !nzchar(output_pdf) || !nzchar(output_layout)) {
    stop("render request must contain output_png_path, output_pdf_path, and layout_sidecar_path")
  }
  dir.create(dirname(output_png), recursive = TRUE, showWarnings = FALSE)
  dir.create(dirname(output_pdf), recursive = TRUE, showWarnings = FALSE)
  dir.create(dirname(output_layout), recursive = TRUE, showWarnings = FALSE)
  plot <- build_evidence_plot(template_id, payload)
  layout_sidecar <- build_layout_sidecar(plot, template_id, payload)
  write_json(layout_sidecar, output_layout, auto_unbox = TRUE, pretty = TRUE, null = "null")
  ggsave(output_png, plot = plot, width = 7.2, height = 5.0, dpi = 320, units = "in", bg = "white")
  ggsave(output_pdf, plot = plot, width = 7.2, height = 5.0, units = "in", bg = "white")
  invisible(list(template_id = template_id, output_png_path = output_png, output_pdf_path = output_pdf, layout_sidecar_path = output_layout))
}

render_legacy_payload <- function(template_id, payload_path, output_png, output_pdf, output_layout) {
  payload <- fromJSON(payload_path, simplifyVector = FALSE)
  request <- list(
    short_template_id = template_id,
    display_payload = payload,
    output_png_path = output_png,
    output_pdf_path = output_pdf,
    layout_sidecar_path = output_layout
  )
  request_path <- tempfile(fileext = ".render_request.json")
  write_json(request, request_path, auto_unbox = TRUE, pretty = TRUE, null = "null")
  on.exit(unlink(request_path), add = TRUE)
  render_evidence_request(request_path, expected_template_id = template_id)
}

if (!identical(Sys.getenv("MAS_DISPLAY_RENDERER_SOURCE_ONLY", unset = ""), "1")) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) == 0) {
    invisible(NULL)
  } else if (length(args) == 2 && identical(args[[1]], "--request")) {
    render_evidence_request(args[[2]])
  } else if (length(args) == 5) {
    render_legacy_payload(args[[1]], args[[2]], args[[3]], args[[4]], args[[5]])
  } else {
    stop("expected args: --request <request_json> or <template_id> <payload_json> <output_png> <output_pdf> <output_layout>")
  }
}
