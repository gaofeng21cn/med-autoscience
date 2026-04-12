from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from .shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _build_python_shap_layout_sidecar,
    _centered_offsets,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _normalize_reference_line_collection_to_device_space,
    _normalize_reference_line_to_device_space,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_namespaced_registry_id,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
    dump_json,
    load_json,
)
_R_EVIDENCE_RENDERER_SOURCE = r"""
suppressPackageStartupMessages({
  library(jsonlite)
  library(ggplot2)
  library(ggsci)
  library(grid)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 5) {
  stop("expected args: <template_id> <payload_json> <output_png> <output_pdf> <output_layout>")
}

template_id <- args[[1]]
payload_path <- args[[2]]
output_png <- args[[3]]
output_pdf <- args[[4]]
output_layout <- args[[5]]

payload <- fromJSON(payload_path, simplifyVector = FALSE)

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

theme_publication <- function() {
  theme_bw(base_size = 11) +
    theme(
      plot.title = element_text(face = "bold", colour = "#13293d", size = 12.5),
      axis.title = element_text(face = "bold", colour = "#13293d"),
      legend.position = "bottom",
      legend.title = element_blank(),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(colour = "#e6edf2", linewidth = 0.25)
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
    geom_line(linewidth = 0.9) +
    coord_cartesian(xlim = c(0, 1), ylim = c(min(curve_df$y, 0), max(curve_df$y, 1))) +
    scale_color_lancet() +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication()
  if (!is.null(reference_df)) {
    plot <- plot + geom_line(
      data = reference_df,
      aes(x = x, y = y),
      inherit.aes = FALSE,
      colour = "#6b7280",
      linewidth = 0.6,
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
    geom_step(linewidth = 0.9, direction = "hv") +
    coord_cartesian(xlim = c(0, max(curve_df$x)), ylim = c(0, 1)) +
    scale_color_lancet() +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication()
  annotation <- trimws(as.character(display_payload$annotation %||% ""))
  if (nzchar(annotation)) {
    plot <- plot + annotate(
      "text",
      x = max(curve_df$x) * 0.98,
      y = 0.08,
      label = annotation,
      hjust = 1,
      vjust = 0,
      size = 3.3,
      colour = "#13293d"
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
    geom_point(size = 2.8, alpha = 0.9) +
    scale_color_lancet() +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication()
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
    geom_text(aes(label = sprintf("%.2f", value)), size = 3.1, colour = "#13293d") +
    scale_fill_gradient2(low = "#2166ac", mid = "white", high = "#b2182b", midpoint = 0) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication() +
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
    geom_text(aes(label = sprintf("%.2f", value)), size = 3.1, colour = "#13293d") +
    scale_fill_gradient2(
      low = "#2166ac",
      mid = "white",
      high = "#b2182b",
      midpoint = 0.5,
      limits = c(0, 1),
      name = metric_name
    ) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = trimws(as.character(display_payload$y_label %||% ""))
    ) +
    theme_publication() +
    theme(axis.text.x = element_text(angle = 25, hjust = 1))
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
    geom_vline(xintercept = reference_value, colour = "#6b7280", linewidth = 0.6, linetype = "dashed") +
    geom_segment(aes(x = lower, xend = upper, y = label, yend = label), linewidth = 0.9, colour = "#1f4e79") +
    geom_point(size = 2.8, colour = "#1f4e79") +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% "")),
      y = ""
    ) +
    theme_publication()
  plot
}

`%||%` <- function(left, right) {
  if (is.null(left)) right else left
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
    tsne_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    heatmap_group_comparison = list(metric_scope = "heatmap_group_comparison"),
    performance_heatmap = list(
      matrix_cells = display_payload$cells,
      metric_name = trimws(as.character(display_payload$metric_name %||% ""))
    ),
    correlation_heatmap = list(matrix_cells = display_payload$cells),
    clustered_heatmap = list(matrix_cells = display_payload$cells),
    gsva_ssgsea_heatmap = list(
      matrix_cells = display_payload$cells,
      score_method = trimws(as.character(display_payload$score_method %||% ""))
    ),
    forest_effect_main = list(rows = display_payload$rows),
    subgroup_forest = list(rows = display_payload$rows),
    list()
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
    if (template_id %in% c("heatmap_group_comparison", "performance_heatmap", "correlation_heatmap", "clustered_heatmap", "gsva_ssgsea_heatmap")) "heatmap_tile_region" else "panel"
  )
  guide_box <- find_layout_box(
    gt,
    widths,
    heights,
    c("guide-box"),
    if (template_id %in% c("heatmap_group_comparison", "performance_heatmap", "correlation_heatmap", "clustered_heatmap", "gsva_ssgsea_heatmap")) "colorbar" else "legend",
    if (template_id %in% c("heatmap_group_comparison", "performance_heatmap", "correlation_heatmap", "clustered_heatmap", "gsva_ssgsea_heatmap")) "colorbar" else "legend"
  )
  axis_left_box <- find_layout_box(gt, widths, heights, c("axis-l"), "axis_left", "axis_left")
  layout_boxes <- Filter(Negate(is.null), list(title_box, x_axis_title_box, y_axis_title_box))
  guide_boxes <- Filter(Negate(is.null), list(guide_box))
  metrics <- build_metrics(template_id, display_payload, panel_box)
  if (template_id %in% c("forest_effect_main", "subgroup_forest") && !is.null(panel_box)) {
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
    metrics = metrics
  )
}

plot <- switch(
  template_id,
  roc_curve_binary = plot_binary_curve(payload),
  pr_curve_binary = plot_binary_curve(payload),
  calibration_curve_binary = plot_binary_curve(payload),
  decision_curve_binary = plot_binary_curve(payload),
  time_dependent_roc_horizon = plot_binary_curve(payload),
  kaplan_meier_grouped = plot_kaplan_meier(payload),
  cumulative_incidence_grouped = plot_kaplan_meier(payload),
  umap_scatter_grouped = plot_embedding_scatter(payload),
  pca_scatter_grouped = plot_embedding_scatter(payload),
  tsne_scatter_grouped = plot_embedding_scatter(payload),
  heatmap_group_comparison = plot_heatmap(payload),
  performance_heatmap = plot_performance_heatmap(payload),
  correlation_heatmap = plot_heatmap(payload),
  clustered_heatmap = plot_heatmap(payload),
  gsva_ssgsea_heatmap = plot_heatmap(payload),
  forest_effect_main = plot_forest(payload),
  subgroup_forest = plot_forest(payload),
  stop(sprintf("unsupported evidence template `%s`", template_id))
)

layout_sidecar <- build_layout_sidecar(plot, template_id, payload)
write_json(layout_sidecar, output_layout, auto_unbox = TRUE, pretty = TRUE, null = "null")

ggsave(output_png, plot = plot, width = 7.2, height = 5.0, dpi = 320, units = "in", bg = "white")
ggsave(output_pdf, plot = plot, width = 7.2, height = 5.0, units = "in", bg = "white")
"""

