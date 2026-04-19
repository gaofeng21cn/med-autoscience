from __future__ import annotations

import math
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


def _render_python_shap_bar_importance(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    bars = list(display_payload.get("bars") or [])
    if not bars:
        raise RuntimeError("shap_bar_importance requires non-empty bars")
    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    figure_height = max(4.6, 0.55 * len(bars) + 1.6)
    fig, ax = plt.subplots(figsize=(7.4, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.98,
        )

    values = [float(item["importance_value"]) for item in bars]
    row_positions = list(range(len(bars)))
    max_value = max(values)
    x_padding = max(max_value * 0.18, 0.02)
    x_limit = max_value + x_padding
    bar_artists = ax.barh(
        row_positions,
        values,
        height=0.58,
        color=matplotlib.colors.to_rgba(model_color, alpha=0.92),
        edgecolor=comparator_color,
        linewidth=0.9,
        zorder=2,
    )
    value_label_artists: list[Any] = []
    value_label_padding = max(x_limit * 0.02, 0.015)
    for row_position, value in zip(row_positions, values, strict=True):
        value_label_artists.append(
            ax.text(
                value + value_label_padding,
                row_position,
                f"{value:.3f}",
                fontsize=max(tick_size - 0.6, 8.4),
                color="#334155",
                va="center",
                ha="left",
            )
        )

    ax.set_xlim(0.0, x_limit + value_label_padding * 3.0)
    ax.set_ylim(-0.6, len(bars) - 0.4)
    ax.set_yticks(row_positions)
    ax.set_yticklabels([str(item["feature"]) for item in bars], fontsize=max(tick_size - 0.3, 8.6))
    ax.invert_yaxis()
    ax.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color="#13293d")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=tick_size)
    ax.tick_params(axis="y", length=0, pad=8)
    _apply_publication_axes_style(ax)
    ax.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")

    fig.subplots_adjust(left=0.30, right=0.97, top=0.90 if show_figure_title else 0.95, bottom=0.14)
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
            bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        )
    )
    feature_label_ids: list[str] = []
    for index, label_artist in enumerate(ax.get_yticklabels(), start=1):
        feature_label_id = f"feature_label_{index}"
        feature_label_ids.append(feature_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=feature_label_id,
                box_type="feature_label",
            )
        )
    bar_ids: list[str] = []
    for index, artist in enumerate(bar_artists, start=1):
        bar_id = f"importance_bar_{index}"
        bar_ids.append(bar_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=bar_id,
                box_type="importance_bar",
            )
        )
    value_label_ids: list[str] = []
    for index, label_artist in enumerate(value_label_artists, start=1):
        value_label_id = f"value_label_{index}"
        value_label_ids.append(value_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=value_label_id,
                box_type="value_label",
            )
        )

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [panel_box],
            "guide_boxes": [],
            "metrics": {
                "bars": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "importance_value": float(item["importance_value"]),
                        "bar_box_id": bar_ids[index],
                        "feature_label_box_id": feature_label_ids[index],
                        "value_label_box_id": value_label_ids[index],
                    }
                    for index, item in enumerate(bars)
                ]
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_signed_importance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    bars = list(display_payload.get("bars") or [])
    if not bars:
        raise RuntimeError("shap_signed_importance_panel requires non-empty bars")
    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    zero_line_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    signed_values = [float(item["signed_importance_value"]) for item in bars]
    row_positions = list(range(len(bars)))
    max_abs_value = max(abs(value) for value in signed_values)
    x_padding = max(max_abs_value * 0.18, 0.02)
    core_limit = max_abs_value + x_padding
    label_padding = max(core_limit * 0.03, 0.018)
    axis_limit = core_limit + label_padding * 3.2

    figure_height = max(4.8, 0.58 * len(bars) + 2.0)
    fig, ax = plt.subplots(figsize=(7.8, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.98,
        )

    bar_artists: list[Any] = []
    value_label_artists: list[Any] = []
    for row_position, signed_value in zip(row_positions, signed_values, strict=True):
        color = positive_color if signed_value > 0.0 else negative_color
        bar_artists.append(
            ax.barh(
                row_position,
                signed_value,
                height=0.58,
                color=matplotlib.colors.to_rgba(color, alpha=0.92),
                edgecolor=color,
                linewidth=0.9,
                zorder=3,
            )[0]
        )
        value_label_artists.append(
            ax.text(
                signed_value + (label_padding if signed_value > 0.0 else -label_padding),
                row_position,
                f"{signed_value:+.3f}",
                fontsize=max(tick_size - 0.6, 8.4),
                color="#334155",
                va="center",
                ha="left" if signed_value > 0.0 else "right",
            )
        )

    ax.axvline(0.0, color=zero_line_color, linewidth=1.1, linestyle="--", zorder=1)
    ax.set_xlim(-axis_limit, axis_limit)
    ax.set_ylim(-0.6, len(bars) - 0.4)
    ax.set_yticks(row_positions)
    ax.set_yticklabels([str(item["feature"]) for item in bars], fontsize=max(tick_size - 0.3, 8.6))
    ax.invert_yaxis()
    ax.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=tick_size)
    ax.tick_params(axis="y", length=0, pad=8)
    _apply_publication_axes_style(ax)
    ax.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")

    negative_direction_artist = ax.text(
        0.18,
        1.03,
        str(display_payload.get("negative_label") or "").strip(),
        transform=ax.transAxes,
        fontsize=max(tick_size - 0.3, 8.8),
        color=negative_color,
        fontweight="bold",
        ha="center",
        va="bottom",
    )
    positive_direction_artist = ax.text(
        0.82,
        1.03,
        str(display_payload.get("positive_label") or "").strip(),
        transform=ax.transAxes,
        fontsize=max(tick_size - 0.3, 8.8),
        color=positive_color,
        fontweight="bold",
        ha="center",
        va="bottom",
    )

    fig.subplots_adjust(left=0.30, right=0.97, top=0.88 if show_figure_title else 0.93, bottom=0.14)
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
                bbox=negative_direction_artist.get_window_extent(renderer=renderer),
                box_id="negative_direction_label",
                box_type="negative_direction_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=positive_direction_artist.get_window_extent(renderer=renderer),
                box_id="positive_direction_label",
                box_type="positive_direction_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="x_axis_title",
            ),
        ]
    )

    feature_label_ids: list[str] = []
    for index, label_artist in enumerate(ax.get_yticklabels(), start=1):
        feature_label_id = f"feature_label_{index}"
        feature_label_ids.append(feature_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=feature_label_id,
                box_type="feature_label",
            )
        )
    bar_ids: list[str] = []
    for index, artist in enumerate(bar_artists, start=1):
        bar_id = f"importance_bar_{index}"
        bar_ids.append(bar_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=bar_id,
                box_type="importance_bar",
            )
        )
    value_label_ids: list[str] = []
    for index, label_artist in enumerate(value_label_artists, start=1):
        value_label_id = f"value_label_{index}"
        value_label_ids.append(value_label_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=value_label_id,
                box_type="value_label",
            )
        )

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )
    zero_line_half_width = max(core_limit * 0.008, 0.0025)
    zero_line_box = _data_box_to_layout_box(
        axes=ax,
        figure=fig,
        x0=-zero_line_half_width,
        y0=-0.55,
        x1=zero_line_half_width,
        y1=len(bars) - 0.45,
        box_id="zero_line",
        box_type="zero_line",
    )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [panel_box],
            "guide_boxes": [zero_line_box],
            "metrics": {
                "bars": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "direction": "positive" if float(item["signed_importance_value"]) > 0.0 else "negative",
                        "signed_importance_value": float(item["signed_importance_value"]),
                        "bar_box_id": bar_ids[index],
                        "feature_label_box_id": feature_label_ids[index],
                        "value_label_box_id": value_label_ids[index],
                    }
                    for index, item in enumerate(bars)
                ]
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_multicohort_importance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError("shap_multicohort_importance_panel requires non-empty panels")

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    max_bar_count = max(len(list(panel.get("bars") or [])) for panel in panels)
    max_value = max(float(bar["importance_value"]) for panel in panels for bar in panel["bars"])
    x_padding = max(max_value * 0.18, 0.02)
    core_limit = max_value + x_padding
    label_padding = max(core_limit * 0.03, 0.015)
    axis_limit = core_limit + label_padding * 3.0

    figure_width = max(7.8, 4.4 * len(panels) + 0.6)
    figure_height = max(4.6, 0.55 * max_bar_count + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, figure_height), sharey=False)
    axes_list = list(axes.flat) if hasattr(axes, "flat") else [axes]
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(
        left=0.12,
        right=0.98,
        top=0.84 if show_figure_title else 0.90,
        bottom=0.16,
        wspace=0.48,
    )

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.98,
        )

    panel_metrics: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []

    for axis_index, (ax, panel) in enumerate(zip(axes_list, panels, strict=True)):
        bars = list(panel["bars"])
        panel_label = str(panel["panel_label"])
        row_positions = list(range(len(bars)))
        values = [float(item["importance_value"]) for item in bars]

        bar_artists = ax.barh(
            row_positions,
            values,
            height=0.58,
            color=matplotlib.colors.to_rgba(model_color, alpha=0.92),
            edgecolor=comparator_color,
            linewidth=0.9,
            zorder=2,
        )
        value_label_artists: list[Any] = []
        for row_position, value in zip(row_positions, values, strict=True):
            value_label_artists.append(
                ax.text(
                    value + label_padding,
                    row_position,
                    f"{value:.3f}",
                    fontsize=max(tick_size - 0.6, 8.4),
                    color="#334155",
                    va="center",
                    ha="left",
                )
            )

        ax.set_xlim(0.0, axis_limit)
        ax.set_ylim(-0.6, len(bars) - 0.4)
        ax.set_yticks(row_positions)
        ax.set_yticklabels([str(item["feature"]) for item in bars], fontsize=max(tick_size - 0.3, 8.6))
        ax.invert_yaxis()
        ax.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        ax.set_ylabel("")
        ax.tick_params(axis="x", labelsize=tick_size)
        ax.tick_params(axis="y", length=0, pad=8)
        if axis_index:
            ax.tick_params(axis="y", pad=10)
        _apply_publication_axes_style(ax)
        ax.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")
        ax.set_title(str(panel["title"]), fontsize=max(tick_size + 0.2, 10.2), color="#13293d", pad=10.0)

        panel_label_artist = ax.text(
            0.01,
            0.99,
            panel_label,
            transform=ax.transAxes,
            fontsize=panel_label_size,
            fontweight="bold",
            color="#13293d",
            ha="left",
            va="top",
        )

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()

        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_label}",
                box_type="panel_label",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.title.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_label}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"x_axis_title_{panel_label}",
                box_type="subplot_x_axis_title",
            )
        )

        feature_label_ids: list[str] = []
        for row_index, label_artist in enumerate(ax.get_yticklabels(), start=1):
            feature_label_id = f"feature_label_{panel_label}_{row_index}"
            feature_label_ids.append(feature_label_id)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=feature_label_id,
                    box_type="feature_label",
                )
            )

        bar_ids: list[str] = []
        for row_index, artist in enumerate(bar_artists, start=1):
            bar_id = f"importance_bar_{panel_label}_{row_index}"
            bar_ids.append(bar_id)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=artist.get_window_extent(renderer=renderer),
                    box_id=bar_id,
                    box_type="importance_bar",
                )
            )

        value_label_ids: list[str] = []
        for row_index, label_artist in enumerate(value_label_artists, start=1):
            value_label_id = f"value_label_{panel_label}_{row_index}"
            value_label_ids.append(value_label_id)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=value_label_id,
                    box_type="value_label",
                )
            )

        panel_box_id = f"panel_{panel_label}"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.get_window_extent(renderer=renderer),
                box_id=panel_box_id,
                box_type="panel",
            )
        )
        panel_metrics.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_label,
                "title": str(panel["title"]),
                "cohort_label": str(panel["cohort_label"]),
                "panel_box_id": panel_box_id,
                "panel_label_box_id": f"panel_label_{panel_label}",
                "panel_title_box_id": f"panel_title_{panel_label}",
                "x_axis_title_box_id": f"x_axis_title_{panel_label}",
                "bars": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "importance_value": float(item["importance_value"]),
                        "bar_box_id": bar_ids[row_index],
                        "feature_label_box_id": feature_label_ids[row_index],
                        "value_label_box_id": value_label_ids[row_index],
                    }
                    for row_index, item in enumerate(bars)
                ],
            }
        )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

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
            "panel_boxes": panel_boxes,
            "guide_boxes": [],
            "metrics": {
                "panels": panel_metrics,
            },
        },
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


