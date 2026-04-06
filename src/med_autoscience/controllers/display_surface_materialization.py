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
import textwrap
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
    graphical_abstract_match = re.fullmatch(r"(?:GraphicalAbstract|GA)(\d+)", item, flags=re.IGNORECASE)
    if graphical_abstract_match:
        return f"GA{int(graphical_abstract_match.group(1))}"
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


def _collect_referenced_generated_surface_paths(
    *,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> set[str]:
    referenced_paths: set[str] = set()

    def maybe_add(path_value: object) -> None:
        normalized = str(path_value or "").strip()
        if not normalized.startswith("paper/") or "/generated/" not in normalized:
            return
        referenced_paths.add(normalized)

    for entry in figure_catalog.get("figures", []):
        if not isinstance(entry, dict):
            continue
        for export_path in entry.get("export_paths") or []:
            maybe_add(export_path)
        qc_result = entry.get("qc_result")
        if isinstance(qc_result, dict):
            maybe_add(qc_result.get("layout_sidecar_path"))

    for entry in table_catalog.get("tables", []):
        if not isinstance(entry, dict):
            continue
        for asset_path in entry.get("asset_paths") or []:
            maybe_add(asset_path)

    return referenced_paths


def _prune_unreferenced_generated_surface_outputs(
    *,
    paper_root: Path,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> list[str]:
    referenced_paths = _collect_referenced_generated_surface_paths(
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    )
    deleted_paths: list[str] = []
    generated_roots = (
        (paper_root / "figures" / "generated", {".png", ".pdf", ".svg", ".json"}),
        (paper_root / "tables" / "generated", {".csv", ".md"}),
    )
    for generated_root, allowed_suffixes in generated_roots:
        if not generated_root.exists():
            continue
        for candidate in sorted(generated_root.glob("*")):
            if not candidate.is_file() or candidate.suffix.lower() not in allowed_suffixes:
                continue
            relpath = f"paper/{candidate.relative_to(paper_root).as_posix()}"
            if relpath in referenced_paths:
                continue
            candidate.unlink()
            deleted_paths.append(relpath)
    return deleted_paths


def _build_paper_surface_readmes(
    *,
    paper_root: Path,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> dict[Path, str]:
    figure_ids = [
        str(entry.get("figure_id") or "").strip()
        for entry in figure_catalog.get("figures", [])
        if isinstance(entry, dict) and str(entry.get("figure_id") or "").strip()
    ]
    table_ids = [
        str(entry.get("table_id") or "").strip()
        for entry in table_catalog.get("tables", [])
        if isinstance(entry, dict) and str(entry.get("table_id") or "").strip()
    ]
    figure_id_line = ", ".join(figure_ids) if figure_ids else "(none materialized yet)"
    table_id_line = ", ".join(table_ids) if table_ids else "(none materialized yet)"
    return {
        paper_root / "README.md": textwrap.dedent(
            f"""\
            # Paper Authority Surface

            - This directory is the manuscript-facing authority surface for the active study line.
            - Figures: `paper/figures/figure_catalog.json` + `paper/figures/generated/`
            - Tables: `paper/tables/table_catalog.json` + `paper/tables/generated/`
            - Canonical submission package: `paper/submission_minimal/`
            - Human-facing delivery mirror: `../manuscript/final/`
            - Auxiliary finalize/runtime evidence only: `../artifacts/`

            If a human needs the latest authoritative display outputs, start here instead of `manuscript/` or `artifacts/`.
            """
        ),
        paper_root / "figures" / "README.md": textwrap.dedent(
            f"""\
            # Figure Authority Surface

            - Catalog contract: `paper/figures/figure_catalog.json`
            - Active rendered outputs: `paper/figures/generated/`
            - Current figure ids: {figure_id_line}

            Treat `figure_catalog.json` as the canonical routing/index surface. The files under `generated/` are the current paper-owned renders referenced by that catalog.
            """
        ),
        paper_root / "figures" / "generated" / "README.md": textwrap.dedent(
            f"""\
            # Generated Figure Outputs

            - Authority: `paper/figures/generated/`
            - Routed by: `paper/figures/figure_catalog.json`
            - Current figure ids: {figure_id_line}

            Every authoritative figure render for the active paper line lives here. Any unreferenced stale generated files are pruned during `materialize-display-surface`; use the catalog rather than guessing by filename age.
            """
        ),
        paper_root / "tables" / "README.md": textwrap.dedent(
            f"""\
            # Table Authority Surface

            - Catalog contract: `paper/tables/table_catalog.json`
            - Active rendered outputs: `paper/tables/generated/`
            - Current table ids: {table_id_line}

            Treat `table_catalog.json` as the canonical routing/index surface. The files under `generated/` are the current paper-owned table renders referenced by that catalog.
            """
        ),
        paper_root / "tables" / "generated" / "README.md": textwrap.dedent(
            f"""\
            # Generated Table Outputs

            - Authority: `paper/tables/generated/`
            - Routed by: `paper/tables/table_catalog.json`
            - Current table ids: {table_id_line}

            Every authoritative table render for the active paper line lives here. Any unreferenced stale generated files are pruned during `materialize-display-surface`; use the catalog rather than guessing by filename age.
            """
        ),
    }


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


def _require_probability_value(value: object, *, label: str) -> float:
    normalized = _require_numeric_value(value, label=label)
    if normalized < 0.0 or normalized > 1.0:
        raise ValueError(f"{label} must be a probability between 0 and 1")
    return normalized


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


def _validate_submission_graphical_abstract_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != "submission_graphical_abstract":
        raise ValueError(f"{path.name} shell_id must be `submission_graphical_abstract`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    catalog_id = _require_non_empty_string(payload.get("catalog_id"), label=f"{path.name} catalog_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")
    caption = _require_non_empty_string(payload.get("caption"), label=f"{path.name} caption")

    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} must contain a non-empty panels list")
    normalized_panels: list[dict[str, Any]] = []
    panel_ids: set[str] = set()
    for panel_index, panel in enumerate(panels_payload):
        if not isinstance(panel, dict):
            raise ValueError(f"{path.name} panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel.get("panel_id"),
            label=f"{path.name} panels[{panel_index}].panel_id",
        )
        if panel_id in panel_ids:
            raise ValueError(f"{path.name} panels[{panel_index}].panel_id must be unique")
        panel_ids.add(panel_id)
        rows_payload = panel.get("rows")
        if not isinstance(rows_payload, list) or not rows_payload:
            raise ValueError(f"{path.name} panels[{panel_index}].rows must be a non-empty list")
        normalized_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows_payload):
            if not isinstance(row, dict):
                raise ValueError(f"{path.name} panels[{panel_index}].rows[{row_index}] must be an object")
            cards_payload = row.get("cards")
            if not isinstance(cards_payload, list) or not cards_payload:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}].cards must be a non-empty list"
                )
            if len(cards_payload) > 2:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}] supports at most two cards"
                )
            normalized_cards: list[dict[str, Any]] = []
            card_ids: set[str] = set()
            for card_index, card in enumerate(cards_payload):
                if not isinstance(card, dict):
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}] must be an object"
                    )
                card_id = _require_non_empty_string(
                    card.get("card_id"),
                    label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id",
                )
                if card_id in card_ids:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id must be unique within the row"
                    )
                card_ids.add(card_id)
                accent_role = str(card.get("accent_role") or "neutral").strip().lower()
                if accent_role not in {"neutral", "primary", "secondary", "contrast", "audit"}:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].accent_role "
                        "must be one of neutral, primary, secondary, contrast, audit"
                    )
                normalized_cards.append(
                    {
                        "card_id": card_id,
                        "title": _require_non_empty_string(
                            card.get("title"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].title",
                        ),
                        "value": _require_non_empty_string(
                            card.get("value"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].value",
                        ),
                        "detail": str(card.get("detail") or "").strip(),
                        "accent_role": accent_role,
                    }
                )
            normalized_rows.append({"cards": normalized_cards})
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": _require_non_empty_string(
                    panel.get("panel_label"),
                    label=f"{path.name} panels[{panel_index}].panel_label",
                ),
                "title": _require_non_empty_string(
                    panel.get("title"),
                    label=f"{path.name} panels[{panel_index}].title",
                ),
                "subtitle": _require_non_empty_string(
                    panel.get("subtitle"),
                    label=f"{path.name} panels[{panel_index}].subtitle",
                ),
                "rows": normalized_rows,
            }
        )

    footer_pills_payload = payload.get("footer_pills") or []
    if not isinstance(footer_pills_payload, list):
        raise ValueError(f"{path.name} footer_pills must be a list when provided")
    normalized_footer_pills: list[dict[str, Any]] = []
    pill_ids: set[str] = set()
    for pill_index, pill in enumerate(footer_pills_payload):
        if not isinstance(pill, dict):
            raise ValueError(f"{path.name} footer_pills[{pill_index}] must be an object")
        pill_id = _require_non_empty_string(
            pill.get("pill_id"),
            label=f"{path.name} footer_pills[{pill_index}].pill_id",
        )
        if pill_id in pill_ids:
            raise ValueError(f"{path.name} footer_pills[{pill_index}].pill_id must be unique")
        pill_ids.add(pill_id)
        panel_id = _require_non_empty_string(
            pill.get("panel_id"),
            label=f"{path.name} footer_pills[{pill_index}].panel_id",
        )
        if panel_id not in panel_ids:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].panel_id must reference a declared panel"
            )
        style_role = str(pill.get("style_role") or "secondary").strip().lower()
        if style_role not in {"primary", "secondary", "contrast", "audit", "neutral"}:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].style_role must be one of primary, secondary, contrast, audit, neutral"
            )
        normalized_footer_pills.append(
            {
                "pill_id": pill_id,
                "panel_id": panel_id,
                "label": _require_non_empty_string(
                    pill.get("label"),
                    label=f"{path.name} footer_pills[{pill_index}].label",
                ),
                "style_role": style_role,
            }
        )

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "submission_companion").strip() or "submission_companion",
        "panels": normalized_panels,
        "footer_pills": normalized_footer_pills,
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
    require_probability_bounds: bool = False,
) -> dict[str, float] | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} {label} must be an object")
    reader = _require_probability_value if require_probability_bounds else _require_numeric_value
    xmin = reader(payload.get("xmin"), label=f"{path.name} {label}.xmin")
    xmax = reader(payload.get("xmax"), label=f"{path.name} {label}.xmax")
    ymin = reader(payload.get("ymin"), label=f"{path.name} {label}.ymin")
    ymax = reader(payload.get("ymax"), label=f"{path.name} {label}.ymax")
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
        require_probability_bounds=True,
    )
    if calibration_axis_window is None:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` calibration_axis_window must be declared for audited binary calibration panels"
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
    panel_a_title = _require_non_empty_string(
        payload.get("panel_a_title"),
        label=f"{path.name} display `{expected_display_id}` panel_a_title",
    )
    panel_b_title = _require_non_empty_string(
        payload.get("panel_b_title"),
        label=f"{path.name} display `{expected_display_id}` panel_b_title",
    )
    discrimination_x_label = _require_non_empty_string(
        payload.get("discrimination_x_label"),
        label=f"{path.name} display `{expected_display_id}` discrimination_x_label",
    )
    calibration_x_label = _require_non_empty_string(
        payload.get("calibration_x_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_x_label",
    )
    calibration_y_label = _require_non_empty_string(
        payload.get("calibration_y_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_y_label",
    )
    discrimination_points_payload = payload.get("discrimination_points")
    if not isinstance(discrimination_points_payload, list) or not discrimination_points_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty discrimination_points list"
        )
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(discrimination_points_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` discrimination_points[{index}] must be an object"
            )
        normalized_points.append(
            {
                "label": _require_non_empty_string(
                    item.get("label"),
                    label=f"{path.name} display `{expected_display_id}` discrimination_points[{index}].label",
                ),
                "c_index": _require_numeric_value(
                    item.get("c_index"),
                    label=f"{path.name} display `{expected_display_id}` discrimination_points[{index}].c_index",
                ),
                "annotation": str(item.get("annotation") or "").strip(),
            }
        )

    calibration_summary_payload = payload.get("calibration_summary")
    if not isinstance(calibration_summary_payload, list) or not calibration_summary_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty calibration_summary list"
        )
    normalized_summary: list[dict[str, Any]] = []
    previous_order = 0
    for index, item in enumerate(calibration_summary_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_summary[{index}] must be an object"
            )
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_summary[{index}].group_order "
                "must be strictly increasing"
            )
        previous_order = group_order
        normalized_summary.append(
            {
                "group_label": _require_non_empty_string(
                    item.get("group_label"),
                    label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].group_label",
                ),
                "group_order": group_order,
                "n": _require_non_negative_int(
                    item.get("n"),
                    label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].n",
                    allow_zero=False,
                ),
                "events_5y": _require_non_negative_int(
                    item.get("events_5y"),
                    label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].events_5y",
                ),
                "predicted_risk_5y": _require_probability_value(
                    item.get("predicted_risk_5y"),
                    label=(
                        f"{path.name} display `{expected_display_id}` calibration_summary[{index}].predicted_risk_5y"
                    ),
                ),
                "observed_risk_5y": _require_probability_value(
                    item.get("observed_risk_5y"),
                    label=(
                        f"{path.name} display `{expected_display_id}` calibration_summary[{index}].observed_risk_5y"
                    ),
                ),
            }
        )

    calibration_callout_payload = payload.get("calibration_callout")
    normalized_callout: dict[str, Any] | None = None
    if calibration_callout_payload is not None:
        if not isinstance(calibration_callout_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_callout must be an object when provided"
            )
        normalized_callout = {
            "group_label": _require_non_empty_string(
                calibration_callout_payload.get("group_label"),
                label=f"{path.name} display `{expected_display_id}` calibration_callout.group_label",
            ),
            "predicted_risk_5y": _require_probability_value(
                calibration_callout_payload.get("predicted_risk_5y"),
                label=f"{path.name} display `{expected_display_id}` calibration_callout.predicted_risk_5y",
            ),
            "observed_risk_5y": _require_probability_value(
                calibration_callout_payload.get("observed_risk_5y"),
                label=f"{path.name} display `{expected_display_id}` calibration_callout.observed_risk_5y",
            ),
            "events_5y": (
                _require_non_negative_int(
                    calibration_callout_payload.get("events_5y"),
                    label=f"{path.name} display `{expected_display_id}` calibration_callout.events_5y",
                )
                if calibration_callout_payload.get("events_5y") is not None
                else None
            ),
            "n": (
                _require_non_negative_int(
                    calibration_callout_payload.get("n"),
                    label=f"{path.name} display `{expected_display_id}` calibration_callout.n",
                    allow_zero=False,
                )
                if calibration_callout_payload.get("n") is not None
                else None
            ),
        }

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_a_title": panel_a_title,
        "panel_b_title": panel_b_title,
        "discrimination_x_label": discrimination_x_label,
        "calibration_x_label": calibration_x_label,
        "calibration_y_label": calibration_y_label,
        "discrimination_points": normalized_points,
        "calibration_summary": normalized_summary,
        "calibration_callout": normalized_callout,
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
    max_chars: int | None = None,
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
    if max_chars is None or max_chars <= 0:
        return tuple(lines)
    normalized_lines: list[str] = []
    for line in lines:
        if len(line) <= max_chars:
            normalized_lines.append(line)
            continue
        normalized_lines.extend(
            textwrap.wrap(
                line,
                width=max_chars,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
    return tuple(normalized_lines)


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
    step_padding_pt = read_float(layout_override, "flow_step_padding_pt", 11.0)
    exclusion_padding_pt = read_float(layout_override, "flow_exclusion_padding_pt", 8.0)
    hierarchy_padding_pt = read_float(layout_override, "hierarchy_panel_padding_pt", 9.0)
    step_min_rendered_height_pt = read_float(layout_override, "flow_step_min_rendered_height_pt", 82.0)
    exclusion_min_rendered_height_pt = read_float(layout_override, "flow_exclusion_min_rendered_height_pt", 58.0)
    step_min_rendered_padding_pt = read_float(layout_override, "flow_step_min_rendered_padding_pt", 8.0)
    exclusion_min_rendered_padding_pt = read_float(layout_override, "flow_exclusion_min_rendered_padding_pt", 6.0)

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
            max_chars=36,
        )
        detail_lines = _wrap_flow_text_to_width(
            str(step.get("detail") or ""),
            max_width_pt=content_width_pt,
            font_size=base_detail_size,
            font_weight="normal",
            max_chars=44,
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
                gap_before=14.0,
            ),
        ]
        lines.extend(
            _FlowTextLine(
                text=line,
                font_size=base_detail_size,
                font_weight="normal",
                color=flow_body_text,
                gap_before=12.0 if index == 0 else 0.0,
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
            max_chars=40,
        )
        detail_lines = _wrap_flow_text_to_width(
            str(exclusion.get("detail") or ""),
            max_width_pt=content_width_pt,
            font_size=base_detail_size,
            font_weight="normal",
            max_chars=44,
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
                gap_before=8.0 if index == 0 else 0.0,
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

    def rendered_padding_for_spec(spec: _FlowNodeSpec) -> float:
        scaled_padding = spec.padding_pt * scale
        if spec.box_type == "main_step":
            return max(scaled_padding, step_min_rendered_padding_pt)
        if spec.box_type == "exclusion_box":
            return max(scaled_padding, exclusion_min_rendered_padding_pt)
        return scaled_padding

    def rendered_height_for_spec(spec: _FlowNodeSpec) -> float:
        height = rendered_padding_for_spec(spec) * 2.0
        for line in spec.lines:
            height += line.gap_before * scale
            height += line.font_size * scale * 1.24
        if spec.box_type == "main_step":
            return max(height, step_min_rendered_height_pt)
        if spec.box_type == "exclusion_box":
            return max(height, exclusion_min_rendered_height_pt)
        return height

    rendered_step_heights_pt = {spec.node_id: rendered_height_for_spec(spec) for spec in step_specs}
    rendered_exclusion_heights_pt = {
        spec.node_id: rendered_height_for_spec(spec) for spec in exclusion_specs.values()
    }
    rendered_step_stack_gap_pt: dict[str, float] = {}
    rendered_stage_cluster_heights_pt: dict[str, float] = {}
    panel_a_rendered_height_pt = 0.0
    rendered_flow_step_gap_pt = flow_step_gap_pt * scale
    rendered_flow_exclusion_stack_gap_pt = flow_exclusion_stack_gap_pt * scale
    rendered_flow_split_clearance_pt = flow_split_clearance_pt * scale
    for index, step in enumerate(steps):
        step_id = str(step["step_id"])
        panel_a_rendered_height_pt += rendered_step_heights_pt[f"step_{step_id}"]
        if index == len(steps) - 1:
            continue
        related_exclusions = exclusions_by_step.get(step_id, [])
        cluster_height_pt = 0.0
        if related_exclusions:
            cluster_height_pt = sum(
                rendered_exclusion_heights_pt[f"exclusion_{item['exclusion_id']}"] for item in related_exclusions
            ) + rendered_flow_exclusion_stack_gap_pt * max(0, len(related_exclusions) - 1)
        gap_height_pt = max(
            rendered_flow_step_gap_pt,
            cluster_height_pt + rendered_flow_split_clearance_pt * 2.0,
        )
        rendered_step_stack_gap_pt[step_id] = gap_height_pt
        rendered_stage_cluster_heights_pt[step_id] = cluster_height_pt
        panel_a_rendered_height_pt += gap_height_pt

    content_height_pt = max(panel_a_rendered_height_pt, panel_b_total_base_height * scale)
    canvas_height_pt = bottom_margin_pt + content_height_pt + heading_band_pt

    fig = plt.figure(figsize=(figure_width_pt / 72.0, canvas_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    panel_a_x0 = side_margin_pt
    panel_a_y0 = bottom_margin_pt + content_height_pt - panel_a_rendered_height_pt
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
        rendered_padding_pt = rendered_padding_for_spec(spec)
        x_text = box["x0"] + rendered_padding_pt
        y_cursor = box["y1"] - rendered_padding_pt
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
    panel_a_top = panel_a_y0 + panel_a_rendered_height_pt
    current_top = panel_a_top
    exclusion_x0 = panel_a_x0 + (step_width_pt + branch_gap_pt) * scale

    for index, spec in enumerate(step_specs):
        step_height_pt = rendered_step_heights_pt[spec.node_id]
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
        stage_gap_pt = rendered_step_stack_gap_pt[step_id]
        stage_split_y = box["y0"] - stage_gap_pt / 2.0
        stage_split_y_by_step[step_id] = stage_split_y
        related_exclusions = exclusions_by_step.get(step_id, [])
        if related_exclusions:
            cluster_height_pt = rendered_stage_cluster_heights_pt[step_id]
            cluster_top = stage_split_y + cluster_height_pt / 2.0
            for exclusion in related_exclusions:
                exclusion_spec = exclusion_specs[str(exclusion["exclusion_id"])]
                exclusion_height_pt = rendered_exclusion_heights_pt[exclusion_spec.node_id]
                exclusion_box = {
                    "x0": exclusion_x0,
                    "y0": cluster_top - exclusion_height_pt,
                    "x1": exclusion_x0 + exclusion_spec.width_pt * scale,
                    "y1": cluster_top,
                }
                cluster_top = exclusion_box["y0"] - rendered_flow_exclusion_stack_gap_pt
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
    flow_nodes = []
    for spec in step_specs:
        box = step_boxes_by_id.get(spec.node_id)
        if box is None:
            continue
        flow_nodes.append(
            {
                "box_id": spec.box_id,
                "box_type": spec.box_type,
                "line_count": len(spec.lines),
                "max_line_chars": max((len(line.text) for line in spec.lines), default=0),
                "rendered_height_pt": box["y1"] - box["y0"],
                "rendered_width_pt": box["x1"] - box["x0"],
                "padding_pt": rendered_padding_for_spec(spec),
            }
        )
    for spec in exclusion_specs.values():
        box = exclusion_boxes_by_id.get(spec.node_id)
        if box is None:
            continue
        flow_nodes.append(
            {
                "box_id": spec.box_id,
                "box_type": spec.box_type,
                "line_count": len(spec.lines),
                "max_line_chars": max((len(line.text) for line in spec.lines), default=0),
                "rendered_height_pt": box["y1"] - box["y0"],
                "rendered_width_pt": box["x1"] - box["x0"],
                "padding_pt": rendered_padding_for_spec(spec),
            }
        )
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
                "flow_nodes": flow_nodes,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=220)
    plt.close(fig)


def _build_submission_graphical_abstract_arrow_lane_spec(
    *,
    left_panel_box: dict[str, float],
    right_panel_box: dict[str, float],
    left_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    right_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    clearance_pt: float,
    arrow_half_height_pt: float,
    edge_proximity_pt: float | None = None,
) -> dict[str, Any]:
    def _collect_expanded_intervals(boxes: list[dict[str, float]] | tuple[dict[str, float], ...]) -> list[tuple[float, float]]:
        intervals: list[tuple[float, float]] = []
        expansion = max(clearance_pt + arrow_half_height_pt, 0.0)
        for box in boxes:
            lower = max(shared_y0, float(box["y0"]) - expansion)
            upper = min(shared_y1, float(box["y1"]) + expansion)
            if upper <= lower:
                continue
            intervals.append((lower, upper))
        intervals.sort()
        return intervals

    def _merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if not intervals:
            return []
        merged: list[list[float]] = [[intervals[0][0], intervals[0][1]]]
        for lower, upper in intervals[1:]:
            current = merged[-1]
            if lower <= current[1]:
                current[1] = max(current[1], upper)
                continue
            merged.append([lower, upper])
        return [(float(lower), float(upper)) for lower, upper in merged]

    shared_y0 = max(float(left_panel_box["y0"]), float(right_panel_box["y0"]))
    shared_y1 = min(float(left_panel_box["y1"]), float(right_panel_box["y1"]))
    if shared_y1 <= shared_y0:
        raise ValueError("submission_graphical_abstract panels must share a vertical overlap to place arrows")

    merged_occupied_intervals = _merge_intervals(
        _collect_expanded_intervals(left_occupied_boxes) + _collect_expanded_intervals(right_occupied_boxes)
    )
    candidate_gaps: list[tuple[float, float]] = []
    cursor = shared_y0
    for lower, upper in merged_occupied_intervals:
        if lower > cursor:
            candidate_gaps.append((cursor, lower))
        cursor = max(cursor, upper)
    if cursor < shared_y1:
        candidate_gaps.append((cursor, shared_y1))

    target_y = (shared_y0 + shared_y1) / 2.0
    left_span_y0 = min((float(box["y0"]) for box in left_occupied_boxes), default=shared_y0)
    right_span_y0 = min((float(box["y0"]) for box in right_occupied_boxes), default=shared_y0)
    left_span_y1 = max((float(box["y1"]) for box in left_occupied_boxes), default=shared_y1)
    right_span_y1 = max((float(box["y1"]) for box in right_occupied_boxes), default=shared_y1)
    shared_content_y0 = max(shared_y0, left_span_y0, right_span_y0)
    shared_content_y1 = min(shared_y1, left_span_y1, right_span_y1)
    if shared_content_y1 > shared_content_y0:
        target_y = (shared_content_y0 + shared_content_y1) / 2.0

    lane_margin = max(arrow_half_height_pt, 0.0)
    edge_margin = max(edge_proximity_pt or 0.0, 0.0)
    usable_gaps: list[tuple[float, float]] = []
    for lower, upper in candidate_gaps:
        usable_lower = max(lower, shared_y0 + lane_margin)
        usable_upper = min(upper, shared_y1 - lane_margin)
        if edge_margin > 0.0:
            usable_lower = max(usable_lower, shared_y0 + edge_margin)
            usable_upper = min(usable_upper, shared_y1 - edge_margin)
        if usable_upper <= usable_lower:
            continue
        usable_gaps.append((usable_lower, usable_upper))

    if not usable_gaps:
        lower_bound = shared_y0 + lane_margin
        upper_bound = shared_y1 - lane_margin
        if lower_bound > upper_bound:
            lower_bound = upper_bound = (shared_y0 + shared_y1) / 2.0
        usable_gaps = [(lower_bound, upper_bound)]

    return {
        "target_y": float(target_y),
        "usable_gaps": [(float(lower), float(upper)) for lower, upper in usable_gaps],
    }


def _choose_submission_graphical_abstract_arrow_lane(
    *,
    left_panel_box: dict[str, float],
    right_panel_box: dict[str, float],
    left_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    right_occupied_boxes: list[dict[str, float]] | tuple[dict[str, float], ...],
    clearance_pt: float,
    arrow_half_height_pt: float,
    edge_proximity_pt: float | None = None,
) -> float:
    lane_spec = _build_submission_graphical_abstract_arrow_lane_spec(
        left_panel_box=left_panel_box,
        right_panel_box=right_panel_box,
        left_occupied_boxes=left_occupied_boxes,
        right_occupied_boxes=right_occupied_boxes,
        clearance_pt=clearance_pt,
        arrow_half_height_pt=arrow_half_height_pt,
        edge_proximity_pt=edge_proximity_pt,
    )
    usable_gaps = list(lane_spec["usable_gaps"])
    target_y = float(lane_spec["target_y"])

    for lower, upper in usable_gaps:
        if lower <= target_y <= upper:
            return target_y
    best_lower, best_upper = min(
        usable_gaps,
        key=lambda gap: abs(((gap[0] + gap[1]) / 2.0) - target_y),
    )
    return (best_lower + best_upper) / 2.0


def _choose_shared_submission_graphical_abstract_arrow_lane(
    lane_specs: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> float:
    normalized_specs = [dict(spec) for spec in lane_specs if isinstance(spec, dict)]
    if not normalized_specs:
        raise ValueError("submission_graphical_abstract requires at least one adjacent panel pair")

    shared_intervals = [tuple(interval) for interval in normalized_specs[0]["usable_gaps"]]
    for spec in normalized_specs[1:]:
        next_intersection: list[tuple[float, float]] = []
        for current_lower, current_upper in shared_intervals:
            for candidate_lower, candidate_upper in spec["usable_gaps"]:
                overlap_lower = max(float(current_lower), float(candidate_lower))
                overlap_upper = min(float(current_upper), float(candidate_upper))
                if overlap_upper <= overlap_lower:
                    continue
                next_intersection.append((overlap_lower, overlap_upper))
        shared_intervals = next_intersection
        if not shared_intervals:
            break

    if not shared_intervals:
        raise ValueError(
            "submission_graphical_abstract arrows require a shared blank lane across all adjacent panel pairs"
        )

    target_y = sum(float(spec["target_y"]) for spec in normalized_specs) / len(normalized_specs)
    for lower, upper in shared_intervals:
        if lower <= target_y <= upper:
            return target_y
    best_lower, best_upper = min(
        shared_intervals,
        key=lambda gap: abs(((gap[0] + gap[1]) / 2.0) - target_y),
    )
    return (best_lower + best_upper) / 2.0


def _render_submission_graphical_abstract(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
) -> None:
    def read_float(mapping: dict[str, Any], key: str, default: float) -> float:
        value = mapping.get(key, default)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(default)

    def resolve_color(role_name: str, fallback: str) -> str:
        return str(style_roles.get(role_name) or fallback).strip() or fallback

    def fit_wrapped_text(
        text: str,
        *,
        preferred: float,
        min_size: float,
        max_width_pt: float,
        font_weight: str,
        max_lines: int,
    ) -> tuple[tuple[str, ...], float, bool]:
        normalized = " ".join(str(text or "").split())
        if not normalized:
            return tuple(), preferred, False
        font_size = preferred
        while font_size >= min_size - 1e-6:
            lines = _wrap_flow_text_to_width(
                normalized,
                max_width_pt=max_width_pt,
                font_size=font_size,
                font_weight=font_weight,
            )
            widest_line_pt = max(
                (
                    _measure_flow_text_width_pt(line, font_size=font_size, font_weight=font_weight)
                    for line in lines
                ),
                default=0.0,
            )
            if len(lines) <= max_lines and widest_line_pt <= max_width_pt + 0.1:
                return lines, font_size, False
            font_size -= 0.5
        resolved_font_size = max(min_size, 1.0)
        resolved_lines = _wrap_flow_text_to_width(
            normalized,
            max_width_pt=max_width_pt,
            font_size=resolved_font_size,
            font_weight=font_weight,
        )
        widest_line_pt = max(
            (
                _measure_flow_text_width_pt(line, font_size=resolved_font_size, font_weight=font_weight)
                for line in resolved_lines
            ),
            default=0.0,
        )
        overflowed = len(resolved_lines) > max_lines or widest_line_pt > max_width_pt + 0.1
        return resolved_lines, resolved_font_size, overflowed

    def text_block_height(lines: tuple[str, ...], *, font_size: float, extra_gap: float = 0.0) -> float:
        if not lines:
            return 0.0
        return len(lines) * font_size * 1.22 + extra_gap

    def row_width_weights(cards: list[dict[str, Any]]) -> list[float]:
        if len(cards) <= 1:
            return [1.0]
        first_score = max(
            len(str(cards[0]["title"])),
            len(str(cards[0]["detail"])),
            int(len(str(cards[0]["value"])) * 1.2),
        )
        second_score = max(
            len(str(cards[1]["title"])),
            len(str(cards[1]["detail"])),
            int(len(str(cards[1]["value"])) * 1.2),
        )
        total = max(float(first_score + second_score), 1.0)
        first_ratio = min(0.66, max(0.42, first_score / total))
        return [first_ratio, 1.0 - first_ratio]

    render_context_payload = dict(render_context or {})
    style_roles = dict(render_context_payload.get("style_roles") or {})
    palette = dict(render_context_payload.get("palette") or {})
    typography = dict(render_context_payload.get("typography") or {})
    layout_override = dict(render_context_payload.get("layout_override") or {})
    stroke = dict(render_context_payload.get("stroke") or {})

    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )

    neutral_color = resolve_color("reference_line", str(palette.get("neutral") or "#7B8794"))
    primary_color = resolve_color("model_curve", str(palette.get("primary") or "#5F766B"))
    secondary_color = resolve_color("comparator_curve", str(palette.get("secondary") or "#B9AD9C"))
    contrast_color = str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A"
    audit_color = str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F"
    soft_fill_by_role = {
        "neutral": str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8",
        "primary": str(palette.get("primary_soft") or "#EEF3F1").strip() or "#EEF3F1",
        "secondary": str(palette.get("secondary_soft") or "#F4EFE8").strip() or "#F4EFE8",
        "contrast": str(palette.get("contrast_soft") or "#E6EDF5").strip() or "#E6EDF5",
        "audit": str(palette.get("audit_soft") or "#F5ECE8").strip() or "#F5ECE8",
    }
    edge_by_role = {
        "neutral": neutral_color,
        "primary": primary_color,
        "secondary": secondary_color,
        "contrast": contrast_color,
        "audit": audit_color,
    }

    title_size = read_float(typography, "title_size", 12.5) + 1.0
    panel_title_size = read_float(typography, "axis_title_size", 11.0) + 1.2
    subtitle_size = max(10.0, read_float(typography, "tick_size", 10.0) + 0.1)
    card_title_size = max(10.0, read_float(typography, "tick_size", 10.0) + 0.6)
    card_detail_size = max(8.8, read_float(typography, "tick_size", 10.0) - 0.4)
    panel_label_size = max(11.2, read_float(typography, "panel_label_size", 11.0) + 0.6)
    value_font_preferred = max(20.0, read_float(typography, "title_size", 12.5) * 2.35)
    value_font_min = max(14.0, read_float(typography, "axis_title_size", 11.0) + 3.0)

    figure_width_pt = read_float(layout_override, "figure_width", 15.4) * 72.0
    side_margin_pt = read_float(layout_override, "figure_side_margin_pt", 30.0)
    panel_gap_pt = read_float(layout_override, "panel_gap_pt", 24.0)
    panel_padding_pt = read_float(layout_override, "panel_padding_pt", 18.0)
    card_padding_pt = read_float(layout_override, "card_padding_pt", 14.0)
    card_gap_pt = read_float(layout_override, "card_gap_pt", 12.0)
    row_gap_pt = read_float(layout_override, "row_gap_pt", 12.0)
    footer_gap_pt = read_float(layout_override, "footer_gap_pt", 16.0)
    footer_pill_height_pt = read_float(layout_override, "footer_pill_height_pt", 28.0)
    top_margin_pt = read_float(layout_override, "top_margin_pt", 22.0)
    title_gap_pt = read_float(layout_override, "title_gap_pt", 16.0)
    bottom_margin_pt = read_float(layout_override, "bottom_margin_pt", 22.0)
    panel_line_width = max(0.9, read_float(stroke, "secondary_linewidth", 1.8) * 0.75)
    accent_line_width = max(1.0, read_float(stroke, "primary_linewidth", 2.2) * 0.58)

    panels_payload = list(shell_payload.get("panels") or [])
    footer_pills = list(shell_payload.get("footer_pills") or [])
    panel_width_pt = (figure_width_pt - side_margin_pt * 2.0 - panel_gap_pt * 2.0) / 3.0
    card_full_width_pt = panel_width_pt - panel_padding_pt * 2.0

    def build_card_spec(
        card: dict[str, Any],
        *,
        available_width_pt: float,
        max_value_lines: int,
    ) -> dict[str, Any]:
        inner_width_pt = max(available_width_pt - card_padding_pt * 2.0, 1.0)
        title_lines = _wrap_flow_text_to_width(
            str(card["title"]),
            max_width_pt=inner_width_pt,
            font_size=card_title_size,
            font_weight="normal",
        )
        detail_lines = _wrap_flow_text_to_width(
            str(card.get("detail") or ""),
            max_width_pt=inner_width_pt,
            font_size=card_detail_size,
            font_weight="normal",
        )
        value_lines, value_font_size, value_overflowed = fit_wrapped_text(
            str(card["value"]),
            preferred=value_font_preferred,
            min_size=value_font_min,
            max_width_pt=inner_width_pt,
            font_weight="bold",
            max_lines=max_value_lines,
        )
        title_height_pt = text_block_height(title_lines, font_size=card_title_size, extra_gap=5.0)
        value_height_pt = text_block_height(value_lines, font_size=value_font_size, extra_gap=0.0)
        detail_height_pt = text_block_height(detail_lines, font_size=card_detail_size, extra_gap=0.0)
        card_height_pt = card_padding_pt * 2.0 + title_height_pt + value_height_pt
        if detail_lines:
            card_height_pt += 7.0 + detail_height_pt
        return {
            "card": card,
            "width_pt": available_width_pt,
            "height_pt": card_height_pt,
            "title_lines": title_lines,
            "detail_lines": detail_lines,
            "value_lines": value_lines,
            "value_font_size": value_font_size,
            "overflowed": value_overflowed,
        }

    def build_row_spec(cards: list[dict[str, Any]]) -> dict[str, Any]:
        if len(cards) == 1:
            row_card_specs = [
                build_card_spec(
                    cards[0],
                    available_width_pt=card_full_width_pt,
                    max_value_lines=3,
                )
            ]
            return {
                "layout_mode": "single",
                "cards": row_card_specs,
                "height_pt": row_card_specs[0]["height_pt"],
                "row_internal_gap_pt": 0.0,
            }

        weights = row_width_weights(cards)
        horizontal_widths = [
            card_full_width_pt * weights[index] - card_gap_pt / 2.0
            for index in range(len(cards))
        ]
        horizontal_specs = [
            build_card_spec(card, available_width_pt=horizontal_widths[index], max_value_lines=2)
            for index, card in enumerate(cards)
        ]
        if not any(card_spec["overflowed"] for card_spec in horizontal_specs):
            return {
                "layout_mode": "horizontal",
                "cards": horizontal_specs,
                "height_pt": max(card_spec["height_pt"] for card_spec in horizontal_specs),
                "row_internal_gap_pt": card_gap_pt,
            }

        stacked_specs = [
            build_card_spec(card, available_width_pt=card_full_width_pt, max_value_lines=3)
            for card in cards
        ]
        stacked_overflow_ids = [str(spec["card"]["card_id"]) for spec in stacked_specs if spec["overflowed"]]
        if stacked_overflow_ids:
            joined_ids = ", ".join(stacked_overflow_ids)
            raise ValueError(
                "submission_graphical_abstract could not fit the following card values even after stacked layout: "
                f"{joined_ids}"
            )
        return {
            "layout_mode": "stacked",
            "cards": stacked_specs,
            "height_pt": (
                sum(card_spec["height_pt"] for card_spec in stacked_specs)
                + card_gap_pt * max(0, len(stacked_specs) - 1)
            ),
            "row_internal_gap_pt": card_gap_pt,
        }

    panel_specs: list[dict[str, Any]] = []
    for panel in panels_payload:
        panel_title_lines = _wrap_flow_text_to_width(
            str(panel["title"]),
            max_width_pt=panel_width_pt - panel_padding_pt * 2.0 - 32.0,
            font_size=panel_title_size,
            font_weight="bold",
        )
        subtitle_lines = _wrap_flow_text_to_width(
            str(panel["subtitle"]),
            max_width_pt=panel_width_pt - panel_padding_pt * 2.0,
            font_size=subtitle_size,
            font_weight="normal",
        )
        header_height_pt = text_block_height(panel_title_lines, font_size=panel_title_size, extra_gap=6.0)
        header_height_pt += text_block_height(subtitle_lines, font_size=subtitle_size, extra_gap=10.0)
        row_specs: list[dict[str, Any]] = []
        for row in panel["rows"]:
            row_specs.append(build_row_spec(list(row["cards"])))
        content_height_pt = header_height_pt
        if row_specs:
            content_height_pt += sum(item["height_pt"] for item in row_specs) + row_gap_pt * max(0, len(row_specs) - 1)
        panel_specs.append(
            {
                "panel": panel,
                "panel_title_lines": panel_title_lines,
                "subtitle_lines": subtitle_lines,
                "header_height_pt": header_height_pt,
                "row_specs": row_specs,
                "content_height_pt": content_height_pt,
            }
        )

    panel_height_pt = max(spec["content_height_pt"] for spec in panel_specs) + panel_padding_pt * 2.0
    title_text, title_line_count = _wrap_figure_title_to_width(
        str(shell_payload.get("title") or "").strip(),
        max_width_pt=figure_width_pt - side_margin_pt * 2.0,
        font_size=title_size,
    )
    title_height_pt = max(title_line_count, 1) * title_size * 1.18
    canvas_height_pt = (
        top_margin_pt
        + title_height_pt
        + title_gap_pt
        + panel_height_pt
        + footer_gap_pt
        + footer_pill_height_pt
        + bottom_margin_pt
    )

    fig = plt.figure(figsize=(figure_width_pt / 72.0, canvas_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    title_artist = ax.text(
        side_margin_pt,
        canvas_height_pt - top_margin_pt,
        title_text,
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    panel_y0 = bottom_margin_pt + footer_pill_height_pt + footer_gap_pt
    footer_y0 = bottom_margin_pt
    text_layout_records: list[tuple[Any, str, str]] = [(title_artist, "title", "title")]
    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    panel_regions: dict[str, dict[str, float]] = {}
    panel_occupied_regions: dict[str, list[dict[str, float]]] = {}
    arrow_artists: list[tuple[str, Any]] = []

    def add_text_box(artist: Any, *, box_id: str, box_type: str) -> None:
        text_layout_records.append((artist, box_id, box_type))

    def draw_graphical_abstract_card(*, panel_id: str, card_spec: dict[str, Any], card_box: dict[str, float]) -> None:
        card = dict(card_spec["card"])
        accent_role = str(card.get("accent_role") or "neutral").strip().lower()
        ax.add_patch(
            FancyBboxPatch(
                (card_box["x0"], card_box["y0"]),
                card_box["x1"] - card_box["x0"],
                card_box["y1"] - card_box["y0"],
                boxstyle="round,pad=0.0,rounding_size=14",
                linewidth=max(0.9, accent_line_width),
                edgecolor=edge_by_role.get(accent_role, neutral_color),
                facecolor=soft_fill_by_role.get(accent_role, soft_fill_by_role["neutral"]),
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                **card_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"{panel_id}_{card['card_id']}",
                box_type="card_box",
            )
        )
        text_x = card_box["x0"] + card_padding_pt
        y_cursor = card_box["y1"] - card_padding_pt
        title_artist = ax.text(
            text_x,
            y_cursor,
            "\n".join(card_spec["title_lines"]),
            fontsize=card_title_size,
            fontweight="normal",
            color=neutral_color,
            ha="left",
            va="top",
        )
        add_text_box(title_artist, box_id=f"{panel_id}_{card['card_id']}_title", box_type="card_title")
        y_cursor -= text_block_height(card_spec["title_lines"], font_size=card_title_size, extra_gap=4.0)
        value_artist = ax.text(
            text_x,
            y_cursor,
            "\n".join(card_spec["value_lines"]),
            fontsize=card_spec["value_font_size"],
            fontweight="bold",
            color=edge_by_role.get(accent_role, neutral_color),
            ha="left",
            va="top",
        )
        add_text_box(value_artist, box_id=f"{panel_id}_{card['card_id']}_value", box_type="card_value")
        y_cursor -= text_block_height(card_spec["value_lines"], font_size=card_spec["value_font_size"], extra_gap=0.0)
        if card_spec["detail_lines"]:
            y_cursor -= 7.0
            detail_artist = ax.text(
                text_x,
                y_cursor,
                "\n".join(card_spec["detail_lines"]),
                fontsize=card_detail_size,
                fontweight="normal",
                color=neutral_color,
                ha="left",
                va="top",
            )
            add_text_box(
                detail_artist,
                box_id=f"{panel_id}_{card['card_id']}_detail",
                box_type="card_detail",
            )

    for panel_index, panel_spec in enumerate(panel_specs):
        panel = dict(panel_spec["panel"])
        panel_x0 = side_margin_pt + panel_index * (panel_width_pt + panel_gap_pt)
        panel_box = {
            "x0": panel_x0,
            "y0": panel_y0,
            "x1": panel_x0 + panel_width_pt,
            "y1": panel_y0 + panel_height_pt,
        }
        panel_regions[str(panel["panel_id"])] = panel_box
        panel_occupied_regions[str(panel["panel_id"])] = []
        panel_fill = str(palette.get("secondary_soft") or palette.get("light") or "#F4EFE8").strip() or "#F4EFE8"
        ax.add_patch(
            FancyBboxPatch(
                (panel_box["x0"], panel_box["y0"]),
                panel_width_pt,
                panel_height_pt,
                boxstyle="round,pad=0.0,rounding_size=18",
                linewidth=panel_line_width,
                edgecolor=neutral_color,
                facecolor=panel_fill,
            )
        )
        panel_boxes.append(
            _flow_box_to_normalized(
                **panel_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_{panel['panel_id']}",
                box_type="panel",
            )
        )

        label_center_x = panel_box["x0"] + panel_padding_pt + 14.0
        label_center_y = panel_box["y1"] - panel_padding_pt - 14.0
        label_radius = 14.0
        ax.add_patch(
            matplotlib.patches.Circle(
                (label_center_x, label_center_y),
                radius=label_radius,
                facecolor="white",
                edgecolor=neutral_color,
                linewidth=max(0.9, panel_line_width * 0.9),
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                x0=label_center_x - label_radius,
                y0=label_center_y - label_radius,
                x1=label_center_x + label_radius,
                y1=label_center_y + label_radius,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_label_{panel['panel_label']}",
                box_type="panel_label",
            )
        )
        label_artist = ax.text(
            label_center_x,
            label_center_y,
            str(panel["panel_label"]),
            fontsize=panel_label_size,
            fontweight="bold",
            color=neutral_color,
            ha="center",
            va="center",
        )
        add_text_box(label_artist, box_id=f"panel_label_text_{panel['panel_label']}", box_type="panel_label_text")

        title_x = label_center_x + label_radius + 10.0
        title_y = panel_box["y1"] - panel_padding_pt
        panel_title_artist = ax.text(
            title_x,
            title_y,
            "\n".join(panel_spec["panel_title_lines"]),
            fontsize=panel_title_size,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )
        add_text_box(panel_title_artist, box_id=f"{panel['panel_id']}_title", box_type="panel_title")
        panel_title_height_pt = text_block_height(panel_spec["panel_title_lines"], font_size=panel_title_size)
        subtitle_y = title_y - panel_title_height_pt - 4.0
        subtitle_artist = ax.text(
            title_x,
            subtitle_y,
            "\n".join(panel_spec["subtitle_lines"]),
            fontsize=subtitle_size,
            fontweight="normal",
            color=neutral_color,
            ha="left",
            va="top",
        )
        add_text_box(subtitle_artist, box_id=f"{panel['panel_id']}_subtitle", box_type="panel_subtitle")

        current_top = panel_box["y1"] - panel_padding_pt - panel_spec["header_height_pt"]
        panel_occupied_regions[str(panel["panel_id"])].append(
            {
                "x0": panel_box["x0"] + panel_padding_pt,
                "y0": current_top,
                "x1": panel_box["x1"] - panel_padding_pt,
                "y1": panel_box["y1"] - panel_padding_pt,
            }
        )
        for row_index, row_spec in enumerate(panel_spec["row_specs"]):
            row_cards = list(row_spec["cards"])
            layout_mode = str(row_spec.get("layout_mode") or "horizontal")
            if layout_mode == "stacked":
                row_top = current_top
                for card_index, card_spec in enumerate(row_cards):
                    card_y1 = row_top
                    card_y0 = card_y1 - card_spec["height_pt"]
                    card_box = {
                        "x0": panel_box["x0"] + panel_padding_pt,
                        "y0": card_y0,
                        "x1": panel_box["x0"] + panel_padding_pt + card_spec["width_pt"],
                        "y1": card_y1,
                    }
                    draw_graphical_abstract_card(
                        panel_id=str(panel["panel_id"]),
                        card_spec=card_spec,
                        card_box=card_box,
                    )
                    panel_occupied_regions[str(panel["panel_id"])].append(dict(card_box))
                    row_top = card_y0 - (
                        row_spec["row_internal_gap_pt"] if card_index < len(row_cards) - 1 else 0.0
                    )
            else:
                card_y1 = current_top
                card_y0 = card_y1 - row_spec["height_pt"]
                x_cursor = panel_box["x0"] + panel_padding_pt
                for card_index, card_spec in enumerate(row_cards):
                    card_box = {
                        "x0": x_cursor,
                        "y0": card_y0,
                        "x1": x_cursor + card_spec["width_pt"],
                        "y1": card_y1,
                    }
                    draw_graphical_abstract_card(
                        panel_id=str(panel["panel_id"]),
                        card_spec=card_spec,
                        card_box=card_box,
                    )
                    panel_occupied_regions[str(panel["panel_id"])].append(dict(card_box))
                    x_cursor = card_box["x1"] + (
                        row_spec["row_internal_gap_pt"] if card_index < len(row_cards) - 1 else 0.0
                    )
            current_top = card_y0 - (row_gap_pt if row_index < len(panel_spec["row_specs"]) - 1 else 0.0)

    ordered_panels = [panel_regions[str(panel["panel_id"])] for panel in panels_payload]
    arrow_pair_specs: list[tuple[int, dict[str, float], dict[str, float], dict[str, Any]]] = []
    for index, (left_panel, right_panel) in enumerate(zip(ordered_panels, ordered_panels[1:], strict=False), start=1):
        left_panel_id = str(panels_payload[index - 1]["panel_id"])
        right_panel_id = str(panels_payload[index]["panel_id"])
        arrow_half_height_pt = max(12.0, min(16.0, panel_gap_pt * 0.58))
        lane_spec = _build_submission_graphical_abstract_arrow_lane_spec(
            left_panel_box=left_panel,
            right_panel_box=right_panel,
            left_occupied_boxes=tuple(panel_occupied_regions[left_panel_id]),
            right_occupied_boxes=tuple(panel_occupied_regions[right_panel_id]),
            clearance_pt=max(6.0, card_gap_pt * 0.45),
            arrow_half_height_pt=arrow_half_height_pt,
            edge_proximity_pt=max(panel_padding_pt + card_padding_pt * 2.0, panel_width_pt * 0.24),
        )
        arrow_pair_specs.append((index, left_panel, right_panel, lane_spec))

    shared_arrow_y = _choose_shared_submission_graphical_abstract_arrow_lane(
        [lane_spec for _, _, _, lane_spec in arrow_pair_specs]
    )
    for index, left_panel, right_panel, _lane_spec in arrow_pair_specs:
        x_left = left_panel["x1"] + 5.0
        x_right = right_panel["x0"] - 5.0
        arrow_artist = FancyArrowPatch(
            (x_left, shared_arrow_y),
            (x_right, shared_arrow_y),
            arrowstyle="simple",
            mutation_scale=max(24.0, min(34.0, panel_gap_pt * 1.35)),
            linewidth=0.0,
            color=neutral_color,
            alpha=0.72,
        )
        ax.add_patch(arrow_artist)
        arrow_artists.append((f"panel_arrow_{index}", arrow_artist))

    for pill in footer_pills:
        panel_box = panel_regions.get(str(pill["panel_id"]))
        if panel_box is None:
            continue
        label = str(pill["label"])
        style_role = str(pill.get("style_role") or "neutral").strip().lower()
        pill_width_pt = max(146.0, _measure_flow_text_width_pt(label, font_size=subtitle_size, font_weight="normal") + 38.0)
        pill_x0 = ((panel_box["x0"] + panel_box["x1"]) / 2.0) - pill_width_pt / 2.0
        pill_box = {
            "x0": pill_x0,
            "y0": footer_y0,
            "x1": pill_x0 + pill_width_pt,
            "y1": footer_y0 + footer_pill_height_pt,
        }
        ax.add_patch(
            FancyBboxPatch(
                (pill_box["x0"], pill_box["y0"]),
                pill_width_pt,
                footer_pill_height_pt,
                boxstyle="round,pad=0.0,rounding_size=14",
                linewidth=max(0.8, panel_line_width * 0.9),
                edgecolor=edge_by_role.get(style_role, neutral_color),
                facecolor="white",
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                **pill_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"footer_pill_{pill['pill_id']}",
                box_type="footer_pill",
            )
        )
        pill_artist = ax.text(
            (pill_box["x0"] + pill_box["x1"]) / 2.0,
            (pill_box["y0"] + pill_box["y1"]) / 2.0,
            label,
            fontsize=subtitle_size,
            fontweight="normal",
            color=neutral_color,
            ha="center",
            va="center",
        )
        add_text_box(pill_artist, box_id=f"footer_pill_text_{pill['pill_id']}", box_type="footer_pill_text")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for box_id, artist in arrow_artists:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="arrow_connector",
            )
        )
    for artist, box_id, box_type in text_layout_records:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type=box_type,
            )
        )

    dump_json(
        output_layout_path,
        {
            "template_id": "submission_graphical_abstract",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "panels": panels_payload,
                "footer_pills": footer_pills,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
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


def _prepare_python_illustration_output_paths(
    *,
    output_png_path: Path,
    output_svg_path: Path,
    layout_sidecar_path: Path,
) -> None:
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
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
    left_axes.text(
        -0.08,
        1.04,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
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
    right_axes.text(
        -0.08,
        1.04,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
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
    left_axes.text(-0.08, 1.04, "A", transform=left_axes.transAxes, fontsize=panel_label_size, fontweight="bold", color=reference_color)

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
    right_axes.text(-0.08, 1.04, "B", transform=right_axes.transAxes, fontsize=panel_label_size, fontweight="bold", color=reference_color)

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
    contrast_color = str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A"
    light_fill = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    audit_color = str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F"
    audit_soft = str(palette.get("audit_soft") or light_fill).strip() or light_fill

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

    submission_graphical_abstract_path = resolved_paper_root / "submission_graphical_abstract.json"
    if submission_graphical_abstract_path.exists():
        spec = display_registry.get_illustration_shell_spec("submission_graphical_abstract")
        if style_profile is None:
            style_profile = publication_display_contract.load_publication_style_profile(
                resolved_paper_root / "publication_style_profile.json"
            )
        if display_overrides is None:
            display_overrides = publication_display_contract.load_display_overrides(
                resolved_paper_root / "display_overrides.json"
            )
        shell_payload = load_json(submission_graphical_abstract_path)
        normalized_shell_payload = _validate_submission_graphical_abstract_payload(
            submission_graphical_abstract_path,
            shell_payload,
        )
        figure_id = _resolve_figure_catalog_id(
            display_id=str(normalized_shell_payload["display_id"]),
            catalog_id=str(normalized_shell_payload["catalog_id"]),
        )
        render_context = _build_render_context(
            style_profile=style_profile,
            display_overrides=display_overrides,
            display_id=str(normalized_shell_payload["display_id"]),
            template_id=spec.shell_id,
        )
        output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.svg"
        output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.png"
        output_layout_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.layout.json"
        _render_submission_graphical_abstract(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        layout_sidecar = load_json(output_layout_path)
        layout_sidecar["render_context"] = render_context
        dump_json(output_layout_path, layout_sidecar)
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
            "paper_role": str(normalized_shell_payload.get("paper_role") or spec.allowed_paper_roles[0]).strip(),
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.shell_qc_profile,
            "qc_result": qc_result,
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
            "export_paths": [
                _paper_relative_path(output_svg_path, paper_root=resolved_paper_root),
                _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
            ],
            "source_paths": [
                _paper_relative_path(submission_graphical_abstract_path, paper_root=resolved_paper_root),
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
        if figure_id not in figures_materialized:
            figures_materialized.append(figure_id)

    pruned_generated_paths = _prune_unreferenced_generated_surface_outputs(
        paper_root=resolved_paper_root,
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    )
    readme_paths: list[str] = []
    for path, content in _build_paper_surface_readmes(
        paper_root=resolved_paper_root,
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    ).items():
        write_text(path, content)
        readme_paths.append(str(path))
    dump_json(resolved_paper_root / "figures" / "figure_catalog.json", figure_catalog)
    dump_json(resolved_paper_root / "tables" / "table_catalog.json", table_catalog)
    written_files.extend(
        [
            str(resolved_paper_root / "figures" / "figure_catalog.json"),
            str(resolved_paper_root / "tables" / "table_catalog.json"),
            *readme_paths,
        ]
    )
    return {
        "status": "materialized",
        "paper_root": str(resolved_paper_root),
        "figures_materialized": figures_materialized,
        "tables_materialized": tables_materialized,
        "pruned_generated_paths": pruned_generated_paths,
        "written_files": written_files,
    }
