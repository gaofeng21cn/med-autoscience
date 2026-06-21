#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(jsonlite)
  library(ggplot2)
  library(dplyr)
  library(grid)
})

`%||%` <- function(left, right) {
  if (is.null(left)) right else left
}

read_render_request <- function(request_path) {
  request <- fromJSON(request_path, simplifyVector = FALSE)
  if (is.null(request$display_payload)) {
    stop("render request must contain display_payload")
  }
  request
}

normalize_template_id <- function(value) {
  template_id <- trimws(as.character(value %||% ""))
  parts <- strsplit(template_id, "::", fixed = TRUE)[[1]]
  parts[[length(parts)]]
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

require_prepared_dependency_environment <- function(request) {
  dependency_environment <- request$dependency_environment %||% list()
  status <- trimws(as.character(dependency_environment$status %||% ""))
  if (!status %in% c("prepared", "gallery_preview")) {
    stop("cohort_flow_figure requires OPL prepared dependency_environment receipt before R/ggconsort render")
  }
  run_context_ref <- trimws(as.character(dependency_environment$run_context_ref %||% ""))
  fingerprint <- trimws(as.character(
    dependency_environment$run_context_fingerprint %||%
      dependency_environment$execution_fingerprint %||%
      ""
  ))
  if (!nzchar(run_context_ref) || !nzchar(fingerprint)) {
    stop("cohort_flow_figure requires OPL dependency run-context ref and fingerprint")
  }
  dependency_environment
}

require_ggconsort <- function() {
  if (!requireNamespace("ggconsort", quietly = TRUE)) {
    stop("cohort_flow_figure requires prepared R package `ggconsort`; renderer does not install packages")
  }
}

required_list <- function(payload, field_name) {
  value <- payload[[field_name]]
  if (!is.list(value) || length(value) < 1) {
    stop(sprintf("cohort_flow_figure payload.%s must contain at least one item", field_name))
  }
  value
}

cohort_step_id <- function(step, index) {
  value <- trimws(as.character(step$step_id %||% step$cohort %||% sprintf("step_%d", index)))
  if (!nzchar(value)) {
    stop(sprintf("cohort_flow_figure steps[%d].step_id must be non-empty", index))
  }
  make.names(value)
}

cohort_step_label <- function(step, index) {
  label <- trimws(as.character(step$label %||% ""))
  n <- suppressWarnings(as.integer(step$n))
  if (!nzchar(label) || is.na(n)) {
    stop(sprintf("cohort_flow_figure steps[%d] requires label and integer n", index))
  }
  sprintf("%s<br>n=%s", wrap_node_label(label, width = 26), format(n, big.mark = ",", scientific = FALSE))
}

cohort_exclusion_label <- function(exclusion, index) {
  label <- trimws(as.character(exclusion$label %||% ""))
  n <- suppressWarnings(as.integer(exclusion$n))
  if (!nzchar(label) || is.na(n)) {
    stop(sprintf("cohort_flow_figure exclusions[%d] requires label and integer n", index))
  }
  sprintf("%s<br>n=%s", wrap_node_label(label, width = 20), format(n, big.mark = ",", scientific = FALSE))
}

wrap_node_label <- function(label, width) {
  lines <- strwrap(label, width = width, simplify = FALSE)[[1]]
  paste(lines, collapse = "<br>")
}

build_ggconsort_plot <- function(payload) {
  require_ggconsort()
  steps <- required_list(payload, "steps")
  exclusions <- payload$exclusions %||% list()
  step_ids <- vapply(seq_along(steps), function(index) cohort_step_id(steps[[index]], index), character(1))
  if (length(unique(step_ids)) != length(step_ids)) {
    stop("cohort_flow_figure step ids must be unique after ggconsort normalization")
  }

  cohort_data <- data.frame(.row_id = seq_len(max(1, length(steps))), stringsAsFactors = FALSE)
  consort <- ggconsort::cohort_start(cohort_data, cohort_step_label(steps[[1]], 1))
  define_args <- setNames(rep(list(quote(.full)), length(step_ids)), step_ids)
  consort <- do.call(ggconsort::cohort_define, c(list(consort), define_args))
  label_args <- list()
  for (index in seq_along(steps)) {
    label_args[[step_ids[[index]]]] <- cohort_step_label(steps[[index]], index)
  }
  consort <- do.call(ggconsort::cohort_label, c(list(consort), label_args))

  y_top <- 90
  y_gap <- if (length(steps) > 1) min(22, max(10, 70 / (length(steps) - 1))) else 0
  diagram <- ggconsort::consort_box_add(consort, step_ids[[1]], 0, y_top, label_args[[step_ids[[1]]]])
  if (length(steps) > 1) {
    for (index in seq(2, length(steps))) {
      y_value <- y_top - (index - 1) * y_gap
      diagram <- ggconsort::consort_box_add(diagram, step_ids[[index]], 0, y_value, label_args[[step_ids[[index]]]])
      diagram <- ggconsort::consort_arrow_add(
        diagram,
        start = step_ids[[index - 1]],
        start_side = "bottom",
        end = step_ids[[index]],
        end_side = "top"
      )
    }
  }

  if (length(exclusions) > 0) {
    for (index in seq_along(exclusions)) {
      exclusion <- exclusions[[index]]
      from_step_raw <- trimws(as.character(exclusion$from_step_id %||% ""))
      from_index <- match(make.names(from_step_raw), step_ids)
      if (is.na(from_index)) {
        stop(sprintf("cohort_flow_figure exclusions[%d].from_step_id does not reference a declared step", index))
      }
      exclusion_id <- make.names(trimws(as.character(exclusion$exclusion_id %||% exclusion$branch_id %||% sprintf("exclusion_%d", index))))
      y_value <- y_top - max(0, from_index - 0.5) * y_gap
      diagram <- ggconsort::consort_box_add(diagram, exclusion_id, 24, y_value, cohort_exclusion_label(exclusion, index))
      diagram <- ggconsort::consort_arrow_add(
        diagram,
        end = exclusion_id,
        end_side = "left",
        start_x = 0,
        start_y = y_value
      )
    }
  }

  ggplot2::ggplot(diagram) +
    ggconsort::geom_consort() +
    ggconsort::theme_consort(margin_h = 8, margin_v = 2) +
    ggplot2::labs(title = trimws(as.character(payload$title %||% "Participant flow"))) +
    ggplot2::theme(plot.title = ggplot2::element_text(face = "bold", size = 11, hjust = 0))
}

sidecar_box <- function(box_id, box_type, x0, y0, x1, y1) {
  list(box_id = box_id, box_type = box_type, x0 = x0, y0 = y0, x1 = x1, y1 = y1)
}

build_layout_sidecar <- function(payload, dependency_environment) {
  steps <- required_list(payload, "steps")
  exclusions <- payload$exclusions %||% list()
  step_ids <- vapply(seq_along(steps), function(index) cohort_step_id(steps[[index]], index), character(1))
  node_height <- 0.105
  y_gap <- if (length(steps) > 1) min(0.19, max(0.12, 0.68 / (length(steps) - 1))) else 0
  y_top <- 0.82
  layout_boxes <- list(sidecar_box("title", "title", 0.05, 0.89, 0.95, 0.96))
  guide_boxes <- list()
  flow_nodes <- list()
  for (index in seq_along(steps)) {
    y_center <- y_top - (index - 1) * y_gap
    box_id <- paste0("participant_step_", step_ids[[index]])
    layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
      box_id,
      "main_step",
      0.20,
      y_center - node_height / 2,
      0.62,
      y_center + node_height / 2
    )
    flow_nodes[[length(flow_nodes) + 1]] <- list(
      box_id = box_id,
      box_type = "main_step",
      line_count = 2L,
      max_line_chars = 44L,
      rendered_height_pt = 74.0,
      rendered_width_pt = 260.0,
      padding_pt = 10.0
    )
    if (index > 1) {
      guide_boxes[[length(guide_boxes) + 1]] <- sidecar_box(
        paste0("flow_spine_", step_ids[[index - 1]], "_to_", step_ids[[index]]),
        "flow_connector",
        0.40,
        y_center + node_height / 2,
        0.42,
        y_center + y_gap - node_height / 2
      )
    }
  }
  if (length(exclusions) > 0) {
    for (index in seq_along(exclusions)) {
      exclusion <- exclusions[[index]]
      exclusion_id <- make.names(trimws(as.character(exclusion$exclusion_id %||% exclusion$branch_id %||% sprintf("exclusion_%d", index))))
      from_index <- match(make.names(trimws(as.character(exclusion$from_step_id %||% ""))), step_ids)
      y_center <- y_top - max(0, from_index - 0.5) * y_gap
      layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
        paste0("participant_exclusion_", exclusion_id),
        "exclusion_box",
        0.64,
        y_center - 0.048,
        0.92,
        y_center + 0.048
      )
      guide_boxes[[length(guide_boxes) + 1]] <- sidecar_box(
        paste0("flow_branch_", exclusion_id),
        "flow_branch_connector",
        0.62,
        y_center - 0.01,
        0.64,
        y_center + 0.01
      )
      flow_nodes[[length(flow_nodes) + 1]] <- list(
        box_id = paste0("participant_exclusion_", exclusion_id),
        box_type = "exclusion_box",
        line_count = 2L,
        max_line_chars = 46L,
        rendered_height_pt = 56.0,
        rendered_width_pt = 180.0,
        padding_pt = 8.0
      )
    }
  }
  list(
    template_id = "cohort_flow_figure",
    device = list(x0 = 0.0, y0 = 0.0, x1 = 1.0, y1 = 1.0),
    layout_boxes = layout_boxes,
    panel_boxes = list(sidecar_box("participant_flow_main", "subfigure_panel", 0.16, 0.08, 0.98, 0.88)),
    guide_boxes = guide_boxes,
    metrics = list(
      layout_mode = "participant_flow",
      reporting_flow_kind = "consort_strobe_participant_flow",
      dependency_profile_ref = "r_ggplot2_ggconsort_reporting_flow_v1",
      mature_dependency_intent = "ggconsort_capable_reporting_flow",
      generated_fallback_renderer = "python_participant_flow",
      uses_ggconsort = TRUE,
      ggconsort_capable_prepared_environment_required = TRUE,
      renderer_family = "r_ggplot2",
      renderer_role = "default",
      opl_dependency_run_context_ref = dependency_environment$run_context_ref %||% "",
      opl_dependency_run_context_fingerprint = dependency_environment$run_context_fingerprint %||% "",
      publication_runtime_receipt = identical(dependency_environment$status %||% "", "prepared"),
      gallery_preview_dependency_context = identical(dependency_environment$status %||% "", "gallery_preview"),
      steps = steps,
      exclusions = exclusions,
      endpoint_inventory = payload$endpoint_inventory %||% list(),
      design_panels = payload$design_panels %||% list(),
      comparison_summary = payload$comparison_summary %||% list(),
      flow_nodes = flow_nodes
    ),
    render_context = payload$render_context %||% list()
  )
}

