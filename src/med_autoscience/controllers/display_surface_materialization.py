from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from med_autoscience import display_layout_qc, display_registry, publication_display_contract


_INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "binary_prediction_curve_inputs_v1": "binary_prediction_curve_inputs.json",
    "time_to_event_grouped_inputs_v1": "time_to_event_grouped_inputs.json",
    "time_to_event_discrimination_calibration_inputs_v1": "time_to_event_discrimination_calibration_inputs.json",
    "time_to_event_decision_curve_inputs_v1": "time_to_event_decision_curve_inputs.json",
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


def _validate_cohort_flow_payload(path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{path.name} must contain a non-empty steps list")
    normalized: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"{path.name} steps[{index}] must be an object")
        step_id = str(step.get("step_id") or "").strip()
        label = str(step.get("label") or "").strip()
        detail = str(step.get("detail") or "").strip()
        if not step_id or not label:
            raise ValueError(f"{path.name} steps[{index}] must include step_id and label")
        raw_n = step.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} steps[{index}].n must be an integer")
        normalized.append({"step_id": step_id, "label": label, "detail": detail, "n": raw_n})
    return normalized


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
        x = _require_numeric_list(item.get("x"), label=f"{path.name} display `{expected_display_id}` series[{index}].x")
        y = _require_numeric_list(item.get("y"), label=f"{path.name} display `{expected_display_id}` series[{index}].y")
        if len(x) != len(y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` series[{index}].x and .y must have the same length"
            )
        normalized_series.append(
            {
                "label": label,
                "x": x,
                "y": y,
                "annotation": str(item.get("annotation") or "").strip(),
            }
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
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    centers = payload.get("centers")
    if not isinstance(centers, list) or not centers:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty centers list")
    normalized_centers: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for index, center in enumerate(centers):
        if not isinstance(center, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` centers[{index}] must be an object")
        center_label = _require_non_empty_string(
            center.get("center_label"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].center_label",
        )
        if center_label in seen_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{index}].center_label must be unique"
            )
        seen_labels.add(center_label)
        sample_size = _require_numeric_value(
            center.get("sample_size"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].sample_size",
        )
        if sample_size <= 0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{index}].sample_size must be positive"
            )
        estimate = _require_numeric_value(
            center.get("estimate"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].estimate",
        )
        lower = _require_numeric_value(
            center.get("lower"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].lower",
        )
        upper = _require_numeric_value(
            center.get("upper"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].upper",
        )
        if not (lower <= estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{index}] must satisfy lower <= estimate <= upper"
            )
        normalized_centers.append(
            {
                "center_label": center_label,
                "sample_size": sample_size,
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
        "reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("reference_line"),
            label=f"display `{expected_display_id}` reference_line",
        ),
        "centers": normalized_centers,
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
        return payload_path, _validate_binary_curve_display_payload(
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


def _render_cohort_flow_figure(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    title: str,
    steps: list[dict[str, Any]],
) -> None:
    figure_height = max(4.5, 1.8 * len(steps))
    fig, ax = plt.subplots(figsize=(8, figure_height))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(steps) * 2.2 + 0.5)
    ax.axis("off")
    ax.text(0.5, len(steps) * 2.05 + 0.25, title, fontsize=15, fontweight="bold", color="#213547")

    box_x = 1.1
    box_width = 7.8
    box_height = 1.2
    for index, step in enumerate(steps):
        y = len(steps) * 2.0 - index * 2.0
        box = FancyBboxPatch(
            (box_x, y - box_height / 2),
            box_width,
            box_height,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            linewidth=1.2,
            edgecolor="#547980",
            facecolor="#f6fbfb",
        )
        ax.add_patch(box)
        ax.text(
            box_x + 0.22,
            y + 0.16,
            step["label"],
            fontsize=11.5,
            fontweight="bold",
            color="#1f2d3d",
            va="center",
        )
        ax.text(
            box_x + 0.22,
            y - 0.14,
            f"n = {step['n']}",
            fontsize=11,
            color="#234b5a",
            va="center",
        )
        if step["detail"]:
            ax.text(
                box_x + 2.0,
                y - 0.14,
                step["detail"],
                fontsize=10.2,
                color="#4f6470",
                va="center",
            )
        if index < len(steps) - 1:
            next_y = len(steps) * 2.0 - (index + 1) * 2.0
            arrow = FancyArrowPatch(
                (5.0, y - box_height / 2 - 0.08),
                (5.0, next_y + box_height / 2 + 0.08),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.0,
                color="#6c8a91",
            )
            ax.add_patch(arrow)

    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
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
    groups = list(display_payload.get("groups") or [])
    if not groups:
        raise RuntimeError(f"{template_id} requires non-empty groups")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    fig.patch.set_facecolor("white")
    palette = ("#1f4e79", "#c94f3d", "#2a9d8f", "#8c6d31")
    max_time = max(max(float(item) for item in group["times"]) for group in groups)
    for index, group in enumerate(groups):
        ax.step(
            group["times"],
            group["values"],
            where="post",
            linewidth=2.0,
            color=palette[index % len(palette)],
            label=str(group["label"]),
        )
    ax.set_xlim(0.0, max_time)
    ax.set_ylim(0.0, 1.02)
    ax.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    ax.set_ylabel(str(display_payload.get("y_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    ax.set_title(str(display_payload.get("title") or "").strip(), fontsize=12.5, fontweight="bold", color="#13293d")
    _apply_publication_axes_style(ax)
    legend = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False)
    annotation_artist = None
    annotation = str(display_payload.get("annotation") or "").strip()
    if annotation:
        annotation_artist = fig.text(0.79, 0.18, annotation, ha="left", va="center", fontsize=9.5, color="#334155")
    fig.subplots_adjust(left=0.12, right=0.74, bottom=0.15, top=0.88)
    fig.canvas.draw()
    dump_json(
        layout_sidecar_path,
        _build_single_panel_layout_sidecar(
            figure=fig,
            axes=ax,
            template_id=template_id,
            metrics={"groups": groups},
            legend=legend,
            annotation_artist=annotation_artist,
        ),
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

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    fig.patch.set_facecolor("white")
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
            ax.axvspan(float(xmin), float(xmax), color=style_roles.get("highlight_band", "#E7E1D8"), alpha=0.22, zorder=0)
    for index, item in enumerate(series):
        label = str(item["label"])
        normalized_label = label.casefold()
        if "treat all" in normalized_label:
            line_color = comparator_color
        elif index == 0:
            line_color = model_color
        else:
            line_color = comparator_color
        ax.plot(
            item["x"],
            item["y"],
            linewidth=2.0,
            color=line_color,
            label=label,
        )
    if isinstance(reference_line, dict):
        ax.plot(
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
    ax.set_xlim(x_min - x_padding, x_max + x_padding)
    ax.set_ylim(y_min - y_padding, y_max + y_padding)
    ax.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    ax.set_ylabel(str(display_payload.get("y_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    ax.set_title(str(display_payload.get("title") or "").strip(), fontsize=12.5, fontweight="bold", color="#13293d")
    _apply_publication_axes_style(ax)
    handles, labels = ax.get_legend_handles_labels()
    legend_position = str(layout_override.get("legend_position") or "upper_left").strip().lower()
    if legend_position == "lower_center":
        legend = fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=max(1, len(labels)), frameon=False)
        fig.subplots_adjust(left=0.12, right=0.94, bottom=0.22, top=0.88)
    else:
        legend = fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.69, 0.84), frameon=False)
        fig.subplots_adjust(left=0.12, right=0.66, bottom=0.15, top=0.88)
    fig.canvas.draw()
    dump_json(
        layout_sidecar_path,
        _build_single_panel_layout_sidecar(
            figure=fig,
            axes=ax,
            template_id=template_id,
            metrics={"series": series, "reference_line": reference_line},
            legend=legend,
        ),
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
    centers = list(display_payload.get("centers") or [])
    if not centers:
        raise RuntimeError(f"{template_id} requires non-empty centers")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    figure_height = max(4.8, 0.72 * len(centers) + 1.8)
    fig, (label_axes, sample_axes, estimate_axes) = plt.subplots(
        1,
        3,
        figsize=(8.6, figure_height),
        sharey=True,
        gridspec_kw={"width_ratios": [1.5, 1.6, 2.6]},
    )
    fig.patch.set_facecolor("white")
    title_artist = fig.suptitle(
        str(display_payload.get("title") or "").strip(),
        fontsize=12.5,
        fontweight="bold",
        color="#13293d",
    )
    y_positions = list(range(len(centers)))
    label_axes.set_xlim(0.0, 1.0)
    label_axes.set_ylim(-0.5, len(centers) - 0.5)
    label_axes.invert_yaxis()
    label_axes.axis("off")
    label_texts = []
    for index, center in enumerate(centers):
        label_texts.append(
            label_axes.text(
                0.98,
                y_positions[index],
                str(center["center_label"]),
                ha="right",
                va="center",
                fontsize=10,
                color="#1f2937",
            )
        )

    sample_sizes = [float(center["sample_size"]) for center in centers]
    sample_axes.barh(y_positions, sample_sizes, height=0.56, color="#9db4c0", edgecolor="#6b8794")
    sample_axes.set_title("Sample Size", fontsize=10.5, fontweight="bold", color="#334155")
    sample_axes.set_yticks(y_positions)
    sample_axes.set_yticklabels([])
    _apply_publication_axes_style(sample_axes)

    lower_errors = [float(center["estimate"]) - float(center["lower"]) for center in centers]
    upper_errors = [float(center["upper"]) - float(center["estimate"]) for center in centers]
    estimate_values = [float(center["estimate"]) for center in centers]
    estimate_axes.errorbar(
        estimate_values,
        y_positions,
        xerr=[lower_errors, upper_errors],
        fmt="o",
        markersize=5.8,
        linewidth=1.2,
        capsize=0,
        color="#1f4e79",
        ecolor="#1f4e79",
    )
    reference_line = display_payload.get("reference_line")
    reference_x = None
    if isinstance(reference_line, dict) and reference_line.get("x"):
        reference_x = float(reference_line["x"][0])
        estimate_axes.axvline(reference_x, color="#6b7280", linewidth=1.0, linestyle="--")
    estimate_axes.set_yticks(y_positions)
    estimate_axes.set_yticklabels([])
    estimate_axes.set_xlabel(str(display_payload.get("x_label") or "").strip(), fontsize=11, fontweight="bold", color="#13293d")
    estimate_axes.set_title("Center Effect", fontsize=10.5, fontweight="bold", color="#334155")
    _apply_publication_axes_style(estimate_axes)

    for axes in (sample_axes, estimate_axes):
        axes.set_ylim(-0.5, len(centers) - 0.5)
        axes.invert_yaxis()

    fig.subplots_adjust(left=0.04, right=0.98, top=0.84, bottom=0.16, wspace=0.06)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    sample_xlim = sample_axes.get_xlim()
    estimate_xlim = estimate_axes.get_xlim()
    marker_half_width = max((estimate_xlim[1] - estimate_xlim[0]) * 0.02, 1e-3)
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=title_artist.get_window_extent(renderer=renderer),
            box_id="title",
            box_type="title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=estimate_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
    ]
    for index, text_artist in enumerate(label_texts, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=text_artist.get_window_extent(renderer=renderer),
                box_id=f"row_label_{index}",
                box_type="row_label",
            )
        )
    for index, (center, y_position) in enumerate(zip(centers, y_positions, strict=True), start=1):
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=sample_axes,
                figure=fig,
                x0=sample_xlim[0],
                y0=y_position - 0.28,
                x1=float(center["sample_size"]),
                y1=y_position + 0.28,
                box_id=f"sample_bar_{index}",
                box_type="sample_bar",
            )
        )
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=estimate_axes,
                figure=fig,
                x0=float(center["estimate"]) - marker_half_width,
                y0=y_position - 0.12,
                x1=float(center["estimate"]) + marker_half_width,
                y1=y_position + 0.12,
                box_id=f"estimate_marker_{index}",
                box_type="estimate_marker",
            )
        )
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=estimate_axes,
                figure=fig,
                x0=float(center["lower"]),
                y0=y_position,
                x1=float(center["upper"]),
                y1=y_position,
                box_id=f"ci_segment_{index}",
                box_type="ci_segment",
            )
        )
    guide_boxes: list[dict[str, Any]] = []
    if reference_x is not None:
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=estimate_axes,
                figure=fig,
                x0=reference_x,
                y0=-0.45,
                x1=reference_x,
                y1=len(centers) - 0.55,
                box_id="reference_line",
                box_type="reference_line",
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
                    bbox=sample_axes.get_window_extent(renderer=renderer),
                    box_id="sample_panel",
                    box_type="sample_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=estimate_axes.get_window_extent(renderer=renderer),
                    box_id="estimate_panel",
                    box_type="estimate_panel",
                ),
            ],
            "guide_boxes": guide_boxes,
            "metrics": {"centers": centers},
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
            steps = _validate_cohort_flow_payload(payload_path, payload)
            title = str(payload.get("title") or "Cohort flow").strip() or "Cohort flow"
            figure_id = _resolve_figure_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_cohort_flow.svg"
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_cohort_flow.png"
            _render_cohort_flow_figure(
                output_svg_path=output_svg_path,
                output_png_path=output_png_path,
                title=title,
                steps=steps,
            )
            written_files.extend([str(output_svg_path), str(output_png_path)])
            entry = {
                "figure_id": figure_id,
                "template_id": spec.shell_id,
                "renderer_family": spec.renderer_family,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.shell_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": title,
                "caption": str(payload.get("caption") or "Study cohort flow and analysis population accounting.").strip(),
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
