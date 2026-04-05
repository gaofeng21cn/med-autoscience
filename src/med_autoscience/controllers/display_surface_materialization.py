from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import html
import json
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402

from med_autoscience import display_layout_qc, display_registry, publication_display_contract  # noqa: E402


_INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "binary_prediction_curve_inputs_v1": "binary_prediction_curve_inputs.json",
    "time_to_event_grouped_inputs_v1": "time_to_event_grouped_inputs.json",
    "time_to_event_discrimination_calibration_inputs_v1": "time_to_event_discrimination_calibration_inputs.json",
    "time_to_event_decision_curve_inputs_v1": "time_to_event_decision_curve_inputs.json",
    "risk_layering_monotonic_inputs_v1": "risk_layering_monotonic_inputs.json",
    "binary_calibration_decision_curve_panel_inputs_v1": "binary_calibration_decision_curve_panel_inputs.json",
    "model_complexity_audit_panel_inputs_v1": "model_complexity_audit_panel_inputs.json",
    "embedding_grouped_inputs_v1": "embedding_grouped_inputs.json",
    "heatmap_group_comparison_inputs_v1": "heatmap_group_comparison_inputs.json",
    "correlation_heatmap_inputs_v1": "correlation_heatmap_inputs.json",
    "clustered_heatmap_inputs_v1": "clustered_heatmap_inputs.json",
    "forest_effect_inputs_v1": "forest_effect_inputs.json",
    "shap_summary_inputs_v1": "shap_summary_inputs.json",
    "multicenter_generalizability_inputs_v1": "multicenter_generalizability_inputs.json",
}

_TABLE_INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "baseline_characteristics_schema_v1": "baseline_characteristics_schema.json",
    "time_to_event_performance_summary_v1": "time_to_event_performance_summary.json",
    "clinical_interpretation_summary_v1": "clinical_interpretation_summary.json",
    "performance_summary_table_generic_v1": "performance_summary_table_generic.json",
    "grouped_risk_event_summary_table_v1": "grouped_risk_event_summary_table.json",
}

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
    time_dependent_roc_horizon = list(series = display_payload$series, reference_line = display_payload$reference_line),
    kaplan_meier_grouped = list(groups = display_payload$groups),
    cumulative_incidence_grouped = list(groups = display_payload$groups),
    umap_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    pca_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    tsne_scatter_grouped = build_embedding_metrics(display_payload, panel_box),
    heatmap_group_comparison = list(metric_scope = "heatmap_group_comparison"),
    correlation_heatmap = list(matrix_cells = display_payload$cells),
    clustered_heatmap = list(matrix_cells = display_payload$cells),
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
    if (template_id %in% c("heatmap_group_comparison", "correlation_heatmap", "clustered_heatmap")) "heatmap_tile_region" else "panel"
  )
  guide_box <- find_layout_box(
    gt,
    widths,
    heights,
    c("guide-box"),
    if (template_id %in% c("heatmap_group_comparison", "correlation_heatmap", "clustered_heatmap")) "colorbar" else "legend",
    if (template_id %in% c("heatmap_group_comparison", "correlation_heatmap", "clustered_heatmap")) "colorbar" else "legend"
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
  correlation_heatmap = plot_heatmap(payload),
  clustered_heatmap = plot_heatmap(payload),
  forest_effect_main = plot_forest(payload),
  subgroup_forest = plot_forest(payload),
  stop(sprintf("unsupported evidence template `%s`", template_id))
)

layout_sidecar <- build_layout_sidecar(plot, template_id, payload)
write_json(layout_sidecar, output_layout, auto_unbox = TRUE, pretty = TRUE, null = "null")

ggsave(output_png, plot = plot, width = 7.2, height = 5.0, dpi = 320, units = "in", bg = "white")
ggsave(output_pdf, plot = plot, width = 7.2, height = 5.0, units = "in", bg = "white")
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _paper_relative_path(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.parent.resolve()).as_posix()


def _build_render_context(
    *,
    style_profile: publication_display_contract.PublicationStyleProfile,
    display_overrides: dict[tuple[str, str], publication_display_contract.DisplayOverride],
    display_id: str,
    template_id: str,
) -> dict[str, Any]:
    override = display_overrides.get((display_id, template_id))
    return {
        "style_profile_id": style_profile.style_profile_id,
        "palette": dict(style_profile.palette),
        "typography": dict(style_profile.typography),
        "stroke": dict(style_profile.stroke),
        "style_roles": publication_display_contract.resolve_style_roles(
            style_profile=style_profile,
            template_id=template_id,
        ),
        "layout_override": dict(override.layout_override) if override is not None else {},
        "readability_override": dict(override.readability_override) if override is not None else {},
    }


def _read_bool_override(mapping: dict[str, Any], key: str, default: bool) -> bool:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    return default


def _normalize_figure_catalog_id(raw_id: str) -> str:
    item = str(raw_id).strip()
    supplementary_match = re.fullmatch(r"SupplementaryFigureS(\d+)", item, flags=re.IGNORECASE)
    if supplementary_match:
        return f"FS{int(supplementary_match.group(1))}"
    supplementary_short_match = re.fullmatch(r"FS(\d+)", item, flags=re.IGNORECASE)
    if supplementary_short_match:
        return f"FS{int(supplementary_short_match.group(1))}"
    match = re.fullmatch(r"F(?:igure)?(\d+)([A-Z]?)", item, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported figure catalog_id `{raw_id}`")
    panel_suffix = str(match.group(2) or "").upper()
    return f"F{int(match.group(1))}{panel_suffix}"


def _normalize_table_catalog_id(raw_id: str) -> str:
    item = str(raw_id).strip()
    appendix_match = re.fullmatch(r"AppendixTable(\d+)", item, flags=re.IGNORECASE)
    if appendix_match:
        return f"TA{int(appendix_match.group(1))}"
    appendix_short_match = re.fullmatch(r"TA(\d+)", item, flags=re.IGNORECASE)
    if appendix_short_match:
        return f"TA{int(appendix_short_match.group(1))}"
    match = re.fullmatch(r"T(?:able)?(\d+)", item, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported table catalog_id `{raw_id}`")
    return f"T{int(match.group(1))}"


def _resolve_figure_catalog_id(*, display_id: str, catalog_id: str | None = None) -> str:
    if str(catalog_id or "").strip():
        return _normalize_figure_catalog_id(str(catalog_id))
    return _normalize_figure_catalog_id(str(display_id))


def _resolve_table_catalog_id(*, display_id: str, catalog_id: str | None = None) -> str:
    if str(catalog_id or "").strip():
        return _normalize_table_catalog_id(str(catalog_id))
    return _normalize_table_catalog_id(str(display_id))


def _replace_catalog_entry(items: list[dict[str, Any]], *, key: str, value: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
    updated = [item for item in items if str(item.get(key) or "").strip() != value]
    updated.append(entry)
    return updated


def _require_non_empty_string(value: object, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{label} must be non-empty")
    return normalized


def _require_numeric_list(value: object, *, label: str, min_length: int = 2) -> list[float]:
    if not isinstance(value, list) or len(value) < min_length:
        raise ValueError(f"{label} must contain at least {min_length} numeric values")
    normalized: list[float] = []
    for index, item in enumerate(value):
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            raise ValueError(f"{label}[{index}] must be numeric")
        normalized.append(float(item))
    return normalized


def _require_numeric_value(value: object, *, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _require_non_negative_int(value: object, *, label: str, allow_zero: bool = True) -> int:
    numeric_value = _require_numeric_value(value, label=label)
    if not float(numeric_value).is_integer():
        raise ValueError(f"{label} must be an integer")
    normalized = int(numeric_value)
    if normalized < 0 or (normalized == 0 and not allow_zero):
        comparator = ">= 1" if not allow_zero else ">= 0"
        raise ValueError(f"{label} must be {comparator}")
    return normalized


_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}


def _validate_cohort_flow_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{path.name} must contain a non-empty steps list")
    normalized_steps: list[dict[str, Any]] = []
    step_ids: set[str] = set()
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"{path.name} steps[{index}] must be an object")
        step_id = str(step.get("step_id") or "").strip()
        label = str(step.get("label") or "").strip()
        detail = str(step.get("detail") or "").strip()
        if not step_id or not label:
            raise ValueError(f"{path.name} steps[{index}] must include step_id and label")
        if step_id in step_ids:
            raise ValueError(f"{path.name} steps[{index}].step_id must be unique")
        step_ids.add(step_id)
        raw_n = step.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} steps[{index}].n must be an integer")
        normalized_steps.append({"step_id": step_id, "label": label, "detail": detail, "n": raw_n})

    exclusions_payload = payload.get("exclusions")
    if exclusions_payload is None:
        exclusions_payload = payload.get("exclusion_branches") or []
    if not isinstance(exclusions_payload, list):
        raise ValueError(f"{path.name} exclusions must be a list when provided")
    normalized_exclusions: list[dict[str, Any]] = []
    exclusion_branch_ids: set[str] = set()
    for index, branch in enumerate(exclusions_payload):
        if not isinstance(branch, dict):
            raise ValueError(f"{path.name} exclusions[{index}] must be an object")
        branch_id = str(branch.get("exclusion_id") or branch.get("branch_id") or "").strip()
        from_step_id = str(branch.get("from_step_id") or "").strip()
        label = str(branch.get("label") or "").strip()
        detail = str(branch.get("detail") or "").strip()
        if not branch_id or not from_step_id or not label:
            raise ValueError(
                f"{path.name} exclusions[{index}] must include exclusion_id/branch_id, from_step_id, and label"
            )
        if branch_id in exclusion_branch_ids:
            raise ValueError(f"{path.name} exclusions[{index}].exclusion_id must be unique")
        if from_step_id not in step_ids:
            raise ValueError(f"{path.name} exclusions[{index}].from_step_id must reference a declared step")
        raw_n = branch.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} exclusions[{index}].n must be an integer")
        exclusion_branch_ids.add(branch_id)
        normalized_exclusions.append(
            {
                "exclusion_id": branch_id,
                "from_step_id": from_step_id,
                "label": label,
                "detail": detail,
                "n": raw_n,
            }
        )

    endpoint_inventory_payload = payload.get("endpoint_inventory") or []
    if not isinstance(endpoint_inventory_payload, list):
        raise ValueError(f"{path.name} endpoint_inventory must be a list when provided")
    normalized_endpoint_inventory: list[dict[str, Any]] = []
    endpoint_ids: set[str] = set()
    for index, endpoint in enumerate(endpoint_inventory_payload):
        if not isinstance(endpoint, dict):
            raise ValueError(f"{path.name} endpoint_inventory[{index}] must be an object")
        endpoint_id = str(endpoint.get("endpoint_id") or "").strip()
        label = str(endpoint.get("label") or "").strip()
        detail = str(endpoint.get("detail") or "").strip()
        if not endpoint_id or not label:
            raise ValueError(f"{path.name} endpoint_inventory[{index}] must include endpoint_id and label")
        if endpoint_id in endpoint_ids:
            raise ValueError(f"{path.name} endpoint_inventory[{index}].endpoint_id must be unique")
        raw_n = endpoint.get("n")
        if raw_n is None:
            raw_n = endpoint.get("event_n")
        if raw_n is not None and not isinstance(raw_n, int):
            raise ValueError(f"{path.name} endpoint_inventory[{index}].n must be an integer when provided")
        endpoint_ids.add(endpoint_id)
        normalized_endpoint_inventory.append(
            {
                "endpoint_id": endpoint_id,
                "label": label,
                "detail": detail,
                "n": raw_n,
            }
        )

    design_panels_payload = payload.get("design_panels")
    if design_panels_payload is None:
        design_panels_payload = payload.get("sidecar_blocks") or []
    if not isinstance(design_panels_payload, list):
        raise ValueError(f"{path.name} design_panels must be a list when provided")
    normalized_design_panels: list[dict[str, Any]] = []
    sidecar_block_ids: set[str] = set()
    for index, block in enumerate(design_panels_payload):
        if not isinstance(block, dict):
            raise ValueError(f"{path.name} design_panels[{index}] must be an object")
        block_id = str(block.get("panel_id") or block.get("block_id") or "").strip()
        raw_block_type = str(block.get("layout_role") or block.get("block_type") or "").strip()
        block_type = _COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES.get(raw_block_type, raw_block_type)
        style_role = str(block.get("style_role") or "secondary").strip().lower()
        title = str(block.get("title") or "").strip()
        items = block.get("lines")
        if items is None:
            items = block.get("items")
        if not block_id or not block_type or not title:
            raise ValueError(f"{path.name} design_panels[{index}] must include panel_id/block_id, layout_role/block_type, and title")
        if style_role not in {"primary", "secondary", "context", "audit"}:
            raise ValueError(
                f"{path.name} design_panels[{index}].style_role must be one of primary, secondary, context, audit"
            )
        if block_id in sidecar_block_ids:
            raise ValueError(f"{path.name} design_panels[{index}].panel_id must be unique")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{path.name} design_panels[{index}].lines/items must be a non-empty list")
        normalized_items: list[dict[str, Any]] = []
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"{path.name} design_panels[{index}].lines[{item_index}] must be an object")
            label = str(item.get("label") or "").strip()
            detail = str(item.get("detail") or "").strip()
            if not label:
                raise ValueError(f"{path.name} design_panels[{index}].lines[{item_index}].label must be non-empty")
            normalized_items.append({"label": label, "detail": detail})
        sidecar_block_ids.add(block_id)
        normalized_design_panels.append(
            {
                "panel_id": block_id,
                "layout_role": block_type,
                "style_role": style_role,
                "title": title,
                "lines": normalized_items,
            }
        )

    return {
        "display_id": str(payload.get("display_id") or "").strip(),
        "title": str(payload.get("title") or "").strip(),
        "caption": str(payload.get("caption") or "").strip(),
        "steps": normalized_steps,
        "exclusions": normalized_exclusions,
        "endpoint_inventory": normalized_endpoint_inventory,
        "design_panels": normalized_design_panels,
    }


def _validate_baseline_table_payload(path: Path, payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"{path.name} must contain a non-empty groups list")
    group_labels: list[str] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"{path.name} groups[{index}] must be an object")
        label = str(group.get("label") or "").strip()
        if not label:
            raise ValueError(f"{path.name} groups[{index}] must include label")
        group_labels.append(label)

    variables = payload.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ValueError(f"{path.name} must contain a non-empty variables list")
    normalized_rows: list[dict[str, Any]] = []
    for index, variable in enumerate(variables):
        if not isinstance(variable, dict):
            raise ValueError(f"{path.name} variables[{index}] must be an object")
        label = str(variable.get("label") or "").strip()
        values = variable.get("values")
        if not label or not isinstance(values, list) or len(values) != len(group_labels):
            raise ValueError(
                f"{path.name} variables[{index}] must include label and values matching the number of groups"
            )
        normalized_rows.append({"label": label, "values": [str(item).strip() for item in values]})
    return group_labels, normalized_rows


def _validate_column_table_payload(path: Path, payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    columns = payload.get("columns")
    if not isinstance(columns, list) or not columns:
        raise ValueError(f"{path.name} must contain a non-empty columns list")
    column_labels: list[str] = []
    for index, column in enumerate(columns):
        if not isinstance(column, dict):
            raise ValueError(f"{path.name} columns[{index}] must be an object")
        column_labels.append(
            _require_non_empty_string(column.get("label"), label=f"{path.name} columns[{index}].label")
        )

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} rows[{index}] must be an object")
        label = _require_non_empty_string(row.get("label"), label=f"{path.name} rows[{index}].label")
        values = row.get("values")
        if not isinstance(values, list) or len(values) != len(column_labels):
            raise ValueError(
                f"{path.name} rows[{index}] must include values matching the number of columns"
            )
        normalized_rows.append({"label": label, "values": [str(item).strip() for item in values]})
    return column_labels, normalized_rows


def _format_percent_1dp(*, numerator: int, denominator: int) -> str:
    percent = (Decimal(numerator) * Decimal("100")) / Decimal(denominator)
    return f"{percent.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"


