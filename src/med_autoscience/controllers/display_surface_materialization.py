from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import html
import json
import math
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
from matplotlib.textpath import TextPath  # noqa: E402

from med_autoscience import display_layout_qc, display_pack_lock, display_pack_runtime, display_registry, publication_display_contract  # noqa: E402
from med_autoscience.display_source_contract import INPUT_FILENAME_BY_SCHEMA_ID, TABLE_INPUT_FILENAME_BY_SCHEMA_ID  # noqa: E402
from med_autoscience.display_pack_resolver import get_pack_id, get_template_short_id  # noqa: E402


_INPUT_FILENAME_BY_SCHEMA_ID = INPUT_FILENAME_BY_SCHEMA_ID
_TABLE_INPUT_FILENAME_BY_SCHEMA_ID = TABLE_INPUT_FILENAME_BY_SCHEMA_ID
_ILLUSTRATION_INPUT_FILENAME_BY_SCHEMA_ID = {
    "cohort_flow_shell_inputs_v1": "cohort_flow.json",
    "submission_graphical_abstract_inputs_v1": "submission_graphical_abstract.json",
    "workflow_fact_sheet_panel_inputs_v1": "workflow_fact_sheet_panel.json",
    "design_evidence_composite_shell_inputs_v1": "design_evidence_composite_shell.json",
    "baseline_missingness_qc_panel_inputs_v1": "baseline_missingness_qc_panel.json",
    "center_coverage_batch_transportability_panel_inputs_v1": "center_coverage_batch_transportability_panel.json",
    "transportability_recalibration_governance_panel_inputs_v1": "transportability_recalibration_governance_panel.json",
}
_ILLUSTRATION_OUTPUT_STEM_BY_TEMPLATE_SHORT_ID = {
    "cohort_flow_figure": "cohort_flow",
    "submission_graphical_abstract": "graphical_abstract",
    "workflow_fact_sheet_panel": "workflow_fact_sheet_panel",
    "design_evidence_composite_shell": "design_evidence_composite_shell",
    "baseline_missingness_qc_panel": "baseline_missingness_qc_panel",
    "center_coverage_batch_transportability_panel": "center_coverage_batch_transportability_panel",
    "transportability_recalibration_governance_panel": "transportability_recalibration_governance_panel",
}
_ILLUSTRATION_DEFAULT_TEXT_BY_TEMPLATE_SHORT_ID = {
    "cohort_flow_figure": (
        "Cohort flow",
        "Study cohort flow and analysis population accounting.",
    ),
    "submission_graphical_abstract": (
        "Submission graphical abstract",
        "",
    ),
    "workflow_fact_sheet_panel": (
        "Study workflow fact sheet",
        "Structured study-design and workflow summary for the audited manuscript-facing surface.",
    ),
    "design_evidence_composite_shell": (
        "Study design evidence composite",
        "Bounded study-design overview with workflow ribbon and manuscript-facing summary panels.",
    ),
    "baseline_missingness_qc_panel": (
        "Baseline balance, missingness, and QC overview",
        "Bounded cohort-quality overview combining baseline balance, missingness, and QC summary evidence.",
    ),
    "center_coverage_batch_transportability_panel": (
        "Center coverage, batch shift, and transportability overview",
        "Bounded center-coverage overview combining support counts, batch-shift governance, and transportability boundary evidence.",
    ),
    "transportability_recalibration_governance_panel": (
        "Transportability recalibration governance overview",
        "Bounded center-coverage overview combining support counts, batch-shift governance, and recalibration decision evidence.",
    ),
}
_TABLE_OUTPUT_CONFIG_BY_TEMPLATE_SHORT_ID: dict[str, dict[str, Any]] = {
    "table1_baseline_characteristics": {
        "stem": "baseline_characteristics",
        "needs_csv": True,
        "default_title": "Baseline characteristics",
        "default_caption": "Baseline characteristics across prespecified groups.",
    },
    "table2_time_to_event_performance_summary": {
        "stem": "time_to_event_performance_summary",
        "needs_csv": False,
        "default_title": "Time-to-event model performance summary",
        "default_caption": "Time-to-event discrimination and error metrics across analysis cohorts.",
    },
    "table3_clinical_interpretation_summary": {
        "stem": "clinical_interpretation_summary",
        "needs_csv": False,
        "default_title": "Clinical interpretation summary",
        "default_caption": "Clinical interpretation anchors for prespecified risk groups and use cases.",
    },
    "performance_summary_table_generic": {
        "stem": "performance_summary_table_generic",
        "needs_csv": True,
        "default_title": "Performance summary",
        "default_caption": "Structured repeated-validation performance summaries across candidate packages.",
    },
    "grouped_risk_event_summary_table": {
        "stem": "grouped_risk_event_summary_table",
        "needs_csv": True,
        "default_title": "Grouped risk event summary",
        "default_caption": "Observed case counts, event counts, and absolute risks across grouped-risk strata.",
    },
}
_REPO_ROOT = Path(__file__).resolve().parents[3]


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