render_cohort_flow_request <- function(request_path) {
  request <- read_render_request(request_path)
  template_id <- normalize_template_id(request$short_template_id %||% request$template_id)
  if (!identical(template_id, "cohort_flow_figure")) {
    stop(sprintf("render request template `%s` does not match expected template `cohort_flow_figure`", template_id))
  }
  dependency_environment <- require_prepared_dependency_environment(request)
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
  plot <- build_ggconsort_plot(payload)
  layout_sidecar <- build_layout_sidecar(payload, dependency_environment)
  write_json(layout_sidecar, output_layout, auto_unbox = TRUE, pretty = TRUE, null = "null")
  output_width <- as.numeric(Sys.getenv("MAS_DISPLAY_OUTPUT_WIDTH_IN", unset = "7.2"))
  output_height <- as.numeric(Sys.getenv("MAS_DISPLAY_OUTPUT_HEIGHT_IN", unset = "5.0"))
  ggsave(output_png, plot = plot, width = output_width, height = output_height, dpi = 320, units = "in", bg = "white")
  ggsave(output_pdf, plot = plot, width = output_width, height = output_height, units = "in", bg = "white")
  invisible(list(template_id = template_id, output_png_path = output_png, output_pdf_path = output_pdf, layout_sidecar_path = output_layout))
}

args <- commandArgs(trailingOnly = TRUE)
request_path <- Sys.getenv("MAS_DISPLAY_RENDER_REQUEST", unset = "")
if (length(args) == 2 && identical(args[[1]], "--request")) {
  request_path <- args[[2]]
}
if (!nzchar(request_path)) {
  stop("expected --request <request_json> or MAS_DISPLAY_RENDER_REQUEST")
}
render_cohort_flow_request(request_path)