def _validate_performance_summary_table_generic_payload(
    path: Path,
    payload: dict[str, Any],
) -> tuple[str, list[str], list[dict[str, Any]]]:
    row_header_label = _require_non_empty_string(
        payload.get("row_header_label"),
        label=f"{path.name} row_header_label",
    )
    column_labels, rows = _validate_column_table_payload(path, payload)
    return row_header_label, column_labels, rows


def _validate_grouped_risk_event_summary_table_payload(
    path: Path,
    payload: dict[str, Any],
) -> tuple[list[str], list[list[str]]]:
    headers = [
        _require_non_empty_string(payload.get("surface_column_label"), label=f"{path.name} surface_column_label"),
        _require_non_empty_string(payload.get("stratum_column_label"), label=f"{path.name} stratum_column_label"),
        _require_non_empty_string(payload.get("cases_column_label"), label=f"{path.name} cases_column_label"),
        _require_non_empty_string(payload.get("events_column_label"), label=f"{path.name} events_column_label"),
        _require_non_empty_string(payload.get("risk_column_label"), label=f"{path.name} risk_column_label"),
    ]
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain a non-empty rows list")
    normalized_rows: list[list[str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} rows[{index}] must be an object")
        surface = _require_non_empty_string(row.get("surface"), label=f"{path.name} rows[{index}].surface")
        stratum = _require_non_empty_string(row.get("stratum"), label=f"{path.name} rows[{index}].stratum")
        cases = _require_non_negative_int(row.get("cases"), label=f"{path.name} rows[{index}].cases", allow_zero=False)
        events = _require_non_negative_int(row.get("events"), label=f"{path.name} rows[{index}].events")
        if events > cases:
            raise ValueError(f"{path.name} rows[{index}].events must not exceed cases")
        risk_display = _require_non_empty_string(
            row.get("risk_display"),
            label=f"{path.name} rows[{index}].risk_display",
        )
        expected_risk_display = _format_percent_1dp(numerator=events, denominator=cases)
        if risk_display != expected_risk_display:
            raise ValueError(
                f"{path.name} rows[{index}].risk_display must equal {expected_risk_display} for {events}/{cases}"
            )
        normalized_rows.append([surface, stratum, str(cases), str(events), risk_display])
    return headers, normalized_rows


def _validate_reference_line_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> dict[str, Any] | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} {label} must be an object")
    ref_x = _require_numeric_list(payload.get("x"), label=f"{path.name} {label}.x")
    ref_y = _require_numeric_list(payload.get("y"), label=f"{path.name} {label}.y")
    if len(ref_x) != len(ref_y):
        raise ValueError(f"{path.name} {label}.x and .y must have the same length")
    return {
        "x": ref_x,
        "y": ref_y,
        "label": str(payload.get("label") or "").strip(),
    }


def _validate_axis_window_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> dict[str, float] | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} {label} must be an object")
    xmin = _require_numeric_value(payload.get("xmin"), label=f"{path.name} {label}.xmin")
    xmax = _require_numeric_value(payload.get("xmax"), label=f"{path.name} {label}.xmax")
    ymin = _require_numeric_value(payload.get("ymin"), label=f"{path.name} {label}.ymin")
    ymax = _require_numeric_value(payload.get("ymax"), label=f"{path.name} {label}.ymax")
    if xmin >= xmax:
        raise ValueError(f"{path.name} {label}.xmin must be < .xmax")
    if ymin >= ymax:
        raise ValueError(f"{path.name} {label}.ymin must be < .ymax")
    return {
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
    }


def _validate_time_to_event_decision_curve_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    panel_a_title = _require_non_empty_string(
        payload.get("panel_a_title"),
        label=f"{path.name} display `{expected_display_id}` panel_a_title",
    )
    panel_b_title = _require_non_empty_string(
        payload.get("panel_b_title"),
        label=f"{path.name} display `{expected_display_id}` panel_b_title",
    )
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    treated_fraction_y_label = _require_non_empty_string(
        payload.get("treated_fraction_y_label"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_y_label",
    )
    series_payload = payload.get("series")
    if not isinstance(series_payload, list) or not series_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty series list")
    normalized_series: list[dict[str, Any]] = []
    for index, item in enumerate(series_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` series[{index}] must be an object")
        label = _require_non_empty_string(
            item.get("label"), label=f"{path.name} display `{expected_display_id}` series[{index}].label"
        )
        x = _require_numeric_list(
            item.get("x"), label=f"{path.name} display `{expected_display_id}` series[{index}].x"
        )
        y = _require_numeric_list(
            item.get("y"), label=f"{path.name} display `{expected_display_id}` series[{index}].y"
        )
        if len(x) != len(y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` series[{index}].x and .y must have the same length"
            )
        normalized_series.append({"label": label, "x": x, "y": y, "annotation": str(item.get("annotation") or "").strip()})

    treated_fraction_payload = payload.get("treated_fraction_series")
    if not isinstance(treated_fraction_payload, dict):
        raise ValueError(f"{path.name} display `{expected_display_id}` treated_fraction_series must be an object")
    treated_fraction_label = _require_non_empty_string(
        treated_fraction_payload.get("label"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_series.label",
    )
    treated_fraction_x = _require_numeric_list(
        treated_fraction_payload.get("x"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_series.x",
    )
    treated_fraction_y = _require_numeric_list(
        treated_fraction_payload.get("y"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_series.y",
    )
    if len(treated_fraction_x) != len(treated_fraction_y):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` treated_fraction_series.x and .y must have the same length"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_a_title": panel_a_title,
        "panel_b_title": panel_b_title,
        "x_label": x_label,
        "y_label": y_label,
        "treated_fraction_y_label": treated_fraction_y_label,
        "reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("reference_line"),
            label=f"display `{expected_display_id}` reference_line",
        ),
        "series": normalized_series,
        "treated_fraction_series": {
            "label": treated_fraction_label,
            "x": treated_fraction_x,
            "y": treated_fraction_y,
        },
    }


def _evidence_payload_path(*, paper_root: Path, input_schema_id: str) -> Path:
    try:
        filename = _INPUT_FILENAME_BY_SCHEMA_ID[input_schema_id]
    except KeyError as exc:
        raise ValueError(f"unsupported evidence input schema `{input_schema_id}`") from exc
    return paper_root / filename


def _table_payload_path(*, paper_root: Path, input_schema_id: str) -> Path:
    try:
        filename = _TABLE_INPUT_FILENAME_BY_SCHEMA_ID[input_schema_id]
    except KeyError as exc:
        raise ValueError(f"unsupported table input schema `{input_schema_id}`") from exc
    return paper_root / filename


def _validate_curve_series_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_series: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        series_label = _require_non_empty_string(
            item.get("label"),
            label=f"{path.name} {label}[{index}].label",
        )
        x = _require_numeric_list(item.get("x"), label=f"{path.name} {label}[{index}].x")
        y = _require_numeric_list(item.get("y"), label=f"{path.name} {label}[{index}].y")
        if len(x) != len(y):
            raise ValueError(f"{path.name} {label}[{index}].x and .y must have the same length")
        normalized_series.append(
            {
                "label": series_label,
                "x": x,
                "y": y,
                "annotation": str(item.get("annotation") or "").strip(),
            }
        )
    return normalized_series


def _validate_single_curve_series_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} {label} must be an object")
    normalized = _validate_curve_series_payload(
        path=path,
        payload=[payload],
        label=label,
    )
    return normalized[0]


def _validate_binary_curve_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    normalized_series = _validate_curve_series_payload(
        path=path,
        payload=payload.get("series"),
        label=f"display `{expected_display_id}` series",
    )
    reference_line = payload.get("reference_line")
    normalized_reference_line: dict[str, Any] | None = None
    if reference_line is not None:
        if not isinstance(reference_line, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` reference_line must be an object")
        ref_x = _require_numeric_list(
            reference_line.get("x"),
            label=f"{path.name} display `{expected_display_id}` reference_line.x",
        )
        ref_y = _require_numeric_list(
            reference_line.get("y"),
            label=f"{path.name} display `{expected_display_id}` reference_line.y",
        )
        if len(ref_x) != len(ref_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` reference_line.x and .y must have the same length"
            )
        normalized_reference_line = {
            "x": ref_x,
            "y": ref_y,
            "label": str(reference_line.get("label") or "").strip(),
        }
    if expected_template_id == "time_to_event_decision_curve":
        return {
            "display_id": expected_display_id,
            "template_id": expected_template_id,
            "title": title,
            "caption": str(payload.get("caption") or "").strip(),
            "paper_role": str(payload.get("paper_role") or "").strip(),
            "panel_a_title": _require_non_empty_string(
                payload.get("panel_a_title"),
                label=f"{path.name} display `{expected_display_id}` panel_a_title",
            ),
            "panel_b_title": _require_non_empty_string(
                payload.get("panel_b_title"),
                label=f"{path.name} display `{expected_display_id}` panel_b_title",
            ),
            "x_label": x_label,
            "y_label": y_label,
            "treated_fraction_y_label": _require_non_empty_string(
                payload.get("treated_fraction_y_label"),
                label=f"{path.name} display `{expected_display_id}` treated_fraction_y_label",
            ),
            "reference_line": normalized_reference_line,
            "series": normalized_series,
            "treated_fraction_series": _validate_single_curve_series_payload(
                path=path,
                payload=payload.get("treated_fraction_series"),
                label=f"display `{expected_display_id}` treated_fraction_series",
            ),
        }
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "reference_line": normalized_reference_line,
        "series": normalized_series,
    }


def _validate_risk_layering_bar_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_bars: list[dict[str, Any]] = []
    previous_risk: float | None = None
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        bar_label = _require_non_empty_string(item.get("label"), label=f"{path.name} {label}[{index}].label")
        cases = _require_non_negative_int(item.get("cases"), label=f"{path.name} {label}[{index}].cases", allow_zero=False)
        events = _require_non_negative_int(item.get("events"), label=f"{path.name} {label}[{index}].events")
        if events > cases:
            raise ValueError(f"{path.name} {label}[{index}].events must not exceed .cases")
        risk = _require_numeric_value(item.get("risk"), label=f"{path.name} {label}[{index}].risk")
        if not 0.0 <= risk <= 1.0:
            raise ValueError(f"{path.name} {label}[{index}].risk must lie within [0, 1]")
        expected_risk = float(events) / float(cases)
        if abs(risk - expected_risk) > 1e-3:
            raise ValueError(
                f"{path.name} {label}[{index}].risk must match events/cases within tolerance 1e-3"
            )
        if previous_risk is not None and risk < previous_risk:
            raise ValueError(f"{path.name} {label}[{index}].risk must be monotonic non-decreasing")
        previous_risk = risk
        normalized_bars.append(
            {
                "label": bar_label,
                "cases": cases,
                "events": events,
                "risk": risk,
            }
        )
    return normalized_bars


def _validate_risk_layering_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(
            payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` title",
        ),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": _require_non_empty_string(
            payload.get("y_label"),
            label=f"{path.name} display `{expected_display_id}` y_label",
        ),
        "left_panel_title": _require_non_empty_string(
            payload.get("left_panel_title"),
            label=f"{path.name} display `{expected_display_id}` left_panel_title",
        ),
        "left_x_label": _require_non_empty_string(
            payload.get("left_x_label"),
            label=f"{path.name} display `{expected_display_id}` left_x_label",
        ),
        "left_bars": _validate_risk_layering_bar_payload(
            path=path,
            payload=payload.get("left_bars"),
            label=f"display `{expected_display_id}` left_bars",
        ),
        "right_panel_title": _require_non_empty_string(
            payload.get("right_panel_title"),
            label=f"{path.name} display `{expected_display_id}` right_panel_title",
        ),
        "right_x_label": _require_non_empty_string(
            payload.get("right_x_label"),
            label=f"{path.name} display `{expected_display_id}` right_x_label",
        ),
        "right_bars": _validate_risk_layering_bar_payload(
            path=path,
            payload=payload.get("right_bars"),
            label=f"display `{expected_display_id}` right_bars",
        ),
    }


def _validate_binary_calibration_decision_curve_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    calibration_series = _validate_curve_series_payload(
        path=path,
        payload=payload.get("calibration_series"),
        label=f"display `{expected_display_id}` calibration_series",
    )
    decision_series = _validate_curve_series_payload(
        path=path,
        payload=payload.get("decision_series"),
        label=f"display `{expected_display_id}` decision_series",
    )
    decision_reference_lines = _validate_curve_series_payload(
        path=path,
        payload=payload.get("decision_reference_lines"),
        label=f"display `{expected_display_id}` decision_reference_lines",
    )
    calibration_axis_window = _validate_axis_window_payload(
        path=path,
        payload=payload.get("calibration_axis_window"),
        label=f"display `{expected_display_id}` calibration_axis_window",
    )
    decision_focus_window = payload.get("decision_focus_window")
    if not isinstance(decision_focus_window, dict):
        raise ValueError(f"{path.name} display `{expected_display_id}` decision_focus_window must be an object")
    xmin = _require_numeric_value(
        decision_focus_window.get("xmin"),
        label=f"{path.name} display `{expected_display_id}` decision_focus_window.xmin",
    )
    xmax = _require_numeric_value(
        decision_focus_window.get("xmax"),
        label=f"{path.name} display `{expected_display_id}` decision_focus_window.xmax",
    )
    if xmin >= xmax:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` decision_focus_window.xmin must be < .xmax"
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(
            payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` title",
        ),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "calibration_x_label": _require_non_empty_string(
            payload.get("calibration_x_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_x_label",
        ),
        "calibration_y_label": _require_non_empty_string(
            payload.get("calibration_y_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_y_label",
        ),
        "decision_x_label": _require_non_empty_string(
            payload.get("decision_x_label"),
            label=f"{path.name} display `{expected_display_id}` decision_x_label",
        ),
        "decision_y_label": _require_non_empty_string(
            payload.get("decision_y_label"),
            label=f"{path.name} display `{expected_display_id}` decision_y_label",
        ),
        "calibration_axis_window": calibration_axis_window,
        "calibration_reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("calibration_reference_line"),
            label=f"display `{expected_display_id}` calibration_reference_line",
        ),
        "calibration_series": calibration_series,
        "decision_series": decision_series,
        "decision_reference_lines": decision_reference_lines,
        "decision_focus_window": {"xmin": xmin, "xmax": xmax},
    }


def _validate_audit_panel_collection(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_panels: list[dict[str, Any]] = []
    panel_ids: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        panel_id = _require_non_empty_string(item.get("panel_id"), label=f"{path.name} {label}[{index}].panel_id")
        if panel_id in panel_ids:
            raise ValueError(f"{path.name} {label}[{index}].panel_id must be unique")
        rows = item.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{path.name} {label}[{index}].rows must contain a non-empty list")
        normalized_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{path.name} {label}[{index}].rows[{row_index}] must be an object")
            normalized_rows.append(
                {
                    "label": _require_non_empty_string(
                        row.get("label"),
                        label=f"{path.name} {label}[{index}].rows[{row_index}].label",
                    ),
                    "value": _require_numeric_value(
                        row.get("value"),
                        label=f"{path.name} {label}[{index}].rows[{row_index}].value",
                    ),
                }
            )
        panel_ids.add(panel_id)
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": _require_non_empty_string(
                    item.get("panel_label"),
                    label=f"{path.name} {label}[{index}].panel_label",
                ),
                "title": _require_non_empty_string(
                    item.get("title"),
                    label=f"{path.name} {label}[{index}].title",
                ),
                "x_label": _require_non_empty_string(
                    item.get("x_label"),
                    label=f"{path.name} {label}[{index}].x_label",
                ),
                "reference_value": (
                    _require_numeric_value(
                        item.get("reference_value"),
                        label=f"{path.name} {label}[{index}].reference_value",
                    )
                    if item.get("reference_value") is not None
                    else None
                ),
                "rows": normalized_rows,
            }
        )
    return normalized_panels