def _require_namespaced_registry_id(identifier: str, *, label: str) -> tuple[str, str]:
    try:
        pack_id = get_pack_id(identifier)
        short_id = get_template_short_id(identifier)
    except ValueError as exc:
        raise ValueError(f"{label} must be namespaced as '<pack_id>::<template_id>'") from exc
    return pack_id, short_id


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
        return f"S{int(supplementary_match.group(1))}"
    supplementary_current_match = re.fullmatch(r"S(\d+)", item, flags=re.IGNORECASE)
    if supplementary_current_match:
        return f"S{int(supplementary_current_match.group(1))}"
    supplementary_short_match = re.fullmatch(r"FS(\d+)", item, flags=re.IGNORECASE)
    if supplementary_short_match:
        return f"S{int(supplementary_short_match.group(1))}"
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
    appendix_alias_match = re.fullmatch(r"A(\d+)", item, flags=re.IGNORECASE)
    if appendix_alias_match:
        return f"TA{int(appendix_alias_match.group(1))}"
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
    updated = [
        item
        for item in items
        if str(item.get(key) or "").strip() != value and str(item.get("catalog_id") or "").strip() != value
    ]
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
            """\
            # Paper Authority Surface

            - This directory is the manuscript-facing authority surface for the active study line.
            - Figures: `paper/figures/figure_catalog.json` + `paper/figures/generated/`
            - Tables: `paper/tables/table_catalog.json` + `paper/tables/generated/`
            - Canonical submission package: `paper/submission_minimal/`
            - Human-facing delivery mirror: `../manuscript/`
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


def _require_strictly_increasing_numeric_list(value: object, *, label: str, min_length: int = 2) -> list[float]:
    normalized = _require_numeric_list(value, label=label, min_length=min_length)
    for index, (previous_value, current_value) in enumerate(zip(normalized[:-1], normalized[1:], strict=True), start=1):
        if current_value > previous_value:
            continue
        raise ValueError(f"{label}[{index}] must be strictly greater than the previous value")
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
    expected_shell_id = display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
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
    time_horizon_months = payload.get("time_horizon_months")
    normalized_time_horizon_months = (
        _require_non_negative_int(
            time_horizon_months,
            label=f"{path.name} display `{expected_display_id}` time_horizon_months",
            allow_zero=False,
        )
        if time_horizon_months is not None
        else None
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
        "time_horizon_months": normalized_time_horizon_months,
    }


def _evidence_payload_path(*, paper_root: Path, input_schema_id: str) -> Path:
    try:
        filename = _INPUT_FILENAME_BY_SCHEMA_ID[input_schema_id]
    except KeyError as exc:
        raise ValueError(f"unsupported evidence input schema `{input_schema_id}`") from exc
    return paper_root / filename


def _illustration_payload_path(*, paper_root: Path, input_schema_id: str) -> Path:
    try:
        filename = _ILLUSTRATION_INPUT_FILENAME_BY_SCHEMA_ID[input_schema_id]
    except KeyError as exc:
        raise ValueError(f"unsupported illustration input schema `{input_schema_id}`") from exc
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
    time_horizon_months = payload.get("time_horizon_months")
    normalized_time_horizon_months = (
        _require_non_negative_int(
            time_horizon_months,
            label=f"{path.name} display `{expected_display_id}` time_horizon_months",
            allow_zero=False,
        )
        if time_horizon_months is not None
        else None
    )
    _, expected_template_short_id = _require_namespaced_registry_id(
        expected_template_id,
        label=f"{path.name} display `{expected_display_id}` template_id",
    )
    if expected_template_short_id == "time_to_event_decision_curve":
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
            "time_horizon_months": normalized_time_horizon_months,
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
        "time_horizon_months": normalized_time_horizon_months,
    }


def _validate_time_dependent_roc_comparison_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)

        analysis_window_label = _require_non_empty_string(
            panel_payload.get("analysis_window_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].analysis_window_label",
        )
        normalized_series = _validate_curve_series_payload(
            path=path,
            payload=panel_payload.get("series"),
            label=f"display `{expected_display_id}` panels[{panel_index}].series",
        )
        seen_series_labels: set[str] = set()
        for series_index, series_payload in enumerate(normalized_series):
            series_label = str(series_payload["label"])
            if series_label in seen_series_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].series[{series_index}].label must be unique within the panel"
                )
            seen_series_labels.add(series_label)
        time_horizon_months = panel_payload.get("time_horizon_months")
        normalized_time_horizon_months = (
            _require_non_negative_int(
                time_horizon_months,
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].time_horizon_months",
                allow_zero=False,
            )
            if time_horizon_months is not None
            else None
        )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "analysis_window_label": analysis_window_label,
                "time_horizon_months": normalized_time_horizon_months,
                "annotation": str(panel_payload.get("annotation") or "").strip(),
                "series": normalized_series,
                "reference_line": _validate_reference_line_payload(
                    path=path,
                    payload=panel_payload.get("reference_line"),
                    label=f"display `{expected_display_id}` panels[{panel_index}].reference_line",
                ),
            }
        )

    if normalized_panels:
        expected_series_labels = tuple(series["label"] for series in normalized_panels[0]["series"])
        for panel_index, panel in enumerate(normalized_panels[1:], start=1):
            observed_series_labels = tuple(series["label"] for series in panel["series"])
            if observed_series_labels == expected_series_labels:
                continue
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].series labels must match the first panel"
            )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "panels": normalized_panels,
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


def _validate_time_to_event_landmark_performance_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    summaries_payload = payload.get("landmark_summaries")
    if not isinstance(summaries_payload, list) or not summaries_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty landmark_summaries list")

    normalized_summaries: list[dict[str, Any]] = []
    seen_window_labels: set[str] = set()
    seen_analysis_window_labels: set[str] = set()
    for index, item in enumerate(summaries_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` landmark_summaries[{index}] must be an object")
        window_label = _require_non_empty_string(
            item.get("window_label"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].window_label",
        )
        if window_label in seen_window_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].window_label must be unique"
            )
        analysis_window_label = _require_non_empty_string(
            item.get("analysis_window_label"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].analysis_window_label",
        )
        if analysis_window_label in seen_analysis_window_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].analysis_window_label must be unique"
            )
        landmark_months = _require_non_negative_int(
            item.get("landmark_months"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].landmark_months",
            allow_zero=False,
        )
        prediction_months = _require_non_negative_int(
            item.get("prediction_months"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].prediction_months",
            allow_zero=False,
        )
        if prediction_months <= landmark_months:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].prediction_months must exceed landmark_months"
            )
        c_index = _require_numeric_value(
            item.get("c_index"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].c_index",
        )
        if c_index < 0.0 or c_index > 1.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].c_index must stay within [0, 1]"
            )
        brier_score = _require_numeric_value(
            item.get("brier_score"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].brier_score",
        )
        if brier_score < 0.0 or brier_score > 1.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].brier_score must stay within [0, 1]"
            )
        calibration_slope = _require_numeric_value(
            item.get("calibration_slope"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].calibration_slope",
        )
        if not math.isfinite(calibration_slope):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].calibration_slope must be finite"
            )
        seen_window_labels.add(window_label)
        seen_analysis_window_labels.add(analysis_window_label)
        normalized_summaries.append(
            {
                "window_label": window_label,
                "analysis_window_label": analysis_window_label,
                "landmark_months": landmark_months,
                "prediction_months": prediction_months,
                "c_index": c_index,
                "brier_score": brier_score,
                "calibration_slope": calibration_slope,
                "annotation": str(item.get("annotation") or "").strip(),
            }
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
        "discrimination_panel_title": _require_non_empty_string(
            payload.get("discrimination_panel_title"),
            label=f"{path.name} display `{expected_display_id}` discrimination_panel_title",
        ),
        "discrimination_x_label": _require_non_empty_string(
            payload.get("discrimination_x_label"),
            label=f"{path.name} display `{expected_display_id}` discrimination_x_label",
        ),
        "error_panel_title": _require_non_empty_string(
            payload.get("error_panel_title"),
            label=f"{path.name} display `{expected_display_id}` error_panel_title",
        ),
        "error_x_label": _require_non_empty_string(
            payload.get("error_x_label"),
            label=f"{path.name} display `{expected_display_id}` error_x_label",
        ),
        "calibration_panel_title": _require_non_empty_string(
            payload.get("calibration_panel_title"),
            label=f"{path.name} display `{expected_display_id}` calibration_panel_title",
        ),
        "calibration_x_label": _require_non_empty_string(
            payload.get("calibration_x_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_x_label",
        ),
        "landmark_summaries": normalized_summaries,
    }


def _validate_time_to_event_threshold_governance_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    threshold_summaries_payload = payload.get("threshold_summaries")
    if not isinstance(threshold_summaries_payload, list) or not threshold_summaries_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty threshold_summaries list"
        )
    normalized_threshold_summaries: list[dict[str, Any]] = []
    seen_threshold_labels: set[str] = set()
    previous_threshold = -1.0
    for index, item in enumerate(threshold_summaries_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` threshold_summaries[{index}] must be an object"
            )
        threshold_label = _require_non_empty_string(
            item.get("threshold_label"),
            label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold_label",
        )
        if threshold_label in seen_threshold_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold_label must be unique"
            )
        threshold = _require_probability_value(
            item.get("threshold"),
            label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold",
        )
        if threshold <= previous_threshold:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold must be strictly increasing"
            )
        previous_threshold = threshold
        seen_threshold_labels.add(threshold_label)
        normalized_threshold_summaries.append(
            {
                "threshold_label": threshold_label,
                "threshold": threshold,
                "sensitivity": _require_probability_value(
                    item.get("sensitivity"),
                    label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].sensitivity",
                ),
                "specificity": _require_probability_value(
                    item.get("specificity"),
                    label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].specificity",
                ),
                "net_benefit": _require_numeric_value(
                    item.get("net_benefit"),
                    label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].net_benefit",
                ),
            }
        )

    risk_group_summaries_payload = payload.get("risk_group_summaries")
    if not isinstance(risk_group_summaries_payload, list) or not risk_group_summaries_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty risk_group_summaries list"
        )
    normalized_risk_group_summaries: list[dict[str, Any]] = []
    previous_group_order = 0
    for index, item in enumerate(risk_group_summaries_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}] must be an object"
            )
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_group_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].group_order must be strictly increasing"
            )
        previous_group_order = group_order
        n = _require_non_negative_int(
            item.get("n"),
            label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].n",
            allow_zero=False,
        )
        events = _require_non_negative_int(
            item.get("events"),
            label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events",
        )
        if events > n:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events must not exceed .n"
            )
        normalized_risk_group_summaries.append(
            {
                "group_label": _require_non_empty_string(
                    item.get("group_label"),
                    label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].group_label",
                ),
                "group_order": group_order,
                "n": n,
                "events": events,
                "predicted_risk": _require_probability_value(
                    item.get("predicted_risk"),
                    label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].predicted_risk",
                ),
                "observed_risk": _require_probability_value(
                    item.get("observed_risk"),
                    label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].observed_risk",
                ),
            }
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
        "threshold_panel_title": _require_non_empty_string(
            payload.get("threshold_panel_title"),
            label=f"{path.name} display `{expected_display_id}` threshold_panel_title",
        ),
        "calibration_panel_title": _require_non_empty_string(
            payload.get("calibration_panel_title"),
            label=f"{path.name} display `{expected_display_id}` calibration_panel_title",
        ),
        "calibration_x_label": _require_non_empty_string(
            payload.get("calibration_x_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_x_label",
        ),
        "threshold_summaries": normalized_threshold_summaries,
        "risk_group_summaries": normalized_risk_group_summaries,
    }


def _validate_time_to_event_multihorizon_calibration_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    previous_time_horizon = 0
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique")
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        time_horizon_months = _require_non_negative_int(
            panel_payload.get("time_horizon_months"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].time_horizon_months",
            allow_zero=False,
        )
        if time_horizon_months <= previous_time_horizon:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].time_horizon_months must be strictly increasing"
            )
        previous_time_horizon = time_horizon_months

        calibration_summary_payload = panel_payload.get("calibration_summary")
        if not isinstance(calibration_summary_payload, list) or not calibration_summary_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary must be a non-empty list"
            )
        normalized_summary: list[dict[str, Any]] = []
        previous_group_order = 0
        for group_index, item in enumerate(calibration_summary_payload):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}] must be an object"
                )
            group_order = _require_non_negative_int(
                item.get("group_order"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                    f"calibration_summary[{group_index}].group_order"
                ),
                allow_zero=False,
            )
            if group_order <= previous_group_order:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].group_order must be strictly increasing"
                )
            previous_group_order = group_order
            n = _require_non_negative_int(
                item.get("n"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].n"
                ),
                allow_zero=False,
            )
            events = _require_non_negative_int(
                item.get("events"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].events"
                ),
            )
            if events > n:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].events must not exceed .n"
                )
            normalized_summary.append(
                {
                    "group_label": _require_non_empty_string(
                        item.get("group_label"),
                        label=(
                            f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                            f"calibration_summary[{group_index}].group_label"
                        ),
                    ),
                    "group_order": group_order,
                    "n": n,
                    "events": events,
                    "predicted_risk": _require_probability_value(
                        item.get("predicted_risk"),
                        label=(
                            f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                            f"calibration_summary[{group_index}].predicted_risk"
                        ),
                    ),
                    "observed_risk": _require_probability_value(
                        item.get("observed_risk"),
                        label=(
                            f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                            f"calibration_summary[{group_index}].observed_risk"
                        ),
                    ),
                }
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "time_horizon_months": time_horizon_months,
                "calibration_summary": normalized_summary,
            }
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
        "x_label": _require_non_empty_string(
            payload.get("x_label"),
            label=f"{path.name} display `{expected_display_id}` x_label",
        ),
        "panels": normalized_panels,
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
    _, expected_template_short_id = _require_namespaced_registry_id(
        expected_template_id,
        label=f"{path.name} display `{expected_display_id}` template_id",
    )
    if expected_template_short_id == "time_to_event_risk_group_summary":
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
            sample_size = _require_non_negative_int(
                item.get("sample_size"),
                label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].sample_size",
                allow_zero=False,
            )
            events_5y = _require_non_negative_int(
                item.get("events_5y"),
                label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events_5y",
            )
            if events_5y > sample_size:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events_5y must not exceed .sample_size"
                )
            normalized_summaries.append(
                {
                    "label": _require_non_empty_string(
                        item.get("label"),
                        label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].label",
                    ),
                    "sample_size": sample_size,
                    "events_5y": events_5y,
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


def _validate_time_to_event_stratified_cumulative_incidence_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        groups_payload = panel_payload.get("groups")
        if not isinstance(groups_payload, list) or not groups_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups must be a non-empty list"
            )
        normalized_groups: list[dict[str, Any]] = []
        seen_group_labels: set[str] = set()
        for group_index, group_payload in enumerate(groups_payload):
            if not isinstance(group_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}] must be an object"
                )
            group_label = _require_non_empty_string(
                group_payload.get("label"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].groups[{group_index}].label"
                ),
            )
            if group_label in seen_group_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}].label must be unique within the panel"
                )
            seen_group_labels.add(group_label)
            times = _require_strictly_increasing_numeric_list(
                group_payload.get("times"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].groups[{group_index}].times"
                ),
            )
            values = _require_numeric_list(
                group_payload.get("values"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].groups[{group_index}].values"
                ),
            )
            if len(times) != len(values):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}].times and .values must have the same length"
                )
            normalized_values: list[float] = []
            previous_value: float | None = None
            for point_index, raw_value in enumerate(values):
                probability = _require_probability_value(
                    raw_value,
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"panels[{panel_index}].groups[{group_index}].values[{point_index}]"
                    ),
                )
                if previous_value is not None and probability + 1e-12 < previous_value:
                    raise ValueError(
                        f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}].values must be monotonic non-decreasing"
                    )
                normalized_values.append(probability)
                previous_value = probability
            normalized_groups.append({"label": group_label, "times": times, "values": normalized_values})
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "annotation": str(panel_payload.get("annotation") or "").strip(),
                "groups": normalized_groups,
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
        "panels": normalized_panels,
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
        n = _require_non_negative_int(
            item.get("n"),
            label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].n",
            allow_zero=False,
        )
        events_5y = _require_non_negative_int(
            item.get("events_5y"),
            label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].events_5y",
        )
        if events_5y > n:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_summary[{index}].events_5y must not exceed .n"
            )
        normalized_summary.append(
            {
                "group_label": _require_non_empty_string(
                    item.get("group_label"),
                    label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].group_label",
                ),
                "group_order": group_order,
                "n": n,
                "events_5y": events_5y,
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
        matched_summary = next(
            (
                item
                for item in normalized_summary
                if str(item.get("group_label") or "").strip() == str(normalized_callout.get("group_label") or "").strip()
            ),
            None,
        )
        if matched_summary is None:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_callout.group_label must match calibration_summary"
            )
        if (
            abs(float(normalized_callout["predicted_risk_5y"]) - float(matched_summary["predicted_risk_5y"])) > 1e-12
            or abs(float(normalized_callout["observed_risk_5y"]) - float(matched_summary["observed_risk_5y"])) > 1e-12
            or (
                normalized_callout.get("events_5y") is not None
                and int(normalized_callout["events_5y"]) != int(matched_summary["events_5y"])
            )
            or (normalized_callout.get("n") is not None and int(normalized_callout["n"]) != int(matched_summary["n"]))
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_callout must match the referenced calibration_summary row"
            )

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


def _validate_celltype_signature_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    embedding_panel_title = _require_non_empty_string(
        payload.get("embedding_panel_title"),
        label=f"{path.name} display `{expected_display_id}` embedding_panel_title",
    )
    embedding_x_label = _require_non_empty_string(
        payload.get("embedding_x_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_x_label",
    )
    embedding_y_label = _require_non_empty_string(
        payload.get("embedding_y_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_y_label",
    )
    heatmap_panel_title = _require_non_empty_string(
        payload.get("heatmap_panel_title"),
        label=f"{path.name} display `{expected_display_id}` heatmap_panel_title",
    )
    heatmap_x_label = _require_non_empty_string(
        payload.get("heatmap_x_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_x_label",
    )
    heatmap_y_label = _require_non_empty_string(
        payload.get("heatmap_y_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_y_label",
    )
    embedding_points = payload.get("embedding_points")
    if not isinstance(embedding_points, list) or not embedding_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty embedding_points list")
    normalized_embedding_points: list[dict[str, Any]] = []
    observed_groups: set[str] = set()
    for index, item in enumerate(embedding_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` embedding_points[{index}] must be an object")
        group_label = _require_non_empty_string(
            item.get("group"),
            label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].group",
        )
        observed_groups.add(group_label)
        normalized_embedding_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].y",
                ),
                "group": group_label,
            }
        )

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
    if observed_groups != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match embedding point groups"
        )
    expected_coordinates = {(column["label"], row["label"]) for row in row_order for column in column_order}
    if observed_coordinates != expected_coordinates:
        raise ValueError(f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "embedding_panel_title": embedding_panel_title,
        "embedding_x_label": embedding_x_label,
        "embedding_y_label": embedding_y_label,
        "embedding_annotation": str(payload.get("embedding_annotation") or "").strip(),
        "embedding_points": normalized_embedding_points,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


def _validate_single_cell_atlas_overview_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    embedding_panel_title = _require_non_empty_string(
        payload.get("embedding_panel_title"),
        label=f"{path.name} display `{expected_display_id}` embedding_panel_title",
    )
    embedding_x_label = _require_non_empty_string(
        payload.get("embedding_x_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_x_label",
    )
    embedding_y_label = _require_non_empty_string(
        payload.get("embedding_y_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_y_label",
    )
    composition_panel_title = _require_non_empty_string(
        payload.get("composition_panel_title"),
        label=f"{path.name} display `{expected_display_id}` composition_panel_title",
    )
    composition_x_label = _require_non_empty_string(
        payload.get("composition_x_label"),
        label=f"{path.name} display `{expected_display_id}` composition_x_label",
    )
    composition_y_label = _require_non_empty_string(
        payload.get("composition_y_label"),
        label=f"{path.name} display `{expected_display_id}` composition_y_label",
    )
    heatmap_panel_title = _require_non_empty_string(
        payload.get("heatmap_panel_title"),
        label=f"{path.name} display `{expected_display_id}` heatmap_panel_title",
    )
    heatmap_x_label = _require_non_empty_string(
        payload.get("heatmap_x_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_x_label",
    )
    heatmap_y_label = _require_non_empty_string(
        payload.get("heatmap_y_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_y_label",
    )

    embedding_points = payload.get("embedding_points")
    if not isinstance(embedding_points, list) or not embedding_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty embedding_points list")
    normalized_embedding_points: list[dict[str, Any]] = []
    observed_states: set[str] = set()
    for index, item in enumerate(embedding_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` embedding_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].state_label",
        )
        observed_states.add(state_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].y",
            ),
            "state_label": state_label,
        }
        group_label = str(item.get("group_label") or "").strip()
        if group_label:
            normalized_point["group_label"] = group_label
        normalized_embedding_points.append(normalized_point)

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
    declared_columns = {item["label"] for item in column_order}
    if observed_states != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match embedding point state labels"
        )

    composition_groups = payload.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty composition_groups list")
    normalized_composition_groups: list[dict[str, Any]] = []
    seen_group_labels: set[str] = set()
    previous_group_order = 0
    for index, item in enumerate(composition_groups):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` composition_groups[{index}] must be an object")
        group_label = _require_non_empty_string(
            item.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_group_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups group_order must be strictly increasing"
            )
        previous_group_order = group_order
        state_proportions = item.get("state_proportions")
        if not isinstance(state_proportions, list) or not state_proportions:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions must be non-empty"
            )
        normalized_state_proportions: list[dict[str, Any]] = []
        seen_state_labels: set[str] = set()
        proportion_sum = 0.0
        for state_index, state_item in enumerate(state_proportions):
            if not isinstance(state_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions[{state_index}] must be an object"
                )
            state_label = _require_non_empty_string(
                state_item.get("state_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].state_label"
                ),
            )
            if state_label in seen_state_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
                )
            seen_state_labels.add(state_label)
            proportion = _require_probability_value(
                state_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].proportion"
                ),
            )
            proportion_sum += proportion
            normalized_state_proportions.append({"state_label": state_label, "proportion": proportion})
        if seen_state_labels != declared_columns:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
            )
        if abs(proportion_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] proportions must sum to 1"
            )
        normalized_composition_groups.append(
            {
                "group_label": group_label,
                "group_order": group_order,
                "state_proportions": normalized_state_proportions,
            }
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
        "embedding_panel_title": embedding_panel_title,
        "embedding_x_label": embedding_x_label,
        "embedding_y_label": embedding_y_label,
        "embedding_annotation": str(payload.get("embedding_annotation") or "").strip(),
        "embedding_points": normalized_embedding_points,
        "composition_panel_title": composition_panel_title,
        "composition_x_label": composition_x_label,
        "composition_y_label": composition_y_label,
        "composition_annotation": str(payload.get("composition_annotation") or "").strip(),
        "composition_groups": normalized_composition_groups,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


def _validate_atlas_spatial_bridge_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    atlas_panel_title = _require_non_empty_string(
        payload.get("atlas_panel_title"),
        label=f"{path.name} display `{expected_display_id}` atlas_panel_title",
    )
    atlas_x_label = _require_non_empty_string(
        payload.get("atlas_x_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_x_label",
    )
    atlas_y_label = _require_non_empty_string(
        payload.get("atlas_y_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_y_label",
    )
    spatial_panel_title = _require_non_empty_string(
        payload.get("spatial_panel_title"),
        label=f"{path.name} display `{expected_display_id}` spatial_panel_title",
    )
    spatial_x_label = _require_non_empty_string(
        payload.get("spatial_x_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_x_label",
    )
    spatial_y_label = _require_non_empty_string(
        payload.get("spatial_y_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_y_label",
    )
    composition_panel_title = _require_non_empty_string(
        payload.get("composition_panel_title"),
        label=f"{path.name} display `{expected_display_id}` composition_panel_title",
    )
    composition_x_label = _require_non_empty_string(
        payload.get("composition_x_label"),
        label=f"{path.name} display `{expected_display_id}` composition_x_label",
    )
    composition_y_label = _require_non_empty_string(
        payload.get("composition_y_label"),
        label=f"{path.name} display `{expected_display_id}` composition_y_label",
    )
    heatmap_panel_title = _require_non_empty_string(
        payload.get("heatmap_panel_title"),
        label=f"{path.name} display `{expected_display_id}` heatmap_panel_title",
    )
    heatmap_x_label = _require_non_empty_string(
        payload.get("heatmap_x_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_x_label",
    )
    heatmap_y_label = _require_non_empty_string(
        payload.get("heatmap_y_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_y_label",
    )

    atlas_points = payload.get("atlas_points")
    if not isinstance(atlas_points, list) or not atlas_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty atlas_points list")
    normalized_atlas_points: list[dict[str, Any]] = []
    observed_atlas_states: set[str] = set()
    for index, item in enumerate(atlas_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` atlas_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].state_label",
        )
        observed_atlas_states.add(state_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].y",
            ),
            "state_label": state_label,
        }
        group_label = str(item.get("group_label") or "").strip()
        if group_label:
            normalized_point["group_label"] = group_label
        normalized_atlas_points.append(normalized_point)

    spatial_points = payload.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty spatial_points list")
    normalized_spatial_points: list[dict[str, Any]] = []
    observed_spatial_states: set[str] = set()
    for index, item in enumerate(spatial_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` spatial_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].state_label",
        )
        observed_spatial_states.add(state_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].y",
            ),
            "state_label": state_label,
        }
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_spatial_points.append(normalized_point)

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
    declared_columns = {item["label"] for item in column_order}
    if observed_atlas_states != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match atlas point state labels"
        )
    if observed_spatial_states != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match spatial point state labels"
        )

    composition_groups = payload.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty composition_groups list")
    normalized_composition_groups: list[dict[str, Any]] = []
    seen_group_labels: set[str] = set()
    previous_group_order = 0
    for index, item in enumerate(composition_groups):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` composition_groups[{index}] must be an object")
        group_label = _require_non_empty_string(
            item.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_group_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups group_order must be strictly increasing"
            )
        previous_group_order = group_order
        state_proportions = item.get("state_proportions")
        if not isinstance(state_proportions, list) or not state_proportions:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions must be non-empty"
            )
        normalized_state_proportions: list[dict[str, Any]] = []
        seen_state_labels: set[str] = set()
        proportion_sum = 0.0
        for state_index, state_item in enumerate(state_proportions):
            if not isinstance(state_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions[{state_index}] must be an object"
                )
            state_label = _require_non_empty_string(
                state_item.get("state_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].state_label"
                ),
            )
            if state_label in seen_state_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
                )
            seen_state_labels.add(state_label)
            proportion = _require_probability_value(
                state_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].proportion"
                ),
            )
            proportion_sum += proportion
            normalized_state_proportions.append({"state_label": state_label, "proportion": proportion})
        if seen_state_labels != declared_columns:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
            )
        if abs(proportion_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] proportions must sum to 1"
            )
        normalized_composition_groups.append(
            {
                "group_label": group_label,
                "group_order": group_order,
                "state_proportions": normalized_state_proportions,
            }
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
        "atlas_panel_title": atlas_panel_title,
        "atlas_x_label": atlas_x_label,
        "atlas_y_label": atlas_y_label,
        "atlas_annotation": str(payload.get("atlas_annotation") or "").strip(),
        "atlas_points": normalized_atlas_points,
        "spatial_panel_title": spatial_panel_title,
        "spatial_x_label": spatial_x_label,
        "spatial_y_label": spatial_y_label,
        "spatial_annotation": str(payload.get("spatial_annotation") or "").strip(),
        "spatial_points": normalized_spatial_points,
        "composition_panel_title": composition_panel_title,
        "composition_x_label": composition_x_label,
        "composition_y_label": composition_y_label,
        "composition_annotation": str(payload.get("composition_annotation") or "").strip(),
        "composition_groups": normalized_composition_groups,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


def _validate_spatial_niche_map_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    spatial_panel_title = _require_non_empty_string(
        payload.get("spatial_panel_title"),
        label=f"{path.name} display `{expected_display_id}` spatial_panel_title",
    )
    spatial_x_label = _require_non_empty_string(
        payload.get("spatial_x_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_x_label",
    )
    spatial_y_label = _require_non_empty_string(
        payload.get("spatial_y_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_y_label",
    )
    composition_panel_title = _require_non_empty_string(
        payload.get("composition_panel_title"),
        label=f"{path.name} display `{expected_display_id}` composition_panel_title",
    )
    composition_x_label = _require_non_empty_string(
        payload.get("composition_x_label"),
        label=f"{path.name} display `{expected_display_id}` composition_x_label",
    )
    composition_y_label = _require_non_empty_string(
        payload.get("composition_y_label"),
        label=f"{path.name} display `{expected_display_id}` composition_y_label",
    )
    heatmap_panel_title = _require_non_empty_string(
        payload.get("heatmap_panel_title"),
        label=f"{path.name} display `{expected_display_id}` heatmap_panel_title",
    )
    heatmap_x_label = _require_non_empty_string(
        payload.get("heatmap_x_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_x_label",
    )
    heatmap_y_label = _require_non_empty_string(
        payload.get("heatmap_y_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_y_label",
    )

    spatial_points = payload.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty spatial_points list")
    normalized_spatial_points: list[dict[str, Any]] = []
    observed_niches: set[str] = set()
    for index, item in enumerate(spatial_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` spatial_points[{index}] must be an object")
        niche_label = _require_non_empty_string(
            item.get("niche_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].niche_label",
        )
        observed_niches.add(niche_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].y",
            ),
            "niche_label": niche_label,
        }
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_spatial_points.append(normalized_point)

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
    declared_columns = {item["label"] for item in column_order}
    if observed_niches != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match spatial point niche labels"
        )

    composition_groups = payload.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty composition_groups list")
    normalized_composition_groups: list[dict[str, Any]] = []
    seen_group_labels: set[str] = set()
    previous_group_order = 0
    for index, item in enumerate(composition_groups):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` composition_groups[{index}] must be an object")
        group_label = _require_non_empty_string(
            item.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_group_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups group_order must be strictly increasing"
            )
        previous_group_order = group_order
        niche_proportions = item.get("niche_proportions")
        if not isinstance(niche_proportions, list) or not niche_proportions:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].niche_proportions must be non-empty"
            )
        normalized_niche_proportions: list[dict[str, Any]] = []
        seen_niche_labels: set[str] = set()
        proportion_sum = 0.0
        for niche_index, niche_item in enumerate(niche_proportions):
            if not isinstance(niche_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}].niche_proportions[{niche_index}] must be an object"
                )
            niche_label = _require_non_empty_string(
                niche_item.get("niche_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"niche_proportions[{niche_index}].niche_label"
                ),
            )
            if niche_label in seen_niche_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared niche labels exactly once"
                )
            seen_niche_labels.add(niche_label)
            proportion = _require_probability_value(
                niche_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"niche_proportions[{niche_index}].proportion"
                ),
            )
            proportion_sum += proportion
            normalized_niche_proportions.append({"niche_label": niche_label, "proportion": proportion})
        if seen_niche_labels != declared_columns:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared niche labels exactly once"
            )
        if abs(proportion_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] proportions must sum to 1"
            )
        normalized_composition_groups.append(
            {
                "group_label": group_label,
                "group_order": group_order,
                "niche_proportions": normalized_niche_proportions,
            }
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
        "spatial_panel_title": spatial_panel_title,
        "spatial_x_label": spatial_x_label,
        "spatial_y_label": spatial_y_label,
        "spatial_annotation": str(payload.get("spatial_annotation") or "").strip(),
        "spatial_points": normalized_spatial_points,
        "composition_panel_title": composition_panel_title,
        "composition_x_label": composition_x_label,
        "composition_y_label": composition_y_label,
        "composition_annotation": str(payload.get("composition_annotation") or "").strip(),
        "composition_groups": normalized_composition_groups,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


def _validate_trajectory_progression_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    trajectory_panel_title = _require_non_empty_string(
        payload.get("trajectory_panel_title"),
        label=f"{path.name} display `{expected_display_id}` trajectory_panel_title",
    )
    trajectory_x_label = _require_non_empty_string(
        payload.get("trajectory_x_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_x_label",
    )
    trajectory_y_label = _require_non_empty_string(
        payload.get("trajectory_y_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_y_label",
    )
    composition_panel_title = _require_non_empty_string(
        payload.get("composition_panel_title"),
        label=f"{path.name} display `{expected_display_id}` composition_panel_title",
    )
    composition_x_label = _require_non_empty_string(
        payload.get("composition_x_label"),
        label=f"{path.name} display `{expected_display_id}` composition_x_label",
    )
    composition_y_label = _require_non_empty_string(
        payload.get("composition_y_label"),
        label=f"{path.name} display `{expected_display_id}` composition_y_label",
    )
    heatmap_panel_title = _require_non_empty_string(
        payload.get("heatmap_panel_title"),
        label=f"{path.name} display `{expected_display_id}` heatmap_panel_title",
    )
    heatmap_x_label = _require_non_empty_string(
        payload.get("heatmap_x_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_x_label",
    )
    heatmap_y_label = _require_non_empty_string(
        payload.get("heatmap_y_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_y_label",
    )

    trajectory_points = payload.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty trajectory_points list")
    normalized_trajectory_points: list[dict[str, Any]] = []
    observed_branches: set[str] = set()
    for index, item in enumerate(trajectory_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` trajectory_points[{index}] must be an object")
        branch_label = _require_non_empty_string(
            item.get("branch_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].branch_label",
        )
        observed_branches.add(branch_label)
        normalized_trajectory_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].y",
                ),
                "branch_label": branch_label,
                "state_label": _require_non_empty_string(
                    item.get("state_label"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].state_label",
                ),
                "pseudotime": _require_probability_value(
                    item.get("pseudotime"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].pseudotime",
                ),
            }
        )

    branch_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("branch_order"),
        label=f"display `{expected_display_id}` branch_order",
    )
    declared_branch_labels = {item["label"] for item in branch_order}
    if observed_branches != declared_branch_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` branch_order labels must match trajectory point branch labels"
        )

    progression_bins = payload.get("progression_bins")
    if not isinstance(progression_bins, list) or not progression_bins:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty progression_bins list")
    normalized_progression_bins: list[dict[str, Any]] = []
    seen_bin_labels: set[str] = set()
    previous_bin_order = 0
    previous_end = -1.0
    for index, item in enumerate(progression_bins):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` progression_bins[{index}] must be an object")
        bin_label = _require_non_empty_string(
            item.get("bin_label"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_label",
        )
        if bin_label in seen_bin_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_label must be unique"
            )
        seen_bin_labels.add(bin_label)
        bin_order = _require_non_negative_int(
            item.get("bin_order"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_order",
            allow_zero=False,
        )
        if bin_order <= previous_bin_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins bin_order must be strictly increasing"
            )
        previous_bin_order = bin_order
        pseudotime_start = _require_probability_value(
            item.get("pseudotime_start"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].pseudotime_start",
        )
        pseudotime_end = _require_probability_value(
            item.get("pseudotime_end"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].pseudotime_end",
        )
        if pseudotime_end <= pseudotime_start:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] must satisfy pseudotime_start < pseudotime_end"
            )
        if pseudotime_start < previous_end - 1e-9:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins intervals must be strictly increasing"
            )
        previous_end = pseudotime_end

        branch_weights = item.get("branch_weights")
        if not isinstance(branch_weights, list) or not branch_weights:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}].branch_weights must be non-empty"
            )
        normalized_branch_weights: list[dict[str, Any]] = []
        seen_branch_labels: set[str] = set()
        weight_sum = 0.0
        for branch_index, branch_item in enumerate(branch_weights):
            if not isinstance(branch_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}].branch_weights[{branch_index}] must be an object"
                )
            branch_label = _require_non_empty_string(
                branch_item.get("branch_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}]."
                    f"branch_weights[{branch_index}].branch_label"
                ),
            )
            if branch_label in seen_branch_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}] must cover the declared branch labels exactly once"
                )
            seen_branch_labels.add(branch_label)
            proportion = _require_probability_value(
                branch_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}]."
                    f"branch_weights[{branch_index}].proportion"
                ),
            )
            weight_sum += proportion
            normalized_branch_weights.append({"branch_label": branch_label, "proportion": proportion})
        if seen_branch_labels != declared_branch_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] must cover the declared branch labels exactly once"
            )
        if abs(weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] branch weights must sum to 1"
            )
        normalized_progression_bins.append(
            {
                "bin_label": bin_label,
                "bin_order": bin_order,
                "pseudotime_start": pseudotime_start,
                "pseudotime_end": pseudotime_end,
                "branch_weights": normalized_branch_weights,
            }
        )

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
    declared_columns = {item["label"] for item in column_order}
    if seen_bin_labels != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match progression bin labels"
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
    if observed_rows != declared_rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` row_order labels must match cell y labels")
    if observed_columns != declared_columns:
        raise ValueError(f"{path.name} display `{expected_display_id}` column_order labels must match cell x labels")
    expected_coordinates = {(column["label"], row["label"]) for row in row_order for column in column_order}
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "trajectory_panel_title": trajectory_panel_title,
        "trajectory_x_label": trajectory_x_label,
        "trajectory_y_label": trajectory_y_label,
        "trajectory_annotation": str(payload.get("trajectory_annotation") or "").strip(),
        "trajectory_points": normalized_trajectory_points,
        "composition_panel_title": composition_panel_title,
        "composition_x_label": composition_x_label,
        "composition_y_label": composition_y_label,
        "composition_annotation": str(payload.get("composition_annotation") or "").strip(),
        "branch_order": branch_order,
        "progression_bins": normalized_progression_bins,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


def _validate_atlas_spatial_trajectory_storyboard_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    atlas_panel_title = _require_non_empty_string(
        payload.get("atlas_panel_title"),
        label=f"{path.name} display `{expected_display_id}` atlas_panel_title",
    )
    atlas_x_label = _require_non_empty_string(
        payload.get("atlas_x_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_x_label",
    )
    atlas_y_label = _require_non_empty_string(
        payload.get("atlas_y_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_y_label",
    )
    spatial_panel_title = _require_non_empty_string(
        payload.get("spatial_panel_title"),
        label=f"{path.name} display `{expected_display_id}` spatial_panel_title",
    )
    spatial_x_label = _require_non_empty_string(
        payload.get("spatial_x_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_x_label",
    )
    spatial_y_label = _require_non_empty_string(
        payload.get("spatial_y_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_y_label",
    )
    trajectory_panel_title = _require_non_empty_string(
        payload.get("trajectory_panel_title"),
        label=f"{path.name} display `{expected_display_id}` trajectory_panel_title",
    )
    trajectory_x_label = _require_non_empty_string(
        payload.get("trajectory_x_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_x_label",
    )
    trajectory_y_label = _require_non_empty_string(
        payload.get("trajectory_y_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_y_label",
    )
    composition_panel_title = _require_non_empty_string(
        payload.get("composition_panel_title"),
        label=f"{path.name} display `{expected_display_id}` composition_panel_title",
    )
    composition_x_label = _require_non_empty_string(
        payload.get("composition_x_label"),
        label=f"{path.name} display `{expected_display_id}` composition_x_label",
    )
    composition_y_label = _require_non_empty_string(
        payload.get("composition_y_label"),
        label=f"{path.name} display `{expected_display_id}` composition_y_label",
    )
    heatmap_panel_title = _require_non_empty_string(
        payload.get("heatmap_panel_title"),
        label=f"{path.name} display `{expected_display_id}` heatmap_panel_title",
    )
    heatmap_x_label = _require_non_empty_string(
        payload.get("heatmap_x_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_x_label",
    )
    heatmap_y_label = _require_non_empty_string(
        payload.get("heatmap_y_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_y_label",
    )

    atlas_points = payload.get("atlas_points")
    if not isinstance(atlas_points, list) or not atlas_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty atlas_points list")
    normalized_atlas_points: list[dict[str, Any]] = []
    observed_atlas_states: set[str] = set()
    for index, item in enumerate(atlas_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` atlas_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].state_label",
        )
        observed_atlas_states.add(state_label)
        normalized_atlas_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].y",
                ),
                "state_label": state_label,
            }
        )

    spatial_points = payload.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty spatial_points list")
    normalized_spatial_points: list[dict[str, Any]] = []
    observed_spatial_states: set[str] = set()
    for index, item in enumerate(spatial_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` spatial_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].state_label",
        )
        observed_spatial_states.add(state_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].y",
            ),
            "state_label": state_label,
        }
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_spatial_points.append(normalized_point)

    trajectory_points = payload.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty trajectory_points list")
    normalized_trajectory_points: list[dict[str, Any]] = []
    observed_trajectory_states: set[str] = set()
    observed_branch_labels: set[str] = set()
    for index, item in enumerate(trajectory_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` trajectory_points[{index}] must be an object")
        branch_label = _require_non_empty_string(
            item.get("branch_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].branch_label",
        )
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].state_label",
        )
        observed_branch_labels.add(branch_label)
        observed_trajectory_states.add(state_label)
        normalized_trajectory_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].y",
                ),
                "branch_label": branch_label,
                "state_label": state_label,
                "pseudotime": _require_probability_value(
                    item.get("pseudotime"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].pseudotime",
                ),
            }
        )

    state_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("state_order"),
        label=f"display `{expected_display_id}` state_order",
    )
    declared_state_labels = {item["label"] for item in state_order}
    if observed_atlas_states != declared_state_labels:
        raise ValueError(f"{path.name} display `{expected_display_id}` state_order labels must match atlas point state labels")
    if observed_spatial_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match spatial point state labels"
        )
    if observed_trajectory_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match trajectory point state labels"
        )

    branch_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("branch_order"),
        label=f"display `{expected_display_id}` branch_order",
    )
    declared_branch_labels = {item["label"] for item in branch_order}
    if observed_branch_labels != declared_branch_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` branch_order labels must match trajectory point branch labels"
        )

    progression_bins = payload.get("progression_bins")
    if not isinstance(progression_bins, list) or not progression_bins:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty progression_bins list")
    normalized_progression_bins: list[dict[str, Any]] = []
    seen_bin_labels: set[str] = set()
    previous_bin_order = 0
    previous_end = -1.0
    for index, item in enumerate(progression_bins):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` progression_bins[{index}] must be an object")
        bin_label = _require_non_empty_string(
            item.get("bin_label"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_label",
        )
        if bin_label in seen_bin_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_label must be unique"
            )
        seen_bin_labels.add(bin_label)
        bin_order = _require_non_negative_int(
            item.get("bin_order"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_order",
            allow_zero=False,
        )
        if bin_order <= previous_bin_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins bin_order must be strictly increasing"
            )
        previous_bin_order = bin_order
        pseudotime_start = _require_probability_value(
            item.get("pseudotime_start"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].pseudotime_start",
        )
        pseudotime_end = _require_probability_value(
            item.get("pseudotime_end"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].pseudotime_end",
        )
        if pseudotime_end <= pseudotime_start:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] must satisfy pseudotime_start < pseudotime_end"
            )
        if pseudotime_start < previous_end - 1e-9:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins intervals must be strictly increasing"
            )
        previous_end = pseudotime_end

        branch_weights = item.get("branch_weights")
        if not isinstance(branch_weights, list) or not branch_weights:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}].branch_weights must be non-empty"
            )
        normalized_branch_weights: list[dict[str, Any]] = []
        seen_weight_branches: set[str] = set()
        weight_sum = 0.0
        for branch_index, branch_item in enumerate(branch_weights):
            if not isinstance(branch_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}].branch_weights[{branch_index}] must be an object"
                )
            branch_label = _require_non_empty_string(
                branch_item.get("branch_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}]."
                    f"branch_weights[{branch_index}].branch_label"
                ),
            )
            if branch_label in seen_weight_branches:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}] must cover the declared branch labels exactly once"
                )
            seen_weight_branches.add(branch_label)
            proportion = _require_probability_value(
                branch_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}]."
                    f"branch_weights[{branch_index}].proportion"
                ),
            )
            weight_sum += proportion
            normalized_branch_weights.append({"branch_label": branch_label, "proportion": proportion})
        if seen_weight_branches != declared_branch_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] must cover the declared branch labels exactly once"
            )
        if abs(weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] branch weights must sum to 1"
            )
        normalized_progression_bins.append(
            {
                "bin_label": bin_label,
                "bin_order": bin_order,
                "pseudotime_start": pseudotime_start,
                "pseudotime_end": pseudotime_end,
                "branch_weights": normalized_branch_weights,
            }
        )

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
    declared_columns = {item["label"] for item in column_order}
    if seen_bin_labels != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match progression bin labels"
        )

    composition_groups = payload.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty composition_groups list")
    normalized_composition_groups: list[dict[str, Any]] = []
    seen_group_labels: set[str] = set()
    previous_group_order = 0
    for index, item in enumerate(composition_groups):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` composition_groups[{index}] must be an object")
        group_label = _require_non_empty_string(
            item.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_group_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups group_order must be strictly increasing"
            )
        previous_group_order = group_order
        state_proportions = item.get("state_proportions")
        if not isinstance(state_proportions, list) or not state_proportions:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions must be non-empty"
            )
        normalized_state_proportions: list[dict[str, Any]] = []
        seen_state_labels: set[str] = set()
        proportion_sum = 0.0
        for state_index, state_item in enumerate(state_proportions):
            if not isinstance(state_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions[{state_index}] must be an object"
                )
            state_label = _require_non_empty_string(
                state_item.get("state_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].state_label"
                ),
            )
            if state_label in seen_state_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
                )
            seen_state_labels.add(state_label)
            proportion = _require_probability_value(
                state_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].proportion"
                ),
            )
            proportion_sum += proportion
            normalized_state_proportions.append({"state_label": state_label, "proportion": proportion})
        if seen_state_labels != declared_state_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
            )
        if abs(proportion_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] proportions must sum to 1"
            )
        normalized_composition_groups.append(
            {
                "group_label": group_label,
                "group_order": group_order,
                "state_proportions": normalized_state_proportions,
            }
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
    if observed_rows != declared_rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` row_order labels must match cell y labels")
    if observed_columns != declared_columns:
        raise ValueError(f"{path.name} display `{expected_display_id}` column_order labels must match cell x labels")
    expected_coordinates = {(column["label"], row["label"]) for row in row_order for column in column_order}
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "atlas_panel_title": atlas_panel_title,
        "atlas_x_label": atlas_x_label,
        "atlas_y_label": atlas_y_label,
        "atlas_annotation": str(payload.get("atlas_annotation") or "").strip(),
        "atlas_points": normalized_atlas_points,
        "spatial_panel_title": spatial_panel_title,
        "spatial_x_label": spatial_x_label,
        "spatial_y_label": spatial_y_label,
        "spatial_annotation": str(payload.get("spatial_annotation") or "").strip(),
        "spatial_points": normalized_spatial_points,
        "trajectory_panel_title": trajectory_panel_title,
        "trajectory_x_label": trajectory_x_label,
        "trajectory_y_label": trajectory_y_label,
        "trajectory_annotation": str(payload.get("trajectory_annotation") or "").strip(),
        "trajectory_points": normalized_trajectory_points,
        "composition_panel_title": composition_panel_title,
        "composition_x_label": composition_x_label,
        "composition_y_label": composition_y_label,
        "composition_annotation": str(payload.get("composition_annotation") or "").strip(),
        "composition_groups": normalized_composition_groups,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "state_order": state_order,
        "branch_order": branch_order,
        "progression_bins": normalized_progression_bins,
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


def _validate_atlas_spatial_trajectory_density_coverage_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    atlas_panel_title = _require_non_empty_string(
        payload.get("atlas_panel_title"),
        label=f"{path.name} display `{expected_display_id}` atlas_panel_title",
    )
    atlas_x_label = _require_non_empty_string(
        payload.get("atlas_x_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_x_label",
    )
    atlas_y_label = _require_non_empty_string(
        payload.get("atlas_y_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_y_label",
    )
    spatial_panel_title = _require_non_empty_string(
        payload.get("spatial_panel_title"),
        label=f"{path.name} display `{expected_display_id}` spatial_panel_title",
    )
    spatial_x_label = _require_non_empty_string(
        payload.get("spatial_x_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_x_label",
    )
    spatial_y_label = _require_non_empty_string(
        payload.get("spatial_y_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_y_label",
    )
    trajectory_panel_title = _require_non_empty_string(
        payload.get("trajectory_panel_title"),
        label=f"{path.name} display `{expected_display_id}` trajectory_panel_title",
    )
    trajectory_x_label = _require_non_empty_string(
        payload.get("trajectory_x_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_x_label",
    )
    trajectory_y_label = _require_non_empty_string(
        payload.get("trajectory_y_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_y_label",
    )
    support_panel_title = _require_non_empty_string(
        payload.get("support_panel_title"),
        label=f"{path.name} display `{expected_display_id}` support_panel_title",
    )
    support_x_label = _require_non_empty_string(
        payload.get("support_x_label"),
        label=f"{path.name} display `{expected_display_id}` support_x_label",
    )
    support_y_label = _require_non_empty_string(
        payload.get("support_y_label"),
        label=f"{path.name} display `{expected_display_id}` support_y_label",
    )
    support_scale_label = _require_non_empty_string(
        payload.get("support_scale_label"),
        label=f"{path.name} display `{expected_display_id}` support_scale_label",
    )

    atlas_points = payload.get("atlas_points")
    if not isinstance(atlas_points, list) or not atlas_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty atlas_points list")
    normalized_atlas_points: list[dict[str, Any]] = []
    observed_atlas_states: set[str] = set()
    for index, item in enumerate(atlas_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` atlas_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].state_label",
        )
        observed_atlas_states.add(state_label)
        normalized_atlas_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].y",
                ),
                "state_label": state_label,
            }
        )

    spatial_points = payload.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty spatial_points list")
    normalized_spatial_points: list[dict[str, Any]] = []
    observed_spatial_states: set[str] = set()
    for index, item in enumerate(spatial_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` spatial_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].state_label",
        )
        region_label = _require_non_empty_string(
            item.get("region_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].region_label",
        )
        observed_spatial_states.add(state_label)
        normalized_spatial_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].y",
                ),
                "state_label": state_label,
                "region_label": region_label,
            }
        )

    trajectory_points = payload.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty trajectory_points list")
    normalized_trajectory_points: list[dict[str, Any]] = []
    observed_trajectory_states: set[str] = set()
    observed_branch_labels: set[str] = set()
    for index, item in enumerate(trajectory_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` trajectory_points[{index}] must be an object")
        branch_label = _require_non_empty_string(
            item.get("branch_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].branch_label",
        )
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].state_label",
        )
        observed_branch_labels.add(branch_label)
        observed_trajectory_states.add(state_label)
        normalized_trajectory_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].y",
                ),
                "branch_label": branch_label,
                "state_label": state_label,
                "pseudotime": _require_probability_value(
                    item.get("pseudotime"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].pseudotime",
                ),
            }
        )

    state_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("state_order"),
        label=f"display `{expected_display_id}` state_order",
    )
    declared_state_labels = {item["label"] for item in state_order}
    if observed_atlas_states != declared_state_labels:
        raise ValueError(f"{path.name} display `{expected_display_id}` state_order labels must match atlas point state labels")
    if observed_spatial_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match spatial point state labels"
        )
    if observed_trajectory_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match trajectory point state labels"
        )

    context_order = payload.get("context_order")
    if not isinstance(context_order, list) or not context_order:
        raise ValueError(f"{path.name} display `{expected_display_id}` context_order must contain a non-empty list")
    normalized_context_order: list[dict[str, str]] = []
    seen_context_labels: set[str] = set()
    seen_context_kinds: set[str] = set()
    required_context_kinds = {"atlas_density", "spatial_coverage", "trajectory_coverage"}
    for index, item in enumerate(context_order):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` context_order[{index}] must be an object")
        context_label = _require_non_empty_string(
            item.get("label"),
            label=f"{path.name} display `{expected_display_id}` context_order[{index}].label",
        )
        if context_label in seen_context_labels:
            raise ValueError(f"{path.name} display `{expected_display_id}` context_order[{index}].label must be unique")
        seen_context_labels.add(context_label)
        context_kind = _require_non_empty_string(
            item.get("context_kind"),
            label=f"{path.name} display `{expected_display_id}` context_order[{index}].context_kind",
        )
        if context_kind not in required_context_kinds:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` context_order[{index}].context_kind must be one of atlas_density, spatial_coverage, trajectory_coverage"
            )
        if context_kind in seen_context_kinds:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` context_order[{index}].context_kind must be unique"
            )
        seen_context_kinds.add(context_kind)
        normalized_context_order.append({"label": context_label, "context_kind": context_kind})
    if seen_context_kinds != required_context_kinds:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` context_order must cover atlas_density, spatial_coverage, and trajectory_coverage exactly once"
        )

    support_cells = payload.get("support_cells")
    if not isinstance(support_cells, list) or not support_cells:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty support_cells list")
    normalized_support_cells: list[dict[str, Any]] = []
    observed_support_rows: set[str] = set()
    observed_support_columns: set[str] = set()
    observed_support_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(support_cells):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` support_cells[{index}] must be an object")
        context_label = _require_non_empty_string(
            item.get("x"),
            label=f"{path.name} display `{expected_display_id}` support_cells[{index}].x",
        )
        state_label = _require_non_empty_string(
            item.get("y"),
            label=f"{path.name} display `{expected_display_id}` support_cells[{index}].y",
        )
        coordinate = (context_label, state_label)
        if coordinate in observed_support_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
            )
        observed_support_coordinates.add(coordinate)
        observed_support_columns.add(context_label)
        observed_support_rows.add(state_label)
        normalized_support_cells.append(
            {
                "x": context_label,
                "y": state_label,
                "value": _require_probability_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` support_cells[{index}].value",
                ),
            }
        )

    declared_context_labels = {item["label"] for item in normalized_context_order}
    if observed_support_rows != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
        )
    if observed_support_columns != declared_context_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
        )
    expected_coordinates = {(context["label"], state["label"]) for state in state_order for context in normalized_context_order}
    if observed_support_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "atlas_panel_title": atlas_panel_title,
        "atlas_x_label": atlas_x_label,
        "atlas_y_label": atlas_y_label,
        "atlas_annotation": str(payload.get("atlas_annotation") or "").strip(),
        "atlas_points": normalized_atlas_points,
        "spatial_panel_title": spatial_panel_title,
        "spatial_x_label": spatial_x_label,
        "spatial_y_label": spatial_y_label,
        "spatial_annotation": str(payload.get("spatial_annotation") or "").strip(),
        "spatial_points": normalized_spatial_points,
        "trajectory_panel_title": trajectory_panel_title,
        "trajectory_x_label": trajectory_x_label,
        "trajectory_y_label": trajectory_y_label,
        "trajectory_annotation": str(payload.get("trajectory_annotation") or "").strip(),
        "trajectory_points": normalized_trajectory_points,
        "support_panel_title": support_panel_title,
        "support_x_label": support_x_label,
        "support_y_label": support_y_label,
        "support_scale_label": support_scale_label,
        "support_annotation": str(payload.get("support_annotation") or "").strip(),
        "state_order": state_order,
        "context_order": normalized_context_order,
        "support_cells": normalized_support_cells,
    }


def _validate_atlas_spatial_trajectory_context_support_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    storyboard_payload = _validate_atlas_spatial_trajectory_storyboard_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    support_payload = _validate_atlas_spatial_trajectory_density_coverage_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    return {
        **storyboard_payload,
        "support_panel_title": support_payload["support_panel_title"],
        "support_x_label": support_payload["support_x_label"],
        "support_y_label": support_payload["support_y_label"],
        "support_annotation": support_payload["support_annotation"],
        "support_scale_label": support_payload["support_scale_label"],
        "context_order": support_payload["context_order"],
        "support_cells": support_payload["support_cells"],
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


def _validate_performance_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized_payload = _validate_clustered_heatmap_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    normalized_payload["metric_name"] = _require_non_empty_string(
        payload.get("metric_name"),
        label=f"{path.name} display `{expected_display_id}` metric_name",
    )
    for index, cell in enumerate(normalized_payload["cells"]):
        value = float(cell["value"])
        if 0.0 <= value <= 1.0:
            continue
        raise ValueError(
            f"{path.name} display `{expected_display_id}` cells[{index}].value must stay within [0, 1]"
        )
    return normalized_payload


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


def _validate_gsva_ssgsea_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized_payload = _validate_clustered_heatmap_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    normalized_payload["score_method"] = _require_non_empty_string(
        payload.get("score_method"),
        label=f"{path.name} display `{expected_display_id}` score_method",
    )
    return normalized_payload


def _validate_panel_order_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, str]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    if len(payload) > 2:
        raise ValueError(f"{path.name} {label} must contain at most two panels")
    normalized_items: list[dict[str, str]] = []
    seen_panel_ids: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} {label}[{index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(f"{path.name} {label}[{index}].panel_id must be unique")
        seen_panel_ids.add(panel_id)
        normalized_items.append(
            {
                "panel_id": panel_id,
                "panel_title": _require_non_empty_string(
                    item.get("panel_title"),
                    label=f"{path.name} {label}[{index}].panel_title",
                ),
            }
        )
    return normalized_items


def _validate_pathway_enrichment_dotplot_panel_display_payload(
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
    panel_order = _validate_panel_order_payload(
        path=path,
        payload=payload.get("panel_order"),
        label=f"display `{expected_display_id}` panel_order",
    )
    pathway_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("pathway_order"),
        label=f"display `{expected_display_id}` pathway_order",
    )
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty points list")

    declared_panel_ids = {item["panel_id"] for item in panel_order}
    declared_pathway_labels = {item["label"] for item in pathway_order}
    expected_coordinates = {
        (panel["panel_id"], pathway["label"]) for panel in panel_order for pathway in pathway_order
    }
    observed_coordinates: set[tuple[str, str]] = set()
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].panel_id",
        )
        if panel_id not in declared_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}].panel_id must match panel_order")
        pathway_label = _require_non_empty_string(
            item.get("pathway_label"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].pathway_label",
        )
        if pathway_label not in declared_pathway_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].pathway_label must match pathway_order"
            )
        coordinate = (panel_id, pathway_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared panel/pathway coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        size_value = _require_numeric_value(
            item.get("size_value"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].size_value",
        )
        if size_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].size_value must be non-negative"
            )
        normalized_points.append(
            {
                "panel_id": panel_id,
                "pathway_label": pathway_label,
                "x_value": _require_numeric_value(
                    item.get("x_value"),
                    label=f"{path.name} display `{expected_display_id}` points[{index}].x_value",
                ),
                "effect_value": _require_numeric_value(
                    item.get("effect_value"),
                    label=f"{path.name} display `{expected_display_id}` points[{index}].effect_value",
                ),
                "size_value": size_value,
            }
        )
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared panel/pathway coordinate exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "effect_scale_label": _require_non_empty_string(
            payload.get("effect_scale_label"),
            label=f"{path.name} display `{expected_display_id}` effect_scale_label",
        ),
        "size_scale_label": _require_non_empty_string(
            payload.get("size_scale_label"),
            label=f"{path.name} display `{expected_display_id}` size_scale_label",
        ),
        "panel_order": panel_order,
        "pathway_order": pathway_order,
        "points": normalized_points,
    }


def _validate_omics_volcano_panel_display_payload(
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
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
    )
    effect_threshold = _require_numeric_value(
        payload.get("effect_threshold"),
        label=f"{path.name} display `{expected_display_id}` effect_threshold",
    )
    if effect_threshold <= 0.0:
        raise ValueError(f"{path.name} display `{expected_display_id}` effect_threshold must be positive")
    significance_threshold = _require_numeric_value(
        payload.get("significance_threshold"),
        label=f"{path.name} display `{expected_display_id}` significance_threshold",
    )
    if significance_threshold <= 0.0:
        raise ValueError(f"{path.name} display `{expected_display_id}` significance_threshold must be positive")
    panel_order = _validate_panel_order_payload(
        path=path,
        payload=payload.get("panel_order"),
        label=f"display `{expected_display_id}` panel_order",
    )
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty points list")

    declared_panel_ids = {item["panel_id"] for item in panel_order}
    panel_point_counts = {panel_id: 0 for panel_id in declared_panel_ids}
    feature_labels_by_panel = {panel_id: set() for panel_id in declared_panel_ids}
    supported_regulation_classes = {"upregulated", "downregulated", "background"}
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].panel_id",
        )
        if panel_id not in declared_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}].panel_id must match panel_order")
        feature_label = _require_non_empty_string(
            item.get("feature_label"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].feature_label",
        )
        if feature_label in feature_labels_by_panel[panel_id]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].feature_label must be unique within its panel"
            )
        feature_labels_by_panel[panel_id].add(feature_label)
        effect_value = _require_numeric_value(
            item.get("effect_value"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].effect_value",
        )
        significance_value = _require_numeric_value(
            item.get("significance_value"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].significance_value",
        )
        if significance_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].significance_value must be non-negative"
            )
        regulation_class = _require_non_empty_string(
            item.get("regulation_class"),
            label=f"{path.name} display `{expected_display_id}` points[{index}].regulation_class",
        )
        if regulation_class not in supported_regulation_classes:
            supported_classes = ", ".join(("upregulated", "downregulated", "background"))
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].regulation_class must be one of {supported_classes}"
            )
        label_text = str(item.get("label_text") or "").strip()
        if "label_text" in item and not label_text:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` points[{index}].label_text must be non-empty when present"
            )
        normalized_point = {
            "panel_id": panel_id,
            "feature_label": feature_label,
            "effect_value": effect_value,
            "significance_value": significance_value,
            "regulation_class": regulation_class,
        }
        if label_text:
            normalized_point["label_text"] = label_text
        normalized_points.append(normalized_point)
        panel_point_counts[panel_id] += 1

    for panel_id, point_count in panel_point_counts.items():
        if point_count > 0:
            continue
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain at least one point for panel `{panel_id}`")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "legend_title": legend_title,
        "effect_threshold": effect_threshold,
        "significance_threshold": significance_threshold,
        "panel_order": panel_order,
        "points": normalized_points,
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


def _validate_compact_effect_estimate_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    reference_value = _require_numeric_value(
        payload.get("reference_value"),
        label=f"{path.name} display `{expected_display_id}` reference_value",
    )
    if not math.isfinite(reference_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` reference_value must be finite")

    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) < 2 or len(panels_payload) > 4:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain between 2 and 4 entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    expected_row_order: tuple[tuple[str, str], ...] | None = None
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        rows_payload = panel_payload.get("rows")
        if not isinstance(rows_payload, list) or not rows_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] must contain a non-empty rows list"
            )

        normalized_rows: list[dict[str, Any]] = []
        seen_row_ids: set[str] = set()
        seen_row_labels: set[str] = set()
        row_order: list[tuple[str, str]] = []
        for row_index, row_payload in enumerate(rows_payload):
            if not isinstance(row_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}] must be an object"
                )
            row_id = _require_non_empty_string(
                row_payload.get("row_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_id"
                ),
            )
            if row_id in seen_row_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_id must be unique within the panel"
                )
            seen_row_ids.add(row_id)
            row_label = _require_non_empty_string(
                row_payload.get("row_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_label"
                ),
            )
            if row_label in seen_row_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].row_label must be unique within the panel"
                )
            seen_row_labels.add(row_label)
            estimate = _require_numeric_value(
                row_payload.get("estimate"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].estimate"
                ),
            )
            lower = _require_numeric_value(
                row_payload.get("lower"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].lower"
                ),
            )
            upper = _require_numeric_value(
                row_payload.get("upper"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].upper"
                ),
            )
            if not all(math.isfinite(value) for value in (estimate, lower, upper)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}] values must be finite"
                )
            if not (lower <= estimate <= upper):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}] must satisfy lower <= estimate <= upper"
                )
            normalized_row = {
                "row_id": row_id,
                "row_label": row_label,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
            if row_payload.get("support_n") is not None:
                normalized_row["support_n"] = _require_non_negative_int(
                    row_payload.get("support_n"),
                    label=(
                        f"{path.name} display `{expected_display_id}` panels[{panel_index}].rows[{row_index}].support_n"
                    ),
                    allow_zero=False,
                )
            normalized_rows.append(normalized_row)
            row_order.append((row_id, row_label))

        if expected_row_order is None:
            expected_row_order = tuple(row_order)
        elif tuple(row_order) != expected_row_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` rows must appear in the same row_id and row_label order across panels"
            )

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "rows": normalized_rows,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "reference_value": reference_value,
        "panels": normalized_panels,
    }


def _validate_coefficient_path_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    path_panel_title = _require_non_empty_string(
        payload.get("path_panel_title"),
        label=f"{path.name} display `{expected_display_id}` path_panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    reference_value = _require_numeric_value(
        payload.get("reference_value"),
        label=f"{path.name} display `{expected_display_id}` reference_value",
    )
    if not math.isfinite(reference_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` reference_value must be finite")
    step_legend_title = _require_non_empty_string(
        payload.get("step_legend_title"),
        label=f"{path.name} display `{expected_display_id}` step_legend_title",
    )
    summary_panel_title = _require_non_empty_string(
        payload.get("summary_panel_title"),
        label=f"{path.name} display `{expected_display_id}` summary_panel_title",
    )

    steps_payload = payload.get("steps")
    if not isinstance(steps_payload, list) or not steps_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty steps list")
    if len(steps_payload) < 2 or len(steps_payload) > 5:
        raise ValueError(f"{path.name} display `{expected_display_id}` steps must contain between 2 and 5 entries")
    normalized_steps: list[dict[str, Any]] = []
    declared_step_ids: list[str] = []
    seen_step_ids: set[str] = set()
    previous_step_order: int | None = None
    for index, item in enumerate(steps_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` steps[{index}] must be an object")
        step_id = _require_non_empty_string(
            item.get("step_id"),
            label=f"{path.name} display `{expected_display_id}` steps[{index}].step_id",
        )
        if step_id in seen_step_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` steps[{index}].step_id must be unique")
        seen_step_ids.add(step_id)
        step_order = _require_non_negative_int(
            item.get("step_order"),
            label=f"{path.name} display `{expected_display_id}` steps[{index}].step_order",
            allow_zero=False,
        )
        if previous_step_order is not None and step_order <= previous_step_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` steps must have strictly increasing step_order"
            )
        previous_step_order = step_order
        declared_step_ids.append(step_id)
        normalized_steps.append(
            {
                "step_id": step_id,
                "step_label": _require_non_empty_string(
                    item.get("step_label"),
                    label=f"{path.name} display `{expected_display_id}` steps[{index}].step_label",
                ),
                "step_order": step_order,
            }
        )

    coefficient_rows_payload = payload.get("coefficient_rows")
    if not isinstance(coefficient_rows_payload, list) or not coefficient_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty coefficient_rows list")
    normalized_rows: list[dict[str, Any]] = []
    seen_row_ids: set[str] = set()
    seen_row_labels: set[str] = set()
    declared_step_id_set = set(declared_step_ids)
    for row_index, row_payload in enumerate(coefficient_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}] must be an object")
        row_id = _require_non_empty_string(
            row_payload.get("row_id"),
            label=f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_id",
        )
        if row_id in seen_row_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_id must be unique"
            )
        seen_row_ids.add(row_id)
        row_label = _require_non_empty_string(
            row_payload.get("row_label"),
            label=f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_label",
        )
        if row_label in seen_row_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].row_label must be unique"
            )
        seen_row_labels.add(row_label)

        points_payload = row_payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points must be a non-empty list"
            )
        normalized_points: list[dict[str, Any]] = []
        seen_point_step_ids: set[str] = set()
        for point_index, point_payload in enumerate(points_payload):
            if not isinstance(point_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}] must be an object"
                )
            step_id = _require_non_empty_string(
                point_payload.get("step_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].step_id"
                ),
            )
            if step_id not in declared_step_id_set:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}].step_id must match a declared step"
                )
            if step_id in seen_point_step_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}].step_id must be unique within the row"
                )
            seen_point_step_ids.add(step_id)
            estimate = _require_numeric_value(
                point_payload.get("estimate"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].estimate"
                ),
            )
            lower = _require_numeric_value(
                point_payload.get("lower"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].lower"
                ),
            )
            upper = _require_numeric_value(
                point_payload.get("upper"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"coefficient_rows[{row_index}].points[{point_index}].upper"
                ),
            )
            if not all(math.isfinite(value) for value in (estimate, lower, upper)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}] values must be finite"
                )
            if not (lower <= estimate <= upper):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}].points[{point_index}] must satisfy lower <= estimate <= upper"
                )
            normalized_point: dict[str, Any] = {
                "step_id": step_id,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
            if point_payload.get("support_n") is not None:
                normalized_point["support_n"] = _require_non_negative_int(
                    point_payload.get("support_n"),
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"coefficient_rows[{row_index}].points[{point_index}].support_n"
                    ),
                    allow_zero=False,
                )
            normalized_points.append(normalized_point)

        if seen_point_step_ids != declared_step_id_set:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coefficient_rows[{row_index}] points must cover every declared step_id exactly once within each coefficient row"
            )

        normalized_points.sort(key=lambda item: declared_step_ids.index(str(item["step_id"])))
        normalized_rows.append(
            {
                "row_id": row_id,
                "row_label": row_label,
                "points": normalized_points,
            }
        )

    summary_cards_payload = payload.get("summary_cards")
    if not isinstance(summary_cards_payload, list) or not summary_cards_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty summary_cards list")
    if len(summary_cards_payload) < 2 or len(summary_cards_payload) > 4:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` summary_cards must contain between 2 and 4 entries"
        )
    normalized_summary_cards: list[dict[str, Any]] = []
    seen_card_ids: set[str] = set()
    for card_index, card_payload in enumerate(summary_cards_payload):
        if not isinstance(card_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` summary_cards[{card_index}] must be an object"
            )
        card_id = _require_non_empty_string(
            card_payload.get("card_id"),
            label=f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].card_id",
        )
        if card_id in seen_card_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].card_id must be unique"
            )
        seen_card_ids.add(card_id)
        normalized_card = {
            "card_id": card_id,
            "label": _require_non_empty_string(
                card_payload.get("label"),
                label=f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].label",
            ),
            "value": _require_non_empty_string(
                card_payload.get("value"),
                label=f"{path.name} display `{expected_display_id}` summary_cards[{card_index}].value",
            ),
        }
        detail_text = str(card_payload.get("detail") or "").strip()
        if detail_text:
            normalized_card["detail"] = detail_text
        normalized_summary_cards.append(normalized_card)

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "path_panel_title": path_panel_title,
        "x_label": x_label,
        "reference_value": reference_value,
        "step_legend_title": step_legend_title,
        "steps": normalized_steps,
        "coefficient_rows": normalized_rows,
        "summary_panel_title": summary_panel_title,
        "summary_cards": normalized_summary_cards,
    }


def _validate_broader_heterogeneity_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    matrix_panel_title = _require_non_empty_string(
        payload.get("matrix_panel_title"),
        label=f"{path.name} display `{expected_display_id}` matrix_panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    reference_value = _require_numeric_value(
        payload.get("reference_value"),
        label=f"{path.name} display `{expected_display_id}` reference_value",
    )
    if not math.isfinite(reference_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` reference_value must be finite")
    slice_legend_title = _require_non_empty_string(
        payload.get("slice_legend_title"),
        label=f"{path.name} display `{expected_display_id}` slice_legend_title",
    )
    summary_panel_title = _require_non_empty_string(
        payload.get("summary_panel_title"),
        label=f"{path.name} display `{expected_display_id}` summary_panel_title",
    )

    slices_payload = payload.get("slices")
    if not isinstance(slices_payload, list) or not slices_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty slices list")
    if len(slices_payload) < 2 or len(slices_payload) > 5:
        raise ValueError(f"{path.name} display `{expected_display_id}` slices must contain between 2 and 5 entries")
    supported_slice_kinds = {"cohort", "subgroup", "adjustment", "sensitivity"}
    normalized_slices: list[dict[str, Any]] = []
    declared_slice_ids: list[str] = []
    seen_slice_ids: set[str] = set()
    seen_slice_labels: set[str] = set()
    previous_slice_order: int | None = None
    for index, item in enumerate(slices_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` slices[{index}] must be an object")
        slice_id = _require_non_empty_string(
            item.get("slice_id"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_id",
        )
        if slice_id in seen_slice_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` slices[{index}].slice_id must be unique")
        seen_slice_ids.add(slice_id)
        slice_label = _require_non_empty_string(
            item.get("slice_label"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_label",
        )
        if slice_label in seen_slice_labels:
            raise ValueError(f"{path.name} display `{expected_display_id}` slices[{index}].slice_label must be unique")
        seen_slice_labels.add(slice_label)
        slice_order = _require_non_negative_int(
            item.get("slice_order"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_order",
            allow_zero=False,
        )
        if previous_slice_order is not None and slice_order <= previous_slice_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` slices must have strictly increasing slice_order"
            )
        previous_slice_order = slice_order
        slice_kind = _require_non_empty_string(
            item.get("slice_kind"),
            label=f"{path.name} display `{expected_display_id}` slices[{index}].slice_kind",
        )
        if slice_kind not in supported_slice_kinds:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` slices[{index}].slice_kind must be one of {sorted(supported_slice_kinds)}"
            )
        declared_slice_ids.append(slice_id)
        normalized_slices.append(
            {
                "slice_id": slice_id,
                "slice_label": slice_label,
                "slice_kind": slice_kind,
                "slice_order": slice_order,
            }
        )

    effect_rows_payload = payload.get("effect_rows")
    if not isinstance(effect_rows_payload, list) or not effect_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty effect_rows list")
    supported_verdicts = {"stable", "attenuated", "context_dependent", "unstable"}
    declared_slice_id_set = set(declared_slice_ids)
    normalized_effect_rows: list[dict[str, Any]] = []
    seen_row_ids: set[str] = set()
    seen_row_labels: set[str] = set()
    for row_index, row_payload in enumerate(effect_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` effect_rows[{row_index}] must be an object")
        row_id = _require_non_empty_string(
            row_payload.get("row_id"),
            label=f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_id",
        )
        if row_id in seen_row_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_id must be unique")
        seen_row_ids.add(row_id)
        row_label = _require_non_empty_string(
            row_payload.get("row_label"),
            label=f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_label",
        )
        if row_label in seen_row_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].row_label must be unique"
            )
        seen_row_labels.add(row_label)
        verdict = _require_non_empty_string(
            row_payload.get("verdict"),
            label=f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].verdict",
        )
        if verdict not in supported_verdicts:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].verdict must be one of {sorted(supported_verdicts)}"
            )
        detail_text = str(row_payload.get("detail") or "").strip()
        if row_payload.get("detail") is not None and not detail_text:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].detail must be non-empty when present"
            )

        slice_estimates_payload = row_payload.get("slice_estimates")
        if not isinstance(slice_estimates_payload, list) or not slice_estimates_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates must be a non-empty list"
            )
        normalized_slice_estimates: list[dict[str, Any]] = []
        seen_row_slice_ids: set[str] = set()
        for estimate_index, estimate_payload in enumerate(slice_estimates_payload):
            if not isinstance(estimate_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}] must be an object"
                )
            slice_id = _require_non_empty_string(
                estimate_payload.get("slice_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id"
                ),
            )
            if slice_id not in declared_slice_id_set:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id must match a declared slice"
                )
            if slice_id in seen_row_slice_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id must be unique within the row"
                )
            seen_row_slice_ids.add(slice_id)
            estimate = _require_numeric_value(
                estimate_payload.get("estimate"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].estimate"
                ),
            )
            lower = _require_numeric_value(
                estimate_payload.get("lower"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].lower"
                ),
            )
            upper = _require_numeric_value(
                estimate_payload.get("upper"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"effect_rows[{row_index}].slice_estimates[{estimate_index}].upper"
                ),
            )
            if not all(math.isfinite(value) for value in (estimate, lower, upper)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}] values must be finite"
                )
            if not (lower <= estimate <= upper):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` effect_rows[{row_index}].slice_estimates[{estimate_index}] must satisfy lower <= estimate <= upper"
                )
            normalized_estimate: dict[str, Any] = {
                "slice_id": slice_id,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
            }
            if estimate_payload.get("support_n") is not None:
                normalized_estimate["support_n"] = _require_non_negative_int(
                    estimate_payload.get("support_n"),
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"effect_rows[{row_index}].slice_estimates[{estimate_index}].support_n"
                    ),
                    allow_zero=False,
                )
            normalized_slice_estimates.append(normalized_estimate)
        if seen_row_slice_ids != declared_slice_id_set:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` effect_rows[{row_index}] slice_estimates must cover every declared slice_id exactly once"
            )
        normalized_slice_estimates.sort(key=lambda item: declared_slice_ids.index(str(item["slice_id"])))
        normalized_row = {
            "row_id": row_id,
            "row_label": row_label,
            "verdict": verdict,
            "slice_estimates": normalized_slice_estimates,
        }
        if detail_text:
            normalized_row["detail"] = detail_text
        normalized_effect_rows.append(normalized_row)

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "matrix_panel_title": matrix_panel_title,
        "x_label": x_label,
        "reference_value": reference_value,
        "slice_legend_title": slice_legend_title,
        "slices": normalized_slices,
        "effect_rows": normalized_effect_rows,
        "summary_panel_title": summary_panel_title,
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


def _validate_shap_dependence_panel_display_payload(
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
    colorbar_label = _require_non_empty_string(
        payload.get("colorbar_label"),
        label=f"{path.name} display `{expected_display_id}` colorbar_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_features: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        feature = _require_non_empty_string(
            panel_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature must be unique"
            )
        seen_features.add(feature)

        points_payload = panel_payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].points must be a non-empty list"
            )
        normalized_points: list[dict[str, float]] = []
        for point_index, point_payload in enumerate(points_payload):
            if not isinstance(point_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].points[{point_index}] must be an object"
                )
            feature_value = _require_numeric_value(
                point_payload.get("feature_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].points[{point_index}].feature_value"
                ),
            )
            shap_value = _require_numeric_value(
                point_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].points[{point_index}].shap_value"
                ),
            )
            interaction_value = _require_numeric_value(
                point_payload.get("interaction_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].points[{point_index}].interaction_value"
                ),
            )
            if not all(math.isfinite(value) for value in (feature_value, shap_value, interaction_value)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].points[{point_index}] point values must be finite"
                )
            normalized_points.append(
                {
                    "feature_value": feature_value,
                    "shap_value": shap_value,
                    "interaction_value": interaction_value,
                }
            )

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "feature": feature,
                "interaction_feature": _require_non_empty_string(
                    panel_payload.get("interaction_feature"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].interaction_feature",
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
        "y_label": y_label,
        "colorbar_label": colorbar_label,
        "panels": normalized_panels,
    }


def _validate_shap_waterfall_local_explanation_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_case_labels: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        case_label = _require_non_empty_string(
            panel_payload.get("case_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label",
        )
        if case_label in seen_case_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label must be unique"
            )
        seen_case_labels.add(case_label)
        baseline_value = _require_numeric_value(
            panel_payload.get("baseline_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric_value(
            panel_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value",
        )
        if not all(math.isfinite(value) for value in (baseline_value, predicted_value)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] values must be finite"
            )
        contributions_payload = panel_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions must be a non-empty list"
            )
        normalized_contributions: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        contribution_sum = 0.0
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].feature must be unique within its panel"
                )
            seen_features.add(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            normalized_contributions.append(
                {
                    "feature": feature,
                    "shap_value": shap_value,
                    "feature_value_text": str(contribution_payload.get("feature_value_text") or "").strip(),
                }
            )
            contribution_sum += shap_value
        if not math.isclose(predicted_value, baseline_value + contribution_sum, rel_tol=0.0, abs_tol=1e-6):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "case_label": case_label,
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "panels": normalized_panels,
    }


def _validate_shap_force_like_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_case_labels: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        case_label = _require_non_empty_string(
            panel_payload.get("case_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label",
        )
        if case_label in seen_case_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label must be unique"
            )
        seen_case_labels.add(case_label)
        baseline_value = _require_numeric_value(
            panel_payload.get("baseline_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric_value(
            panel_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value",
        )
        if not all(math.isfinite(value) for value in (baseline_value, predicted_value)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] values must be finite"
            )
        contributions_payload = panel_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        contribution_sum = 0.0
        previous_abs_magnitude = float("inf")
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].feature must be unique within its panel"
                )
            seen_features.add(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            magnitude = abs(shap_value)
            if magnitude > previous_abs_magnitude + 1e-9:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}] contributions must be sorted by descending absolute shap_value within each panel"
                )
            previous_abs_magnitude = magnitude
            contribution_sum += shap_value
            normalized_contributions.append(
                {
                    "feature": feature,
                    "feature_value_text": str(contribution_payload.get("feature_value_text") or "").strip(),
                    "shap_value": shap_value,
                }
            )
        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "case_label": case_label,
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "panels": normalized_panels,
    }


def _normalize_shap_grouped_local_panels(
    *,
    path: Path,
    panels_payload: object,
    expected_display_id: str,
    panels_field: str,
    minimum_count: int,
    maximum_count: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty {panels_field} list"
        )
    if len(panels_payload) < minimum_count or len(panels_payload) > maximum_count:
        if minimum_count == maximum_count:
            count_description = f"exactly {minimum_count}"
        elif minimum_count == 1:
            count_description = f"at most {maximum_count}"
        else:
            count_description = f"between {minimum_count} and {maximum_count}"
        raise ValueError(
            f"{path.name} display `{expected_display_id}` {panels_field} must contain {count_description} entries"
        )

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_group_labels: set[str] = set()
    expected_feature_order: list[str] | None = None
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}] must be an object"
            )
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        group_label = _require_non_empty_string(
            panel_payload.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        baseline_value = _require_numeric_value(
            panel_payload.get("baseline_value"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric_value(
            panel_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].predicted_value",
        )
        if not all(math.isfinite(value) for value in (baseline_value, predicted_value)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}] values must be finite"
            )
        contributions_payload = panel_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        previous_rank = 0
        contribution_sum = 0.0
        feature_order: list[str] = []
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            rank = _require_non_negative_int(
                contribution_payload.get("rank"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].contributions[{contribution_index}].rank"
                ),
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}] contribution ranks must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions[{contribution_index}].feature must be unique within its panel"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            contribution_sum += shap_value
            normalized_contributions.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "shap_value": shap_value,
                }
            )

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif tuple(feature_order) != tuple(expected_feature_order):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` contribution feature order must match across {panels_field}"
            )

        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].title",
                ),
                "group_label": group_label,
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return normalized_panels, list(expected_feature_order or ())


def _validate_shap_grouped_local_explanation_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    normalized_panels, _ = _normalize_shap_grouped_local_panels(
        path=path,
        panels_payload=payload.get("panels"),
        expected_display_id=expected_display_id,
        panels_field="panels",
        minimum_count=1,
        maximum_count=3,
    )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "panels": normalized_panels,
    }


def _validate_shap_grouped_decision_path_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    panel_title = _require_non_empty_string(
        payload.get("panel_title"),
        label=f"{path.name} display `{expected_display_id}` panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
    )
    baseline_value = _require_numeric_value(
        payload.get("baseline_value"),
        label=f"{path.name} display `{expected_display_id}` baseline_value",
    )
    if not math.isfinite(baseline_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` baseline_value must be finite")

    groups_payload = payload.get("groups")
    if not isinstance(groups_payload, list) or not groups_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty groups list")
    if len(groups_payload) != 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` groups must contain exactly two entries")

    normalized_groups: list[dict[str, Any]] = []
    seen_group_ids: set[str] = set()
    seen_group_labels: set[str] = set()
    expected_feature_order: list[str] | None = None
    for group_index, group_payload in enumerate(groups_payload):
        if not isinstance(group_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` groups[{group_index}] must be an object")
        group_id = _require_non_empty_string(
            group_payload.get("group_id"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id",
        )
        if group_id in seen_group_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id must be unique"
            )
        seen_group_ids.add(group_id)
        group_label = _require_non_empty_string(
            group_payload.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        predicted_value = _require_numeric_value(
            group_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value",
        )
        if not math.isfinite(predicted_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must be finite"
            )

        contributions_payload = group_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        previous_rank = 0
        contribution_sum = 0.0
        seen_features: set[str] = set()
        feature_order: list[str] = []
        cumulative_value = baseline_value
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}] must be an object"
                )
            rank = _require_non_negative_int(
                contribution_payload.get("rank"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].rank"
                ),
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}] contribution ranks must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].feature must be unique within its group"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            start_value = cumulative_value
            end_value = cumulative_value + shap_value
            cumulative_value = end_value
            contribution_sum += shap_value
            normalized_contributions.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "shap_value": shap_value,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif tuple(feature_order) != tuple(expected_feature_order):
            raise ValueError(f"{path.name} display `{expected_display_id}` contribution feature order must match across groups")

        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_groups.append(
            {
                "group_id": group_id,
                "group_label": group_label,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_title": panel_title,
        "x_label": x_label,
        "y_label": y_label,
        "legend_title": legend_title,
        "baseline_value": baseline_value,
        "feature_order": list(expected_feature_order or ()),
        "groups": normalized_groups,
    }


def _validate_shap_multigroup_decision_path_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    panel_title = _require_non_empty_string(
        payload.get("panel_title"),
        label=f"{path.name} display `{expected_display_id}` panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
    )
    baseline_value = _require_numeric_value(
        payload.get("baseline_value"),
        label=f"{path.name} display `{expected_display_id}` baseline_value",
    )
    if not math.isfinite(baseline_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` baseline_value must be finite")

    groups_payload = payload.get("groups")
    if not isinstance(groups_payload, list) or not groups_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty groups list")
    if len(groups_payload) != 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` groups must contain exactly three entries")

    normalized_groups: list[dict[str, Any]] = []
    seen_group_ids: set[str] = set()
    seen_group_labels: set[str] = set()
    expected_feature_order: list[str] | None = None
    for group_index, group_payload in enumerate(groups_payload):
        if not isinstance(group_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` groups[{group_index}] must be an object")
        group_id = _require_non_empty_string(
            group_payload.get("group_id"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id",
        )
        if group_id in seen_group_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id must be unique"
            )
        seen_group_ids.add(group_id)
        group_label = _require_non_empty_string(
            group_payload.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        predicted_value = _require_numeric_value(
            group_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value",
        )
        if not math.isfinite(predicted_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must be finite"
            )

        contributions_payload = group_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        previous_rank = 0
        contribution_sum = 0.0
        seen_features: set[str] = set()
        feature_order: list[str] = []
        cumulative_value = baseline_value
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}] must be an object"
                )
            rank = _require_non_negative_int(
                contribution_payload.get("rank"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].rank"
                ),
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}] contribution ranks must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].feature must be unique within its group"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            start_value = cumulative_value
            end_value = cumulative_value + shap_value
            normalized_contributions.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "shap_value": shap_value,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )
            contribution_sum += shap_value
            cumulative_value = end_value

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif feature_order != expected_feature_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}] feature order must match the first group"
            )
        if not math.isclose(predicted_value, baseline_value + contribution_sum, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must equal baseline_value plus contribution sum"
            )

        normalized_groups.append(
            {
                "group_id": group_id,
                "group_label": group_label,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_title": panel_title,
        "x_label": x_label,
        "y_label": y_label,
        "legend_title": legend_title,
        "baseline_value": baseline_value,
        "feature_order": expected_feature_order or [],
        "groups": normalized_groups,
    }


def _validate_partial_dependence_ice_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_features: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        feature = _require_non_empty_string(
            panel_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature must be unique"
            )
        seen_features.add(feature)
        reference_value = _require_numeric_value(
            panel_payload.get("reference_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value",
        )
        if not math.isfinite(reference_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_label",
        )

        pdp_curve_payload = panel_payload.get("pdp_curve")
        if not isinstance(pdp_curve_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve must be an object"
            )
        pdp_x = _require_numeric_list(
            pdp_curve_payload.get("x"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x",
        )
        pdp_y = _require_numeric_list(
            pdp_curve_payload.get("y"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.y",
        )
        if len(pdp_x) != len(pdp_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x and pdp_curve.y must have the same length"
            )
        if not all(math.isfinite(value) for value in (*pdp_x, *pdp_y)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve values must be finite"
            )
        if any(right <= left for left, right in zip(pdp_x, pdp_x[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x must be strictly increasing"
            )
        if reference_value < pdp_x[0] or reference_value > pdp_x[-1]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must fall within pdp_curve.x range"
            )

        ice_curves_payload = panel_payload.get("ice_curves")
        if not isinstance(ice_curves_payload, list) or not ice_curves_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves must be a non-empty list"
            )
        normalized_ice_curves: list[dict[str, Any]] = []
        seen_curve_ids: set[str] = set()
        for curve_index, curve_payload in enumerate(ice_curves_payload):
            if not isinstance(curve_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}] must be an object"
                )
            curve_id = _require_non_empty_string(
                curve_payload.get("curve_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].curve_id"
                ),
            )
            if curve_id in seen_curve_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].curve_id must be unique within the panel"
                )
            seen_curve_ids.add(curve_id)
            curve_x = _require_numeric_list(
                curve_payload.get("x"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].x"
                ),
            )
            curve_y = _require_numeric_list(
                curve_payload.get("y"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].y"
                ),
            )
            if len(curve_x) != len(curve_y):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].x and y must have the same length"
                )
            if not all(math.isfinite(value) for value in (*curve_x, *curve_y)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}] values must be finite"
                )
            if len(curve_x) != len(pdp_x) or any(
                not math.isclose(curve_value, pdp_value, rel_tol=0.0, abs_tol=1e-9)
                for curve_value, pdp_value in zip(curve_x, pdp_x, strict=True)
            ):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].x must match pdp_curve.x within each panel"
                )
            normalized_ice_curves.append({"curve_id": curve_id, "x": curve_x, "y": curve_y})

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "feature": feature,
                "reference_value": reference_value,
                "reference_label": reference_label,
                "pdp_curve": {"x": pdp_x, "y": pdp_y},
                "ice_curves": normalized_ice_curves,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "panels": normalized_panels,
    }


def _validate_partial_dependence_interaction_contour_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    colorbar_label = _require_non_empty_string(
        payload.get("colorbar_label"),
        label=f"{path.name} display `{expected_display_id}` colorbar_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most two entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_feature_pairs: set[tuple[str, str]] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        x_feature = _require_non_empty_string(
            panel_payload.get("x_feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_feature",
        )
        y_feature = _require_non_empty_string(
            panel_payload.get("y_feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_feature",
        )
        feature_pair = (x_feature, y_feature)
        if feature_pair in seen_feature_pairs:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] feature pair must be unique"
            )
        seen_feature_pairs.add(feature_pair)
        reference_x_value = _require_numeric_value(
            panel_payload.get("reference_x_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_x_value",
        )
        reference_y_value = _require_numeric_value(
            panel_payload.get("reference_y_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_y_value",
        )
        if not math.isfinite(reference_x_value) or not math.isfinite(reference_y_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] reference values must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_label",
        )
        x_grid = _require_numeric_list(
            panel_payload.get("x_grid"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_grid",
        )
        y_grid = _require_numeric_list(
            panel_payload.get("y_grid"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_grid",
        )
        if any(right <= left for left, right in zip(x_grid, x_grid[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_grid must be strictly increasing"
            )
        if any(right <= left for left, right in zip(y_grid, y_grid[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_grid must be strictly increasing"
            )

        response_grid_payload = panel_payload.get("response_grid")
        if not isinstance(response_grid_payload, list) or len(response_grid_payload) != len(y_grid):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].response_grid must match y_grid length"
            )
        normalized_response_grid: list[list[float]] = []
        for row_index, row_payload in enumerate(response_grid_payload):
            if not isinstance(row_payload, list) or len(row_payload) != len(x_grid):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].response_grid[{row_index}] must match x_grid length"
                )
            row_values = [
                _require_numeric_value(
                    value,
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"panels[{panel_index}].response_grid[{row_index}]"
                    ),
                )
                for value in row_payload
            ]
            if not all(math.isfinite(value) for value in row_values):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].response_grid[{row_index}] must be finite"
                )
            normalized_response_grid.append(row_values)

        if not (x_grid[0] <= reference_x_value <= x_grid[-1]):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_x_value must fall within x_grid range"
            )
        if not (y_grid[0] <= reference_y_value <= y_grid[-1]):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_y_value must fall within y_grid range"
            )

        observed_points_payload = panel_payload.get("observed_points")
        if not isinstance(observed_points_payload, list) or not observed_points_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points must be a non-empty list"
            )
        normalized_observed_points: list[dict[str, Any]] = []
        seen_point_ids: set[str] = set()
        for point_index, point_payload in enumerate(observed_points_payload):
            if not isinstance(point_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}] must be an object"
                )
            point_id = _require_non_empty_string(
                point_payload.get("point_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].observed_points[{point_index}].point_id"
                ),
            )
            if point_id in seen_point_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}].point_id must be unique within the panel"
                )
            seen_point_ids.add(point_id)
            point_x = _require_numeric_value(
                point_payload.get("x"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].observed_points[{point_index}].x"
                ),
            )
            point_y = _require_numeric_value(
                point_payload.get("y"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].observed_points[{point_index}].y"
                ),
            )
            if not math.isfinite(point_x) or not math.isfinite(point_y):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}] must be finite"
                )
            if not (x_grid[0] <= point_x <= x_grid[-1]) or not (y_grid[0] <= point_y <= y_grid[-1]):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}] must fall within declared grid range"
                )
            normalized_observed_points.append({"point_id": point_id, "x": point_x, "y": point_y})

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "y_label": _require_non_empty_string(
                    panel_payload.get("y_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_label",
                ),
                "x_feature": x_feature,
                "y_feature": y_feature,
                "reference_x_value": reference_x_value,
                "reference_y_value": reference_y_value,
                "reference_label": reference_label,
                "x_grid": x_grid,
                "y_grid": y_grid,
                "response_grid": normalized_response_grid,
                "observed_points": normalized_observed_points,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "colorbar_label": colorbar_label,
        "panels": normalized_panels,
    }


def _validate_shap_bar_importance_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    bars_payload = payload.get("bars")
    if not isinstance(bars_payload, list) or not bars_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty bars list")

    normalized_bars: list[dict[str, Any]] = []
    seen_features: set[str] = set()
    previous_rank = 0
    previous_importance = float("inf")
    for bar_index, bar_payload in enumerate(bars_payload):
        if not isinstance(bar_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` bars[{bar_index}] must be an object")
        rank = _require_non_negative_int(
            bar_payload.get("rank"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank",
            allow_zero=False,
        )
        if rank <= previous_rank:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank must be strictly increasing"
            )
        previous_rank = rank
        feature = _require_non_empty_string(
            bar_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature must be unique"
            )
        seen_features.add(feature)
        importance_value = _require_numeric_value(
            bar_payload.get("importance_value"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].importance_value",
        )
        if not math.isfinite(importance_value) or importance_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].importance_value must be finite and non-negative"
            )
        if importance_value > previous_importance + 1e-12:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].importance_value must stay sorted descending by rank"
            )
        previous_importance = importance_value
        normalized_bars.append(
            {
                "rank": rank,
                "feature": feature,
                "importance_value": importance_value,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "bars": normalized_bars,
    }


def _validate_shap_signed_importance_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    negative_label = _require_non_empty_string(
        payload.get("negative_label"),
        label=f"{path.name} display `{expected_display_id}` negative_label",
    )
    positive_label = _require_non_empty_string(
        payload.get("positive_label"),
        label=f"{path.name} display `{expected_display_id}` positive_label",
    )
    bars_payload = payload.get("bars")
    if not isinstance(bars_payload, list) or not bars_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty bars list")

    normalized_bars: list[dict[str, Any]] = []
    seen_features: set[str] = set()
    previous_rank = 0
    previous_absolute_value = float("inf")
    for bar_index, bar_payload in enumerate(bars_payload):
        if not isinstance(bar_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` bars[{bar_index}] must be an object")
        rank = _require_non_negative_int(
            bar_payload.get("rank"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank",
            allow_zero=False,
        )
        if rank <= previous_rank:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank must be strictly increasing"
            )
        previous_rank = rank
        feature = _require_non_empty_string(
            bar_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature must be unique"
            )
        seen_features.add(feature)
        signed_importance_value = _require_numeric_value(
            bar_payload.get("signed_importance_value"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].signed_importance_value",
        )
        if not math.isfinite(signed_importance_value) or math.isclose(
            signed_importance_value,
            0.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].signed_importance_value must be finite and non-zero"
            )
        absolute_value = abs(signed_importance_value)
        if absolute_value > previous_absolute_value + 1e-12:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].signed_importance_value must stay sorted by descending absolute magnitude"
            )
        previous_absolute_value = absolute_value
        normalized_bars.append(
            {
                "rank": rank,
                "feature": feature,
                "signed_importance_value": signed_importance_value,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "negative_label": negative_label,
        "positive_label": positive_label,
        "bars": normalized_bars,
    }


def _validate_shap_multicohort_importance_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must not exceed three cohorts")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_cohort_labels: set[str] = set()
    expected_feature_order: list[str] | None = None

    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique")
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        cohort_label = _require_non_empty_string(
            panel_payload.get("cohort_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].cohort_label",
        )
        if cohort_label in seen_cohort_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].cohort_label must be unique"
            )
        seen_cohort_labels.add(cohort_label)
        panel_title = _require_non_empty_string(
            panel_payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
        )
        bars_payload = panel_payload.get("bars")
        if not isinstance(bars_payload, list) or not bars_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] must contain a non-empty bars list"
            )

        normalized_bars: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        previous_rank = 0
        previous_importance = float("inf")
        feature_order: list[str] = []
        for bar_index, bar_payload in enumerate(bars_payload):
            if not isinstance(bar_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}] must be an object"
                )
            rank = _require_non_negative_int(
                bar_payload.get("rank"),
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].rank",
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].rank must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                bar_payload.get("feature"),
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].feature",
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].feature must be unique within each panel"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            importance_value = _require_numeric_value(
                bar_payload.get("importance_value"),
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].importance_value",
            )
            if not math.isfinite(importance_value) or importance_value < 0.0:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].importance_value must be finite and non-negative"
                )
            if importance_value > previous_importance + 1e-12:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].importance_value must stay sorted descending by rank"
                )
            previous_importance = importance_value
            normalized_bars.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "importance_value": importance_value,
                }
            )

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif tuple(feature_order) != tuple(expected_feature_order):
            raise ValueError(f"{path.name} display `{expected_display_id}` bars feature order must match across panels")

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": panel_title,
                "cohort_label": cohort_label,
                "bars": normalized_bars,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "panels": normalized_panels,
    }


def _validate_partial_dependence_interaction_slice_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most two entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_feature_pairs: set[tuple[str, str]] = set()
    expected_slice_labels: tuple[str, ...] | None = None
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        x_feature = _require_non_empty_string(
            panel_payload.get("x_feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_feature",
        )
        slice_feature = _require_non_empty_string(
            panel_payload.get("slice_feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_feature",
        )
        feature_pair = (x_feature, slice_feature)
        if feature_pair in seen_feature_pairs:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] feature pair must be unique"
            )
        seen_feature_pairs.add(feature_pair)
        reference_value = _require_numeric_value(
            panel_payload.get("reference_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value",
        )
        if not math.isfinite(reference_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_label",
        )

        slice_curves_payload = panel_payload.get("slice_curves")
        if not isinstance(slice_curves_payload, list) or len(slice_curves_payload) < 2:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves must contain at least two entries"
            )
        normalized_slice_curves: list[dict[str, Any]] = []
        seen_slice_ids: set[str] = set()
        seen_slice_labels: set[str] = set()
        reference_x: list[float] | None = None
        ordered_slice_labels: list[str] = []
        for curve_index, curve_payload in enumerate(slice_curves_payload):
            if not isinstance(curve_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}] must be an object"
                )
            slice_id = _require_non_empty_string(
                curve_payload.get("slice_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].slice_id"
                ),
            )
            if slice_id in seen_slice_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].slice_id must be unique within the panel"
                )
            seen_slice_ids.add(slice_id)
            slice_label = _require_non_empty_string(
                curve_payload.get("slice_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].slice_label"
                ),
            )
            if slice_label in seen_slice_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].slice_label must be unique within the panel"
                )
            seen_slice_labels.add(slice_label)
            ordered_slice_labels.append(slice_label)
            conditioning_value = _require_numeric_value(
                curve_payload.get("conditioning_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].conditioning_value"
                ),
            )
            curve_x = _require_numeric_list(
                curve_payload.get("x"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].x"
                ),
            )
            curve_y = _require_numeric_list(
                curve_payload.get("y"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].y"
                ),
            )
            if len(curve_x) != len(curve_y):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].x and y must have the same length"
                )
            if not all(math.isfinite(value) for value in (*curve_x, *curve_y)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}] values must be finite"
                )
            if any(right <= left for left, right in zip(curve_x, curve_x[1:], strict=False)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].x must be strictly increasing"
                )
            if reference_x is None:
                reference_x = curve_x
            elif len(curve_x) != len(reference_x) or any(
                not math.isclose(curve_value, reference_value_item, rel_tol=0.0, abs_tol=1e-9)
                for curve_value, reference_value_item in zip(curve_x, reference_x, strict=True)
            ):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].x must match the first slice x grid within each panel"
                )
            normalized_slice_curves.append(
                {
                    "slice_id": slice_id,
                    "slice_label": slice_label,
                    "conditioning_value": conditioning_value,
                    "x": curve_x,
                    "y": curve_y,
                }
            )
        if reference_x is None or not (reference_x[0] <= reference_value <= reference_x[-1]):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must fall within slice_curve.x range"
            )
        if expected_slice_labels is None:
            expected_slice_labels = tuple(ordered_slice_labels)
        elif tuple(ordered_slice_labels) != expected_slice_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` slice_curves must keep the same ordered slice_label set across panels"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "x_feature": x_feature,
                "slice_feature": slice_feature,
                "reference_value": reference_value,
                "reference_label": reference_label,
                "slice_curves": normalized_slice_curves,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "legend_title": legend_title,
        "legend_labels": list(expected_slice_labels or ()),
        "panels": normalized_panels,
    }


def _validate_partial_dependence_subgroup_comparison_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    subgroup_panel_label = _require_non_empty_string(
        payload.get("subgroup_panel_label"),
        label=f"{path.name} display `{expected_display_id}` subgroup_panel_label",
    )
    subgroup_panel_title = _require_non_empty_string(
        payload.get("subgroup_panel_title"),
        label=f"{path.name} display `{expected_display_id}` subgroup_panel_title",
    )
    subgroup_x_label = _require_non_empty_string(
        payload.get("subgroup_x_label"),
        label=f"{path.name} display `{expected_display_id}` subgroup_x_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_subgroup_labels: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        subgroup_label = _require_non_empty_string(
            panel_payload.get("subgroup_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].subgroup_label",
        )
        if subgroup_label in seen_subgroup_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].subgroup_label must be unique"
            )
        seen_subgroup_labels.add(subgroup_label)
        reference_value = _require_numeric_value(
            panel_payload.get("reference_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value",
        )
        if not math.isfinite(reference_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_label",
        )
        pdp_curve_payload = panel_payload.get("pdp_curve")
        if not isinstance(pdp_curve_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve must be an object"
            )
        pdp_x = _require_numeric_list(
            pdp_curve_payload.get("x"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x",
        )
        pdp_y = _require_numeric_list(
            pdp_curve_payload.get("y"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.y",
        )
        if len(pdp_x) != len(pdp_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x and pdp_curve.y must have the same length"
            )
        if not all(math.isfinite(value) for value in (*pdp_x, *pdp_y)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve values must be finite"
            )
        if any(right <= left for left, right in zip(pdp_x, pdp_x[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x must be strictly increasing"
            )
        if reference_value < pdp_x[0] or reference_value > pdp_x[-1]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must fall within pdp_curve.x range"
            )

        ice_curves_payload = panel_payload.get("ice_curves")
        if not isinstance(ice_curves_payload, list) or not ice_curves_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves must be a non-empty list"
            )
        normalized_ice_curves: list[dict[str, Any]] = []
        seen_curve_ids: set[str] = set()
        for curve_index, curve_payload in enumerate(ice_curves_payload):
            if not isinstance(curve_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}] must be an object"
                )
            curve_id = _require_non_empty_string(
                curve_payload.get("curve_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].curve_id"
                ),
            )
            if curve_id in seen_curve_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].curve_id must be unique within the panel"
                )
            seen_curve_ids.add(curve_id)
            curve_x = _require_numeric_list(
                curve_payload.get("x"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].x"
                ),
            )
            curve_y = _require_numeric_list(
                curve_payload.get("y"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].y"
                ),
            )
            if len(curve_x) != len(curve_y):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].x and y must have the same length"
                )
            if not all(math.isfinite(value) for value in (*curve_x, *curve_y)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}] values must be finite"
                )
            if len(curve_x) != len(pdp_x) or any(
                not math.isclose(curve_value, pdp_value, rel_tol=0.0, abs_tol=1e-9)
                for curve_value, pdp_value in zip(curve_x, pdp_x, strict=True)
            ):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].x must match pdp_curve.x within each panel"
                )
            normalized_ice_curves.append({"curve_id": curve_id, "x": curve_x, "y": curve_y})
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "subgroup_label": subgroup_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "feature": _require_non_empty_string(
                    panel_payload.get("feature"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature",
                ),
                "reference_value": reference_value,
                "reference_label": reference_label,
                "pdp_curve": {"x": pdp_x, "y": pdp_y},
                "ice_curves": normalized_ice_curves,
            }
        )

    if subgroup_panel_label in seen_panel_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` subgroup_panel_label must be distinct from top-panel labels"
        )

    subgroup_rows_payload = payload.get("subgroup_rows")
    if not isinstance(subgroup_rows_payload, list) or not subgroup_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty subgroup_rows list")
    normalized_rows: list[dict[str, Any]] = []
    seen_row_ids: set[str] = set()
    seen_row_labels: set[str] = set()
    seen_row_panel_ids: set[str] = set()
    valid_panel_ids = {panel["panel_id"] for panel in normalized_panels}
    for row_index, row_payload in enumerate(subgroup_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must be an object")
        row_id = _require_non_empty_string(
            row_payload.get("row_id"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_id",
        )
        if row_id in seen_row_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_id must be unique"
            )
        seen_row_ids.add(row_id)
        panel_id = _require_non_empty_string(
            row_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].panel_id",
        )
        if panel_id not in valid_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].panel_id must match one of the declared panels"
            )
        if panel_id in seen_row_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows must reference each panel_id at most once"
            )
        seen_row_panel_ids.add(panel_id)
        row_label = _require_non_empty_string(
            row_payload.get("row_label"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_label",
        )
        if row_label in seen_row_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_label must be unique"
            )
        seen_row_labels.add(row_label)
        estimate = _require_numeric_value(
            row_payload.get("estimate"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].estimate",
        )
        lower = _require_numeric_value(
            row_payload.get("lower"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].lower",
        )
        upper = _require_numeric_value(
            row_payload.get("upper"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].upper",
        )
        if not (lower <= estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must satisfy lower <= estimate <= upper"
            )
        support_n = _require_non_negative_int(
            row_payload.get("support_n"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].support_n",
            allow_zero=False,
        )
        normalized_rows.append(
            {
                "row_id": row_id,
                "panel_id": panel_id,
                "row_label": row_label,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
                "support_n": support_n,
            }
        )
    if seen_row_panel_ids != valid_panel_ids:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` subgroup_rows must reference every declared panel_id exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "legend_labels": ["ICE curves", "PDP mean", "Subgroup interval"],
        "subgroup_panel_label": subgroup_panel_label,
        "subgroup_panel_title": subgroup_panel_title,
        "subgroup_x_label": subgroup_x_label,
        "panels": normalized_panels,
        "subgroup_rows": normalized_rows,
    }


def _validate_accumulated_local_effects_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_features: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        feature = _require_non_empty_string(
            panel_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature must be unique"
            )
        seen_features.add(feature)
        reference_value = _require_numeric_value(
            panel_payload.get("reference_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value",
        )
        if not math.isfinite(reference_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_label",
        )

        ale_curve_payload = panel_payload.get("ale_curve")
        if not isinstance(ale_curve_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve must be an object"
            )
        ale_x = _require_numeric_list(
            ale_curve_payload.get("x"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x",
        )
        ale_y = _require_numeric_list(
            ale_curve_payload.get("y"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.y",
        )
        if len(ale_x) != len(ale_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x and ale_curve.y must have the same length"
            )
        if not all(math.isfinite(value) for value in (*ale_x, *ale_y)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve values must be finite"
            )
        if any(right <= left for left, right in zip(ale_x, ale_x[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x must be strictly increasing"
            )

        bins_payload = panel_payload.get("local_effect_bins")
        if not isinstance(bins_payload, list) or not bins_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins must be a non-empty list"
            )
        normalized_bins: list[dict[str, Any]] = []
        seen_bin_ids: set[str] = set()
        previous_right: float | None = None
        bin_centers: list[float] = []
        cumulative_values: list[float] = []
        running_total = 0.0
        for bin_index, bin_payload in enumerate(bins_payload):
            if not isinstance(bin_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}] must be an object"
                )
            bin_id = _require_non_empty_string(
                bin_payload.get("bin_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_id"
                ),
            )
            if bin_id in seen_bin_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}].bin_id must be unique within the panel"
                )
            seen_bin_ids.add(bin_id)
            bin_left = _require_numeric_value(
                bin_payload.get("bin_left"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_left"
                ),
            )
            bin_right = _require_numeric_value(
                bin_payload.get("bin_right"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_right"
                ),
            )
            if previous_right is not None and bin_left < previous_right:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins must be strictly ordered and non-overlapping"
                )
            if bin_right <= bin_left:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}] must satisfy bin_left < bin_right"
                )
            previous_right = bin_right
            bin_center = _require_numeric_value(
                bin_payload.get("bin_center"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_center"
                ),
            )
            if not (bin_left <= bin_center <= bin_right):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}].bin_center must fall within bin_left/bin_right"
                )
            local_effect = _require_numeric_value(
                bin_payload.get("local_effect"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].local_effect"
                ),
            )
            if not math.isfinite(local_effect):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}].local_effect must be finite"
                )
            support_count = _require_non_negative_int(
                bin_payload.get("support_count"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].support_count"
                ),
                allow_zero=False,
            )
            running_total += local_effect
            cumulative_values.append(running_total)
            bin_centers.append(bin_center)
            normalized_bins.append(
                {
                    "bin_id": bin_id,
                    "bin_left": bin_left,
                    "bin_right": bin_right,
                    "bin_center": bin_center,
                    "local_effect": local_effect,
                    "support_count": support_count,
                }
            )
        if len(bin_centers) != len(ale_x) or any(
            not math.isclose(x_value, center_value, rel_tol=0.0, abs_tol=1e-9)
            for x_value, center_value in zip(ale_x, bin_centers, strict=True)
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x must match local_effect_bins.bin_center"
            )
        if any(
            not math.isclose(curve_value, cumulative_value, rel_tol=1e-9, abs_tol=1e-9)
            for curve_value, cumulative_value in zip(ale_y, cumulative_values, strict=True)
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.y must equal the cumulative sum of local_effect_bins within each panel"
            )
        if reference_value < normalized_bins[0]["bin_left"] or reference_value > normalized_bins[-1]["bin_right"]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must fall within local_effect_bins range"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "feature": feature,
                "reference_value": reference_value,
                "reference_label": reference_label,
                "ale_curve": {"x": ale_x, "y": ale_y},
                "local_effect_bins": normalized_bins,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "legend_labels": ["Accumulated local effect", "Local effect per bin"],
        "panels": normalized_panels,
    }


def _normalize_feature_response_support_panels(
    *,
    path: Path,
    panels_payload: object,
    expected_display_id: str,
    panels_field: str,
    minimum_count: int,
    maximum_count: int,
) -> list[dict[str, Any]]:
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty {panels_field} list"
        )
    if len(panels_payload) < minimum_count or len(panels_payload) > maximum_count:
        if minimum_count == maximum_count:
            count_description = f"exactly {minimum_count}"
        else:
            count_description = f"between {minimum_count} and {maximum_count}"
        raise ValueError(
            f"{path.name} display `{expected_display_id}` {panels_field} must contain {count_description} entries"
        )

    allowed_support_kinds = {
        "observed_support",
        "subgroup_support",
        "bin_support",
        "extrapolation_warning",
    }
    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_features: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}] must be an object"
            )
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        feature = _require_non_empty_string(
            panel_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].feature must be unique"
            )
        seen_features.add(feature)
        reference_value = _require_numeric_value(
            panel_payload.get("reference_value"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_value",
        )
        if not math.isfinite(reference_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_value must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_label",
        )
        response_curve_payload = panel_payload.get("response_curve")
        if not isinstance(response_curve_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve must be an object"
            )
        curve_x = _require_numeric_list(
            response_curve_payload.get("x"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.x",
        )
        curve_y = _require_numeric_list(
            response_curve_payload.get("y"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.y",
        )
        if len(curve_x) != len(curve_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.x and response_curve.y must have the same length"
            )
        if not all(math.isfinite(value) for value in (*curve_x, *curve_y)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve values must be finite"
            )
        if any(right <= left for left, right in zip(curve_x, curve_x[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.x must be strictly increasing"
            )
        if reference_value < curve_x[0] or reference_value > curve_x[-1]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_value must fall within response_curve.x range"
            )

        support_segments_payload = panel_payload.get("support_segments")
        if not isinstance(support_segments_payload, list) or not support_segments_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must be a non-empty list"
            )
        normalized_support_segments: list[dict[str, Any]] = []
        seen_segment_ids: set[str] = set()
        previous_domain_end: float | None = None
        curve_start = float(curve_x[0])
        curve_end = float(curve_x[-1])
        for segment_index, segment_payload in enumerate(support_segments_payload):
            if not isinstance(segment_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}] must be an object"
                )
            segment_id = _require_non_empty_string(
                segment_payload.get("segment_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].segment_id"
                ),
            )
            if segment_id in seen_segment_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}].segment_id must be unique within the panel"
                )
            seen_segment_ids.add(segment_id)
            segment_label = _require_non_empty_string(
                segment_payload.get("segment_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].segment_label"
                ),
            )
            support_kind = _require_non_empty_string(
                segment_payload.get("support_kind"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].support_kind"
                ),
            )
            if support_kind not in allowed_support_kinds:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}].support_kind must be one of {sorted(allowed_support_kinds)}"
                )
            domain_start = _require_numeric_value(
                segment_payload.get("domain_start"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].domain_start"
                ),
            )
            domain_end = _require_numeric_value(
                segment_payload.get("domain_end"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].domain_end"
                ),
            )
            if not math.isfinite(domain_start) or not math.isfinite(domain_end) or domain_end <= domain_start:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}] domain bounds must be finite and strictly increasing"
                )
            if domain_start < curve_start or domain_end > curve_end:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}] must stay within response_curve.x range"
                )
            if segment_index == 0 and not math.isclose(domain_start, curve_start, rel_tol=0.0, abs_tol=1e-9):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must cover the full response_curve.x range without gaps"
                )
            if previous_domain_end is not None and not math.isclose(
                domain_start,
                previous_domain_end,
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must cover the full response_curve.x range without gaps"
                )
            previous_domain_end = domain_end
            normalized_support_segments.append(
                {
                    "segment_id": segment_id,
                    "segment_label": segment_label,
                    "support_kind": support_kind,
                    "domain_start": domain_start,
                    "domain_end": domain_end,
                }
            )
        if previous_domain_end is None or not math.isclose(previous_domain_end, curve_end, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must cover the full response_curve.x range without gaps"
            )

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].x_label",
                ),
                "feature": feature,
                "reference_value": reference_value,
                "reference_label": reference_label,
                "response_curve": {"x": curve_x, "y": curve_y},
                "support_segments": normalized_support_segments,
            }
        )

    return normalized_panels


def _validate_feature_response_support_domain_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    normalized_panels = _normalize_feature_response_support_panels(
        path=path,
        panels_payload=payload.get("panels"),
        expected_display_id=expected_display_id,
        panels_field="panels",
        minimum_count=2,
        maximum_count=3,
    )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "panels": normalized_panels,
    }


def _validate_shap_grouped_local_support_domain_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    grouped_local_x_label = _require_non_empty_string(
        payload.get("grouped_local_x_label"),
        label=f"{path.name} display `{expected_display_id}` grouped_local_x_label",
    )
    support_y_label = _require_non_empty_string(
        payload.get("support_y_label"),
        label=f"{path.name} display `{expected_display_id}` support_y_label",
    )
    support_legend_title = _require_non_empty_string(
        payload.get("support_legend_title"),
        label=f"{path.name} display `{expected_display_id}` support_legend_title",
    )
    local_panels, local_feature_order = _normalize_shap_grouped_local_panels(
        path=path,
        panels_payload=payload.get("local_panels"),
        expected_display_id=expected_display_id,
        panels_field="local_panels",
        minimum_count=2,
        maximum_count=3,
    )
    support_panels = _normalize_feature_response_support_panels(
        path=path,
        panels_payload=payload.get("support_panels"),
        expected_display_id=expected_display_id,
        panels_field="support_panels",
        minimum_count=2,
        maximum_count=2,
    )

    local_panel_labels = {str(panel["panel_label"]) for panel in local_panels}
    support_features = [str(panel["feature"]) for panel in support_panels]
    if any(str(panel["panel_label"]) in local_panel_labels for panel in support_panels):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.panel_label must stay distinct from local_panels.panel_label"
        )
    if not set(support_features).issubset(set(local_feature_order)):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature must stay within the shared local feature order"
        )
    expected_support_feature_order = [feature for feature in local_feature_order if feature in set(support_features)]
    if support_features != expected_support_feature_order:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature order must follow the shared local feature order"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "grouped_local_x_label": grouped_local_x_label,
        "support_y_label": support_y_label,
        "support_legend_title": support_legend_title,
        "support_legend_labels": [
            "Response curve",
            "Observed support",
            "Subgroup support",
            "Bin support",
            "Extrapolation reminder",
        ],
        "local_shared_feature_order": local_feature_order,
        "local_panels": local_panels,
        "support_panels": support_panels,
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


def _validate_generalizability_subgroup_composite_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    metric_family = _require_non_empty_string(
        payload.get("metric_family"),
        label=f"{path.name} display `{expected_display_id}` metric_family",
    )
    if metric_family not in {"discrimination", "calibration_ratio", "effect_estimate", "utility_delta"}:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` metric_family must be one of discrimination, calibration_ratio, effect_estimate, or utility_delta"
        )
    primary_label = _require_non_empty_string(
        payload.get("primary_label"),
        label=f"{path.name} display `{expected_display_id}` primary_label",
    )
    comparator_label = str(payload.get("comparator_label") or "").strip()
    overview_rows_payload = payload.get("overview_rows")
    if not isinstance(overview_rows_payload, list) or not overview_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty overview_rows list")
    normalized_overview_rows: list[dict[str, Any]] = []
    seen_cohort_ids: set[str] = set()
    seen_cohort_labels: set[str] = set()
    for row_index, row_payload in enumerate(overview_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` overview_rows[{row_index}] must be an object")
        cohort_id = _require_non_empty_string(
            row_payload.get("cohort_id"),
            label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_id",
        )
        if cohort_id in seen_cohort_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_id must be unique"
            )
        seen_cohort_ids.add(cohort_id)
        cohort_label = _require_non_empty_string(
            row_payload.get("cohort_label"),
            label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_label",
        )
        if cohort_label in seen_cohort_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_label must be unique"
            )
        seen_cohort_labels.add(cohort_label)
        metric_value = _require_numeric_value(
            row_payload.get("metric_value"),
            label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].metric_value",
        )
        if not math.isfinite(metric_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].metric_value must be finite"
            )
        comparator_metric_raw = row_payload.get("comparator_metric_value")
        if comparator_label:
            if comparator_metric_raw is None:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].comparator_metric_value must be provided for every overview row when comparator_label is declared"
                )
            comparator_metric_value = _require_numeric_value(
                comparator_metric_raw,
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"overview_rows[{row_index}].comparator_metric_value"
                ),
            )
            if not math.isfinite(comparator_metric_value):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].comparator_metric_value must be finite"
                )
        else:
            if comparator_metric_raw is not None:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].comparator_metric_value must be absent unless comparator_label is declared"
                )
            comparator_metric_value = None
        normalized_row: dict[str, Any] = {
            "cohort_id": cohort_id,
            "cohort_label": cohort_label,
            "support_count": _require_non_negative_int(
                row_payload.get("support_count"),
                label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].support_count",
            ),
            "metric_value": metric_value,
        }
        if comparator_metric_value is not None:
            normalized_row["comparator_metric_value"] = comparator_metric_value
        if row_payload.get("event_count") is not None:
            normalized_row["event_count"] = _require_non_negative_int(
                row_payload.get("event_count"),
                label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].event_count",
            )
        normalized_overview_rows.append(normalized_row)

    subgroup_rows_payload = payload.get("subgroup_rows")
    if not isinstance(subgroup_rows_payload, list) or not subgroup_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty subgroup_rows list")
    normalized_subgroup_rows: list[dict[str, Any]] = []
    seen_subgroup_ids: set[str] = set()
    seen_subgroup_labels: set[str] = set()
    for row_index, row_payload in enumerate(subgroup_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must be an object")
        subgroup_id = _require_non_empty_string(
            row_payload.get("subgroup_id"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_id",
        )
        if subgroup_id in seen_subgroup_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_id must be unique"
            )
        seen_subgroup_ids.add(subgroup_id)
        subgroup_label = _require_non_empty_string(
            row_payload.get("subgroup_label"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_label",
        )
        if subgroup_label in seen_subgroup_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_label must be unique"
            )
        seen_subgroup_labels.add(subgroup_label)
        estimate = _require_numeric_value(
            row_payload.get("estimate"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].estimate",
        )
        lower = _require_numeric_value(
            row_payload.get("lower"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].lower",
        )
        upper = _require_numeric_value(
            row_payload.get("upper"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].upper",
        )
        if not all(math.isfinite(value) for value in (estimate, lower, upper)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] values must be finite"
            )
        if not (lower <= estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must satisfy lower <= estimate <= upper"
            )
        normalized_row = {
            "subgroup_id": subgroup_id,
            "subgroup_label": subgroup_label,
            "estimate": estimate,
            "lower": lower,
            "upper": upper,
        }
        if row_payload.get("group_n") is not None:
            normalized_row["group_n"] = _require_non_negative_int(
                row_payload.get("group_n"),
                label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].group_n",
            )
        normalized_subgroup_rows.append(normalized_row)

    subgroup_reference_value = _require_numeric_value(
        payload.get("subgroup_reference_value"),
        label=f"{path.name} display `{expected_display_id}` subgroup_reference_value",
    )
    if not math.isfinite(subgroup_reference_value):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` subgroup_reference_value must be finite"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_family": metric_family,
        "primary_label": primary_label,
        "comparator_label": comparator_label,
        "overview_panel_title": _require_non_empty_string(
            payload.get("overview_panel_title"),
            label=f"{path.name} display `{expected_display_id}` overview_panel_title",
        ),
        "overview_x_label": _require_non_empty_string(
            payload.get("overview_x_label"),
            label=f"{path.name} display `{expected_display_id}` overview_x_label",
        ),
        "overview_rows": normalized_overview_rows,
        "subgroup_panel_title": _require_non_empty_string(
            payload.get("subgroup_panel_title"),
            label=f"{path.name} display `{expected_display_id}` subgroup_panel_title",
        ),
        "subgroup_x_label": _require_non_empty_string(
            payload.get("subgroup_x_label"),
            label=f"{path.name} display `{expected_display_id}` subgroup_x_label",
        ),
        "subgroup_reference_value": subgroup_reference_value,
        "subgroup_rows": normalized_subgroup_rows,
    }


def _validate_center_transportability_governance_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    metric_family = _require_non_empty_string(
        payload.get("metric_family"),
        label=f"{path.name} display `{expected_display_id}` metric_family",
    )
    supported_metric_families = {"discrimination", "calibration_ratio", "effect_estimate", "utility_delta"}
    if metric_family not in supported_metric_families:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` metric_family must be one of "
            "discrimination, calibration_ratio, effect_estimate, or utility_delta"
        )

    metric_reference_value = _require_numeric_value(
        payload.get("metric_reference_value"),
        label=f"{path.name} display `{expected_display_id}` metric_reference_value",
    )
    if not math.isfinite(metric_reference_value):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` metric_reference_value must be finite"
        )
    batch_shift_threshold = _require_numeric_value(
        payload.get("batch_shift_threshold"),
        label=f"{path.name} display `{expected_display_id}` batch_shift_threshold",
    )
    if not math.isfinite(batch_shift_threshold) or batch_shift_threshold <= 0.0:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` batch_shift_threshold must be positive and finite"
        )
    slope_acceptance_lower = _require_numeric_value(
        payload.get("slope_acceptance_lower"),
        label=f"{path.name} display `{expected_display_id}` slope_acceptance_lower",
    )
    slope_acceptance_upper = _require_numeric_value(
        payload.get("slope_acceptance_upper"),
        label=f"{path.name} display `{expected_display_id}` slope_acceptance_upper",
    )
    if (
        not math.isfinite(slope_acceptance_lower)
        or not math.isfinite(slope_acceptance_upper)
        or slope_acceptance_lower <= 0.0
        or slope_acceptance_upper <= 0.0
        or slope_acceptance_lower >= slope_acceptance_upper
    ):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` slope_acceptance band must be positive, finite, and ordered"
        )
    oe_ratio_acceptance_lower = _require_numeric_value(
        payload.get("oe_ratio_acceptance_lower"),
        label=f"{path.name} display `{expected_display_id}` oe_ratio_acceptance_lower",
    )
    oe_ratio_acceptance_upper = _require_numeric_value(
        payload.get("oe_ratio_acceptance_upper"),
        label=f"{path.name} display `{expected_display_id}` oe_ratio_acceptance_upper",
    )
    if (
        not math.isfinite(oe_ratio_acceptance_lower)
        or not math.isfinite(oe_ratio_acceptance_upper)
        or oe_ratio_acceptance_lower <= 0.0
        or oe_ratio_acceptance_upper <= 0.0
        or oe_ratio_acceptance_lower >= oe_ratio_acceptance_upper
    ):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` oe_ratio_acceptance band must be positive, finite, and ordered"
        )

    centers_payload = payload.get("centers")
    if not isinstance(centers_payload, list) or not centers_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty centers list")
    supported_verdicts = {
        "stable",
        "context_dependent",
        "recalibration_required",
        "insufficient_support",
        "unstable",
    }
    normalized_centers: list[dict[str, Any]] = []
    seen_center_ids: set[str] = set()
    seen_center_labels: set[str] = set()
    for center_index, center_payload in enumerate(centers_payload):
        if not isinstance(center_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` centers[{center_index}] must be an object")
        center_id = _require_non_empty_string(
            center_payload.get("center_id"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].center_id",
        )
        if center_id in seen_center_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].center_id must be unique"
            )
        seen_center_ids.add(center_id)
        center_label = _require_non_empty_string(
            center_payload.get("center_label"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].center_label",
        )
        if center_label in seen_center_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].center_label must be unique"
            )
        seen_center_labels.add(center_label)
        support_count = _require_non_negative_int(
            center_payload.get("support_count"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].support_count",
            allow_zero=False,
        )
        event_count = _require_non_negative_int(
            center_payload.get("event_count"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].event_count",
        )
        if event_count > support_count:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].event_count must not exceed support_count"
            )
        metric_estimate = _require_numeric_value(
            center_payload.get("metric_estimate"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].metric_estimate",
        )
        metric_lower = _require_numeric_value(
            center_payload.get("metric_lower"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].metric_lower",
        )
        metric_upper = _require_numeric_value(
            center_payload.get("metric_upper"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].metric_upper",
        )
        if not all(math.isfinite(value) for value in (metric_estimate, metric_lower, metric_upper)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}] metric values must be finite"
            )
        if not (metric_lower <= metric_estimate <= metric_upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}] must satisfy metric_lower <= metric_estimate <= metric_upper"
            )
        max_shift = _require_probability_value(
            center_payload.get("max_shift"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].max_shift",
        )
        slope = _require_numeric_value(
            center_payload.get("slope"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].slope",
        )
        if not math.isfinite(slope) or slope <= 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].slope must be positive and finite"
            )
        oe_ratio = _require_numeric_value(
            center_payload.get("oe_ratio"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].oe_ratio",
        )
        if not math.isfinite(oe_ratio) or oe_ratio <= 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].oe_ratio must be positive and finite"
            )
        verdict = _require_non_empty_string(
            center_payload.get("verdict"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].verdict",
        )
        if verdict not in supported_verdicts:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].verdict must be one of {sorted(supported_verdicts)}"
            )
        normalized_center = {
            "center_id": center_id,
            "center_label": center_label,
            "cohort_role": _require_non_empty_string(
                center_payload.get("cohort_role"),
                label=f"{path.name} display `{expected_display_id}` centers[{center_index}].cohort_role",
            ),
            "support_count": support_count,
            "event_count": event_count,
            "metric_estimate": metric_estimate,
            "metric_lower": metric_lower,
            "metric_upper": metric_upper,
            "max_shift": max_shift,
            "slope": slope,
            "oe_ratio": oe_ratio,
            "verdict": verdict,
            "action": _require_non_empty_string(
                center_payload.get("action"),
                label=f"{path.name} display `{expected_display_id}` centers[{center_index}].action",
            ),
        }
        detail_text = str(center_payload.get("detail") or "").strip()
        if center_payload.get("detail") is not None and not detail_text:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].detail must be non-empty when present"
            )
        if detail_text:
            normalized_center["detail"] = detail_text
        normalized_centers.append(normalized_center)

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_family": metric_family,
        "metric_panel_title": _require_non_empty_string(
            payload.get("metric_panel_title"),
            label=f"{path.name} display `{expected_display_id}` metric_panel_title",
        ),
        "metric_x_label": _require_non_empty_string(
            payload.get("metric_x_label"),
            label=f"{path.name} display `{expected_display_id}` metric_x_label",
        ),
        "metric_reference_value": metric_reference_value,
        "batch_shift_threshold": batch_shift_threshold,
        "slope_acceptance_lower": slope_acceptance_lower,
        "slope_acceptance_upper": slope_acceptance_upper,
        "oe_ratio_acceptance_lower": oe_ratio_acceptance_lower,
        "oe_ratio_acceptance_upper": oe_ratio_acceptance_upper,
        "summary_panel_title": _require_non_empty_string(
            payload.get("summary_panel_title"),
            label=f"{path.name} display `{expected_display_id}` summary_panel_title",
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
    if spec.input_schema_id == "time_dependent_roc_comparison_inputs_v1":
        return payload_path, _validate_time_dependent_roc_comparison_display_payload(
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
    if spec.input_schema_id == "time_to_event_landmark_performance_inputs_v1":
        return payload_path, _validate_time_to_event_landmark_performance_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_threshold_governance_inputs_v1":
        return payload_path, _validate_time_to_event_threshold_governance_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_multihorizon_calibration_inputs_v1":
        return payload_path, _validate_time_to_event_multihorizon_calibration_display_payload(
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
    if spec.input_schema_id == "time_to_event_stratified_cumulative_incidence_inputs_v1":
        return payload_path, _validate_time_to_event_stratified_cumulative_incidence_display_payload(
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
    if spec.input_schema_id == "celltype_signature_heatmap_inputs_v1":
        return payload_path, _validate_celltype_signature_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "single_cell_atlas_overview_inputs_v1":
        return payload_path, _validate_single_cell_atlas_overview_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_bridge_panel_inputs_v1":
        return payload_path, _validate_atlas_spatial_bridge_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "spatial_niche_map_inputs_v1":
        return payload_path, _validate_spatial_niche_map_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "trajectory_progression_inputs_v1":
        return payload_path, _validate_trajectory_progression_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_trajectory_storyboard_inputs_v1":
        return payload_path, _validate_atlas_spatial_trajectory_storyboard_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_trajectory_density_coverage_panel_inputs_v1":
        return payload_path, _validate_atlas_spatial_trajectory_density_coverage_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_trajectory_context_support_panel_inputs_v1":
        return payload_path, _validate_atlas_spatial_trajectory_context_support_display_payload(
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
    if spec.input_schema_id == "performance_heatmap_inputs_v1":
        return payload_path, _validate_performance_heatmap_display_payload(
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
    if spec.input_schema_id == "gsva_ssgsea_heatmap_inputs_v1":
        return payload_path, _validate_gsva_ssgsea_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "pathway_enrichment_dotplot_panel_inputs_v1":
        return payload_path, _validate_pathway_enrichment_dotplot_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "omics_volcano_panel_inputs_v1":
        return payload_path, _validate_omics_volcano_panel_display_payload(
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
    if spec.input_schema_id == "compact_effect_estimate_panel_inputs_v1":
        return payload_path, _validate_compact_effect_estimate_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "coefficient_path_panel_inputs_v1":
        return payload_path, _validate_coefficient_path_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "broader_heterogeneity_summary_panel_inputs_v1":
        return payload_path, _validate_broader_heterogeneity_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "center_transportability_governance_summary_panel_inputs_v1":
        return payload_path, _validate_center_transportability_governance_summary_panel_display_payload(
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
    if spec.input_schema_id == "shap_dependence_panel_inputs_v1":
        return payload_path, _validate_shap_dependence_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_waterfall_local_explanation_panel_inputs_v1":
        return payload_path, _validate_shap_waterfall_local_explanation_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_force_like_summary_panel_inputs_v1":
        return payload_path, _validate_shap_force_like_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_grouped_local_explanation_panel_inputs_v1":
        return payload_path, _validate_shap_grouped_local_explanation_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_grouped_decision_path_panel_inputs_v1":
        return payload_path, _validate_shap_grouped_decision_path_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_multigroup_decision_path_panel_inputs_v1":
        return payload_path, _validate_shap_multigroup_decision_path_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_bar_importance_inputs_v1":
        return payload_path, _validate_shap_bar_importance_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_signed_importance_panel_inputs_v1":
        return payload_path, _validate_shap_signed_importance_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_multicohort_importance_panel_inputs_v1":
        return payload_path, _validate_shap_multicohort_importance_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_ice_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_ice_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_interaction_contour_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_interaction_contour_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_interaction_slice_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_interaction_slice_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_subgroup_comparison_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_subgroup_comparison_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "accumulated_local_effects_panel_inputs_v1":
        return payload_path, _validate_accumulated_local_effects_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "feature_response_support_domain_panel_inputs_v1":
        return payload_path, _validate_feature_response_support_domain_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_grouped_local_support_domain_panel_inputs_v1":
        return payload_path, _validate_shap_grouped_local_support_domain_panel_display_payload(
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
    if spec.input_schema_id == "generalizability_subgroup_composite_inputs_v1":
        return payload_path, _validate_generalizability_subgroup_composite_display_payload(
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


@lru_cache(maxsize=4)
def _flow_font_path(font_weight: str) -> str:
    normalized_weight = str(font_weight or "normal").strip().lower()
    filename = "DejaVuSans-Bold.ttf" if "bold" in normalized_weight else "DejaVuSans.ttf"
    font_path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / filename
    if not font_path.exists():
        raise FileNotFoundError(f"matplotlib bundled flow font is missing: {font_path}")
    return str(font_path)


def _flow_font_properties(*, font_weight: str) -> FontProperties:
    return FontProperties(fname=_flow_font_path(font_weight), weight=font_weight)


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
    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )
    template_id = display_registry.get_illustration_shell_spec("cohort_flow_figure").shell_id
    render_callable = display_pack_runtime.load_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=template_id,
    )
    render_callable(
        template_id=template_id,
        output_svg_path=output_svg_path,
        output_png_path=output_png_path,
        output_layout_path=output_layout_path,
        title=title,
        steps=steps,
        exclusions=exclusions,
        endpoint_inventory=endpoint_inventory,
        design_panels=design_panels,
        render_context=render_context,
    )



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
    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )
    template_id = display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id
    render_callable = display_pack_runtime.load_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=template_id,
    )
    render_callable(
        template_id=template_id,
        output_svg_path=output_svg_path,
        output_png_path=output_png_path,
        output_layout_path=output_layout_path,
        shell_payload=shell_payload,
        render_context=render_context,
    )



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
    layout_boxes = []
    if str(axes.title.get_text() or "").strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=axes.title.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=figure,
            bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        )
    )
    panel_box = _bbox_to_layout_box(
        figure=figure,
        bbox=axes.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )
    x_min, x_max = axes.get_xlim()
    for row_index, row in enumerate(rows):
        row_box = _data_box_to_layout_box(
            axes=axes,
            figure=figure,
            x0=x_min,
            y0=row_index - 0.42,
            x1=x_max,
            y1=row_index + 0.42,
            box_id=f"feature_row_{row['feature']}",
            box_type="feature_row",
        )
        row_box["y0"] = max(float(row_box["y0"]), float(panel_box["y0"]))
        row_box["y1"] = min(float(row_box["y1"]), float(panel_box["y1"]))
        layout_boxes.append(row_box)
    zero_line_x, _ = _data_point_to_figure_xy(
        axes=axes,
        figure=figure,
        x=0.0,
        y=0.0,
    )
    guide_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        ),
        {
            "box_id": "zero_line",
            "box_type": "zero_line",
            "x0": zero_line_x,
            "y0": float(panel_box["y0"]),
            "x1": zero_line_x,
            "y1": float(panel_box["y1"]),
        },
    ]
    row_box_id_by_feature = {f"{row['feature']}": f"feature_row_{row['feature']}" for row in rows}
    feature_label_metrics: list[dict[str, Any]] = []
    for row, label_artist in zip(rows, axes.get_yticklabels()):
        label_box_id = f"feature_label_{row['feature']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=label_box_id,
                box_type="feature_label",
            )
        )
        feature_label_metrics.append(
            {
                "feature": str(row["feature"]),
                "row_box_id": row_box_id_by_feature[str(row["feature"])],
                "label_box_id": label_box_id,
            }
        )
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
            "figure_height_inches": float(figure.get_figheight()),
            "figure_width_inches": float(figure.get_figwidth()),
            "feature_labels": feature_label_metrics,
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
    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
    render_callable = display_pack_runtime.load_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=template_id,
    )
    render_callable(
        template_id=template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
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


def _prepare_table_shell_output_paths(*, output_md_path: Path, output_csv_path: Path | None = None) -> None:
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    if output_csv_path is not None:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)


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






















def _render_python_evidence_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
    render_callable = display_pack_runtime.resolve_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=template_id,
    )
    if render_callable is None:
        raise RuntimeError(f"template `{template_id}` is not wired to a pack-local python entrypoint")
    render_callable(
        template_id=template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )



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
        requirement_short_id = ""
        if display_kind == "figure":
            if display_registry.is_illustration_shell(requirement_key):
                requirement_short_id = get_template_short_id(
                    display_registry.get_illustration_shell_spec(requirement_key).shell_id
                )
            elif display_registry.is_evidence_figure_template(requirement_key):
                requirement_short_id = get_template_short_id(
                    display_registry.get_evidence_figure_spec(requirement_key).template_id
                )
        elif display_kind == "table" and display_registry.is_table_shell(requirement_key):
            requirement_short_id = get_template_short_id(display_registry.get_table_shell_spec(requirement_key).shell_id)

        if (
            display_kind == "figure"
            and display_registry.is_illustration_shell(requirement_key)
            and requirement_short_id != "submission_graphical_abstract"
        ):
            spec = display_registry.get_illustration_shell_spec(requirement_key)
            pack_id, template_short_id = _require_namespaced_registry_id(
                spec.shell_id,
                label=f"{requirement_key} shell_id",
            )
            output_stem = _ILLUSTRATION_OUTPUT_STEM_BY_TEMPLATE_SHORT_ID.get(template_short_id)
            if output_stem is None:
                raise ValueError(f"unsupported illustration shell output stem for `{spec.shell_id}`")
            default_title, default_caption = _ILLUSTRATION_DEFAULT_TEXT_BY_TEMPLATE_SHORT_ID.get(
                template_short_id,
                ("", ""),
            )
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
            payload_path = _illustration_payload_path(
                paper_root=resolved_paper_root,
                input_schema_id=spec.input_schema_id,
            )
            shell_payload = load_json(payload_path)
            paper_role = str(shell_payload.get("paper_role") or spec.allowed_paper_roles[0]).strip()
            if paper_role not in spec.allowed_paper_roles:
                allowed_roles = ", ".join(spec.allowed_paper_roles)
                raise ValueError(
                    f"display `{display_id}` paper_role `{paper_role}` is not allowed for illustration shell `{spec.shell_id}`; "
                    f"allowed: {allowed_roles}"
                )
            figure_id = _resolve_figure_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.svg"
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.png"
            output_layout_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.layout.json"
            _prepare_python_illustration_output_paths(
                output_png_path=output_png_path,
                output_svg_path=output_svg_path,
                layout_sidecar_path=output_layout_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.shell_id,
                paper_root=resolved_paper_root,
            )
            render_result = dict(
                render_callable(
                    template_id=spec.shell_id,
                    shell_payload=shell_payload,
                    payload_path=payload_path,
                    render_context=render_context,
                    output_svg_path=output_svg_path,
                    output_png_path=output_png_path,
                    output_layout_path=output_layout_path,
                )
                or {}
            )
            layout_sidecar = _load_layout_sidecar_or_raise(path=output_layout_path, template_id=spec.shell_id)
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
                "pack_id": pack_id,
                "renderer_family": spec.renderer_family,
                "paper_role": paper_role,
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.shell_qc_profile,
                "qc_result": qc_result,
                "title": str(render_result.get("title") or shell_payload.get("title") or default_title).strip()
                or default_title,
                "caption": str(render_result.get("caption") or shell_payload.get("caption") or default_caption).strip(),
                "export_paths": [
                    _paper_relative_path(output_svg_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
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

        if requirement_short_id == "table1_baseline_characteristics":
            if display_kind != "table":
                raise ValueError("table1_baseline_characteristics must be registered as a table display")
            spec = display_registry.get_table_shell_spec(requirement_key)
            pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label="table1_baseline_characteristics shell_id")
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.csv"
            output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.md"
            _prepare_table_shell_output_paths(
                output_md_path=output_md_path,
                output_csv_path=output_csv_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.shell_id,
                paper_root=resolved_paper_root,
            )
            render_result = dict(
                render_callable(
                    template_id=spec.shell_id,
                    payload_path=payload_path,
                    payload=payload,
                    output_md_path=output_md_path,
                    output_csv_path=output_csv_path,
                )
                or {}
            )
            written_files.extend([str(output_csv_path), str(output_md_path)])
            entry = {
                "table_id": table_id,
                "table_shell_id": spec.shell_id,
                "pack_id": pack_id,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.table_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": str(render_result.get("title") or "Baseline characteristics").strip() or "Baseline characteristics",
                "caption": str(
                    render_result.get("caption") or "Baseline characteristics across prespecified groups."
                ).strip(),
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

        if requirement_short_id in {
            "table2_time_to_event_performance_summary",
            "table3_clinical_interpretation_summary",
            "performance_summary_table_generic",
            "grouped_risk_event_summary_table",
        }:
            if display_kind != "table":
                raise ValueError(f"{requirement_key} must be registered as a table display")
            spec = display_registry.get_table_shell_spec(requirement_key)
            pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label=f"{requirement_key} shell_id")
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path: Path | None = None
            if requirement_short_id == "table2_time_to_event_performance_summary":
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_time_to_event_performance_summary.md"
                default_title = "Time-to-event model performance summary"
                default_caption = "Time-to-event discrimination and error metrics across analysis cohorts."
            elif requirement_short_id == "table3_clinical_interpretation_summary":
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_clinical_interpretation_summary.md"
                default_title = "Clinical interpretation summary"
                default_caption = "Clinical interpretation anchors for prespecified risk groups and use cases."
            elif requirement_short_id == "performance_summary_table_generic":
                output_md_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.md"
                )
                output_csv_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.csv"
                )
                default_title = "Performance summary"
                default_caption = "Structured repeated-validation performance summaries across candidate packages."
            else:
                output_md_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.md"
                )
                output_csv_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.csv"
                )
                default_title = "Grouped risk event summary"
                default_caption = "Observed case counts, event counts, and absolute risks across grouped-risk strata."
            _prepare_table_shell_output_paths(
                output_md_path=output_md_path,
                output_csv_path=output_csv_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.shell_id,
                paper_root=resolved_paper_root,
            )
            render_result = dict(
                render_callable(
                    template_id=spec.shell_id,
                    payload_path=payload_path,
                    payload=payload,
                    output_md_path=output_md_path,
                    output_csv_path=output_csv_path,
                )
                or {}
            )
            written_files.append(str(output_md_path))
            if output_csv_path is not None:
                written_files.append(str(output_csv_path))
            entry = {
                "table_id": table_id,
                "table_shell_id": spec.shell_id,
                "pack_id": pack_id,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.table_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": str(render_result.get("title") or default_title).strip() or default_title,
                "caption": str(render_result.get("caption") or default_caption).strip(),
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
            pack_id, template_short_id = _require_namespaced_registry_id(spec.template_id, label=f"{requirement_key} template_id")
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
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.png"
            output_pdf_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.pdf"
            layout_sidecar_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.layout.json"
            _prepare_python_render_output_paths(
                output_png_path=output_png_path,
                output_pdf_path=output_pdf_path,
                layout_sidecar_path=layout_sidecar_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.template_id,
                paper_root=resolved_paper_root,
            )
            render_callable(
                template_id=spec.template_id,
                display_payload=render_payload,
                output_png_path=output_png_path,
                output_pdf_path=output_pdf_path,
                layout_sidecar_path=layout_sidecar_path,
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
                "pack_id": pack_id,
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
        pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label="submission_graphical_abstract shell_id")
        if style_profile is None:
            style_profile = publication_display_contract.load_publication_style_profile(
                resolved_paper_root / "publication_style_profile.json"
            )
        if display_overrides is None:
            display_overrides = publication_display_contract.load_display_overrides(
                resolved_paper_root / "display_overrides.json"
            )
        shell_payload = load_json(submission_graphical_abstract_path)
        figure_id = _resolve_figure_catalog_id(
            display_id=str(shell_payload.get("display_id") or ""),
            catalog_id=str(shell_payload.get("catalog_id") or ""),
        )
        render_context = _build_render_context(
            style_profile=style_profile,
            display_overrides=display_overrides,
            display_id=str(shell_payload.get("display_id") or ""),
            template_id=spec.shell_id,
        )
        output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.svg"
        output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.png"
        output_layout_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.layout.json"
        _prepare_python_illustration_output_paths(
            output_png_path=output_png_path,
            output_svg_path=output_svg_path,
            layout_sidecar_path=output_layout_path,
        )
        render_callable = display_pack_runtime.load_python_plugin_callable(
            repo_root=_REPO_ROOT,
            template_id=spec.shell_id,
            paper_root=resolved_paper_root,
        )
        render_result = dict(
            render_callable(
                template_id=spec.shell_id,
                shell_payload=shell_payload,
                payload_path=submission_graphical_abstract_path,
                render_context=render_context,
                output_svg_path=output_svg_path,
                output_png_path=output_png_path,
                output_layout_path=output_layout_path,
            )
            or {}
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
            "pack_id": pack_id,
            "renderer_family": spec.renderer_family,
            "paper_role": str(shell_payload.get("paper_role") or spec.allowed_paper_roles[0]).strip(),
            "input_schema_id": spec.input_schema_id,
            "qc_profile": spec.shell_qc_profile,
            "qc_result": qc_result,
            "title": str(render_result.get("title") or shell_payload.get("title") or "").strip(),
            "caption": str(render_result.get("caption") or shell_payload.get("caption") or "").strip(),
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
    display_pack_lock_path = display_pack_lock.write_display_pack_lock(
        paper_root=resolved_paper_root,
        repo_root=Path(__file__).resolve().parents[3],
    )
    written_files.extend(
        [
            str(resolved_paper_root / "figures" / "figure_catalog.json"),
            str(resolved_paper_root / "tables" / "table_catalog.json"),
            str(display_pack_lock_path),
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
