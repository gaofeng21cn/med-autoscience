from __future__ import annotations

import csv
from datetime import datetime, timezone
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
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from med_autoscience import display_layout_qc, display_registry, publication_display_contract


_INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "binary_prediction_curve_inputs_v1": "binary_prediction_curve_inputs.json",
    "risk_layering_monotonic_inputs_v1": "risk_layering_monotonic_inputs.json",
    "binary_calibration_decision_curve_panel_inputs_v1": "binary_calibration_decision_curve_panel_inputs.json",
    "time_to_event_grouped_inputs_v1": "time_to_event_grouped_inputs.json",
    "time_to_event_discrimination_calibration_inputs_v1": "time_to_event_discrimination_calibration_inputs.json",
    "time_to_event_decision_curve_inputs_v1": "time_to_event_decision_curve_inputs.json",
    "embedding_grouped_inputs_v1": "embedding_grouped_inputs.json",
    "heatmap_group_comparison_inputs_v1": "heatmap_group_comparison_inputs.json",
    "correlation_heatmap_inputs_v1": "correlation_heatmap_inputs.json",
    "clustered_heatmap_inputs_v1": "clustered_heatmap_inputs.json",
    "forest_effect_inputs_v1": "forest_effect_inputs.json",
    "shap_summary_inputs_v1": "shap_summary_inputs.json",
    "model_complexity_audit_panel_inputs_v1": "model_complexity_audit_panel_inputs.json",
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
    def _is_same_catalog_item(item_value: object) -> bool:
        normalized = str(item_value or "").strip()
        if normalized == value:
            return True
        if key == "figure_id":
            try:
                return _normalize_figure_catalog_id(normalized) == _normalize_figure_catalog_id(value)
            except ValueError:
                return False
        if key == "table_id":
            try:
                return _normalize_table_catalog_id(normalized) == _normalize_table_catalog_id(value)
            except ValueError:
                return False
        return False

    updated = [item for item in items if not _is_same_catalog_item(item.get(key))]
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
        block_type = str(block.get("layout_role") or block.get("block_type") or "").strip()
        title = str(block.get("title") or "").strip()
        items = block.get("lines")
        if items is None:
            items = block.get("items")
        if not block_id or not block_type or not title:
            raise ValueError(f"{path.name} design_panels[{index}] must include panel_id/block_id, layout_role/block_type, and title")
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


def _validate_generic_performance_table_payload(
    path: Path,
    payload: dict[str, Any],
) -> tuple[str, list[str], list[dict[str, Any]]]:
    stub_column_label = _require_non_empty_string(
        payload.get("row_header_label"),
        label=f"{path.name} row_header_label",
    )
    column_labels, rows = _validate_column_table_payload(path, payload)
    return stub_column_label, column_labels, rows


def _validate_grouped_risk_event_summary_table_payload(
    path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    risk_column_label = _require_non_empty_string(
        payload.get("risk_column_label"),
        label=f"{path.name} risk_column_label",
    )
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} rows[{index}] must be an object")
        cases = _require_non_negative_int(row.get("cases"), label=f"{path.name} rows[{index}].cases")
        events = _require_non_negative_int(row.get("events"), label=f"{path.name} rows[{index}].events")
        if events > cases:
            raise ValueError(f"{path.name} rows[{index}] must satisfy events <= cases")
        normalized_rows.append(
            {
                "row_id": _require_non_empty_string(row.get("row_id"), label=f"{path.name} rows[{index}].row_id"),
                "surface": _require_non_empty_string(row.get("surface"), label=f"{path.name} rows[{index}].surface"),
                "stratum": _require_non_empty_string(row.get("stratum"), label=f"{path.name} rows[{index}].stratum"),
                "cases": cases,
                "events": events,
                "risk_display": _require_non_empty_string(
                    row.get("risk_display"),
                    label=f"{path.name} rows[{index}].risk_display",
                ),
            }
        )
    return {
        "surface_column_label": str(payload.get("surface_column_label") or "Surface").strip() or "Surface",
        "stratum_column_label": str(payload.get("stratum_column_label") or "Stratum").strip() or "Stratum",
        "cases_column_label": str(payload.get("cases_column_label") or "Cases").strip() or "Cases",
        "events_column_label": str(payload.get("events_column_label") or "Events").strip() or "Events",
        "risk_column_label": risk_column_label,
        "rows": normalized_rows,
    }


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