def _validate_model_complexity_audit_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(
            payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` title",
        ),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_panels": _validate_audit_panel_collection(
            path=path,
            payload=payload.get("metric_panels"),
            label=f"display `{expected_display_id}` metric_panels",
        ),
        "audit_panels": _validate_audit_panel_collection(
            path=path,
            payload=payload.get("audit_panels"),
            label=f"display `{expected_display_id}` audit_panels",
        ),
    }


def _validate_time_to_event_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    if expected_template_id == "time_to_event_risk_group_summary":
        summaries_payload = payload.get("risk_group_summaries")
        if not isinstance(summaries_payload, list) or not summaries_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must contain a non-empty risk_group_summaries list"
            )
        normalized_summaries: list[dict[str, Any]] = []
        for index, item in enumerate(summaries_payload):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}] must be an object"
                )
            normalized_summaries.append(
                {
                    "label": _require_non_empty_string(
                        item.get("label"),
                        label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].label",
                    ),
                    "sample_size": _require_non_negative_int(
                        item.get("sample_size"),
                        label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].sample_size",
                        allow_zero=False,
                    ),
                    "events_5y": _require_non_negative_int(
                        item.get("events_5y"),
                        label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events_5y",
                    ),
                    "mean_predicted_risk_5y": _require_numeric_value(
                        item.get("mean_predicted_risk_5y"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"risk_group_summaries[{index}].mean_predicted_risk_5y"
                        ),
                    ),
                    "observed_km_risk_5y": _require_numeric_value(
                        item.get("observed_km_risk_5y"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"risk_group_summaries[{index}].observed_km_risk_5y"
                        ),
                    ),
                }
            )
        return {
            "display_id": expected_display_id,
            "template_id": expected_template_id,
            "title": title,
            "caption": str(payload.get("caption") or "").strip(),
            "paper_role": str(payload.get("paper_role") or "").strip(),
            "panel_a_title": _require_non_empty_string(
                payload.get("panel_a_title"),
                label=f"{path.name} display `{expected_display_id}` panel_a_title",
            ),
            "panel_b_title": _require_non_empty_string(
                payload.get("panel_b_title"),
                label=f"{path.name} display `{expected_display_id}` panel_b_title",
            ),
            "x_label": x_label,
            "y_label": y_label,
            "event_count_y_label": _require_non_empty_string(
                payload.get("event_count_y_label"),
                label=f"{path.name} display `{expected_display_id}` event_count_y_label",
            ),
            "risk_group_summaries": normalized_summaries,
        }
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty groups list")
    normalized_groups: list[dict[str, Any]] = []
    for index, item in enumerate(groups):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` groups[{index}] must be an object")
        label = _require_non_empty_string(
            item.get("label"), label=f"{path.name} display `{expected_display_id}` groups[{index}].label"
        )
        times = _require_numeric_list(
            item.get("times"), label=f"{path.name} display `{expected_display_id}` groups[{index}].times"
        )
        values = _require_numeric_list(
            item.get("values"), label=f"{path.name} display `{expected_display_id}` groups[{index}].values"
        )
        if len(times) != len(values):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{index}].times and .values must have the same length"
            )
        normalized_groups.append({"label": label, "times": times, "values": values})
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "groups": normalized_groups,
        "annotation": str(payload.get("annotation") or "").strip(),
    }


def _validate_time_to_event_discrimination_calibration_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    discrimination_x_label = _require_non_empty_string(
        payload.get("discrimination_x_label"),
        label=f"{path.name} display `{expected_display_id}` discrimination_x_label",
    )
    discrimination_y_label = _require_non_empty_string(
        payload.get("discrimination_y_label"),
        label=f"{path.name} display `{expected_display_id}` discrimination_y_label",
    )
    calibration_x_label = _require_non_empty_string(
        payload.get("calibration_x_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_x_label",
    )
    calibration_y_label = _require_non_empty_string(
        payload.get("calibration_y_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_y_label",
    )
    discrimination_series_payload = payload.get("discrimination_series")
    if not isinstance(discrimination_series_payload, list) or not discrimination_series_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty discrimination_series list"
        )
    normalized_series: list[dict[str, Any]] = []
    for index, item in enumerate(discrimination_series_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` discrimination_series[{index}] must be an object"
            )
        label = _require_non_empty_string(
            item.get("label"),
            label=f"{path.name} display `{expected_display_id}` discrimination_series[{index}].label",
        )
        x = _require_numeric_list(
            item.get("x"),
            label=f"{path.name} display `{expected_display_id}` discrimination_series[{index}].x",
        )
        y = _require_numeric_list(
            item.get("y"),
            label=f"{path.name} display `{expected_display_id}` discrimination_series[{index}].y",
        )
        if len(x) != len(y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` discrimination_series[{index}].x and .y "
                "must have the same length"
            )
        normalized_series.append(
            {
                "label": label,
                "x": x,
                "y": y,
                "annotation": str(item.get("annotation") or "").strip(),
            }
        )

    calibration_groups_payload = payload.get("calibration_groups")
    if not isinstance(calibration_groups_payload, list) or not calibration_groups_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty calibration_groups list")
    normalized_groups: list[dict[str, Any]] = []
    for index, item in enumerate(calibration_groups_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_groups[{index}] must be an object"
            )
        label = _require_non_empty_string(
            item.get("label"),
            label=f"{path.name} display `{expected_display_id}` calibration_groups[{index}].label",
        )
        times = _require_numeric_list(
            item.get("times"),
            label=f"{path.name} display `{expected_display_id}` calibration_groups[{index}].times",
        )
        values = _require_numeric_list(
            item.get("values"),
            label=f"{path.name} display `{expected_display_id}` calibration_groups[{index}].values",
        )
        if len(times) != len(values):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_groups[{index}].times and .values "
                "must have the same length"
            )
        normalized_groups.append({"label": label, "times": times, "values": values})

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "discrimination_x_label": discrimination_x_label,
        "discrimination_y_label": discrimination_y_label,
        "calibration_x_label": calibration_x_label,
        "calibration_y_label": calibration_y_label,
        "discrimination_reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("discrimination_reference_line"),
            label=f"display `{expected_display_id}` discrimination_reference_line",
        ),
        "calibration_reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("calibration_reference_line"),
            label=f"display `{expected_display_id}` calibration_reference_line",
        ),
        "discrimination_series": normalized_series,
        "calibration_groups": normalized_groups,
    }


def _validate_embedding_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty points list")
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}] must be an object")
        normalized_points.append(
            {
                "x": _require_numeric_value(item.get("x"), label=f"{path.name} display `{expected_display_id}` points[{index}].x"),
                "y": _require_numeric_value(item.get("y"), label=f"{path.name} display `{expected_display_id}` points[{index}].y"),
                "group": _require_non_empty_string(
                    item.get("group"),
                    label=f"{path.name} display `{expected_display_id}` points[{index}].group",
                ),
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "points": normalized_points,
    }


def _validate_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty cells list")
    normalized_cells: list[dict[str, Any]] = []
    for index, item in enumerate(cells):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` cells[{index}] must be an object")
        normalized_cells.append(
            {
                "x": _require_non_empty_string(item.get("x"), label=f"{path.name} display `{expected_display_id}` cells[{index}].x"),
                "y": _require_non_empty_string(item.get("y"), label=f"{path.name} display `{expected_display_id}` cells[{index}].y"),
                "value": _require_numeric_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` cells[{index}].value",
                ),
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "cells": normalized_cells,
    }


def _validate_labeled_order_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, str]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_items: list[dict[str, str]] = []
    seen_labels: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        item_label = _require_non_empty_string(item.get("label"), label=f"{path.name} {label}[{index}].label")
        if item_label in seen_labels:
            raise ValueError(f"{path.name} {label}[{index}].label must be unique")
        seen_labels.add(item_label)
        normalized_items.append({"label": item_label})
    return normalized_items