def _render_r_evidence_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    rscript = shutil.which("Rscript")
    if rscript is None:
        raise RuntimeError("Rscript not found on PATH; required for r_ggplot2 evidence figure materialization")

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    layout_sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    _, template_short_id = _require_namespaced_registry_id(template_id, label="template_id")

    with tempfile.TemporaryDirectory(prefix="medautosci-evidence-") as tmpdir:
        tmpdir_path = Path(tmpdir)
        payload_path = tmpdir_path / "display_payload.json"
        script_path = tmpdir_path / "render_evidence_figure.R"
        payload_path.write_text(json.dumps(display_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        script_path.write_text(_R_EVIDENCE_RENDERER_SOURCE, encoding="utf-8")
        completed = subprocess.run(
            [
                rscript,
                str(script_path),
                template_short_id,
                str(payload_path),
                str(output_png_path),
                str(output_pdf_path),
                str(layout_sidecar_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"R evidence renderer failed for `{template_id}`: {stderr or 'unknown R error'}")
    missing_outputs = [str(path) for path in (output_png_path, output_pdf_path, layout_sidecar_path) if not path.exists()]
    if missing_outputs:
        raise RuntimeError(
            f"R evidence renderer did not produce required exports for `{template_id}`: {', '.join(missing_outputs)}"
        )

def _render_python_risk_layering_monotonic_bars(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    left_bars = list(display_payload.get("left_bars") or [])
    right_bars = list(display_payload.get("right_bars") or [])
    if not left_bars or not right_bars:
        raise RuntimeError(f"{template_id} requires non-empty left_bars and right_bars")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_subplot_titles = _read_bool_override(layout_override, "show_subplot_titles", True)
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = str(style_roles.get("reference_line") or "#6b7280").strip() or "#6b7280"
    comparator_fill = str(palette.get("secondary_soft") or "").strip() or comparator_color
    model_fill = str(palette.get("primary_soft") or "").strip() or model_color

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.2, 4.5), sharey=True)
    fig.patch.set_facecolor("white")
    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )
    wrapped_y_label, _ = _wrap_figure_title_to_width(
        str(display_payload.get("y_label") or "").strip(),
        max_width_pt=fig.get_figheight() * 72.0 * 0.72,
        font_size=axis_title_size,
    )

    max_risk_pct = max(
        max(float(item["risk"]) for item in left_bars),
        max(float(item["risk"]) for item in right_bars),
    ) * 100.0
    upper_margin = max(max_risk_pct * 0.18, 6.0)
    y_upper = max_risk_pct + upper_margin

    def _draw_panel(
        *,
        axes,
        bars_payload: list[dict[str, Any]],
        panel_title: str,
        x_label: str,
        fill_color: str,
        edge_color: str,
        panel_label: str,
    ) -> list[Any]:
        labels = [str(item["label"]) for item in bars_payload]
        risks = [float(item["risk"]) * 100.0 for item in bars_payload]
        bar_artists = axes.bar(
            labels,
            risks,
            width=0.64,
            color=matplotlib.colors.to_rgba(fill_color, alpha=0.88),
            edgecolor=edge_color,
            linewidth=1.2,
            zorder=3,
        )
        axes.set_ylim(0.0, y_upper)
        axes.set_xlabel(x_label, fontsize=axis_title_size, fontweight="bold", color="#13293d")
        if show_subplot_titles:
            axes.set_title(panel_title, fontsize=axis_title_size, fontweight="bold", color="#334155", pad=10)
        axes.tick_params(axis="x", labelsize=tick_size)
        axes.tick_params(axis="y", labelsize=tick_size)
        axes.axhline(0.0, color=reference_color, linewidth=0.8, zorder=1)
        _apply_publication_axes_style(axes)
        axes.grid(axis="y", color="#d8d1c7", linewidth=0.8, linestyle=":", zorder=0)
        axes.text(
            -0.09,
            1.04,
            panel_label,
            transform=axes.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#2F3437",
            va="bottom",
        )
        for index, (artist, bar_payload) in enumerate(zip(bar_artists, bars_payload, strict=True)):
            risk_pct = float(bar_payload["risk"]) * 100.0
            axes.text(
                float(artist.get_x()) + float(artist.get_width()) / 2.0,
                float(artist.get_height()) + upper_margin * 0.12,
                f"{risk_pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=max(tick_size - 1.0, 8.0),
                color=edge_color,
            )
        return list(bar_artists)

    left_bar_artists = _draw_panel(
        axes=left_axes,
        bars_payload=left_bars,
        panel_title=str(display_payload.get("left_panel_title") or "").strip(),
        x_label=str(display_payload.get("left_x_label") or "").strip(),
        fill_color=comparator_fill,
        edge_color=comparator_color,
        panel_label="A",
    )
    right_bar_artists = _draw_panel(
        axes=right_axes,
        bars_payload=right_bars,
        panel_title=str(display_payload.get("right_panel_title") or "").strip(),
        x_label=str(display_payload.get("right_x_label") or "").strip(),
        fill_color=model_fill,
        edge_color=model_color,
        panel_label="B",
    )
    left_axes.set_ylabel(
        wrapped_y_label,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )

    title_top = 0.83 - 0.08 * max(title_line_count - 1, 0)
    top_margin = max(0.68, title_top) if show_figure_title else 0.90
    if not show_subplot_titles:
        top_margin = min(0.94, top_margin + 0.02)
    fig.subplots_adjust(left=0.10, right=0.98, top=top_margin, bottom=0.20, wspace=0.18)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    for index, artist in enumerate(left_bar_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"left_risk_bar_{index}",
                box_type="risk_bar",
            )
        )
    for index, artist in enumerate(right_bar_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"right_risk_bar_{index}",
                box_type="risk_bar",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=left_axes.get_window_extent(renderer=renderer),
                    box_id="panel_left",
                    box_type="panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_axes.get_window_extent(renderer=renderer),
                    box_id="panel_right",
                    box_type="panel",
                ),
            ],
            "guide_boxes": [],
            "metrics": {
                "left_bars": left_bars,
                "right_bars": right_bars,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_binary_calibration_decision_curve_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    calibration_series = list(display_payload.get("calibration_series") or [])
    decision_series = list(display_payload.get("decision_series") or [])
    decision_reference_lines = list(display_payload.get("decision_reference_lines") or [])
    decision_focus_window = dict(display_payload.get("decision_focus_window") or {})
    if not calibration_series or not decision_series or not decision_reference_lines:
        raise RuntimeError(
            f"{template_id} requires non-empty calibration_series, decision_series, and decision_reference_lines"
        )

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
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    primary_linewidth = float(stroke.get("primary_linewidth") or 2.2)
    secondary_linewidth = float(stroke.get("secondary_linewidth") or 1.8)
    marker_size = float(stroke.get("marker_size") or 4.5)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_subplot_titles = _read_bool_override(layout_override, "show_subplot_titles", True)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    highlight_band_color = str(palette.get("light") or palette.get("secondary_soft") or "#E7E1D8").strip() or "#E7E1D8"
    fallback_palette = [
        str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F",
        str(palette.get("neutral") or "#7B8794").strip() or "#7B8794",
        str(palette.get("secondary") or "#B9AD9C").strip() or "#B9AD9C",
    ]

    def _series_color(index: int) -> str:
        if index == 0:
            return comparator_color
        if index == 1:
            return model_color
        return fallback_palette[(index - 2) % len(fallback_palette)]

    fig, (calibration_axes, decision_axes) = plt.subplots(1, 2, figsize=(10.8, 4.9))
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
            y=0.982,
        )

    calibration_title = None
    if show_subplot_titles:
        calibration_title = calibration_axes.set_title(
            "Calibration",
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10,
        )
    calibration_axes.text(
        -0.11,
        1.04,
        "A",
        transform=calibration_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color="#2F3437",
        va="bottom",
    )

    calibration_handles: list[Any] = []
    calibration_labels: list[str] = []
    for index, item in enumerate(calibration_series):
        (line_artist,) = calibration_axes.plot(
            item["x"],
            item["y"],
            linewidth=primary_linewidth if index == 1 else secondary_linewidth,
            marker="o",
            markersize=max(marker_size - 0.4, 3.6),
            color=_series_color(index),
            label=str(item["label"]),
            zorder=3,
        )
        calibration_handles.append(line_artist)
        calibration_labels.append(str(item["label"]))
    calibration_reference_line = display_payload.get("calibration_reference_line")
    if isinstance(calibration_reference_line, dict):
        (reference_artist,) = calibration_axes.plot(
            calibration_reference_line["x"],
            calibration_reference_line["y"],
            linewidth=1.1,
            linestyle="--",
            color=reference_color,
            label=str(calibration_reference_line.get("label") or ""),
            zorder=2,
        )
        calibration_handles.append(reference_artist)
        calibration_labels.append(str(calibration_reference_line.get("label") or ""))

    calibration_axis_window = display_payload.get("calibration_axis_window")
    if isinstance(calibration_axis_window, dict):
        calibration_x_lower = float(calibration_axis_window["xmin"])
        calibration_x_upper = float(calibration_axis_window["xmax"])
        calibration_y_lower = float(calibration_axis_window["ymin"])
        calibration_y_upper = float(calibration_axis_window["ymax"])
    else:
        calibration_x_values = [
            float(value) for item in calibration_series for value in item["x"]
        ] + [float(value) for value in (calibration_reference_line or {}).get("x", [])]
        calibration_y_values = [
            float(value) for item in calibration_series for value in item["y"]
        ] + [float(value) for value in (calibration_reference_line or {}).get("y", [])]
        calibration_x_lower = min(0.0, min(calibration_x_values, default=0.0))
        calibration_x_upper = max(1.0, max(calibration_x_values, default=1.0))
        calibration_y_lower = min(0.0, min(calibration_y_values, default=0.0))
        calibration_y_upper = max(1.0, max(calibration_y_values, default=1.0))
    calibration_axes.set_xlim(calibration_x_lower, calibration_x_upper)
    calibration_axes.set_ylim(calibration_y_lower, calibration_y_upper)
    calibration_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    calibration_axes.set_ylabel(
        str(display_payload.get("calibration_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    calibration_axes.tick_params(axis="both", labelsize=tick_size)
    _apply_publication_axes_style(calibration_axes)
    calibration_axes.grid(axis="both", color="#e6edf2", linewidth=0.45, linestyle=":")

    decision_title = None
    if show_subplot_titles:
        decision_title = decision_axes.set_title(
            "Decision curve",
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10,
        )
    decision_axes.text(
        -0.11,
        1.04,
        "B",
        transform=decision_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color="#2F3437",
        va="bottom",
    )

    focus_xmin = float(decision_focus_window["xmin"])
    focus_xmax = float(decision_focus_window["xmax"])
    decision_axes.axvspan(
        focus_xmin,
        focus_xmax,
        color=highlight_band_color,
        alpha=0.22,
        zorder=0,
    )

    decision_handles: list[Any] = []
    decision_labels: list[str] = []
    for reference_index, item in enumerate(decision_reference_lines):
        (line_artist,) = decision_axes.plot(
            item["x"],
            item["y"],
            linewidth=1.0,
            linestyle="--" if reference_index == 0 else "-.",
            color=reference_color,
            label=str(item["label"]),
            zorder=1,
        )
        decision_handles.append(line_artist)
        decision_labels.append(str(item["label"]))
    for index, item in enumerate(decision_series):
        (line_artist,) = decision_axes.plot(
            item["x"],
            item["y"],
            linewidth=primary_linewidth if index == 1 else secondary_linewidth,
            color=_series_color(index),
            label=str(item["label"]),
            zorder=3,
        )
        decision_handles.append(line_artist)
        decision_labels.append(str(item["label"]))

    decision_x_values = [float(value) for item in decision_series for value in item["x"]]
    decision_y_values = [float(value) for item in decision_series for value in item["y"]]
    decision_x_values.extend(float(value) for item in decision_reference_lines for value in item["x"])
    decision_y_values.extend(float(value) for item in decision_reference_lines for value in item["y"])
    decision_x_lower = min(focus_xmin, min(decision_x_values))
    decision_x_upper = max(focus_xmax, max(decision_x_values))
    decision_x_padding = max((decision_x_upper - decision_x_lower) * 0.03, 0.005)
    decision_y_lower = min(decision_y_values)
    decision_y_upper = max(decision_y_values)
    decision_y_padding = max((decision_y_upper - decision_y_lower) * 0.12, 0.01)
    decision_axes.set_xlim(decision_x_lower - decision_x_padding, decision_x_upper + decision_x_padding)
    decision_axes.set_ylim(decision_y_lower - decision_y_padding, decision_y_upper + decision_y_padding)
    decision_axes.set_xlabel(
        str(display_payload.get("decision_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    decision_axes.set_ylabel(
        str(display_payload.get("decision_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    decision_axes.tick_params(axis="both", labelsize=tick_size)
    _apply_publication_axes_style(decision_axes)
    decision_axes.grid(axis="both", color="#e6edf2", linewidth=0.45, linestyle=":")

    legend_handles: list[Any] = []
    legend_labels: list[str] = []
    for handle, label in [*zip(calibration_handles, calibration_labels, strict=True), *zip(decision_handles, decision_labels, strict=True)]:
        if label in legend_labels:
            continue
        legend_handles.append(handle)
        legend_labels.append(label)
    legend_columns = min(4, max(2, len(legend_labels)))
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=legend_columns,
        frameon=False,
        fontsize=max(tick_size - 0.5, 8.5),
        handlelength=2.4,
        columnspacing=1.3,
    )

    title_top = 0.84 - 0.06 * max(title_line_count - 1, 0)
    top_margin = max(0.70, title_top) if show_figure_title else 0.90
    if not show_subplot_titles:
        top_margin = min(0.94, top_margin + 0.02)
    fig.subplots_adjust(left=0.09, right=0.98, top=top_margin, bottom=0.23, wspace=0.22)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    resolved_calibration_xmin, resolved_calibration_xmax = (
        float(value) for value in calibration_axes.get_xlim()
    )
    resolved_calibration_ymin, resolved_calibration_ymax = (
        float(value) for value in calibration_axes.get_ylim()
    )

    decision_ymin, decision_ymax = decision_axes.get_ylim()
    focus_window_box = _data_box_to_layout_box(
        axes=decision_axes,
        figure=fig,
        x0=focus_xmin,
        y0=decision_ymin,
        x1=focus_xmax,
        y1=decision_ymax,
        box_id="decision_focus_window",
        box_type="focus_window",
    )
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=calibration_axes.xaxis.label.get_window_extent(renderer=renderer),
                    box_id="calibration_x_axis_title",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=calibration_axes.yaxis.label.get_window_extent(renderer=renderer),
                    box_id="calibration_y_axis_title",
                    box_type="subplot_y_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=decision_axes.xaxis.label.get_window_extent(renderer=renderer),
                    box_id="decision_x_axis_title",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=decision_axes.yaxis.label.get_window_extent(renderer=renderer),
                    box_id="decision_y_axis_title",
                    box_type="subplot_y_axis_title",
                ),
            ],
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=calibration_axes.get_window_extent(renderer=renderer),
                    box_id="calibration_panel",
                    box_type="calibration_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=decision_axes.get_window_extent(renderer=renderer),
                    box_id="decision_panel",
                    box_type="decision_panel",
                ),
            ],
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                ),
                focus_window_box,
            ],
            "metrics": {
                "calibration_axis_window": {
                    "xmin": resolved_calibration_xmin,
                    "xmax": resolved_calibration_xmax,
                    "ymin": resolved_calibration_ymin,
                    "ymax": resolved_calibration_ymax,
                },
                "calibration_series": calibration_series,
                "calibration_reference_line": _normalize_reference_line_to_device_space(
                    reference_line=calibration_reference_line,
                    axes=calibration_axes,
                    figure=fig,
                    clip_to_axes_window=True,
                ),
                "decision_series": decision_series,
                "decision_reference_lines": _normalize_reference_line_collection_to_device_space(
                    reference_lines=decision_reference_lines,
                    axes=decision_axes,
                    figure=fig,
                ),
                "decision_focus_window": {
                    "xmin": focus_xmin,
                    "xmax": focus_xmax,
                },
            },
        },
    )
    layout_boxes = load_json(layout_sidecar_path)["layout_boxes"]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    if calibration_title is not None:
        layout_boxes.insert(
            1 if title_artist is not None else 0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=calibration_title.get_window_extent(renderer=renderer),
                box_id="calibration_subplot_title",
                box_type="subplot_title",
            ),
        )
    if decision_title is not None:
        insert_index = 1 if title_artist is not None else 0
        if calibration_title is not None:
            insert_index += 1
        layout_boxes.insert(
            insert_index,
            _bbox_to_layout_box(
                figure=fig,
                bbox=decision_title.get_window_extent(renderer=renderer),
                box_id="decision_subplot_title",
                box_type="subplot_title",
            ),
        )
    sidecar_payload = load_json(layout_sidecar_path)
    sidecar_payload["layout_boxes"] = layout_boxes
    dump_json(layout_sidecar_path, sidecar_payload)
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_model_complexity_audit_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    metric_panels = list(display_payload.get("metric_panels") or [])
    audit_panels = list(display_payload.get("audit_panels") or [])
    if not metric_panels or not audit_panels:
        raise RuntimeError(f"{template_id} requires non-empty metric_panels and audit_panels")

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
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = float(stroke.get("marker_size") or 4.5)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_subplot_titles = _read_bool_override(layout_override, "show_subplot_titles", True)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    metric_fill = str(palette.get("primary_soft") or "#EEF3F1").strip() or "#EEF3F1"
    audit_fill = str(palette.get("secondary_soft") or "#F4EFE8").strip() or "#F4EFE8"

    max_row_count = max(
        max((len(panel.get("rows") or []) for panel in metric_panels), default=1),
        max((len(panel.get("rows") or []) for panel in audit_panels), default=1),
    )
    figure_height = max(7.8, 0.52 * max_row_count + 3.6)
    fig = plt.figure(figsize=(12.4, figure_height))
    fig.patch.set_facecolor("white")
    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.86,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    outer = fig.add_gridspec(1, 2, width_ratios=[1.06, 0.94], wspace=0.60)
    left_grid = outer[0, 0].subgridspec(
        len(metric_panels),
        1,
        hspace=0.70,
        height_ratios=[max(1, len(panel.get("rows") or [])) for panel in metric_panels],
    )
    right_grid = outer[0, 1].subgridspec(
        len(audit_panels),
        1,
        hspace=0.42,
        height_ratios=[max(1, len(panel.get("rows") or [])) for panel in audit_panels],
    )
    metric_axes = [fig.add_subplot(left_grid[index, 0]) for index in range(len(metric_panels))]
    audit_axes = [fig.add_subplot(right_grid[index, 0]) for index in range(len(audit_panels))]

    metric_title_artists: list[Any] = []
    audit_title_artists: list[Any] = []
    metric_reference_artists: list[Any] = []
    audit_reference_artists: list[Any] = []
    metric_marker_specs: list[tuple[Any, float, float]] = []
    audit_bar_artists: list[Any] = []

    def _panel_limits(rows: list[dict[str, Any]], *, reference_value: float | None) -> tuple[float, float]:
        values = [float(item["value"]) for item in rows]
        if reference_value is not None:
            values.append(float(reference_value))
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum
        padding = max(span * 0.14, 0.03 if maximum <= 1.5 else 0.12)
        if minimum >= 0.0:
            lower = max(0.0, minimum - padding)
        else:
            lower = minimum - padding
        upper = maximum + padding
        if upper <= lower:
            upper = lower + 1.0
        return lower, upper

    for panel_index, (axes, panel) in enumerate(zip(metric_axes, metric_panels, strict=True), start=1):
        rows = list(panel["rows"])
        values = [float(item["value"]) for item in rows]
        row_positions = list(range(len(rows)))
        lower_limit, upper_limit = _panel_limits(rows, reference_value=panel.get("reference_value"))
        if panel.get("reference_value") is not None:
            reference_artist = axes.axvline(
                float(panel["reference_value"]),
                color=reference_color,
                linewidth=1.0,
                linestyle="--",
                zorder=1,
            )
            metric_reference_artists.append(reference_artist)
        scatter_artist = axes.scatter(
            values,
            row_positions,
            s=max(marker_size, 4.2) ** 2,
            color=model_color,
            edgecolors="white",
            linewidths=0.8,
            zorder=3,
        )
        axes.hlines(
            row_positions,
            [lower_limit] * len(row_positions),
            values,
            color=matplotlib.colors.to_rgba(metric_fill, alpha=0.95),
            linewidth=2.1,
            zorder=2,
        )
        axes.set_xlim(lower_limit, upper_limit)
        axes.set_ylim(-0.6, len(rows) - 0.4)
        axes.set_yticks(row_positions)
        axes.set_yticklabels([str(item["label"]) for item in rows], fontsize=max(tick_size - 1.2, 8.2))
        axes.invert_yaxis()
        axes.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        panel_title_artist = None
        if show_subplot_titles:
            panel_title_artist = axes.set_title(
                str(panel["title"]),
                fontsize=axis_title_size,
                fontweight="bold",
                color="#334155",
                pad=8,
            )
        metric_title_artists.append(panel_title_artist)
        axes.text(
            -0.11,
            1.04,
            str(panel["panel_label"]),
            transform=axes.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#2F3437",
            va="bottom",
        )
        axes.tick_params(axis="x", labelsize=tick_size)
        axes.tick_params(axis="y", length=0, pad=6)
        _apply_publication_axes_style(axes)
        axes.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")
        x_radius = max((upper_limit - lower_limit) * 0.018, 0.01)
        for value, row_position in zip(values, row_positions, strict=True):
            metric_marker_specs.append((axes, float(value), float(row_position)))
        _ = scatter_artist

    for panel_index, (axes, panel) in enumerate(zip(audit_axes, audit_panels, strict=True), start=1):
        rows = list(panel["rows"])
        values = [float(item["value"]) for item in rows]
        row_positions = list(range(len(rows)))
        lower_limit, upper_limit = _panel_limits(rows, reference_value=panel.get("reference_value"))
        left_edge = 0.0 if lower_limit >= 0.0 else lower_limit
        bar_artists = axes.barh(
            row_positions,
            [value - left_edge for value in values],
            left=left_edge,
            height=0.66,
            color=matplotlib.colors.to_rgba(audit_fill, alpha=0.96),
            edgecolor=comparator_color,
            linewidth=1.0,
            zorder=2,
        )
        audit_bar_artists.extend(list(bar_artists))
        if panel.get("reference_value") is not None:
            reference_artist = axes.axvline(
                float(panel["reference_value"]),
                color=reference_color,
                linewidth=1.0,
                linestyle="--",
                zorder=1,
            )
            audit_reference_artists.append(reference_artist)
        axes.set_xlim(lower_limit, upper_limit)
        axes.set_ylim(-0.6, len(rows) - 0.4)
        axes.set_yticks(row_positions)
        axes.set_yticklabels([str(item["label"]) for item in rows], fontsize=max(tick_size - 1.2, 8.2))
        axes.invert_yaxis()
        axes.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        panel_title_artist = None
        if show_subplot_titles:
            panel_title_artist = axes.set_title(
                str(panel["title"]),
                fontsize=axis_title_size,
                fontweight="bold",
                color="#334155",
                pad=8,
            )
        audit_title_artists.append(panel_title_artist)
        axes.text(
            -0.11,
            1.04,
            str(panel["panel_label"]),
            transform=axes.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#2F3437",
            va="bottom",
        )
        axes.tick_params(axis="x", labelsize=tick_size)
        axes.tick_params(axis="y", length=0, pad=6)
        _apply_publication_axes_style(axes)
        axes.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")

    top_value = 0.91 - 0.05 * max(title_line_count - 1, 0)
    top_margin = max(0.76, top_value) if show_figure_title else 0.95
    if not show_subplot_titles:
        top_margin = min(0.97, top_margin + 0.01)
    fig.subplots_adjust(left=0.28, right=0.98, top=top_margin, bottom=0.07)
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
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []

    for index, (axes, title_artist_item) in enumerate(zip(metric_axes, metric_title_artists, strict=True), start=1):
        if title_artist_item is not None:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=title_artist_item.get_window_extent(renderer=renderer),
                    box_id=f"metric_panel_title_{index}",
                    box_type="subplot_title",
                )
            )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"metric_panel_x_axis_title_{index}",
                box_type="subplot_x_axis_title",
            )
        )
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=f"metric_panel_{index}",
                box_type="metric_panel",
            )
        )
    for index, (axes, title_artist_item) in enumerate(zip(audit_axes, audit_title_artists, strict=True), start=1):
        if title_artist_item is not None:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=title_artist_item.get_window_extent(renderer=renderer),
                    box_id=f"audit_panel_title_{index}",
                    box_type="subplot_title",
                )
            )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"audit_panel_x_axis_title_{index}",
                box_type="subplot_x_axis_title",
            )
        )
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=f"audit_panel_{index}",
                box_type="audit_panel",
            )
        )

    marker_index = 1
    for axes, panel in zip(metric_axes, metric_panels, strict=True):
        lower_limit, upper_limit = axes.get_xlim()
        x_radius = max((upper_limit - lower_limit) * 0.018, 0.01)
        for row_position, row in enumerate(panel["rows"]):
            value = float(row["value"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes,
                    figure=fig,
                    x0=value - x_radius,
                    y0=float(row_position) - 0.18,
                    x1=value + x_radius,
                    y1=float(row_position) + 0.18,
                    box_id=f"metric_marker_{marker_index}",
                    box_type="metric_marker",
                )
            )
            marker_index += 1

    for index, artist in enumerate(audit_bar_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"audit_bar_{index}",
                box_type="audit_bar",
            )
        )

    for index, artist in enumerate([*metric_reference_artists, *audit_reference_artists], start=1):
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"reference_line_{index}",
                box_type="reference_line",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_panels": metric_panels,
                "audit_panels": audit_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_shap_summary_beeswarm(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    rows = list(display_payload.get("rows") or [])
    if not rows:
        raise RuntimeError("shap_summary_beeswarm requires non-empty rows")
    render_context = dict(display_payload.get("render_context") or {})
    layout_override = dict(render_context.get("layout_override") or {})
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    figure_height = max(4.8, 0.85 * len(rows) + 1.4)
    fig, ax = plt.subplots(figsize=(7.2, figure_height))
    fig.patch.set_facecolor("white")

    feature_values = [point["feature_value"] for row in rows for point in row["points"]]
    min_value = min(feature_values)
    max_value = max(feature_values)
    if max_value == min_value:
        max_value = min_value + 1.0
    norm = matplotlib.colors.Normalize(vmin=min_value, vmax=max_value)
    cmap = plt.get_cmap("coolwarm")
    point_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows):
        ordered_points = sorted(row["points"], key=lambda item: float(item["shap_value"]))
        offsets = _centered_offsets(len(ordered_points))
        for point_index, point in enumerate(ordered_points):
            row_position = row_index + offsets[point_index]
            ax.scatter(
                point["shap_value"],
                row_position,
                s=42,
                c=[cmap(norm(point["feature_value"]))],
                edgecolors="white",
                linewidths=0.35,
                alpha=0.95,
            )
            point_rows.append(
                {
                    "feature": str(row["feature"]),
                    "row_position": row_position,
                    "shap_value": float(point["shap_value"]),
                }
            )

    ax.axvline(0.0, color="#6b7280", linewidth=0.8, linestyle="--")
    ax.set_yticks(list(range(len(rows))))
    ax.set_yticklabels([str(row["feature"]) for row in rows], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    ax.set_ylabel("")
    if show_figure_title:
        ax.set_title(str(display_payload.get("title") or "").strip(), fontsize=12.5, fontweight="bold", color="#13293d")
    _apply_publication_axes_style(ax)

    scalar_mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(scalar_mappable, ax=ax, pad=0.02)
    colorbar.set_label("Feature value", fontsize=10, color="#13293d")

    fig.tight_layout()
    fig.canvas.draw()
    dump_json(
        layout_sidecar_path,
        _build_python_shap_layout_sidecar(
            figure=fig,
            axes=ax,
            colorbar=colorbar,
            rows=rows,
            point_rows=point_rows,
            template_id=template_id,
        ),
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_dependence_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = float(stroke.get("marker_size") or 4.5)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    interaction_values = [float(point["interaction_value"]) for panel in panels for point in panel["points"]]
    interaction_min = min(interaction_values)
    interaction_max = max(interaction_values)
    if interaction_max <= interaction_min:
        interaction_max = interaction_min + 1.0
    color_norm = matplotlib.colors.Normalize(vmin=interaction_min, vmax=interaction_max)
    cmap = plt.get_cmap("coolwarm")

    shap_values = [float(point["shap_value"]) for panel in panels for point in panel["points"]]
    y_min = min(min(shap_values), 0.0)
    y_max = max(max(shap_values), 0.0)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.16, 0.08)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding
    if y_upper <= y_lower:
        y_upper = y_lower + 0.25

    figure_width = max(8.8, 3.7 * len(panels) + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 4.9), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    panel_title_artists: list[Any] = []
    for axes_item, panel in zip(axes_list, panels, strict=True):
        feature_values = [float(point["feature_value"]) for point in panel["points"]]
        x_min = min(feature_values)
        x_max = max(feature_values)
        x_span = x_max - x_min
        if x_span <= 0.0:
            x_padding = max(abs(x_min) * 0.15, 1.0)
        else:
            x_padding = max(x_span * 0.14, x_span * 0.06)
        axes_item.scatter(
            feature_values,
            [float(point["shap_value"]) for point in panel["points"]],
            c=[float(point["interaction_value"]) for point in panel["points"]],
            cmap=cmap,
            norm=color_norm,
            s=marker_size**2,
            alpha=0.94,
            edgecolors="white",
            linewidths=0.5,
            zorder=3,
        )
        axes_item.axhline(0.0, color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.set_xlim(x_min - x_padding, x_max + x_padding)
        axes_item.set_ylim(y_lower, y_upper)
        axes_item.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="both", labelsize=tick_size, colors="#2F3437")
        axes_item.grid(axis="both", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)
        panel_title_artists.append(axes_item.title)

    top_margin = 0.78 if show_figure_title else 0.86
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.11, right=0.88, top=top_margin, bottom=0.22, wspace=0.26)

    y_axis_title_artist = fig.text(
        0.035,
        0.51,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    scalar_mappable = plt.cm.ScalarMappable(norm=color_norm, cmap=cmap)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(scalar_mappable, ax=axes_list, fraction=0.048, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("colorbar_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        color="#13293d",
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.4), colors="#2F3437")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
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

    panel_label_artists = [
        _add_panel_label(axes_item=axes_item, label=str(panel["panel_label"]))
        for axes_item, panel in zip(axes_list, panels, strict=True)
    ]
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
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="subplot_y_axis_title",
        )
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        )
    ]
    normalized_panels: list[dict[str, Any]] = []

    for axes_item, panel_title_artist, panel_label_artist, panel in zip(
        axes_list,
        panel_title_artists,
        panel_label_artists,
        panels,
        strict=True,
    ):
        panel_token = str(panel["panel_label"])
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_title_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
            ]
        )
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=f"panel_{panel_token}",
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        x_lower, x_upper = axes_item.get_xlim()
        y_thickness = max((axes_item.get_ylim()[1] - axes_item.get_ylim()[0]) * 0.012, 0.01)
        zero_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(x_lower),
            y0=-y_thickness / 2.0,
            x1=float(x_upper),
            y1=y_thickness / 2.0,
            box_id=f"zero_line_{panel_token}",
            box_type="zero_line",
        )
        zero_line_box["x0"] = float(panel_box["x0"])
        zero_line_box["x1"] = float(panel_box["x1"])
        zero_line_box["y0"] = max(float(panel_box["y0"]), float(zero_line_box["y0"]))
        zero_line_box["y1"] = min(float(panel_box["y1"]), float(zero_line_box["y1"]))
        guide_boxes.append(
            zero_line_box
        )

        normalized_points: list[dict[str, Any]] = []
        for point in panel["points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(point["feature_value"]),
                y=float(point["shap_value"]),
            )
            normalized_points.append(
                {
                    "feature_value": float(point["feature_value"]),
                    "shap_value": float(point["shap_value"]),
                    "interaction_value": float(point["interaction_value"]),
                    "x": point_x,
                    "y": point_y,
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "interaction_feature": str(panel["interaction_feature"]),
                "points": normalized_points,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "colorbar_label": str(display_payload.get("colorbar_label") or "").strip(),
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_waterfall_local_explanation_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    all_values: list[float] = []
    max_contribution_count = 0
    for panel in panels:
        baseline_value = float(panel["baseline_value"])
        predicted_value = float(panel["predicted_value"])
        running_value = baseline_value
        normalized_contributions: list[dict[str, Any]] = []
        raw_contributions = list(panel["contributions"])
        for contribution_index, contribution in enumerate(raw_contributions):
            shap_value = float(contribution["shap_value"])
            start_value = running_value
            end_value = running_value + shap_value
            if contribution_index == len(raw_contributions) - 1:
                end_value = predicted_value
            normalized_contributions.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution.get("feature_value_text") or "").strip(),
                    "shap_value": shap_value,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )
            running_value = end_value
            all_values.extend((start_value, end_value))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )
        all_values.extend((baseline_value, predicted_value))
        max_contribution_count = max(max_contribution_count, len(normalized_contributions))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.12, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    x_marker_half_width = max(x_span * 0.004, 0.0025)

    figure_width = max(8.8, 3.7 * len(normalized_panels) + 1.7)
    figure_height = max(4.8, 0.62 * max_contribution_count + 2.2)
    fig, axes = plt.subplots(1, len(normalized_panels), figsize=(figure_width, figure_height), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, normalized_panels, strict=True):
        contributions = list(panel["contributions"])
        row_positions = list(range(len(contributions)))
        feature_labels = [
            (
                f"{item['feature']} = {item['feature_value_text']}"
                if item["feature_value_text"]
                else str(item["feature"])
            )
            for item in contributions
        ]
        bar_artists: list[Any] = []
        value_label_artists: list[Any] = []
        for row_index, contribution in enumerate(contributions):
            start_value = float(contribution["start_value"])
            end_value = float(contribution["end_value"])
            shap_value = float(contribution["shap_value"])
            left_value = min(start_value, end_value)
            bar_width = abs(end_value - start_value)
            bar_artist = axes_item.barh(
                row_index,
                bar_width,
                left=left_value,
                height=0.6,
                color=matplotlib.colors.to_rgba(positive_color if shap_value > 0 else negative_color, alpha=0.92),
                edgecolor=positive_color if shap_value > 0 else negative_color,
                linewidth=0.95,
                zorder=3,
            )[0]
            bar_artists.append(bar_artist)
            value_label_artists.append(
                axes_item.annotate(
                    f"{shap_value:+.2f}",
                    xy=(end_value, row_index),
                    xytext=(6 if shap_value > 0 else -6, 0),
                    textcoords="offset points",
                    ha="left" if shap_value > 0 else "right",
                    va="center",
                    fontsize=max(tick_size - 0.7, 8.2),
                    color="#13293d",
                )
            )

        axes_item.axvline(float(panel["baseline_value"]), color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.axvline(float(panel["predicted_value"]), color="#13293d", linewidth=1.1, linestyle="-", zorder=1)
        axes_item.set_xlim(x_lower, x_upper)
        axes_item.set_ylim(-1.1, len(contributions) - 0.4)
        axes_item.set_yticks(row_positions)
        axes_item.set_yticklabels(feature_labels, fontsize=max(tick_size - 0.6, 8.4))
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.tick_params(axis="y", length=0, pad=6)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)
        case_label_artist = axes_item.text(
            0.16,
            0.965,
            str(panel["case_label"]),
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.4, 8.8),
            color="#475569",
            ha="left",
            va="top",
        )
        baseline_label_artist = axes_item.text(
            0.02,
            0.885,
            f"Baseline {float(panel['baseline_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#475569",
            ha="left",
            va="top",
        )
        prediction_label_artist = axes_item.text(
            0.98,
            0.885,
            f"Prediction {float(panel['predicted_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#13293d",
            ha="right",
            va="top",
        )
        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "bar_artists": bar_artists,
                "value_label_artists": value_label_artists,
                "case_label_artist": case_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.94, top=top_margin, bottom=0.18, wspace=0.30)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            max(0.01, panel_x0 - x_padding * 1.3),
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in panel_records
    ]
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

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_layout_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["panel_title_artist"].get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["case_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"case_label_{panel_token}",
                    box_type="case_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["baseline_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"baseline_label_{panel_token}",
                    box_type="baseline_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"prediction_label_{panel_token}",
                    box_type="prediction_label",
                ),
            ]
        )

        feature_label_box_ids: list[str] = []
        for label_index, tick_label in enumerate(axes_item.get_yticklabels(), start=1):
            if not str(tick_label.get_text() or "").strip():
                continue
            box_id = f"feature_label_{panel_token}_{label_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=tick_label.get_window_extent(renderer=renderer),
                    box_id=box_id,
                    box_type="feature_label",
                )
            )
            feature_label_box_ids.append(box_id)

        contribution_metrics: list[dict[str, Any]] = []
        for contribution_index, (contribution, bar_artist, value_label_artist) in enumerate(
            zip(
                panel["contributions"],
                record["bar_artists"],
                record["value_label_artists"],
                strict=True,
            ),
            start=1,
        ):
            bar_box_id = f"contribution_bar_{panel_token}_{contribution_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=bar_artist.get_window_extent(renderer=renderer),
                    box_id=bar_box_id,
                    box_type="contribution_bar",
                )
            )
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=value_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"contribution_label_{panel_token}_{contribution_index}",
                    box_type="contribution_label",
                )
            )
            contribution_metrics.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution["feature_value_text"]),
                    "shap_value": float(contribution["shap_value"]),
                    "start_value": float(contribution["start_value"]),
                    "end_value": float(contribution["end_value"]),
                    "bar_box_id": bar_box_id,
                    "label_box_id": feature_label_box_ids[contribution_index - 1],
                }
            )

        marker_y0 = -0.95
        marker_y1 = len(panel["contributions"]) - 0.45
        baseline_marker_box_id = f"baseline_marker_{panel_token}"
        prediction_marker_box_id = f"prediction_marker_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["baseline_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["baseline_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=baseline_marker_box_id,
                box_type="baseline_marker",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["predicted_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["predicted_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        normalized_layout_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "baseline_marker_box_id": baseline_marker_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "contributions": contribution_metrics,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "panels": normalized_layout_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_force_like_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    all_values: list[float] = []
    max_contribution_count = 0
    for panel in panels:
        baseline_value = float(panel["baseline_value"])
        predicted_value = float(panel["predicted_value"])
        positive_cursor = baseline_value
        negative_cursor = baseline_value
        normalized_contributions: list[dict[str, Any]] = []
        for contribution in list(panel["contributions"]):
            shap_value = float(contribution["shap_value"])
            direction = "positive" if shap_value > 0 else "negative"
            if direction == "positive":
                start_value = positive_cursor
                end_value = positive_cursor + shap_value
                positive_cursor = end_value
            else:
                start_value = negative_cursor
                end_value = negative_cursor + shap_value
                negative_cursor = end_value
            normalized_contributions.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution.get("feature_value_text") or "").strip(),
                    "shap_value": shap_value,
                    "direction": direction,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )
            all_values.extend((start_value, end_value))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )
        all_values.extend((baseline_value, predicted_value))
        max_contribution_count = max(max_contribution_count, len(normalized_contributions))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.14, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    x_marker_half_width = max(x_span * 0.004, 0.0025)

    figure_width = max(8.8, 3.7 * len(normalized_panels) + 1.8)
    figure_height = max(4.9, 0.35 * max_contribution_count + 3.2)
    fig, axes = plt.subplots(1, len(normalized_panels), figsize=(figure_width, figure_height), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    positive_band = (0.49, 0.57)
    negative_band = (0.30, 0.38)
    marker_y0 = 0.20
    marker_y1 = 0.74

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, normalized_panels, strict=True):
        axes_item.set_xlim(x_lower, x_upper)
        axes_item.set_ylim(0.14, 0.84)
        axes_item.set_yticks([])
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)

        case_label_artist = axes_item.text(
            0.5,
            0.965,
            str(panel["case_label"]),
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.4, 8.8),
            color="#475569",
            ha="center",
            va="top",
        )
        baseline_label_artist = axes_item.text(
            0.02,
            0.885,
            f"Baseline {float(panel['baseline_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#475569",
            ha="left",
            va="top",
        )
        prediction_label_artist = axes_item.text(
            0.98,
            0.885,
            f"Prediction {float(panel['predicted_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#13293d",
            ha="right",
            va="top",
        )

        segment_artists: list[dict[str, Any]] = []
        label_artists: list[Any] = []
        for contribution in panel["contributions"]:
            direction = str(contribution["direction"])
            start_value = float(contribution["start_value"])
            end_value = float(contribution["end_value"])
            left_value = min(start_value, end_value)
            right_value = max(start_value, end_value)
            width = max(right_value - left_value, 1e-9)
            tip_width = min(max(x_span * 0.018, width * 0.22), width * 0.45)
            y0, y1 = positive_band if direction == "positive" else negative_band
            y_mid = (y0 + y1) / 2.0
            if direction == "positive":
                polygon_points = [
                    (left_value, y0),
                    (right_value - tip_width, y0),
                    (right_value, y_mid),
                    (right_value - tip_width, y1),
                    (left_value, y1),
                    (left_value + tip_width * 0.35, y_mid),
                ]
                face_color = matplotlib.colors.to_rgba(positive_color, alpha=0.92)
                edge_color = positive_color
            else:
                polygon_points = [
                    (right_value, y0),
                    (left_value + tip_width, y0),
                    (left_value, y_mid),
                    (left_value + tip_width, y1),
                    (right_value, y1),
                    (right_value - tip_width * 0.35, y_mid),
                ]
                face_color = matplotlib.colors.to_rgba(negative_color, alpha=0.92)
                edge_color = negative_color
            segment_artist = matplotlib.patches.Polygon(
                polygon_points,
                closed=True,
                facecolor=face_color,
                edgecolor=edge_color,
                linewidth=0.85,
                zorder=3,
            )
            axes_item.add_patch(segment_artist)
            segment_artists.append({"artist": segment_artist, "contribution": contribution})

            label_text = (
                f"{contribution['feature']} = {contribution['feature_value_text']}"
                if contribution["feature_value_text"]
                else str(contribution["feature"])
            )
            label_artists.append(
                axes_item.text(
                    (left_value + right_value) / 2.0,
                    y_mid,
                    textwrap.fill(label_text, width=16),
                    fontsize=max(tick_size - 1.6, 7.0),
                    color="white",
                    ha="center",
                    va="center",
                    zorder=4,
                )
            )

        axes_item.axvline(float(panel["baseline_value"]), color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.axvline(float(panel["predicted_value"]), color="#13293d", linewidth=1.15, linestyle="-", zorder=1)
        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "segment_artists": segment_artists,
                "label_artists": label_artists,
                "case_label_artist": case_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.10, right=0.95, top=top_margin, bottom=0.19, wspace=0.28)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in panel_records
    ]
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

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_layout_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["panel_title_artist"].get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["case_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"case_label_{panel_token}",
                    box_type="case_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["baseline_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"baseline_label_{panel_token}",
                    box_type="baseline_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"prediction_label_{panel_token}",
                    box_type="prediction_label",
                ),
            ]
        )

        contribution_metrics: list[dict[str, Any]] = []
        for contribution_index, (segment_record, label_artist) in enumerate(
            zip(record["segment_artists"], record["label_artists"], strict=True),
            start=1,
        ):
            contribution = segment_record["contribution"]
            direction = str(contribution["direction"])
            segment_box_id = f"{direction}_force_segment_{panel_token}_{contribution_index}"
            label_box_id = f"force_label_{panel_token}_{contribution_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=segment_record["artist"].get_window_extent(renderer=renderer),
                    box_id=segment_box_id,
                    box_type=f"{direction}_force_segment",
                )
            )
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="force_feature_label",
                )
            )
            contribution_metrics.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution["feature_value_text"]),
                    "shap_value": float(contribution["shap_value"]),
                    "direction": direction,
                    "start_value": float(contribution["start_value"]),
                    "end_value": float(contribution["end_value"]),
                    "segment_box_id": segment_box_id,
                    "label_box_id": label_box_id,
                }
            )

        baseline_marker_box_id = f"baseline_marker_{panel_token}"
        prediction_marker_box_id = f"prediction_marker_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["baseline_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["baseline_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=baseline_marker_box_id,
                box_type="baseline_marker",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["predicted_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["predicted_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        normalized_layout_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "baseline_marker_box_id": baseline_marker_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "contributions": contribution_metrics,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "panels": normalized_layout_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_time_dependent_roc_comparison_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    color_cycle = (
        str(palette.get("primary") or model_color).strip() or model_color,
        str(palette.get("secondary") or comparator_color).strip() or comparator_color,
        str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F",
    )

    panel_count = len(panels)
    figure_width = max(10.2, 4.25 * panel_count + 0.8)
    fig, axes = plt.subplots(1, panel_count, figsize=(figure_width, 4.8))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
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

    x_axis_artist = fig.text(
        0.5,
        0.055,
        str(display_payload.get("x_label") or "").strip(),
        ha="center",
        va="center",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    y_axis_artist = fig.text(
        0.018,
        0.52,
        str(display_payload.get("y_label") or "").strip(),
        ha="center",
        va="center",
        rotation="vertical",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )

    panel_title_artists: list[Any] = []
    panel_label_artists: list[Any] = []
    panel_annotation_artists: list[Any] = []
    normalized_panels: list[dict[str, Any]] = []
    shared_legend_handles: list[Any] | None = None
    shared_legend_labels: list[str] | None = None

    for axes_index, (axes, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        series = list(panel.get("series") or [])
        if not series:
            raise RuntimeError(f"{template_id} panel {axes_index} requires non-empty series")

        normalized_series: list[dict[str, Any]] = []
        normalized_reference_line: dict[str, Any] | None = None
        reference_line = panel.get("reference_line")
        if isinstance(reference_line, dict):
            ref_x = [float(value) for value in reference_line.get("x") or []]
            ref_y = [float(value) for value in reference_line.get("y") or []]
            normalized_reference_line = {
                "label": str(reference_line.get("label") or "").strip(),
                "x": ref_x,
                "y": ref_y,
            }
            axes.plot(
                ref_x,
                ref_y,
                linewidth=1.2,
                color=reference_color,
                linestyle="--",
                label=str(reference_line.get("label") or "Chance"),
                zorder=1,
            )

        for series_index, series_item in enumerate(series):
            x_values = [float(value) for value in series_item["x"]]
            y_values = [float(value) for value in series_item["y"]]
            line_color = color_cycle[series_index % len(color_cycle)]
            axes.plot(
                x_values,
                y_values,
                linewidth=2.0,
                color=line_color,
                label=str(series_item["label"]),
                zorder=2 + series_index,
            )
            normalized_series.append(
                {
                    "label": str(series_item["label"]),
                    "x": x_values,
                    "y": y_values,
                    "annotation": str(series_item.get("annotation") or "").strip(),
                }
            )

        axes.set_xlim(0.0, 1.0)
        axes.set_ylim(0.0, 1.0)
        axes.set_title(
            textwrap.fill(str(panel.get("title") or "").strip(), width=28),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
            pad=10.0,
        )
        axes.tick_params(axis="both", labelsize=tick_size, colors="#2F3437")
        axes.grid(color="#E6EDF5", linewidth=0.8, linestyle=":")
        _apply_publication_axes_style(axes)

        panel_label = str(panel.get("panel_label") or "").strip()
        panel_label_artists.append(
            axes.text(
                0.02,
                0.98,
                panel_label,
                transform=axes.transAxes,
                fontsize=panel_label_size,
                fontweight="bold",
                color="#2F3437",
                ha="left",
                va="top",
            )
        )
        panel_title_artists.append(axes.title)

        annotation_lines = [str(panel.get("analysis_window_label") or "").strip()]
        if panel.get("time_horizon_months") is not None:
            annotation_lines.append(f"Horizon: {int(panel['time_horizon_months'])} months")
        annotation = str(panel.get("annotation") or "").strip()
        if annotation:
            annotation_lines.append(annotation)
        annotation_artist = axes.text(
            0.03,
            0.05,
            "\n".join(item for item in annotation_lines if item),
            transform=axes.transAxes,
            fontsize=max(tick_size - 0.6, 8.1),
            color=reference_color,
            ha="left",
            va="bottom",
        )
        panel_annotation_artists.append(annotation_artist)

        if shared_legend_handles is None:
            legend_handles, legend_labels = axes.get_legend_handles_labels()
            shared_legend_handles = list(legend_handles)
            shared_legend_labels = list(legend_labels)

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_label,
                "title": str(panel["title"]),
                "analysis_window_label": str(panel["analysis_window_label"]),
                "time_horizon_months": (
                    int(panel["time_horizon_months"]) if panel.get("time_horizon_months") is not None else None
                ),
                "annotation": annotation,
                "series": normalized_series,
                "reference_line": normalized_reference_line,
            }
        )

    top_margin = 0.80 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.07, right=0.99, top=top_margin, bottom=0.28, wspace=0.28)
    legend = None
    if shared_legend_handles and shared_legend_labels:
        legend = fig.legend(
            shared_legend_handles,
            shared_legend_labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.06),
            ncol=min(3, len(shared_legend_labels)),
            frameon=False,
            fontsize=max(tick_size - 1.2, 8.0),
            handlelength=2.2,
            columnspacing=1.3,
        )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=x_axis_artist.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )

    panel_boxes: list[dict[str, Any]] = []
    for axes, panel, title_artist_item, label_artist_item, annotation_artist_item in zip(
        axes_list,
        normalized_panels,
        panel_title_artists,
        panel_label_artists,
        panel_annotation_artists,
        strict=True,
    ):
        panel_label_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_label_token}",
                box_type="panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_label_token}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_label_token}",
                box_type="panel_label",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=annotation_artist_item.get_window_extent(renderer=renderer),
                box_id=f"annotation_{panel_label_token}",
                box_type="annotation_text",
            )
        )

    guide_boxes: list[dict[str, Any]] = []
    if legend is not None:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend",
                box_type="legend",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_time_to_event_landmark_performance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    landmark_summaries = list(display_payload.get("landmark_summaries") or [])
    if not landmark_summaries:
        raise RuntimeError(f"{template_id} requires non-empty landmark_summaries")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    discrimination_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    error_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    calibration_color = str(palette.get("primary") or discrimination_color).strip() or discrimination_color
    discrimination_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    error_fill = str(palette.get("secondary_soft") or "#fee2e2").strip() or "#fee2e2"
    calibration_fill = str(palette.get("primary_soft") or "#dbeafe").strip() or "#dbeafe"

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(11.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.2, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    def _build_metric_rows(metric_key: str) -> list[dict[str, Any]]:
        normalized_rows: list[dict[str, Any]] = []
        for item in landmark_summaries:
            row = {
                "label": str(item["window_label"]),
                "analysis_window_label": str(item["analysis_window_label"]),
                "landmark_months": int(item["landmark_months"]),
                "prediction_months": int(item["prediction_months"]),
                "value": float(item[metric_key]),
            }
            annotation = str(item.get("annotation") or "").strip()
            if annotation:
                row["annotation"] = annotation
            normalized_rows.append(row)
        return normalized_rows

    metric_panels = [
        {
            "panel_id": "discrimination_panel",
            "panel_label": "A",
            "metric_kind": "c_index",
            "title": str(display_payload.get("discrimination_panel_title") or "").strip(),
            "x_label": str(display_payload.get("discrimination_x_label") or "").strip(),
            "rows": _build_metric_rows("c_index"),
        },
        {
            "panel_id": "error_panel",
            "panel_label": "B",
            "metric_kind": "brier_score",
            "title": str(display_payload.get("error_panel_title") or "").strip(),
            "x_label": str(display_payload.get("error_x_label") or "").strip(),
            "rows": _build_metric_rows("brier_score"),
        },
        {
            "panel_id": "calibration_panel",
            "panel_label": "C",
            "metric_kind": "calibration_slope",
            "title": str(display_payload.get("calibration_panel_title") or "").strip(),
            "x_label": str(display_payload.get("calibration_x_label") or "").strip(),
            "reference_value": 1.0,
            "rows": _build_metric_rows("calibration_slope"),
        },
    ]

    def _panel_limits(
        rows: list[dict[str, Any]],
        *,
        reference_value: float | None,
        clamp_probability: bool,
    ) -> tuple[float, float]:
        values = [float(item["value"]) for item in rows]
        if reference_value is not None:
            values.append(float(reference_value))
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum
        padding = max(span * 0.20, 0.035 if clamp_probability else 0.08)
        lower = minimum - padding
        upper = maximum + padding
        if clamp_probability:
            lower = max(0.0, lower)
            upper = min(1.0, upper)
        if upper <= lower:
            upper = lower + (0.10 if clamp_probability else 0.25)
        return lower, upper

    figure_height = max(4.8, 0.42 * len(landmark_summaries) + 3.4)
    fig, axes = plt.subplots(1, 3, figsize=(12.4, figure_height))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    panel_title_artists: list[Any] = []
    reference_specs: list[tuple[Any, float, int]] = []

    row_labels = [str(item["window_label"]) for item in landmark_summaries]
    row_positions = list(range(len(row_labels)))
    y_axis_title_artist = None
    panel_style = (
        (discrimination_color, discrimination_fill),
        (error_color, error_fill),
        (calibration_color, calibration_fill),
    )

    for panel_index, (axes_item, panel, style) in enumerate(zip(axes_list, metric_panels, panel_style, strict=True), start=1):
        line_color, fill_color = style
        rows = list(panel["rows"])
        values = [float(item["value"]) for item in rows]
        lower_limit, upper_limit = _panel_limits(
            rows,
            reference_value=float(panel["reference_value"]) if panel.get("reference_value") is not None else None,
            clamp_probability=str(panel["metric_kind"]) in {"c_index", "brier_score"},
        )

        if panel.get("reference_value") is not None:
            reference_specs.append((axes_item, float(panel["reference_value"]), len(rows)))
            axes_item.axvline(
                float(panel["reference_value"]),
                color=reference_color,
                linewidth=1.0,
                linestyle="--",
                zorder=1,
            )

        axes_item.hlines(
            row_positions,
            [lower_limit] * len(row_positions),
            values,
            color=matplotlib.colors.to_rgba(fill_color, alpha=0.96),
            linewidth=2.2,
            zorder=2,
        )
        axes_item.scatter(
            values,
            row_positions,
            s=marker_size**2,
            color=line_color,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )

        axes_item.set_xlim(lower_limit, upper_limit)
        axes_item.set_ylim(-0.6, len(rows) - 0.4)
        axes_item.set_yticks(row_positions)
        if panel_index == 1:
            axes_item.set_yticklabels(row_labels, fontsize=max(tick_size - 1.0, 8.2), color="#2F3437")
            axes_item.set_ylabel(
                "Landmark window",
                fontsize=axis_title_size,
                fontweight="bold",
                color="#13293d",
                labelpad=16,
            )
            y_axis_title_artist = axes_item.yaxis.label
        else:
            axes_item.set_yticklabels([""] * len(row_labels))
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        panel_title_artists.append(
            axes_item.set_title(
                str(panel["title"]),
                fontsize=axis_title_size,
                fontweight="bold",
                color="#334155",
                pad=10.0,
            )
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.tick_params(axis="y", length=0, pad=6 if panel_index == 1 else 0)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)

    top_margin = 0.78 if show_figure_title else 0.88
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.22, right=0.985, top=top_margin, bottom=0.20, wspace=0.28)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.030, 0.010), 0.018)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.2, 12.8),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=axes_list[0], label="A"),
        _add_panel_label(axes_item=axes_list[1], label="B"),
        _add_panel_label(axes_item=axes_list[2], label="C"),
    ]
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

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    marker_index = 1

    for panel_index, (axes_item, panel_title_artist, panel_label_artist, panel) in enumerate(
        zip(axes_list, panel_title_artists, panel_label_artists, metric_panels, strict=True),
        start=1,
    ):
        panel_token = str(panel["panel_label"])
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_title_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_token}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"x_axis_title_{panel_token}",
                box_type="subplot_x_axis_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_token}",
                box_type="panel_label",
            )
        )
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_token}",
                box_type="metric_panel",
            )
        )
        lower_limit, upper_limit = axes_item.get_xlim()
        x_radius = max((upper_limit - lower_limit) * 0.018, 0.008)
        for row_position, row in enumerate(panel["rows"]):
            value = float(row["value"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=value - x_radius,
                    y0=float(row_position) - 0.18,
                    x1=value + x_radius,
                    y1=float(row_position) + 0.18,
                    box_id=f"metric_marker_{marker_index}",
                    box_type="metric_marker",
                )
            )
            marker_index += 1

    if y_axis_title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="y_axis_title_A",
                box_type="subplot_y_axis_title",
            )
        )

    for index, (axes_item, reference_value, row_count) in enumerate(reference_specs, start=1):
        lower_limit, upper_limit = axes_item.get_xlim()
        x_radius = max((upper_limit - lower_limit) * 0.012, 0.006)
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=reference_value - x_radius,
                y0=-0.45,
                x1=reference_value + x_radius,
                y1=float(max(row_count - 1, 0)) + 0.45,
                box_id=f"reference_line_{index}",
                box_type="reference_line",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_panels": metric_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_time_to_event_stratified_cumulative_incidence_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    color_cycle = (
        str(palette.get("primary") or model_color).strip() or model_color,
        str(palette.get("secondary") or comparator_color).strip() or comparator_color,
        str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F",
        str(palette.get("neutral") or reference_color).strip() or reference_color,
    )

    panel_count = len(panels)
    figure_width = max(11.6, 3.85 * panel_count + 0.8)
    fig, axes = plt.subplots(1, panel_count, figsize=(figure_width, 4.9))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
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

    x_axis_artist = fig.text(
        0.5,
        0.055,
        str(display_payload.get("x_label") or "").strip(),
        ha="center",
        va="center",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    y_axis_artist = fig.text(
        0.018,
        0.52,
        str(display_payload.get("y_label") or "").strip(),
        ha="center",
        va="center",
        rotation="vertical",
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )

    panel_title_artists: list[Any] = []
    panel_label_artists: list[Any] = []
    panel_annotation_artists: list[Any | None] = []
    normalized_panels: list[dict[str, Any]] = []

    for axes_index, (axes, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        groups = list(panel.get("groups") or [])
        if not groups:
            raise RuntimeError(f"{template_id} panel {axes_index} requires non-empty groups")

        all_times = [float(value) for group in groups for value in group["times"]]
        all_values = [float(value) for group in groups for value in group["values"]]
        x_min = min(all_times)
        x_max = max(all_times)
        x_padding = max((x_max - x_min) * 0.06, 0.5 if x_max > x_min else 0.5)
        y_max = max(all_values)
        y_upper = min(1.0, max(0.12, y_max * 1.10 + 0.01))

        panel_groups: list[dict[str, Any]] = []
        for group_index, group in enumerate(groups):
            line_color = color_cycle[group_index % len(color_cycle)]
            times = [float(value) for value in group["times"]]
            values = [float(value) for value in group["values"]]
            axes.step(
                times,
                values,
                where="post",
                linewidth=2.0,
                color=line_color,
                label=str(group["label"]),
            )
            panel_groups.append(
                {
                    "label": str(group["label"]),
                    "times": times,
                    "values": values,
                }
            )

        axes.set_xlim(x_min, x_max + x_padding)
        axes.set_ylim(0.0, y_upper)
        axes.set_title(
            textwrap.fill(str(panel.get("title") or "").strip(), width=28),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10,
        )
        axes.tick_params(axis="both", labelsize=tick_size)
        axes.grid(axis="y", color="#e6edf2", linewidth=0.5, linestyle=":")
        axes.grid(axis="x", visible=False)
        _apply_publication_axes_style(axes)

        legend_columns = min(3, max(1, len(panel_groups)))
        axes.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.19),
            ncol=legend_columns,
            frameon=False,
            fontsize=max(tick_size - 1.2, 8.0),
            handlelength=2.2,
            columnspacing=1.3,
        )

        panel_label = str(panel.get("panel_label") or "").strip()
        panel_label_artists.append(
            axes.text(
                0.02,
                0.98,
                panel_label,
                transform=axes.transAxes,
                fontsize=panel_label_size,
                fontweight="bold",
                color="#2F3437",
                ha="left",
                va="top",
            )
        )
        panel_title_artists.append(axes.title)
        annotation_artist = None
        annotation = str(panel.get("annotation") or "").strip()
        if annotation:
            annotation_artist = axes.text(
                0.03,
                0.05,
                annotation,
                transform=axes.transAxes,
                fontsize=max(tick_size - 0.4, 8.2),
                color=reference_color,
                ha="left",
                va="bottom",
            )
        panel_annotation_artists.append(annotation_artist)
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_label,
                "title": str(panel["title"]),
                "annotation": annotation,
                "groups": panel_groups,
            }
        )

    top_margin = 0.80 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.07, right=0.99, top=top_margin, bottom=0.26, wspace=0.26)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=x_axis_artist.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )

    panel_boxes: list[dict[str, Any]] = []
    for axes, panel, title_artist_item, label_artist_item, annotation_artist_item in zip(
        axes_list,
        normalized_panels,
        panel_title_artists,
        panel_label_artists,
        panel_annotation_artists,
        strict=True,
    ):
        panel_label_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_label_token}",
                box_type="panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_label_token}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_label_token}",
                box_type="panel_label",
            )
        )
        if annotation_artist_item is not None:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=annotation_artist_item.get_window_extent(renderer=renderer),
                    box_id=f"annotation_{panel_label_token}",
                    box_type="annotation_text",
                )
            )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [],
            "metrics": {
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_time_to_event_threshold_governance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    threshold_summaries = list(display_payload.get("threshold_summaries") or [])
    risk_group_summaries = list(display_payload.get("risk_group_summaries") or [])
    if not threshold_summaries or not risk_group_summaries:
        raise RuntimeError(f"{template_id} requires non-empty threshold_summaries and risk_group_summaries")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    observed_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    predicted_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    primary_color = str(palette.get("primary") or observed_color).strip() or observed_color
    threshold_fill = str(palette.get("primary_soft") or "#EAF2F5").strip() or "#EAF2F5"
    threshold_fill_alt = str(palette.get("secondary_soft") or "#F4EEE5").strip() or "#F4EEE5"
    grid_color = str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = max(float(stroke.get("marker_size") or 4.2), 3.8)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    figure_height = max(4.4, 3.2 + 0.34 * len(threshold_summaries))
    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(11.2, figure_height))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    left_axes.set_axis_off()
    left_axes.set_xlim(0.0, 1.0)
    left_axes.set_ylim(0.0, 1.0)
    left_axes.set_title(
        str(display_payload.get("threshold_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=12.0,
    )
    left_panel_label = left_axes.text(
        0.02,
        0.98,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    card_top = 0.82
    card_bottom = 0.10
    card_gap = 0.05
    card_x0 = 0.10
    card_x1 = 0.92
    available_height = card_top - card_bottom - card_gap * max(len(threshold_summaries) - 1, 0)
    card_height = available_height / max(len(threshold_summaries), 1)
    threshold_card_patches: list[tuple[str, Any]] = []
    for index, item in enumerate(threshold_summaries, start=1):
        y1 = card_top - (index - 1) * (card_height + card_gap)
        y0 = y1 - card_height
        fill_color = threshold_fill if index % 2 == 1 else threshold_fill_alt
        card_patch = matplotlib.patches.FancyBboxPatch(
            (card_x0, y0),
            card_x1 - card_x0,
            card_height,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            transform=left_axes.transAxes,
            linewidth=1.2,
            facecolor=fill_color,
            edgecolor=neutral_color,
        )
        left_axes.add_patch(card_patch)
        accent_patch = matplotlib.patches.Rectangle(
            (card_x0, y0),
            0.022,
            card_height,
            transform=left_axes.transAxes,
            linewidth=0,
            facecolor=primary_color if index % 2 == 1 else predicted_color,
        )
        left_axes.add_patch(accent_patch)
        left_axes.text(
            card_x0 + 0.05,
            y1 - card_height * 0.26,
            str(item["threshold_label"]),
            transform=left_axes.transAxes,
            fontsize=tick_size + 0.2,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x0 + 0.05,
            y1 - card_height * 0.49,
            f"Threshold {float(item['threshold']):.0%}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.1,
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x0 + 0.05,
            y0 + card_height * 0.26,
            f"Sens {float(item['sensitivity']):.0%} · Spec {float(item['specificity']):.0%}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.4,
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x1 - 0.04,
            y0 + card_height * 0.26,
            f"NB {float(item['net_benefit']):.3f}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.2,
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        threshold_card_patches.append((f"threshold_card_{index}", card_patch))

    right_axes.set_title(
        str(display_payload.get("calibration_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=12.0,
    )
    right_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    group_labels = [str(item["group_label"]) for item in risk_group_summaries]
    y_positions = [float(index) for index in range(1, len(risk_group_summaries) + 1)]
    predicted_risks = [float(item["predicted_risk"]) for item in risk_group_summaries]
    observed_risks = [float(item["observed_risk"]) for item in risk_group_summaries]
    x_upper = max(max(predicted_risks), max(observed_risks))
    x_upper = min(1.0, max(0.18, x_upper * 1.22 + 0.02))
    right_axes.set_xlim(0.0, x_upper)
    right_axes.set_ylim(0.5, len(risk_group_summaries) + 0.5)
    right_axes.set_yticks(y_positions)
    right_axes.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
    right_axes.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
    right_axes.tick_params(axis="x", labelsize=tick_size)
    right_axes.tick_params(axis="y", length=0, pad=7)
    right_axes.grid(axis="x", color=grid_color, linewidth=0.8, linestyle=":")
    right_axes.grid(axis="y", visible=False)
    _apply_publication_axes_style(right_axes)
    right_panel_label = right_axes.text(
        0.02,
        0.98,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    normalized_risk_group_summaries: list[dict[str, Any]] = []
    for index, (item, y_value, predicted_risk, observed_risk) in enumerate(
        zip(risk_group_summaries, y_positions, predicted_risks, observed_risks, strict=True),
        start=1,
    ):
        right_axes.hlines(
            y=y_value,
            xmin=min(predicted_risk, observed_risk),
            xmax=max(predicted_risk, observed_risk),
            color=neutral_color,
            linewidth=1.7,
            zorder=1,
        )
        right_axes.scatter(
            [predicted_risk],
            [y_value],
            s=marker_size * 18.0,
            color=predicted_color,
            label="Predicted" if index == 1 else None,
            zorder=3,
        )
        right_axes.scatter(
            [observed_risk],
            [y_value],
            s=marker_size * 18.0,
            color=observed_color,
            label="Observed" if index == 1 else None,
            zorder=4,
        )
        predicted_x, point_y = _data_point_to_figure_xy(
            axes=right_axes,
            figure=fig,
            x=predicted_risk,
            y=y_value,
        )
        observed_x, _ = _data_point_to_figure_xy(
            axes=right_axes,
            figure=fig,
            x=observed_risk,
            y=y_value,
        )
        normalized_risk_group_summaries.append(
            {
                "group_label": str(item["group_label"]),
                "group_order": int(item["group_order"]),
                "n": int(item["n"]),
                "events": int(item["events"]),
                "predicted_risk": predicted_risk,
                "observed_risk": observed_risk,
                "predicted_x": predicted_x,
                "observed_x": observed_x,
                "y": point_y,
            }
        )

    legend_handles, legend_labels = right_axes.get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.72, 0.03),
        ncol=min(2, max(1, len(legend_labels))),
        frameon=False,
        fontsize=tick_size - 0.2,
    )

    fig.subplots_adjust(
        left=0.07,
        right=0.98,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.18,
        wspace=0.20,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_title_A",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_title_B",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title_B",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_A",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_B",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    normalized_threshold_summaries: list[dict[str, Any]] = []
    for index, (card_box_id, card_patch) in enumerate(threshold_card_patches):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=card_patch.get_window_extent(renderer=renderer),
                box_id=card_box_id,
                box_type="threshold_card",
            )
        )
        threshold_item = threshold_summaries[index]
        normalized_threshold_summaries.append(
            {
                "threshold_label": str(threshold_item["threshold_label"]),
                "threshold": float(threshold_item["threshold"]),
                "sensitivity": float(threshold_item["sensitivity"]),
                "specificity": float(threshold_item["specificity"]),
                "net_benefit": float(threshold_item["net_benefit"]),
                "card_box_id": card_box_id,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=left_axes.get_window_extent(renderer=renderer),
                    box_id="threshold_panel",
                    box_type="threshold_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_axes.get_window_extent(renderer=renderer),
                    box_id="calibration_panel",
                    box_type="calibration_panel",
                ),
            ],
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "threshold_summaries": normalized_threshold_summaries,
                "risk_group_summaries": normalized_risk_group_summaries,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_time_to_event_multihorizon_calibration_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    observed_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    predicted_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    grid_color = str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = max(float(stroke.get("marker_size") or 4.2), 3.8)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    panel_count = len(panels)
    figure_width = max(9.8, 4.1 * panel_count + 0.8)
    fig, axes = plt.subplots(1, panel_count, figsize=(figure_width, 4.7))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )
    x_axis_artist = fig.text(
        0.5,
        0.06,
        str(display_payload.get("x_label") or "").strip(),
        ha="center",
        va="center",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    fig.subplots_adjust(
        left=0.08,
        right=0.99,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.20,
        wspace=0.28,
    )

    panel_label_artists: list[Any] = []
    panel_title_artists: list[Any] = []
    normalized_panels: list[dict[str, Any]] = []
    for axes_index, (axes_item, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        calibration_summary = list(panel.get("calibration_summary") or [])
        if not calibration_summary:
            raise RuntimeError(f"{template_id} panel {axes_index} requires non-empty calibration_summary")
        group_labels = [str(item["group_label"]) for item in calibration_summary]
        y_positions = [float(index) for index in range(1, len(calibration_summary) + 1)]
        predicted_risks = [float(item["predicted_risk"]) for item in calibration_summary]
        observed_risks = [float(item["observed_risk"]) for item in calibration_summary]
        x_upper = min(1.0, max(0.18, max(max(predicted_risks), max(observed_risks)) * 1.22 + 0.02))

        axes_item.set_xlim(0.0, x_upper)
        axes_item.set_ylim(0.5, len(calibration_summary) + 0.5)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
        axes_item.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
        axes_item.tick_params(axis="x", labelsize=tick_size)
        axes_item.tick_params(axis="y", length=0, pad=6)
        axes_item.grid(axis="x", color=grid_color, linewidth=0.8, linestyle=":")
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)
        axes_item.set_title(
            str(panel.get("title") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=12.0,
        )
        panel_label_artists.append(
            axes_item.text(
                0.02,
                0.98,
                str(panel.get("panel_label") or "").strip(),
                transform=axes_item.transAxes,
                fontsize=panel_label_size,
                fontweight="bold",
                color=neutral_color,
                ha="left",
                va="top",
            )
        )
        panel_title_artists.append(axes_item.title)

        normalized_summary: list[dict[str, Any]] = []
        for group_index, (item, y_value, predicted_risk, observed_risk) in enumerate(
            zip(calibration_summary, y_positions, predicted_risks, observed_risks, strict=True),
            start=1,
        ):
            axes_item.hlines(
                y=y_value,
                xmin=min(predicted_risk, observed_risk),
                xmax=max(predicted_risk, observed_risk),
                color=neutral_color,
                linewidth=1.7,
                zorder=1,
            )
            axes_item.scatter(
                [predicted_risk],
                [y_value],
                s=marker_size * 18.0,
                color=predicted_color,
                label="Predicted" if axes_index == 1 and group_index == 1 else None,
                zorder=3,
            )
            axes_item.scatter(
                [observed_risk],
                [y_value],
                s=marker_size * 18.0,
                color=observed_color,
                label="Observed" if axes_index == 1 and group_index == 1 else None,
                zorder=4,
            )
            predicted_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=predicted_risk,
                y=y_value,
            )
            observed_x, _ = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=observed_risk,
                y=y_value,
            )
            normalized_summary.append(
                {
                    "group_label": str(item["group_label"]),
                    "group_order": int(item["group_order"]),
                    "n": int(item["n"]),
                    "events": int(item["events"]),
                    "predicted_risk": predicted_risk,
                    "observed_risk": observed_risk,
                    "predicted_x": predicted_x,
                    "observed_x": observed_x,
                    "y": point_y,
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "time_horizon_months": int(panel["time_horizon_months"]),
                "calibration_summary": normalized_summary,
            }
        )

    legend_handles, legend_labels = axes_list[0].get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=min(2, max(1, len(legend_labels))),
        frameon=False,
        fontsize=tick_size - 0.2,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=x_axis_artist.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="subplot_x_axis_title",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )

    panel_boxes: list[dict[str, Any]] = []
    for axes_item, panel, title_artist_item, label_artist_item in zip(
        axes_list,
        normalized_panels,
        panel_title_artists,
        panel_label_artists,
        strict=True,
    ):
        panel_label_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_label_token}",
                box_type="calibration_panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_label_token}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_label_token}",
                box_type="panel_label",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_time_to_event_risk_group_summary(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    risk_group_summaries = list(display_payload.get("risk_group_summaries") or [])
    if not risk_group_summaries:
        raise RuntimeError(f"{template_id} requires non-empty risk_group_summaries")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})
    observed_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    predicted_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    group_colors = (
        str(palette.get("light") or palette.get("secondary_soft") or predicted_color).strip() or predicted_color,
        str(palette.get("secondary") or predicted_color).strip() or predicted_color,
        str(palette.get("primary") or observed_color).strip() or observed_color,
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_legend = _read_bool_override(layout_override, "show_legend", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )
    x_positions = list(range(len(risk_group_summaries)))
    group_labels = [str(item["label"]) for item in risk_group_summaries]
    predicted_risk = [float(item["mean_predicted_risk_5y"]) * 100.0 for item in risk_group_summaries]
    observed_risk = [float(item["observed_km_risk_5y"]) * 100.0 for item in risk_group_summaries]
    event_counts = [int(item["events_5y"]) for item in risk_group_summaries]
    bar_width = 0.34

    left_axes.bar(
        [position - bar_width / 2.0 for position in x_positions],
        predicted_risk,
        width=bar_width,
        color=predicted_color,
        label="Predicted",
    )
    left_axes.bar(
        [position + bar_width / 2.0 for position in x_positions],
        observed_risk,
        width=bar_width,
        color=observed_color,
        label="Observed",
    )
    left_axes.set_xticks(x_positions)
    left_axes.set_xticklabels(group_labels)
    left_axes.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_title(
        str(display_payload.get("panel_a_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.grid(axis="y", color=str(palette.get("light") or "#E7E1D8"), linewidth=0.8, linestyle=":")
    left_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(left_axes)
    legend = None
    if show_legend:
        legend = fig.legend(
            *left_axes.get_legend_handles_labels(),
            loc="lower center",
            bbox_to_anchor=(0.28, 0.02),
            ncol=2,
            frameon=False,
        )
    left_panel_label = left_axes.text(
        0.02,
        0.98,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    right_axes.bar(
        x_positions,
        event_counts,
        width=0.58,
        color=[group_colors[index % len(group_colors)] for index in x_positions],
    )
    upper_margin = max(max(event_counts) * 0.08, 1.2)
    for index, value in enumerate(event_counts):
        right_axes.text(
            index,
            float(value) + upper_margin * 0.35,
            str(value),
            ha="center",
            va="bottom",
            fontsize=tick_size - 1.0,
            color=neutral_color,
        )
    right_axes.set_xticks(x_positions)
    right_axes.set_xticklabels(group_labels)
    right_axes.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("event_count_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_title(
        str(display_payload.get("panel_b_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylim(0.0, max(event_counts) + upper_margin)
    right_axes.grid(axis="y", color=str(palette.get("light") or "#E7E1D8"), linewidth=0.8, linestyle=":")
    right_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(right_axes)
    right_panel_label = right_axes.text(
        0.02,
        0.98,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.21 if show_legend else 0.12,
        wspace=0.26,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_left_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_right_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_A",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_B",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=left_axes.get_window_extent(renderer=renderer),
                    box_id="panel_left",
                    box_type="panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_axes.get_window_extent(renderer=renderer),
                    box_id="panel_right",
                    box_type="panel",
                ),
            ],
            "guide_boxes": []
            if legend is None
            else [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "risk_group_summaries": risk_group_summaries,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_time_to_event_decision_curve(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    series = list(display_payload.get("series") or [])
    if not series:
        raise RuntimeError(f"{template_id} requires non-empty series")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    treated_fraction_series = dict(display_payload.get("treated_fraction_series") or {})
    if not treated_fraction_series:
        raise RuntimeError(f"{template_id} requires treated_fraction_series")

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_legend = _read_bool_override(layout_override, "show_legend", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.8, 4.2))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=reference_color,
        )
    extra_series_palette = (
        str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("secondary") or comparator_color).strip() or comparator_color,
        str(palette.get("neutral") or reference_color).strip() or reference_color,
        str(palette.get("primary_soft") or model_color).strip() or model_color,
    )
    x_values = [float(value) for item in series for value in item["x"]]
    y_values = [float(value) for item in series for value in item["y"]]
    reference_line = display_payload.get("reference_line")
    if isinstance(reference_line, dict):
        x_values.extend(float(value) for value in reference_line.get("x", []))
        y_values.extend(float(value) for value in reference_line.get("y", []))
    highlight_band = layout_override.get("highlight_band")
    if isinstance(highlight_band, dict):
        xmin = highlight_band.get("xmin")
        xmax = highlight_band.get("xmax")
        if (
            isinstance(xmin, (int, float))
            and not isinstance(xmin, bool)
            and isinstance(xmax, (int, float))
            and not isinstance(xmax, bool)
            and float(xmin) < float(xmax)
        ):
            highlight_band_color = _require_non_empty_string(
                style_roles.get("highlight_band"),
                label=f"{template_id} render_context.style_roles.highlight_band",
            )
            left_axes.axvspan(float(xmin), float(xmax), color=highlight_band_color, alpha=0.22, zorder=0)
    for index, item in enumerate(series):
        label = str(item["label"])
        normalized_label = label.casefold()
        if "treat all" in normalized_label:
            line_color = comparator_color
        elif index == 0:
            line_color = model_color
        else:
            line_color = extra_series_palette[(index - 1) % len(extra_series_palette)]
        left_axes.plot(
            item["x"],
            item["y"],
            linewidth=2.0,
            color=line_color,
            label=label,
        )
    if isinstance(reference_line, dict):
        left_axes.plot(
            reference_line["x"],
            reference_line["y"],
            linewidth=1.0,
            linestyle="--",
            color=reference_color,
            label=str(reference_line.get("label") or ""),
        )
    x_min = min(x_values)
    x_max = max(x_values)
    y_min = min(y_values)
    y_max = max(y_values)
    x_padding = max((x_max - x_min) * 0.04, 0.01)
    y_padding = max((y_max - y_min) * 0.10, 0.02)
    left_axes.set_xlim(x_min - x_padding, x_max + x_padding)
    left_axes.set_ylim(y_min - y_padding, y_max + y_padding)
    left_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    left_axes.set_ylabel(str(display_payload.get("y_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    left_axes.set_title(str(display_payload.get("panel_a_title") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    _apply_publication_axes_style(left_axes)
    left_panel_label = left_axes.text(
        0.02,
        0.98,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=reference_color,
        ha="left",
        va="top",
    )

    right_x_values = [float(value) for value in treated_fraction_series["x"]]
    right_y_values = [float(value) for value in treated_fraction_series["y"]]
    right_axes.plot(
        treated_fraction_series["x"],
        treated_fraction_series["y"],
        linewidth=2.2,
        marker="o",
        markersize=4.8,
        color=model_color,
    )
    right_x_padding = max((max(right_x_values) - min(right_x_values)) * 0.04, 0.01)
    right_y_padding = max((max(right_y_values) - min(right_y_values)) * 0.10, 0.5)
    right_axes.set_xlim(min(right_x_values) - right_x_padding, max(right_x_values) + right_x_padding)
    right_axes.set_ylim(min(0.0, min(right_y_values) - right_y_padding), max(right_y_values) + right_y_padding)
    right_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    right_axes.set_ylabel(
        str(display_payload.get("treated_fraction_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    right_axes.set_title(str(display_payload.get("panel_b_title") or "").strip(), fontsize=axis_title_size, fontweight="bold", color=reference_color)
    right_axes.grid(axis="y", color="#e6edf2", linewidth=0.4)
    right_axes.grid(axis="x", visible=False)
    right_axes.spines["top"].set_visible(False)
    right_axes.spines["right"].set_visible(False)
    right_panel_label = right_axes.text(
        0.02,
        0.98,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=reference_color,
        ha="left",
        va="top",
    )

    handles, labels = left_axes.get_legend_handles_labels()
    legend_position = "none" if not show_legend else str(layout_override.get("legend_position") or "lower_center").strip().lower()
    legend = None
    if legend_position != "none":
        if legend_position == "right_bottom":
            legend = fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.98, 0.02), ncol=1, frameon=False)
        else:
            legend = fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=3, frameon=False)
    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        bottom=0.22 if show_legend else 0.12,
        top=0.82 if show_figure_title else 0.90,
        wspace=0.28,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    normalized_reference_line = _normalize_reference_line_to_device_space(
        reference_line=reference_line,
        axes=left_axes,
        figure=fig,
    )
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_left_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_right_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_A",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_B",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=left_axes.get_window_extent(renderer=renderer),
                    box_id="panel_left",
                    box_type="panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_axes.get_window_extent(renderer=renderer),
                    box_id="panel_right",
                    box_type="panel",
                ),
            ],
            "guide_boxes": []
            if legend is None
            else [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "series": series,
                "reference_line": normalized_reference_line,
                "treated_fraction_series": {
                    "label": str(treated_fraction_series["label"]),
                    "x": [float(value) for value in treated_fraction_series["x"]],
                    "y": [float(value) for value in treated_fraction_series["y"]],
                },
                "time_horizon_months": (
                    int(display_payload["time_horizon_months"])
                    if display_payload.get("time_horizon_months") is not None
                    else None
                ),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_time_to_event_discrimination_calibration_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    discrimination_points = list(display_payload.get("discrimination_points") or [])
    calibration_summary = list(display_payload.get("calibration_summary") or [])
    if not discrimination_points or not calibration_summary:
        raise RuntimeError(f"{template_id} requires non-empty discrimination_points and calibration_summary")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    highlight_color = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    marker_size = max(float(stroke.get("marker_size") or 4.5), 3.8)
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.8, 4.3))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    c_index_values = [float(item["c_index"]) for item in discrimination_points]
    x_range = max(max(c_index_values) - min(c_index_values), 0.01)
    x_floor = max(0.0, min(c_index_values) - max(0.012, x_range * 0.8))
    x_ceiling = min(1.0, max(c_index_values) + max(0.012, x_range * 1.2))
    y_positions = list(range(len(discrimination_points)))[::-1]
    left_axes.set_xlim(x_floor, x_ceiling)
    left_axes.set_ylim(-0.5, len(discrimination_points) - 0.5)
    left_axes.set_yticks(y_positions)
    left_axes.set_yticklabels(
        [str(item["label"]) for item in discrimination_points],
        fontsize=tick_size,
        color=neutral_color,
    )
    discrimination_marker_boxes: list[dict[str, Any]] = []
    for y_position, item in zip(y_positions, discrimination_points, strict=True):
        label = str(item["label"])
        c_index = float(item["c_index"])
        point_color = comparator_color if "lasso" in label.casefold() else model_color
        left_axes.hlines(
            y=y_position,
            xmin=x_floor,
            xmax=c_index,
            linewidth=2.1,
            color=point_color,
            zorder=2,
        )
        left_axes.scatter([c_index], [y_position], s=(marker_size * 11.0), color=point_color, zorder=3)
        annotation_text = str(item.get("annotation") or f"{c_index:.3f}").strip()
        x_offset = max(x_range * 0.07, 0.0025)
        text_x = c_index + x_offset
        text_ha = "left"
        if text_x > x_ceiling - x_offset * 0.35:
            text_x = c_index - x_offset
            text_ha = "right"
        left_axes.text(
            text_x,
            y_position + 0.02,
            annotation_text,
            fontsize=tick_size - 0.2,
            color=neutral_color,
            va="center",
            ha=text_ha,
        )
        discrimination_marker_boxes.append(
            {
                "label": label,
                "c_index": c_index,
                "y": float(y_position),
            }
        )
    left_axes.set_xlabel(
        str(display_payload.get("discrimination_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        "Model",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_title(
        str(display_payload.get("panel_a_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.tick_params(axis="x", labelsize=tick_size)
    left_axes.tick_params(axis="y", length=0, pad=6)
    left_axes.grid(axis="y", visible=False)
    left_axes.grid(axis="x", color=highlight_color, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(left_axes)
    left_axes.text(
        -0.10,
        1.04,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
    )

    risk_deciles = [int(item["group_order"]) for item in calibration_summary]
    predicted_risk = [float(item["predicted_risk_5y"]) * 100.0 for item in calibration_summary]
    observed_risk = [float(item["observed_risk_5y"]) * 100.0 for item in calibration_summary]
    calibration_marker_boxes: list[dict[str, Any]] = []
    right_axes.plot(
        risk_deciles,
        predicted_risk,
        linewidth=2.2,
        marker="o",
        markersize=marker_size,
        color=comparator_color,
        label="Predicted",
        zorder=2,
    )
    right_axes.plot(
        risk_deciles,
        observed_risk,
        linewidth=2.2,
        marker="o",
        markersize=marker_size,
        color=model_color,
        label="Observed",
        zorder=3,
    )
    y_top = max(max(predicted_risk), max(observed_risk))
    right_axes.set_xlim(0.7, max(risk_deciles) + 0.3)
    right_axes.set_ylim(0.0, max(4.0, y_top * 1.18))
    right_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("calibration_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_title(
        str(display_payload.get("panel_b_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_xticks(risk_deciles)
    right_axes.set_xticklabels([str(item) for item in risk_deciles], fontsize=tick_size, color=neutral_color)
    right_axes.tick_params(axis="y", labelsize=tick_size)
    right_axes.grid(axis="y", color=highlight_color, linewidth=0.8, linestyle=":")
    right_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(right_axes)
    right_axes.text(
        -0.10,
        1.04,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
    )
    legend_handles, legend_labels = right_axes.get_legend_handles_labels()
    for group_order, predicted_value, observed_value in zip(risk_deciles, predicted_risk, observed_risk, strict=True):
        calibration_marker_boxes.append(
            {
                "group_order": group_order,
                "predicted_risk_pct": predicted_value,
                "observed_risk_pct": observed_value,
            }
        )

    calibration_callout = display_payload.get("calibration_callout")
    callout_artist = None
    if isinstance(calibration_callout, dict):
        callout_group_label = str(calibration_callout.get("group_label") or "").strip()
        callout_predicted = float(calibration_callout["predicted_risk_5y"]) * 100.0
        callout_observed = float(calibration_callout["observed_risk_5y"]) * 100.0
        callout_events = int(calibration_callout.get("events_5y") or 0)
        callout_n = int(calibration_callout.get("n") or 0)
        callout_lines = _wrap_flow_text_to_width(
            (
                f"{callout_group_label}: {callout_predicted:.2f}% predicted, "
                f"{callout_observed:.2f}% observed, {callout_events}/{callout_n} events"
            ),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.19,
            font_size=max(tick_size - 0.6, 8.6),
            font_weight="normal",
        )
        callout_artist = right_axes.text(
            0.03,
            0.88,
            "\n".join(callout_lines),
            transform=right_axes.transAxes,
            fontsize=max(tick_size - 0.6, 8.6),
            color=neutral_color,
            ha="left",
            va="top",
            bbox={
                "boxstyle": "round,pad=0.26,rounding_size=0.18",
                "facecolor": matplotlib.colors.to_rgba(highlight_color, alpha=0.94),
                "edgecolor": neutral_color,
                "linewidth": 0.9,
            },
        )

    fig.subplots_adjust(
        left=0.10,
        right=0.96,
        top=0.72 if show_figure_title else 0.78,
        bottom=0.24,
        wspace=0.28,
    )
    legend = fig.legend(
        legend_handles,
        legend_labels,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.50, 0.035),
        ncol=min(2, max(1, len(legend_labels))),
    )
    fig.canvas.draw()
    if callout_artist is not None:
        renderer = fig.canvas.get_renderer()
        right_panel_bbox = right_axes.get_window_extent(renderer=renderer)
        right_title_bbox = right_axes.title.get_window_extent(renderer=renderer)
        callout_bbox = callout_artist.get_window_extent(renderer=renderer)
        horizontal_padding_px = max(right_panel_bbox.width * 0.03, 10.0)
        vertical_padding_px = max(right_panel_bbox.height * 0.08, 12.0)
        target_x0_px = right_panel_bbox.x0 + horizontal_padding_px
        target_y1_px = min(right_panel_bbox.y1 - vertical_padding_px, right_title_bbox.y0 - vertical_padding_px)
        minimum_y1_px = right_panel_bbox.y0 + vertical_padding_px + callout_bbox.height
        target_y1_px = max(target_y1_px, minimum_y1_px)
        target_axes_x, target_axes_y = right_axes.transAxes.inverted().transform((target_x0_px, target_y1_px))
        callout_artist.set_position((float(target_axes_x), float(target_axes_y)))
        fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_left_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="calibration_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="calibration_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_right_title",
            box_type="panel_title",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    for index, marker in enumerate(discrimination_marker_boxes, start=1):
        marker_width = max((x_ceiling - x_floor) * 0.015, 0.002)
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=left_axes,
                figure=fig,
                x0=float(marker["c_index"]) - marker_width,
                y0=float(marker["y"]) - 0.14,
                x1=float(marker["c_index"]) + marker_width,
                y1=float(marker["y"]) + 0.14,
                box_id=f"discrimination_marker_{index}",
                box_type="metric_marker",
            )
        )
    for index, marker in enumerate(calibration_marker_boxes, start=1):
        marker_half_width = 0.14
        marker_half_height = max(y_top * 0.03, 0.18)
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=right_axes,
                figure=fig,
                x0=float(marker["group_order"]) - marker_half_width,
                y0=float(marker["predicted_risk_pct"]) - marker_half_height,
                x1=float(marker["group_order"]) + marker_half_width,
                y1=float(marker["predicted_risk_pct"]) + marker_half_height,
                box_id=f"predicted_marker_{index}",
                box_type="metric_marker",
            )
        )
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=right_axes,
                figure=fig,
                x0=float(marker["group_order"]) - marker_half_width,
                y0=float(marker["observed_risk_pct"]) - marker_half_height,
                x1=float(marker["group_order"]) + marker_half_width,
                y1=float(marker["observed_risk_pct"]) + marker_half_height,
                box_id=f"observed_marker_{index}",
                box_type="metric_marker",
            )
        )
    if callout_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=callout_artist.get_window_extent(renderer=renderer),
                box_id="annotation_callout",
                box_type="annotation_block",
            )
        )
    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.get_window_extent(renderer=renderer),
            box_id="panel_left",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.get_window_extent(renderer=renderer),
            box_id="panel_right",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend",
            box_type="legend",
        )
    ]
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "discrimination_points": discrimination_points,
                "calibration_summary": calibration_summary,
                "calibration_callout": calibration_callout,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_generalizability_subgroup_composite_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    overview_rows = list(display_payload.get("overview_rows") or [])
    subgroup_rows = list(display_payload.get("subgroup_rows") or [])
    if not overview_rows or not subgroup_rows:
        raise RuntimeError(f"{template_id} requires non-empty overview_rows and subgroup_rows")

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

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    light_fill = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    primary_label = str(display_payload.get("primary_label") or "").strip()
    comparator_label = str(display_payload.get("comparator_label") or "").strip()

    overview_values = [float(row["metric_value"]) for row in overview_rows]
    if comparator_label:
        overview_values.extend(float(row["comparator_metric_value"]) for row in overview_rows)
    overview_min = min(overview_values)
    overview_max = max(overview_values)
    overview_span = max(overview_max - overview_min, 1e-6)
    overview_padding = max(overview_span * 0.16, 0.03)
    overview_support_margin = max(overview_span * 0.36, 0.08)
    overview_panel_xmin = overview_min - overview_padding
    overview_panel_xmax = overview_max + overview_padding + overview_support_margin
    overview_support_x = overview_max + overview_padding * 0.35

    subgroup_values = [float(display_payload["subgroup_reference_value"])]
    for row in subgroup_rows:
        subgroup_values.extend((float(row["lower"]), float(row["upper"]), float(row["estimate"])))
    subgroup_min = min(subgroup_values)
    subgroup_max = max(subgroup_values)
    subgroup_span = max(subgroup_max - subgroup_min, 1e-6)
    subgroup_padding = max(subgroup_span * 0.16, 0.03)
    subgroup_panel_xmin = subgroup_min - subgroup_padding
    subgroup_panel_xmax = subgroup_max + subgroup_padding
    max_rows = max(len(overview_rows), len(subgroup_rows))
    figure_height = max(4.8, 0.54 * max_rows + 2.6)
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [1.18, 1.0]},
        squeeze=False,
    )
    overview_axes, subgroup_axes = axes[0]
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=reference_color,
            y=0.985,
        )

    overview_row_label_specs: list[tuple[str, float]] = []
    overview_support_label_artists: list[Any] = []
    overview_metric_artists: list[Any] = []
    overview_comparator_artists: list[Any] = []
    overview_metrics_for_sidecar: list[dict[str, Any]] = []
    for row_index, row in enumerate(overview_rows):
        y_pos = float(row_index)
        overview_row_label_specs.append((str(row["cohort_label"]), y_pos))
        overview_support_label_artists.append(
            overview_axes.text(
                overview_support_x,
                y_pos,
                f"n={int(row['support_count'])}",
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.1, 7.8),
                color="#475569",
                clip_on=False,
            )
        )
        if comparator_label:
            overview_comparator_artists.append(
                overview_axes.plot(
                    float(row["comparator_metric_value"]),
                    y_pos,
                    marker="o",
                    markersize=marker_size + 1.0,
                    markerfacecolor="white",
                    markeredgecolor=comparator_color,
                    markeredgewidth=1.1,
                    linestyle="None",
                    zorder=3,
                )[0]
            )
        overview_metric_artists.append(
            overview_axes.plot(
                float(row["metric_value"]),
                y_pos,
                marker="o",
                markersize=marker_size + 1.2,
                markerfacecolor=model_color,
                markeredgecolor=model_color,
                linestyle="None",
                zorder=4,
            )[0]
        )
        sidecar_row = {
            "cohort_id": str(row["cohort_id"]),
            "cohort_label": str(row["cohort_label"]),
            "support_count": int(row["support_count"]),
            "metric_value": float(row["metric_value"]),
            "label_box_id": f"overview_row_label_{row_index + 1}",
            "support_label_box_id": f"overview_support_label_{row_index + 1}",
            "metric_marker_box_id": f"overview_metric_marker_{row_index + 1}",
        }
        if row.get("event_count") is not None:
            sidecar_row["event_count"] = int(row["event_count"])
        if comparator_label:
            sidecar_row["comparator_metric_value"] = float(row["comparator_metric_value"])
            sidecar_row["comparator_marker_box_id"] = f"overview_comparator_marker_{row_index + 1}"
        overview_metrics_for_sidecar.append(sidecar_row)

    overview_axes.set_xlim(overview_panel_xmin, overview_panel_xmax)
    overview_axes.set_ylim(-0.7, len(overview_rows) - 0.3)
    overview_axes.invert_yaxis()
    overview_axes.set_yticks([])
    overview_axes.set_xlabel(
        str(display_payload.get("overview_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    overview_axes.set_title(
        str(display_payload.get("overview_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
        pad=10.0,
    )
    overview_axes.tick_params(axis="x", labelsize=tick_size, colors=reference_color)
    overview_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.65, zorder=0)
    _apply_publication_axes_style(overview_axes)

    subgroup_row_label_specs: list[tuple[str, float]] = []
    subgroup_ci_artists: list[Any] = []
    subgroup_estimate_artists: list[Any] = []
    subgroup_metrics_for_sidecar: list[dict[str, Any]] = []
    for row_index, row in enumerate(subgroup_rows):
        y_pos = float(row_index)
        subgroup_row_label_specs.append((str(row["subgroup_label"]), y_pos))
        subgroup_ci_artists.append(
            subgroup_axes.plot(
                [float(row["lower"]), float(row["upper"])],
                [y_pos, y_pos],
                color=reference_color,
                linewidth=1.4,
                zorder=2,
            )[0]
        )
        subgroup_estimate_artists.append(
            subgroup_axes.plot(
                float(row["estimate"]),
                y_pos,
                marker="s",
                markersize=marker_size + 0.8,
                markerfacecolor=model_color,
                markeredgecolor=model_color,
                linestyle="None",
                zorder=3,
            )[0]
        )
        sidecar_row = {
            "subgroup_id": str(row["subgroup_id"]),
            "subgroup_label": str(row["subgroup_label"]),
            "estimate": float(row["estimate"]),
            "lower": float(row["lower"]),
            "upper": float(row["upper"]),
            "label_box_id": f"subgroup_row_label_{row_index + 1}",
            "ci_box_id": f"subgroup_ci_{row_index + 1}",
            "estimate_box_id": f"subgroup_estimate_{row_index + 1}",
        }
        if row.get("group_n") is not None:
            sidecar_row["group_n"] = int(row["group_n"])
        subgroup_metrics_for_sidecar.append(sidecar_row)

    subgroup_axes.axvline(
        float(display_payload["subgroup_reference_value"]),
        color=comparator_color if comparator_label else reference_color,
        linewidth=1.0,
        linestyle="--",
        zorder=1,
    )
    subgroup_axes.set_xlim(subgroup_panel_xmin, subgroup_panel_xmax)
    subgroup_axes.set_ylim(-0.7, len(subgroup_rows) - 0.3)
    subgroup_axes.invert_yaxis()
    subgroup_axes.set_yticks([])
    subgroup_axes.set_xlabel(
        str(display_payload.get("subgroup_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    subgroup_axes.set_title(
        str(display_payload.get("subgroup_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
        pad=10.0,
    )
    subgroup_axes.tick_params(axis="x", labelsize=tick_size, colors=reference_color)
    subgroup_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.65, zorder=0)
    _apply_publication_axes_style(subgroup_axes)

    legend = None
    if comparator_label:
        legend = fig.legend(
            handles=[
                matplotlib.lines.Line2D(
                    [], [], marker="o", linestyle="None", markersize=marker_size + 1.2, color=model_color, label=primary_label
                ),
                matplotlib.lines.Line2D(
                    [],
                    [],
                    marker="o",
                    linestyle="None",
                    markersize=marker_size + 1.0,
                    markerfacecolor="white",
                    markeredgecolor=comparator_color,
                    color=comparator_color,
                    label=comparator_label,
                ),
            ],
            title="Model context",
            frameon=False,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.02),
            ncol=2,
            borderaxespad=0.0,
        )

    subplot_top = 0.88 if show_figure_title else 0.94
    subplot_bottom = 0.14 if comparator_label else 0.11
    fig.subplots_adjust(left=0.11, right=0.97, top=subplot_top, bottom=subplot_bottom, wspace=0.36)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    overview_row_label_artists: list[Any] = []
    subgroup_row_label_artists: list[Any] = []

    overview_panel_bbox = overview_axes.get_window_extent(renderer=renderer)
    subgroup_panel_bbox = subgroup_axes.get_window_extent(renderer=renderer)
    overview_panel_x0, _ = fig.transFigure.inverted().transform((overview_panel_bbox.x0, overview_panel_bbox.y0))
    subgroup_panel_x0, _ = fig.transFigure.inverted().transform((subgroup_panel_bbox.x0, subgroup_panel_bbox.y0))
    outboard_gap = 0.008

    for label_text, y_pos in overview_row_label_specs:
        _, label_y = _data_point_to_figure_xy(
            axes=overview_axes,
            figure=fig,
            x=overview_panel_xmin,
            y=y_pos,
        )
        overview_row_label_artists.append(
            fig.text(
                overview_panel_x0 - outboard_gap,
                label_y,
                label_text,
                fontsize=max(tick_size - 0.3, 8.6),
                color=reference_color,
                ha="right",
                va="center",
            )
        )

    for label_text, y_pos in subgroup_row_label_specs:
        _, label_y = _data_point_to_figure_xy(
            axes=subgroup_axes,
            figure=fig,
            x=subgroup_panel_xmin,
            y=y_pos,
        )
        subgroup_row_label_artists.append(
            fig.text(
                subgroup_panel_x0 - outboard_gap,
                label_y,
                label_text,
                fontsize=max(tick_size - 0.3, 8.6),
                color=reference_color,
                ha="right",
                va="center",
            )
        )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.2),
            fontweight="bold",
            color=reference_color,
            ha="left",
            va="top",
        )

    overview_panel_label = _add_panel_label(axes_item=overview_axes, label="A")
    subgroup_panel_label = _add_panel_label(axes_item=subgroup_axes, label="B")
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
                bbox=overview_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=overview_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_B",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=overview_panel_label.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_panel_label.get_window_extent(renderer=renderer),
                box_id="panel_label_B",
                box_type="panel_label",
            ),
        ]
    )
    for index, artist in enumerate(overview_row_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_row_label_{index}",
                box_type="overview_row_label",
            )
        )
    for index, artist in enumerate(overview_support_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_support_label_{index}",
                box_type="support_label",
            )
        )
    for index, artist in enumerate(overview_metric_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_metric_marker_{index}",
                box_type="overview_metric_marker",
            )
        )
    for index, artist in enumerate(overview_comparator_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_comparator_marker_{index}",
                box_type="overview_comparator_marker",
            )
        )
    for index, artist in enumerate(subgroup_row_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_row_label_{index}",
                box_type="subgroup_row_label",
            )
        )
    for index, artist in enumerate(subgroup_ci_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_ci_{index}",
                box_type="ci_segment",
            )
        )
    for index, artist in enumerate(subgroup_estimate_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_estimate_{index}",
                box_type="estimate_marker",
            )
        )

    guide_boxes: list[dict[str, Any]] = []
    if legend is not None:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend",
                box_type="legend",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=overview_axes.get_window_extent(renderer=renderer),
                    box_id="overview_panel",
                    box_type="panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=subgroup_axes.get_window_extent(renderer=renderer),
                    box_id="subgroup_panel",
                    box_type="panel",
                ),
            ],
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_family": str(display_payload.get("metric_family") or "").strip(),
                "primary_label": primary_label,
                "comparator_label": comparator_label,
                "legend_title": "Model context" if comparator_label else "",
                "legend_labels": [primary_label, comparator_label] if comparator_label else [],
                "overview_rows": overview_metrics_for_sidecar,
                "subgroup_reference_value": float(display_payload["subgroup_reference_value"]),
                "subgroup_rows": subgroup_metrics_for_sidecar,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_multicenter_generalizability_overview(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    center_event_counts = list(display_payload.get("center_event_counts") or [])
    coverage_panels = list(display_payload.get("coverage_panels") or [])
    if not center_event_counts or not coverage_panels:
        raise RuntimeError(f"{template_id} requires non-empty center_event_counts and coverage_panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
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

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    light_fill = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    audit_color = str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F"

    def _resolve_center_axis_labels(labels: list[str]) -> tuple[list[str], str, str]:
        if not labels:
            return [], "verbatim", "Anonymous center identifier"
        parsed: list[tuple[str, str]] = []
        for label in labels:
            match = re.fullmatch(r"\s*([^\d]+?)\s*(\d+)\s*", label)
            if match is None:
                return labels, "verbatim", "Anonymous center identifier"
            prefix = re.sub(r"\s+", " ", match.group(1)).strip()
            digits = match.group(2)
            if not prefix:
                return labels, "verbatim", "Anonymous center identifier"
            parsed.append((prefix, digits))
        normalized_prefixes = {prefix.casefold() for prefix, _ in parsed}
        compacted_labels = [digits for _, digits in parsed]
        if len(normalized_prefixes) != 1 or len(set(compacted_labels)) != len(compacted_labels):
            return labels, "verbatim", "Anonymous center identifier"
        shared_prefix = parsed[0][0]
        axis_title = f"{shared_prefix} ID"
        return compacted_labels, "shared_prefix_compacted", axis_title

    figure_height = max(7.0, 0.18 * len(center_event_counts) + 5.8)
    fig = plt.figure(figsize=(10.8, figure_height))
    grid = fig.add_gridspec(2, 2, height_ratios=[2.0, 1.0], hspace=0.38, width_ratios=[1.0, 1.0])
    center_axes = fig.add_subplot(grid[0, :])
    region_axes = fig.add_subplot(grid[1, 0])
    right_grid = grid[1, 1].subgridspec(2, 1, hspace=0.85)
    north_south_axes = fig.add_subplot(right_grid[0, 0])
    urban_rural_axes = fig.add_subplot(right_grid[1, 0])
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )
    center_colors = {"train": comparator_color, "validation": model_color}
    center_labels = [str(item["center_label"]) for item in center_event_counts]
    center_tick_labels, center_label_mode, center_axis_title = _resolve_center_axis_labels(center_labels)
    if not center_tick_labels:
        center_tick_labels = center_labels
    center_values = [int(item["event_count"]) for item in center_event_counts]
    center_split_buckets = [str(item["split_bucket"]) for item in center_event_counts]
    center_bars = center_axes.bar(
        center_tick_labels,
        center_values,
        color=[center_colors[item] for item in center_split_buckets],
        edgecolor="none",
        linewidth=0,
    )
    center_axes.set_ylabel(
        str(display_payload.get("center_event_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    center_axes.set_xlabel(center_axis_title, fontsize=axis_title_size, fontweight="bold", color=neutral_color)
    center_axes.set_title(
        "Center-level support across the frozen split",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=10,
    )
    center_axes.grid(axis="y", linestyle=":", color=light_fill, zorder=0)
    center_axes.tick_params(axis="x", rotation=90, labelsize=max(tick_size - 3.0, 6.0), colors=neutral_color)
    center_axes.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
    _apply_publication_axes_style(center_axes)
    legend = fig.legend(
        handles=[
            matplotlib.patches.Patch(color=center_colors["train"], label="Train"),
            matplotlib.patches.Patch(color=center_colors["validation"], label="Validation"),
        ],
        title="Split",
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=2,
        borderaxespad=0.0,
    )
    coverage_axes_by_role = {
        "wide_left": region_axes,
        "top_right": north_south_axes,
        "bottom_right": urban_rural_axes,
    }
    coverage_bar_artists: list[tuple[str, Any]] = []
    for panel in coverage_panels:
        axes = coverage_axes_by_role[str(panel["layout_role"])]
        labels = [str(bar["label"]) for bar in panel["bars"]]
        counts = [int(bar["count"]) for bar in panel["bars"]]
        if panel["layout_role"] == "wide_left":
            colors = [neutral_color] * len(counts)
        elif panel["layout_role"] == "top_right":
            colors = [neutral_color, comparator_color][: len(counts)] or [neutral_color]
        else:
            default_palette = [model_color, audit_color, light_fill, comparator_color]
            colors = default_palette[: len(counts)]
            if len(colors) < len(counts):
                colors.extend([default_palette[-1]] * (len(counts) - len(colors)))
        bars = axes.bar(labels, counts, color=colors, edgecolor="none")
        axes.set_title(str(panel["title"]), fontsize=max(axis_title_size - 1.0, 9.8), fontweight="bold", color=neutral_color, pad=8)
        axes.set_ylabel(
            str(display_payload.get("coverage_y_label") or "").strip(),
            fontsize=max(axis_title_size - 2.0, 9.0),
            color=neutral_color,
        )
        axes.grid(axis="y", linestyle=":", color=light_fill, zorder=0)
        if panel["layout_role"] == "wide_left":
            axes.tick_params(axis="x", rotation=45, labelsize=max(tick_size - 2.0, 8.0), colors=neutral_color)
        else:
            axes.tick_params(axis="x", labelsize=max(tick_size - 2.0, 8.0), colors=neutral_color)
        axes.tick_params(axis="y", labelsize=max(tick_size - 1.0, 8.5), colors=neutral_color)
        _apply_publication_axes_style(axes)
        upper = max(counts, default=0)
        y_offset = upper * 0.02 if upper > 0 else 0.0
        for idx, value in enumerate(counts):
            axes.text(
                idx,
                value + y_offset,
                f"{value:,}",
                ha="center",
                va="bottom",
                fontsize=max(tick_size - 2.0, 8.0),
                color=neutral_color,
            )
        for idx, artist in enumerate(bars, start=1):
            coverage_bar_artists.append((f"{panel['panel_id']}_{idx}", artist))

    subplot_left = 0.08
    subplot_right = 0.97
    subplot_bottom = 0.10
    subplot_top = 0.90 if show_figure_title else 0.95
    fig.subplots_adjust(top=subplot_top, bottom=subplot_bottom, left=subplot_left, right=subplot_right)
    fig.canvas.draw()
    for _ in range(3):
        renderer = fig.canvas.get_renderer()
        legend_bbox = legend.get_window_extent(renderer=renderer)
        overflow_px = float(legend_bbox.y1 - fig.bbox.height)
        if overflow_px <= 0.0:
            break
        min_top = 0.82 if show_figure_title else 0.88
        top_delta = overflow_px / max(float(fig.bbox.height), 1.0)
        next_top = max(min_top, subplot_top - top_delta - 0.01)
        if next_top >= subplot_top - 1e-6:
            break
        subplot_top = next_top
        fig.subplots_adjust(top=subplot_top, bottom=subplot_bottom, left=subplot_left, right=subplot_right)
        fig.canvas.draw()

    renderer = fig.canvas.get_renderer()
    center_panel_bbox = matplotlib.transforms.Bbox.union(
        [
            center_axes.get_window_extent(renderer=renderer),
            center_axes.title.get_window_extent(renderer=renderer),
        ]
    )
    region_panel_bbox = matplotlib.transforms.Bbox.union(
        [
            region_axes.get_window_extent(renderer=renderer),
            region_axes.title.get_window_extent(renderer=renderer),
        ]
    )
    right_stack_bbox = matplotlib.transforms.Bbox.union(
        [
            north_south_axes.get_window_extent(renderer=renderer),
            urban_rural_axes.get_window_extent(renderer=renderer),
            north_south_axes.title.get_window_extent(renderer=renderer),
        ]
    )

    def _add_figure_panel_label(*, panel_bbox, label: str) -> Any:
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.014, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 2.6, 15.0),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    center_panel_label = _add_figure_panel_label(panel_bbox=center_panel_bbox, label="A")
    wide_left_panel_label = _add_figure_panel_label(panel_bbox=region_panel_bbox, label="B")
    right_stack_panel_label = _add_figure_panel_label(panel_bbox=right_stack_bbox, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=center_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="center_event_y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=center_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="center_event_x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=region_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="coverage_y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=center_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_A",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=wide_left_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_B",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_stack_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_C",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    for index, artist in enumerate(center_bars, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"center_event_bar_{index}",
                box_type="center_event_bar",
            )
        )
    for box_suffix, artist in coverage_bar_artists:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"coverage_bar_{box_suffix}",
                box_type="coverage_bar",
            )
        )
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=center_panel_bbox,
                    box_id="center_event_panel",
                    box_type="center_event_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=region_panel_bbox,
                    box_id="coverage_panel_wide_left",
                    box_type="coverage_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=north_south_axes.get_window_extent(renderer=renderer),
                    box_id="coverage_panel_top_right",
                    box_type="coverage_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=urban_rural_axes.get_window_extent(renderer=renderer),
                    box_id="coverage_panel_bottom_right",
                    box_type="coverage_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_stack_bbox,
                    box_id="coverage_panel_right_stack",
                    box_type="coverage_panel",
                ),
            ],
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "center_event_counts": center_event_counts,
                "coverage_panels": coverage_panels,
                "center_label_mode": center_label_mode,
                "center_tick_labels": center_tick_labels,
                "center_axis_title": center_axis_title,
                "legend_title": "Split",
                "legend_labels": ["Train", "Validation"],
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_single_cell_atlas_overview_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    embedding_points = list(display_payload.get("embedding_points") or [])
    composition_groups = list(display_payload.get("composition_groups") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if not embedding_points or not composition_groups or not matrix_cells or not row_order or not column_order:
        raise RuntimeError(
            f"{template_id} requires non-empty embedding_points, composition_groups, row_order, column_order, and cells"
        )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
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

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    state_palette = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#9467bd").strip() or "#9467bd",
        str(palette.get("secondary_soft") or "#17becf").strip() or "#17becf",
    ]
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    state_labels = [str(item["label"]) for item in column_order]
    row_labels = [str(item["label"]) for item in row_order]
    state_color_lookup = {
        label: state_palette[index % len(state_palette)] for index, label in enumerate(state_labels)
    }

    fig, (embedding_axes, composition_axes, heatmap_axes) = plt.subplots(
        1,
        3,
        figsize=(13.6, 4.9),
        gridspec_kw={"width_ratios": [1.02, 0.94, 1.00]},
    )
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )

    for state_label in state_labels:
        state_points = [item for item in embedding_points if str(item["state_label"]) == state_label]
        if not state_points:
            continue
        embedding_axes.scatter(
            [float(item["x"]) for item in state_points],
            [float(item["y"]) for item in state_points],
            label=state_label,
            s=38,
            alpha=0.92,
            color=state_color_lookup[state_label],
            edgecolors="white",
            linewidths=0.4,
        )
    embedding_axes.set_title(
        str(display_payload.get("embedding_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    embedding_axes.set_xlabel(
        str(display_payload.get("embedding_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    embedding_axes.set_ylabel(
        str(display_payload.get("embedding_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    embedding_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    embedding_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(embedding_axes)
    embedding_annotation = str(display_payload.get("embedding_annotation") or "").strip()
    embedding_annotation_artist = None
    if embedding_annotation:
        embedding_annotation_artist = embedding_axes.text(
            0.03,
            0.05,
            embedding_annotation,
            transform=embedding_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    ordered_composition_groups = sorted(composition_groups, key=lambda item: int(item["group_order"]))
    group_labels = [str(item["group_label"]) for item in ordered_composition_groups]
    y_positions = list(range(len(ordered_composition_groups)))
    cumulative = [0.0] * len(ordered_composition_groups)
    for state_label in state_labels:
        state_values = []
        for group in ordered_composition_groups:
            state_lookup = {
                str(item["state_label"]): float(item["proportion"]) for item in list(group.get("state_proportions") or [])
            }
            state_values.append(state_lookup[state_label])
        bar_artists = composition_axes.barh(
            y_positions,
            state_values,
            left=cumulative,
            height=0.62,
            color=matplotlib.colors.to_rgba(state_color_lookup[state_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
            label=state_label,
        )
        for bar_artist, value, left_start in zip(bar_artists, state_values, cumulative, strict=True):
            if value < 0.12:
                continue
            composition_axes.text(
                left_start + value / 2.0,
                float(bar_artist.get_y()) + float(bar_artist.get_height()) / 2.0,
                f"{value * 100:.0f}%",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.6, 7.2),
                color="#13293d",
            )
        cumulative = [left_start + value for left_start, value in zip(cumulative, state_values, strict=True)]
    composition_axes.set_xlim(0.0, 1.0)
    composition_axes.set_yticks(y_positions)
    composition_axes.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
    composition_axes.invert_yaxis()
    composition_axes.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
    composition_axes.set_title(
        str(display_payload.get("composition_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_xlabel(
        str(display_payload.get("composition_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_ylabel(
        str(display_payload.get("composition_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
    composition_axes.tick_params(axis="y", length=0, colors=neutral_color)
    composition_axes.grid(axis="x", color=light_fill, linewidth=0.8, linestyle=":")
    composition_axes.grid(axis="y", visible=False)
    _apply_publication_axes_style(composition_axes)
    composition_annotation = str(display_payload.get("composition_annotation") or "").strip()
    composition_annotation_artist = None
    if composition_annotation:
        composition_annotation_artist = composition_axes.text(
            0.03,
            0.05,
            composition_annotation,
            transform=composition_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    matrix_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in matrix_cells}
    matrix_rows = [[matrix_lookup[(state_label, row_label)] for state_label in state_labels] for row_label in row_labels]
    vmax = max(abs(value) for value in matrix_lookup.values()) if matrix_lookup else 1.0
    vmax = max(vmax, 1e-6)
    heatmap_artist = heatmap_axes.imshow(matrix_rows, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
    heatmap_axes.set_title(
        str(display_payload.get("heatmap_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xlabel(
        str(display_payload.get("heatmap_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_ylabel(
        str(display_payload.get("heatmap_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xticks(range(len(state_labels)))
    heatmap_axes.set_xticklabels(state_labels, fontsize=tick_size, rotation=22, ha="right", color=neutral_color)
    heatmap_axes.set_yticks(range(len(row_labels)))
    heatmap_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    heatmap_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(heatmap_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, state_label in enumerate(state_labels):
            value = matrix_lookup[(state_label, row_label)]
            heatmap_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )
    heatmap_annotation = str(display_payload.get("heatmap_annotation") or "").strip()
    heatmap_annotation_artist = None
    if heatmap_annotation:
        heatmap_annotation_artist = heatmap_axes.text(
            0.03,
            0.05,
            heatmap_annotation,
            transform=heatmap_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.06,
        right=0.92,
        top=max(0.72, title_top) if show_figure_title else 0.86,
        bottom=0.24,
        wspace=0.32,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.07, 0.02),
        ncol=min(4, max(1, len(state_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=heatmap_axes, fraction=0.050, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_figure_panel_label(*, axes_item, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_figure_panel_label(axes_item=embedding_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes_item=composition_axes, label="B")
    panel_label_c = _add_figure_panel_label(axes_item=heatmap_axes, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=embedding_axes.title.get_window_extent(renderer=renderer),
            box_id="embedding_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=embedding_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="embedding_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=embedding_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="embedding_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.title.get_window_extent(renderer=renderer),
            box_id="composition_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.title.get_window_extent(renderer=renderer),
            box_id="heatmap_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_y_axis_title",
            box_type="subplot_y_axis_title",
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
            bbox=panel_label_c.get_window_extent(renderer=renderer),
            box_id="panel_label_C",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    for annotation_artist, box_id in (
        (embedding_annotation_artist, "embedding_annotation"),
        (composition_annotation_artist, "composition_annotation"),
        (heatmap_annotation_artist, "heatmap_annotation"),
    ):
        if annotation_artist is None:
            continue
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=annotation_artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_text",
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=embedding_axes.get_window_extent(renderer=renderer),
            box_id="panel_embedding",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.get_window_extent(renderer=renderer),
            box_id="panel_composition",
            box_type="composition_panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.get_window_extent(renderer=renderer),
            box_id="panel_heatmap",
            box_type="heatmap_tile_region",
        ),
    ]

    normalized_points: list[dict[str, Any]] = []
    for item in embedding_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=embedding_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_point = {
            "x": point_x,
            "y": point_y,
            "state_label": str(item["state_label"]),
        }
        group_label = str(item.get("group_label") or "").strip()
        if group_label:
            normalized_point["group_label"] = group_label
        normalized_points.append(normalized_point)

    normalized_composition_groups: list[dict[str, Any]] = []
    for group in ordered_composition_groups:
        normalized_composition_groups.append(
            {
                "group_label": str(group["group_label"]),
                "group_order": int(group["group_order"]),
                "state_proportions": [
                    {
                        "state_label": str(item["state_label"]),
                        "proportion": float(item["proportion"]),
                    }
                    for item in list(group.get("state_proportions") or [])
                ],
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=colorbar.ax.get_window_extent(renderer=renderer),
                    box_id="colorbar",
                    box_type="colorbar",
                ),
            ],
            "metrics": {
                "points": normalized_points,
                "state_labels": state_labels,
                "row_labels": row_labels,
                "composition_groups": normalized_composition_groups,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_spatial_niche_map_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    spatial_points = list(display_payload.get("spatial_points") or [])
    composition_groups = list(display_payload.get("composition_groups") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if not spatial_points or not composition_groups or not matrix_cells or not row_order or not column_order:
        raise RuntimeError(
            f"{template_id} requires non-empty spatial_points, composition_groups, row_order, column_order, and cells"
        )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
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

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    niche_palette = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#9467bd").strip() or "#9467bd",
        str(palette.get("secondary_soft") or "#17becf").strip() or "#17becf",
    ]
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    niche_labels = [str(item["label"]) for item in column_order]
    row_labels = [str(item["label"]) for item in row_order]
    niche_color_lookup = {
        label: niche_palette[index % len(niche_palette)] for index, label in enumerate(niche_labels)
    }

    fig, (spatial_axes, composition_axes, heatmap_axes) = plt.subplots(
        1,
        3,
        figsize=(13.6, 4.9),
        gridspec_kw={"width_ratios": [1.02, 0.94, 1.00]},
    )
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )

    for niche_label in niche_labels:
        niche_points = [item for item in spatial_points if str(item["niche_label"]) == niche_label]
        if not niche_points:
            continue
        spatial_axes.scatter(
            [float(item["x"]) for item in niche_points],
            [float(item["y"]) for item in niche_points],
            label=niche_label,
            s=38,
            alpha=0.92,
            color=niche_color_lookup[niche_label],
            edgecolors="white",
            linewidths=0.4,
        )
    spatial_axes.set_title(
        str(display_payload.get("spatial_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    spatial_axes.set_xlabel(
        str(display_payload.get("spatial_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    spatial_axes.set_ylabel(
        str(display_payload.get("spatial_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    spatial_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    spatial_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(spatial_axes)
    spatial_annotation = str(display_payload.get("spatial_annotation") or "").strip()
    spatial_annotation_artist = None
    if spatial_annotation:
        spatial_annotation_artist = spatial_axes.text(
            0.03,
            0.05,
            spatial_annotation,
            transform=spatial_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    ordered_composition_groups = sorted(composition_groups, key=lambda item: int(item["group_order"]))
    group_labels = [str(item["group_label"]) for item in ordered_composition_groups]
    y_positions = list(range(len(ordered_composition_groups)))
    cumulative = [0.0] * len(ordered_composition_groups)
    for niche_label in niche_labels:
        niche_values = []
        for group in ordered_composition_groups:
            niche_lookup = {
                str(item["niche_label"]): float(item["proportion"]) for item in list(group.get("niche_proportions") or [])
            }
            niche_values.append(niche_lookup[niche_label])
        bar_artists = composition_axes.barh(
            y_positions,
            niche_values,
            left=cumulative,
            height=0.62,
            color=matplotlib.colors.to_rgba(niche_color_lookup[niche_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
            label=niche_label,
        )
        for bar_artist, value, left_start in zip(bar_artists, niche_values, cumulative, strict=True):
            if value < 0.12:
                continue
            composition_axes.text(
                left_start + value / 2.0,
                float(bar_artist.get_y()) + float(bar_artist.get_height()) / 2.0,
                f"{value * 100:.0f}%",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.6, 7.2),
                color="#13293d",
            )
        cumulative = [left_start + value for left_start, value in zip(cumulative, niche_values, strict=True)]
    composition_axes.set_xlim(0.0, 1.0)
    composition_axes.set_yticks(y_positions)
    composition_axes.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
    composition_axes.invert_yaxis()
    composition_axes.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
    composition_axes.set_title(
        str(display_payload.get("composition_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_xlabel(
        str(display_payload.get("composition_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_ylabel(
        str(display_payload.get("composition_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
    composition_axes.tick_params(axis="y", length=0, colors=neutral_color)
    composition_axes.grid(axis="x", color=light_fill, linewidth=0.8, linestyle=":")
    composition_axes.grid(axis="y", visible=False)
    _apply_publication_axes_style(composition_axes)
    composition_annotation = str(display_payload.get("composition_annotation") or "").strip()
    composition_annotation_artist = None
    if composition_annotation:
        composition_annotation_artist = composition_axes.text(
            0.03,
            0.05,
            composition_annotation,
            transform=composition_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    matrix_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in matrix_cells}
    matrix_rows = [[matrix_lookup[(niche_label, row_label)] for niche_label in niche_labels] for row_label in row_labels]
    vmax = max(abs(value) for value in matrix_lookup.values()) if matrix_lookup else 1.0
    vmax = max(vmax, 1e-6)
    heatmap_artist = heatmap_axes.imshow(matrix_rows, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
    heatmap_axes.set_title(
        str(display_payload.get("heatmap_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xlabel(
        str(display_payload.get("heatmap_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_ylabel(
        str(display_payload.get("heatmap_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xticks(range(len(niche_labels)))
    heatmap_axes.set_xticklabels(niche_labels, fontsize=tick_size, rotation=22, ha="right", color=neutral_color)
    heatmap_axes.set_yticks(range(len(row_labels)))
    heatmap_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    heatmap_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(heatmap_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, niche_label in enumerate(niche_labels):
            value = matrix_lookup[(niche_label, row_label)]
            heatmap_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )
    heatmap_annotation = str(display_payload.get("heatmap_annotation") or "").strip()
    heatmap_annotation_artist = None
    if heatmap_annotation:
        heatmap_annotation_artist = heatmap_axes.text(
            0.03,
            0.05,
            heatmap_annotation,
            transform=heatmap_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.06,
        right=0.92,
        top=max(0.72, title_top) if show_figure_title else 0.86,
        bottom=0.24,
        wspace=0.32,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=niche_color_lookup[niche_label], label=niche_label) for niche_label in niche_labels
    ]
    legend = fig.legend(
        legend_handles,
        niche_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.07, 0.02),
        ncol=min(4, max(1, len(niche_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=heatmap_axes, fraction=0.050, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_figure_panel_label(*, axes_item, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_figure_panel_label(axes_item=spatial_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes_item=composition_axes, label="B")
    panel_label_c = _add_figure_panel_label(axes_item=heatmap_axes, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.title.get_window_extent(renderer=renderer),
            box_id="spatial_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="spatial_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="spatial_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.title.get_window_extent(renderer=renderer),
            box_id="composition_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.title.get_window_extent(renderer=renderer),
            box_id="heatmap_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_y_axis_title",
            box_type="subplot_y_axis_title",
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
            bbox=panel_label_c.get_window_extent(renderer=renderer),
            box_id="panel_label_C",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    for annotation_artist, box_id in (
        (spatial_annotation_artist, "spatial_annotation"),
        (composition_annotation_artist, "composition_annotation"),
        (heatmap_annotation_artist, "heatmap_annotation"),
    ):
        if annotation_artist is None:
            continue
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=annotation_artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_text",
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.get_window_extent(renderer=renderer),
            box_id="panel_spatial",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.get_window_extent(renderer=renderer),
            box_id="panel_composition",
            box_type="composition_panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.get_window_extent(renderer=renderer),
            box_id="panel_heatmap",
            box_type="heatmap_tile_region",
        ),
    ]

    normalized_points: list[dict[str, Any]] = []
    for item in spatial_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=spatial_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_point = {
            "x": point_x,
            "y": point_y,
            "niche_label": str(item["niche_label"]),
        }
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_points.append(normalized_point)

    normalized_composition_groups: list[dict[str, Any]] = []
    for group in ordered_composition_groups:
        normalized_composition_groups.append(
            {
                "group_label": str(group["group_label"]),
                "group_order": int(group["group_order"]),
                "niche_proportions": [
                    {
                        "niche_label": str(item["niche_label"]),
                        "proportion": float(item["proportion"]),
                    }
                    for item in list(group.get("niche_proportions") or [])
                ],
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=colorbar.ax.get_window_extent(renderer=renderer),
                    box_id="colorbar",
                    box_type="colorbar",
                ),
            ],
            "metrics": {
                "points": normalized_points,
                "niche_labels": niche_labels,
                "row_labels": row_labels,
                "composition_groups": normalized_composition_groups,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_trajectory_progression_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    trajectory_points = list(display_payload.get("trajectory_points") or [])
    branch_order = list(display_payload.get("branch_order") or [])
    progression_bins = list(display_payload.get("progression_bins") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if not trajectory_points or not branch_order or not progression_bins or not matrix_cells or not row_order or not column_order:
        raise RuntimeError(
            f"{template_id} requires non-empty trajectory_points, branch_order, progression_bins, row_order, column_order, and cells"
        )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
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

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    branch_palette = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#9467bd").strip() or "#9467bd",
        str(palette.get("secondary_soft") or "#17becf").strip() or "#17becf",
    ]
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    branch_labels = [str(item["label"]) for item in branch_order]
    ordered_progression_bins = sorted(progression_bins, key=lambda item: int(item["bin_order"]))
    bin_labels = [str(item["bin_label"]) for item in ordered_progression_bins]
    row_labels = [str(item["label"]) for item in row_order]
    branch_color_lookup = {
        label: branch_palette[index % len(branch_palette)] for index, label in enumerate(branch_labels)
    }

    fig, (trajectory_axes, composition_axes, heatmap_axes) = plt.subplots(
        1,
        3,
        figsize=(13.8, 5.0),
        gridspec_kw={"width_ratios": [1.04, 0.96, 1.00]},
    )
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )

    for branch_label in branch_labels:
        branch_points = sorted(
            [item for item in trajectory_points if str(item["branch_label"]) == branch_label],
            key=lambda item: float(item["pseudotime"]),
        )
        if not branch_points:
            continue
        branch_x = [float(item["x"]) for item in branch_points]
        branch_y = [float(item["y"]) for item in branch_points]
        trajectory_axes.plot(
            branch_x,
            branch_y,
            color=branch_color_lookup[branch_label],
            linewidth=2.1,
            alpha=0.92,
            zorder=2,
        )
        trajectory_axes.scatter(
            branch_x,
            branch_y,
            label=branch_label,
            s=42,
            alpha=0.96,
            color=branch_color_lookup[branch_label],
            edgecolors="white",
            linewidths=0.4,
            zorder=3,
        )
    trajectory_axes.set_title(
        str(display_payload.get("trajectory_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    trajectory_axes.set_xlabel(
        str(display_payload.get("trajectory_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    trajectory_axes.set_ylabel(
        str(display_payload.get("trajectory_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    trajectory_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    trajectory_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(trajectory_axes)
    trajectory_annotation = str(display_payload.get("trajectory_annotation") or "").strip()
    trajectory_annotation_artist = None
    if trajectory_annotation:
        trajectory_annotation_artist = trajectory_axes.text(
            0.03,
            0.05,
            trajectory_annotation,
            transform=trajectory_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    y_positions = list(range(len(ordered_progression_bins)))
    cumulative = [0.0] * len(ordered_progression_bins)
    for branch_label in branch_labels:
        branch_values = []
        for progression_bin in ordered_progression_bins:
            branch_lookup = {
                str(item["branch_label"]): float(item["proportion"])
                for item in list(progression_bin.get("branch_weights") or [])
            }
            branch_values.append(branch_lookup[branch_label])
        bar_artists = composition_axes.barh(
            y_positions,
            branch_values,
            left=cumulative,
            height=0.62,
            color=matplotlib.colors.to_rgba(branch_color_lookup[branch_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
            label=branch_label,
        )
        for bar_artist, value, left_start in zip(bar_artists, branch_values, cumulative, strict=True):
            if value < 0.12:
                continue
            composition_axes.text(
                left_start + value / 2.0,
                float(bar_artist.get_y()) + float(bar_artist.get_height()) / 2.0,
                f"{value * 100:.0f}%",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.6, 7.2),
                color="#13293d",
            )
        cumulative = [left_start + value for left_start, value in zip(cumulative, branch_values, strict=True)]
    composition_axes.set_xlim(0.0, 1.0)
    composition_axes.set_yticks(y_positions)
    composition_axes.set_yticklabels(bin_labels, fontsize=tick_size, color=neutral_color)
    composition_axes.invert_yaxis()
    composition_axes.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
    composition_axes.set_title(
        str(display_payload.get("composition_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_xlabel(
        str(display_payload.get("composition_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_ylabel(
        str(display_payload.get("composition_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
    composition_axes.tick_params(axis="y", length=0, colors=neutral_color)
    composition_axes.grid(axis="x", color=light_fill, linewidth=0.8, linestyle=":")
    composition_axes.grid(axis="y", visible=False)
    _apply_publication_axes_style(composition_axes)
    composition_annotation = str(display_payload.get("composition_annotation") or "").strip()
    composition_annotation_artist = None
    if composition_annotation:
        composition_annotation_artist = composition_axes.text(
            0.03,
            0.05,
            composition_annotation,
            transform=composition_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    matrix_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in matrix_cells}
    matrix_rows = [[matrix_lookup[(bin_label, row_label)] for bin_label in bin_labels] for row_label in row_labels]
    vmax = max(abs(value) for value in matrix_lookup.values()) if matrix_lookup else 1.0
    vmax = max(vmax, 1e-6)
    heatmap_artist = heatmap_axes.imshow(matrix_rows, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
    heatmap_axes.set_title(
        str(display_payload.get("heatmap_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xlabel(
        str(display_payload.get("heatmap_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_ylabel(
        str(display_payload.get("heatmap_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xticks(range(len(bin_labels)))
    heatmap_axes.set_xticklabels(bin_labels, fontsize=tick_size, rotation=22, ha="right", color=neutral_color)
    heatmap_axes.set_yticks(range(len(row_labels)))
    heatmap_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    heatmap_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(heatmap_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, bin_label in enumerate(bin_labels):
            value = matrix_lookup[(bin_label, row_label)]
            heatmap_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )
    heatmap_annotation = str(display_payload.get("heatmap_annotation") or "").strip()
    heatmap_annotation_artist = None
    if heatmap_annotation:
        heatmap_annotation_artist = heatmap_axes.text(
            0.03,
            0.05,
            heatmap_annotation,
            transform=heatmap_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.06,
        right=0.92,
        top=max(0.72, title_top) if show_figure_title else 0.86,
        bottom=0.24,
        wspace=0.32,
    )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            color=branch_color_lookup[branch_label],
            marker="o",
            markersize=6.4,
            linewidth=2.0,
            label=branch_label,
        )
        for branch_label in branch_labels
    ]
    legend = fig.legend(
        legend_handles,
        branch_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.07, 0.02),
        ncol=min(4, max(1, len(branch_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=heatmap_axes, fraction=0.050, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_figure_panel_label(*, axes_item, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_figure_panel_label(axes_item=trajectory_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes_item=composition_axes, label="B")
    panel_label_c = _add_figure_panel_label(axes_item=heatmap_axes, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.title.get_window_extent(renderer=renderer),
            box_id="trajectory_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="trajectory_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="trajectory_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.title.get_window_extent(renderer=renderer),
            box_id="composition_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.title.get_window_extent(renderer=renderer),
            box_id="heatmap_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_y_axis_title",
            box_type="subplot_y_axis_title",
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
            bbox=panel_label_c.get_window_extent(renderer=renderer),
            box_id="panel_label_C",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    for annotation_artist, box_id in (
        (trajectory_annotation_artist, "trajectory_annotation"),
        (composition_annotation_artist, "composition_annotation"),
        (heatmap_annotation_artist, "heatmap_annotation"),
    ):
        if annotation_artist is None:
            continue
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=annotation_artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_text",
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.get_window_extent(renderer=renderer),
            box_id="panel_trajectory",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.get_window_extent(renderer=renderer),
            box_id="panel_composition",
            box_type="composition_panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.get_window_extent(renderer=renderer),
            box_id="panel_heatmap",
            box_type="heatmap_tile_region",
        ),
    ]

    normalized_points: list[dict[str, Any]] = []
    for item in trajectory_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=trajectory_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_points.append(
            {
                "x": point_x,
                "y": point_y,
                "branch_label": str(item["branch_label"]),
                "state_label": str(item["state_label"]),
                "pseudotime": float(item["pseudotime"]),
            }
        )

    normalized_progression_bins: list[dict[str, Any]] = []
    for progression_bin in ordered_progression_bins:
        normalized_progression_bins.append(
            {
                "bin_label": str(progression_bin["bin_label"]),
                "bin_order": int(progression_bin["bin_order"]),
                "pseudotime_start": float(progression_bin["pseudotime_start"]),
                "pseudotime_end": float(progression_bin["pseudotime_end"]),
                "branch_weights": [
                    {
                        "branch_label": str(item["branch_label"]),
                        "proportion": float(item["proportion"]),
                    }
                    for item in list(progression_bin.get("branch_weights") or [])
                ],
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=colorbar.ax.get_window_extent(renderer=renderer),
                    box_id="colorbar",
                    box_type="colorbar",
                ),
            ],
            "metrics": {
                "points": normalized_points,
                "branch_labels": branch_labels,
                "bin_labels": bin_labels,
                "row_labels": row_labels,
                "progression_bins": normalized_progression_bins,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_celltype_signature_heatmap(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    embedding_points = list(display_payload.get("embedding_points") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if not embedding_points or not matrix_cells or not row_order or not column_order:
        raise RuntimeError(f"{template_id} requires non-empty embedding_points, row_order, column_order, and cells")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
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

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    fallback_palette = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#9467bd").strip() or "#9467bd",
        str(palette.get("secondary_soft") or "#17becf").strip() or "#17becf",
    ]
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    fig, (left_axes, right_axes) = plt.subplots(
        1,
        2,
        figsize=(11.2, 4.8),
        gridspec_kw={"width_ratios": [1.0, 0.92]},
    )
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    group_labels = [str(item["label"]) for item in column_order]
    palette_lookup = {
        label: fallback_palette[index % len(fallback_palette)] for index, label in enumerate(group_labels)
    }
    for group_label in group_labels:
        group_points = [item for item in embedding_points if str(item["group"]) == group_label]
        if not group_points:
            continue
        left_axes.scatter(
            [float(item["x"]) for item in group_points],
            [float(item["y"]) for item in group_points],
            label=group_label,
            s=38,
            alpha=0.92,
            color=palette_lookup[group_label],
            edgecolors="white",
            linewidths=0.4,
        )
    left_axes.set_title(
        str(display_payload.get("embedding_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_xlabel(
        str(display_payload.get("embedding_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        str(display_payload.get("embedding_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.tick_params(axis="both", labelsize=tick_size)
    left_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(left_axes)

    embedding_annotation = str(display_payload.get("embedding_annotation") or "").strip()
    embedding_annotation_artist = None
    if embedding_annotation:
        embedding_annotation_artist = left_axes.text(
            0.03,
            0.05,
            embedding_annotation,
            transform=left_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    row_labels = [str(item["label"]) for item in row_order]
    matrix_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in matrix_cells}
    matrix_rows = [[matrix_lookup[(column_label, row_label)] for column_label in group_labels] for row_label in row_labels]
    vmax = max(abs(value) for value in matrix_lookup.values()) if matrix_lookup else 1.0
    vmax = max(vmax, 1e-6)
    heatmap_artist = right_axes.imshow(matrix_rows, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
    right_axes.set_title(
        str(display_payload.get("heatmap_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_xlabel(
        str(display_payload.get("heatmap_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("heatmap_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_xticks(range(len(group_labels)))
    right_axes.set_xticklabels(group_labels, fontsize=tick_size, rotation=22, ha="right", color=neutral_color)
    right_axes.set_yticks(range(len(row_labels)))
    right_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    right_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(right_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, column_label in enumerate(group_labels):
            value = matrix_lookup[(column_label, row_label)]
            right_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )

    heatmap_annotation = str(display_payload.get("heatmap_annotation") or "").strip()
    heatmap_annotation_artist = None
    if heatmap_annotation:
        heatmap_annotation_artist = right_axes.text(
            0.03,
            0.05,
            heatmap_annotation,
            transform=right_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    fig.subplots_adjust(
        left=0.08,
        right=0.90,
        top=0.76 if show_figure_title else 0.82,
        bottom=0.24,
        wspace=0.24,
    )
    legend_handles, legend_labels = left_axes.get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.09, 0.02),
        ncol=min(3, max(1, len(legend_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=right_axes, fraction=0.050, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_figure_panel_label(*, axes, label: str) -> Any:
        panel_bbox = axes.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_figure_panel_label(axes=left_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes=right_axes, label="B")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="embedding_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="embedding_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="embedding_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="heatmap_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_y_axis_title",
            box_type="subplot_y_axis_title",
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
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    if embedding_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=embedding_annotation_artist.get_window_extent(renderer=renderer),
                box_id="embedding_annotation",
                box_type="annotation_text",
            )
        )
    if heatmap_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=heatmap_annotation_artist.get_window_extent(renderer=renderer),
                box_id="heatmap_annotation",
                box_type="annotation_text",
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.get_window_extent(renderer=renderer),
            box_id="panel_left",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.get_window_extent(renderer=renderer),
            box_id="panel_right",
            box_type="heatmap_tile_region",
        ),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        ),
    ]

    normalized_points = []
    for item in embedding_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=left_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_points.append({"x": point_x, "y": point_y, "group": str(item["group"])})

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "points": normalized_points,
                "group_labels": group_labels,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

_PYTHON_EVIDENCE_RENDERERS = {
    "binary_calibration_decision_curve_panel": _render_python_binary_calibration_decision_curve_panel,
    "celltype_signature_heatmap": _render_python_celltype_signature_heatmap,
    "generalizability_subgroup_composite_panel": _render_python_generalizability_subgroup_composite_panel,
    "model_complexity_audit_panel": _render_python_model_complexity_audit_panel,
    "single_cell_atlas_overview_panel": _render_python_single_cell_atlas_overview_panel,
    "spatial_niche_map_panel": _render_python_spatial_niche_map_panel,
    "trajectory_progression_panel": _render_python_trajectory_progression_panel,
    "risk_layering_monotonic_bars": _render_python_risk_layering_monotonic_bars,
    "shap_dependence_panel": _render_python_shap_dependence_panel,
    "shap_summary_beeswarm": _render_python_shap_summary_beeswarm,
    "shap_force_like_summary_panel": _render_python_shap_force_like_summary_panel,
    "shap_waterfall_local_explanation_panel": _render_python_shap_waterfall_local_explanation_panel,
    "time_dependent_roc_comparison_panel": _render_python_time_dependent_roc_comparison_panel,
    "time_to_event_landmark_performance_panel": _render_python_time_to_event_landmark_performance_panel,
    "time_to_event_multihorizon_calibration_panel": _render_python_time_to_event_multihorizon_calibration_panel,
    "time_to_event_threshold_governance_panel": _render_python_time_to_event_threshold_governance_panel,
    "time_to_event_stratified_cumulative_incidence_panel": _render_python_time_to_event_stratified_cumulative_incidence_panel,
    "time_to_event_risk_group_summary": _render_python_time_to_event_risk_group_summary,
    "time_to_event_decision_curve": _render_python_time_to_event_decision_curve,
    "time_to_event_discrimination_calibration_panel": _render_python_time_to_event_discrimination_calibration_panel,
    "multicenter_generalizability_overview": _render_python_multicenter_generalizability_overview,
}


def render_r_evidence_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    _render_r_evidence_figure(
        template_id=template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )



def render_python_evidence_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    _, template_short_id = _require_namespaced_registry_id(template_id, label="template_id")
    try:
        renderer = _PYTHON_EVIDENCE_RENDERERS[template_short_id]
    except KeyError as exc:
        raise RuntimeError(f"unsupported python evidence template `{template_id}`") from exc
    renderer(
        template_id=template_short_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