def _validate_xy_series_list(
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
        item_label = _require_non_empty_string(item.get("label"), label=f"{path.name} {label}[{index}].label")
        x_values = _require_numeric_list(item.get("x"), label=f"{path.name} {label}[{index}].x")
        y_values = _require_numeric_list(item.get("y"), label=f"{path.name} {label}[{index}].y")
        if len(x_values) != len(y_values):
            raise ValueError(f"{path.name} {label}[{index}].x and .y must have the same length")
        normalized_series.append(
            {
                "label": item_label,
                "x": x_values,
                "y": y_values,
                "annotation": str(item.get("annotation") or "").strip(),
            }
        )
    return normalized_series


def _validate_named_value_rows(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_rows: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        row_label = _require_non_empty_string(item.get("label"), label=f"{path.name} {label}[{index}].label")
        if row_label in seen_labels:
            raise ValueError(f"{path.name} {label}[{index}].label must be unique")
        seen_labels.add(row_label)
        normalized_rows.append(
            {
                "label": row_label,
                "value": _require_numeric_value(item.get("value"), label=f"{path.name} {label}[{index}].value"),
            }
        )
    return normalized_rows


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


def _validate_risk_layering_monotonic_bars_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    def normalize_bar_collection(
        *,
        bars_payload: object,
        label: str,
    ) -> list[dict[str, Any]]:
        if not isinstance(bars_payload, list) or not bars_payload:
            raise ValueError(f"{path.name} {label} must be a non-empty list")
        normalized_bars: list[dict[str, Any]] = []
        previous_risk_rate: float | None = None
        for bar_index, bar in enumerate(bars_payload):
            if not isinstance(bar, dict):
                raise ValueError(f"{path.name} {label}[{bar_index}] must be an object")
            bar_label = _require_non_empty_string(
                bar.get("label"),
                label=f"{path.name} {label}[{bar_index}].label",
            )
            raw_cases = bar.get("cases")
            raw_events = bar.get("events")
            if not isinstance(raw_cases, int) or isinstance(raw_cases, bool) or raw_cases <= 0:
                raise ValueError(f"{path.name} {label}[{bar_index}].cases must be a positive integer")
            if (
                not isinstance(raw_events, int)
                or isinstance(raw_events, bool)
                or raw_events < 0
                or raw_events > raw_cases
            ):
                raise ValueError(
                    f"{path.name} {label}[{bar_index}].events must satisfy 0 <= events <= cases"
                )
            risk_rate = _require_numeric_value(
                bar.get("risk"),
                label=f"{path.name} {label}[{bar_index}].risk",
            )
            expected_risk_rate = raw_events / raw_cases
            if not (-1e-9 <= risk_rate <= 1.0 + 1e-9):
                raise ValueError(f"{path.name} {label}[{bar_index}].risk must lie within [0, 1]")
            if not abs(risk_rate - expected_risk_rate) <= 5e-4:
                raise ValueError(f"{path.name} {label}[{bar_index}].risk must match events / cases")
            if previous_risk_rate is not None and risk_rate + 1e-9 < previous_risk_rate:
                raise ValueError(f"{path.name} {label} must be monotonic in the declared order")
            previous_risk_rate = risk_rate
            normalized_bars.append(
                {
                    "label": bar_label,
                    "n": raw_cases,
                    "events": raw_events,
                    "risk_rate": risk_rate,
                }
            )
        return normalized_bars

    normalized_panels = [
        {
            "panel_id": "left_panel",
            "title": _require_non_empty_string(
                payload.get("left_panel_title"),
                label=f"{path.name} display `{expected_display_id}` left_panel_title",
            ),
            "x_label": _require_non_empty_string(
                payload.get("left_x_label"),
                label=f"{path.name} display `{expected_display_id}` left_x_label",
            ),
            "bars": normalize_bar_collection(
                bars_payload=payload.get("left_bars"),
                label=f"display `{expected_display_id}` left_bars",
            ),
        },
        {
            "panel_id": "right_panel",
            "title": _require_non_empty_string(
                payload.get("right_panel_title"),
                label=f"{path.name} display `{expected_display_id}` right_panel_title",
            ),
            "x_label": _require_non_empty_string(
                payload.get("right_x_label"),
                label=f"{path.name} display `{expected_display_id}` right_x_label",
            ),
            "bars": normalize_bar_collection(
                bars_payload=payload.get("right_bars"),
                label=f"display `{expected_display_id}` right_bars",
            ),
        },
    ]
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "panels": normalized_panels,
    }


def _validate_binary_calibration_decision_curve_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    calibration_x_label = _require_non_empty_string(
        payload.get("calibration_x_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_x_label",
    )
    calibration_y_label = _require_non_empty_string(
        payload.get("calibration_y_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_y_label",
    )
    decision_x_label = _require_non_empty_string(
        payload.get("decision_x_label"),
        label=f"{path.name} display `{expected_display_id}` decision_x_label",
    )
    decision_y_label = _require_non_empty_string(
        payload.get("decision_y_label"),
        label=f"{path.name} display `{expected_display_id}` decision_y_label",
    )
    calibration_series = _validate_xy_series_list(
        path=path,
        payload=payload.get("calibration_series"),
        label=f"display `{expected_display_id}` calibration_series",
    )
    decision_series = _validate_xy_series_list(
        path=path,
        payload=payload.get("decision_series"),
        label=f"display `{expected_display_id}` decision_series",
    )
    decision_reference_lines = _validate_xy_series_list(
        path=path,
        payload=payload.get("decision_reference_lines"),
        label=f"display `{expected_display_id}` decision_reference_lines",
    )
    focus_window_payload = payload.get("decision_focus_window")
    focus_window: dict[str, float] | None = None
    if focus_window_payload is not None:
        if not isinstance(focus_window_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` decision_focus_window must be an object")
        xmin = _require_numeric_value(
            focus_window_payload.get("xmin"),
            label=f"{path.name} display `{expected_display_id}` decision_focus_window.xmin",
        )
        xmax = _require_numeric_value(
            focus_window_payload.get("xmax"),
            label=f"{path.name} display `{expected_display_id}` decision_focus_window.xmax",
        )
        if xmax <= xmin:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` decision_focus_window must satisfy xmin < xmax"
            )
        focus_window = {"xmin": xmin, "xmax": xmax}
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "calibration_x_label": calibration_x_label,
        "calibration_y_label": calibration_y_label,
        "decision_x_label": decision_x_label,
        "decision_y_label": decision_y_label,
        "calibration_series": calibration_series,
        "calibration_reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("calibration_reference_line"),
            label=f"display `{expected_display_id}` calibration_reference_line",
        ),
        "decision_series": decision_series,
        "decision_reference_lines": decision_reference_lines,
        "decision_focus_window": focus_window,
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


def _validate_model_complexity_audit_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    metric_panels_payload = payload.get("metric_panels")
    audit_panels_payload = payload.get("audit_panels")
    if not isinstance(metric_panels_payload, list) or not metric_panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty metric_panels list")
    if not isinstance(audit_panels_payload, list) or not audit_panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty audit_panels list")

    normalized_metric_panels: list[dict[str, Any]] = []
    normalized_audit_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()

    def normalize_panels(panels_payload: list[dict[str, Any]], *, panel_kind: str) -> list[dict[str, Any]]:
        normalized_panels: list[dict[str, Any]] = []
        for panel_index, panel in enumerate(panels_payload):
            if not isinstance(panel, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panel_kind}[{panel_index}] must be an object"
                )
            panel_id = _require_non_empty_string(
                panel.get("panel_id"),
                label=f"{path.name} display `{expected_display_id}` {panel_kind}[{panel_index}].panel_id",
            )
            if panel_id in seen_panel_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panel_kind}[{panel_index}].panel_id must be unique"
                )
            seen_panel_ids.add(panel_id)
            normalized_panels.append(
                {
                    "panel_id": panel_id,
                    "panel_label": _require_non_empty_string(
                        panel.get("panel_label"),
                        label=f"{path.name} display `{expected_display_id}` {panel_kind}[{panel_index}].panel_label",
                    ),
                    "title": _require_non_empty_string(
                        panel.get("title"),
                        label=f"{path.name} display `{expected_display_id}` {panel_kind}[{panel_index}].title",
                    ),
                    "x_label": _require_non_empty_string(
                        panel.get("x_label"),
                        label=f"{path.name} display `{expected_display_id}` {panel_kind}[{panel_index}].x_label",
                    ),
                    "reference_value": (
                        _require_numeric_value(
                            panel.get("reference_value"),
                            label=f"{path.name} display `{expected_display_id}` {panel_kind}[{panel_index}].reference_value",
                        )
                        if panel.get("reference_value") is not None
                        else None
                    ),
                    "rows": _validate_named_value_rows(
                        path=path,
                        payload=panel.get("rows"),
                        label=f"display `{expected_display_id}` {panel_kind}[{panel_index}].rows",
                    ),
                }
            )
        return normalized_panels

    normalized_metric_panels = normalize_panels(metric_panels_payload, panel_kind="metric_panels")
    normalized_audit_panels = normalize_panels(audit_panels_payload, panel_kind="audit_panels")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_panels": normalized_metric_panels,
        "audit_panels": normalized_audit_panels,
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
        return payload_path, _validate_risk_layering_monotonic_bars_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "binary_calibration_decision_curve_panel_inputs_v1":
        return payload_path, _validate_binary_calibration_decision_curve_panel_display_payload(
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
    if spec.input_schema_id == "model_complexity_audit_panel_inputs_v1":
        return payload_path, _validate_model_complexity_audit_panel_display_payload(
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
) -> None:
    def wrap_text(value: str, *, width: int) -> str:
        return textwrap.fill(str(value), width=width, break_long_words=False, break_on_hyphens=False)

    right_blocks: list[dict[str, Any]] = []
    if endpoint_inventory:
        right_blocks.append(
            {
                "panel_id": "endpoint_inventory",
                "layout_role": "endpoint_inventory",
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
    right_blocks.extend(design_panels)

    total_right_lines = sum(len(block["lines"]) for block in right_blocks)
    figure_height = max(6.6, 1.4 + 1.35 * len(steps) + 0.42 * total_right_lines)
    fig, ax = plt.subplots(figsize=(12.8, figure_height))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")

    title_box = {"box_id": "title", "box_type": "title", "x0": 0.04, "y0": 0.94, "x1": 0.96, "y1": 0.985}
    ax.text(
        0.50,
        0.962,
        title,
        fontsize=15,
        fontweight="bold",
        color="#213547",
        ha="center",
        va="center",
        transform=ax.transAxes,
    )

    flow_x0, flow_x1 = 0.04, 0.43
    exclusion_x0, exclusion_x1 = 0.46, 0.69
    sidecar_x0, sidecar_x1 = 0.72, 0.97
    vertical_gap = 0.035
    available_flow_height = 0.76
    step_box_height = min(0.14, max(0.10, (available_flow_height - vertical_gap * max(0, len(steps) - 1)) / max(len(steps), 1)))

    branch_groups: dict[str, list[dict[str, Any]]] = {}
    for branch in exclusions:
        branch_groups.setdefault(str(branch["from_step_id"]), []).append(branch)

    layout_boxes: list[dict[str, Any]] = [title_box]
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []

    current_top = 0.88
    flow_y_min = 0.88
    for index, step in enumerate(steps):
        step_y1 = current_top
        step_y0 = step_y1 - step_box_height
        flow_y_min = min(flow_y_min, step_y0)
        box = FancyBboxPatch(
            (flow_x0, step_y0),
            flow_x1 - flow_x0,
            step_box_height,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            linewidth=1.2,
            edgecolor="#547980",
            facecolor="#f6fbfb",
            transform=ax.transAxes,
        )
        ax.add_patch(box)
        layout_boxes.append(
            {
                "box_id": f"step_{step['step_id']}",
                "box_type": "main_step",
                "x0": flow_x0,
                "y0": step_y0,
                "x1": flow_x1,
                "y1": step_y1,
            }
        )
        ax.text(
            flow_x0 + 0.016,
            step_y1 - 0.028,
            step["label"],
            fontsize=11.2,
            fontweight="bold",
            color="#1f2d3d",
            ha="left",
            va="top",
            transform=ax.transAxes,
        )
        ax.text(
            flow_x0 + 0.016,
            step_y0 + 0.030,
            f"n = {step['n']}",
            fontsize=10.8,
            color="#234b5a",
            ha="left",
            va="bottom",
            transform=ax.transAxes,
        )
        if step["detail"]:
            ax.text(
                flow_x0 + 0.09,
                step_y0 + 0.030,
                step["detail"],
                fontsize=9.3,
                color="#4f6470",
                ha="left",
                va="bottom",
                transform=ax.transAxes,
            )

        related_branches = branch_groups.get(str(step["step_id"]), [])
        if related_branches:
            branch_gap = 0.010
            branch_height = min(0.080, (step_box_height - branch_gap * max(0, len(related_branches) - 1)) / max(len(related_branches), 1))
            branch_y_cursor = step_y1
            for branch in related_branches:
                branch_y1 = branch_y_cursor
                branch_y0 = branch_y1 - branch_height
                branch_y_cursor = branch_y0 - branch_gap
                branch_patch = FancyBboxPatch(
                    (exclusion_x0, branch_y0),
                    exclusion_x1 - exclusion_x0,
                    branch_height,
                    boxstyle="round,pad=0.02,rounding_size=0.05",
                    linewidth=1.0,
                    edgecolor="#b45d5d",
                    facecolor="#fff7f5",
                    transform=ax.transAxes,
                )
                ax.add_patch(branch_patch)
                layout_boxes.append(
                    {
                        "box_id": f"exclusion_{branch['exclusion_id']}",
                        "box_type": "exclusion_box",
                        "x0": exclusion_x0,
                        "y0": branch_y0,
                        "x1": exclusion_x1,
                        "y1": branch_y1,
                    }
                )
                ax.text(
                    exclusion_x0 + 0.012,
                    branch_y1 - 0.016,
                    wrap_text(f"{branch['label']} (n={branch['n']})", width=34),
                    fontsize=8.8,
                    fontweight="bold",
                    color="#7a2e2e",
                    ha="left",
                    va="top",
                    transform=ax.transAxes,
                )
                if branch["detail"]:
                    ax.text(
                        exclusion_x0 + 0.012,
                        branch_y0 + 0.012,
                        wrap_text(branch["detail"], width=36),
                        fontsize=8.0,
                        color="#7a4d4d",
                        ha="left",
                        va="bottom",
                        transform=ax.transAxes,
                    )
                branch_arrow = FancyArrowPatch(
                    (flow_x1, (step_y0 + step_y1) / 2),
                    (exclusion_x0, (branch_y0 + branch_y1) / 2),
                    arrowstyle="-|>",
                    mutation_scale=10,
                    linewidth=0.9,
                    color="#9a8c86",
                    transform=ax.transAxes,
                )
                ax.add_patch(branch_arrow)
        if index < len(steps) - 1:
            arrow = FancyArrowPatch(
                ((flow_x0 + flow_x1) / 2, step_y0 - 0.005),
                ((flow_x0 + flow_x1) / 2, step_y0 - vertical_gap + 0.010),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.0,
                color="#6c8a91",
                transform=ax.transAxes,
            )
            ax.add_patch(arrow)
        current_top = step_y0 - vertical_gap

    panel_boxes.append(
        {
            "box_id": "flow_panel",
            "box_type": "flow_panel",
            "x0": flow_x0,
            "y0": flow_y_min,
            "x1": exclusion_x1,
            "y1": 0.88,
        }
    )

    if right_blocks:
        def draw_block(*, block: dict[str, Any], x0: float, x1: float, y1: float, height: float) -> float:
            y0 = max(0.05, y1 - height)
            block_patch = FancyBboxPatch(
                (x0, y0),
                x1 - x0,
                y1 - y0,
                boxstyle="round,pad=0.02,rounding_size=0.05",
                linewidth=1.0,
                edgecolor="#8fa1ac",
                facecolor="#f7fafb",
                transform=ax.transAxes,
            )
            ax.add_patch(block_patch)
            panel_boxes.append(
                {
                    "box_id": f"secondary_panel_{block['panel_id']}",
                    "box_type": "secondary_panel",
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                }
            )
            ax.text(
                x0 + 0.012,
                y1 - 0.020,
                wrap_text(str(block["title"]), width=24),
                fontsize=9.8,
                fontweight="bold",
                color="#334155",
                ha="left",
                va="top",
                transform=ax.transAxes,
            )
            y_cursor = y1 - 0.056
            for item in block["lines"]:
                if y_cursor <= y0 + 0.012:
                    break
                text = str(item["label"])
                detail = str(item.get("detail") or "").strip()
                if detail:
                    text = f"{text}: {detail}"
                text = wrap_text(text, width=22 if (x1 - x0) < 0.16 else 32)
                ax.text(
                    x0 + 0.014,
                    y_cursor,
                    text,
                    fontsize=8.2,
                    color="#415161",
                    ha="left",
                    va="top",
                    transform=ax.transAxes,
                )
                y_cursor -= 0.026 * max(1, len(text.splitlines())) + 0.006
            return y0

        current_block_top = 0.88
        for block in right_blocks:
            block_height = min(0.20, 0.06 + 0.04 * len(block["lines"]))
            current_block_top = draw_block(
                block=block,
                x0=sidecar_x0,
                x1=sidecar_x1,
                y1=current_block_top,
                height=block_height,
            ) - 0.018

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
        },
    )

    fig.savefig(output_svg_path, format="svg", bbox_inches="tight")
    fig.savefig(output_png_path, format="png", dpi=220, bbox_inches="tight")
    plt.close(fig)

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


def _write_grouped_risk_event_summary_outputs(
    *,
    output_md_path: Path,
    output_csv_path: Path,
    title: str,
    surface_column_label: str,
    stratum_column_label: str,
    cases_column_label: str,
    events_column_label: str,
    risk_column_label: str,
    rows: list[dict[str, Any]],
) -> None:
    headers = [
        surface_column_label,
        stratum_column_label,
        cases_column_label,
        events_column_label,
        risk_column_label,
    ]
    table_rows = [
        [
            str(row["surface"]),
            str(row["stratum"]),
            str(row["cases"]),
            str(row["events"]),
            str(row["risk_display"]),
        ]
        for row in rows
    ]
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


def _single_offset_collection_to_layout_box(
    *,
    collection,
    axes,
    figure: plt.Figure,
    renderer,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    offsets = collection.get_offsets()
    if len(offsets) != 1:
        raise ValueError(f"{box_id} expected a single plotted offset")
    paths = collection.get_paths()
    transforms = collection.get_transforms()
    if not paths or len(transforms) == 0:
        raise ValueError(f"{box_id} expected a rendered marker path")

    marker_bbox = paths[0].get_extents(matplotlib.transforms.Affine2D(transforms[0]))
    offset_x, offset_y = collection.get_offset_transform().transform(offsets)[0]
    translated_bbox = matplotlib.transforms.Bbox.from_extents(
        float(marker_bbox.x0 + offset_x),
        float(marker_bbox.y0 + offset_y),
        float(marker_bbox.x1 + offset_x),
        float(marker_bbox.y1 + offset_y),
    )
    clip_bbox = axes.get_window_extent(renderer=renderer)
    clipped_bbox = matplotlib.transforms.Bbox.from_extents(
        float(max(translated_bbox.x0, clip_bbox.x0)),
        float(max(translated_bbox.y0, clip_bbox.y0)),
        float(min(translated_bbox.x1, clip_bbox.x1)),
        float(min(translated_bbox.y1, clip_bbox.y1)),
    )
    return _bbox_to_layout_box(
        figure=figure,
        bbox=clipped_bbox,
        box_id=box_id,
        box_type=box_type,
    )


def _normalize_reference_line_to_device_space(
    *,
    reference_line: dict[str, Any] | None,
    axes,
    figure: plt.Figure,
) -> dict[str, Any] | None:
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
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    figure_width = max(7.8, 4.0 * len(panels))
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.0), sharey=len(panels) > 1)
    fig.patch.set_facecolor("white")
    axes_list = list(axes.ravel()) if hasattr(axes, "ravel") else [axes]
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    y_label_artist = fig.text(
        0.02,
        0.5,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        va="center",
        ha="center",
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    palette = ("#e6ded4", "#ddd2bf", "#ccc1ae", "#b7aa98", "#8b998f")
    max_percentage = max(float(bar["risk_rate"]) * 100.0 for panel in panels for bar in panel["bars"])
    y_upper = max(10.0, max_percentage * 1.22)
    y_upper = float(((int(y_upper) + 9) // 10) * 10)
    value_text_artists: list[Any] = []

    for panel_index, (axes_item, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        percentage_values = [float(bar["risk_rate"]) * 100.0 for bar in panel["bars"]]
        x_positions = list(range(len(panel["bars"])))
        bars = axes_item.bar(
            x_positions,
            percentage_values,
            color=[palette[min(index, len(palette) - 1)] for index in range(len(panel["bars"]))],
            edgecolor="none",
            width=0.78,
        )
        for bar_index, (bar_artist, bar_payload, percentage_value) in enumerate(
            zip(bars, panel["bars"], percentage_values, strict=True),
            start=1,
        ):
            value_text_artists.append(
                axes_item.text(
                    bar_artist.get_x() + bar_artist.get_width() / 2.0,
                    percentage_value + y_upper * 0.025,
                    f"{percentage_value:.1f}%\n{bar_payload['events']}/{bar_payload['n']}",
                    ha="center",
                    va="bottom",
                    fontsize=9.5,
                    color="#4b596d",
                )
            )
        axes_item.set_ylim(0.0, y_upper)
        axes_item.set_xticks(x_positions)
        axes_item.set_xticklabels([str(bar["label"]) for bar in panel["bars"]], fontsize=10)
        axes_item.set_xlabel(str(panel["x_label"]), fontsize=11, fontweight="bold", color="#13293d")
        axes_item.set_title(str(panel["title"]), fontsize=11, fontweight="bold", color="#334155", pad=10)
        axes_item.grid(axis="y", color="#e6edf2", linewidth=0.4)
        axes_item.grid(axis="x", visible=False)
        axes_item.spines["top"].set_visible(False)
        axes_item.spines["right"].set_visible(False)
        if panel_index == 1:
            axes_item.tick_params(axis="y", labelsize=10)
        else:
            axes_item.tick_params(axis="y", labelleft=False)

    fig.subplots_adjust(left=0.10, right=0.98, top=0.84, bottom=0.18, wspace=0.24)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=title_artist.get_window_extent(renderer=renderer),
            box_id="title",
            box_type="title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_label_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
    ]
    panel_boxes: list[dict[str, Any]] = []
    for panel_index, (axes_item, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_index}",
                box_type="panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.title.get_window_extent(renderer=renderer),
                box_id=f"subplot_title_{panel_index}",
                box_type="subplot_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"subplot_x_axis_title_{panel_index}",
                box_type="subplot_x_axis_title",
            )
        )
        for bar_index, bar_artist in enumerate(axes_item.patches, start=1):
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=float(bar_artist.get_x()),
                    y0=0.0,
                    x1=float(bar_artist.get_x() + bar_artist.get_width()),
                    y1=float(bar_artist.get_height()),
                    box_id=f"panel_{panel_index}_bar_{bar_index}",
                    box_type="bar",
                )
            )
    for label_index, artist in enumerate(value_text_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"value_label_{label_index}",
                box_type="value_label",
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
            "metrics": {"panels": panels},
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
    if not calibration_series or not decision_series:
        raise RuntimeError(f"{template_id} requires non-empty calibration_series and decision_series")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    fig, (calibration_axes, decision_axes) = plt.subplots(1, 2, figsize=(10.2, 5.0))
    fig.patch.set_facecolor("white")
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    palette = ("#7c9183", "#b8a892", "#7f8a98", "#bf8f8f", "#d7cfc1")

    calibration_reference_line = display_payload.get("calibration_reference_line")
    calibration_x_values = [float(value) for series in calibration_series for value in series["x"]]
    calibration_y_values = [float(value) for series in calibration_series for value in series["y"]]
    if isinstance(calibration_reference_line, dict):
        calibration_x_values.extend(float(value) for value in calibration_reference_line["x"])
        calibration_y_values.extend(float(value) for value in calibration_reference_line["y"])
    for index, series in enumerate(calibration_series):
        calibration_axes.plot(
            series["x"],
            series["y"],
            linewidth=2.0,
            marker="o",
            markersize=4.6,
            color=palette[index % len(palette)],
            label=str(series["label"]),
        )
    if isinstance(calibration_reference_line, dict):
        calibration_axes.plot(
            calibration_reference_line["x"],
            calibration_reference_line["y"],
            linewidth=1.0,
            linestyle="--",
            color="#8c97a5",
            label=str(calibration_reference_line.get("label") or ""),
        )
    calibration_axes.set_xlim(min(0.0, min(calibration_x_values)), max(calibration_x_values) * 1.03)
    calibration_axes.set_ylim(min(0.0, min(calibration_y_values)), max(calibration_y_values) * 1.06)
    calibration_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    calibration_axes.set_ylabel(
        str(display_payload.get("calibration_y_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    calibration_axes.set_title("Calibration", fontsize=11, fontweight="bold", color="#334155")
    _apply_publication_axes_style(calibration_axes)

    focus_window = display_payload.get("decision_focus_window")
    decision_reference_lines = list(display_payload.get("decision_reference_lines") or [])
    decision_x_values = [float(value) for series in decision_series for value in series["x"]]
    decision_y_values = [float(value) for series in decision_series for value in series["y"]]
    for line in decision_reference_lines:
        decision_x_values.extend(float(value) for value in line["x"])
        decision_y_values.extend(float(value) for value in line["y"])
    if isinstance(focus_window, dict):
        decision_axes.axvspan(
            float(focus_window["xmin"]),
            float(focus_window["xmax"]),
            color="#e7e1d8",
            alpha=0.35,
            zorder=0,
        )
    for index, series in enumerate(decision_series):
        decision_axes.plot(
            series["x"],
            series["y"],
            linewidth=2.0,
            color=palette[index % len(palette)],
            label=str(series["label"]),
        )
    for line in decision_reference_lines:
        decision_axes.plot(
            line["x"],
            line["y"],
            linewidth=1.0,
            linestyle="--",
            color="#8c97a5",
            label=str(line.get("label") or ""),
        )
    decision_axes.set_xlim(min(decision_x_values), max(decision_x_values))
    decision_axes.set_ylim(min(decision_y_values) * 1.08, max(decision_y_values) * 1.08)
    decision_axes.set_xlabel(
        str(display_payload.get("decision_x_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    decision_axes.set_ylabel(
        str(display_payload.get("decision_y_label") or "").strip(),
        fontsize=11,
        fontweight="bold",
        color="#13293d",
    )
    if isinstance(focus_window, dict):
        decision_title = f"Decision curve (thresholds {focus_window['xmin']:.2f}-{focus_window['xmax']:.2f})"
    else:
        decision_title = "Decision curve"
    decision_axes.set_title(decision_title, fontsize=11, fontweight="bold", color="#334155")
    _apply_publication_axes_style(decision_axes)

    handles: list[Any] = []
    labels: list[str] = []
    for axes_item in (calibration_axes, decision_axes):
        axis_handles, axis_labels = axes_item.get_legend_handles_labels()
        for handle, label in zip(axis_handles, axis_labels, strict=True):
            if not label or label in labels:
                continue
            handles.append(handle)
            labels.append(label)
    legend = fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=3, frameon=False)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.84, bottom=0.22, wspace=0.22)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend",
            box_type="legend",
        )
    ]
    if isinstance(focus_window, dict):
        y_min, y_max = decision_axes.get_ylim()
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=decision_axes,
                figure=fig,
                x0=float(focus_window["xmin"]),
                y0=float(y_min),
                x1=float(focus_window["xmax"]),
                y1=float(y_max),
                box_id="decision_focus_window",
                box_type="focus_window",
            )
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
                    bbox=calibration_axes.title.get_window_extent(renderer=renderer),
                    box_id="calibration_subplot_title",
                    box_type="subplot_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=decision_axes.title.get_window_extent(renderer=renderer),
                    box_id="decision_subplot_title",
                    box_type="subplot_title",
                ),
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
            "guide_boxes": guide_boxes,
            "metrics": {
                "calibration_series": calibration_series,
                "calibration_reference_line": calibration_reference_line,
                "decision_series": decision_series,
                "decision_reference_lines": decision_reference_lines,
                "decision_focus_window": focus_window,
            },
        },
    )
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

    figure_height = max(7.2, 2.2 * max(len(metric_panels), len(audit_panels)))
    fig = plt.figure(figsize=(10.8, figure_height))
    fig.patch.set_facecolor("white")
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    outer_grid = fig.add_gridspec(1, 2, width_ratios=[1.28, 1.0], wspace=0.34)
    left_grid = outer_grid[0].subgridspec(len(metric_panels), 1, hspace=0.78)
    right_grid = outer_grid[1].subgridspec(len(audit_panels), 1, hspace=0.56)

    metric_axes = [fig.add_subplot(left_grid[index, 0]) for index in range(len(metric_panels))]
    audit_axes = [fig.add_subplot(right_grid[index, 0]) for index in range(len(audit_panels))]
    metric_colors = ("#7c9183", "#b8a892", "#7f8a98")
    audit_colors = ("#c1b19f", "#c08f8f", "#9db4c0")

    metric_marker_specs: list[dict[str, Any]] = []
    audit_bar_specs: list[dict[str, Any]] = []
    reference_line_specs: list[dict[str, Any]] = []

    for panel_index, (axes_item, panel) in enumerate(zip(metric_axes, metric_panels, strict=True), start=1):
        rows = panel["rows"]
        y_positions = list(range(len(rows)))
        values = [float(row["value"]) for row in rows]
        labels = [str(row["label"]) for row in rows]
        for row_index, (row, y_position) in enumerate(zip(rows, y_positions, strict=True), start=1):
            marker_artist = axes_item.scatter(
                float(row["value"]),
                y_position,
                s=40,
                color=metric_colors[(panel_index - 1) % len(metric_colors)],
                zorder=3,
            )
            axes_item.text(
                float(row["value"]) + max(0.001, (max(values) - min(values) if len(values) > 1 else max(values, 1.0)) * 0.03),
                y_position,
                f"{float(row['value']):.4f}",
                va="center",
                ha="left",
                fontsize=9.2,
                color="#5a677a",
            )
            metric_marker_specs.append(
                {
                    "artist": marker_artist,
                    "label": str(row["label"]),
                }
            )
        if panel.get("reference_value") is not None:
            reference_value = float(panel["reference_value"])
            axes_item.axvline(reference_value, color="#8c97a5", linewidth=1.0, linestyle="--")
            reference_line_specs.append(
                {
                    "panel_kind": "metric",
                    "panel_index": panel_index,
                    "value": reference_value,
                    "y_min": -0.5,
                    "y_max": float(len(rows)) - 0.5,
                }
            )
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(labels, fontsize=9.4)
        axes_item.set_ylim(float(len(rows)) - 0.5, -0.5)
        axes_item.set_xlabel(str(panel["x_label"]), fontsize=10.5, fontweight="bold", color="#13293d")
        axes_item.set_title(
            f"{panel['panel_label']}  {panel['title']}",
            fontsize=11,
            fontweight="bold",
            color="#334155",
            loc="left",
            pad=6,
        )
        x_min = min(values + ([float(panel["reference_value"])] if panel.get("reference_value") is not None else []))
        x_max = max(values + ([float(panel["reference_value"])] if panel.get("reference_value") is not None else []))
        x_padding = max((x_max - x_min) * 0.12, 0.01)
        axes_item.set_xlim(x_min - x_padding, x_max + x_padding)
        _apply_publication_axes_style(axes_item)

    for panel_index, (axes_item, panel) in enumerate(zip(audit_axes, audit_panels, strict=True), start=1):
        rows = panel["rows"]
        y_positions = list(range(len(rows)))
        values = [float(row["value"]) for row in rows]
        labels = [str(row["label"]) for row in rows]
        bars = axes_item.barh(
            y_positions,
            values,
            height=0.72,
            color=audit_colors[(panel_index - 1) % len(audit_colors)],
            edgecolor="none",
        )
        for row_index, (bar_artist, row, y_position) in enumerate(zip(bars, rows, y_positions, strict=True), start=1):
            axes_item.text(
                float(row["value"]) + max(0.002, max(values) * 0.02),
                y_position,
                f"{float(row['value']):.3f}",
                va="center",
                ha="left",
                fontsize=9.2,
                color="#5a677a",
            )
            audit_bar_specs.append(
                {
                    "panel_index": panel_index,
                    "x0": min(0.0, float(row["value"])),
                    "x1": max(0.0, float(row["value"])),
                    "y": float(y_position),
                    "label": str(row["label"]),
                }
            )
        if panel.get("reference_value") is not None:
            reference_value = float(panel["reference_value"])
            axes_item.axvline(reference_value, color="#8c97a5", linewidth=1.0, linestyle="--")
            reference_line_specs.append(
                {
                    "panel_kind": "audit",
                    "panel_index": panel_index,
                    "value": reference_value,
                    "y_min": -0.5,
                    "y_max": float(len(rows)) - 0.5,
                }
            )
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(labels, fontsize=9.2)
        axes_item.set_ylim(float(len(rows)) - 0.5, -0.5)
        axes_item.set_xlabel(str(panel["x_label"]), fontsize=10.5, fontweight="bold", color="#13293d")
        axes_item.set_title(
            f"{panel['panel_label']}  {panel['title']}",
            fontsize=11,
            fontweight="bold",
            color="#334155",
            loc="left",
            pad=6,
        )
        axes_item.set_xlim(0.0, max(values) * 1.18)
        _apply_publication_axes_style(axes_item)

    fig.subplots_adjust(left=0.13, right=0.98, top=0.88, bottom=0.08)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=title_artist.get_window_extent(renderer=renderer),
            box_id="title",
            box_type="title",
        )
    ]
    panel_boxes: list[dict[str, Any]] = []
    for panel_index, axes_item in enumerate(metric_axes, start=1):
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"metric_panel_{panel_index}",
                box_type="metric_panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.title.get_window_extent(renderer=renderer),
                box_id=f"metric_panel_title_{panel_index}",
                box_type="subplot_title",
            )
        )
    for panel_index, axes_item in enumerate(audit_axes, start=1):
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"audit_panel_{panel_index}",
                box_type="audit_panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.title.get_window_extent(renderer=renderer),
                box_id=f"audit_panel_title_{panel_index}",
                box_type="subplot_title",
            )
        )
    for marker_index, marker_spec in enumerate(metric_marker_specs, start=1):
        layout_boxes.append(
            _single_offset_collection_to_layout_box(
                collection=marker_spec["artist"],
                axes=marker_spec["artist"].axes,
                figure=fig,
                renderer=renderer,
                box_id=f"metric_marker_{marker_index}",
                box_type="metric_marker",
            )
        )
    for bar_index, bar_spec in enumerate(audit_bar_specs, start=1):
        axes_item = audit_axes[int(bar_spec["panel_index"]) - 1]
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(bar_spec["x0"]),
                y0=float(bar_spec["y"]) - 0.36,
                x1=float(bar_spec["x1"]),
                y1=float(bar_spec["y"]) + 0.36,
                box_id=f"audit_bar_{bar_index}",
                box_type="audit_bar",
            )
        )
    guide_boxes: list[dict[str, Any]] = []
    for line_index, line_spec in enumerate(reference_line_specs, start=1):
        axes_item = (
            metric_axes[int(line_spec["panel_index"]) - 1]
            if line_spec["panel_kind"] == "metric"
            else audit_axes[int(line_spec["panel_index"]) - 1]
        )
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=f"_reference_panel_{line_index}",
            box_type="panel",
        )
        line_center_x, _ = _data_point_to_figure_xy(
            axes=axes_item,
            figure=fig,
            x=float(line_spec["value"]),
            y=float((line_spec["y_min"] + line_spec["y_max"]) / 2.0),
        )
        guide_boxes.append(
            {
                "box_id": f"reference_line_{line_index}",
                "box_type": "reference_line",
                "x0": line_center_x - 0.0015,
                "y0": panel_box["y0"] + 0.001,
                "x1": line_center_x + 0.0015,
                "y1": panel_box["y1"] - 0.001,
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
            "metrics": {"metric_panels": metric_panels, "audit_panels": audit_panels},
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
    if template_id == "risk_layering_monotonic_bars":
        _render_python_risk_layering_monotonic_bars(
            template_id=template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
        return
    if template_id == "binary_calibration_decision_curve_panel":
        _render_python_binary_calibration_decision_curve_panel(
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
    if template_id == "model_complexity_audit_panel":
        _render_python_model_complexity_audit_panel(
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
    written_files: list[str] = []

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
        }:
            if display_kind != "table":
                raise ValueError(f"{requirement_key} must be registered as a table display")
            spec = display_registry.get_table_shell_spec(requirement_key)
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            column_labels, rows = _validate_column_table_payload(payload_path, payload)
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            if requirement_key == "table2_time_to_event_performance_summary":
                title = (
                    str(payload.get("title") or "Time-to-event model performance summary").strip()
                    or "Time-to-event model performance summary"
                )
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_time_to_event_performance_summary.md"
                stub_header = "Metric"
                default_caption = "Time-to-event discrimination and error metrics across analysis cohorts."
            else:
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
            written_files.append(str(output_md_path))
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

        if requirement_key == "performance_summary_table_generic":
            if display_kind != "table":
                raise ValueError("performance_summary_table_generic must be registered as a table display")
            spec = display_registry.get_table_shell_spec("performance_summary_table_generic")
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            row_header_label, column_labels, rows = _validate_generic_performance_table_payload(payload_path, payload)
            title = str(payload.get("title") or "Performance summary").strip() or "Performance summary"
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.csv"
            output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.md"
            _write_table_outputs(
                output_md_path=output_md_path,
                title=title,
                column_labels=column_labels,
                rows=rows,
                stub_header=row_header_label,
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
                "caption": str(payload.get("caption") or "Primary and comparator model performance summary.").strip(),
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

        if requirement_key == "grouped_risk_event_summary_table":
            if display_kind != "table":
                raise ValueError("grouped_risk_event_summary_table must be registered as a table display")
            spec = display_registry.get_table_shell_spec("grouped_risk_event_summary_table")
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            grouped_risk_payload = _validate_grouped_risk_event_summary_table_payload(payload_path, payload)
            title = str(payload.get("title") or "Grouped risk-event summary").strip() or "Grouped risk-event summary"
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.csv"
            output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.md"
            _write_grouped_risk_event_summary_outputs(
                output_md_path=output_md_path,
                output_csv_path=output_csv_path,
                title=title,
                surface_column_label=grouped_risk_payload["surface_column_label"],
                stratum_column_label=grouped_risk_payload["stratum_column_label"],
                cases_column_label=grouped_risk_payload["cases_column_label"],
                events_column_label=grouped_risk_payload["events_column_label"],
                risk_column_label=grouped_risk_payload["risk_column_label"],
                rows=grouped_risk_payload["rows"],
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
                "caption": str(payload.get("caption") or "Observed event counts and risks across predefined strata.").strip(),
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