def _validate_clustered_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    row_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("row_order"),
        label=f"display `{expected_display_id}` row_order",
    )
    column_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("column_order"),
        label=f"display `{expected_display_id}` column_order",
    )
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty cells list")
    normalized_cells: list[dict[str, Any]] = []
    observed_rows: set[str] = set()
    observed_columns: set[str] = set()
    observed_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(cells):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` cells[{index}] must be an object")
        column_label = _require_non_empty_string(
            item.get("x"),
            label=f"{path.name} display `{expected_display_id}` cells[{index}].x",
        )
        row_label = _require_non_empty_string(
            item.get("y"),
            label=f"{path.name} display `{expected_display_id}` cells[{index}].y",
        )
        coordinate = (column_label, row_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        observed_columns.add(column_label)
        observed_rows.add(row_label)
        normalized_cells.append(
            {
                "x": column_label,
                "y": row_label,
                "value": _require_numeric_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` cells[{index}].value",
                ),
            }
        )

    declared_rows = {item["label"] for item in row_order}
    declared_columns = {item["label"] for item in column_order}
    if observed_rows != declared_rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` row_order labels must match cell y labels")
    if observed_columns != declared_columns:
        raise ValueError(f"{path.name} display `{expected_display_id}` column_order labels must match cell x labels")
    expected_coordinates = {(column["label"], row["label"]) for row in row_order for column in column_order}
    if observed_coordinates != expected_coordinates:
        raise ValueError(f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


def _validate_forest_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` rows[{index}] must be an object")
        estimate = _require_numeric_value(
            item.get("estimate"),
            label=f"{path.name} display `{expected_display_id}` rows[{index}].estimate",
        )
        lower = _require_numeric_value(
            item.get("lower"),
            label=f"{path.name} display `{expected_display_id}` rows[{index}].lower",
        )
        upper = _require_numeric_value(
            item.get("upper"),
            label=f"{path.name} display `{expected_display_id}` rows[{index}].upper",
        )
        if not (lower <= estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` rows[{index}] must satisfy lower <= estimate <= upper"
            )
        normalized_rows.append(
            {
                "label": _require_non_empty_string(
                    item.get("label"),
                    label=f"{path.name} display `{expected_display_id}` rows[{index}].label",
                ),
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "reference_value": _require_numeric_value(
            payload.get("reference_value", 1.0),
            label=f"{path.name} display `{expected_display_id}` reference_value",
        ),
        "rows": normalized_rows,
    }


def _validate_shap_summary_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` rows[{row_index}] must be an object")
        points = row.get("points")
        if not isinstance(points, list) or not points:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` rows[{row_index}] must contain a non-empty points list"
            )
        normalized_points: list[dict[str, Any]] = []
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` rows[{row_index}].points[{point_index}] must be an object"
                )
            normalized_points.append(
                {
                    "shap_value": _require_numeric_value(
                        point.get("shap_value"),
                        label=(
                            f"{path.name} display `{expected_display_id}` rows[{row_index}].points[{point_index}]."
                            "shap_value"
                        ),
                    ),
                    "feature_value": _require_numeric_value(
                        point.get("feature_value"),
                        label=(
                            f"{path.name} display `{expected_display_id}` rows[{row_index}].points[{point_index}]."
                            "feature_value"
                        ),
                    ),
                }
            )
        normalized_rows.append(
            {
                "feature": _require_non_empty_string(
                    row.get("feature"),
                    label=f"{path.name} display `{expected_display_id}` rows[{row_index}].feature",
                ),
                "points": normalized_points,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "rows": normalized_rows,
    }


def _validate_multicenter_generalizability_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    overview_mode = _require_non_empty_string(
        payload.get("overview_mode"),
        label=f"{path.name} display `{expected_display_id}` overview_mode",
    )
    if overview_mode != "center_support_counts":
        raise ValueError(
            f"{path.name} display `{expected_display_id}` overview_mode must equal `center_support_counts`"
        )
    center_event_y_label = _require_non_empty_string(
        payload.get("center_event_y_label"),
        label=f"{path.name} display `{expected_display_id}` center_event_y_label",
    )
    coverage_y_label = _require_non_empty_string(
        payload.get("coverage_y_label"),
        label=f"{path.name} display `{expected_display_id}` coverage_y_label",
    )
    center_event_counts_payload = payload.get("center_event_counts")
    if not isinstance(center_event_counts_payload, list) or not center_event_counts_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty center_event_counts list")
    normalized_center_event_counts: list[dict[str, Any]] = []
    for index, item in enumerate(center_event_counts_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` center_event_counts[{index}] must be an object"
            )
        split_bucket = _require_non_empty_string(
            item.get("split_bucket"),
            label=f"{path.name} display `{expected_display_id}` center_event_counts[{index}].split_bucket",
        )
        if split_bucket not in {"train", "validation"}:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` center_event_counts[{index}].split_bucket must be `train` or `validation`"
            )
        normalized_center_event_counts.append(
            {
                "center_label": _require_non_empty_string(
                    item.get("center_label"),
                    label=f"{path.name} display `{expected_display_id}` center_event_counts[{index}].center_label",
                ),
                "split_bucket": split_bucket,
                "event_count": _require_non_negative_int(
                    item.get("event_count"),
                    label=f"{path.name} display `{expected_display_id}` center_event_counts[{index}].event_count",
                ),
            }
        )

    coverage_panels_payload = payload.get("coverage_panels")
    if not isinstance(coverage_panels_payload, list) or not coverage_panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty coverage_panels list")
    normalized_coverage_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_layout_roles: set[str] = set()
    for index, panel in enumerate(coverage_panels_payload):
        if not isinstance(panel, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` coverage_panels[{index}] must be an object")
        panel_id = _require_non_empty_string(
            panel.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` coverage_panels[{index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels[{index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        layout_role = _require_non_empty_string(
            panel.get("layout_role"),
            label=f"{path.name} display `{expected_display_id}` coverage_panels[{index}].layout_role",
        )
        if layout_role not in {"wide_left", "top_right", "bottom_right"}:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels[{index}].layout_role is not supported"
            )
        if layout_role in seen_layout_roles:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels layout_role `{layout_role}` must be unique"
            )
        seen_layout_roles.add(layout_role)
        bars_payload = panel.get("bars")
        if not isinstance(bars_payload, list) or not bars_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels[{index}].bars must be a non-empty list"
            )
        normalized_bars: list[dict[str, Any]] = []
        for bar_index, bar in enumerate(bars_payload):
            if not isinstance(bar, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coverage_panels[{index}].bars[{bar_index}] must be an object"
                )
            normalized_bars.append(
                {
                    "label": _require_non_empty_string(
                        bar.get("label"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"coverage_panels[{index}].bars[{bar_index}].label"
                        ),
                    ),
                    "count": _require_non_negative_int(
                        bar.get("count"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"coverage_panels[{index}].bars[{bar_index}].count"
                        ),
                    ),
                }
            )
        normalized_coverage_panels.append(
            {
                "panel_id": panel_id,
                "title": _require_non_empty_string(
                    panel.get("title"),
                    label=f"{path.name} display `{expected_display_id}` coverage_panels[{index}].title",
                ),
                "layout_role": layout_role,
                "bars": normalized_bars,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "overview_mode": overview_mode,
        "center_event_y_label": center_event_y_label,
        "coverage_y_label": coverage_y_label,
        "center_event_counts": normalized_center_event_counts,
        "coverage_panels": normalized_coverage_panels,
    }


def _load_evidence_display_payload(
    *,
    paper_root: Path,
    spec: display_registry.EvidenceFigureSpec,
    display_id: str,
) -> tuple[Path, dict[str, Any]]:
    payload_path = _evidence_payload_path(paper_root=paper_root, input_schema_id=spec.input_schema_id)
    payload = load_json(payload_path)
    if str(payload.get("input_schema_id") or "").strip() != spec.input_schema_id:
        raise ValueError(f"{payload_path.name} must declare input_schema_id `{spec.input_schema_id}`")
    displays = payload.get("displays")
    if not isinstance(displays, list) or not displays:
        raise ValueError(f"{payload_path.name} must contain a non-empty displays list")
    matched_display: dict[str, Any] | None = None
    for index, item in enumerate(displays):
        if not isinstance(item, dict):
            raise ValueError(f"{payload_path.name} displays[{index}] must be an object")
        if str(item.get("display_id") or "").strip() == display_id:
            matched_display = item
            break
    if matched_display is None:
        raise ValueError(f"{payload_path.name} does not define display `{display_id}` for template `{spec.template_id}`")

    if spec.input_schema_id == "binary_prediction_curve_inputs_v1":
        return payload_path, _validate_binary_curve_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "risk_layering_monotonic_inputs_v1":
        return payload_path, _validate_risk_layering_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "binary_calibration_decision_curve_panel_inputs_v1":
        return payload_path, _validate_binary_calibration_decision_curve_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "model_complexity_audit_panel_inputs_v1":
        return payload_path, _validate_model_complexity_audit_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_grouped_inputs_v1":
        return payload_path, _validate_time_to_event_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_discrimination_calibration_inputs_v1":
        return payload_path, _validate_time_to_event_discrimination_calibration_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_decision_curve_inputs_v1":
        return payload_path, _validate_time_to_event_decision_curve_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "embedding_grouped_inputs_v1":
        return payload_path, _validate_embedding_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id in {"heatmap_group_comparison_inputs_v1", "correlation_heatmap_inputs_v1"}:
        return payload_path, _validate_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "clustered_heatmap_inputs_v1":
        return payload_path, _validate_clustered_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "forest_effect_inputs_v1":
        return payload_path, _validate_forest_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_summary_inputs_v1":
        return payload_path, _validate_shap_summary_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "multicenter_generalizability_inputs_v1":
        return payload_path, _validate_multicenter_generalizability_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    raise ValueError(f"unsupported evidence input schema `{spec.input_schema_id}`")


@dataclass(frozen=True)
class _FlowTextLine:
    text: str
    font_size: float
    font_weight: str
    color: str
    gap_before: float = 0.0


@dataclass(frozen=True)
class _FlowNodeSpec:
    node_id: str
    box_id: str
    box_type: str
    panel_role: str
    fill_color: str
    edge_color: str
    linewidth: float
    lines: tuple[_FlowTextLine, ...]
    width_pt: float
    padding_pt: float


@dataclass(frozen=True)
class _GraphvizNodeBox:
    node_id: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class _GraphvizLayout:
    width_pt: float
    height_pt: float
    nodes: dict[str, _GraphvizNodeBox]


def _flow_font_properties(*, font_weight: str) -> FontProperties:
    return FontProperties(family="DejaVu Sans", weight=font_weight)


def _measure_flow_text_width_pt(text: str, *, font_size: float, font_weight: str) -> float:
    if not text:
        return 0.0
    path = TextPath((0.0, 0.0), text, size=font_size, prop=_flow_font_properties(font_weight=font_weight))
    return float(path.get_extents().width)


def _wrap_flow_text_to_width(
    value: str,
    *,
    max_width_pt: float,
    font_size: float,
    font_weight: str,
) -> tuple[str, ...]:
    normalized = " ".join(str(value or "").split())
    if not normalized:
        return tuple()
    words = normalized.split(" ")
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate_words = [*current, word]
        candidate = " ".join(candidate_words)
        if current and _measure_flow_text_width_pt(candidate, font_size=font_size, font_weight=font_weight) > max_width_pt:
            lines.append(" ".join(current))
            current = [word]
            continue
        current = candidate_words
    if current:
        lines.append(" ".join(current))
    return tuple(lines)


def _wrap_figure_title_to_width(
    title: str,
    *,
    max_width_pt: float,
    font_size: float,
    font_weight: str = "bold",
) -> tuple[str, int]:
    lines = _wrap_flow_text_to_width(
        title,
        max_width_pt=max_width_pt,
        font_size=font_size,
        font_weight=font_weight,
    )
    if not lines:
        return "", 0
    return "\n".join(lines), len(lines)


def _flow_html_label_for_node(spec: _FlowNodeSpec) -> str:
    parts = [
        (
            f'<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="{int(round(spec.padding_pt))}" '
            f'COLOR="{spec.edge_color}" BGCOLOR="{spec.fill_color}" STYLE="ROUNDED" '
            f'WIDTH="{int(round(spec.width_pt))}">'
        )
    ]
    for line in spec.lines:
        if line.gap_before > 0:
            parts.append(f'<TR><TD HEIGHT="{int(round(line.gap_before))}"></TD></TR>')
        escaped_text = html.escape(line.text)
        font_attrs = [f'POINT-SIZE="{line.font_size:.2f}"', f'COLOR="{line.color}"']
        font_open = "<FONT " + " ".join(font_attrs) + ">"
        if line.font_weight == "bold":
            font_payload = f"{font_open}<B>{escaped_text}</B></FONT>"
        else:
            font_payload = f"{font_open}{escaped_text}</FONT>"
        parts.append(f"<TR><TD ALIGN=\"LEFT\">{font_payload}</TD></TR>")
    parts.append("</TABLE>")
    return "<" + "".join(parts) + ">"


def _run_graphviz_layout(*, graph_name: str, dot_source: str) -> _GraphvizLayout:
    dot_binary = shutil.which("dot")
    if dot_binary is None:
        raise RuntimeError(f"dot not found on PATH; required for `{graph_name}` graph layout")
    with tempfile.TemporaryDirectory(prefix=f"medautosci-{graph_name}-") as tmpdir:
        dot_path = Path(tmpdir) / f"{graph_name}.dot"
        json_path = Path(tmpdir) / f"{graph_name}.json"
        dot_path.write_text(dot_source, encoding="utf-8")
        completed = subprocess.run(
            [dot_binary, "-Tjson", str(dot_path), "-o", str(json_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"dot layout failed for `{graph_name}`: {stderr or 'unknown graphviz error'}")
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    bb_text = str(payload.get("bb") or "").strip()
    try:
        bb_left, bb_bottom, bb_right, bb_top = [float(item) for item in bb_text.split(",")]
    except ValueError as exc:
        raise RuntimeError(f"dot layout for `{graph_name}` returned invalid bounding box: {bb_text}") from exc
    nodes: dict[str, _GraphvizNodeBox] = {}
    for item in payload.get("objects") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        pos_text = str(item.get("pos") or "").strip()
        width_text = str(item.get("width") or "").strip()
        height_text = str(item.get("height") or "").strip()
        if not name or not pos_text or not width_text or not height_text:
            continue
        try:
            center_x, center_y = [float(part) for part in pos_text.split(",", 1)]
            width_pt = float(width_text) * 72.0
            height_pt = float(height_text) * 72.0
        except ValueError:
            continue
        nodes[name] = _GraphvizNodeBox(
            node_id=name,
            x0=center_x - width_pt / 2.0,
            y0=center_y - height_pt / 2.0,
            x1=center_x + width_pt / 2.0,
            y1=center_y + height_pt / 2.0,
        )
    return _GraphvizLayout(width_pt=bb_right - bb_left, height_pt=bb_top - bb_bottom, nodes=nodes)


def _flow_box_to_normalized(
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    canvas_width_pt: float,
    canvas_height_pt: float,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": float(min(x0, x1) / canvas_width_pt),
        "y0": float(min(y0, y1) / canvas_height_pt),
        "x1": float(max(x0, x1) / canvas_width_pt),
        "y1": float(max(y0, y1) / canvas_height_pt),
    }


def _flow_union_box(*, boxes: list[dict[str, float]], box_id: str, box_type: str) -> dict[str, float]:
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": min(item["x0"] for item in boxes),
        "y0": min(item["y0"] for item in boxes),
        "x1": max(item["x1"] for item in boxes),
        "y1": max(item["y1"] for item in boxes),
    }


def _render_cohort_flow_figure(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    title: str,
    steps: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    endpoint_inventory: list[dict[str, Any]],
    design_panels: list[dict[str, Any]],
    render_context: dict[str, Any],
) -> None:
    def read_float(mapping: dict[str, Any], key: str, default: float) -> float:
        value = mapping.get(key, default)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(default)

    def read_ratio(mapping: dict[str, Any], key: str) -> float | None:
        value = mapping.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            normalized = float(value)
            if 0.0 < normalized < 1.0:
                return normalized
        return None

    render_context_payload = dict(render_context or {})
    style_roles = dict(render_context_payload.get("style_roles") or {})
    layout_override = dict(render_context_payload.get("layout_override") or {})
    typography = dict(render_context_payload.get("typography") or {})
    stroke = dict(render_context_payload.get("stroke") or {})

    def role_color(role_name: str) -> str:
        return _require_non_empty_string(
            style_roles.get(role_name),
            label=f"cohort_flow_figure render_context.style_roles.{role_name}",
        )

    flow_main_fill = role_color("flow_main_fill")
    flow_main_edge = role_color("flow_main_edge")
    flow_exclusion_fill = role_color("flow_exclusion_fill")
    flow_exclusion_edge = role_color("flow_exclusion_edge")
    flow_primary_fill = role_color("flow_primary_fill")
    flow_primary_edge = role_color("flow_primary_edge")
    flow_secondary_fill = role_color("flow_secondary_fill")
    flow_secondary_edge = role_color("flow_secondary_edge")
    flow_context_fill = role_color("flow_context_fill")
    flow_context_edge = role_color("flow_context_edge")
    flow_audit_fill = role_color("flow_audit_fill")
    flow_audit_edge = role_color("flow_audit_edge")
    flow_title_text = role_color("flow_title_text")
    flow_body_text = role_color("flow_body_text")
    flow_panel_label = role_color("flow_panel_label")
    flow_connector = role_color("flow_connector")

    base_card_title_size = max(11.8, read_float(typography, "axis_title_size", 11.0) + 0.8)
    base_label_size = max(10.4, read_float(typography, "tick_size", 10.0) + 0.4)
    base_detail_size = max(9.5, read_float(typography, "tick_size", 10.0) - 0.5)
    base_panel_label_size = max(11.2, read_float(typography, "panel_label_size", 11.0) + 0.6)

    base_primary_linewidth = read_float(stroke, "primary_linewidth", 2.2)
    base_secondary_linewidth = read_float(stroke, "secondary_linewidth", 1.8)
    base_connector_linewidth = read_float(stroke, "reference_linewidth", 1.0)

    figure_width_pt = read_float(layout_override, "figure_width", 13.6) * 72.0
    legacy_panel_gap_ratio = read_ratio(layout_override, "panel_gap")
    legacy_card_gap_ratio = read_ratio(layout_override, "card_gap_y")

    step_width_pt = read_float(layout_override, "flow_step_width_pt", 280.0)
    exclusion_width_pt = read_float(layout_override, "flow_exclusion_width_pt", 220.0)
    wide_block_width_pt = read_float(layout_override, "hierarchy_wide_width_pt", 344.0)
    standard_block_width_pt = read_float(layout_override, "hierarchy_block_width_pt", 208.0)
    footer_block_width_pt = read_float(layout_override, "hierarchy_footer_width_pt", 316.0)
    panel_gap_pt = read_float(
        layout_override,
        "panel_gap_pt",
        figure_width_pt * legacy_panel_gap_ratio if legacy_panel_gap_ratio is not None else 36.0,
    )
    branch_gap_pt = read_float(layout_override, "flow_branch_gap_pt", 18.0)
    side_margin_pt = read_float(layout_override, "figure_side_margin_pt", 34.0)
    heading_band_pt = read_float(layout_override, "heading_band_pt", 36.0)
    bottom_margin_pt = read_float(layout_override, "bottom_margin_pt", 24.0)
    footer_gap_pt = read_float(layout_override, "footer_gap_pt", 22.0)
    flow_step_gap_pt = read_float(
        layout_override,
        "flow_step_gap_pt",
        figure_width_pt * legacy_card_gap_ratio if legacy_card_gap_ratio is not None else 26.0,
    )
    flow_exclusion_stack_gap_pt = read_float(layout_override, "flow_exclusion_stack_gap_pt", 10.0)
    flow_split_clearance_pt = read_float(layout_override, "flow_split_clearance_pt", 12.0)
    hierarchy_nodesep = read_float(layout_override, "graphviz_hierarchy_nodesep", 0.60)
    hierarchy_ranksep = read_float(layout_override, "graphviz_hierarchy_ranksep", 0.82)
    sparse_stack_gap_pt = read_float(layout_override, "hierarchy_sparse_stack_gap_pt", 18.0)
    step_padding_pt = read_float(layout_override, "flow_step_padding_pt", 9.0)
    exclusion_padding_pt = read_float(layout_override, "flow_exclusion_padding_pt", 8.0)
    hierarchy_padding_pt = read_float(layout_override, "hierarchy_panel_padding_pt", 9.0)

    modern_roles = {"wide_top", "wide_bottom", "left_middle", "right_middle", "left_bottom", "right_bottom"}
    legacy_roles = {"wide_left", "top_right", "bottom_right"}
    declared_design_panel_roles = {
        str(item.get("layout_role") or "").strip()
        for item in design_panels
        if isinstance(item, dict) and str(item.get("layout_role") or "").strip()
    }
    if declared_design_panel_roles and not (
        declared_design_panel_roles.issubset(modern_roles) or declared_design_panel_roles.issubset(legacy_roles)
    ):
        unknown_roles = ", ".join(sorted(declared_design_panel_roles))
        raise ValueError(f"cohort_flow_figure received unsupported design panel layout roles: {unknown_roles}")
    declared_modern_layout = not declared_design_panel_roles or declared_design_panel_roles.issubset(modern_roles)
    declared_left_branch = bool({"left_middle", "left_bottom"} & declared_design_panel_roles)
    declared_right_branch = bool({"right_middle", "right_bottom"} & declared_design_panel_roles)
    sparse_modern_layout = bool(
        declared_modern_layout and declared_design_panel_roles and not (declared_left_branch and declared_right_branch)
    )

    def block_colors(style_role: str) -> tuple[str, str]:
        if style_role == "primary":
            return flow_primary_fill, flow_primary_edge
        if style_role == "context":
            return flow_context_fill, flow_context_edge
        if style_role == "audit":
            return flow_audit_fill, flow_audit_edge
        return flow_secondary_fill, flow_secondary_edge

    def build_step_spec(step: dict[str, Any]) -> _FlowNodeSpec:
        content_width_pt = step_width_pt - 28.0
        title_lines = _wrap_flow_text_to_width(
            str(step["label"]),
            max_width_pt=content_width_pt,
            font_size=base_card_title_size + 0.5,
            font_weight="bold",
        )
        detail_lines = _wrap_flow_text_to_width(
            str(step.get("detail") or ""),
            max_width_pt=content_width_pt,
            font_size=base_detail_size,
            font_weight="normal",
        )
        lines = [
            *[
                _FlowTextLine(
                    text=line,
                    font_size=base_card_title_size + 0.5,
                    font_weight="bold",
                    color=flow_title_text,
                )
                for line in title_lines
            ],
            _FlowTextLine(
                text=f"n = {step['n']}",
                font_size=base_label_size,
                font_weight="normal",
                color=flow_body_text,
                gap_before=8.0,
            ),
        ]
        lines.extend(
            _FlowTextLine(
                text=line,
                font_size=base_detail_size,
                font_weight="normal",
                color=flow_body_text,
                gap_before=6.0 if index == 0 else 0.0,
            )
            for index, line in enumerate(detail_lines)
        )
        return _FlowNodeSpec(
            node_id=f"step_{step['step_id']}",
            box_id=f"step_{step['step_id']}",
            box_type="main_step",
            panel_role="flow",
            fill_color=flow_main_fill,
            edge_color=flow_main_edge,
            linewidth=base_secondary_linewidth,
            lines=tuple(lines),
            width_pt=step_width_pt,
            padding_pt=step_padding_pt,
        )

    def build_exclusion_spec(exclusion: dict[str, Any]) -> _FlowNodeSpec:
        content_width_pt = exclusion_width_pt - 24.0
        title_lines = _wrap_flow_text_to_width(
            f"{exclusion['label']} (n={exclusion['n']})",
            max_width_pt=content_width_pt,
            font_size=base_label_size,
            font_weight="bold",
        )
        detail_lines = _wrap_flow_text_to_width(
            str(exclusion.get("detail") or ""),
            max_width_pt=content_width_pt,
            font_size=base_detail_size,
            font_weight="normal",
        )
        lines = [
            *[
                _FlowTextLine(
                    text=line,
                    font_size=base_label_size,
                    font_weight="bold",
                    color=flow_exclusion_edge,
                )
                for line in title_lines
            ]
        ]
        lines.extend(
            _FlowTextLine(
                text=line,
                font_size=base_detail_size,
                font_weight="normal",
                color=flow_exclusion_edge,
                gap_before=6.0 if index == 0 else 0.0,
            )
            for index, line in enumerate(detail_lines)
        )
        return _FlowNodeSpec(
            node_id=f"exclusion_{exclusion['exclusion_id']}",
            box_id=f"exclusion_{exclusion['exclusion_id']}",
            box_type="exclusion_box",
            panel_role="flow",
            fill_color=flow_exclusion_fill,
            edge_color=flow_exclusion_edge,
            linewidth=max(1.2, base_secondary_linewidth - 0.2),
            lines=tuple(lines),
            width_pt=exclusion_width_pt,
            padding_pt=exclusion_padding_pt,
        )

    def build_design_panel_spec(block: dict[str, Any]) -> _FlowNodeSpec:
        style_role = str(block.get("style_role") or "secondary")
        panel_role = str(block["layout_role"])
        fill_color, edge_color = block_colors(style_role)
        is_wide = panel_role in {"wide_top", "wide_bottom", "wide_left", "footer_stack"}
        width_pt = wide_block_width_pt if is_wide else standard_block_width_pt
        if sparse_modern_layout and panel_role in {"left_middle", "right_middle", "left_bottom", "right_bottom"}:
            width_pt = wide_block_width_pt
        if panel_role == "footer_stack":
            width_pt = footer_block_width_pt
        content_width_pt = width_pt - 26.0
        title_lines = _wrap_flow_text_to_width(
            str(block["title"]),
            max_width_pt=content_width_pt,
            font_size=base_card_title_size,
            font_weight="bold",
        )
        lines: list[_FlowTextLine] = [
            *[
                _FlowTextLine(
                    text=line,
                    font_size=base_card_title_size,
                    font_weight="bold",
                    color=flow_title_text,
                )
                for line in title_lines
            ]
        ]
        for item_index, item in enumerate(block["lines"]):
            label_lines = _wrap_flow_text_to_width(
                str(item["label"]),
                max_width_pt=content_width_pt,
                font_size=base_label_size,
                font_weight="bold",
            )
            detail_lines = _wrap_flow_text_to_width(
                str(item.get("detail") or ""),
                max_width_pt=content_width_pt,
                font_size=base_detail_size,
                font_weight="normal",
            )
            item_gap = 8.0 if item_index == 0 else 10.0
            for label_index, line in enumerate(label_lines):
                lines.append(
                    _FlowTextLine(
                        text=line,
                        font_size=base_label_size,
                        font_weight="bold",
                        color=flow_title_text,
                        gap_before=item_gap if label_index == 0 else 0.0,
                    )
                )
            for detail_index, line in enumerate(detail_lines):
                lines.append(
                    _FlowTextLine(
                        text=line,
                        font_size=base_detail_size,
                        font_weight="normal",
                        color=flow_body_text,
                        gap_before=4.0 if detail_index == 0 else 0.0,
                    )
                )
        return _FlowNodeSpec(
            node_id=f"secondary_panel_{block['panel_id']}",
            box_id=f"secondary_panel_{block['panel_id']}",
            box_type="secondary_panel",
            panel_role=panel_role,
            fill_color=fill_color,
            edge_color=edge_color,
            linewidth=base_primary_linewidth if style_role == "primary" else base_secondary_linewidth,
            lines=tuple(lines),
            width_pt=width_pt,
            padding_pt=hierarchy_padding_pt,
        )

    def spec_base_height(spec: _FlowNodeSpec) -> float:
        height = spec.padding_pt * 2.0
        for line in spec.lines:
            height += line.gap_before
            height += line.font_size * 1.24
        return height

    right_blocks: list[dict[str, Any]] = [*design_panels]
    if endpoint_inventory:
        right_blocks.append(
            {
                "panel_id": "endpoint_inventory",
                "layout_role": "footer_stack",
                "style_role": "audit",
                "title": "Endpoint inventory",
                "lines": [
                    {
                        "label": (
                            f"{item['label']} (n={item['n']})"
                            if isinstance(item.get("n"), int)
                            else str(item["label"])
                        ),
                        "detail": str(item.get("detail") or "").strip(),
                    }
                    for item in endpoint_inventory
                ],
            }
        )

    step_specs = [build_step_spec(step) for step in steps]
    exclusion_specs = {str(item["exclusion_id"]): build_exclusion_spec(item) for item in exclusions}
    design_specs = [build_design_panel_spec(block) for block in right_blocks]

    exclusions_by_step: dict[str, list[dict[str, Any]]] = {}
    for exclusion in exclusions:
        exclusions_by_step.setdefault(str(exclusion["from_step_id"]), []).append(exclusion)
    step_heights_pt = {spec.node_id: spec_base_height(spec) for spec in step_specs}
    exclusion_heights_pt = {spec.node_id: spec_base_height(spec) for spec in exclusion_specs.values()}
    step_stack_gap_pt: dict[str, float] = {}
    stage_cluster_heights_pt: dict[str, float] = {}
    panel_a_base_height_pt = 0.0
    for index, step in enumerate(steps):
        step_id = str(step["step_id"])
        panel_a_base_height_pt += step_heights_pt[f"step_{step_id}"]
        if index == len(steps) - 1:
            continue
        related_exclusions = exclusions_by_step.get(step_id, [])
        cluster_height_pt = 0.0
        if related_exclusions:
            cluster_height_pt = sum(
                exclusion_heights_pt[f"exclusion_{item['exclusion_id']}"] for item in related_exclusions
            ) + flow_exclusion_stack_gap_pt * max(0, len(related_exclusions) - 1)
        gap_height_pt = max(flow_step_gap_pt, cluster_height_pt + flow_split_clearance_pt * 2.0)
        step_stack_gap_pt[step_id] = gap_height_pt
        stage_cluster_heights_pt[step_id] = cluster_height_pt
        panel_a_base_height_pt += gap_height_pt
    flow_panel_base_width_pt = step_width_pt
    if exclusions:
        flow_panel_base_width_pt = max(flow_panel_base_width_pt, step_width_pt + branch_gap_pt + exclusion_width_pt)

    footer_specs = [spec for spec in design_specs if spec.panel_role == "footer_stack"]
    main_panel_specs = [spec for spec in design_specs if spec.panel_role != "footer_stack"]
    main_role_set = {spec.panel_role for spec in main_panel_specs}
    if main_role_set and not (main_role_set.issubset(modern_roles) or main_role_set.issubset(legacy_roles)):
        unknown_roles = ", ".join(sorted(main_role_set))
        raise ValueError(f"cohort_flow_figure received unsupported design panel layout roles: {unknown_roles}")
    modern_layout = not main_role_set or main_role_set.issubset(modern_roles)
    has_left_branch = bool({"left_middle", "left_bottom"} & main_role_set)
    has_right_branch = bool({"right_middle", "right_bottom"} & main_role_set)
    sparse_modern_layout = bool(modern_layout and main_role_set and not (has_left_branch and has_right_branch))

    hierarchy_dot_lines = [
        "digraph CohortFlowPanelB {",
        (
            f'graph [rankdir=TB, splines=ortho, nodesep="{hierarchy_nodesep}", '
            f'ranksep="{hierarchy_ranksep}", margin="0.12", bgcolor="white"];'
        ),
        'node [shape=plain, fontname="DejaVu Sans"];',
        f'edge [color="{flow_connector}", penwidth="{base_connector_linewidth}", arrowhead=none];',
    ]
    for spec in main_panel_specs:
        hierarchy_dot_lines.append(f'{spec.node_id} [label={_flow_html_label_for_node(spec)}];')
    blocks_by_role = {spec.panel_role: spec for spec in main_panel_specs}
    if modern_layout:
        if "left_middle" in blocks_by_role and "right_middle" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{{ rank=same; {blocks_by_role['left_middle'].node_id}; {blocks_by_role['right_middle'].node_id}; }}"
            )
        if "left_bottom" in blocks_by_role and "right_bottom" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{{ rank=same; {blocks_by_role['left_bottom'].node_id}; {blocks_by_role['right_bottom'].node_id}; }}"
            )
        if (
            "wide_top" in blocks_by_role
            and ("left_middle" in blocks_by_role or "left_bottom" in blocks_by_role)
            and ("right_middle" in blocks_by_role or "right_bottom" in blocks_by_role)
        ):
            left_target = blocks_by_role.get("left_middle") or blocks_by_role.get("left_bottom")
            right_target = blocks_by_role.get("right_middle") or blocks_by_role.get("right_bottom")
            hierarchy_dot_lines.extend(
                [
                    'hierarchy_root_branch [shape=point, width=0.01, label="", style=invis];',
                    'hierarchy_left_drop [shape=point, width=0.01, label="", style=invis];',
                    'hierarchy_right_drop [shape=point, width=0.01, label="", style=invis];',
                    "{ rank=same; hierarchy_left_drop; hierarchy_right_drop; }",
                    f"{blocks_by_role['wide_top'].node_id} -> hierarchy_root_branch [weight=14];",
                    "hierarchy_root_branch -> hierarchy_left_drop [weight=14];",
                    "hierarchy_root_branch -> hierarchy_right_drop [weight=14];",
                    f"hierarchy_left_drop -> {left_target.node_id} [weight=14];",
                    f"hierarchy_right_drop -> {right_target.node_id} [weight=14];",
                ]
            )
        if "left_middle" in blocks_by_role and "left_bottom" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{blocks_by_role['left_middle'].node_id} -> {blocks_by_role['left_bottom'].node_id} [weight=14];"
            )
        if "right_middle" in blocks_by_role and "right_bottom" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{blocks_by_role['right_middle'].node_id} -> {blocks_by_role['right_bottom'].node_id} [weight=14];"
            )
    else:
        if "wide_left" in blocks_by_role and "top_right" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{{ rank=same; {blocks_by_role['wide_left'].node_id}; {blocks_by_role['top_right'].node_id}; }}"
            )
            hierarchy_dot_lines.append(
                f"{blocks_by_role['wide_left'].node_id} -> {blocks_by_role['top_right'].node_id} [style=invis, weight=4];"
            )
        if "top_right" in blocks_by_role and "bottom_right" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{blocks_by_role['top_right'].node_id} -> {blocks_by_role['bottom_right'].node_id} [style=invis, weight=18];"
            )
    hierarchy_dot_lines.append("}")
    hierarchy_layout = _run_graphviz_layout(graph_name="cohort-flow-panel-b", dot_source="\n".join(hierarchy_dot_lines))

    footer_stack_base_height = 0.0
    if footer_specs:
        footer_stack_base_height = sum(spec_base_height(spec) for spec in footer_specs) + footer_gap_pt * max(0, len(footer_specs) - 1)
    sparse_stack_specs = (
        [
            blocks_by_role[role]
            for role in ("wide_top", "left_middle", "right_middle", "left_bottom", "right_bottom", "wide_bottom")
            if role in blocks_by_role
        ]
        if sparse_modern_layout
        else []
    )
    panel_b_main_base_height = (
        sum(spec_base_height(spec) for spec in sparse_stack_specs) + sparse_stack_gap_pt * max(0, len(sparse_stack_specs) - 1)
        if sparse_modern_layout
        else hierarchy_layout.height_pt
    )
    panel_b_main_base_width = (
        max((spec.width_pt for spec in sparse_stack_specs), default=0.0)
        if sparse_modern_layout
        else hierarchy_layout.width_pt
    )

    panel_b_total_base_height = panel_b_main_base_height + (footer_stack_base_height + footer_gap_pt if footer_specs else 0.0)
    available_width_pt = figure_width_pt - side_margin_pt * 2.0 - panel_gap_pt
    total_base_width = flow_panel_base_width_pt + max(panel_b_main_base_width, max((spec.width_pt for spec in footer_specs), default=0.0))
    scale = available_width_pt / total_base_width if total_base_width > 0 else 1.0
    content_height_pt = max(panel_a_base_height_pt, panel_b_total_base_height) * scale
    canvas_height_pt = bottom_margin_pt + content_height_pt + heading_band_pt

    fig = plt.figure(figsize=(figure_width_pt / 72.0, canvas_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    panel_a_x0 = side_margin_pt
    panel_a_y0 = bottom_margin_pt + content_height_pt - panel_a_base_height_pt * scale
    panel_a_width_pt = flow_panel_base_width_pt * scale
    panel_b_x0 = panel_a_x0 + panel_a_width_pt + panel_gap_pt
    panel_b_total_y0 = bottom_margin_pt + content_height_pt - panel_b_total_base_height * scale
    footer_stack_height_scaled = footer_stack_base_height * scale
    panel_b_main_y0 = panel_b_total_y0 + footer_stack_height_scaled + (footer_gap_pt * scale if footer_specs else 0.0)
    panel_b_width_pt = max(panel_b_main_base_width, max((spec.width_pt for spec in footer_specs), default=0.0)) * scale
    panel_b_main_width_pt = panel_b_main_base_width * scale

    def transform_graphviz_box(box: _GraphvizNodeBox, *, panel_x0: float, panel_y0: float) -> dict[str, float]:
        return {
            "x0": panel_x0 + box.x0 * scale,
            "y0": panel_y0 + box.y0 * scale,
            "x1": panel_x0 + box.x1 * scale,
            "y1": panel_y0 + box.y1 * scale,
        }

    def draw_node(spec: _FlowNodeSpec, box: dict[str, float]) -> None:
        ax.add_patch(
            FancyBboxPatch(
                (box["x0"], box["y0"]),
                box["x1"] - box["x0"],
                box["y1"] - box["y0"],
                boxstyle=f"round,pad=0.0,rounding_size={max(8.0, 14.0 * scale):.2f}",
                linewidth=max(0.9, spec.linewidth * scale),
                edgecolor=spec.edge_color,
                facecolor=spec.fill_color,
            )
        )
        x_text = box["x0"] + spec.padding_pt * scale
        y_cursor = box["y1"] - spec.padding_pt * scale
        for line in spec.lines:
            y_cursor -= line.gap_before * scale
            ax.text(
                x_text,
                y_cursor,
                line.text,
                fontsize=line.font_size * scale,
                fontweight=line.font_weight,
                color=line.color,
                ha="left",
                va="top",
            )
            y_cursor -= line.font_size * scale * 1.22

    def draw_vertical_connector(
        *,
        box_id: str,
        x: float,
        y_top: float,
        y_bottom: float,
        box_type: str,
        arrow: bool,
        record_box: bool = True,
    ) -> None:
        half_width = max(1.4, base_connector_linewidth * scale * 2.0)
        if record_box:
            guide_boxes.append(
                _flow_box_to_normalized(
                    x0=x - half_width,
                    y0=y_bottom,
                    x1=x + half_width,
                    y1=y_top,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=box_id,
                    box_type=box_type,
                )
            )
        if y_top < y_bottom:
            y_top, y_bottom = y_bottom, y_top
        if arrow:
            ax.add_patch(
                FancyArrowPatch(
                    (x, y_top),
                    (x, y_bottom),
                    arrowstyle="-|>",
                    mutation_scale=max(10.0, 12.0 * scale),
                    linewidth=max(0.9, base_connector_linewidth * scale),
                    color=flow_connector,
                )
            )
            return
        ax.plot([x, x], [y_top, y_bottom], color=flow_connector, linewidth=max(0.9, base_connector_linewidth * scale))

    def draw_horizontal_connector(
        *,
        box_id: str,
        x_left: float,
        x_right: float,
        y: float,
        box_type: str,
        arrow: bool,
        record_box: bool = True,
    ) -> None:
        half_height = max(1.4, base_connector_linewidth * scale * 2.0)
        if record_box:
            guide_boxes.append(
                _flow_box_to_normalized(
                    x0=x_left,
                    y0=y - half_height,
                    x1=x_right,
                    y1=y + half_height,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=box_id,
                    box_type=box_type,
                )
            )
        if x_left > x_right:
            x_left, x_right = x_right, x_left
        if arrow:
            ax.add_patch(
                FancyArrowPatch(
                    (x_left, y),
                    (x_right, y),
                    arrowstyle="-|>",
                    mutation_scale=max(9.0, 11.0 * scale),
                    linewidth=max(0.9, base_connector_linewidth * scale),
                    color=flow_connector,
                )
            )
            return
        ax.plot([x_left, x_right], [y, y], color=flow_connector, linewidth=max(0.9, base_connector_linewidth * scale))

    guide_boxes: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []

    next_step_by_id = {
        str(step["step_id"]): str(steps[index + 1]["step_id"])
        for index, step in enumerate(steps[:-1])
    }
    step_boxes_by_id: dict[str, dict[str, float]] = {}
    exclusion_boxes_by_id: dict[str, dict[str, float]] = {}
    stage_split_y_by_step: dict[str, float] = {}
    panel_a_top = panel_a_y0 + panel_a_base_height_pt * scale
    current_top = panel_a_top
    exclusion_x0 = panel_a_x0 + (step_width_pt + branch_gap_pt) * scale

    for index, spec in enumerate(step_specs):
        step_height_pt = step_heights_pt[spec.node_id] * scale
        box = {
            "x0": panel_a_x0,
            "y0": current_top - step_height_pt,
            "x1": panel_a_x0 + spec.width_pt * scale,
            "y1": current_top,
        }
        draw_node(spec, box)
        step_boxes_by_id[spec.node_id] = box
        layout_boxes.append(
            _flow_box_to_normalized(
                **box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=spec.box_id,
                box_type=spec.box_type,
            )
        )
        if index == len(steps) - 1:
            continue
        step_id = str(steps[index]["step_id"])
        stage_gap_pt = step_stack_gap_pt[step_id] * scale
        stage_split_y = box["y0"] - stage_gap_pt / 2.0
        stage_split_y_by_step[step_id] = stage_split_y
        related_exclusions = exclusions_by_step.get(step_id, [])
        if related_exclusions:
            cluster_height_pt = stage_cluster_heights_pt[step_id] * scale
            cluster_top = stage_split_y + cluster_height_pt / 2.0
            for exclusion in related_exclusions:
                exclusion_spec = exclusion_specs[str(exclusion["exclusion_id"])]
                exclusion_height_pt = exclusion_heights_pt[exclusion_spec.node_id] * scale
                exclusion_box = {
                    "x0": exclusion_x0,
                    "y0": cluster_top - exclusion_height_pt,
                    "x1": exclusion_x0 + exclusion_spec.width_pt * scale,
                    "y1": cluster_top,
                }
                cluster_top = exclusion_box["y0"] - flow_exclusion_stack_gap_pt * scale
                draw_node(exclusion_spec, exclusion_box)
                exclusion_boxes_by_id[exclusion_spec.node_id] = exclusion_box
                layout_boxes.append(
                    _flow_box_to_normalized(
                        **exclusion_box,
                        canvas_width_pt=figure_width_pt,
                        canvas_height_pt=canvas_height_pt,
                        box_id=exclusion_spec.box_id,
                        box_type=exclusion_spec.box_type,
                    )
                )
        current_top = box["y0"] - stage_gap_pt

    flow_panel_union_boxes = [*step_boxes_by_id.values(), *exclusion_boxes_by_id.values()]
    if flow_panel_union_boxes:
        union_box = _flow_union_box(boxes=flow_panel_union_boxes, box_id="flow_panel", box_type="flow_panel")
        panel_boxes.append(
            _flow_box_to_normalized(
                **union_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
            )
        )

    for upper_step, lower_step in zip(steps, steps[1:], strict=False):
        upper_box = step_boxes_by_id[f"step_{upper_step['step_id']}"]
        lower_box = step_boxes_by_id[f"step_{lower_step['step_id']}"]
        spine_x = (upper_box["x0"] + upper_box["x1"]) / 2.0
        spine_box_id = f"flow_spine_{upper_step['step_id']}_to_{lower_step['step_id']}"
        related_exclusions = exclusions_by_step.get(str(upper_step["step_id"]), [])
        if related_exclusions:
            half_width = max(1.4, base_connector_linewidth * scale * 2.0)
            guide_boxes.append(
                _flow_box_to_normalized(
                    x0=spine_x - half_width,
                    y0=lower_box["y1"],
                    x1=spine_x + half_width,
                    y1=upper_box["y0"],
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spine_box_id,
                    box_type="flow_connector",
                )
            )
            split_y = stage_split_y_by_step[str(upper_step["step_id"])]
            draw_vertical_connector(
                box_id=f"{spine_box_id}_upper",
                x=spine_x,
                y_top=upper_box["y0"],
                y_bottom=split_y,
                box_type="flow_connector",
                arrow=False,
                record_box=False,
            )
            draw_vertical_connector(
                box_id=f"{spine_box_id}_lower",
                x=spine_x,
                y_top=split_y,
                y_bottom=lower_box["y1"],
                box_type="flow_connector",
                arrow=True,
                record_box=False,
            )
            continue
        draw_vertical_connector(
            box_id=spine_box_id,
            x=spine_x,
            y_top=upper_box["y0"],
            y_bottom=lower_box["y1"],
            box_type="flow_connector",
            arrow=True,
        )

    for exclusion in exclusions:
        source_step_id = str(exclusion["from_step_id"])
        next_step_id = next_step_by_id.get(source_step_id)
        if next_step_id is None:
            continue
        source_box = step_boxes_by_id[f"step_{source_step_id}"]
        exclusion_box = exclusion_boxes_by_id[f"exclusion_{exclusion['exclusion_id']}"]
        spine_x = (source_box["x0"] + source_box["x1"]) / 2.0
        split_y = stage_split_y_by_step.get(source_step_id)
        exclusion_center_y = (exclusion_box["y0"] + exclusion_box["y1"]) / 2.0
        if split_y is not None and abs(exclusion_center_y - split_y) > 0.5:
            draw_vertical_connector(
                box_id=f"flow_branch_stem_{exclusion['exclusion_id']}",
                x=spine_x,
                y_top=max(split_y, exclusion_center_y),
                y_bottom=min(split_y, exclusion_center_y),
                box_type="flow_branch_connector",
                arrow=False,
            )
        draw_horizontal_connector(
            box_id=f"flow_branch_{exclusion['exclusion_id']}",
            x_left=spine_x,
            x_right=exclusion_box["x0"],
            y=exclusion_center_y,
            box_type="flow_branch_connector",
            arrow=True,
        )

    secondary_panel_regions: dict[str, dict[str, float]] = {}
    if sparse_modern_layout:
        current_top = panel_b_main_y0 + panel_b_main_base_height * scale
        for spec in sparse_stack_specs:
            box_height_pt = spec_base_height(spec) * scale
            box_width_pt = spec.width_pt * scale
            box = {
                "x0": panel_b_x0 + (panel_b_main_width_pt - box_width_pt) / 2.0,
                "y0": current_top - box_height_pt,
                "x1": panel_b_x0 + (panel_b_main_width_pt - box_width_pt) / 2.0 + box_width_pt,
                "y1": current_top,
            }
            draw_node(spec, box)
            secondary_panel_regions[spec.panel_role] = box
            panel_boxes.append(
                _flow_box_to_normalized(
                    **box,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spec.box_id,
                    box_type=spec.box_type,
                )
            )
            current_top = box["y0"] - sparse_stack_gap_pt * scale
    else:
        for spec in main_panel_specs:
            box = transform_graphviz_box(hierarchy_layout.nodes[spec.node_id], panel_x0=panel_b_x0, panel_y0=panel_b_main_y0)
            if modern_layout and spec.panel_role == "wide_top":
                box = {
                    "x0": panel_b_x0 - 1.0,
                    "y0": box["y0"],
                    "x1": panel_b_x0 + panel_b_main_width_pt + 1.0,
                    "y1": box["y1"],
                }
            draw_node(spec, box)
            secondary_panel_regions[spec.panel_role] = box
            panel_boxes.append(
                _flow_box_to_normalized(
                    **box,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spec.box_id,
                    box_type=spec.box_type,
                )
            )

    if footer_specs:
        footer_cursor_y = panel_b_total_y0
        for spec in footer_specs:
            footer_height_pt = spec_base_height(spec) * scale
            footer_x0 = panel_b_x0 + (panel_b_width_pt - spec.width_pt * scale) / 2.0
            footer_box = {
                "x0": footer_x0,
                "y0": footer_cursor_y,
                "x1": footer_x0 + spec.width_pt * scale,
                "y1": footer_cursor_y + footer_height_pt,
            }
            draw_node(spec, footer_box)
            secondary_panel_regions[spec.panel_role] = footer_box
            panel_boxes.append(
                _flow_box_to_normalized(
                    **footer_box,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spec.box_id,
                    box_type=spec.box_type,
                )
            )
            footer_cursor_y = footer_box["y1"] + footer_gap_pt * scale

    if modern_layout:
        if sparse_modern_layout:
            sparse_stack_roles = [spec.panel_role for spec in sparse_stack_specs]
            for upper_role, lower_role in zip(sparse_stack_roles, sparse_stack_roles[1:], strict=False):
                upper_region = secondary_panel_regions.get(upper_role)
                lower_region = secondary_panel_regions.get(lower_role)
                if upper_region is None or lower_region is None:
                    continue
                draw_vertical_connector(
                    box_id=f"hierarchy_connector_{upper_role}_to_{lower_role}",
                    x=(upper_region["x0"] + upper_region["x1"]) / 2.0,
                    y_top=upper_region["y0"],
                    y_bottom=lower_region["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
        else:
            validation_region = secondary_panel_regions.get("wide_top")
            left_middle_region = secondary_panel_regions.get("left_middle")
            right_middle_region = secondary_panel_regions.get("right_middle")
            left_bottom_region = secondary_panel_regions.get("left_bottom")
            right_bottom_region = secondary_panel_regions.get("right_bottom")
            left_branch_target = left_middle_region or left_bottom_region
            right_branch_target = right_middle_region or right_bottom_region
            branch_root = hierarchy_layout.nodes.get("hierarchy_root_branch")
            left_drop = hierarchy_layout.nodes.get("hierarchy_left_drop")
            right_drop = hierarchy_layout.nodes.get("hierarchy_right_drop")
            if (
                validation_region is not None
                and left_branch_target is not None
                and right_branch_target is not None
                and branch_root is not None
                and left_drop is not None
                and right_drop is not None
            ):
                branch_y = panel_b_main_y0 + branch_root.cy * scale
                validation_center_x = (validation_region["x0"] + validation_region["x1"]) / 2.0
                left_branch_center_x = (left_branch_target["x0"] + left_branch_target["x1"]) / 2.0
                right_branch_center_x = (right_branch_target["x0"] + right_branch_target["x1"]) / 2.0
                draw_vertical_connector(
                    box_id="hierarchy_root_trunk",
                    x=validation_center_x,
                    y_top=validation_region["y0"],
                    y_bottom=branch_y,
                    box_type="hierarchy_connector",
                    arrow=False,
                )
                draw_horizontal_connector(
                    box_id="hierarchy_root_branch",
                    x_left=left_branch_center_x,
                    x_right=right_branch_center_x,
                    y=branch_y,
                    box_type="hierarchy_connector",
                    arrow=False,
                )
                draw_vertical_connector(
                    box_id="hierarchy_connector_branch_to_left",
                    x=left_branch_center_x,
                    y_top=branch_y,
                    y_bottom=left_branch_target["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
                draw_vertical_connector(
                    box_id="hierarchy_connector_branch_to_right",
                    x=right_branch_center_x,
                    y_top=branch_y,
                    y_bottom=right_branch_target["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
            if left_middle_region is not None and left_bottom_region is not None:
                draw_vertical_connector(
                    box_id="hierarchy_connector_left_middle_to_left_bottom",
                    x=(left_middle_region["x0"] + left_middle_region["x1"]) / 2.0,
                    y_top=left_middle_region["y0"],
                    y_bottom=left_bottom_region["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
            if right_middle_region is not None and right_bottom_region is not None:
                draw_vertical_connector(
                    box_id="hierarchy_connector_right_middle_to_right_bottom",
                    x=(right_middle_region["x0"] + right_middle_region["x1"]) / 2.0,
                    y_top=right_middle_region["y0"],
                    y_bottom=right_bottom_region["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )

    panel_a_outer = {
        "x0": max(0.0, panel_a_x0 - 10.0 * scale),
        "y0": max(0.0, bottom_margin_pt - 4.0),
        "x1": min(figure_width_pt, panel_a_x0 + panel_a_width_pt + 10.0 * scale),
        "y1": min(canvas_height_pt, canvas_height_pt - 6.0),
    }
    panel_b_outer = {
        "x0": max(0.0, panel_b_x0 - 10.0 * scale),
        "y0": max(0.0, bottom_margin_pt - 4.0),
        "x1": min(figure_width_pt, panel_b_x0 + panel_b_width_pt + 10.0 * scale),
        "y1": min(canvas_height_pt, canvas_height_pt - 6.0),
    }
    panel_boxes.insert(
        0,
        _flow_box_to_normalized(
            **panel_b_outer,
            canvas_width_pt=figure_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id="subfigure_panel_B",
            box_type="subfigure_panel",
        ),
    )
    panel_boxes.insert(
        0,
        _flow_box_to_normalized(
            **panel_a_outer,
            canvas_width_pt=figure_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id="subfigure_panel_A",
            box_type="subfigure_panel",
        ),
    )

    heading_y = canvas_height_pt - 12.0
    for panel_id, x0, heading in (
        ("A", panel_a_x0, "Cohort assembly"),
        ("B", panel_b_x0, "Validation and model hierarchy"),
    ):
        ax.text(
            x0,
            heading_y,
            panel_id,
            fontsize=base_panel_label_size * scale,
            fontweight="bold",
            color=flow_panel_label,
            ha="left",
            va="top",
        )
        label_width = _measure_flow_text_width_pt(panel_id, font_size=base_panel_label_size * scale, font_weight="bold")
        layout_boxes.append(
            _flow_box_to_normalized(
                x0=x0,
                y0=heading_y - base_panel_label_size * scale * 1.2,
                x1=x0 + label_width,
                y1=heading_y,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_label_{panel_id}",
                box_type="panel_label",
            )
        )
        ax.text(
            x0 + label_width + 12.0 * scale,
            heading_y - 1.0,
            heading,
            fontsize=base_card_title_size * scale,
            fontweight="bold",
            color=flow_title_text,
            ha="left",
            va="top",
        )

    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(
        output_layout_path,
        {
            "template_id": "cohort_flow_figure",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "steps": steps,
                "exclusions": exclusions,
                "endpoint_inventory": endpoint_inventory,
                "design_panels": design_panels,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=220)
    plt.close(fig)

def _write_rectangular_table_outputs(
    *,
    output_md_path: Path,
    title: str,
    headers: list[str],
    table_rows: list[list[str]],
    output_csv_path: Path | None = None,
) -> None:
    if output_csv_path is not None:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(table_rows)

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in table_rows:
        markdown_lines.append("| " + " | ".join(row) + " |")
    output_md_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")


def _write_table_outputs(
    *,
    output_md_path: Path,
    title: str,
    column_labels: list[str],
    rows: list[dict[str, Any]],
    stub_header: str,
    output_csv_path: Path | None = None,
) -> None:
    headers = [stub_header, *column_labels]
    table_rows = [[row["label"], *row["values"]] for row in rows]
    _write_rectangular_table_outputs(
        output_md_path=output_md_path,
        title=title,
        headers=headers,
        table_rows=table_rows,
        output_csv_path=output_csv_path,
    )


def _bbox_to_layout_box(
    *,
    figure: plt.Figure,
    bbox,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    x0, y0 = figure.transFigure.inverted().transform((bbox.x0, bbox.y0))
    x1, y1 = figure.transFigure.inverted().transform((bbox.x1, bbox.y1))
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": float(min(x0, x1)),
        "y0": float(min(y0, y1)),
        "x1": float(max(x0, x1)),
        "y1": float(max(y0, y1)),
    }


def _data_box_to_layout_box(
    *,
    axes,
    figure: plt.Figure,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    left_bottom = axes.transData.transform((x0, y0))
    right_top = axes.transData.transform((x1, y1))
    bbox = matplotlib.transforms.Bbox.from_extents(left_bottom[0], left_bottom[1], right_top[0], right_top[1])
    return _bbox_to_layout_box(figure=figure, bbox=bbox, box_id=box_id, box_type=box_type)


def _data_point_to_figure_xy(*, axes, figure: plt.Figure, x: float, y: float) -> tuple[float, float]:
    display_x, display_y = axes.transData.transform((x, y))
    figure_x, figure_y = figure.transFigure.inverted().transform((display_x, display_y))
    return float(figure_x), float(figure_y)


def _clip_line_segment_to_axes_window(
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> tuple[float, float, float, float] | None:
    dx = x1 - x0
    dy = y1 - y0
    t0 = 0.0
    t1 = 1.0
    for p, q in (
        (-dx, x0 - xmin),
        (dx, xmax - x0),
        (-dy, y0 - ymin),
        (dy, ymax - y0),
    ):
        if p == 0.0:
            if q < 0.0:
                return None
            continue
        t = q / p
        if p < 0.0:
            if t > t1:
                return None
            if t > t0:
                t0 = t
        else:
            if t < t0:
                return None
            if t < t1:
                t1 = t
    return (
        x0 + t0 * dx,
        y0 + t0 * dy,
        x0 + t1 * dx,
        y0 + t1 * dy,
    )


def _clip_reference_line_to_axes_window(
    *,
    reference_line: dict[str, Any] | None,
    axes,
) -> dict[str, Any] | None:
    if not isinstance(reference_line, dict):
        return None
    x_values = [float(value) for value in reference_line.get("x") or []]
    y_values = [float(value) for value in reference_line.get("y") or []]
    if len(x_values) != len(y_values):
        raise ValueError("reference_line.x and reference_line.y must have the same length")
    xmin, xmax = sorted(float(value) for value in axes.get_xlim())
    ymin, ymax = sorted(float(value) for value in axes.get_ylim())
    if len(x_values) == 1:
        x_value = x_values[0]
        y_value = y_values[0]
        if xmin <= x_value <= xmax and ymin <= y_value <= ymax:
            return {
                "x": [x_value],
                "y": [y_value],
                "label": str(reference_line.get("label") or "").strip(),
            }
        return None

    clipped_points: list[tuple[float, float]] = []
    for index in range(len(x_values) - 1):
        start_x = x_values[index]
        start_y = y_values[index]
        end_x = x_values[index + 1]
        end_y = y_values[index + 1]
        clipped_segment = _clip_line_segment_to_axes_window(
            x0=start_x,
            y0=start_y,
            x1=end_x,
            y1=end_y,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
        )
        if clipped_segment is None:
            continue
        clipped_start = (clipped_segment[0], clipped_segment[1])
        clipped_end = (clipped_segment[2], clipped_segment[3])
        if not clipped_points or clipped_points[-1] != clipped_start:
            clipped_points.append(clipped_start)
        if clipped_points[-1] != clipped_end:
            clipped_points.append(clipped_end)
    if not clipped_points:
        return None
    return {
        "x": [point[0] for point in clipped_points],
        "y": [point[1] for point in clipped_points],
        "label": str(reference_line.get("label") or "").strip(),
    }


def _normalize_reference_line_to_device_space(
    *,
    reference_line: dict[str, Any] | None,
    axes,
    figure: plt.Figure,
    clip_to_axes_window: bool = False,
) -> dict[str, Any] | None:
    if clip_to_axes_window:
        reference_line = _clip_reference_line_to_axes_window(reference_line=reference_line, axes=axes)
    if not isinstance(reference_line, dict):
        return None
    x_values = list(reference_line.get("x") or [])
    y_values = list(reference_line.get("y") or [])
    if len(x_values) != len(y_values):
        raise ValueError("reference_line.x and reference_line.y must have the same length")
    normalized_x: list[float] = []
    normalized_y: list[float] = []
    for x_value, y_value in zip(x_values, y_values, strict=True):
        figure_x, figure_y = _data_point_to_figure_xy(
            axes=axes,
            figure=figure,
            x=float(x_value),
            y=float(y_value),
        )
        normalized_x.append(figure_x)
        normalized_y.append(figure_y)
    return {
        "x": normalized_x,
        "y": normalized_y,
        "label": str(reference_line.get("label") or "").strip(),
    }


def _normalize_reference_line_collection_to_device_space(
    *,
    reference_lines: list[dict[str, Any]] | None,
    axes,
    figure: plt.Figure,
) -> list[dict[str, Any]]:
    normalized_lines: list[dict[str, Any]] = []
    for item in reference_lines or []:
        normalized_line = _normalize_reference_line_to_device_space(
            reference_line=item,
            axes=axes,
            figure=figure,
        )
        if normalized_line is not None:
            normalized_lines.append(normalized_line)
    return normalized_lines


def _build_python_shap_layout_sidecar(
    *,
    figure: plt.Figure,
    axes,
    colorbar,
    rows: list[dict[str, Any]],
    point_rows: list[dict[str, Any]],
    template_id: str,
) -> dict[str, Any]:
    renderer = figure.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=axes.title.get_window_extent(renderer=renderer),
            box_id="title",
            box_type="title",
        ),
        _bbox_to_layout_box(
            figure=figure,
            bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
    ]
    panel_box = _bbox_to_layout_box(
        figure=figure,
        bbox=axes.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )
    x_min, x_max = axes.get_xlim()
    for row_index, row in enumerate(rows):
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=axes,
                figure=figure,
                x0=x_min,
                y0=row_index - 0.42,
                x1=x_max,
                y1=row_index + 0.42,
                box_id=f"feature_row_{row['feature']}",
                box_type="feature_row",
            )
        )
    guide_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        ),
        _data_box_to_layout_box(
            axes=axes,
            figure=figure,
            x0=0.0,
            y0=-0.5,
            x1=0.0,
            y1=float(len(rows)) - 0.5,
            box_id="zero_line",
            box_type="zero_line",
        ),
    ]
    row_box_id_by_feature = {f"{row['feature']}": f"feature_row_{row['feature']}" for row in rows}
    point_metrics: list[dict[str, Any]] = []
    for item in point_rows:
        figure_x, figure_y = _data_point_to_figure_xy(
            axes=axes,
            figure=figure,
            x=float(item["shap_value"]),
            y=float(item["row_position"]),
        )
        point_metrics.append(
            {
                "feature": str(item["feature"]),
                "row_box_id": row_box_id_by_feature[str(item["feature"])],
                "x": figure_x,
                "y": figure_y,
            }
        )
    return {
        "template_id": template_id,
        "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        "layout_boxes": layout_boxes,
        "panel_boxes": [panel_box],
        "guide_boxes": guide_boxes,
        "metrics": {
            "points": point_metrics,
        },
    }


def _load_layout_sidecar_or_raise(*, path: Path, template_id: str) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"renderer did not produce layout sidecar for `{template_id}`: {path}")
    return load_json(path)


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
                template_id,
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


def _centered_offsets(count: int, *, half_span: float = 0.28) -> list[float]:
    if count <= 1:
        return [0.0]
    step = (half_span * 2.0) / float(count - 1)
    return [(-half_span + step * float(index)) for index in range(count)]


def _prepare_python_render_output_paths(*, output_png_path: Path, output_pdf_path: Path, layout_sidecar_path: Path) -> None:
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    layout_sidecar_path.parent.mkdir(parents=True, exist_ok=True)


def _apply_publication_axes_style(axes) -> None:
    axes.grid(axis="x", color="#e6edf2", linewidth=0.4)
    axes.grid(axis="y", visible=False)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)


def _build_single_panel_layout_sidecar(
    *,
    figure: plt.Figure,
    axes,
    template_id: str,
    metrics: dict[str, Any],
    legend=None,
    annotation_artist=None,
    title_artist=None,
    panel_box_id: str = "panel",
    panel_box_type: str = "panel",
) -> dict[str, Any]:
    renderer = figure.canvas.get_renderer()
    resolved_title_artist = title_artist if title_artist is not None else axes.title
    layout_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=resolved_title_artist.get_window_extent(renderer=renderer),
            box_id="title",
            box_type="title",
        ),
        _bbox_to_layout_box(
            figure=figure,
            bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=figure,
            bbox=axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
    ]
    if annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=annotation_artist.get_window_extent(renderer=renderer),
                box_id="annotation_block",
                box_type="annotation_block",
            )
        )
    guide_boxes: list[dict[str, Any]] = []
    if legend is not None:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend",
                box_type="legend",
            )
        )
    return {
        "template_id": template_id,
        "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        "layout_boxes": layout_boxes,
        "panel_boxes": [
            _bbox_to_layout_box(
                figure=figure,
                bbox=axes.get_window_extent(renderer=renderer),
                box_id=panel_box_id,
                box_type=panel_box_type,
            )
        ],
        "guide_boxes": guide_boxes,
        "metrics": metrics,
    }


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

    outer = fig.add_gridspec(1, 2, width_ratios=[1.06, 0.94], wspace=0.34)
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

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    fig.patch.set_facecolor("white")
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    predicted_color = "#b7a99a"
    observed_color = "#7f8f84"
    group_colors = ("#d8d1c7", "#b7a99a", "#7f8f84")
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
    left_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    left_axes.set_ylabel(str(display_payload.get("y_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    left_axes.set_title(str(display_payload.get("panel_a_title") or "").strip(), fontsize=11, fontweight="bold", color="#334155")
    left_axes.grid(axis="y", color="#d8d1c7", linewidth=0.8, linestyle=":")
    left_axes.grid(axis="x", visible=False)
    left_axes.spines["top"].set_visible(False)
    left_axes.spines["right"].set_visible(False)
    legend = fig.legend(
        *left_axes.get_legend_handles_labels(),
        loc="lower center",
        bbox_to_anchor=(0.28, 0.02),
        ncol=2,
        frameon=False,
    )
    left_axes.text(-0.08, 1.04, "A", transform=left_axes.transAxes, fontsize=11, fontweight="bold", color="#2F3437")

    right_axes.bar(
        x_positions,
        event_counts,
        width=0.58,
        color=[group_colors[index % len(group_colors)] for index in x_positions],
    )
    upper_margin = max(max(event_counts) * 0.08, 1.2)
    for index, value in enumerate(event_counts):
        right_axes.text(index, float(value) + upper_margin * 0.35, str(value), ha="center", va="bottom", fontsize=9)
    right_axes.set_xticks(x_positions)
    right_axes.set_xticklabels(group_labels)
    right_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    right_axes.set_ylabel(
        str(display_payload.get("event_count_y_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    right_axes.set_title(str(display_payload.get("panel_b_title") or "").strip(), fontsize=11, fontweight="bold", color="#334155")
    right_axes.set_ylim(0.0, max(event_counts) + upper_margin)
    right_axes.grid(axis="y", color="#d8d1c7", linewidth=0.8, linestyle=":")
    right_axes.grid(axis="x", visible=False)
    right_axes.spines["top"].set_visible(False)
    right_axes.spines["right"].set_visible(False)
    right_axes.text(-0.08, 1.04, "B", transform=right_axes.transAxes, fontsize=11, fontweight="bold", color="#2F3437")

    fig.subplots_adjust(left=0.09, right=0.98, top=0.82, bottom=0.21, wspace=0.26)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=title_artist.get_window_extent(renderer=renderer),
                    box_id="title",
                    box_type="title",
                ),
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
            ],
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
            "guide_boxes": [
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

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.8, 4.2))
    fig.patch.set_facecolor("white")
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    palette = ("#2a9d8f", "#8c6d31", "#9467bd", "#7f7f7f")
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
            line_color = palette[(index - 1) % len(palette)]
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
    left_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    left_axes.set_ylabel(str(display_payload.get("y_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    left_axes.set_title(str(display_payload.get("panel_a_title") or "").strip(), fontsize=11, fontweight="bold", color="#334155")
    _apply_publication_axes_style(left_axes)
    left_axes.text(-0.08, 1.04, "A", transform=left_axes.transAxes, fontsize=11, fontweight="bold", color="#2F3437")

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
    right_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    right_axes.set_ylabel(
        str(display_payload.get("treated_fraction_y_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    right_axes.set_title(str(display_payload.get("panel_b_title") or "").strip(), fontsize=11, fontweight="bold", color="#334155")
    right_axes.grid(axis="y", color="#e6edf2", linewidth=0.4)
    right_axes.grid(axis="x", visible=False)
    right_axes.spines["top"].set_visible(False)
    right_axes.spines["right"].set_visible(False)
    right_axes.text(-0.08, 1.04, "B", transform=right_axes.transAxes, fontsize=11, fontweight="bold", color="#2F3437")

    handles, labels = left_axes.get_legend_handles_labels()
    legend_position = str(layout_override.get("legend_position") or "lower_center").strip().lower()
    legend = None
    if legend_position != "none":
        if legend_position == "right_bottom":
            legend = fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.98, 0.02), ncol=1, frameon=False)
        else:
            legend = fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=3, frameon=False)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.22, top=0.82, wspace=0.28)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    normalized_reference_line = _normalize_reference_line_to_device_space(
        reference_line=reference_line,
        axes=left_axes,
        figure=fig,
    )
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=title_artist.get_window_extent(renderer=renderer),
                    box_id="title",
                    box_type="title",
                ),
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
            ],
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
    discrimination_series = list(display_payload.get("discrimination_series") or [])
    calibration_groups = list(display_payload.get("calibration_groups") or [])
    if not discrimination_series or not calibration_groups:
        raise RuntimeError(f"{template_id} requires non-empty discrimination_series and calibration_groups")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(9.0, 4.8))
    fig.patch.set_facecolor("white")
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    palette = ("#1f4e79", "#c94f3d", "#2a9d8f", "#8c6d31")

    for index, item in enumerate(discrimination_series):
        left_axes.plot(
            item["x"],
            item["y"],
            linewidth=2.0,
            color=palette[index % len(palette)],
            label=str(item["label"]),
        )
    discrimination_reference_line = display_payload.get("discrimination_reference_line")
    if isinstance(discrimination_reference_line, dict):
        left_axes.plot(
            discrimination_reference_line["x"],
            discrimination_reference_line["y"],
            linewidth=1.0,
            linestyle="--",
            color="#6b7280",
        )
    left_axes.set_xlim(0.0, 1.0)
    left_axes.set_ylim(0.0, 1.02)
    left_axes.set_xlabel(
        str(display_payload.get("discrimination_x_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    left_axes.set_ylabel(
        str(display_payload.get("discrimination_y_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    left_axes.set_title("Discrimination", fontsize=11, fontweight="bold", color="#334155")
    _apply_publication_axes_style(left_axes)

    max_time = max(max(float(item) for item in group["times"]) for group in calibration_groups)
    for index, group in enumerate(calibration_groups):
        right_axes.plot(
            group["times"],
            group["values"],
            linewidth=1.8,
            marker="o",
            markersize=4.2,
            color=palette[index % len(palette)],
            label=str(group["label"]),
        )
    calibration_reference_line = display_payload.get("calibration_reference_line")
    if isinstance(calibration_reference_line, dict):
        right_axes.plot(
            calibration_reference_line["x"],
            calibration_reference_line["y"],
            linewidth=1.0,
            linestyle="--",
            color="#6b7280",
        )
    right_axes.set_xlim(0.0, max_time)
    right_axes.set_ylim(0.0, 1.02)
    right_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    right_axes.set_ylabel(
        str(display_payload.get("calibration_y_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    right_axes.set_title("Grouped Calibration", fontsize=11, fontweight="bold", color="#334155")
    _apply_publication_axes_style(right_axes)

    handles, labels = [], []
    for axes in (left_axes, right_axes):
        axis_handles, axis_labels = axes.get_legend_handles_labels()
        for handle, label in zip(axis_handles, axis_labels, strict=True):
            if label in labels or not label:
                continue
            handles.append(handle)
            labels.append(label)
    legend = fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.03), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.80, bottom=0.22, wspace=0.28)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=title_artist.get_window_extent(renderer=renderer),
            box_id="title",
            box_type="title",
        ),
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
            box_id="calibration_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="calibration_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
    ]
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
                "series": discrimination_series,
                "reference_line": discrimination_reference_line,
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

    figure_height = max(7.0, 0.18 * len(center_event_counts) + 5.8)
    fig = plt.figure(figsize=(10.8, figure_height))
    grid = fig.add_gridspec(2, 2, height_ratios=[2.0, 1.0], hspace=0.38, width_ratios=[1.0, 1.0])
    center_axes = fig.add_subplot(grid[0, :])
    region_axes = fig.add_subplot(grid[1, 0])
    right_grid = grid[1, 1].subgridspec(2, 1, hspace=0.85)
    north_south_axes = fig.add_subplot(right_grid[0, 0])
    urban_rural_axes = fig.add_subplot(right_grid[1, 0])
    fig.patch.set_facecolor("white")
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    center_colors = {"train": "#B7A99A", "validation": "#7F8F84"}
    center_labels = [str(item["center_label"]) for item in center_event_counts]
    center_values = [int(item["event_count"]) for item in center_event_counts]
    center_split_buckets = [str(item["split_bucket"]) for item in center_event_counts]
    center_bars = center_axes.bar(
        center_labels,
        center_values,
        color=[center_colors[item] for item in center_split_buckets],
        edgecolor="none",
        linewidth=0,
    )
    center_axes.set_ylabel(
        str(display_payload.get("center_event_y_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    center_axes.set_xlabel("Anonymous center identifier", fontsize=11, fontweight="bold", color="#13293d")
    center_axes.set_title("Center-level support across the frozen split", fontsize=11, fontweight="bold", color="#334155")
    center_axes.grid(axis="y", linestyle=":", color="#d0d0d0", zorder=0)
    center_axes.tick_params(axis="x", rotation=90, labelsize=6)
    center_axes.spines["top"].set_visible(False)
    center_axes.spines["right"].set_visible(False)
    legend = center_axes.legend(
        handles=[
            matplotlib.patches.Patch(color=center_colors["train"], label="Train"),
            matplotlib.patches.Patch(color=center_colors["validation"], label="Validation"),
        ],
        title="Split",
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.0, 1.02),
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
            colors = ["#8A9199"] * len(counts)
        elif panel["layout_role"] == "top_right":
            colors = ["#8A9199", "#CDB89B"][: len(counts)] or ["#8A9199"]
        else:
            default_palette = ["#7F8F84", "#C59D7B", "#D8D1C7", "#B7A99A"]
            colors = default_palette[: len(counts)]
            if len(colors) < len(counts):
                colors.extend([default_palette[-1]] * (len(counts) - len(colors)))
        bars = axes.bar(labels, counts, color=colors, edgecolor="none")
        axes.set_title(str(panel["title"]), fontsize=10, pad=8)
        axes.set_ylabel(
            str(display_payload.get("coverage_y_label") or "").strip(),
            fontsize=9,
            color="#13293d",
        )
        axes.grid(axis="y", linestyle=":", color="#dddddd", zorder=0)
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)
        if panel["layout_role"] == "wide_left":
            axes.tick_params(axis="x", rotation=45, labelsize=8)
        else:
            axes.tick_params(axis="x", labelsize=8)
        upper = max(counts, default=0)
        y_offset = upper * 0.02 if upper > 0 else 0.0
        for idx, value in enumerate(counts):
            axes.text(idx, value + y_offset, f"{value:,}", ha="center", va="bottom", fontsize=8)
        for idx, artist in enumerate(bars, start=1):
            coverage_bar_artists.append((f"{panel['panel_id']}_{idx}", artist))

    fig.subplots_adjust(top=0.92, bottom=0.10, left=0.08, right=0.97)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=title_artist.get_window_extent(renderer=renderer),
            box_id="title",
            box_type="title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=center_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="center_event_y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=region_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="coverage_y_axis_title",
            box_type="y_axis_title",
        ),
    ]
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
                    bbox=center_axes.get_window_extent(renderer=renderer),
                    box_id="center_event_panel",
                    box_type="center_event_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=region_axes.get_window_extent(renderer=renderer),
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
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)


def _render_python_evidence_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    if template_id == "binary_calibration_decision_curve_panel":
        _render_python_binary_calibration_decision_curve_panel(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "model_complexity_audit_panel":
        _render_python_model_complexity_audit_panel(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "risk_layering_monotonic_bars":
        _render_python_risk_layering_monotonic_bars(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "shap_summary_beeswarm":
        _render_python_shap_summary_beeswarm(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "time_to_event_risk_group_summary":
        _render_python_time_to_event_risk_group_summary(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "time_to_event_decision_curve":
        _render_python_time_to_event_decision_curve(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "time_to_event_discrimination_calibration_panel":
        _render_python_time_to_event_discrimination_calibration_panel(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "multicenter_generalizability_overview":
        _render_python_multicenter_generalizability_overview(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    raise RuntimeError(f"unsupported python evidence template `{template_id}`")


def materialize_display_surface(*, paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    display_registry_payload = load_json(resolved_paper_root / "display_registry.json")
    figure_catalog = load_json(resolved_paper_root / "figures" / "figure_catalog.json")
    table_catalog = load_json(resolved_paper_root / "tables" / "table_catalog.json")
    style_profile: publication_display_contract.PublicationStyleProfile | None = None
    display_overrides: dict[tuple[str, str], publication_display_contract.DisplayOverride] | None = None

    figures_materialized: list[str] = []
    tables_materialized: list[str] = []
    written_files: list[str] = publication_display_contract.seed_publication_display_contracts_if_missing(
        paper_root=resolved_paper_root
    )

    for item in display_registry_payload.get("displays", []):
        if not isinstance(item, dict):
            raise ValueError("display_registry.json displays must contain objects")
        requirement_key = str(item.get("requirement_key") or "").strip()
        display_id = str(item.get("display_id") or "").strip()
        display_kind = str(item.get("display_kind") or "").strip()
        catalog_id = str(item.get("catalog_id") or "").strip()

        if requirement_key == "cohort_flow_figure":
            if display_kind != "figure":
                raise ValueError("cohort_flow_figure must be registered as a figure display")
            spec = display_registry.get_illustration_shell_spec("cohort_flow_figure")
            if style_profile is None:
                style_profile = publication_display_contract.load_publication_style_profile(
                    resolved_paper_root / "publication_style_profile.json"
                )
            if display_overrides is None:
                display_overrides = publication_display_contract.load_display_overrides(
                    resolved_paper_root / "display_overrides.json"
                )
            render_context = _build_render_context(
                style_profile=style_profile,
                display_overrides=display_overrides,
                display_id=display_id,
                template_id=spec.shell_id,
            )
            payload_path = resolved_paper_root / "cohort_flow.json"
            payload = load_json(payload_path)
            normalized_shell_payload = _validate_cohort_flow_payload(payload_path, payload)
            title = str(normalized_shell_payload.get("title") or "Cohort flow").strip() or "Cohort flow"
            figure_id = _resolve_figure_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_cohort_flow.svg"
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_cohort_flow.png"
            output_layout_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_cohort_flow.layout.json"
            _render_cohort_flow_figure(
                output_svg_path=output_svg_path,
                output_png_path=output_png_path,
                output_layout_path=output_layout_path,
                title=title,
                steps=list(normalized_shell_payload["steps"]),
                exclusions=list(normalized_shell_payload["exclusions"]),
                endpoint_inventory=list(normalized_shell_payload["endpoint_inventory"]),
                design_panels=list(normalized_shell_payload["design_panels"]),
                render_context=render_context,
            )
            layout_sidecar = load_json(output_layout_path)
            qc_result = display_layout_qc.run_display_layout_qc(
                qc_profile=spec.shell_qc_profile,
                layout_sidecar=layout_sidecar,
            )
            qc_result["layout_sidecar_path"] = _paper_relative_path(output_layout_path, paper_root=resolved_paper_root)
            written_files.extend([str(output_svg_path), str(output_png_path), str(output_layout_path)])
            entry = {
                "figure_id": figure_id,
                "template_id": spec.shell_id,
                "renderer_family": spec.renderer_family,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.shell_qc_profile,
                "qc_result": qc_result,
                "title": title,
                "caption": str(
                    normalized_shell_payload.get("caption") or "Study cohort flow and analysis population accounting."
                ).strip(),
                "export_paths": [
                    _paper_relative_path(output_svg_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
            }
            figure_catalog["figures"] = _replace_catalog_entry(
                list(figure_catalog.get("figures") or []),
                key="figure_id",
                value=figure_id,
                entry=entry,
            )
            figures_materialized.append(figure_id)
            continue

        if requirement_key == "table1_baseline_characteristics":
            if display_kind != "table":
                raise ValueError("table1_baseline_characteristics must be registered as a table display")
            spec = display_registry.get_table_shell_spec("table1_baseline_characteristics")
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            group_labels, rows = _validate_baseline_table_payload(payload_path, payload)
            title = str(payload.get("title") or "Baseline characteristics").strip() or "Baseline characteristics"
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.csv"
            output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.md"
            _write_table_outputs(
                output_md_path=output_md_path,
                title=title,
                column_labels=group_labels,
                rows=rows,
                stub_header="Characteristic",
                output_csv_path=output_csv_path,
            )
            written_files.extend([str(output_csv_path), str(output_md_path)])
            entry = {
                "table_id": table_id,
                "table_shell_id": spec.shell_id,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.table_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": title,
                "caption": str(payload.get("caption") or "Baseline characteristics across prespecified groups.").strip(),
                "asset_paths": [
                    _paper_relative_path(output_csv_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_md_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
            }
            table_catalog["tables"] = _replace_catalog_entry(
                list(table_catalog.get("tables") or []),
                key="table_id",
                value=table_id,
                entry=entry,
            )
            tables_materialized.append(table_id)
            continue

        if requirement_key in {
            "table2_time_to_event_performance_summary",
            "table3_clinical_interpretation_summary",
            "performance_summary_table_generic",
            "grouped_risk_event_summary_table",
        }:
            if display_kind != "table":
                raise ValueError(f"{requirement_key} must be registered as a table display")
            spec = display_registry.get_table_shell_spec(requirement_key)
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path: Path | None = None
            if requirement_key == "table2_time_to_event_performance_summary":
                column_labels, rows = _validate_column_table_payload(payload_path, payload)
                title = (
                    str(payload.get("title") or "Time-to-event model performance summary").strip()
                    or "Time-to-event model performance summary"
                )
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_time_to_event_performance_summary.md"
                stub_header = "Metric"
                default_caption = "Time-to-event discrimination and error metrics across analysis cohorts."
                _write_table_outputs(
                    output_md_path=output_md_path,
                    title=title,
                    column_labels=column_labels,
                    rows=rows,
                    stub_header=stub_header,
                )
            elif requirement_key == "table3_clinical_interpretation_summary":
                column_labels, rows = _validate_column_table_payload(payload_path, payload)
                title = str(payload.get("title") or "Clinical interpretation summary").strip() or "Clinical interpretation summary"
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_clinical_interpretation_summary.md"
                stub_header = "Clinical Item"
                default_caption = "Clinical interpretation anchors for prespecified risk groups and use cases."
                _write_table_outputs(
                    output_md_path=output_md_path,
                    title=title,
                    column_labels=column_labels,
                    rows=rows,
                    stub_header=stub_header,
                )
            elif requirement_key == "performance_summary_table_generic":
                row_header_label, column_labels, rows = _validate_performance_summary_table_generic_payload(
                    payload_path,
                    payload,
                )
                title = str(payload.get("title") or "Performance summary").strip() or "Performance summary"
                output_md_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.md"
                )
                output_csv_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.csv"
                )
                default_caption = "Structured repeated-validation performance summaries across candidate packages."
                _write_table_outputs(
                    output_md_path=output_md_path,
                    title=title,
                    column_labels=column_labels,
                    rows=rows,
                    stub_header=row_header_label,
                    output_csv_path=output_csv_path,
                )
            else:
                headers, table_rows = _validate_grouped_risk_event_summary_table_payload(payload_path, payload)
                title = str(payload.get("title") or "Grouped risk event summary").strip() or "Grouped risk event summary"
                output_md_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.md"
                )
                output_csv_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.csv"
                )
                default_caption = "Observed case counts, event counts, and absolute risks across grouped-risk strata."
                _write_rectangular_table_outputs(
                    output_md_path=output_md_path,
                    title=title,
                    headers=headers,
                    table_rows=table_rows,
                    output_csv_path=output_csv_path,
                )
            written_files.append(str(output_md_path))
            if output_csv_path is not None:
                written_files.append(str(output_csv_path))
            entry = {
                "table_id": table_id,
                "table_shell_id": spec.shell_id,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.table_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": title,
                "caption": str(payload.get("caption") or default_caption).strip(),
                "asset_paths": [
                    *(
                        [_paper_relative_path(output_csv_path, paper_root=resolved_paper_root)]
                        if output_csv_path is not None
                        else []
                    ),
                    _paper_relative_path(output_md_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
            }
            table_catalog["tables"] = _replace_catalog_entry(
                list(table_catalog.get("tables") or []),
                key="table_id",
                value=table_id,
                entry=entry,
            )
            tables_materialized.append(table_id)
            continue

        if display_kind == "figure" and display_registry.is_evidence_figure_template(requirement_key):
            spec = display_registry.get_evidence_figure_spec(requirement_key)
            if style_profile is None:
                style_profile = publication_display_contract.load_publication_style_profile(
                    resolved_paper_root / "publication_style_profile.json"
                )
            if display_overrides is None:
                display_overrides = publication_display_contract.load_display_overrides(
                    resolved_paper_root / "display_overrides.json"
                )
            figure_id = _resolve_figure_catalog_id(display_id=display_id, catalog_id=catalog_id)
            payload_path, display_payload = _load_evidence_display_payload(
                paper_root=resolved_paper_root,
                spec=spec,
                display_id=display_id,
            )
            render_context = _build_render_context(
                style_profile=style_profile,
                display_overrides=display_overrides,
                display_id=display_id,
                template_id=spec.template_id,
            )
            render_payload = dict(display_payload)
            render_payload["render_context"] = render_context
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{spec.template_id}.png"
            output_pdf_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{spec.template_id}.pdf"
            layout_sidecar_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{spec.template_id}.layout.json"
            if spec.renderer_family == "r_ggplot2":
                _render_r_evidence_figure(
                    template_id=spec.template_id,
                    display_payload=render_payload,
                    output_png_path=output_png_path,
                    output_pdf_path=output_pdf_path,
                    layout_sidecar_path=layout_sidecar_path,
                )
            elif spec.renderer_family == "python":
                _render_python_evidence_figure(
                    template_id=spec.template_id,
                    display_payload=render_payload,
                    output_png_path=output_png_path,
                    output_pdf_path=output_pdf_path,
                    layout_sidecar_path=layout_sidecar_path,
                )
            else:
                raise RuntimeError(
                    f"unsupported renderer_family `{spec.renderer_family}` for evidence template `{spec.template_id}`"
                )
            layout_sidecar = _load_layout_sidecar_or_raise(path=layout_sidecar_path, template_id=spec.template_id)
            layout_sidecar["render_context"] = render_context
            dump_json(layout_sidecar_path, layout_sidecar)
            qc_result = display_layout_qc.run_display_layout_qc(
                qc_profile=spec.layout_qc_profile,
                layout_sidecar=layout_sidecar,
            )
            qc_result["layout_sidecar_path"] = _paper_relative_path(layout_sidecar_path, paper_root=resolved_paper_root)
            written_files.extend([str(output_png_path), str(output_pdf_path), str(layout_sidecar_path)])
            paper_role = str(display_payload.get("paper_role") or spec.allowed_paper_roles[0]).strip()
            if paper_role not in spec.allowed_paper_roles:
                allowed_roles = ", ".join(spec.allowed_paper_roles)
                raise ValueError(
                    f"display `{display_id}` paper_role `{paper_role}` is not allowed for template `{spec.template_id}`; "
                    f"allowed: {allowed_roles}"
                )
            entry = {
                "figure_id": figure_id,
                "template_id": spec.template_id,
                "renderer_family": spec.renderer_family,
                "paper_role": paper_role,
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.layout_qc_profile,
                "qc_result": qc_result,
                "title": str(display_payload.get("title") or "").strip(),
                "caption": str(display_payload.get("caption") or "").strip(),
                "export_paths": [
                    _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_pdf_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
                "render_context": render_context,
            }
            figure_catalog["figures"] = _replace_catalog_entry(
                list(figure_catalog.get("figures") or []),
                key="figure_id",
                value=figure_id,
                entry=entry,
            )
            figures_materialized.append(figure_id)
            continue

    dump_json(resolved_paper_root / "figures" / "figure_catalog.json", figure_catalog)
    dump_json(resolved_paper_root / "tables" / "table_catalog.json", table_catalog)
    written_files.extend(
        [
            str(resolved_paper_root / "figures" / "figure_catalog.json"),
            str(resolved_paper_root / "tables" / "table_catalog.json"),
        ]
    )
    return {
        "status": "materialized",
        "paper_root": str(resolved_paper_root),
        "figures_materialized": figures_materialized,
        "tables_materialized": tables_materialized,
        "written_files": written_files,
    }