def _render_python_shap_grouped_local_explanation_panel(
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
    zero_line_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    max_abs_value = 0.0
    max_contribution_count = 0
    for panel in panels:
        contributions = []
        for contribution in panel["contributions"]:
            shap_value = float(contribution["shap_value"])
            max_abs_value = max(max_abs_value, abs(shap_value))
            contributions.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": shap_value,
                }
            )
        max_contribution_count = max(max_contribution_count, len(contributions))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "contributions": contributions,
            }
        )

    x_padding = max(max_abs_value * 0.20, 0.05)
    x_limit = max_abs_value + x_padding
    label_margin = max(x_limit * 0.06, 0.03)

    figure_width = max(8.8, 3.8 * len(normalized_panels) + 1.7)
    figure_height = max(4.8, 0.58 * max_contribution_count + 2.2)
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
        values = [float(item["shap_value"]) for item in contributions]
        feature_labels = [str(item["feature"]) for item in contributions]
        colors = [
            matplotlib.colors.to_rgba(positive_color if value > 0 else negative_color, alpha=0.92)
            for value in values
        ]
        edge_colors = [positive_color if value > 0 else negative_color for value in values]

        bar_artists = axes_item.barh(
            row_positions,
            values,
            height=0.58,
            color=colors,
            edgecolor=edge_colors,
            linewidth=0.9,
            zorder=3,
        )
        value_label_artists: list[Any] = []
        for row_position, value in zip(row_positions, values, strict=True):
            text_x = value + label_margin if value > 0 else value - label_margin
            text_x = min(max(text_x, -x_limit + label_margin), x_limit - label_margin)
            value_label_artists.append(
                axes_item.text(
                    text_x,
                    row_position,
                    f"{value:+.2f}",
                    fontsize=max(tick_size - 0.6, 8.3),
                    color="#334155",
                    va="center",
                    ha="left" if value > 0 else "right",
                )
            )

        axes_item.axvline(0.0, color=zero_line_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit, x_limit)
        axes_item.set_ylim(-0.7, len(contributions) - 0.35)
        axes_item.set_yticks(row_positions)
        axes_item.set_yticklabels(feature_labels, fontsize=max(tick_size - 0.4, 8.5))
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
        axes_item.tick_params(axis="y", length=0, pad=8)
        _apply_publication_axes_style(axes_item)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")

        group_label_artist = axes_item.text(
            0.5,
            0.965,
            str(panel["group_label"]),
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

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "bar_artists": list(bar_artists),
                "value_label_artists": value_label_artists,
                "group_label_artist": group_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.28, right=0.95, top=top_margin, bottom=0.18, wspace=0.32)
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
    layout_metrics_panels: list[dict[str, Any]] = []
    zero_line_half_width = max((x_limit * 2.0) * 0.004, 0.01)

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
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["group_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"group_label_{panel_token}",
                    box_type="group_label",
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
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
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
            zip(panel["contributions"], record["bar_artists"], record["value_label_artists"], strict=True),
            start=1,
        ):
            bar_box_id = f"contribution_bar_{panel_token}_{contribution_index}"
            value_label_box_id = f"value_label_{panel_token}_{contribution_index}"
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
                    box_id=value_label_box_id,
                    box_type="value_label",
                )
            )
            contribution_metrics.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": float(contribution["shap_value"]),
                    "bar_box_id": bar_box_id,
                    "feature_label_box_id": feature_label_box_ids[contribution_index - 1],
                    "value_label_box_id": value_label_box_id,
                }
            )

        zero_line_box_id = f"zero_line_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=-zero_line_half_width,
                y0=-0.7,
                x1=zero_line_half_width,
                y1=len(panel["contributions"]) - 0.35,
                box_id=zero_line_box_id,
                box_type="zero_line",
            )
        )
        layout_metrics_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "zero_line_box_id": zero_line_box_id,
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
                "panels": layout_metrics_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_grouped_decision_path_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    groups = list(display_payload.get("groups") or [])
    if len(groups) != 2:
        raise RuntimeError(f"{template_id} requires exactly two groups")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    group_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
    ]
    baseline_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    feature_order = list(display_payload.get("feature_order") or [])
    if not feature_order:
        feature_order = [str(item["feature"]) for item in groups[0]["contributions"]]
    baseline_value = float(display_payload["baseline_value"])
    all_values = [baseline_value]
    for group in groups:
        all_values.append(float(group["predicted_value"]))
        for contribution in group["contributions"]:
            all_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    y_start = -0.55
    row_positions = list(range(len(feature_order)))
    y_lower = row_positions[-1] + 0.55
    y_upper = y_start - 0.25

    fig = plt.figure(figsize=(8.6, max(4.8, 2.9 + 0.35 * len(feature_order))))
    ax = fig.add_subplot(1, 1, 1)
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

    ax.set_xlim(x_lower, x_upper)
    ax.set_ylim(y_lower, y_upper)
    ax.set_yticks(row_positions)
    ax.set_yticklabels(feature_order, fontsize=max(tick_size - 0.2, 8.6))
    ax.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_title(
        str(display_payload.get("panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    ax.tick_params(axis="y", length=0, pad=8, colors="#2F3437")
    ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    ax.grid(axis="y", visible=False)
    _apply_publication_axes_style(ax)

    ax.axvline(baseline_value, color=baseline_color, linewidth=1.1, linestyle="--", zorder=1)

    line_records: list[dict[str, Any]] = []
    legend_handles: list[Any] = []
    label_padding = max(x_span * 0.04, 0.03)
    for group, color in zip(groups, group_colors, strict=True):
        x_values = [baseline_value] + [float(item["end_value"]) for item in group["contributions"]]
        y_values = [y_start] + row_positions
        line_artist = ax.plot(
            x_values,
            y_values,
            color=color,
            linewidth=2.1,
            marker="o",
            markersize=4.8,
            markeredgecolor="white",
            markeredgewidth=0.6,
            zorder=3,
        )[0]
        prediction_x = x_values[-1]
        prediction_y = y_values[-1]
        prediction_marker_artist = ax.scatter(
            [prediction_x],
            [prediction_y],
            s=42,
            color=color,
            edgecolors="white",
            linewidths=0.7,
            zorder=4,
        )
        if prediction_x >= baseline_value:
            label_x = min(x_upper - label_padding * 0.3, prediction_x + label_padding)
            ha = "left"
        else:
            label_x = max(x_lower + label_padding * 0.3, prediction_x - label_padding)
            ha = "right"
        prediction_label_artist = ax.text(
            label_x,
            prediction_y,
            f"{float(group['predicted_value']):.2f}",
            fontsize=max(tick_size - 0.6, 8.2),
            color="#334155",
            ha=ha,
            va="center",
            zorder=4,
        )
        legend_handles.append(
            matplotlib.lines.Line2D(
                [0],
                [0],
                color=color,
                linewidth=2.1,
                marker="o",
                markersize=5.0,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=str(group["group_label"]),
            )
        )
        line_records.append(
            {
                "group": group,
                "line_artist": line_artist,
                "prediction_marker_artist": prediction_marker_artist,
                "prediction_label_artist": prediction_label_artist,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.89
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.58, top=top_margin, bottom=0.16)
    legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="center left",
        bbox_to_anchor=(0.66, 0.54),
        bbox_transform=fig.transFigure,
        frameon=True,
        framealpha=1.0,
        edgecolor="#d7dee7",
        fontsize=max(tick_size - 0.5, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.6),
    )
    legend.get_frame().set_facecolor("white")

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

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel_decision_path",
        box_type="panel",
    )
    panel_boxes = [panel_box]
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.title.get_window_extent(renderer=renderer),
                box_id="panel_title",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="legend_title",
                box_type="legend_title",
            ),
        ]
    )

    feature_label_box_ids: list[str] = []
    for index, tick_label in enumerate(ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
        feature_label_box_ids.append(box_id)

    line_half_width = max((x_upper - x_lower) * 0.004, 0.003)
    marker_half_width = max((x_upper - x_lower) * 0.007, 0.004)
    marker_half_height = 0.10
    guide_boxes: list[dict[str, Any]] = [
        _data_box_to_layout_box(
            axes=ax,
            figure=fig,
            x0=baseline_value - line_half_width,
            y0=y_start,
            x1=baseline_value + line_half_width,
            y1=row_positions[-1],
            box_id="baseline_reference_line",
            box_type="baseline_reference_line",
        )
    ]

    metrics_groups: list[dict[str, Any]] = []
    for record in line_records:
        group = record["group"]
        group_token = re.sub(r"[^A-Za-z0-9]+", "_", str(group["group_id"])) or "group"
        line_box_id = f"decision_path_line_{group_token}"
        prediction_marker_box_id = f"prediction_marker_{group_token}"
        prediction_label_box_id = f"prediction_label_{group_token}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["line_artist"].get_window_extent(renderer=renderer),
                box_id=line_box_id,
                box_type="decision_path_line",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                box_id=prediction_label_box_id,
                box_type="prediction_label",
            )
        )
        prediction_x = float(group["contributions"][-1]["end_value"])
        prediction_y = row_positions[-1]
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=ax,
                figure=fig,
                x0=prediction_x - marker_half_width,
                y0=prediction_y - marker_half_height,
                x1=prediction_x + marker_half_width,
                y1=prediction_y + marker_half_height,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        metrics_groups.append(
            {
                "group_id": str(group["group_id"]),
                "group_label": str(group["group_label"]),
                "predicted_value": float(group["predicted_value"]),
                "line_box_id": line_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "prediction_label_box_id": prediction_label_box_id,
                "contributions": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "shap_value": float(item["shap_value"]),
                        "start_value": float(item["start_value"]),
                        "end_value": float(item["end_value"]),
                    }
                    for item in group["contributions"]
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
            "guide_boxes": guide_boxes,
            "metrics": {
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": baseline_value,
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "feature_order": [str(item) for item in feature_order],
                "feature_label_box_ids": feature_label_box_ids,
                "groups": metrics_groups,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_multigroup_decision_path_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    groups = list(display_payload.get("groups") or [])
    if len(groups) != 3:
        raise RuntimeError(f"{template_id} requires exactly three groups")

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

    group_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("contrast") or palette.get("secondary") or "#2F5D8A").strip() or "#2F5D8A",
    ]
    baseline_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    feature_order = list(display_payload.get("feature_order") or [])
    if not feature_order:
        feature_order = [str(item["feature"]) for item in groups[0]["contributions"]]
    baseline_value = float(display_payload["baseline_value"])
    all_values = [baseline_value]
    for group in groups:
        all_values.append(float(group["predicted_value"]))
        for contribution in group["contributions"]:
            all_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    y_start = -0.55
    row_positions = list(range(len(feature_order)))
    y_lower = row_positions[-1] + 0.55
    y_upper = y_start - 0.25

    fig = plt.figure(figsize=(9.0, max(4.8, 2.9 + 0.35 * len(feature_order))))
    ax = fig.add_subplot(1, 1, 1)
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.82,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    ax.set_xlim(x_lower, x_upper)
    ax.set_ylim(y_lower, y_upper)
    ax.set_yticks(row_positions)
    ax.set_yticklabels(feature_order, fontsize=max(tick_size - 0.2, 8.6))
    ax.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_title(
        str(display_payload.get("panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    ax.tick_params(axis="y", length=0, pad=8, colors="#2F3437")
    ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    ax.grid(axis="y", visible=False)
    _apply_publication_axes_style(ax)

    ax.axvline(baseline_value, color=baseline_color, linewidth=1.1, linestyle="--", zorder=1)

    line_records: list[dict[str, Any]] = []
    legend_handles: list[Any] = []
    label_padding = max(x_span * 0.04, 0.03)
    for group, color in zip(groups, group_colors, strict=True):
        x_values = [baseline_value] + [float(item["end_value"]) for item in group["contributions"]]
        y_values = [y_start] + row_positions
        line_artist = ax.plot(
            x_values,
            y_values,
            color=color,
            linewidth=2.1,
            marker="o",
            markersize=4.8,
            markeredgecolor="white",
            markeredgewidth=0.6,
            zorder=3,
        )[0]
        prediction_x = x_values[-1]
        prediction_y = y_values[-1]
        prediction_marker_artist = ax.scatter(
            [prediction_x],
            [prediction_y],
            s=42,
            color=color,
            edgecolors="white",
            linewidths=0.7,
            zorder=4,
        )
        if prediction_x >= baseline_value:
            label_x = min(x_upper - label_padding * 0.3, prediction_x + label_padding)
            ha = "left"
        else:
            label_x = max(x_lower + label_padding * 0.3, prediction_x - label_padding)
            ha = "right"
        prediction_label_artist = ax.text(
            label_x,
            prediction_y,
            f"{float(group['predicted_value']):.2f}",
            fontsize=max(tick_size - 0.6, 8.2),
            color="#334155",
            ha=ha,
            va="center",
            zorder=4,
        )
        legend_handles.append(
            matplotlib.lines.Line2D(
                [0],
                [0],
                color=color,
                linewidth=2.1,
                marker="o",
                markersize=5.0,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=str(group["group_label"]),
            )
        )
        line_records.append(
            {
                "group": group,
                "line_artist": line_artist,
                "prediction_marker_artist": prediction_marker_artist,
                "prediction_label_artist": prediction_label_artist,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.89
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.56, top=top_margin, bottom=0.16)
    legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="center left",
        bbox_to_anchor=(0.64, 0.54),
        bbox_transform=fig.transFigure,
        frameon=True,
        framealpha=1.0,
        edgecolor="#d7dee7",
        fontsize=max(tick_size - 0.5, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.6),
    )
    legend.get_frame().set_facecolor("white")

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

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel_decision_path",
        box_type="panel",
    )
    panel_boxes = [panel_box]
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.title.get_window_extent(renderer=renderer),
                box_id="panel_title",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="legend_title",
                box_type="legend_title",
            ),
        ]
    )

    feature_label_box_ids: list[str] = []
    for index, tick_label in enumerate(ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
        feature_label_box_ids.append(box_id)

    line_half_width = max((x_upper - x_lower) * 0.004, 0.003)
    marker_half_width = max((x_upper - x_lower) * 0.007, 0.004)
    marker_half_height = 0.10
    guide_boxes: list[dict[str, Any]] = [
        _data_box_to_layout_box(
            axes=ax,
            figure=fig,
            x0=baseline_value - line_half_width,
            y0=y_start,
            x1=baseline_value + line_half_width,
            y1=row_positions[-1],
            box_id="baseline_reference_line",
            box_type="baseline_reference_line",
        )
    ]

    metrics_groups: list[dict[str, Any]] = []
    for record in line_records:
        group = record["group"]
        group_token = re.sub(r"[^A-Za-z0-9]+", "_", str(group["group_id"])) or "group"
        line_box_id = f"decision_path_line_{group_token}"
        prediction_marker_box_id = f"prediction_marker_{group_token}"
        prediction_label_box_id = f"prediction_label_{group_token}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["line_artist"].get_window_extent(renderer=renderer),
                box_id=line_box_id,
                box_type="decision_path_line",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                box_id=prediction_label_box_id,
                box_type="prediction_label",
            )
        )
        prediction_x = float(group["contributions"][-1]["end_value"])
        prediction_y = row_positions[-1]
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=ax,
                figure=fig,
                x0=prediction_x - marker_half_width,
                y0=prediction_y - marker_half_height,
                x1=prediction_x + marker_half_width,
                y1=prediction_y + marker_half_height,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        metrics_groups.append(
            {
                "group_id": str(group["group_id"]),
                "group_label": str(group["group_label"]),
                "predicted_value": float(group["predicted_value"]),
                "line_box_id": line_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "prediction_label_box_id": prediction_label_box_id,
                "contributions": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "shap_value": float(item["shap_value"]),
                        "start_value": float(item["start_value"]),
                        "end_value": float(item["end_value"]),
                    }
                    for item in group["contributions"]
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
            "guide_boxes": guide_boxes,
            "metrics": {
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": baseline_value,
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "feature_order": [str(item) for item in feature_order],
                "feature_label_box_ids": feature_label_box_ids,
                "groups": metrics_groups,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_partial_dependence_ice_panel(
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

    ice_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    pdp_color = _require_non_empty_string(
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

    all_y_values = [
        float(value)
        for panel in panels
        for value in (
            list(panel["pdp_curve"]["y"])
            + [point for curve in panel["ice_curves"] for point in curve["y"]]
        )
    ]
    y_min = min(all_y_values)
    y_max = max(all_y_values)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.18, 0.04)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding

    figure_width = max(8.8, 3.8 * len(panels) + 1.6)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.0), squeeze=False)
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
    for axes_item, panel in zip(axes_list, panels, strict=True):
        pdp_x = [float(value) for value in panel["pdp_curve"]["x"]]
        pdp_y = [float(value) for value in panel["pdp_curve"]["y"]]
        x_min = min(pdp_x)
        x_max = max(pdp_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        ice_line_artists: list[Any] = []
        normalized_ice_curves: list[dict[str, Any]] = []
        for curve in panel["ice_curves"]:
            curve_x = [float(value) for value in curve["x"]]
            curve_y = [float(value) for value in curve["y"]]
            line_artist = axes_item.plot(
                curve_x,
                curve_y,
                color=ice_color,
                linewidth=1.1,
                alpha=0.24,
                zorder=2,
            )[0]
            ice_line_artists.append(line_artist)
            normalized_ice_curves.append(
                {
                    "curve_id": str(curve["curve_id"]),
                    "x": curve_x,
                    "y": curve_y,
                }
            )

        pdp_line_artist = axes_item.plot(
            pdp_x,
            pdp_y,
            color=pdp_color,
            linewidth=2.4,
            zorder=3,
        )[0]
        reference_line_artist = axes_item.axvline(
            float(panel["reference_value"]),
            color=neutral_color,
            linewidth=1.1,
            linestyle="--",
            zorder=1,
        )
        reference_label_artist = axes_item.text(
            float(panel["reference_value"]),
            y_upper - y_span * 0.05,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="center",
            va="top",
            zorder=4,
        )

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

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "ice_line_artists": ice_line_artists,
                "pdp_line_artist": pdp_line_artist,
                "reference_line_artist": reference_line_artist,
                "reference_label_artist": reference_label_artist,
                "normalized_pdp": {"x": pdp_x, "y": pdp_y},
                "normalized_ice_curves": normalized_ice_curves,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.11, right=0.95, top=top_margin, bottom=0.25, wspace=0.28)

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

    legend = fig.legend(
        handles=[
            matplotlib.lines.Line2D([], [], color=ice_color, linewidth=1.4, alpha=0.30),
            matplotlib.lines.Line2D([], [], color=pdp_color, linewidth=2.4),
        ],
        labels=["ICE curves", "PDP mean"],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.05),
        ncol=2,
        frameon=False,
        fontsize=max(tick_size - 1.0, 8.2),
        handlelength=2.4,
        columnspacing=1.6,
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
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="subplot_y_axis_title",
        )
    )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend_box",
            box_type="legend_box",
        )
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        reference_line_box_id = f"reference_line_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
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
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=reference_label_box_id,
                    box_type="pdp_reference_label",
                ),
            ]
        )
        x_span = max(record["normalized_pdp"]["x"][-1] - record["normalized_pdp"]["x"][0], 1e-6)
        reference_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_value"]) - max(x_span * 0.003, 0.0015),
            y0=float(y_lower),
            x1=float(panel["reference_value"]) + max(x_span * 0.003, 0.0015),
            y1=float(y_upper),
            box_id=reference_line_box_id,
            box_type="pdp_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_pdp_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(
            record["normalized_pdp"]["x"],
            record["normalized_pdp"]["y"],
            strict=True,
        ):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_pdp_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_ice_curve_metrics: list[dict[str, Any]] = []
        for curve in record["normalized_ice_curves"]:
            normalized_points: list[dict[str, Any]] = []
            for feature_value, response_value in zip(curve["x"], curve["y"], strict=True):
                point_x, point_y = _data_point_to_figure_xy(
                    axes=axes_item,
                    figure=fig,
                    x=float(feature_value),
                    y=float(response_value),
                )
                normalized_points.append(
                    {
                        "feature_value": float(feature_value),
                        "response_value": float(response_value),
                        "x": point_x,
                        "y": point_y,
                    }
                )
            normalized_ice_curve_metrics.append({"curve_id": str(curve["curve_id"]), "points": normalized_points})

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "pdp_points": normalized_pdp_points,
                "ice_curves": normalized_ice_curve_metrics,
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
                "legend_labels": ["ICE curves", "PDP mean"],
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_partial_dependence_interaction_contour_panel(
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

    support_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    contour_line_color = _require_non_empty_string(
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
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    all_response_values = [
        float(value)
        for panel in panels
        for row in panel["response_grid"]
        for value in row
    ]
    vmin = min(all_response_values)
    vmax = max(all_response_values)
    if abs(vmax - vmin) < 1e-9:
        vmax = vmin + 1e-6

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        f"{template_id}_cmap",
        [
            str(palette.get("light") or "#eff6ff"),
            str(palette.get("secondary_soft") or "#cbd5e1"),
            str(palette.get("primary") or support_color),
        ],
    )

    figure_width = max(9.2, 4.5 * len(panels) + 1.9)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.2), squeeze=False)
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
    contour_handle = None
    for axes_item, panel in zip(axes_list, panels, strict=True):
        x_grid = [float(value) for value in panel["x_grid"]]
        y_grid = [float(value) for value in panel["y_grid"]]
        response_grid = [[float(value) for value in row] for row in panel["response_grid"]]

        contour_handle = axes_item.contourf(
            x_grid,
            y_grid,
            response_grid,
            levels=12,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            antialiased=True,
            zorder=1,
        )
        axes_item.contour(
            x_grid,
            y_grid,
            response_grid,
            levels=6,
            colors=contour_line_color,
            linewidths=0.55,
            alpha=0.7,
            zorder=2,
        )

        support_x = [float(point["x"]) for point in panel["observed_points"]]
        support_y = [float(point["y"]) for point in panel["observed_points"]]
        axes_item.scatter(
            support_x,
            support_y,
            s=18.0,
            color=matplotlib.colors.to_rgba(support_color, alpha=0.32),
            edgecolors="white",
            linewidths=0.45,
            zorder=3,
        )

        axes_item.axvline(
            float(panel["reference_x_value"]),
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=4,
        )
        axes_item.axhline(
            float(panel["reference_y_value"]),
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=4,
        )
        axes_item.scatter(
            [float(panel["reference_x_value"])],
            [float(panel["reference_y_value"])],
            s=28.0,
            color=reference_color,
            edgecolors="white",
            linewidths=0.5,
            zorder=5,
        )

        x_span = max(x_grid[-1] - x_grid[0], 1e-6)
        y_span = max(y_grid[-1] - y_grid[0], 1e-6)
        reference_label_x = min(
            max(float(panel["reference_x_value"]) + x_span * 0.03, x_grid[0] + x_span * 0.08),
            x_grid[-1] - x_span * 0.08,
        )
        reference_label_y = min(
            max(float(panel["reference_y_value"]) + y_span * 0.05, y_grid[0] + y_span * 0.10),
            y_grid[-1] - y_span * 0.08,
        )
        reference_label_artist = axes_item.text(
            reference_label_x,
            reference_label_y,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="bottom",
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": (1.0, 1.0, 1.0, 0.72),
                "edgecolor": reference_color,
                "linewidth": 0.55,
            },
            zorder=6,
        )

        axes_item.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_ylabel(
            str(panel["y_label"]),
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

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "reference_label_artist": reference_label_artist,
            }
        )

    top_margin = 0.80 if show_figure_title else 0.88
    top_margin = max(0.73, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.09, right=0.88, top=top_margin, bottom=0.18, wspace=0.28)

    colorbar = fig.colorbar(
        contour_handle,
        ax=axes_list,
        fraction=0.035,
        pad=0.04,
    )
    colorbar.set_label(
        str(display_payload.get("colorbar_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors="#2F3437")

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
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        )
    ]
    normalized_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        reference_vertical_box_id = f"reference_vertical_{panel_token}"
        reference_horizontal_box_id = f"reference_horizontal_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
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
                    bbox=axes_item.yaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"y_axis_title_{panel_token}",
                    box_type="subplot_y_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=reference_label_box_id,
                    box_type="interaction_reference_label",
                ),
            ]
        )

        x_span = max(float(panel["x_grid"][-1]) - float(panel["x_grid"][0]), 1e-6)
        y_span = max(float(panel["y_grid"][-1]) - float(panel["y_grid"][0]), 1e-6)
        vertical_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_x_value"]) - max(x_span * 0.003, 0.0015),
            y0=float(panel["y_grid"][0]),
            x1=float(panel["reference_x_value"]) + max(x_span * 0.003, 0.0015),
            y1=float(panel["y_grid"][-1]),
            box_id=reference_vertical_box_id,
            box_type="interaction_reference_vertical",
        )
        vertical_box["y0"] = max(float(panel_box["y0"]), float(vertical_box["y0"]))
        vertical_box["y1"] = min(float(panel_box["y1"]), float(vertical_box["y1"]))
        guide_boxes.append(vertical_box)

        horizontal_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["x_grid"][0]),
            y0=float(panel["reference_y_value"]) - max(y_span * 0.003, 0.0015),
            x1=float(panel["x_grid"][-1]),
            y1=float(panel["reference_y_value"]) + max(y_span * 0.003, 0.0015),
            box_id=reference_horizontal_box_id,
            box_type="interaction_reference_horizontal",
        )
        horizontal_box["x0"] = max(float(panel_box["x0"]), float(horizontal_box["x0"]))
        horizontal_box["x1"] = min(float(panel_box["x1"]), float(horizontal_box["x1"]))
        guide_boxes.append(horizontal_box)

        normalized_observed_points: list[dict[str, Any]] = []
        for point in panel["observed_points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(point["x"]),
                y=float(point["y"]),
            )
            normalized_observed_points.append(
                {
                    "point_id": str(point["point_id"]),
                    "feature_x_value": float(point["x"]),
                    "feature_y_value": float(point["y"]),
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
                "y_label": str(panel["y_label"]),
                "x_feature": str(panel["x_feature"]),
                "y_feature": str(panel["y_feature"]),
                "reference_x_value": float(panel["reference_x_value"]),
                "reference_y_value": float(panel["reference_y_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_vertical_box_id": reference_vertical_box_id,
                "reference_horizontal_box_id": reference_horizontal_box_id,
                "reference_label_box_id": reference_label_box_id,
                "x_grid": [float(value) for value in panel["x_grid"]],
                "y_grid": [float(value) for value in panel["y_grid"]],
                "response_grid": [[float(value) for value in row] for row in panel["response_grid"]],
                "observed_points": normalized_observed_points,
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


def _render_python_partial_dependence_interaction_slice_panel(
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

    slice_palette = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("secondary_soft") or "#94a3b8").strip() or "#94a3b8",
    ]
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    all_y_values = [
        float(value)
        for panel in panels
        for curve in panel["slice_curves"]
        for value in curve["y"]
    ]
    y_min = min(all_y_values)
    y_max = max(all_y_values)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.18, 0.04)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding

    figure_width = max(8.8, 3.8 * len(panels) + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.0), squeeze=False)
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

    legend_labels = [str(item) for item in list(display_payload.get("legend_labels") or [])]
    legend_handles: list[Any] = []
    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, panels, strict=True):
        raw_slice_curves: list[dict[str, Any]] = []
        first_curve_x = [float(value) for value in panel["slice_curves"][0]["x"]]
        x_min = min(first_curve_x)
        x_max = max(first_curve_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        for curve_index, curve in enumerate(panel["slice_curves"]):
            curve_x = [float(value) for value in curve["x"]]
            curve_y = [float(value) for value in curve["y"]]
            curve_color = slice_palette[curve_index % len(slice_palette)]
            axes_item.plot(
                curve_x,
                curve_y,
                color=curve_color,
                linewidth=2.2,
                alpha=0.95,
                zorder=3 + curve_index,
            )
            raw_slice_curves.append(
                {
                    "slice_id": str(curve["slice_id"]),
                    "slice_label": str(curve["slice_label"]),
                    "conditioning_value": float(curve["conditioning_value"]),
                    "x": curve_x,
                    "y": curve_y,
                    "color": curve_color,
                }
            )
            if not legend_handles:
                legend_handles.append(
                    matplotlib.lines.Line2D(
                        [], [], color=curve_color, linewidth=2.2, label=str(curve["slice_label"])
                    )
                )

        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.1,
            linestyle="--",
            zorder=2,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            y_upper - y_span * 0.05,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=5,
        )

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

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "raw_slice_curves": raw_slice_curves,
                "x_span": x_span,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.11, right=0.95, top=top_margin, bottom=0.25, wspace=0.28)

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

    legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.50, 0.045),
        ncol=min(max(len(legend_handles), 1), 3),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.7),
        handlelength=2.2,
        columnspacing=1.5,
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="legend_title",
                box_type="legend_title",
            ),
        ]
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_panels: list[dict[str, Any]] = []
    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
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
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=reference_label_box_id,
                    box_type="slice_reference_label",
                ),
            ]
        )

        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        reference_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_value"]) - reference_half_width,
            y0=float(y_lower),
            x1=float(panel["reference_value"]) + reference_half_width,
            y1=float(y_upper),
            box_id=reference_line_box_id,
            box_type="slice_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_slice_curves: list[dict[str, Any]] = []
        for curve in record["raw_slice_curves"]:
            normalized_points: list[dict[str, Any]] = []
            for feature_value, response_value in zip(curve["x"], curve["y"], strict=True):
                point_x, point_y = _data_point_to_figure_xy(
                    axes=axes_item,
                    figure=fig,
                    x=float(feature_value),
                    y=float(response_value),
                )
                normalized_points.append(
                    {
                        "feature_value": float(feature_value),
                        "response_value": float(response_value),
                        "x": point_x,
                        "y": point_y,
                    }
                )
            normalized_slice_curves.append(
                {
                    "slice_id": str(curve["slice_id"]),
                    "slice_label": str(curve["slice_label"]),
                    "conditioning_value": float(curve["conditioning_value"]),
                    "points": normalized_points,
                }
            )

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "x_feature": str(panel["x_feature"]),
                "slice_feature": str(panel["slice_feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "slice_curves": normalized_slice_curves,
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
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "legend_labels": legend_labels,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_partial_dependence_subgroup_comparison_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    subgroup_rows = list(display_payload.get("subgroup_rows") or [])
    if not panels or not subgroup_rows:
        raise RuntimeError(f"{template_id} requires non-empty panels and subgroup_rows")

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

    ice_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    pdp_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    interval_fill = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    top_y_values = [
        float(value)
        for panel in panels
        for value in (
            list(panel["pdp_curve"]["y"])
            + [point for curve in panel["ice_curves"] for point in curve["y"]]
        )
    ]
    top_y_min = min(top_y_values)
    top_y_max = max(top_y_values)
    top_y_span = max(top_y_max - top_y_min, 1e-6)
    top_y_padding = max(top_y_span * 0.18, 0.04)
    top_y_lower = top_y_min - top_y_padding
    top_y_upper = top_y_max + top_y_padding

    subgroup_values = [float(item["estimate"]) for item in subgroup_rows]
    subgroup_values.extend(float(item["lower"]) for item in subgroup_rows)
    subgroup_values.extend(float(item["upper"]) for item in subgroup_rows)
    subgroup_x_min = min(subgroup_values)
    subgroup_x_max = max(subgroup_values)
    subgroup_x_span = max(subgroup_x_max - subgroup_x_min, 1e-6)
    subgroup_x_padding = max(subgroup_x_span * 0.18, 0.04)

    figure_width = max(9.8, 3.8 * len(panels) + 2.8)
    fig = plt.figure(figsize=(figure_width, 6.2))
    grid = fig.add_gridspec(2, len(panels), height_ratios=[1.0, 0.78], hspace=0.56, wspace=0.34)
    top_axes = [fig.add_subplot(grid[0, index]) for index in range(len(panels))]
    subgroup_axes = fig.add_subplot(grid[1, :])
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

    top_panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(top_axes, panels, strict=True):
        pdp_x = [float(value) for value in panel["pdp_curve"]["x"]]
        pdp_y = [float(value) for value in panel["pdp_curve"]["y"]]
        x_min = min(pdp_x)
        x_max = max(pdp_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        raw_ice_curves: list[dict[str, Any]] = []
        for curve in panel["ice_curves"]:
            curve_x = [float(value) for value in curve["x"]]
            curve_y = [float(value) for value in curve["y"]]
            axes_item.plot(
                curve_x,
                curve_y,
                color=ice_color,
                linewidth=1.1,
                alpha=0.24,
                zorder=2,
            )
            raw_ice_curves.append(
                {
                    "curve_id": str(curve["curve_id"]),
                    "x": curve_x,
                    "y": curve_y,
                }
            )

        axes_item.plot(
            pdp_x,
            pdp_y,
            color=pdp_color,
            linewidth=2.4,
            zorder=3,
        )
        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=1,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            top_y_upper - top_y_span * 0.05,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=4,
        )

        axes_item.set_xlim(x_min - x_padding, x_max + x_padding)
        axes_item.set_ylim(top_y_lower, top_y_upper)
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

        top_panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "normalized_pdp": {"x": pdp_x, "y": pdp_y},
                "raw_ice_curves": raw_ice_curves,
                "x_span": x_span,
            }
        )

    subgroup_row_records: list[dict[str, Any]] = []
    ci_line_artists: list[Any] = []
    estimate_artists: list[Any] = []
    for row_index, row in enumerate(subgroup_rows):
        y_pos = float(row_index)
        ci_artist = subgroup_axes.plot(
            [float(row["lower"]), float(row["upper"])],
            [y_pos, y_pos],
            color=reference_color,
            linewidth=1.5,
            zorder=2,
        )[0]
        marker_artist = subgroup_axes.plot(
            float(row["estimate"]),
            y_pos,
            marker="s",
            markersize=marker_size + 0.8,
            markerfacecolor=matplotlib.colors.to_rgba(pdp_color, alpha=0.95),
            markeredgecolor=pdp_color,
            linestyle="None",
            zorder=3,
        )[0]
        ci_line_artists.append(ci_artist)
        estimate_artists.append(marker_artist)
        subgroup_row_records.append(
            {
                "row": row,
                "y_pos": y_pos,
            }
        )

    subgroup_axes.set_xlim(subgroup_x_min - subgroup_x_padding, subgroup_x_max + subgroup_x_padding)
    subgroup_axes.set_ylim(-0.7, len(subgroup_rows) - 0.3)
    subgroup_axes.invert_yaxis()
    subgroup_axes.set_yticks([])
    subgroup_axes.set_xlabel(
        str(display_payload.get("subgroup_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    subgroup_axes.set_title(
        str(display_payload.get("subgroup_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    subgroup_axes.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    subgroup_axes.grid(axis="x", color=interval_fill, linewidth=0.55, linestyle=":")
    _apply_publication_axes_style(subgroup_axes)

    top_margin = 0.79 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.12, right=0.80, top=top_margin, bottom=0.14, wspace=0.36, hspace=0.56)

    y_axis_title_artist = fig.text(
        0.040,
        0.62,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    legend = fig.legend(
        handles=[
            matplotlib.lines.Line2D([], [], color=ice_color, linewidth=1.4, alpha=0.30, label="ICE curves"),
            matplotlib.lines.Line2D([], [], color=pdp_color, linewidth=2.4, label="PDP mean"),
            matplotlib.lines.Line2D([], [], color=reference_color, linewidth=1.5, label="Subgroup interval"),
        ],
        loc="center right",
        bbox_to_anchor=(0.95, 0.72),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        handlelength=2.2,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_top_panel_label(*, axes_item: Any, label: str) -> Any:
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
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    top_panel_label_artists = [
        _add_top_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in top_panel_records
    ]

    subgroup_panel_bbox = subgroup_axes.get_window_extent(renderer=renderer)
    subgroup_panel_x0, subgroup_panel_y0 = fig.transFigure.inverted().transform(
        (subgroup_panel_bbox.x0, subgroup_panel_bbox.y0)
    )
    subgroup_panel_x1, subgroup_panel_y1 = fig.transFigure.inverted().transform(
        (subgroup_panel_bbox.x1, subgroup_panel_bbox.y1)
    )
    subgroup_panel_label_artist = fig.text(
        max(0.01, subgroup_panel_x0 - 0.018),
        subgroup_panel_y1 + 0.010,
        str(display_payload.get("subgroup_panel_label") or "").strip(),
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.6, 13.2),
        fontweight="bold",
        color="#2F3437",
        ha="left",
        va="bottom",
    )

    row_label_artists: list[Any] = []
    row_label_anchor_x = max(0.04, subgroup_panel_x0 - 0.012)
    for row_record in subgroup_row_records:
        _, label_y = _data_point_to_figure_xy(
            axes=subgroup_axes,
            figure=fig,
            x=float(subgroup_x_min - subgroup_x_padding),
            y=float(row_record["y_pos"]),
        )
        row_label_artists.append(
            fig.text(
                row_label_anchor_x,
                label_y,
                str(row_record["row"]["row_label"]),
                fontsize=max(tick_size - 0.3, 8.4),
                color="#334155",
                ha="right",
                va="center",
            )
        )

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
                bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.title.get_window_extent(renderer=renderer),
                box_id=f"subgroup_panel_title_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
                box_type="subgroup_panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"subgroup_x_axis_title_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
                box_type="subgroup_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
                box_type="panel_label",
            ),
        ]
    )
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_top_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(top_panel_records, top_panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
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
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=reference_label_box_id,
                    box_type="pdp_reference_label",
                ),
            ]
        )

        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        reference_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_value"]) - reference_half_width,
            y0=float(top_y_lower),
            x1=float(panel["reference_value"]) + reference_half_width,
            y1=float(top_y_upper),
            box_id=reference_line_box_id,
            box_type="pdp_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_pdp_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(
            record["normalized_pdp"]["x"],
            record["normalized_pdp"]["y"],
            strict=True,
        ):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_pdp_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_ice_curves: list[dict[str, Any]] = []
        for curve in record["raw_ice_curves"]:
            normalized_points: list[dict[str, Any]] = []
            for feature_value, response_value in zip(curve["x"], curve["y"], strict=True):
                point_x, point_y = _data_point_to_figure_xy(
                    axes=axes_item,
                    figure=fig,
                    x=float(feature_value),
                    y=float(response_value),
                )
                normalized_points.append(
                    {
                        "feature_value": float(feature_value),
                        "response_value": float(response_value),
                        "x": point_x,
                        "y": point_y,
                    }
                )
            normalized_ice_curves.append({"curve_id": str(curve["curve_id"]), "points": normalized_points})

        normalized_top_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "subgroup_label": str(panel["subgroup_label"]),
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "pdp_points": normalized_pdp_points,
                "ice_curves": normalized_ice_curves,
            }
        )

    subgroup_panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=subgroup_axes.get_window_extent(renderer=renderer),
        box_id=f"panel_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
        box_type="subgroup_panel",
    )
    panel_boxes.append(subgroup_panel_box)

    normalized_subgroup_rows: list[dict[str, Any]] = []
    row_band_half_height = 0.11
    marker_half_width = max((subgroup_x_max - subgroup_x_min) * 0.010, 0.006)
    for row_index, (row_record, row_label_artist, ci_artist, estimate_artist) in enumerate(
        zip(subgroup_row_records, row_label_artists, ci_line_artists, estimate_artists, strict=True),
        start=1,
    ):
        row = row_record["row"]
        label_box_id = f"subgroup_row_label_{row_index}"
        ci_box_id = f"subgroup_ci_segment_{row_index}"
        estimate_box_id = f"subgroup_estimate_marker_{row_index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=row_label_artist.get_window_extent(renderer=renderer),
                box_id=label_box_id,
                box_type="subgroup_row_label",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=subgroup_axes,
                figure=fig,
                x0=float(row["lower"]),
                y0=float(row_record["y_pos"]) - 0.012,
                x1=float(row["upper"]),
                y1=float(row_record["y_pos"]) + 0.012,
                box_id=ci_box_id,
                box_type="subgroup_ci_segment",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=subgroup_axes,
                figure=fig,
                x0=float(row["estimate"]) - marker_half_width,
                y0=float(row_record["y_pos"]) - row_band_half_height,
                x1=float(row["estimate"]) + marker_half_width,
                y1=float(row_record["y_pos"]) + row_band_half_height,
                box_id=estimate_box_id,
                box_type="subgroup_estimate_marker",
            )
        )
        normalized_subgroup_rows.append(
            {
                "row_id": str(row["row_id"]),
                "panel_id": str(row["panel_id"]),
                "row_label": str(row["row_label"]),
                "estimate": float(row["estimate"]),
                "lower": float(row["lower"]),
                "upper": float(row["upper"]),
                "support_n": int(row["support_n"]),
                "label_box_id": label_box_id,
                "ci_segment_box_id": ci_box_id,
                "estimate_marker_box_id": estimate_box_id,
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
                "legend_labels": ["ICE curves", "PDP mean", "Subgroup interval"],
                "panels": normalized_top_panels,
                "subgroup_panel": {
                    "panel_label": str(display_payload.get("subgroup_panel_label") or "").strip(),
                    "title": str(display_payload.get("subgroup_panel_title") or "").strip(),
                    "x_label": str(display_payload.get("subgroup_x_label") or "").strip(),
                    "panel_box_id": subgroup_panel_box["box_id"],
                    "rows": normalized_subgroup_rows,
                },
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_accumulated_local_effects_panel(
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

    curve_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    bin_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    bar_fill = str(palette.get("secondary_soft") or bin_color).strip() or bin_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    all_y_values = [0.0]
    for panel in panels:
        all_y_values.extend(float(value) for value in panel["ale_curve"]["y"])
        all_y_values.extend(float(item["local_effect"]) for item in panel["local_effect_bins"])
    y_min = min(all_y_values)
    y_max = max(all_y_values)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.18, 0.04)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding

    figure_width = max(8.8, 3.8 * len(panels) + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.0), squeeze=False)
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
    for axes_item, panel in zip(axes_list, panels, strict=True):
        ale_x = [float(value) for value in panel["ale_curve"]["x"]]
        ale_y = [float(value) for value in panel["ale_curve"]["y"]]
        panel_bins = list(panel["local_effect_bins"])
        x_candidates = ale_x + [float(item["bin_left"]) for item in panel_bins] + [float(item["bin_right"]) for item in panel_bins]
        x_min = min(x_candidates)
        x_max = max(x_candidates)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        raw_bin_metrics: list[dict[str, Any]] = []
        for bin_item in panel_bins:
            bin_left = float(bin_item["bin_left"])
            bin_right = float(bin_item["bin_right"])
            bin_center = float(bin_item["bin_center"])
            local_effect = float(bin_item["local_effect"])
            axes_item.bar(
                [bin_center],
                [local_effect],
                width=(bin_right - bin_left) * 0.88,
                color=matplotlib.colors.to_rgba(bar_fill, alpha=0.55),
                edgecolor=bin_color,
                linewidth=0.8,
                zorder=2,
            )
            raw_bin_metrics.append(
                {
                    "bin_id": str(bin_item["bin_id"]),
                    "bin_left": bin_left,
                    "bin_right": bin_right,
                    "bin_center": bin_center,
                    "local_effect": local_effect,
                    "support_count": int(bin_item["support_count"]),
                }
            )

        axes_item.plot(
            ale_x,
            ale_y,
            color=curve_color,
            linewidth=2.4,
            zorder=4,
        )
        axes_item.axhline(0.0, color=reference_color, linewidth=0.8, linestyle=":", zorder=1)
        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=3,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            y_upper - y_span * 0.05,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=5,
        )

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

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "ale_curve": {"x": ale_x, "y": ale_y},
                "raw_bin_metrics": raw_bin_metrics,
                "x_span": x_span,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.11, right=0.95, top=top_margin, bottom=0.25, wspace=0.28)

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

    legend = fig.legend(
        handles=[
            matplotlib.lines.Line2D([], [], color=curve_color, linewidth=2.4, label="Accumulated local effect"),
            matplotlib.patches.Patch(
                facecolor=matplotlib.colors.to_rgba(bar_fill, alpha=0.55),
                edgecolor=bin_color,
                label="Local effect per bin",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.50, 0.045),
        ncol=2,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        handlelength=2.2,
        columnspacing=1.5,
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
        ]
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_panels: list[dict[str, Any]] = []
    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
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
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=reference_label_box_id,
                    box_type="ale_reference_label",
                ),
            ]
        )

        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        reference_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_value"]) - reference_half_width,
            y0=float(y_lower),
            x1=float(panel["reference_value"]) + reference_half_width,
            y1=float(y_upper),
            box_id=reference_line_box_id,
            box_type="ale_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_ale_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(
            record["ale_curve"]["x"],
            record["ale_curve"]["y"],
            strict=True,
        ):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_ale_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_bins: list[dict[str, Any]] = []
        for bin_index, bin_metric in enumerate(record["raw_bin_metrics"], start=1):
            bin_box_id = f"ale_bin_{panel_token}_{bin_index}"
            guide_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=float(bin_metric["bin_left"]),
                    y0=min(0.0, float(bin_metric["local_effect"])),
                    x1=float(bin_metric["bin_right"]),
                    y1=max(0.0, float(bin_metric["local_effect"])),
                    box_id=bin_box_id,
                    box_type="local_effect_bin",
                )
            )
            normalized_bins.append(
                {
                    "bin_id": str(bin_metric["bin_id"]),
                    "bin_box_id": bin_box_id,
                    "bin_center": float(bin_metric["bin_center"]),
                    "local_effect": float(bin_metric["local_effect"]),
                    "support_count": int(bin_metric["support_count"]),
                }
            )

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "ale_points": normalized_ale_points,
                "local_effect_bins": normalized_bins,
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
                "legend_labels": ["Accumulated local effect", "Local effect per bin"],
                "panels": normalized_panels,
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


def _render_python_compact_effect_estimate_panel(
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
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    interval_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    grid_color = str(palette.get("secondary_soft") or "#dbe4ee").strip() or "#dbe4ee"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_value = float(display_payload["reference_value"])
    row_count = max((len(panel.get("rows") or []) for panel in panels), default=1)
    all_x_values = [reference_value]
    for panel in panels:
        for row in panel["rows"]:
            all_x_values.extend((float(row["lower"]), float(row["estimate"]), float(row["upper"])))
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.16, 0.08)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)
    estimate_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    estimate_half_height = 0.11
    ci_half_height = 0.028

    figure_width = max(8.8, 3.4 * len(panels) + 1.8)
    figure_height = max(4.8, 0.58 * row_count + 2.6)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, figure_height), squeeze=False)
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
    for axes_item, panel in zip(axes_list, panels, strict=True):
        row_label_artists: list[Any] = []
        blended_transform = matplotlib.transforms.blended_transform_factory(axes_item.transAxes, axes_item.transData)
        for row_index, row in enumerate(panel["rows"]):
            y_pos = float(row_index)
            lower = float(row["lower"])
            estimate = float(row["estimate"])
            upper = float(row["upper"])
            axes_item.plot(
                [lower, upper],
                [y_pos, y_pos],
                color=interval_color,
                linewidth=2.0,
                solid_capstyle="round",
                zorder=2,
            )
            axes_item.scatter(
                [estimate],
                [y_pos],
                s=marker_size**2,
                color=model_color,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )
            row_label_artists.append(
                axes_item.text(
                    -0.06,
                    y_pos,
                    str(row["row_label"]),
                    transform=blended_transform,
                    ha="right",
                    va="center",
                    fontsize=max(tick_size - 0.5, 8.2),
                    color="#334155",
                    clip_on=False,
                )
            )
            if row.get("support_n") is not None:
                axes_item.text(
                    0.98,
                    y_pos,
                    f"n={int(row['support_n'])}",
                    transform=blended_transform,
                    ha="right",
                    va="center",
                    fontsize=max(tick_size - 1.0, 7.8),
                    color="#64748b",
                    clip_on=False,
                )

        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=1,
        )
        axes_item.set_xlim(x_lower, x_upper)
        axes_item.set_ylim(-0.6, row_count - 0.4)
        axes_item.invert_yaxis()
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
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#334155")
        axes_item.grid(axis="x", linestyle=":", color=grid_color, linewidth=0.65, zorder=0)
        _apply_publication_axes_style(axes_item)

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "row_label_artists": row_label_artists,
            }
        )

    top_margin = 0.82 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.14, right=0.97, top=top_margin, bottom=0.24, wspace=0.42)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.015, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
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
    normalized_panels: list[dict[str, Any]] = []
    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
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
            ]
        )

        reference_line_box_id = f"reference_line_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=reference_value - reference_half_width,
                y0=-0.5,
                x1=reference_value + reference_half_width,
                y1=row_count - 0.5,
                box_id=reference_line_box_id,
                box_type="reference_line",
            )
        )

        normalized_rows: list[dict[str, Any]] = []
        for row_index, (row, row_label_artist) in enumerate(zip(panel["rows"], record["row_label_artists"], strict=True), start=1):
            y_pos = float(row_index - 1)
            label_box_id = f"row_label_{panel_token}_{row_index}"
            estimate_box_id = f"estimate_{panel_token}_{row_index}"
            ci_box_id = f"ci_{panel_token}_{row_index}"
            layout_boxes.extend(
                [
                    _bbox_to_layout_box(
                        figure=fig,
                        bbox=row_label_artist.get_window_extent(renderer=renderer),
                        box_id=label_box_id,
                        box_type="row_label",
                    ),
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=float(row["estimate"]) - estimate_half_width,
                        y0=y_pos - estimate_half_height,
                        x1=float(row["estimate"]) + estimate_half_width,
                        y1=y_pos + estimate_half_height,
                        box_id=estimate_box_id,
                        box_type="estimate_marker",
                    ),
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=float(row["lower"]),
                        y0=y_pos - ci_half_height,
                        x1=float(row["upper"]),
                        y1=y_pos + ci_half_height,
                        box_id=ci_box_id,
                        box_type="ci_segment",
                    ),
                ]
            )
            normalized_row = {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "estimate": float(row["estimate"]),
                "lower": float(row["lower"]),
                "upper": float(row["upper"]),
                "label_box_id": label_box_id,
                "estimate_box_id": estimate_box_id,
                "ci_box_id": ci_box_id,
            }
            if row.get("support_n") is not None:
                normalized_row["support_n"] = int(row["support_n"])
            normalized_rows.append(normalized_row)

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "panel_box_id": panel_box_id,
                "panel_label_box_id": f"panel_label_{panel_token}",
                "panel_title_box_id": f"panel_title_{panel_token}",
                "x_axis_title_box_id": f"x_axis_title_{panel_token}",
                "reference_line_box_id": reference_line_box_id,
                "rows": normalized_rows,
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
                "reference_value": reference_value,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_coefficient_path_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    coefficient_rows = list(display_payload.get("coefficient_rows") or [])
    steps = list(display_payload.get("steps") or [])
    summary_cards = list(display_payload.get("summary_cards") or [])
    if not coefficient_rows or not steps or not summary_cards:
        raise RuntimeError(f"{template_id} requires non-empty coefficient_rows, steps, and summary_cards")

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
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.8))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

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
    accent_colors = [
        comparator_color,
        model_color,
        str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed",
        str(palette.get("secondary_soft") or "#0f766e").strip() or "#0f766e",
        str(palette.get("primary") or "#b45309").strip() or "#b45309",
    ]
    step_color_lookup = {
        str(step["step_id"]): accent_colors[index % len(accent_colors)] for index, step in enumerate(steps)
    }

    reference_value = float(display_payload["reference_value"])
    all_x_values = [reference_value]
    for row in coefficient_rows:
        for point in list(row.get("points") or []):
            all_x_values.extend((float(point["lower"]), float(point["estimate"]), float(point["upper"])))
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.08)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    interval_half_height = 0.030
    marker_half_height = 0.095
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)
    row_count = len(coefficient_rows)
    figure_height = max(5.0, 0.82 * row_count + 2.1)
    fig, (path_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [2.7, 1.25]},
    )
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

    path_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("path_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.20,
        font_size=axis_title_size,
        font_weight="bold",
    )
    x_axis_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.36,
        font_size=axis_title_size,
        font_weight="bold",
    )
    path_axes.set_title("\n".join(path_title_lines), fontsize=axis_title_size, fontweight="bold", color="#334155", pad=12.0)
    path_axes.set_xlabel("\n".join(x_axis_title_lines), fontsize=axis_title_size, fontweight="bold", color="#13293d")
    path_axes.axvline(reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    path_axes.set_xlim(x_lower, x_upper)
    path_axes.set_ylim(-0.6, row_count - 0.4)
    path_axes.invert_yaxis()
    path_axes.set_yticks([])
    path_axes.tick_params(axis="x", labelsize=tick_size, colors="#334155")
    path_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(path_axes)

    row_label_artists: list[Any] = []
    point_records: list[dict[str, Any]] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(path_axes.transAxes, path_axes.transData)
    row_offsets = _centered_offsets(len(steps), half_span=0.22 if len(steps) <= 3 else 0.27)
    step_order_lookup = {str(step["step_id"]): index for index, step in enumerate(steps)}
    for row_index, row in enumerate(coefficient_rows):
        y_center = float(row_index)
        row_label_artists.append(
            path_axes.text(
                -0.03,
                y_center,
                str(row["row_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color="#334155",
                clip_on=False,
            )
        )
        ordered_points = sorted(
            list(row.get("points") or []),
            key=lambda item: step_order_lookup[str(item["step_id"])],
        )
        path_x = [float(point["estimate"]) for point in ordered_points]
        path_y = [y_center + row_offsets[index] for index in range(len(ordered_points))]
        path_axes.plot(
            path_x,
            path_y,
            color="#94a3b8",
            linewidth=1.0,
            alpha=0.85,
            zorder=2,
        )
        normalized_points: list[dict[str, Any]] = []
        for point_index, point in enumerate(ordered_points):
            step_id = str(point["step_id"])
            point_y = y_center + row_offsets[point_index]
            point_color = step_color_lookup[step_id]
            path_axes.plot(
                [float(point["lower"]), float(point["upper"])],
                [point_y, point_y],
                color=point_color,
                linewidth=2.1,
                solid_capstyle="round",
                zorder=3,
            )
            path_axes.scatter(
                [float(point["estimate"])],
                [point_y],
                s=marker_size**2,
                color=point_color,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )
            normalized_point = {
                "step_id": step_id,
                "estimate": float(point["estimate"]),
                "lower": float(point["lower"]),
                "upper": float(point["upper"]),
                "plot_y": float(point_y),
            }
            if point.get("support_n") is not None:
                normalized_point["support_n"] = int(point["support_n"])
            normalized_points.append(normalized_point)
        point_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "points": normalized_points,
            }
        )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0.0],
            [0.0],
            color=step_color_lookup[str(step["step_id"])],
            linewidth=2.0,
            marker="o",
            markersize=max(marker_size + 1.0, 5.5),
            markerfacecolor=step_color_lookup[str(step["step_id"])],
            markeredgecolor="white",
            label=str(step["step_label"]),
        )
        for step in steps
    ]
    legend = path_axes.legend(
        handles=legend_handles,
        title=str(display_payload.get("step_legend_title") or "").strip(),
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.14),
        ncol=min(len(steps), 3),
        columnspacing=1.2,
        handletextpad=0.6,
        borderaxespad=0.0,
        fontsize=max(tick_size - 0.4, 8.8),
        title_fontsize=max(axis_title_size - 0.6, 9.4),
    )

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    summary_axes.set_xlim(0.0, 1.0)
    summary_axes.set_ylim(0.0, 1.0)
    summary_axes.set_xticks([])
    summary_axes.set_yticks([])
    for spine in summary_axes.spines.values():
        spine.set_visible(False)
    summary_axes.set_facecolor("white")

    summary_card_artists: list[dict[str, Any]] = []
    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    top_y = 0.87
    bottom_y = 0.08
    gap = 0.035
    card_height = (top_y - bottom_y - gap * max(len(summary_cards) - 1, 0)) / float(len(summary_cards))
    for card_index, card in enumerate(summary_cards):
        card_top = top_y - card_index * (card_height + gap)
        card_bottom = card_top - card_height
        card_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, card_bottom),
            0.90,
            card_height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=summary_axes.transAxes,
            facecolor=str(palette.get("light") or "#f8fafc").strip() or "#f8fafc",
            edgecolor=str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1",
            linewidth=1.0,
            zorder=1,
        )
        summary_axes.add_patch(card_patch)

        label_lines = _wrap_flow_text_to_width(
            str(card["label"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 0.2, 8.8),
            font_weight="bold",
        )
        value_lines = _wrap_flow_text_to_width(
            str(card["value"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        detail_text = str(card.get("detail") or "").strip()
        detail_lines = _wrap_flow_text_to_width(
            detail_text,
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 1.0, 7.8),
            font_weight="normal",
        )

        label_artist = summary_axes.text(
            0.10,
            card_top - card_height * 0.18,
            "\n".join(label_lines),
            transform=summary_axes.transAxes,
            ha="left",
            va="top",
            fontsize=max(tick_size - 0.2, 8.8),
            fontweight="bold",
            color="#334155",
            zorder=2,
        )
        value_artist = summary_axes.text(
            0.10,
            card_top - card_height * 0.48,
            "\n".join(value_lines),
            transform=summary_axes.transAxes,
            ha="left",
            va="top",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        if detail_lines:
            detail_artist = summary_axes.text(
                0.10,
                card_top - card_height * 0.74,
                "\n".join(detail_lines),
                transform=summary_axes.transAxes,
                ha="left",
                va="top",
                fontsize=max(tick_size - 1.0, 7.8),
                color="#64748b",
                zorder=2,
            )
        summary_card_artists.append(
            {
                "card_id": str(card["card_id"]),
                "label": str(card["label"]),
                "value": str(card["value"]),
                "detail": detail_text,
                "label_artist": label_artist,
                "value_artist": value_artist,
                "detail_artist": detail_artist,
            }
        )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.22, right=0.97, top=top_margin, bottom=0.24, wspace=0.16)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.026, 0.009), 0.017)
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

    panel_label_a = _add_panel_label(axes_item=path_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=summary_axes, label="B")
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
                bbox=path_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=summary_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
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
                bbox=path_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    legend_title = legend.get_title()
    if legend_title.get_text().strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_title.get_window_extent(renderer=renderer),
                box_id="step_legend_title",
                box_type="legend_title",
            )
        )
    legend_texts = list(legend.get_texts())
    normalized_steps: list[dict[str, Any]] = []
    for step, legend_text in zip(steps, legend_texts, strict=True):
        legend_box_id = f"step_legend_{step['step_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_text.get_window_extent(renderer=renderer),
                box_id=legend_box_id,
                box_type="legend_label",
            )
        )
        normalized_steps.append(
            {
                "step_id": str(step["step_id"]),
                "step_label": str(step["step_label"]),
                "step_order": int(step["step_order"]),
                "legend_label_box_id": legend_box_id,
            }
        )

    normalized_rows: list[dict[str, Any]] = []
    for row_index, (row, row_label_artist, row_record) in enumerate(
        zip(coefficient_rows, row_label_artists, point_records, strict=True),
        start=1,
    ):
        label_box_id = f"coefficient_row_{row['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=row_label_artist.get_window_extent(renderer=renderer),
                box_id=label_box_id,
                box_type="coefficient_row_label",
            )
        )
        normalized_points: list[dict[str, Any]] = []
        for point in row_record["points"]:
            step_id = str(point["step_id"])
            marker_box_id = f"marker_{row['row_id']}_{step_id}"
            interval_box_id = f"interval_{row['row_id']}_{step_id}"
            layout_boxes.extend(
                [
                    _data_box_to_layout_box(
                        axes=path_axes,
                        figure=fig,
                        x0=float(point["estimate"]) - marker_half_width,
                        y0=float(point["plot_y"]) - marker_half_height,
                        x1=float(point["estimate"]) + marker_half_width,
                        y1=float(point["plot_y"]) + marker_half_height,
                        box_id=marker_box_id,
                        box_type="coefficient_marker",
                    ),
                    _data_box_to_layout_box(
                        axes=path_axes,
                        figure=fig,
                        x0=float(point["lower"]),
                        y0=float(point["plot_y"]) - interval_half_height,
                        x1=float(point["upper"]),
                        y1=float(point["plot_y"]) + interval_half_height,
                        box_id=interval_box_id,
                        box_type="coefficient_interval",
                    ),
                ]
            )
            normalized_point = {
                "step_id": step_id,
                "estimate": float(point["estimate"]),
                "lower": float(point["lower"]),
                "upper": float(point["upper"]),
                "marker_box_id": marker_box_id,
                "interval_box_id": interval_box_id,
            }
            if point.get("support_n") is not None:
                normalized_point["support_n"] = int(point["support_n"])
            normalized_points.append(normalized_point)
        normalized_rows.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "label_box_id": label_box_id,
                "points": normalized_points,
            }
        )

    normalized_summary_cards: list[dict[str, Any]] = []
    for artist_record in summary_card_artists:
        label_box_id = f"summary_label_{artist_record['card_id']}"
        value_box_id = f"summary_value_{artist_record['card_id']}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=artist_record["label_artist"].get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="summary_card_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=artist_record["value_artist"].get_window_extent(renderer=renderer),
                    box_id=value_box_id,
                    box_type="summary_card_value",
                ),
            ]
        )
        normalized_card = {
            "card_id": artist_record["card_id"],
            "label": artist_record["label"],
            "value": artist_record["value"],
            "label_box_id": label_box_id,
            "value_box_id": value_box_id,
        }
        detail_artist = artist_record["detail_artist"]
        if detail_artist is not None:
            detail_box_id = f"summary_detail_{artist_record['card_id']}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artist.get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="summary_card_detail",
                )
            )
            normalized_card["detail"] = artist_record["detail"]
            normalized_card["detail_box_id"] = detail_box_id
        normalized_summary_cards.append(normalized_card)

    reference_line_box_id = "reference_line"
    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=path_axes.get_window_extent(renderer=renderer),
            box_id="path_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=path_axes,
            figure=fig,
            x0=reference_value - reference_half_width,
            y0=-0.5,
            x1=reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id=reference_line_box_id,
            box_type="reference_line",
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
                "reference_value": reference_value,
                "path_panel": {
                    "panel_box_id": "path_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": reference_line_box_id,
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "step_legend_title_box_id": "step_legend_title",
                "steps": normalized_steps,
                "coefficient_rows": normalized_rows,
                "summary_cards": normalized_summary_cards,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_feature_response_support_domain_panel(
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

    curve_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

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
    legend_labels = [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]

    all_curve_y = [
        float(value)
        for panel in panels
        for value in list(panel["response_curve"]["y"])
    ]
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
    band_mid_y = (band_y0 + band_y1) / 2.0

    figure_width = max(9.4, 4.1 * len(panels) + 1.0)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.8), squeeze=False)
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
    for axes_item, panel in zip(axes_list, panels, strict=True):
        curve_x = [float(value) for value in panel["response_curve"]["x"]]
        curve_y = [float(value) for value in panel["response_curve"]["y"]]
        x_min = min(curve_x)
        x_max = max(curve_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.08, 0.04)

        support_label_artists: list[Any] = []
        for segment in panel["support_segments"]:
            support_style = support_style_map[str(segment["support_kind"])]
            segment_start = float(segment["domain_start"])
            segment_end = float(segment["domain_end"])
            segment_patch = matplotlib.patches.Rectangle(
                (segment_start, band_y0),
                segment_end - segment_start,
                support_band_height,
                facecolor=support_style["facecolor"],
                edgecolor=support_style["edgecolor"],
                linewidth=1.0,
                zorder=1,
            )
            axes_item.add_patch(segment_patch)
            support_label_artists.append(
                axes_item.text(
                    (segment_start + segment_end) / 2.0,
                    band_mid_y,
                    str(segment["segment_label"]),
                    fontsize=max(tick_size - 1.1, 7.6),
                    color="#334155",
                    ha="center",
                    va="center",
                    zorder=3,
                )
            )

        axes_item.plot(
            curve_x,
            curve_y,
            color=curve_color,
            linewidth=2.4,
            marker="o",
            markersize=marker_size,
            markerfacecolor="white",
            markeredgecolor=curve_color,
            markeredgewidth=1.1,
            zorder=4,
        )
        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=2,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            plot_y_upper - curve_y_padding * 0.35,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=5,
        )

        axes_item.set_xlim(x_min - x_padding, x_max + x_padding)
        axes_item.set_ylim(plot_y_lower, plot_y_upper)
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
        axes_item.tick_params(axis="both", labelsize=tick_size, colors="#334155")
        axes_item.grid(axis="y", linestyle=":", color="#e6edf2", linewidth=0.65, zorder=0)
        _apply_publication_axes_style(axes_item)

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "curve_x": curve_x,
                "curve_y": curve_y,
                "x_span": x_span,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "support_label_artists": support_label_artists,
            }
        )

    top_margin = 0.84 if show_figure_title else 0.89
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.10, right=0.97, top=top_margin, bottom=0.24, wspace=0.34)

    y_axis_title_artist = fig.text(
        0.045,
        0.58,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    legend = fig.legend(
        handles=[
            matplotlib.lines.Line2D(
                [],
                [],
                color=curve_color,
                linewidth=2.4,
                marker="o",
                markersize=5.2,
                markerfacecolor="white",
                label="Response curve",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["observed_support"]["facecolor"],
                edgecolor=support_style_map["observed_support"]["edgecolor"],
                label="Observed support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["subgroup_support"]["facecolor"],
                edgecolor=support_style_map["subgroup_support"]["edgecolor"],
                label="Subgroup support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["bin_support"]["facecolor"],
                edgecolor=support_style_map["bin_support"]["edgecolor"],
                label="Bin support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["extrapolation_warning"]["facecolor"],
                edgecolor=support_style_map["extrapolation_warning"]["edgecolor"],
                label="Extrapolation reminder",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.50, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        handlelength=2.0,
        columnspacing=1.3,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.015, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
        ]
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_panels: list[dict[str, Any]] = []
    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["reference_value"]) - reference_half_width,
                y0=plot_y_lower,
                x1=float(panel["reference_value"]) + reference_half_width,
                y1=plot_y_upper,
                box_id=reference_line_box_id,
                box_type="support_domain_reference_line",
            )
        )

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
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"reference_label_{panel_token}",
                    box_type="support_domain_reference_label",
                ),
            ]
        )

        normalized_response_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(record["curve_x"], record["curve_y"], strict=True):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_response_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_support_segments: list[dict[str, Any]] = []
        for segment_index, (segment, label_artist) in enumerate(
            zip(panel["support_segments"], record["support_label_artists"], strict=True),
            start=1,
        ):
            segment_box_id = f"support_segment_{panel_token}_{segment_index}"
            label_box_id = f"support_label_{panel_token}_{segment_index}"
            segment_box = _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(segment["domain_start"]),
                y0=band_y0,
                x1=float(segment["domain_end"]),
                y1=band_y1,
                box_id=segment_box_id,
                box_type="support_domain_segment",
            )
            guide_boxes.append(segment_box)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="support_label",
                )
            )
            normalized_support_segments.append(
                {
                    "segment_id": str(segment["segment_id"]),
                    "segment_label": str(segment["segment_label"]),
                    "support_kind": str(segment["support_kind"]),
                    "domain_start": float(segment["domain_start"]),
                    "domain_end": float(segment["domain_end"]),
                    "segment_box_id": segment_box_id,
                    "label_box_id": label_box_id,
                }
            )

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": f"reference_label_{panel_token}",
                "response_points": normalized_response_points,
                "support_segments": normalized_support_segments,
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
                "legend_labels": legend_labels,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_shap_grouped_local_support_domain_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    local_panels = list(display_payload.get("local_panels") or [])
    support_panels = list(display_payload.get("support_panels") or [])
    if not local_panels or not support_panels:
        raise RuntimeError(f"{template_id} requires non-empty local_panels and support_panels")

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

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    zero_line_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    curve_color = negative_color
    reference_color = zero_line_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

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
    legend_labels = [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]

    normalized_local_panels: list[dict[str, Any]] = []
    max_abs_value = 0.0
    max_contribution_count = 0
    for panel in local_panels:
        contributions: list[dict[str, Any]] = []
        for contribution in panel["contributions"]:
            shap_value = float(contribution["shap_value"])
            max_abs_value = max(max_abs_value, abs(shap_value))
            contributions.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": shap_value,
                }
            )
        max_contribution_count = max(max_contribution_count, len(contributions))
        normalized_local_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "contributions": contributions,
            }
        )

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

    x_padding = max(max_abs_value * 0.20, 0.05)
    x_limit = max_abs_value + x_padding
    label_margin = max(x_limit * 0.06, 0.03)

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
    band_mid_y = (band_y0 + band_y1) / 2.0

    figure_width = max(10.6, 3.5 * max(len(normalized_local_panels), len(normalized_support_panels)) + 2.6)
    local_row_height = max(3.3, 0.62 * max_contribution_count + 1.8)
    support_row_height = 3.8
    figure_height = local_row_height + support_row_height + 0.8

    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")
    root_grid = fig.add_gridspec(2, 1, height_ratios=[local_row_height, support_row_height], hspace=0.46)
    local_grid = root_grid[0].subgridspec(1, len(normalized_local_panels), wspace=0.34)
    support_grid = root_grid[1].subgridspec(1, len(normalized_support_panels), wspace=0.34)
    local_axes = [fig.add_subplot(local_grid[0, index]) for index in range(len(normalized_local_panels))]
    support_axes = [fig.add_subplot(support_grid[0, index]) for index in range(len(normalized_support_panels))]

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

    local_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(local_axes, normalized_local_panels, strict=True):
        contributions = list(panel["contributions"])
        row_positions = list(range(len(contributions)))
        values = [float(item["shap_value"]) for item in contributions]
        feature_labels = [str(item["feature"]) for item in contributions]
        colors = [
            matplotlib.colors.to_rgba(positive_color if value > 0 else negative_color, alpha=0.92)
            for value in values
        ]
        edge_colors = [positive_color if value > 0 else negative_color for value in values]

        bar_artists = axes_item.barh(
            row_positions,
            values,
            height=0.58,
            color=colors,
            edgecolor=edge_colors,
            linewidth=0.9,
            zorder=3,
        )
        value_label_artists: list[Any] = []
        for row_position, value in zip(row_positions, values, strict=True):
            text_x = value + label_margin if value > 0 else value - label_margin
            text_x = min(max(text_x, -x_limit + label_margin), x_limit - label_margin)
            value_label_artists.append(
                axes_item.text(
                    text_x,
                    row_position,
                    f"{value:+.2f}",
                    fontsize=max(tick_size - 0.6, 8.3),
                    color="#334155",
                    va="center",
                    ha="left" if value > 0 else "right",
                )
            )

        axes_item.axvline(0.0, color=zero_line_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit, x_limit)
        axes_item.set_ylim(-0.7, len(contributions) - 0.35)
        axes_item.set_yticks(row_positions)
        axes_item.set_yticklabels(feature_labels, fontsize=max(tick_size - 0.4, 8.5))
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("grouped_local_x_label") or "").strip(),
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
        axes_item.tick_params(axis="y", length=0, pad=8)
        _apply_publication_axes_style(axes_item)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")

        group_label_artist = axes_item.text(
            0.5,
            0.965,
            str(panel["group_label"]),
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

        local_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "bar_artists": list(bar_artists),
                "value_label_artists": value_label_artists,
                "group_label_artist": group_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    support_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(support_axes, normalized_support_panels, strict=True):
        curve_x = [float(value) for value in panel["response_curve"]["x"]]
        curve_y = [float(value) for value in panel["response_curve"]["y"]]
        x_min = min(curve_x)
        x_max = max(curve_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding_support = max(x_span * 0.08, 0.04)

        support_label_artists: list[Any] = []
        for segment in panel["support_segments"]:
            support_style = support_style_map[str(segment["support_kind"])]
            segment_start = float(segment["domain_start"])
            segment_end = float(segment["domain_end"])
            segment_patch = matplotlib.patches.Rectangle(
                (segment_start, band_y0),
                segment_end - segment_start,
                support_band_height,
                facecolor=support_style["facecolor"],
                edgecolor=support_style["edgecolor"],
                linewidth=1.0,
                zorder=1,
            )
            axes_item.add_patch(segment_patch)
            support_label_artists.append(
                axes_item.text(
                    (segment_start + segment_end) / 2.0,
                    band_mid_y,
                    str(segment["segment_label"]),
                    fontsize=max(tick_size - 1.1, 7.6),
                    color="#334155",
                    ha="center",
                    va="center",
                    zorder=3,
                )
            )

        axes_item.plot(
            curve_x,
            curve_y,
            color=curve_color,
            linewidth=2.4,
            marker="o",
            markersize=marker_size,
            markerfacecolor="white",
            markeredgecolor=curve_color,
            markeredgewidth=1.1,
            zorder=4,
        )
        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=2,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            plot_y_upper - curve_y_padding * 0.35,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=5,
        )

        axes_item.set_xlim(x_min - x_padding_support, x_max + x_padding_support)
        axes_item.set_ylim(plot_y_lower, plot_y_upper)
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
        axes_item.tick_params(axis="both", labelsize=tick_size, colors="#334155")
        axes_item.grid(axis="y", linestyle=":", color="#e6edf2", linewidth=0.65, zorder=0)
        _apply_publication_axes_style(axes_item)

        support_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "curve_x": curve_x,
                "curve_y": curve_y,
                "x_span": x_span,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "support_label_artists": support_label_artists,
            }
        )

    top_margin = 0.82 if show_figure_title else 0.91
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.97, top=top_margin, bottom=0.17)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    support_bboxes = [record["axes"].get_window_extent(renderer=renderer) for record in support_records]
    support_row_center_y = 0.34
    if support_bboxes:
        support_row_center_y = fig.transFigure.inverted().transform(
            (0.0, (min(item.y0 for item in support_bboxes) + max(item.y1 for item in support_bboxes)) / 2.0)
        )[1]
    support_y_axis_title_artist = fig.text(
        0.045,
        support_row_center_y,
        str(display_payload.get("support_y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    legend = fig.legend(
        handles=[
            matplotlib.lines.Line2D(
                [],
                [],
                color=curve_color,
                linewidth=2.4,
                marker="o",
                markersize=5.2,
                markerfacecolor="white",
                label="Response curve",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["observed_support"]["facecolor"],
                edgecolor=support_style_map["observed_support"]["edgecolor"],
                label="Observed support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["subgroup_support"]["facecolor"],
                edgecolor=support_style_map["subgroup_support"]["edgecolor"],
                label="Subgroup support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["bin_support"]["facecolor"],
                edgecolor=support_style_map["bin_support"]["edgecolor"],
                label="Bin support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["extrapolation_warning"]["facecolor"],
                edgecolor=support_style_map["extrapolation_warning"]["edgecolor"],
                label="Extrapolation reminder",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.58, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        handlelength=2.0,
        columnspacing=1.3,
        title=str(display_payload.get("support_legend_title") or "").strip(),
    )

    def _add_panel_label(*, axes_item: Any, label: str, left_of_panel: bool) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, _ = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y1))[1] - fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))[1])
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.018, 0.006), 0.013)
        x_anchor = panel_x0 + (x_padding * 0.55 if left_of_panel else x_padding)
        return fig.text(
            x_anchor,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.5, 13.0),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    local_panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]), left_of_panel=True)
        for record in local_records
    ]
    support_panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]), left_of_panel=False)
        for record in support_records
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="support_y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="support_legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="support_legend_title",
                box_type="legend_title",
            ),
        ]
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    layout_metrics_local_panels: list[dict[str, Any]] = []
    layout_metrics_support_panels: list[dict[str, Any]] = []
    zero_line_half_width = max((x_limit * 2.0) * 0.004, 0.01)

    for record, panel_label_artist in zip(local_records, local_panel_label_artists, strict=True):
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
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["group_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"group_label_{panel_token}",
                    box_type="group_label",
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
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
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
            zip(panel["contributions"], record["bar_artists"], record["value_label_artists"], strict=True),
            start=1,
        ):
            bar_box_id = f"contribution_bar_{panel_token}_{contribution_index}"
            value_label_box_id = f"value_label_{panel_token}_{contribution_index}"
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
                    box_id=value_label_box_id,
                    box_type="value_label",
                )
            )
            contribution_metrics.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": float(contribution["shap_value"]),
                    "bar_box_id": bar_box_id,
                    "feature_label_box_id": feature_label_box_ids[contribution_index - 1],
                    "value_label_box_id": value_label_box_id,
                }
            )

        zero_line_box_id = f"zero_line_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=-zero_line_half_width,
                y0=-0.7,
                x1=zero_line_half_width,
                y1=len(panel["contributions"]) - 0.35,
                box_id=zero_line_box_id,
                box_type="zero_line",
            )
        )
        layout_metrics_local_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "zero_line_box_id": zero_line_box_id,
                "contributions": contribution_metrics,
            }
        )

    for record, panel_label_artist in zip(support_records, support_panel_label_artists, strict=True):
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

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["reference_value"]) - reference_half_width,
                y0=plot_y_lower,
                x1=float(panel["reference_value"]) + reference_half_width,
                y1=plot_y_upper,
                box_id=reference_line_box_id,
                box_type="support_domain_reference_line",
            )
        )

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
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"reference_label_{panel_token}",
                    box_type="support_domain_reference_label",
                ),
            ]
        )

        normalized_response_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(record["curve_x"], record["curve_y"], strict=True):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_response_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_support_segments: list[dict[str, Any]] = []
        for segment_index, (segment, label_artist) in enumerate(
            zip(panel["support_segments"], record["support_label_artists"], strict=True),
            start=1,
        ):
            segment_box_id = f"support_segment_{panel_token}_{segment_index}"
            label_box_id = f"support_label_{panel_token}_{segment_index}"
            segment_box = _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(segment["domain_start"]),
                y0=band_y0,
                x1=float(segment["domain_end"]),
                y1=band_y1,
                box_id=segment_box_id,
                box_type="support_domain_segment",
            )
            guide_boxes.append(segment_box)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="support_label",
                )
            )
            normalized_support_segments.append(
                {
                    "segment_id": str(segment["segment_id"]),
                    "segment_label": str(segment["segment_label"]),
                    "support_kind": str(segment["support_kind"]),
                    "domain_start": float(segment["domain_start"]),
                    "domain_end": float(segment["domain_end"]),
                    "segment_box_id": segment_box_id,
                    "label_box_id": label_box_id,
                }
            )

        layout_metrics_support_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": f"reference_label_{panel_token}",
                "response_points": normalized_response_points,
                "support_segments": normalized_support_segments,
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
                "local_shared_feature_order": list(display_payload.get("local_shared_feature_order") or []),
                "local_panels": layout_metrics_local_panels,
                "support_panels": layout_metrics_support_panels,
                "support_legend_labels": legend_labels,
                "support_legend_title": str(display_payload.get("support_legend_title") or "").strip(),
                "support_legend_title_box_id": "support_legend_title",
                "support_y_axis_title_box_id": "support_y_axis_title",
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_broader_heterogeneity_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    effect_rows = list(display_payload.get("effect_rows") or [])
    slices = sorted(list(display_payload.get("slices") or []), key=lambda item: int(item["slice_order"]))
    if not effect_rows or not slices:
        raise RuntimeError(f"{template_id} requires non-empty effect_rows and slices")

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
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.8))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    accent_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed",
        str(palette.get("secondary_soft") or "#0f766e").strip() or "#0f766e",
        str(palette.get("primary") or "#b45309").strip() or "#b45309",
    ]
    slice_color_lookup = {
        str(slice_item["slice_id"]): accent_colors[index % len(accent_colors)] for index, slice_item in enumerate(slices)
    }

    reference_value = float(display_payload["reference_value"])
    all_x_values = [reference_value]
    for row in effect_rows:
        for estimate in list(row.get("slice_estimates") or []):
            all_x_values.extend((float(estimate["lower"]), float(estimate["estimate"]), float(estimate["upper"])))
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.08)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    interval_half_height = 0.030
    marker_half_height = 0.095
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)

    row_count = len(effect_rows)
    figure_height = max(5.0, 0.82 * row_count + 2.2)
    fig, (matrix_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [2.75, 1.35]},
    )
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

    matrix_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("matrix_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.20,
        font_size=axis_title_size,
        font_weight="bold",
    )
    x_axis_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )

    matrix_axes.set_title(
        "\n".join(matrix_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    matrix_axes.set_xlabel(
        "\n".join(x_axis_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    matrix_axes.axvline(reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    matrix_axes.set_xlim(x_lower, x_upper)
    matrix_axes.set_ylim(-0.6, row_count - 0.4)
    matrix_axes.invert_yaxis()
    matrix_axes.set_yticks([])
    matrix_axes.tick_params(axis="x", labelsize=tick_size, colors="#334155")
    matrix_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(matrix_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    summary_axes.set_xlim(0.0, 1.0)
    summary_axes.set_ylim(-0.6, row_count - 0.4)
    summary_axes.invert_yaxis()
    summary_axes.set_xticks([])
    summary_axes.set_yticks([])
    for spine in summary_axes.spines.values():
        spine.set_visible(False)
    summary_axes.set_facecolor("white")

    row_label_artists: list[Any] = []
    estimate_records: list[dict[str, Any]] = []
    verdict_records: list[dict[str, Any]] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(matrix_axes.transAxes, matrix_axes.transData)
    slice_offsets = _centered_offsets(len(slices), half_span=0.22 if len(slices) <= 3 else 0.27)
    slice_order_lookup = {str(slice_item["slice_id"]): index for index, slice_item in enumerate(slices)}

    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    row_band_height = 0.56
    for row_index, row in enumerate(effect_rows):
        y_center = float(row_index)
        row_label_artists.append(
            matrix_axes.text(
                -0.03,
                y_center,
                str(row["row_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color="#334155",
                clip_on=False,
            )
        )
        ordered_estimates = sorted(
            list(row.get("slice_estimates") or []),
            key=lambda item: slice_order_lookup[str(item["slice_id"])],
        )
        normalized_slice_estimates: list[dict[str, Any]] = []
        for estimate_index, estimate in enumerate(ordered_estimates):
            slice_id = str(estimate["slice_id"])
            plot_y = y_center + slice_offsets[estimate_index]
            slice_color = slice_color_lookup[slice_id]
            matrix_axes.plot(
                [float(estimate["lower"]), float(estimate["upper"])],
                [plot_y, plot_y],
                color=slice_color,
                linewidth=2.1,
                solid_capstyle="round",
                zorder=3,
            )
            matrix_axes.scatter(
                [float(estimate["estimate"])],
                [plot_y],
                s=marker_size**2,
                color=slice_color,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )
            normalized_estimate = {
                "slice_id": slice_id,
                "estimate": float(estimate["estimate"]),
                "lower": float(estimate["lower"]),
                "upper": float(estimate["upper"]),
                "plot_y": float(plot_y),
            }
            if estimate.get("support_n") is not None:
                normalized_estimate["support_n"] = int(estimate["support_n"])
            normalized_slice_estimates.append(normalized_estimate)
        estimate_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "verdict": str(row["verdict"]),
                "detail": str(row.get("detail") or "").strip(),
                "slice_estimates": normalized_slice_estimates,
            }
        )

        band_bottom = y_center - row_band_height / 2.0
        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, band_bottom),
            0.90,
            row_band_height,
            boxstyle="round,pad=0.010,rounding_size=0.015",
            transform=summary_axes.transData,
            facecolor=str(palette.get("light") or "#f8fafc").strip() or "#f8fafc",
            edgecolor=str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1",
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_lines = _wrap_flow_text_to_width(
            str(row["verdict"]).replace("_", " "),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        detail_text = str(row.get("detail") or "").strip()
        detail_lines = _wrap_flow_text_to_width(
            detail_text,
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 1.0, 7.8),
            font_weight="normal",
        )
        verdict_artist = summary_axes.text(
            0.10,
            y_center - 0.11,
            "\n".join(verdict_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        if detail_lines:
            detail_artist = summary_axes.text(
                0.10,
                y_center + 0.10,
                "\n".join(detail_lines),
                transform=summary_axes.transData,
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.0, 7.8),
                color="#64748b",
                zorder=2,
            )
        verdict_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "verdict": str(row["verdict"]),
                "detail": detail_text,
                "verdict_artist": verdict_artist,
                "detail_artist": detail_artist,
            }
        )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0.0],
            [0.0],
            color=slice_color_lookup[str(slice_item["slice_id"])],
            linewidth=2.0,
            marker="o",
            markersize=max(marker_size + 1.0, 5.5),
            markerfacecolor=slice_color_lookup[str(slice_item["slice_id"])],
            markeredgecolor="white",
            label=str(slice_item["slice_label"]),
        )
        for slice_item in slices
    ]
    legend = matrix_axes.legend(
        handles=legend_handles,
        title=str(display_payload.get("slice_legend_title") or "").strip(),
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.14),
        ncol=min(len(slices), 3),
        columnspacing=1.2,
        handletextpad=0.6,
        borderaxespad=0.0,
        fontsize=max(tick_size - 0.4, 8.8),
        title_fontsize=max(axis_title_size - 0.6, 9.4),
    )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.22, right=0.97, top=top_margin, bottom=0.24, wspace=0.16)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.026, 0.009), 0.017)
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

    panel_label_a = _add_panel_label(axes_item=matrix_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=summary_axes, label="B")
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
                bbox=matrix_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=summary_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
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
                bbox=matrix_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    legend_title = legend.get_title()
    if legend_title.get_text().strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_title.get_window_extent(renderer=renderer),
                box_id="slice_legend_title",
                box_type="legend_title",
            )
        )
    legend_texts = list(legend.get_texts())
    normalized_slices: list[dict[str, Any]] = []
    for slice_item, legend_text in zip(slices, legend_texts, strict=True):
        legend_box_id = f"slice_legend_{slice_item['slice_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_text.get_window_extent(renderer=renderer),
                box_id=legend_box_id,
                box_type="legend_label",
            )
        )
        normalized_slices.append(
            {
                "slice_id": str(slice_item["slice_id"]),
                "slice_label": str(slice_item["slice_label"]),
                "slice_kind": str(slice_item["slice_kind"]),
                "slice_order": int(slice_item["slice_order"]),
                "legend_label_box_id": legend_box_id,
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="matrix_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=matrix_axes,
            figure=fig,
            x0=reference_value - reference_half_width,
            y0=-0.5,
            x1=reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_effect_rows: list[dict[str, Any]] = []
    for row_record, row_label_artist, verdict_record in zip(
        estimate_records,
        row_label_artists,
        verdict_records,
        strict=True,
    ):
        row_label_box_id = f"row_label_{row_record['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=row_label_artist.get_window_extent(renderer=renderer),
                box_id=row_label_box_id,
                box_type="row_label",
            )
        )
        verdict_box_id = f"verdict_{row_record['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=verdict_record["verdict_artist"].get_window_extent(renderer=renderer),
                box_id=verdict_box_id,
                box_type="verdict_value",
            )
        )
        detail_box_id = ""
        if verdict_record["detail_artist"] is not None:
            detail_box_id = f"detail_{row_record['row_id']}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_record["detail_artist"].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                )
            )

        normalized_slice_estimates: list[dict[str, Any]] = []
        for estimate in row_record["slice_estimates"]:
            slice_id = str(estimate["slice_id"])
            marker_box_id = f"estimate_{row_record['row_id']}_{slice_id}"
            interval_box_id = f"ci_{row_record['row_id']}_{slice_id}"
            layout_boxes.extend(
                [
                    _data_box_to_layout_box(
                        axes=matrix_axes,
                        figure=fig,
                        x0=float(estimate["estimate"]) - marker_half_width,
                        y0=float(estimate["plot_y"]) - marker_half_height,
                        x1=float(estimate["estimate"]) + marker_half_width,
                        y1=float(estimate["plot_y"]) + marker_half_height,
                        box_id=marker_box_id,
                        box_type="estimate_marker",
                    ),
                    _data_box_to_layout_box(
                        axes=matrix_axes,
                        figure=fig,
                        x0=float(estimate["lower"]),
                        y0=float(estimate["plot_y"]) - interval_half_height,
                        x1=float(estimate["upper"]),
                        y1=float(estimate["plot_y"]) + interval_half_height,
                        box_id=interval_box_id,
                        box_type="ci_segment",
                    ),
                ]
            )
            normalized_estimate = {
                "slice_id": slice_id,
                "estimate": float(estimate["estimate"]),
                "lower": float(estimate["lower"]),
                "upper": float(estimate["upper"]),
                "marker_box_id": marker_box_id,
                "interval_box_id": interval_box_id,
            }
            if estimate.get("support_n") is not None:
                normalized_estimate["support_n"] = int(estimate["support_n"])
            normalized_slice_estimates.append(normalized_estimate)

        normalized_row = {
            "row_id": str(row_record["row_id"]),
            "row_label": str(row_record["row_label"]),
            "verdict": str(row_record["verdict"]),
            "label_box_id": row_label_box_id,
            "verdict_box_id": verdict_box_id,
            "slice_estimates": normalized_slice_estimates,
        }
        detail_text = str(row_record.get("detail") or "").strip()
        if detail_text:
            normalized_row["detail"] = detail_text
        if detail_box_id:
            normalized_row["detail_box_id"] = detail_box_id
        normalized_effect_rows.append(normalized_row)

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "reference_value": reference_value,
                "matrix_panel": {
                    "panel_box_id": "matrix_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "slice_legend_title_box_id": "slice_legend_title",
                "slices": normalized_slices,
                "effect_rows": normalized_effect_rows,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_center_transportability_governance_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    centers = list(display_payload.get("centers") or [])
    if not centers:
        raise RuntimeError(f"{template_id} requires non-empty centers")

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
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    derivation_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    validation_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    light_fill = str(palette.get("light") or "#f8fafc").strip() or "#f8fafc"
    summary_fill = str(palette.get("secondary_soft") or "#e2e8f0").strip() or "#e2e8f0"
    audit_color = str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed"
    primary_fill = str(palette.get("primary_soft") or "#eff6ff").strip() or "#eff6ff"
    neutral_text = "#334155"

    verdict_color_lookup = {
        "stable": derivation_color,
        "context_dependent": audit_color,
        "recalibration_required": audit_color,
        "insufficient_support": reference_color,
        "unstable": "#7f1d1d",
    }

    def _center_color(center_payload: dict[str, Any]) -> str:
        cohort_role = str(center_payload.get("cohort_role") or "").strip().casefold()
        if "derivation" in cohort_role or "train" in cohort_role:
            return derivation_color
        if "validation" in cohort_role:
            return validation_color
        return audit_color

    metric_values = [float(display_payload["metric_reference_value"])]
    for center in centers:
        metric_values.extend(
            (
                float(center["metric_lower"]),
                float(center["metric_estimate"]),
                float(center["metric_upper"]),
            )
        )
    x_min = min(metric_values)
    x_max = max(metric_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.03)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.010)
    marker_half_height = 0.085
    interval_half_height = 0.028
    reference_half_width = max((x_upper - x_lower) * 0.004, 0.0015)

    row_count = len(centers)
    figure_height = max(5.4, 1.02 * row_count + 2.5)
    fig, (metric_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(11.2, figure_height),
        gridspec_kw={"width_ratios": [2.15, 1.25]},
    )
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

    metric_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("metric_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.23,
        font_size=axis_title_size,
        font_weight="bold",
    )
    metric_x_label_lines = _wrap_flow_text_to_width(
        str(display_payload.get("metric_x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.32,
        font_size=axis_title_size,
        font_weight="bold",
    )

    metric_axes.set_title(
        "\n".join(metric_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    metric_axes.set_xlabel(
        "\n".join(metric_x_label_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    metric_reference_value = float(display_payload["metric_reference_value"])
    metric_axes.axvline(metric_reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    metric_axes.set_xlim(x_lower, x_upper)
    metric_axes.set_ylim(-0.6, row_count - 0.4)
    metric_axes.invert_yaxis()
    metric_axes.set_yticks([])
    metric_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_text)
    metric_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(metric_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    summary_axes.set_xlim(0.0, 1.0)
    summary_axes.set_ylim(-0.6, row_count - 0.4)
    summary_axes.invert_yaxis()
    summary_axes.set_xticks([])
    summary_axes.set_yticks([])
    for spine in summary_axes.spines.values():
        spine.set_visible(False)
    summary_axes.set_facecolor("white")

    row_label_artists: list[Any] = []
    center_metrics_for_sidecar: list[dict[str, Any]] = []
    verdict_artists: list[Any] = []
    metrics_text_artists: list[Any] = []
    action_artists: list[Any] = []
    detail_artists: list[Any | None] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(metric_axes.transAxes, metric_axes.transData)
    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18

    for row_index, center in enumerate(centers):
        y_center = float(row_index)
        row_label_artists.append(
            metric_axes.text(
                -0.03,
                y_center,
                str(center["center_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color=neutral_text,
                clip_on=False,
            )
        )
        interval_color = _center_color(center)
        metric_axes.plot(
            [float(center["metric_lower"]), float(center["metric_upper"])],
            [y_center, y_center],
            color=interval_color,
            linewidth=2.2,
            solid_capstyle="round",
            zorder=3,
        )
        metric_axes.scatter(
            [float(center["metric_estimate"])],
            [y_center],
            s=marker_size**2,
            color=interval_color,
            edgecolors="white",
            linewidths=0.8,
            zorder=4,
        )

        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, y_center - 0.36),
            0.90,
            0.72,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            transform=summary_axes.transData,
            facecolor=primary_fill if row_index % 2 == 0 else light_fill,
            edgecolor=summary_fill,
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_lines = _wrap_flow_text_to_width(
            str(center["verdict"]).replace("_", " "),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        verdict_artist = summary_axes.text(
            0.08,
            y_center - 0.18,
            "\n".join(verdict_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color=verdict_color_lookup.get(str(center["verdict"]), neutral_text),
            zorder=2,
        )
        metrics_line = (
            f"n={int(center['support_count'])} | events={int(center['event_count'])} | "
            f"shift={float(center['max_shift']):.2f}\n"
            f"slope={float(center['slope']):.2f} | O:E={float(center['oe_ratio']):.2f}"
        )
        metrics_artist = summary_axes.text(
            0.08,
            y_center + 0.00,
            metrics_line,
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.0, 7.9),
            color=neutral_text,
            zorder=2,
        )
        action_lines = _wrap_flow_text_to_width(
            str(center["action"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 0.8, 8.1),
            font_weight="bold",
        )
        action_artist = summary_axes.text(
            0.08,
            y_center + 0.18,
            "\n".join(action_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 0.8, 8.1),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        detail_text = str(center.get("detail") or "").strip()
        if detail_text:
            detail_lines = _wrap_flow_text_to_width(
                detail_text,
                max_width_pt=summary_text_width_pt,
                font_size=max(tick_size - 1.2, 7.6),
                font_weight="normal",
            )
            detail_artist = summary_axes.text(
                0.08,
                y_center + 0.33,
                "\n".join(detail_lines),
                transform=summary_axes.transData,
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.2, 7.6),
                color="#64748b",
                zorder=2,
            )

        verdict_artists.append(verdict_artist)
        metrics_text_artists.append(metrics_artist)
        action_artists.append(action_artist)
        detail_artists.append(detail_artist)
        normalized_center = {
            "center_id": str(center["center_id"]),
            "center_label": str(center["center_label"]),
            "cohort_role": str(center["cohort_role"]),
            "support_count": int(center["support_count"]),
            "event_count": int(center["event_count"]),
            "metric_estimate": float(center["metric_estimate"]),
            "metric_lower": float(center["metric_lower"]),
            "metric_upper": float(center["metric_upper"]),
            "max_shift": float(center["max_shift"]),
            "slope": float(center["slope"]),
            "oe_ratio": float(center["oe_ratio"]),
            "verdict": str(center["verdict"]),
            "action": str(center["action"]),
        }
        if detail_text:
            normalized_center["detail"] = detail_text
        center_metrics_for_sidecar.append(normalized_center)

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.23, right=0.97, top=top_margin, bottom=0.18, wspace=0.18)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.026, 0.009), 0.017)
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

    panel_label_a = _add_panel_label(axes_item=metric_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=summary_axes, label="B")
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
                bbox=metric_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=summary_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
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
                bbox=metric_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=metric_axes.get_window_extent(renderer=renderer),
            box_id="metric_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=metric_axes,
            figure=fig,
            x0=metric_reference_value - reference_half_width,
            y0=-0.5,
            x1=metric_reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_centers: list[dict[str, Any]] = []
    for row_index, center in enumerate(center_metrics_for_sidecar):
        center_id = str(center["center_id"])
        y_center = float(row_index)
        row_label_box_id = f"row_label_{center_id}"
        metric_box_id = f"metric_{center_id}"
        interval_box_id = f"ci_{center_id}"
        verdict_box_id = f"verdict_{center_id}"
        metrics_box_id = f"metrics_{center_id}"
        action_box_id = f"action_{center_id}"
        detail_box_id = ""

        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=row_label_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=row_label_box_id,
                    box_type="row_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=verdict_box_id,
                    box_type="verdict_value",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=metrics_text_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=metrics_box_id,
                    box_type="row_metric",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=action_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=action_box_id,
                    box_type="row_action",
                ),
                _data_box_to_layout_box(
                    axes=metric_axes,
                    figure=fig,
                    x0=float(center["metric_estimate"]) - marker_half_width,
                    y0=y_center - marker_half_height,
                    x1=float(center["metric_estimate"]) + marker_half_width,
                    y1=y_center + marker_half_height,
                    box_id=metric_box_id,
                    box_type="estimate_marker",
                ),
                _data_box_to_layout_box(
                    axes=metric_axes,
                    figure=fig,
                    x0=float(center["metric_lower"]),
                    y0=y_center - interval_half_height,
                    x1=float(center["metric_upper"]),
                    y1=y_center + interval_half_height,
                    box_id=interval_box_id,
                    box_type="ci_segment",
                ),
            ]
        )
        if detail_artists[row_index] is not None:
            detail_box_id = f"detail_{center_id}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                )
            )

        normalized_center = dict(center)
        normalized_center.update(
            {
                "label_box_id": row_label_box_id,
                "metric_box_id": metric_box_id,
                "interval_box_id": interval_box_id,
                "verdict_box_id": verdict_box_id,
                "metrics_box_id": metrics_box_id,
                "action_box_id": action_box_id,
            }
        )
        if detail_box_id:
            normalized_center["detail_box_id"] = detail_box_id
        normalized_centers.append(normalized_center)

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_family": str(display_payload.get("metric_family") or "").strip(),
                "metric_reference_value": metric_reference_value,
                "metric_panel": {
                    "panel_box_id": "metric_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "batch_shift_threshold": float(display_payload["batch_shift_threshold"]),
                "slope_acceptance_lower": float(display_payload["slope_acceptance_lower"]),
                "slope_acceptance_upper": float(display_payload["slope_acceptance_upper"]),
                "oe_ratio_acceptance_lower": float(display_payload["oe_ratio_acceptance_lower"]),
                "oe_ratio_acceptance_upper": float(display_payload["oe_ratio_acceptance_upper"]),
                "centers": normalized_centers,
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


def _render_python_pathway_enrichment_dotplot_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panel_order = list(display_payload.get("panel_order") or [])
    pathway_order = list(display_payload.get("pathway_order") or [])
    points = list(display_payload.get("points") or [])
    if not panel_order or not pathway_order or not points:
        raise RuntimeError(f"{template_id} requires non-empty panel_order, pathway_order, and points")

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
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    pathway_labels = [str(item["label"]) for item in pathway_order]
    panel_id_order = [str(item["panel_id"]) for item in panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in panel_order}
    point_lookup = {(str(item["panel_id"]), str(item["pathway_label"])): item for item in points}

    all_x_values = [float(item["x_value"]) for item in points]
    all_effect_values = [float(item["effect_value"]) for item in points]
    all_size_values = [float(item["size_value"]) for item in points]
    global_x_min = min(all_x_values)
    global_x_max = max(all_x_values)
    global_x_span = max(global_x_max - global_x_min, 1e-6)
    x_padding = max(global_x_span * 0.08, 0.12)
    size_min = min(all_size_values)
    size_max = max(all_size_values)
    max_abs_effect = max(abs(value) for value in all_effect_values)
    max_abs_effect = max(max_abs_effect, 1e-6)

    if any(value < 0.0 for value in all_effect_values) and any(value > 0.0 for value in all_effect_values):
        color_norm: matplotlib.colors.Normalize = matplotlib.colors.TwoSlopeNorm(
            vmin=-max_abs_effect,
            vcenter=0.0,
            vmax=max_abs_effect,
        )
    else:
        min_effect = min(all_effect_values)
        max_effect = max(all_effect_values)
        if math.isclose(min_effect, max_effect, rel_tol=1e-9, abs_tol=1e-9):
            min_effect -= 1.0
            max_effect += 1.0
        color_norm = matplotlib.colors.Normalize(vmin=min_effect, vmax=max_effect)
    effect_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "pathway_enrichment_dotplot",
        [negative_color, "#f8fafc", positive_color],
    )

    def _marker_size(size_value: float) -> float:
        if math.isclose(size_min, size_max, rel_tol=1e-9, abs_tol=1e-9):
            return 220.0
        normalized = (size_value - size_min) / (size_max - size_min)
        return 120.0 + normalized * 260.0

    figure_width = max(8.8, 4.2 * len(panel_id_order) + 1.8)
    fig, axes = plt.subplots(1, len(panel_id_order), figsize=(figure_width, 5.8), squeeze=False)
    axes_list = list(axes[0])
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
            color=neutral_color,
            y=0.985,
        )

    scatter_artist = None
    panel_records: list[dict[str, Any]] = []
    y_positions = list(range(len(pathway_labels)))
    pathway_position_lookup = {label: index for index, label in enumerate(pathway_labels)}
    for axes_item, panel_id in zip(axes_list, panel_id_order, strict=True):
        panel_points = [point_lookup[(panel_id, pathway_label)] for pathway_label in pathway_labels]
        scatter_x = [float(item["x_value"]) for item in panel_points]
        scatter_y = [pathway_position_lookup[str(item["pathway_label"])] for item in panel_points]
        scatter_sizes = [_marker_size(float(item["size_value"])) for item in panel_points]
        scatter_colors = [float(item["effect_value"]) for item in panel_points]
        scatter_artist = axes_item.scatter(
            scatter_x,
            scatter_y,
            s=scatter_sizes,
            c=scatter_colors,
            cmap=effect_cmap,
            norm=color_norm,
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        if global_x_min < 0.0 < global_x_max:
            axes_item.axvline(0.0, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(global_x_min - x_padding, global_x_max + x_padding)
        axes_item.set_ylim(-0.5, len(pathway_labels) - 0.5)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(pathway_labels, fontsize=tick_size, color=neutral_color)
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_title(
            panel_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", length=0, colors=neutral_color)
        axes_item.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)
        panel_records.append({"panel_id": panel_id, "axes": axes_item, "points": panel_points})

    top_margin = 0.84 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.20, right=0.86, top=top_margin, bottom=0.22, wspace=0.24)

    y_axis_title_artist = fig.text(
        0.07,
        0.52,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        ha="center",
        va="center",
    )

    legend_value_candidates = sorted({round(size_min, 2), round((size_min + size_max) / 2.0, 2), round(size_max, 2)})
    legend_handles = [
        plt.scatter([], [], s=_marker_size(float(value)), color="#94a3b8", edgecolors="white", linewidths=0.8)
        for value in legend_value_candidates
    ]
    legend = fig.legend(
        legend_handles,
        [f"{value:g}" for value in legend_value_candidates],
        title=str(display_payload.get("size_scale_label") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.50, 0.02),
        ncol=len(legend_handles),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.4),
        title_fontsize=max(tick_size - 0.4, 8.8),
        columnspacing=1.4,
    )
    if scatter_artist is None:
        raise RuntimeError(f"{template_id} failed to render scatter artist")
    colorbar = fig.colorbar(scatter_artist, ax=axes_list, fraction=0.040, pad=0.03)
    colorbar.set_label(
        str(display_payload.get("effect_scale_label") or "").strip(),
        fontsize=max(axis_title_size - 0.4, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.015, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=chr(ord("A") + index))
        for index, record in enumerate(panel_records)
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
    normalized_panels: list[dict[str, Any]] = []
    for index, (record, panel_label_artist) in enumerate(zip(panel_records, panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_box_id = f"panel_{chr(ord('A') + index - 1)}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"panel_title_{chr(ord('A') + index - 1)}"
        x_axis_title_box_id = f"x_axis_title_{chr(ord('A') + index - 1)}"
        panel_label_box_id = f"panel_label_{chr(ord('A') + index - 1)}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
                    box_id=panel_title_box_id,
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=x_axis_title_box_id,
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=panel_label_box_id,
                    box_type="panel_label",
                ),
            ]
        )
        normalized_points: list[dict[str, Any]] = []
        for point in record["points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(point["x_value"]),
                y=float(pathway_position_lookup[str(point["pathway_label"])]),
            )
            normalized_points.append(
                {
                    "pathway_label": str(point["pathway_label"]),
                    "x": point_x,
                    "y": point_y,
                    "x_value": float(point["x_value"]),
                    "effect_value": float(point["effect_value"]),
                    "size_value": float(point["size_value"]),
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": panel_title_lookup[str(record["panel_id"])],
                "panel_label": chr(ord("A") + index - 1),
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
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
                "effect_scale_label": str(display_payload.get("effect_scale_label") or "").strip(),
                "size_scale_label": str(display_payload.get("size_scale_label") or "").strip(),
                "pathway_labels": pathway_labels,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_oncoplot_mutation_landscape_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    mutation_records = list(display_payload.get("mutation_records") or [])
    if not gene_order or not sample_order or not annotation_tracks or not mutation_records:
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, and mutation_records"
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
    contrast_color = str(palette.get("contrast") or "#8b3a3a").strip() or "#8b3a3a"
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#f7ebeb").strip() or "#f7ebeb"

    gene_labels = [str(item["label"]) for item in gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}

    mutation_lookup = {
        (str(item["sample_id"]), str(item["gene_label"])): str(item["alteration_class"])
        for item in mutation_records
    }
    burden_counts = {
        sample_id: sum(1 for gene_label in gene_labels if (sample_id, gene_label) in mutation_lookup)
        for sample_id in sample_ids
    }
    gene_altered_counts = {
        gene_label: sum(1 for sample_id in sample_ids if (sample_id, gene_label) in mutation_lookup)
        for gene_label in gene_labels
    }
    gene_altered_fractions = {
        gene_label: gene_altered_counts[gene_label] / float(len(sample_ids))
        for gene_label in gene_labels
    }

    alteration_color_map = {
        "missense": primary_color,
        "truncating": contrast_color,
        "amplification": secondary_color,
        "fusion": neutral_color,
    }
    alteration_label_map = {
        "missense": "Missense",
        "truncating": "Truncating",
        "amplification": "Amplification",
        "fusion": "Fusion",
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

    figure_width = max(8.4, 0.52 * len(sample_ids) + 4.4)
    figure_height = max(5.6, 0.60 * len(gene_labels) + 0.42 * len(annotation_tracks) + 2.8)
    fig = plt.figure(figsize=(figure_width, figure_height))
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
            color=neutral_color,
            y=0.985,
        )

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.20,
        right=0.92,
        bottom=0.22,
        top=top_margin,
        width_ratios=(max(3.8, 0.60 * len(sample_ids) + 0.8), 1.55),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.70 * len(gene_labels))),
        hspace=0.10,
        wspace=0.14,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(sample_ids, rotation=45, ha="right", fontsize=max(tick_size - 0.3, 8.6), color=neutral_color)
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    matrix_background_color = "#ffffff"
    altered_cell_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=matrix_background_color,
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            alteration_class = mutation_lookup.get((sample_id, gene_label))
            if not alteration_class:
                continue
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=alteration_color_map[alteration_class],
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            altered_cell_patches.append(
                {
                    "box_id": f"mutation_{gene_label}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "alteration_class": alteration_class,
                }
            )

    legend_handles = [
        matplotlib.patches.Patch(facecolor=alteration_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "amplification", "fusion")
    ]
    legend = fig.legend(
        handles=legend_handles,
        labels=[handle.get_label() for handle in legend_handles],
        title=str(display_payload.get("mutation_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.53, 0.02),
        ncol=min(4, len(legend_handles)),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.3, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, burden_y0 = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    burden_x1, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, annotation_y0 = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

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
    y_axis_title_box = _bbox_to_layout_box(
        figure=fig,
        bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
        box_id="y_axis_title",
        box_type="subplot_y_axis_title",
    )
    layout_boxes.extend(
        [
            y_axis_title_box,
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    altered_cells_metrics: list[dict[str, Any]] = []
    for item in altered_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="mutation_cell",
            )
        )
        altered_cells_metrics.append(
            {
                "sample_id": str(item["sample_id"]),
                "gene_label": str(item["gene_label"]),
                "alteration_class": str(item["alteration_class"]),
                "box_id": str(item["box_id"]),
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

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
                "mutation_legend_title": str(display_payload.get("mutation_legend_title") or "").strip(),
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_altered_frequencies": gene_frequency_metrics,
                "altered_cells": altered_cells_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_cnv_recurrence_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    region_order = list(display_payload.get("region_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    cnv_records = list(display_payload.get("cnv_records") or [])
    if not region_order or not sample_order or not annotation_tracks or not cnv_records:
        raise RuntimeError(
            f"{template_id} requires non-empty region_order, sample_order, annotation_tracks, and cnv_records"
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
    contrast_color = str(palette.get("contrast") or "#d97706").strip() or "#d97706"
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#fef3c7").strip() or "#fef3c7"

    region_labels = [str(item["label"]) for item in region_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    region_index = {region_label: index for index, region_label in enumerate(region_labels)}

    cnv_lookup = {
        (str(item["sample_id"]), str(item["region_label"])): str(item["cnv_state"])
        for item in cnv_records
    }
    sample_burdens = {
        sample_id: sum(1 for region_label in region_labels if (sample_id, region_label) in cnv_lookup)
        for sample_id in sample_ids
    }
    gain_like_states = {"amplification", "gain"}
    loss_like_states = {"loss", "deep_loss"}
    region_gain_counts = {
        region_label: sum(
            1 for sample_id in sample_ids if cnv_lookup.get((sample_id, region_label)) in gain_like_states
        )
        for region_label in region_labels
    }
    region_loss_counts = {
        region_label: sum(
            1 for sample_id in sample_ids if cnv_lookup.get((sample_id, region_label)) in loss_like_states
        )
        for region_label in region_labels
    }
    region_gain_fractions = {
        region_label: region_gain_counts[region_label] / float(len(sample_ids))
        for region_label in region_labels
    }
    region_loss_fractions = {
        region_label: region_loss_counts[region_label] / float(len(sample_ids))
        for region_label in region_labels
    }

    cnv_color_map = {
        "amplification": secondary_color,
        "gain": contrast_color,
        "loss": primary_color,
        "deep_loss": neutral_color,
    }
    cnv_label_map = {
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

    figure_width = max(8.4, 0.52 * len(sample_ids) + 4.6)
    figure_height = max(5.8, 0.58 * len(region_labels) + 0.42 * len(annotation_tracks) + 2.9)
    fig = plt.figure(figsize=(figure_width, figure_height))
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
            color=neutral_color,
            y=0.985,
        )

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.20,
        right=0.93,
        bottom=0.22,
        top=top_margin,
        width_ratios=(max(3.8, 0.60 * len(sample_ids) + 0.8), 1.70),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.66 * len(region_labels))),
        hspace=0.10,
        wspace=0.14,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)

    burden_positions = list(range(len(sample_ids)))
    burden_values = [sample_burdens[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(region_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(sample_ids, rotation=45, ha="right", fontsize=max(tick_size - 0.3, 8.6), color=neutral_color)
    matrix_axes.set_yticks(range(len(region_labels)))
    matrix_axes.set_yticklabels(region_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(
        max(region_gain_fractions.values(), default=0.0),
        max(region_loss_fractions.values(), default=0.0),
        1e-6,
    )
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(region_labels)))
    gain_values = [region_gain_fractions[region_label] for region_label in region_labels]
    loss_values = [-region_loss_fractions[region_label] for region_label in region_labels]
    gain_bars = frequency_axes.barh(
        frequency_positions,
        gain_values,
        height=0.32,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    loss_bars = frequency_axes.barh(
        frequency_positions,
        loss_values,
        height=0.32,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.axvline(0.0, color=neutral_color, linewidth=0.9, alpha=0.9, zorder=2)
    frequency_axes.set_xlim(-frequency_limit, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(region_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    cnv_cell_patches: list[dict[str, Any]] = []
    for region_label in region_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = region_index[region_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            cnv_state = cnv_lookup.get((sample_id, region_label))
            if not cnv_state:
                continue
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cnv_color_map[cnv_state],
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            cnv_cell_patches.append(
                {
                    "box_id": f"cnv_{region_label}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "region_label": region_label,
                    "cnv_state": cnv_state,
                }
            )

    legend_handles = [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=cnv_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    legend = fig.legend(
        handles=legend_handles,
        labels=[handle.get_label() for handle in legend_handles],
        title=str(display_payload.get("cnv_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.53, 0.02),
        ncol=min(4, len(legend_handles)),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.3, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, burden_y0 = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    burden_x1, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, annotation_y0 = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

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
    y_axis_title_box = _bbox_to_layout_box(
        figure=fig,
        bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
        box_id="y_axis_title",
        box_type="subplot_y_axis_title",
    )
    layout_boxes.extend(
        [
            y_axis_title_box,
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_region_count": int(sample_burdens[sample_id]),
                "bar_box_id": box_id,
            }
        )

    region_frequency_metrics: list[dict[str, Any]] = []
    for region_label, gain_bar, loss_bar in zip(region_labels, gain_bars, loss_bars, strict=True):
        gain_box_id = f"freq_gain_{region_label}"
        loss_box_id = f"freq_loss_{region_label}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=gain_bar.get_window_extent(renderer=renderer),
                    box_id=gain_box_id,
                    box_type="bar",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=loss_bar.get_window_extent(renderer=renderer),
                    box_id=loss_box_id,
                    box_type="bar",
                ),
            ]
        )
        region_frequency_metrics.append(
            {
                "region_label": region_label,
                "gain_fraction": float(region_gain_fractions[region_label]),
                "loss_fraction": float(region_loss_fractions[region_label]),
                "gain_bar_box_id": gain_box_id,
                "loss_bar_box_id": loss_box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    cnv_cells_metrics: list[dict[str, Any]] = []
    for item in cnv_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="cnv_cell",
            )
        )
        cnv_cells_metrics.append(
            {
                "sample_id": str(item["sample_id"]),
                "region_label": str(item["region_label"]),
                "cnv_state": str(item["cnv_state"]),
                "box_id": str(item["box_id"]),
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

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
                "cnv_legend_title": str(display_payload.get("cnv_legend_title") or "").strip(),
                "sample_ids": sample_ids,
                "region_labels": region_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "region_gain_loss_frequencies": region_frequency_metrics,
                "cnv_cells": cnv_cells_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_genomic_alteration_landscape_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    alteration_records = list(display_payload.get("alteration_records") or [])
    if not gene_order or not sample_order or not annotation_tracks or not alteration_records:
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, and alteration_records"
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

    gene_labels = [str(item["label"]) for item in gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}

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

    figure_width = max(8.8, 0.52 * len(sample_ids) + 4.8)
    figure_height = max(5.8, 0.60 * len(gene_labels) + 0.42 * len(annotation_tracks) + 3.0)
    fig = plt.figure(figsize=(figure_width, figure_height))
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
            color=neutral_color,
            y=0.985,
        )

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.20,
        right=0.93,
        bottom=0.22,
        top=top_margin,
        width_ratios=(max(3.8, 0.60 * len(sample_ids) + 0.8), 1.55),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.70 * len(gene_labels))),
        hspace=0.10,
        wspace=0.14,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(
        sample_ids,
        rotation=45,
        ha="right",
        fontsize=max(tick_size - 0.3, 8.6),
        color=neutral_color,
    )
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    alteration_cell_patches: list[dict[str, Any]] = []
    alteration_overlay_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            alteration = alteration_lookup.get((sample_id, gene_label))
            if alteration is None:
                continue
            mutation_class = str(alteration.get("mutation_class") or "").strip()
            cnv_state = str(alteration.get("cnv_state") or "").strip()
            cell_color = cnv_color_map[cnv_state] if cnv_state else mutation_color_map[mutation_class]
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cell_color,
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            box_id = f"alteration_{gene_label}_{sample_id}"
            overlay_box_id = ""
            if mutation_class and cnv_state:
                overlay_patch = matplotlib.patches.Rectangle(
                    (x_index - 0.21, y_index - 0.32),
                    0.42,
                    0.64,
                    facecolor=mutation_color_map[mutation_class],
                    edgecolor="white",
                    linewidth=0.8,
                    zorder=4,
                )
                matrix_axes.add_patch(overlay_patch)
                overlay_box_id = f"overlay_{gene_label}_{sample_id}"
                alteration_overlay_patches.append(
                    {
                        "box_id": overlay_box_id,
                        "patch": overlay_patch,
                    }
                )
            alteration_cell_patches.append(
                {
                    "box_id": box_id,
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "mutation_class": mutation_class,
                    "cnv_state": cnv_state,
                    "overlay_box_id": overlay_box_id,
                }
            )

    legend_handles = [
        matplotlib.patches.Patch(facecolor=mutation_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "fusion")
    ] + [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    legend = fig.legend(
        handles=legend_handles,
        labels=[handle.get_label() for handle in legend_handles],
        title=str(display_payload.get("alteration_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.54, 0.02),
        ncol=4,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.3, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, _ = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    _, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, _ = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

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
    y_axis_title_box = _bbox_to_layout_box(
        figure=fig,
        bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
        box_id="y_axis_title",
        box_type="subplot_y_axis_title",
    )
    layout_boxes.extend(
        [
            y_axis_title_box,
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    overlay_box_id_by_alteration_id: dict[str, str] = {}
    for item in alteration_overlay_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_overlay",
            )
        )
        overlay_box_id_by_alteration_id[str(item["box_id"])] = str(item["box_id"])

    alteration_cells_metrics: list[dict[str, Any]] = []
    for item in alteration_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_cell",
            )
        )
        metric_item = {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "box_id": str(item["box_id"]),
        }
        mutation_class = str(item["mutation_class"])
        cnv_state = str(item["cnv_state"])
        if mutation_class:
            metric_item["mutation_class"] = mutation_class
        if cnv_state:
            metric_item["cnv_state"] = cnv_state
        overlay_box_id = str(item["overlay_box_id"])
        if overlay_box_id:
            metric_item["overlay_box_id"] = overlay_box_id_by_alteration_id[overlay_box_id]
        alteration_cells_metrics.append(metric_item)

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

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
                "alteration_legend_title": str(display_payload.get("alteration_legend_title") or "").strip(),
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_alteration_frequencies": gene_frequency_metrics,
                "alteration_cells": alteration_cells_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_genomic_alteration_consequence_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    alteration_records = list(display_payload.get("alteration_records") or [])
    driver_gene_order = list(display_payload.get("driver_gene_order") or [])
    consequence_panel_order = list(display_payload.get("consequence_panel_order") or [])
    consequence_points = list(display_payload.get("consequence_points") or [])
    if (
        not gene_order
        or not sample_order
        or not annotation_tracks
        or not alteration_records
        or not driver_gene_order
        or not consequence_panel_order
        or not consequence_points
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, alteration_records, "
            "driver_gene_order, consequence_panel_order, and consequence_points"
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
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}

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

    panel_id_order = [str(item["panel_id"]) for item in consequence_panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in consequence_panel_order}
    point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in panel_id_order}
    for point in consequence_points:
        point_lookup[str(point["panel_id"])].append(point)

    effect_threshold = float(display_payload.get("effect_threshold") or 0.0)
    significance_threshold = float(display_payload.get("significance_threshold") or 0.0)
    all_effect_values = [float(item["effect_value"]) for item in consequence_points]
    all_significance_values = [float(item["significance_value"]) for item in consequence_points]
    x_limit_core = max(max(abs(value) for value in all_effect_values), effect_threshold, 1e-6)
    x_padding = max(x_limit_core * 0.18, 0.20)
    x_limit_abs = x_limit_core + x_padding
    y_limit_top = max(max(all_significance_values), significance_threshold) * 1.12 + 0.25
    y_limit_top = max(y_limit_top, significance_threshold + 0.50)

    figure_width = max(12.6, 0.52 * len(sample_ids) + 7.6)
    figure_height = max(6.4, 0.60 * len(gene_labels) + 3.2)
    fig = plt.figure(figsize=(figure_width, figure_height))
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

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        3,
        left=0.17,
        right=0.96,
        bottom=0.22,
        top=top_margin,
        width_ratios=(
            max(3.8, 0.60 * len(sample_ids) + 0.8),
            1.45,
            max(2.5, 1.9 + 0.30 * len(driver_gene_labels)),
        ),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.70 * len(gene_labels))),
        hspace=0.10,
        wspace=0.16,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)
    consequence_grid = grid[:, 2].subgridspec(len(panel_id_order), 1, hspace=0.28)
    consequence_axes_list = [fig.add_subplot(consequence_grid[index, 0]) for index in range(len(panel_id_order))]

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(
        sample_ids,
        rotation=45,
        ha="right",
        fontsize=max(tick_size - 0.3, 8.6),
        color=neutral_color,
    )
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    alteration_cell_patches: list[dict[str, Any]] = []
    alteration_overlay_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            alteration = alteration_lookup.get((sample_id, gene_label))
            if alteration is None:
                continue
            mutation_class = str(alteration.get("mutation_class") or "").strip()
            cnv_state = str(alteration.get("cnv_state") or "").strip()
            cell_color = cnv_color_map[cnv_state] if cnv_state else mutation_color_map[mutation_class]
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cell_color,
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            box_id = f"alteration_{gene_label}_{sample_id}"
            overlay_box_id = ""
            if mutation_class and cnv_state:
                overlay_patch = matplotlib.patches.Rectangle(
                    (x_index - 0.21, y_index - 0.32),
                    0.42,
                    0.64,
                    facecolor=mutation_color_map[mutation_class],
                    edgecolor="white",
                    linewidth=0.8,
                    zorder=4,
                )
                matrix_axes.add_patch(overlay_patch)
                overlay_box_id = f"overlay_{gene_label}_{sample_id}"
                alteration_overlay_patches.append({"box_id": overlay_box_id, "patch": overlay_patch})
            alteration_cell_patches.append(
                {
                    "box_id": box_id,
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "mutation_class": mutation_class,
                    "cnv_state": cnv_state,
                    "overlay_box_id": overlay_box_id,
                }
            )

    consequence_records: list[dict[str, Any]] = []
    for axes_item, panel_id in zip(consequence_axes_list, panel_id_order, strict=True):
        panel_points = list(point_lookup.get(panel_id) or [])
        scatter_colors = {
            "upregulated": secondary_color,
            "downregulated": primary_color,
            "background": background_color,
        }
        axes_item.scatter(
            [float(item["effect_value"]) for item in panel_points],
            [float(item["significance_value"]) for item in panel_points],
            s=74.0,
            c=[scatter_colors[str(item["regulation_class"])] for item in panel_points],
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        axes_item.axvline(-effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axvline(effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axhline(significance_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit_abs, x_limit_abs)
        axes_item.set_ylim(0.0, y_limit_top)
        axes_item.set_xlabel(
            str(display_payload.get("consequence_x_label") or "").strip(),
            fontsize=max(axis_title_size - 0.1, 10.0),
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            panel_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
        axes_item.grid(axis="both", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        _apply_publication_axes_style(axes_item)

        point_artists: list[dict[str, Any]] = []
        label_artists: list[dict[str, Any]] = []
        for point in panel_points:
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            gene_label = str(point["gene_label"])
            point_box_id = f"consequence_point_{panel_id}_{gene_label}"
            point_artists.append(
                {
                    "point_box_id": point_box_id,
                    "gene_label": gene_label,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                }
            )
            offset_x = -8 if effect_value >= 0.0 else 8
            ha = "right" if effect_value >= 0.0 else "left"
            label_artist = axes_item.annotate(
                gene_label,
                xy=(effect_value, significance_value),
                xytext=(offset_x, 6),
                textcoords="offset points",
                fontsize=max(tick_size - 0.6, 8.2),
                color=neutral_color,
                ha=ha,
                va="bottom",
                zorder=4,
                annotation_clip=True,
            )
            label_artists.append(
                {
                    "gene_label": gene_label,
                    "box_id": f"consequence_label_{panel_id}_{gene_label}",
                    "artist": label_artist,
                }
            )

        consequence_records.append(
            {
                "panel_id": panel_id,
                "axes": axes_item,
                "points": point_artists,
                "label_artists": label_artists,
            }
        )

    alteration_legend_handles = [
        matplotlib.patches.Patch(facecolor=mutation_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "fusion")
    ] + [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    alteration_legend = fig.legend(
        handles=alteration_legend_handles,
        labels=[handle.get_label() for handle in alteration_legend_handles],
        title=str(display_payload.get("alteration_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.33, 0.02),
        ncol=4,
        frameon=False,
        fontsize=max(tick_size - 1.0, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.2,
    )
    consequence_legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=secondary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Upregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=primary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Downregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=background_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Background",
        ),
    ]
    consequence_legend = fig.legend(
        consequence_legend_handles,
        [str(handle.get_label()) for handle in consequence_legend_handles],
        title=str(display_payload.get("consequence_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.80, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.9, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.1,
    )
    fig.add_artist(alteration_legend)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, _ = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    _, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, _ = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

    consequence_panel_label_artists: list[Any] = []
    for index, record in enumerate(consequence_records, start=1):
        axes_item = record["axes"]
        panel_token = chr(ord("B") + index - 1)
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.060, 0.020), 0.032)
        consequence_panel_label_artists.append(
            fig.text(
                panel_x0 + x_padding,
                panel_y1 - y_padding,
                panel_token,
                transform=fig.transFigure,
                fontsize=max(panel_label_size + 1.4, 13.0),
                fontweight="bold",
                color=neutral_color,
                ha="left",
                va="top",
            )
        )

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
                bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    overlay_box_id_by_alteration_id: dict[str, str] = {}
    for item in alteration_overlay_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_overlay",
            )
        )
        overlay_box_id_by_alteration_id[str(item["box_id"])] = str(item["box_id"])

    alteration_cells_metrics: list[dict[str, Any]] = []
    for item in alteration_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_cell",
            )
        )
        metric_item = {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "box_id": str(item["box_id"]),
        }
        mutation_class = str(item["mutation_class"])
        cnv_state = str(item["cnv_state"])
        if mutation_class:
            metric_item["mutation_class"] = mutation_class
        if cnv_state:
            metric_item["cnv_state"] = cnv_state
        overlay_box_id = str(item["overlay_box_id"])
        if overlay_box_id:
            metric_item["overlay_box_id"] = overlay_box_id_by_alteration_id[overlay_box_id]
        alteration_cells_metrics.append(metric_item)

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=alteration_legend.get_window_extent(renderer=renderer),
            box_id="legend_alteration",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=consequence_legend.get_window_extent(renderer=renderer),
            box_id="legend_consequence",
            box_type="legend",
        ),
    ]

    consequence_panels_metrics: list[dict[str, Any]] = []
    threshold_half_width = max(x_limit_abs * 0.006, 0.015)
    threshold_half_height = max(y_limit_top * 0.008, 0.04)
    horizontal_threshold_inset = max(x_limit_abs * 0.015, 0.03)
    point_half_width = max(x_limit_abs * 0.03, 0.05)
    point_half_height = max(y_limit_top * 0.035, 0.08)

    def _clip_box_to_panel(
        box: dict[str, Any],
        *,
        panel_box: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **box,
            "x0": max(float(box["x0"]), float(panel_box["x0"])),
            "y0": max(float(box["y0"]), float(panel_box["y0"])),
            "x1": min(float(box["x1"]), float(panel_box["x1"])),
            "y1": min(float(box["y1"]), float(panel_box["y1"])),
        }

    for index, (record, panel_label_artist) in enumerate(zip(consequence_records, consequence_panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_label_token = chr(ord("A") + index)
        panel_token = chr(ord("A") + index - 1)
        panel_box_id = f"panel_consequence_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"consequence_title_{panel_token}"
        panel_label_box_id = f"panel_label_{panel_label_token}"
        x_axis_title_box_id = f"consequence_x_axis_title_{panel_token}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
                    box_id=panel_title_box_id,
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=x_axis_title_box_id,
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=panel_label_box_id,
                    box_type="panel_label",
                ),
            ]
        )
        threshold_left_box_id = f"{record['panel_id']}_threshold_left"
        threshold_right_box_id = f"{record['panel_id']}_threshold_right"
        threshold_significance_box_id = f"{record['panel_id']}_significance_threshold"
        guide_boxes.extend(
            [
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=-effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_left_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_right_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-x_limit_abs + horizontal_threshold_inset,
                        y0=significance_threshold - threshold_half_height,
                        x1=x_limit_abs - horizontal_threshold_inset,
                        y1=significance_threshold + threshold_half_height,
                        box_id=threshold_significance_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
            ]
        )

        label_box_lookup: dict[str, str] = {}
        for label_item in record["label_artists"]:
            label_box_id = str(label_item["box_id"])
            label_box_lookup[str(label_item["gene_label"])] = label_box_id
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_item["artist"].get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="annotation_label",
                )
            )

        normalized_points: list[dict[str, Any]] = []
        for point in record["points"]:
            gene_label = str(point["gene_label"])
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            point_box_id = str(point["point_box_id"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=effect_value - point_half_width,
                    y0=significance_value - point_half_height,
                    x1=effect_value + point_half_width,
                    y1=significance_value + point_half_height,
                    box_id=point_box_id,
                    box_type="scatter_point",
                )
            )
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=effect_value,
                y=significance_value,
            )
            normalized_points.append(
                {
                    "gene_label": gene_label,
                    "x": point_x,
                    "y": point_y,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                    "point_box_id": point_box_id,
                    "label_box_id": label_box_lookup[gene_label],
                }
            )

        consequence_panels_metrics.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": panel_title_lookup[str(record["panel_id"])],
                "panel_label": panel_label_token,
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
                "effect_threshold_left_box_id": threshold_left_box_id,
                "effect_threshold_right_box_id": threshold_right_box_id,
                "significance_threshold_box_id": threshold_significance_box_id,
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
                "alteration_legend_title": str(display_payload.get("alteration_legend_title") or "").strip(),
                "consequence_legend_title": str(display_payload.get("consequence_legend_title") or "").strip(),
                "effect_threshold": effect_threshold,
                "significance_threshold": significance_threshold,
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "driver_gene_labels": driver_gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_alteration_frequencies": gene_frequency_metrics,
                "alteration_cells": alteration_cells_metrics,
                "consequence_panels": consequence_panels_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_omics_volcano_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panel_order = list(display_payload.get("panel_order") or [])
    points = list(display_payload.get("points") or [])
    if not panel_order or not points:
        raise RuntimeError(f"{template_id} requires non-empty panel_order and points")

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

    downregulated_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    upregulated_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    background_color = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    panel_id_order = [str(item["panel_id"]) for item in panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in panel_order}
    point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in panel_id_order}
    for point in points:
        point_lookup[str(point["panel_id"])].append(point)

    effect_threshold = float(display_payload.get("effect_threshold") or 0.0)
    significance_threshold = float(display_payload.get("significance_threshold") or 0.0)
    all_effect_values = [float(item["effect_value"]) for item in points]
    all_significance_values = [float(item["significance_value"]) for item in points]
    x_limit_core = max(max(abs(value) for value in all_effect_values), effect_threshold, 1e-6)
    x_padding = max(x_limit_core * 0.18, 0.20)
    x_limit_abs = x_limit_core + x_padding
    y_limit_top = max(max(all_significance_values), significance_threshold) * 1.12 + 0.25
    y_limit_top = max(y_limit_top, significance_threshold + 0.50)

    figure_width = max(8.6, 4.2 * len(panel_id_order) + 1.4)
    fig, axes = plt.subplots(1, len(panel_id_order), figsize=(figure_width, 5.7), squeeze=False)
    axes_list = list(axes[0])
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
            color=neutral_color,
            y=0.985,
        )

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel_id in zip(axes_list, panel_id_order, strict=True):
        panel_points = list(point_lookup.get(panel_id) or [])
        color_lookup = {
            "upregulated": upregulated_color,
            "downregulated": downregulated_color,
            "background": background_color,
        }
        scatter = axes_item.scatter(
            [float(item["effect_value"]) for item in panel_points],
            [float(item["significance_value"]) for item in panel_points],
            s=70.0,
            c=[color_lookup[str(item["regulation_class"])] for item in panel_points],
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        _ = scatter
        axes_item.axvline(-effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axvline(effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axhline(significance_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit_abs, x_limit_abs)
        axes_item.set_ylim(0.0, y_limit_top)
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            panel_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
        axes_item.grid(axis="both", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        _apply_publication_axes_style(axes_item)

        annotation_artists: list[dict[str, Any]] = []
        for label_index, point in enumerate((item for item in panel_points if str(item.get("label_text") or "").strip())):
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            label_text = str(point.get("label_text") or "").strip()
            offset_x = -8 if effect_value >= 0.0 else 8
            ha = "right" if effect_value >= 0.0 else "left"
            artist = axes_item.annotate(
                label_text,
                xy=(effect_value, significance_value),
                xytext=(offset_x, 6),
                textcoords="offset points",
                fontsize=max(tick_size - 0.5, 8.2),
                color=neutral_color,
                ha=ha,
                va="bottom",
                zorder=4,
                annotation_clip=True,
            )
            annotation_artists.append(
                {
                    "box_id": f"label_{chr(ord('A') + len(panel_records))}_{label_index}",
                    "artist": artist,
                    "feature_label": str(point["feature_label"]),
                    "label_text": label_text,
                }
            )

        panel_records.append(
            {
                "panel_id": panel_id,
                "axes": axes_item,
                "points": panel_points,
                "annotation_artists": annotation_artists,
            }
        )

    top_margin = 0.84 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.10, right=0.96, top=top_margin, bottom=0.22, wspace=0.24)

    y_axis_title_artist = fig.text(
        0.03,
        0.52,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        ha="center",
        va="center",
    )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=upregulated_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Upregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=downregulated_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Downregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=background_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Background",
        ),
    ]
    legend = fig.legend(
        legend_handles,
        [str(handle.get_label()) for handle in legend_handles],
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.50, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.4),
        title_fontsize=max(tick_size - 0.4, 8.8),
        columnspacing=1.4,
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
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=chr(ord("A") + index))
        for index, record in enumerate(panel_records)
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
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend",
            box_type="legend",
        )
    ]
    normalized_panels: list[dict[str, Any]] = []
    threshold_half_width = max(x_limit_abs * 0.006, 0.015)
    threshold_half_height = max(y_limit_top * 0.008, 0.04)
    horizontal_threshold_inset = max(x_limit_abs * 0.015, 0.03)

    for index, (record, panel_label_artist) in enumerate(zip(panel_records, panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_token = chr(ord("A") + index - 1)
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"panel_title_{panel_token}"
        panel_label_box_id = f"panel_label_{panel_token}"
        x_axis_title_box_id = f"x_axis_title_{panel_token}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
                    box_id=panel_title_box_id,
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=x_axis_title_box_id,
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=panel_label_box_id,
                    box_type="panel_label",
                ),
            ]
        )
        guide_boxes.extend(
            [
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=-effect_threshold - threshold_half_width,
                    y0=0.0,
                    x1=-effect_threshold + threshold_half_width,
                    y1=y_limit_top,
                    box_id=f"panel_{panel_token}_threshold_left",
                    box_type="reference_line",
                ),
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=effect_threshold - threshold_half_width,
                    y0=0.0,
                    x1=effect_threshold + threshold_half_width,
                    y1=y_limit_top,
                    box_id=f"panel_{panel_token}_threshold_right",
                    box_type="reference_line",
                ),
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=-x_limit_abs + horizontal_threshold_inset,
                    y0=significance_threshold - threshold_half_height,
                    x1=x_limit_abs - horizontal_threshold_inset,
                    y1=significance_threshold + threshold_half_height,
                    box_id=f"panel_{panel_token}_significance_threshold",
                    box_type="reference_line",
                ),
            ]
        )

        normalized_points: list[dict[str, Any]] = []
        label_box_lookup = {item["feature_label"]: item["box_id"] for item in record["annotation_artists"]}
        for annotation in record["annotation_artists"]:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=annotation["artist"].get_window_extent(renderer=renderer),
                    box_id=str(annotation["box_id"]),
                    box_type="annotation_label",
                )
            )
        for point in record["points"]:
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=effect_value,
                y=significance_value,
            )
            normalized_point = {
                "feature_label": str(point["feature_label"]),
                "x": point_x,
                "y": point_y,
                "effect_value": effect_value,
                "significance_value": significance_value,
                "regulation_class": str(point["regulation_class"]),
            }
            label_text = str(point.get("label_text") or "").strip()
            if label_text:
                normalized_point["label_text"] = label_text
                normalized_point["label_box_id"] = label_box_lookup[str(point["feature_label"])]
            normalized_points.append(normalized_point)

        normalized_panels.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": panel_title_lookup[str(record["panel_id"])],
                "panel_label": panel_token,
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
                "effect_threshold_left_box_id": f"panel_{panel_token}_threshold_left",
                "effect_threshold_right_box_id": f"panel_{panel_token}_threshold_right",
                "significance_threshold_box_id": f"panel_{panel_token}_significance_threshold",
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
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "effect_threshold": effect_threshold,
                "significance_threshold": significance_threshold,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_atlas_spatial_bridge_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    atlas_points = list(display_payload.get("atlas_points") or [])
    spatial_points = list(display_payload.get("spatial_points") or [])
    composition_groups = list(display_payload.get("composition_groups") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if (
        not atlas_points
        or not spatial_points
        or not composition_groups
        or not matrix_cells
        or not row_order
        or not column_order
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty atlas_points, spatial_points, composition_groups, row_order, column_order, and cells"
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

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(13.8, 8.2),
        gridspec_kw={"height_ratios": [1.0, 0.94], "width_ratios": [1.0, 1.0]},
    )
    atlas_axes, spatial_axes = axes[0]
    composition_axes, heatmap_axes = axes[1]
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
        state_points = [item for item in atlas_points if str(item["state_label"]) == state_label]
        if not state_points:
            continue
        atlas_axes.scatter(
            [float(item["x"]) for item in state_points],
            [float(item["y"]) for item in state_points],
            label=state_label,
            s=38,
            alpha=0.92,
            color=state_color_lookup[state_label],
            edgecolors="white",
            linewidths=0.4,
        )
    atlas_axes.set_title(
        str(display_payload.get("atlas_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_xlabel(
        str(display_payload.get("atlas_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_ylabel(
        str(display_payload.get("atlas_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    atlas_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(atlas_axes)
    atlas_annotation_artist = None
    atlas_annotation = str(display_payload.get("atlas_annotation") or "").strip()
    if atlas_annotation:
        atlas_annotation_artist = atlas_axes.text(
            0.03,
            0.05,
            atlas_annotation,
            transform=atlas_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    for state_label in state_labels:
        state_points = [item for item in spatial_points if str(item["state_label"]) == state_label]
        if not state_points:
            continue
        spatial_axes.scatter(
            [float(item["x"]) for item in state_points],
            [float(item["y"]) for item in state_points],
            label=state_label,
            s=42,
            alpha=0.94,
            color=state_color_lookup[state_label],
            edgecolors="white",
            linewidths=0.5,
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
    spatial_annotation_artist = None
    spatial_annotation = str(display_payload.get("spatial_annotation") or "").strip()
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
    for state_label in state_labels:
        state_values = []
        for group in ordered_composition_groups:
            state_lookup = {
                str(item["state_label"]): float(item["proportion"])
                for item in list(group.get("state_proportions") or [])
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
    composition_annotation_artist = None
    composition_annotation = str(display_payload.get("composition_annotation") or "").strip()
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
    heatmap_annotation_artist = None
    heatmap_annotation = str(display_payload.get("heatmap_annotation") or "").strip()
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

    title_top = 0.86 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.10,
        right=0.92,
        top=max(0.78, title_top) if show_figure_title else 0.88,
        bottom=0.18,
        hspace=0.34,
        wspace=0.28,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.15, 0.02),
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

    panel_label_a = _add_figure_panel_label(axes_item=atlas_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes_item=spatial_axes, label="B")
    panel_label_c = _add_figure_panel_label(axes_item=composition_axes, label="C")
    panel_label_d = _add_figure_panel_label(axes_item=heatmap_axes, label="D")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.title.get_window_extent(renderer=renderer),
            box_id="atlas_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
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
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_d.get_window_extent(renderer=renderer),
            box_id="panel_label_D",
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
        (atlas_annotation_artist, "atlas_annotation"),
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
            bbox=atlas_axes.get_window_extent(renderer=renderer),
            box_id="panel_atlas",
            box_type="panel",
        ),
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

    normalized_atlas_points: list[dict[str, Any]] = []
    for item in atlas_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=atlas_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_point = {"x": point_x, "y": point_y, "state_label": str(item["state_label"])}
        group_label = str(item.get("group_label") or "").strip()
        if group_label:
            normalized_point["group_label"] = group_label
        normalized_atlas_points.append(normalized_point)

    normalized_spatial_points: list[dict[str, Any]] = []
    for item in spatial_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=spatial_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_point = {"x": point_x, "y": point_y, "state_label": str(item["state_label"])}
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_spatial_points.append(normalized_point)

    normalized_composition_groups: list[dict[str, Any]] = []
    for group in ordered_composition_groups:
        normalized_composition_groups.append(
            {
                "group_label": str(group["group_label"]),
                "group_order": int(group["group_order"]),
                "state_proportions": [
                    {"state_label": str(item["state_label"]), "proportion": float(item["proportion"])}
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
                "atlas_points": normalized_atlas_points,
                "spatial_points": normalized_spatial_points,
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


def _render_python_atlas_spatial_trajectory_storyboard_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    atlas_points = list(display_payload.get("atlas_points") or [])
    spatial_points = list(display_payload.get("spatial_points") or [])
    trajectory_points = list(display_payload.get("trajectory_points") or [])
    composition_groups = list(display_payload.get("composition_groups") or [])
    progression_bins = list(display_payload.get("progression_bins") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    state_order = list(display_payload.get("state_order") or [])
    branch_order = list(display_payload.get("branch_order") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if (
        not atlas_points
        or not spatial_points
        or not trajectory_points
        or not composition_groups
        or not progression_bins
        or not matrix_cells
        or not state_order
        or not branch_order
        or not row_order
        or not column_order
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty atlas_points, spatial_points, trajectory_points, composition_groups, "
            "progression_bins, state_order, branch_order, row_order, column_order, and cells"
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

    state_labels = [str(item["label"]) for item in state_order]
    branch_labels = [str(item["label"]) for item in branch_order]
    row_labels = [str(item["label"]) for item in row_order]
    bin_labels = [str(item["label"]) for item in column_order]
    state_color_lookup = {
        label: state_palette[index % len(state_palette)] for index, label in enumerate(state_labels)
    }

    fig = plt.figure(figsize=(14.2, 8.2))
    fig.patch.set_facecolor("white")
    grid = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.94], width_ratios=[1.0, 1.0, 1.08])
    atlas_axes = fig.add_subplot(grid[0, 0])
    spatial_axes = fig.add_subplot(grid[0, 1])
    trajectory_axes = fig.add_subplot(grid[0, 2])
    composition_axes = fig.add_subplot(grid[1, 0])
    heatmap_axes = fig.add_subplot(grid[1, 1:3])

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

    def _plot_state_scatter(axes: Any, points: list[dict[str, Any]]) -> None:
        for state_label in state_labels:
            filtered_points = [item for item in points if str(item["state_label"]) == state_label]
            if not filtered_points:
                continue
            axes.scatter(
                [float(item["x"]) for item in filtered_points],
                [float(item["y"]) for item in filtered_points],
                label=state_label,
                s=36,
                alpha=0.92,
                color=state_color_lookup[state_label],
                edgecolors="white",
                linewidths=0.4,
            )

    _plot_state_scatter(atlas_axes, atlas_points)
    atlas_axes.set_title(
        str(display_payload.get("atlas_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_xlabel(
        str(display_payload.get("atlas_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_ylabel(
        str(display_payload.get("atlas_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    atlas_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(atlas_axes)

    _plot_state_scatter(spatial_axes, spatial_points)
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

    for branch_label in branch_labels:
        branch_points = sorted(
            [item for item in trajectory_points if str(item["branch_label"]) == branch_label],
            key=lambda item: float(item["pseudotime"]),
        )
        if len(branch_points) >= 2:
            trajectory_axes.plot(
                [float(item["x"]) for item in branch_points],
                [float(item["y"]) for item in branch_points],
                color=neutral_color,
                linewidth=1.4,
                alpha=0.45,
            )
    _plot_state_scatter(trajectory_axes, trajectory_points)
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
            height=0.60,
            color=matplotlib.colors.to_rgba(state_color_lookup[state_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
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
    heatmap_axes.set_xticklabels(bin_labels, fontsize=tick_size, rotation=18, ha="right", color=neutral_color)
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

    def _optional_annotation(axes_item: Any, key: str) -> Any:
        annotation = str(display_payload.get(key) or "").strip()
        if not annotation:
            return None
        return axes_item.text(
            0.03,
            0.05,
            annotation,
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    atlas_annotation_artist = _optional_annotation(atlas_axes, "atlas_annotation")
    spatial_annotation_artist = _optional_annotation(spatial_axes, "spatial_annotation")
    trajectory_annotation_artist = _optional_annotation(trajectory_axes, "trajectory_annotation")
    composition_annotation_artist = _optional_annotation(composition_axes, "composition_annotation")
    heatmap_annotation_artist = _optional_annotation(heatmap_axes, "heatmap_annotation")

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.10,
        right=0.92,
        top=max(0.70, title_top) if show_figure_title else 0.88,
        bottom=0.20,
        wspace=0.34,
        hspace=0.42,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.06, 0.02),
        ncol=min(4, max(1, len(state_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=heatmap_axes, fraction=0.032, pad=0.03)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

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
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_panel_label(axes_item=atlas_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=spatial_axes, label="B")
    panel_label_c = _add_panel_label(axes_item=trajectory_axes, label="C")
    panel_label_d = _add_panel_label(axes_item=composition_axes, label="D")
    panel_label_e = _add_panel_label(axes_item=heatmap_axes, label="E")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.title.get_window_extent(renderer=renderer),
            box_id="atlas_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
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
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_d.get_window_extent(renderer=renderer),
            box_id="panel_label_D",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_e.get_window_extent(renderer=renderer),
            box_id="panel_label_E",
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
        (atlas_annotation_artist, "atlas_annotation"),
        (spatial_annotation_artist, "spatial_annotation"),
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
            bbox=atlas_axes.get_window_extent(renderer=renderer),
            box_id="panel_atlas",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.get_window_extent(renderer=renderer),
            box_id="panel_spatial",
            box_type="panel",
        ),
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

    def _normalize_scatter_points(axes_item: Any, points: list[dict[str, Any]], extra_keys: tuple[str, ...]) -> list[dict[str, Any]]:
        normalized_points: list[dict[str, Any]] = []
        for item in points:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(item["x"]),
                y=float(item["y"]),
            )
            normalized_point = {
                "x": point_x,
                "y": point_y,
                "state_label": str(item["state_label"]),
            }
            for extra_key in extra_keys:
                if extra_key in item and str(item.get(extra_key) or "").strip():
                    normalized_point[extra_key] = item[extra_key]
            if "pseudotime" in item:
                normalized_point["pseudotime"] = float(item["pseudotime"])
            normalized_points.append(normalized_point)
        return normalized_points

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

    ordered_progression_bins = sorted(progression_bins, key=lambda item: int(item["bin_order"]))
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
                "atlas_points": _normalize_scatter_points(atlas_axes, atlas_points, ()),
                "spatial_points": _normalize_scatter_points(spatial_axes, spatial_points, ("region_label",)),
                "trajectory_points": _normalize_scatter_points(
                    trajectory_axes,
                    trajectory_points,
                    ("branch_label",),
                ),
                "state_labels": state_labels,
                "branch_labels": branch_labels,
                "bin_labels": bin_labels,
                "row_labels": row_labels,
                "composition_groups": normalized_composition_groups,
                "progression_bins": normalized_progression_bins,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_atlas_spatial_trajectory_density_coverage_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    atlas_points = list(display_payload.get("atlas_points") or [])
    spatial_points = list(display_payload.get("spatial_points") or [])
    trajectory_points = list(display_payload.get("trajectory_points") or [])
    state_order = list(display_payload.get("state_order") or [])
    context_order = list(display_payload.get("context_order") or [])
    support_cells = list(display_payload.get("support_cells") or [])
    if not atlas_points or not spatial_points or not trajectory_points or not state_order or not context_order or not support_cells:
        raise RuntimeError(
            f"{template_id} requires non-empty atlas_points, spatial_points, trajectory_points, "
            "state_order, context_order, and support_cells"
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

    state_labels = [str(item["label"]) for item in state_order]
    context_labels = [str(item["label"]) for item in context_order]
    context_kinds = [str(item["context_kind"]) for item in context_order]
    region_labels = list(
        dict.fromkeys(
            str(item.get("region_label") or "").strip()
            for item in spatial_points
            if str(item.get("region_label") or "").strip()
        )
    )
    branch_labels = list(
        dict.fromkeys(
            str(item.get("branch_label") or "").strip()
            for item in trajectory_points
            if str(item.get("branch_label") or "").strip()
        )
    )
    state_color_lookup = {
        label: state_palette[index % len(state_palette)] for index, label in enumerate(state_labels)
    }
    support_scale_label = str(display_payload.get("support_scale_label") or "").strip()

    fig = plt.figure(figsize=(13.8, 8.0))
    fig.patch.set_facecolor("white")
    grid = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.92], width_ratios=[1.0, 1.0, 1.0])
    atlas_axes = fig.add_subplot(grid[0, 0])
    spatial_axes = fig.add_subplot(grid[0, 1])
    trajectory_axes = fig.add_subplot(grid[0, 2])
    support_axes = fig.add_subplot(grid[1, :])

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

    def _plot_state_scatter(axes_item: Any, points: list[dict[str, Any]]) -> None:
        for state_label in state_labels:
            filtered_points = [item for item in points if str(item["state_label"]) == state_label]
            if not filtered_points:
                continue
            axes_item.scatter(
                [float(item["x"]) for item in filtered_points],
                [float(item["y"]) for item in filtered_points],
                label=state_label,
                s=36,
                alpha=0.92,
                color=state_color_lookup[state_label],
                edgecolors="white",
                linewidths=0.4,
            )

    _plot_state_scatter(atlas_axes, atlas_points)
    atlas_axes.set_title(
        str(display_payload.get("atlas_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_xlabel(
        str(display_payload.get("atlas_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_ylabel(
        str(display_payload.get("atlas_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    atlas_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(atlas_axes)

    _plot_state_scatter(spatial_axes, spatial_points)
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

    for branch_label in branch_labels:
        branch_points = sorted(
            [item for item in trajectory_points if str(item["branch_label"]) == branch_label],
            key=lambda item: float(item["pseudotime"]),
        )
        if len(branch_points) >= 2:
            trajectory_axes.plot(
                [float(item["x"]) for item in branch_points],
                [float(item["y"]) for item in branch_points],
                color=neutral_color,
                linewidth=1.4,
                alpha=0.45,
            )
    _plot_state_scatter(trajectory_axes, trajectory_points)
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

    support_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in support_cells}
    support_matrix = [[support_lookup[(context_label, state_label)] for context_label in context_labels] for state_label in state_labels]
    heatmap_artist = support_axes.imshow(support_matrix, aspect="auto", cmap="Blues", vmin=0.0, vmax=1.0)
    support_axes.set_title(
        str(display_payload.get("support_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_xlabel(
        str(display_payload.get("support_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_ylabel(
        str(display_payload.get("support_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_xticks(range(len(context_labels)))
    support_axes.set_xticklabels(context_labels, fontsize=tick_size, rotation=18, ha="right", color=neutral_color)
    support_axes.set_yticks(range(len(state_labels)))
    support_axes.set_yticklabels(state_labels, fontsize=tick_size, color=neutral_color)
    support_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(support_axes)
    for row_index, state_label in enumerate(state_labels):
        for column_index, context_label in enumerate(context_labels):
            value = support_lookup[(context_label, state_label)]
            support_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )

    def _optional_annotation(axes_item: Any, key: str) -> Any:
        annotation = str(display_payload.get(key) or "").strip()
        if not annotation:
            return None
        return axes_item.text(
            0.03,
            0.05,
            annotation,
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    atlas_annotation_artist = _optional_annotation(atlas_axes, "atlas_annotation")
    spatial_annotation_artist = _optional_annotation(spatial_axes, "spatial_annotation")
    trajectory_annotation_artist = _optional_annotation(trajectory_axes, "trajectory_annotation")
    support_annotation_artist = _optional_annotation(support_axes, "support_annotation")

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.08,
        right=0.90,
        top=max(0.70, title_top) if show_figure_title else 0.88,
        bottom=0.20,
        wspace=0.32,
        hspace=0.38,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.06, 0.02),
        ncol=min(4, max(1, len(state_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=support_axes, fraction=0.034, pad=0.03)
    colorbar.set_label(
        support_scale_label,
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

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
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_panel_label(axes_item=atlas_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=spatial_axes, label="B")
    panel_label_c = _add_panel_label(axes_item=trajectory_axes, label="C")
    panel_label_d = _add_panel_label(axes_item=support_axes, label="D")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.title.get_window_extent(renderer=renderer),
            box_id="atlas_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
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
            bbox=support_axes.title.get_window_extent(renderer=renderer),
            box_id="support_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="support_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="support_y_axis_title",
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
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_d.get_window_extent(renderer=renderer),
            box_id="panel_label_D",
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
    if atlas_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=atlas_annotation_artist.get_window_extent(renderer=renderer),
                box_id="atlas_annotation",
                box_type="annotation_text",
            )
        )
    if spatial_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=spatial_annotation_artist.get_window_extent(renderer=renderer),
                box_id="spatial_annotation",
                box_type="annotation_text",
            )
        )
    if trajectory_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=trajectory_annotation_artist.get_window_extent(renderer=renderer),
                box_id="trajectory_annotation",
                box_type="annotation_text",
            )
        )
    if support_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_annotation_artist.get_window_extent(renderer=renderer),
                box_id="support_annotation",
                box_type="annotation_text",
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.get_window_extent(renderer=renderer),
            box_id="panel_atlas",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.get_window_extent(renderer=renderer),
            box_id="panel_spatial",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.get_window_extent(renderer=renderer),
            box_id="panel_trajectory",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.get_window_extent(renderer=renderer),
            box_id="panel_support",
            box_type="heatmap_tile_region",
        ),
    ]

    def _normalize_scatter_points(axes_item: Any, points: list[dict[str, Any]], extra_keys: tuple[str, ...]) -> list[dict[str, Any]]:
        normalized_points: list[dict[str, Any]] = []
        for item in points:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(item["x"]),
                y=float(item["y"]),
            )
            normalized_point = {
                "x": point_x,
                "y": point_y,
                "state_label": str(item["state_label"]),
            }
            for extra_key in extra_keys:
                if extra_key in item and str(item.get(extra_key) or "").strip():
                    normalized_point[extra_key] = item[extra_key]
            if "pseudotime" in item:
                normalized_point["pseudotime"] = float(item["pseudotime"])
            normalized_points.append(normalized_point)
        return normalized_points

    normalized_support_cells = [
        {
            "x": str(item["x"]),
            "y": str(item["y"]),
            "value": float(item["value"]),
        }
        for item in support_cells
    ]

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
                "atlas_points": _normalize_scatter_points(atlas_axes, atlas_points, ()),
                "spatial_points": _normalize_scatter_points(spatial_axes, spatial_points, ("region_label",)),
                "trajectory_points": _normalize_scatter_points(trajectory_axes, trajectory_points, ("branch_label",)),
                "state_labels": state_labels,
                "region_labels": region_labels,
                "branch_labels": branch_labels,
                "context_labels": context_labels,
                "context_kinds": context_kinds,
                "support_scale_label": support_scale_label,
                "support_cells": normalized_support_cells,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_atlas_spatial_trajectory_context_support_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    atlas_points = list(display_payload.get("atlas_points") or [])
    spatial_points = list(display_payload.get("spatial_points") or [])
    trajectory_points = list(display_payload.get("trajectory_points") or [])
    composition_groups = list(display_payload.get("composition_groups") or [])
    progression_bins = list(display_payload.get("progression_bins") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    state_order = list(display_payload.get("state_order") or [])
    branch_order = list(display_payload.get("branch_order") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    context_order = list(display_payload.get("context_order") or [])
    support_cells = list(display_payload.get("support_cells") or [])
    if (
        not atlas_points
        or not spatial_points
        or not trajectory_points
        or not composition_groups
        or not progression_bins
        or not matrix_cells
        or not state_order
        or not branch_order
        or not row_order
        or not column_order
        or not context_order
        or not support_cells
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty atlas_points, spatial_points, trajectory_points, composition_groups, "
            "progression_bins, state_order, branch_order, row_order, column_order, context_order, support_cells, and cells"
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

    state_labels = [str(item["label"]) for item in state_order]
    branch_labels = [str(item["label"]) for item in branch_order]
    row_labels = [str(item["label"]) for item in row_order]
    bin_labels = [str(item["label"]) for item in column_order]
    context_labels = [str(item["label"]) for item in context_order]
    context_kinds = [str(item["context_kind"]) for item in context_order]
    state_color_lookup = {
        label: state_palette[index % len(state_palette)] for index, label in enumerate(state_labels)
    }
    support_scale_label = str(display_payload.get("support_scale_label") or "").strip()

    fig = plt.figure(figsize=(15.0, 8.6))
    fig.patch.set_facecolor("white")
    grid = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.96], width_ratios=[1.0, 1.0, 1.0])
    atlas_axes = fig.add_subplot(grid[0, 0])
    spatial_axes = fig.add_subplot(grid[0, 1])
    trajectory_axes = fig.add_subplot(grid[0, 2])
    composition_axes = fig.add_subplot(grid[1, 0])
    heatmap_axes = fig.add_subplot(grid[1, 1])
    support_axes = fig.add_subplot(grid[1, 2])

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

    def _plot_state_scatter(axes_item: Any, points: list[dict[str, Any]]) -> None:
        for state_label in state_labels:
            filtered_points = [item for item in points if str(item["state_label"]) == state_label]
            if not filtered_points:
                continue
            axes_item.scatter(
                [float(item["x"]) for item in filtered_points],
                [float(item["y"]) for item in filtered_points],
                label=state_label,
                s=36,
                alpha=0.92,
                color=state_color_lookup[state_label],
                edgecolors="white",
                linewidths=0.4,
            )

    _plot_state_scatter(atlas_axes, atlas_points)
    atlas_axes.set_title(
        str(display_payload.get("atlas_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_xlabel(
        str(display_payload.get("atlas_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_ylabel(
        str(display_payload.get("atlas_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    atlas_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(atlas_axes)

    _plot_state_scatter(spatial_axes, spatial_points)
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

    for branch_label in branch_labels:
        branch_points = sorted(
            [item for item in trajectory_points if str(item["branch_label"]) == branch_label],
            key=lambda item: float(item["pseudotime"]),
        )
        if len(branch_points) >= 2:
            trajectory_axes.plot(
                [float(item["x"]) for item in branch_points],
                [float(item["y"]) for item in branch_points],
                color=neutral_color,
                linewidth=1.4,
                alpha=0.45,
            )
    _plot_state_scatter(trajectory_axes, trajectory_points)
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
            height=0.60,
            color=matplotlib.colors.to_rgba(state_color_lookup[state_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
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
    heatmap_axes.set_xticklabels(bin_labels, fontsize=tick_size, rotation=18, ha="right", color=neutral_color)
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

    support_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in support_cells}
    support_matrix = [[support_lookup[(context_label, state_label)] for context_label in context_labels] for state_label in state_labels]
    support_axes.imshow(support_matrix, aspect="auto", cmap="Blues", vmin=0.0, vmax=1.0)
    support_axes.set_title(
        str(display_payload.get("support_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_xlabel(
        str(display_payload.get("support_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_ylabel(
        str(display_payload.get("support_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_xticks(range(len(context_labels)))
    support_axes.set_xticklabels(context_labels, fontsize=tick_size, rotation=18, ha="right", color=neutral_color)
    support_axes.set_yticks(range(len(state_labels)))
    support_axes.set_yticklabels(state_labels, fontsize=tick_size, color=neutral_color)
    support_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(support_axes)
    for row_index, state_label in enumerate(state_labels):
        for column_index, context_label in enumerate(context_labels):
            value = support_lookup[(context_label, state_label)]
            support_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )
    support_scale_artist = support_axes.text(
        0.02,
        1.03,
        support_scale_label,
        transform=support_axes.transAxes,
        fontsize=max(tick_size - 0.8, 8.4),
        color=neutral_color,
        ha="left",
        va="bottom",
    )

    def _optional_annotation(axes_item: Any, key: str) -> Any:
        annotation = str(display_payload.get(key) or "").strip()
        if not annotation:
            return None
        return axes_item.text(
            0.03,
            0.05,
            annotation,
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    atlas_annotation_artist = _optional_annotation(atlas_axes, "atlas_annotation")
    spatial_annotation_artist = _optional_annotation(spatial_axes, "spatial_annotation")
    trajectory_annotation_artist = _optional_annotation(trajectory_axes, "trajectory_annotation")
    composition_annotation_artist = _optional_annotation(composition_axes, "composition_annotation")
    heatmap_annotation_artist = _optional_annotation(heatmap_axes, "heatmap_annotation")
    support_annotation_artist = _optional_annotation(support_axes, "support_annotation")

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.12,
        right=0.95,
        top=max(0.70, title_top) if show_figure_title else 0.88,
        bottom=0.20,
        wspace=0.34,
        hspace=0.42,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.06, 0.02),
        ncol=min(4, max(1, len(state_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=heatmap_axes, fraction=0.046, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

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
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_panel_label(axes_item=atlas_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=spatial_axes, label="B")
    panel_label_c = _add_panel_label(axes_item=trajectory_axes, label="C")
    panel_label_d = _add_panel_label(axes_item=composition_axes, label="D")
    panel_label_e = _add_panel_label(axes_item=heatmap_axes, label="E")
    panel_label_f = _add_panel_label(axes_item=support_axes, label="F")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.title.get_window_extent(renderer=renderer),
            box_id="atlas_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
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
            bbox=support_axes.title.get_window_extent(renderer=renderer),
            box_id="support_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="support_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="support_y_axis_title",
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
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_d.get_window_extent(renderer=renderer),
            box_id="panel_label_D",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_e.get_window_extent(renderer=renderer),
            box_id="panel_label_E",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_f.get_window_extent(renderer=renderer),
            box_id="panel_label_F",
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
    if atlas_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=atlas_annotation_artist.get_window_extent(renderer=renderer),
                box_id="atlas_annotation",
                box_type="annotation_text",
            )
        )
    if spatial_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=spatial_annotation_artist.get_window_extent(renderer=renderer),
                box_id="spatial_annotation",
                box_type="annotation_text",
            )
        )
    if trajectory_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=trajectory_annotation_artist.get_window_extent(renderer=renderer),
                box_id="trajectory_annotation",
                box_type="annotation_text",
            )
        )
    if composition_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=composition_annotation_artist.get_window_extent(renderer=renderer),
                box_id="composition_annotation",
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
    if support_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_annotation_artist.get_window_extent(renderer=renderer),
                box_id="support_annotation",
                box_type="annotation_text",
            )
        )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_scale_artist.get_window_extent(renderer=renderer),
            box_id="support_scale_label",
            box_type="annotation_text",
        )
    )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.get_window_extent(renderer=renderer),
            box_id="panel_atlas",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.get_window_extent(renderer=renderer),
            box_id="panel_spatial",
            box_type="panel",
        ),
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
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.get_window_extent(renderer=renderer),
            box_id="panel_support",
            box_type="heatmap_tile_region",
        ),
    ]

    def _normalize_scatter_points(axes_item: Any, points: list[dict[str, Any]], extra_keys: tuple[str, ...]) -> list[dict[str, Any]]:
        normalized_points: list[dict[str, Any]] = []
        for item in points:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(item["x"]),
                y=float(item["y"]),
            )
            normalized_point = {
                "x": point_x,
                "y": point_y,
                "state_label": str(item["state_label"]),
            }
            for extra_key in extra_keys:
                if extra_key in item and str(item.get(extra_key) or "").strip():
                    normalized_point[extra_key] = item[extra_key]
            if "pseudotime" in item:
                normalized_point["pseudotime"] = float(item["pseudotime"])
            normalized_points.append(normalized_point)
        return normalized_points

    ordered_progression_bins = sorted(progression_bins, key=lambda item: int(item["bin_order"]))
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

    normalized_composition_groups: list[dict[str, Any]] = []
    for composition_group in ordered_composition_groups:
        normalized_composition_groups.append(
            {
                "group_label": str(composition_group["group_label"]),
                "group_order": int(composition_group["group_order"]),
                "state_proportions": [
                    {
                        "state_label": str(item["state_label"]),
                        "proportion": float(item["proportion"]),
                    }
                    for item in list(composition_group.get("state_proportions") or [])
                ],
            }
        )

    normalized_support_cells = [
        {
            "x": str(item["x"]),
            "y": str(item["y"]),
            "value": float(item["value"]),
        }
        for item in support_cells
    ]

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
                "atlas_points": _normalize_scatter_points(atlas_axes, atlas_points, ()),
                "spatial_points": _normalize_scatter_points(spatial_axes, spatial_points, ("region_label",)),
                "trajectory_points": _normalize_scatter_points(
                    trajectory_axes,
                    trajectory_points,
                    ("branch_label",),
                ),
                "state_labels": state_labels,
                "branch_labels": branch_labels,
                "bin_labels": bin_labels,
                "row_labels": row_labels,
                "context_labels": context_labels,
                "context_kinds": context_kinds,
                "composition_groups": normalized_composition_groups,
                "progression_bins": normalized_progression_bins,
                "matrix_cells": matrix_cells,
                "support_cells": normalized_support_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
                "support_scale_label": support_scale_label,
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
    "compact_effect_estimate_panel": _render_python_compact_effect_estimate_panel,
    "coefficient_path_panel": _render_python_coefficient_path_panel,
    "broader_heterogeneity_summary_panel": _render_python_broader_heterogeneity_summary_panel,
    "center_transportability_governance_summary_panel": _render_python_center_transportability_governance_summary_panel,
    "generalizability_subgroup_composite_panel": _render_python_generalizability_subgroup_composite_panel,
    "model_complexity_audit_panel": _render_python_model_complexity_audit_panel,
    "single_cell_atlas_overview_panel": _render_python_single_cell_atlas_overview_panel,
    "pathway_enrichment_dotplot_panel": _render_python_pathway_enrichment_dotplot_panel,
    "oncoplot_mutation_landscape_panel": _render_python_oncoplot_mutation_landscape_panel,
    "cnv_recurrence_summary_panel": _render_python_cnv_recurrence_summary_panel,
    "genomic_alteration_landscape_panel": _render_python_genomic_alteration_landscape_panel,
    "genomic_alteration_consequence_panel": _render_python_genomic_alteration_consequence_panel,
    "omics_volcano_panel": _render_python_omics_volcano_panel,
    "atlas_spatial_bridge_panel": _render_python_atlas_spatial_bridge_panel,
    "spatial_niche_map_panel": _render_python_spatial_niche_map_panel,
    "trajectory_progression_panel": _render_python_trajectory_progression_panel,
    "atlas_spatial_trajectory_storyboard_panel": _render_python_atlas_spatial_trajectory_storyboard_panel,
    "atlas_spatial_trajectory_density_coverage_panel": _render_python_atlas_spatial_trajectory_density_coverage_panel,
    "atlas_spatial_trajectory_context_support_panel": _render_python_atlas_spatial_trajectory_context_support_panel,
    "risk_layering_monotonic_bars": _render_python_risk_layering_monotonic_bars,
    "shap_dependence_panel": _render_python_shap_dependence_panel,
    "shap_summary_beeswarm": _render_python_shap_summary_beeswarm,
    "shap_bar_importance": _render_python_shap_bar_importance,
    "shap_signed_importance_panel": _render_python_shap_signed_importance_panel,
    "shap_multicohort_importance_panel": _render_python_shap_multicohort_importance_panel,
    "shap_force_like_summary_panel": _render_python_shap_force_like_summary_panel,
    "shap_grouped_local_explanation_panel": _render_python_shap_grouped_local_explanation_panel,
    "shap_grouped_decision_path_panel": _render_python_shap_grouped_decision_path_panel,
    "shap_multigroup_decision_path_panel": _render_python_shap_multigroup_decision_path_panel,
    "partial_dependence_ice_panel": _render_python_partial_dependence_ice_panel,
    "partial_dependence_interaction_contour_panel": _render_python_partial_dependence_interaction_contour_panel,
    "partial_dependence_interaction_slice_panel": _render_python_partial_dependence_interaction_slice_panel,
    "partial_dependence_subgroup_comparison_panel": _render_python_partial_dependence_subgroup_comparison_panel,
    "accumulated_local_effects_panel": _render_python_accumulated_local_effects_panel,
    "feature_response_support_domain_panel": _render_python_feature_response_support_domain_panel,
    "shap_grouped_local_support_domain_panel": _render_python_shap_grouped_local_support_domain_panel,
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
