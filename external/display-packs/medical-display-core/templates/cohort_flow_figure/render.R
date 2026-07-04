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

render_device_dimension <- function(payload, field_name, env_name, fallback) {
  render_context <- payload$render_context %||% list()
  layout_override <- render_context$layout_override %||% list()
  value <- layout_override[[field_name]]
  if (is.null(value)) {
    value <- Sys.getenv(env_name, unset = "")
  }
  if (is.null(value) || !nzchar(trimws(as.character(value)))) {
    return(as.numeric(fallback))
  }
  numeric_value <- suppressWarnings(as.numeric(value))
  if (!is.finite(numeric_value) || numeric_value <= 0) {
    return(as.numeric(fallback))
  }
  numeric_value
}

style_bool <- function(mapping, field_name, fallback) {
  value <- mapping[[field_name]]
  if (is.null(value)) {
    return(isTRUE(fallback))
  }
  if (is.logical(value)) {
    return(isTRUE(value))
  }
  normalized <- tolower(trimws(as.character(value)))
  if (normalized %in% c("1", "true", "yes", "y", "on")) {
    return(TRUE)
  }
  if (normalized %in% c("0", "false", "no", "n", "off")) {
    return(FALSE)
  }
  isTRUE(fallback)
}

style_color <- function(payload, role, fallback) {
  render_context <- payload$render_context %||% list()
  style_roles <- render_context$style_roles %||% list()
  palette <- render_context$palette %||% list()
  value <- style_roles[[role]] %||% palette[[role]] %||% fallback
  text <- trimws(as.character(value %||% ""))
  if (nzchar(text)) text else fallback
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

wrap_plain_label <- function(label, width) {
  text <- trimws(as.character(label %||% ""))
  if (length(text) < 1 || !nzchar(text[[1]])) {
    return("")
  }
  lines <- strwrap(text[[1]], width = width, simplify = FALSE)[[1]]
  paste(lines, collapse = "\n")
}

clamp_wrapped_lines <- function(text, width, max_lines) {
  lines <- unlist(strwrap(trimws(as.character(text %||% "")), width = width, simplify = FALSE), use.names = FALSE)
  lines <- lines[nzchar(trimws(lines))]
  if (length(lines) <= max_lines) {
    return(paste(lines, collapse = "\n"))
  }
  clamped <- lines[seq_len(max_lines)]
  clamped[[max_lines]] <- paste0(sub("\\s+$", "", clamped[[max_lines]]), " ...")
  paste(clamped, collapse = "\n")
}

wrap_complete_lines <- function(text, width) {
  lines <- unlist(strwrap(trimws(as.character(text %||% "")), width = width, simplify = FALSE), use.names = FALSE)
  lines <- lines[nzchar(trimws(lines))]
  paste(lines, collapse = "\n")
}

join_limited_lines <- function(lines, max_lines) {
  normalized <- unlist(strsplit(paste(lines, collapse = "\n"), "\n", fixed = TRUE), use.names = FALSE)
  normalized <- normalized[nzchar(trimws(normalized))]
  if (length(normalized) <= max_lines) {
    return(paste(normalized, collapse = "\n"))
  }
  pasted <- normalized[seq_len(max_lines)]
  pasted[[max_lines]] <- paste0(sub("\\s+$", "", pasted[[max_lines]]), " ...")
  paste(pasted, collapse = "\n")
}

cohort_design_line_label <- function(item) {
  label <- trimws(as.character(item$label %||% ""))
  detail <- trimws(as.character(item$detail %||% ""))
  if (nzchar(label) && nzchar(detail)) {
    return(sprintf("%s: %s", label, detail))
  }
  if (nzchar(label)) {
    return(label)
  }
  detail
}

cohort_design_panel_label <- function(panel) {
  title <- trimws(as.character(panel$title %||% panel$label %||% "Design"))
  lines <- panel$lines %||% panel$items %||% list()
  line_labels <- vapply(lines, cohort_design_line_label, character(1))
  line_labels <- line_labels[nzchar(trimws(line_labels))]
  if (length(line_labels) > 5) {
    line_labels <- c(line_labels[seq_len(5)], sprintf("+%d more", length(line_labels) - 5))
  }
  body <- paste(vapply(line_labels, wrap_plain_label, character(1), width = 24), collapse = "\n")
  paste(c(title, body), collapse = "\n")
}

cohort_design_panel_body <- function(panel) {
  lines <- panel$lines %||% panel$items %||% list()
  if (length(lines) < 1) {
    return("")
  }
  labels <- vapply(lines, function(item) trimws(as.character(item$label %||% "")), character(1))
  details <- vapply(lines, function(item) trimws(as.character(item$detail %||% "")), character(1))
  labels <- labels[nzchar(labels)]
  if (length(labels) > 0 && !any(nzchar(details))) {
    joined <- paste(labels, collapse = ", ")
    return(clamp_wrapped_lines(joined, width = 30, max_lines = 5))
  }
  line_labels <- vapply(lines, cohort_design_line_label, character(1))
  line_labels <- line_labels[nzchar(trimws(line_labels))]
  if (length(line_labels) > 3) {
    line_labels <- c(line_labels[seq_len(3)], sprintf("+%d more", length(line_labels) - 3))
  }
  join_limited_lines(vapply(line_labels, clamp_wrapped_lines, character(1), width = 28, max_lines = 2), max_lines = 6)
}

cohort_endpoint_label <- function(endpoint) {
  label <- trimws(as.character(endpoint$label %||% endpoint$endpoint %||% "Endpoint"))
  event_n <- endpoint$event_n %||% endpoint$n_events
  count_n <- endpoint$n
  count_text <- ""
  if (!is.null(event_n)) {
    count_text <- sprintf("Events: %s", format(as.integer(event_n), big.mark = ",", scientific = FALSE))
  } else if (!is.null(count_n)) {
    count_text <- sprintf("n=%s", format(as.integer(count_n), big.mark = ",", scientific = FALSE))
  }
  detail <- trimws(as.character(endpoint$detail %||% endpoint$status %||% ""))
  cohort_events <- character(0)
  event_match <- regexec("([0-9,]+)\\s+China events?\\s+and\\s+([0-9,]+)\\s+NHANES events?", detail, ignore.case = TRUE)
  event_parts <- regmatches(detail, event_match)[[1]]
  if (length(event_parts) == 3) {
    cohort_events <- sprintf("China %s; NHANES %s", event_parts[[2]], event_parts[[3]])
  } else if (nzchar(detail)) {
    cohort_events <- clamp_wrapped_lines(detail, width = 32, max_lines = 2)
  }
  paste(
    c(
      clamp_wrapped_lines(label, width = 28, max_lines = 2),
      clamp_wrapped_lines(count_text, width = 28, max_lines = 1),
      cohort_events
    )[nzchar(c(label, count_text, cohort_events))],
    collapse = "\n"
  )
}

cohort_step_plot_label <- function(step, index) {
  label <- trimws(as.character(step$label %||% ""))
  n <- suppressWarnings(as.integer(step$n))
  if (!nzchar(label) || is.na(n)) {
    stop(sprintf("cohort_flow_figure steps[%d] requires label and integer n", index))
  }
  detail <- trimws(as.character(step$detail %||% ""))
  detail_text <- ""
  if (nzchar(detail)) {
    detail_text <- wrap_complete_lines(detail, width = 36)
  }
  lines <- c(
    strwrap(label, width = 24, simplify = FALSE)[[1]],
    sprintf("n=%s", format(n, big.mark = ",", scientific = FALSE)),
    detail_text
  )
  paste(lines[nzchar(trimws(lines))], collapse = "\n")
}

cohort_step_label_line_count <- function(step) {
  label <- trimws(as.character(step$label %||% ""))
  detail <- trimws(as.character(step$detail %||% ""))
  label_lines <- strwrap(label, width = 24, simplify = FALSE)[[1]]
  detail_lines <- character(0)
  if (nzchar(detail)) {
    detail_lines <- strsplit(wrap_complete_lines(detail, width = 36), "\n", fixed = TRUE)[[1]]
    detail_lines <- detail_lines[nzchar(trimws(detail_lines))]
  }
  length(label_lines) + 1L + length(detail_lines)
}

participant_flow_node_height <- function(has_step_details, max_step_line_count) {
  if (!has_step_details) {
    return(9.5)
  }
  min(30.0, max(15.5, as.numeric(max_step_line_count) * 3.4 + 3.2))
}

participant_flow_node_gap <- function(node_height) {
  max(4.2, as.numeric(node_height) * 0.22)
}

participant_flow_layout <- function(count, node_height, node_gap = participant_flow_node_gap(node_height)) {
  if (count < 1) {
    return(list(y = numeric(0), y_min = 0.0, y_max = 100.0, y_span = 100.0))
  }
  if (count == 1) {
    y <- 70.0
  } else {
    y_top <- 96.0 - node_height / 2.0
    y <- y_top - (seq_len(count) - 1) * (node_height + node_gap)
  }
  y_min <- min(0.0, y[[length(y)]] - node_height / 2.0 - 5.0)
  y_max <- max(101.0, y[[1]] + node_height / 2.0 + 5.0)
  list(y = y, y_min = y_min, y_max = y_max, y_span = y_max - y_min)
}

participant_flow_default_height_in <- function(payload, fallback = 5.8) {
  if (identical(cohort_flow_mode(payload), "source_layer_accounting")) {
    return(fallback)
  }
  steps <- required_list(payload, "steps")
  has_step_details <- any(vapply(steps, function(step) nzchar(trimws(as.character(step$detail %||% ""))), logical(1)))
  step_line_counts <- vapply(steps, cohort_step_label_line_count, integer(1))
  max_step_line_count <- max(step_line_counts, 1L)
  node_height <- participant_flow_node_height(has_step_details, max_step_line_count)
  layout <- participant_flow_layout(length(steps), node_height)
  max(fallback, fallback * layout$y_span / 105.0)
}

cohort_step_frame <- function(steps, step_ids, node_height, node_gap = participant_flow_node_gap(node_height)) {
  layout <- participant_flow_layout(length(steps), node_height, node_gap)
  data.frame(
    step_id = step_ids,
    label = vapply(seq_along(steps), function(index) cohort_step_plot_label(steps[[index]], index), character(1)),
    x = rep(4, length(steps)),
    y = layout$y,
    stringsAsFactors = FALSE
  )
}

cohort_flow_mode <- function(payload) {
  mode <- trimws(as.character(payload$flow_mode %||% "participant_flow"))
  if (nzchar(mode)) mode else "participant_flow"
}

cohort_integer <- function(value, field_name) {
  numeric_value <- suppressWarnings(as.integer(value))
  if (is.na(numeric_value)) {
    stop(sprintf("cohort_flow_figure %s must be an integer", field_name))
  }
  numeric_value
}

cohort_count_label <- function(n) {
  format(as.integer(n), big.mark = ",", scientific = FALSE)
}

cohort_denominator_step <- function(payload) {
  denominator_step_id <- trimws(as.character(payload$denominator_step_id %||% ""))
  if (!nzchar(denominator_step_id)) {
    stop("cohort_flow_figure source_layer_accounting requires denominator_step_id")
  }
  steps <- required_list(payload, "steps")
  for (index in seq_along(steps)) {
    step_id <- cohort_step_id(steps[[index]], index)
    if (identical(step_id, make.names(denominator_step_id))) {
      step <- steps[[index]]
      label <- trimws(as.character(step$label %||% ""))
      n <- cohort_integer(step$n, sprintf("steps[%d].n", index))
      if (!nzchar(label)) {
        stop(sprintf("cohort_flow_figure steps[%d].label must be non-empty", index))
      }
      return(list(step_id = step_id, label = label, n = n, detail = trimws(as.character(step$detail %||% ""))))
    }
  }
  stop("cohort_flow_figure denominator_step_id must reference a declared step")
}

normalize_source_layers <- function(payload) {
  source_layers <- payload$source_layers %||% list()
  if (!is.list(source_layers) || length(source_layers) < 1) {
    stop("cohort_flow_figure source_layer_accounting requires non-empty source_layers")
  }
  normalized <- list()
  seen_ids <- character(0)
  for (index in seq_along(source_layers)) {
    layer <- source_layers[[index]]
    layer_id <- trimws(as.character(layer$layer_id %||% layer$step_id %||% sprintf("source_layer_%d", index)))
    label <- trimws(as.character(layer$label %||% ""))
    n <- cohort_integer(layer$n, sprintf("source_layers[%d].n", index))
    if (!nzchar(layer_id) || !nzchar(label)) {
      stop(sprintf("cohort_flow_figure source_layers[%d] requires layer_id, label, and n", index))
    }
    layer_id <- make.names(layer_id)
    if (layer_id %in% seen_ids) {
      stop(sprintf("cohort_flow_figure source_layers[%d].layer_id must be unique", index))
    }
    seen_ids <- c(seen_ids, layer_id)
    normalized[[length(normalized) + 1]] <- list(
      layer_id = layer_id,
      step_id = trimws(as.character(layer$step_id %||% layer_id)),
      label = label,
      detail = trimws(as.character(layer$detail %||% "")),
      n = n
    )
  }
  normalized
}

normalize_subcohort_coverage <- function(payload) {
  coverage_items <- payload$subcohort_coverage %||% list()
  if (!is.list(coverage_items) || length(coverage_items) < 1) {
    stop("cohort_flow_figure source_layer_accounting requires non-empty subcohort_coverage")
  }
  normalized <- list()
  seen_ids <- character(0)
  for (index in seq_along(coverage_items)) {
    item <- coverage_items[[index]]
    coverage_id <- trimws(as.character(item$coverage_id %||% sprintf("coverage_%d", index)))
    label <- trimws(as.character(item$label %||% ""))
    n <- cohort_integer(item$n, sprintf("subcohort_coverage[%d].n", index))
    denominator_n <- item$denominator_n
    if (!is.null(denominator_n)) {
      denominator_n <- cohort_integer(denominator_n, sprintf("subcohort_coverage[%d].denominator_n", index))
    }
    if (!nzchar(coverage_id) || !nzchar(label)) {
      stop(sprintf("cohort_flow_figure subcohort_coverage[%d] requires coverage_id, label, and n", index))
    }
    coverage_id <- make.names(coverage_id)
    if (coverage_id %in% seen_ids) {
      stop(sprintf("cohort_flow_figure subcohort_coverage[%d].coverage_id must be unique", index))
    }
    seen_ids <- c(seen_ids, coverage_id)
    normalized[[length(normalized) + 1]] <- list(
      coverage_id = coverage_id,
      label = label,
      detail = trimws(as.character(item$detail %||% "")),
      n = n,
      denominator_n = denominator_n
    )
  }
  normalized
}

cohort_exclusion_frame <- function(exclusions, step_df, step_ids) {
  if (length(exclusions) < 1) {
    return(data.frame())
  }
  rows <- list()
  for (index in seq_along(exclusions)) {
    exclusion <- exclusions[[index]]
    from_step_raw <- trimws(as.character(exclusion$from_step_id %||% ""))
    from_index <- match(make.names(from_step_raw), step_ids)
    if (is.na(from_index)) {
      stop(sprintf("cohort_flow_figure exclusions[%d].from_step_id does not reference a declared step", index))
    }
    rows[[length(rows) + 1]] <- data.frame(
      exclusion_id = make.names(trimws(as.character(exclusion$exclusion_id %||% exclusion$branch_id %||% sprintf("exclusion_%d", index)))),
      from_step_id = step_ids[[from_index]],
      label = cohort_exclusion_label(exclusion, index),
      x = 34,
      y = step_df$y[[from_index]] - 6,
      stringsAsFactors = FALSE
    )
  }
  do.call(rbind, rows)
}

source_layer_label <- function(layer) {
  paste(
    c(
      strwrap(layer$label, width = 22, simplify = FALSE)[[1]],
      sprintf("n=%s", cohort_count_label(layer$n))
    ),
    collapse = "\n"
  )
}

source_layer_frame <- function(source_layers) {
  count <- length(source_layers)
  x_values <- if (count == 1) 0 else seq(from = -25, to = 25, length.out = count)
  data.frame(
    layer_id = vapply(source_layers, function(layer) layer$layer_id, character(1)),
    label = vapply(source_layers, source_layer_label, character(1)),
    x = x_values,
    y = rep(62, count),
    stringsAsFactors = FALSE
  )
}

coverage_frame <- function(subcohort_coverage) {
  max_n <- max(vapply(subcohort_coverage, function(item) item$n, numeric(1)))
  if (!is.finite(max_n) || max_n <= 0) {
    max_n <- 1
  }
  y_values <- rev(seq(from = 14, to = 38, length.out = length(subcohort_coverage)))
  data.frame(
    coverage_id = vapply(subcohort_coverage, function(item) item$coverage_id, character(1)),
    label = vapply(subcohort_coverage, function(item) item$label, character(1)),
    n = vapply(subcohort_coverage, function(item) item$n, numeric(1)),
    denominator_n = vapply(subcohort_coverage, function(item) item$denominator_n %||% NA_integer_, numeric(1)),
    width = vapply(subcohort_coverage, function(item) item$n, numeric(1)) / max_n * 44,
    y = y_values,
    stringsAsFactors = FALSE
  )
}

build_source_layer_accounting_plot <- function(payload) {
  require_ggconsort()
  render_context <- payload$render_context %||% list()
  layout_override <- render_context$layout_override %||% list()
  show_figure_title <- style_bool(layout_override, "show_figure_title", FALSE)
  denominator <- cohort_denominator_step(payload)
  source_layers <- normalize_source_layers(payload)
  subcohort_coverage <- normalize_subcohort_coverage(payload)
  source_total <- sum(vapply(source_layers, function(layer) layer$n, numeric(1)))
  if (!identical(as.integer(source_total), as.integer(denominator$n))) {
    stop("cohort_flow_figure source_layers n must sum to denominator step n")
  }
  layer_df <- source_layer_frame(source_layers)
  coverage_df <- coverage_frame(subcohort_coverage)

  node_fill <- style_color(payload, "flow_main_fill", "#F8FAFC")
  node_edge <- style_color(payload, "flow_main_edge", "#62717D")
  layer_fill <- style_color(payload, "flow_primary_fill", "#DCEBF0")
  layer_edge <- style_color(payload, "flow_primary_edge", "#245A6B")
  coverage_fill <- style_color(payload, "flow_context_fill", "#E7EEF5")
  coverage_edge <- style_color(payload, "flow_context_edge", "#2F5D8A")
  text_colour <- style_color(payload, "flow_body_text", "#111827")
  muted_text <- style_color(payload, "flow_muted_text", "#4B5563")
  guide_colour <- style_color(payload, "flow_connector", "#7B8794")

  denominator_label <- paste(
    c(
      strwrap(denominator$label, width = 30, simplify = FALSE)[[1]],
      sprintf("n=%s", cohort_count_label(denominator$n))
    ),
    collapse = "\n"
  )

  plot <- ggplot2::ggplot() +
    ggplot2::theme_void() +
    ggplot2::coord_cartesian(xlim = c(-42, 42), ylim = c(0, 100), clip = "off") +
    ggplot2::annotate(
      "text",
      x = -37,
      y = 95,
      label = "Source layers",
      hjust = 0,
      vjust = 1,
      fontface = "bold",
      size = 3.5,
      colour = muted_text
    ) +
    ggplot2::annotate(
      "text",
      x = -37,
      y = 48,
      label = "Analysis coverage",
      hjust = 0,
      vjust = 1,
      fontface = "bold",
      size = 3.5,
      colour = muted_text
    ) +
    ggplot2::annotate(
      "rect",
      xmin = -24,
      xmax = 24,
      ymin = 70,
      ymax = 82,
      fill = node_fill,
      colour = node_edge,
      linewidth = 0.36
    ) +
    ggplot2::annotate(
      "text",
      x = 0,
      y = 76,
      label = denominator_label,
      hjust = 0.5,
      vjust = 0.5,
      size = 3.45,
      colour = text_colour,
      lineheight = 0.9
    )
  for (index in seq_len(nrow(layer_df))) {
    plot <- plot +
      ggplot2::annotate(
        "segment",
        x = layer_df$x[[index]],
        xend = layer_df$x[[index]],
        y = 86,
        yend = 82,
        colour = guide_colour,
        linewidth = 0.28
      ) +
      ggplot2::annotate(
        "segment",
        x = layer_df$x[[index]],
        xend = layer_df$x[[index]] * 0.25,
        y = 86,
        yend = 82,
        colour = guide_colour,
        linewidth = 0.28,
        arrow = grid::arrow(type = "closed", length = grid::unit(0.075, "in"))
      ) +
      ggplot2::annotate(
        "rect",
        xmin = layer_df$x[[index]] - 14,
        xmax = layer_df$x[[index]] + 14,
        ymin = 86,
        ymax = 98,
        fill = layer_fill,
        colour = layer_edge,
        linewidth = 0.34
      ) +
      ggplot2::annotate(
        "text",
        x = layer_df$x[[index]],
        y = 92,
        label = layer_df$label[[index]],
        hjust = 0.5,
        vjust = 0.5,
        size = 3.25,
        colour = text_colour,
        lineheight = 0.88
      )
  }
  for (index in seq_len(nrow(coverage_df))) {
    n_label <- if (is.na(coverage_df$denominator_n[[index]])) {
      sprintf("n=%s", cohort_count_label(coverage_df$n[[index]]))
    } else {
      sprintf("n=%s/%s", cohort_count_label(coverage_df$n[[index]]), cohort_count_label(coverage_df$denominator_n[[index]]))
    }
    center_y <- coverage_df$y[[index]]
    if (index == 1) {
      plot <- plot +
        ggplot2::annotate(
          "segment",
          x = 0,
          xend = 0,
          y = 70,
          yend = center_y + 5.2,
          colour = guide_colour,
          linewidth = 0.28,
          arrow = grid::arrow(type = "closed", length = grid::unit(0.075, "in"))
        )
    } else {
      plot <- plot +
        ggplot2::annotate(
          "segment",
          x = 0,
          xend = 0,
          y = coverage_df$y[[index - 1]] - 4.2,
          yend = center_y + 4.2,
          colour = guide_colour,
          linewidth = 0.24,
          arrow = grid::arrow(type = "closed", length = grid::unit(0.065, "in"))
        )
    }
    plot <- plot +
      ggplot2::annotate(
        "rect",
        xmin = -22,
        xmax = 22,
        ymin = center_y - 5.2,
        ymax = center_y + 5.2,
        fill = coverage_fill,
        colour = coverage_edge,
        linewidth = 0.32
      ) +
      ggplot2::annotate(
        "text",
        x = -19.5,
        y = center_y,
        label = wrap_plain_label(coverage_df$label[[index]], width = 20),
        hjust = 0,
        vjust = 0.5,
        size = 3.15,
        colour = text_colour,
        lineheight = 0.88
      ) +
      ggplot2::annotate(
        "text",
        x = 19.5,
        y = center_y,
        label = n_label,
        hjust = 1,
        vjust = 0.5,
        size = 3.0,
        colour = text_colour,
        lineheight = 0.88
      )
  }
  if (show_figure_title) {
    plot <- plot +
      ggplot2::labs(title = trimws(as.character(payload$title %||% "Cohort source accounting"))) +
      ggplot2::theme(plot.title = ggplot2::element_text(face = "bold", size = 11, hjust = 0))
  } else {
    plot <- plot + ggplot2::theme(plot.title = ggplot2::element_blank())
  }
  plot
}

build_ggconsort_plot <- function(payload) {
  if (identical(cohort_flow_mode(payload), "source_layer_accounting")) {
    return(build_source_layer_accounting_plot(payload))
  }
  require_ggconsort()
  render_context <- payload$render_context %||% list()
  layout_override <- render_context$layout_override %||% list()
  show_figure_title <- style_bool(layout_override, "show_figure_title", FALSE)
  steps <- required_list(payload, "steps")
  exclusions <- payload$exclusions %||% list()
  endpoint_inventory <- payload$endpoint_inventory %||% list()
  design_panels <- payload$design_panels %||% list()
  has_step_details <- any(vapply(steps, function(step) nzchar(trimws(as.character(step$detail %||% ""))), logical(1)))
  step_line_counts <- vapply(steps, cohort_step_label_line_count, integer(1))
  max_step_line_count <- max(step_line_counts, 1L)
  step_ids <- vapply(seq_along(steps), function(index) cohort_step_id(steps[[index]], index), character(1))
  if (length(unique(step_ids)) != length(step_ids)) {
    stop("cohort_flow_figure step ids must be unique after ggconsort normalization")
  }
  node_height <- participant_flow_node_height(has_step_details, max_step_line_count)
  node_gap <- participant_flow_node_gap(node_height)
  plot_layout <- participant_flow_layout(length(steps), node_height, node_gap)
  step_df <- cohort_step_frame(steps, step_ids, node_height, node_gap)
  step_df$x <- 0
  exclusion_df <- cohort_exclusion_frame(exclusions, step_df, step_ids)
  node_width <- if (length(exclusions) > 0) 50 else 68
  exclusion_width <- if (length(exclusions) > 0) 18 else 22
  exclusion_height <- 8
  plot_y_min <- plot_layout$y_min
  plot_y_max <- plot_layout$y_max
  if (nrow(exclusion_df) > 0) {
    plot_y_min <- min(plot_y_min, min(exclusion_df$y - exclusion_height / 2) - 5)
    plot_y_max <- max(plot_y_max, max(exclusion_df$y + exclusion_height / 2) + 5)
  }
  connector_colour <- style_color(payload, "flow_connector", "#7B8794")
  node_fill <- style_color(payload, "flow_main_fill", "#FFFFFF")
  node_edge <- style_color(payload, "flow_main_edge", "#7B8794")
  exclusion_fill <- style_color(payload, "flow_exclusion_fill", "#F5ECE8")
  exclusion_edge <- style_color(payload, "flow_exclusion_edge", "#B57F7F")
  text_colour <- style_color(payload, "flow_body_text", "#111827")

  plot_xlim <- if (length(exclusions) > 0) c(-44, 44) else c(-36, 36)
  plot <- ggplot2::ggplot() +
    ggplot2::theme_void() +
    ggplot2::coord_cartesian(xlim = plot_xlim, ylim = c(plot_y_min, plot_y_max), clip = "off")
  if (nrow(step_df) > 1) {
    for (index in seq_len(nrow(step_df) - 1)) {
      plot <- plot +
        ggplot2::annotate(
          "segment",
          x = step_df$x[[index]],
          xend = step_df$x[[index + 1]],
          y = step_df$y[[index]] - node_height / 2,
          yend = step_df$y[[index + 1]] + node_height / 2 + 1.2,
          colour = connector_colour,
          linewidth = 0.35,
          arrow = grid::arrow(type = "closed", length = grid::unit(0.09, "in"))
        )
    }
  }
  if (nrow(exclusion_df) > 0) {
    for (index in seq_len(nrow(exclusion_df))) {
      from_row <- step_df[step_df$step_id == exclusion_df$from_step_id[[index]], , drop = FALSE]
      plot <- plot +
        ggplot2::annotate(
          "segment",
          x = from_row$x[[1]] + node_width / 2,
          xend = exclusion_df$x[[index]] - exclusion_width / 2,
          y = exclusion_df$y[[index]],
          yend = exclusion_df$y[[index]],
          colour = exclusion_edge,
          linewidth = 0.32,
          arrow = grid::arrow(type = "closed", length = grid::unit(0.08, "in"))
        )
    }
  }
  plot <- plot +
    ggplot2::annotate(
      "rect",
      xmin = step_df$x - node_width / 2,
      xmax = step_df$x + node_width / 2,
      ymin = step_df$y - node_height / 2,
      ymax = step_df$y + node_height / 2,
      fill = node_fill,
      colour = node_edge,
      linewidth = 0.34
    ) +
    ggplot2::annotate(
      "text",
      x = step_df$x,
      y = step_df$y,
      label = step_df$label,
      hjust = 0.5,
      vjust = 0.5,
      size = if (has_step_details && max_step_line_count > 6L) 3.35 else if (has_step_details) 3.55 else 3.65,
      colour = text_colour,
      lineheight = if (has_step_details) 0.88 else 0.9
    )
  if (nrow(exclusion_df) > 0) {
    plot <- plot +
      ggplot2::annotate(
        "rect",
        xmin = exclusion_df$x - exclusion_width / 2,
        xmax = exclusion_df$x + exclusion_width / 2,
        ymin = exclusion_df$y - exclusion_height / 2,
        ymax = exclusion_df$y + exclusion_height / 2,
        fill = exclusion_fill,
        colour = exclusion_edge,
        linewidth = 0.32
      ) +
      ggplot2::annotate(
        "text",
        x = exclusion_df$x,
        y = exclusion_df$y,
        label = exclusion_df$label,
        hjust = 0.5,
        vjust = 0.5,
        size = 2.7,
        colour = text_colour,
        lineheight = 0.88
      )
  }
  if (show_figure_title) {
    plot <- plot +
      ggplot2::labs(title = trimws(as.character(payload$title %||% "Participant flow"))) +
      ggplot2::theme(plot.title = ggplot2::element_text(face = "bold", size = 11, hjust = 0))
  } else {
    plot <- plot + ggplot2::theme(plot.title = ggplot2::element_blank())
  }
  plot
}

sidecar_box <- function(box_id, box_type, x0, y0, x1, y1, panel_id = "") {
  box <- list(
    box_id = box_id,
    box_type = box_type,
    x0 = min(as.numeric(x0), as.numeric(x1)),
    y0 = min(as.numeric(y0), as.numeric(y1)),
    x1 = max(as.numeric(x0), as.numeric(x1)),
    y1 = max(as.numeric(y0), as.numeric(y1))
  )
  panel_id <- trimws(as.character(panel_id %||% ""))
  if (nzchar(panel_id)) {
    box$panel_id <- panel_id
  }
  box
}

declared_panel_ids <- function(payload) {
  panels <- payload$panels %||% list()
  panel_ids <- vapply(panels, function(panel) {
    trimws(as.character(panel$panel_id %||% ""))
  }, character(1))
  panel_ids[nzchar(panel_ids)]
}

source_accounting_panel_id <- function(panel_ids, fallback, position) {
  if (fallback %in% panel_ids) {
    return(fallback)
  }
  if (length(panel_ids) >= position) {
    return(panel_ids[[position]])
  }
  ""
}

build_source_layer_layout_sidecar <- function(payload, dependency_environment) {
  render_context <- payload$render_context %||% list()
  layout_override <- render_context$layout_override %||% list()
  show_figure_title <- style_bool(layout_override, "show_figure_title", FALSE)
  denominator <- cohort_denominator_step(payload)
  source_layers <- normalize_source_layers(payload)
  subcohort_coverage <- normalize_subcohort_coverage(payload)
  panel_ids <- declared_panel_ids(payload)
  panel_a_id <- source_accounting_panel_id(panel_ids, "A", 1)
  panel_b_id <- source_accounting_panel_id(panel_ids, "B", 2)
  rendered_panel_ids <- panel_ids
  source_count <- length(source_layers)
  source_centers <- if (source_count == 1) 0.50 else seq(from = 0.20, to = 0.80, length.out = source_count)
  coverage_count <- length(subcohort_coverage)
  coverage_y <- if (coverage_count == 1) 0.30 else seq(from = 0.38, to = 0.14, length.out = coverage_count)
  layout_boxes <- list()
  if (show_figure_title) {
    layout_boxes <- list(sidecar_box("title", "title", 0.05, 0.94, 0.95, 0.98))
  }
  layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box("source_layer_heading", "section_label", 0.075, 0.905, 0.28, 0.94, panel_id = panel_a_id)
  layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box("analysis_coverage_heading", "section_label", 0.075, 0.355, 0.33, 0.39, panel_id = panel_b_id)
  layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
    paste0("source_denominator_", denominator$step_id),
    "main_step",
    0.32,
    0.67,
    0.68,
    0.79,
    panel_id = panel_a_id
  )
  flow_nodes <- list(list(
    box_id = paste0("source_denominator_", denominator$step_id),
    box_type = "main_step",
    line_count = 2L,
    max_line_chars = 44L,
    rendered_height_pt = 78.0,
    rendered_width_pt = 260.0,
    padding_pt = 9.0
  ))
  guide_boxes <- list()
  for (index in seq_along(source_layers)) {
    layer <- source_layers[[index]]
    x_center <- source_centers[[index]]
    box_id <- paste0("source_layer_", layer$layer_id)
    layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
      box_id,
      "source_layer_box",
      x_center - 0.13,
      0.83,
      x_center + 0.13,
      0.95,
      panel_id = panel_a_id
    )
    guide_boxes[[length(guide_boxes) + 1]] <- sidecar_box(
      paste0("source_layer_link_", layer$layer_id),
      "source_layer_connector",
      min(0.50, x_center),
      0.79,
      max(0.50, x_center),
      0.83,
      panel_id = panel_a_id
    )
    flow_nodes[[length(flow_nodes) + 1]] <- list(
      box_id = box_id,
      box_type = "source_layer_box",
      line_count = 2L,
      max_line_chars = 40L,
      rendered_height_pt = 72.0,
      rendered_width_pt = 170.0,
      padding_pt = 8.0
    )
  }
  for (index in seq_along(subcohort_coverage)) {
    item <- subcohort_coverage[[index]]
    y_center <- coverage_y[[index]]
    layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
      paste0("coverage_bar_", item$coverage_id),
      "coverage_step",
      0.30,
      y_center - 0.052,
      0.70,
      y_center + 0.052,
      panel_id = panel_b_id
    )
    if (index == 1) {
      guide_boxes[[length(guide_boxes) + 1]] <- sidecar_box(
        "denominator_to_coverage",
        "coverage_flow_connector",
        0.50,
        y_center + 0.052,
        0.50,
        0.67,
        panel_id = panel_b_id
      )
    } else {
      guide_boxes[[length(guide_boxes) + 1]] <- sidecar_box(
        paste0("coverage_flow_", subcohort_coverage[[index - 1]]$coverage_id, "_to_", item$coverage_id),
        "coverage_flow_connector",
        0.50,
        y_center + 0.052,
        0.50,
        coverage_y[[index - 1]] - 0.052,
        panel_id = panel_b_id
      )
    }
    flow_nodes[[length(flow_nodes) + 1]] <- list(
      box_id = paste0("coverage_bar_", item$coverage_id),
      box_type = "coverage_step",
      line_count = 2L,
      max_line_chars = 24L,
      rendered_height_pt = 52.0,
      rendered_width_pt = 180.0,
      padding_pt = 6.0
    )
  }
  list(
    template_id = "cohort_flow_figure",
    device = list(x0 = 0.0, y0 = 0.0, x1 = 1.0, y1 = 1.0),
    layout_boxes = layout_boxes,
    panel_boxes = list(
      sidecar_box("subfigure_panel_A", "subfigure_panel", 0.06, 0.49, 0.98, 0.94, panel_id = panel_a_id),
      sidecar_box("subfigure_panel_B", "subfigure_panel", 0.06, 0.08, 0.98, 0.44, panel_id = panel_b_id)
    ),
    guide_boxes = guide_boxes,
    metrics = list(
      layout_mode = "source_layer_accounting",
      layout_generation = "scholarskills_cohort_flow_v2",
      flow_visual_policy = "purpose_first_reporting_flow_no_legacy_card_shell",
      figure_title_policy = "metadata_only_no_drawn_title",
      reporting_flow_kind = "cohort_source_layer_and_subcohort_coverage",
      dependency_profile_ref = "r_ggplot2_ggconsort_reporting_flow_v1",
      mature_dependency_intent = "ggconsort_capable_reporting_flow",
      source_renderer = "MAS/ReportingFlow::cohort_flow_figure",
      figure_purpose = "participant_accounting_and_strobe_source_boundary",
      rendered_title_policy = "figure_title_metadata_only_not_drawn_inside_plot",
      uses_ggconsort = TRUE,
      panel_ids = rendered_panel_ids,
      ggconsort_capable_prepared_environment_required = TRUE,
      renderer_family = "r_ggplot2",
      renderer_role = "default",
      opl_dependency_run_context_ref = dependency_environment$run_context_ref %||% "",
      opl_dependency_run_context_fingerprint = dependency_environment$run_context_fingerprint %||% "",
      publication_runtime_receipt = identical(dependency_environment$status %||% "", "prepared"),
      gallery_preview_dependency_context = identical(dependency_environment$status %||% "", "gallery_preview"),
      denominator_step = denominator,
      source_layers = source_layers,
      subcohort_coverage = subcohort_coverage,
      exported_centers = payload$exported_centers %||% NULL,
      flow_nodes = flow_nodes
    ),
    render_context = payload$render_context %||% list()
  )
}

build_layout_sidecar <- function(payload, dependency_environment) {
  if (identical(cohort_flow_mode(payload), "source_layer_accounting")) {
    return(build_source_layer_layout_sidecar(payload, dependency_environment))
  }
  render_context <- payload$render_context %||% list()
  layout_override <- render_context$layout_override %||% list()
  show_figure_title <- style_bool(layout_override, "show_figure_title", FALSE)
  steps <- required_list(payload, "steps")
  exclusions <- payload$exclusions %||% list()
  endpoint_inventory <- payload$endpoint_inventory %||% list()
  design_panels <- payload$design_panels %||% list()
  has_step_details <- any(vapply(steps, function(step) nzchar(trimws(as.character(step$detail %||% ""))), logical(1)))
  step_line_counts <- vapply(steps, cohort_step_label_line_count, integer(1))
  max_step_line_count <- max(step_line_counts, 1L)
  node_height_units <- participant_flow_node_height(has_step_details, max_step_line_count)
  node_gap_units <- participant_flow_node_gap(node_height_units)
  plot_layout <- participant_flow_layout(length(steps), node_height_units, node_gap_units)
  output_height <- render_device_dimension(
    payload,
    "output_height_in",
    "MAS_DISPLAY_OUTPUT_HEIGHT_IN",
    participant_flow_default_height_in(payload)
  )
  normalize_y <- function(value) {
    (as.numeric(value) - plot_layout$y_min) / plot_layout$y_span
  }
  node_height <- node_height_units / plot_layout$y_span
  node_gap <- node_gap_units / plot_layout$y_span
  panel_ids <- declared_panel_ids(payload)
  rendered_panel_ids <- if (length(panel_ids) == 1) panel_ids else character(0)
  step_ids <- vapply(seq_along(steps), function(index) cohort_step_id(steps[[index]], index), character(1))
  step_count <- length(steps)
  y_gap <- if (step_count > 1) node_height + node_gap else 0
  y_centers <- normalize_y(plot_layout$y)
  flow_panel_y0 <- max(0.0, min(y_centers - node_height / 2.0) - 0.02)
  flow_panel_y1 <- min(1.0, max(y_centers + node_height / 2.0) + 0.02)
  layout_boxes <- list()
  if (show_figure_title) {
    layout_boxes <- list(sidecar_box("title", "title", 0.05, 0.89, 0.95, 0.96))
  }
  guide_boxes <- list()
  flow_nodes <- list()
  has_exclusion_boxes <- length(exclusions) > 0
  step_x0 <- if (has_exclusion_boxes) 0.12 else 0.14
  step_x1 <- if (has_exclusion_boxes) 0.74 else 0.86
  connector_x0 <- 0.50
  connector_x1 <- 0.50
  rendered_width_pt <- if (has_exclusion_boxes) 410.0 else 460.0
  for (index in seq_along(steps)) {
    y_center <- y_centers[[index]]
    box_id <- paste0("participant_step_", step_ids[[index]])
    layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
      box_id,
      "main_step",
      step_x0,
      y_center - node_height / 2,
      step_x1,
      y_center + node_height / 2
    )
    flow_nodes[[length(flow_nodes) + 1]] <- list(
      box_id = box_id,
      box_type = "main_step",
      line_count = as.integer(step_line_counts[[index]]),
      max_line_chars = if (has_step_details) 48L else 44L,
      rendered_height_pt = max(
        if (has_step_details) 94.0 else 74.0,
        node_height_units / plot_layout$y_span * output_height * 72.0
      ),
      rendered_width_pt = rendered_width_pt,
      padding_pt = 10.0,
      detail_truncated = FALSE
    )
    if (index > 1) {
      guide_boxes[[length(guide_boxes) + 1]] <- sidecar_box(
        paste0("flow_spine_", step_ids[[index - 1]], "_to_", step_ids[[index]]),
        "flow_connector",
        connector_x0,
        y_center + node_height / 2,
        connector_x1,
        y_center + y_gap - node_height / 2
      )
    }
  }
  if (length(exclusions) > 0) {
    for (index in seq_along(exclusions)) {
      exclusion <- exclusions[[index]]
      exclusion_id <- make.names(trimws(as.character(exclusion$exclusion_id %||% exclusion$branch_id %||% sprintf("exclusion_%d", index))))
      from_index <- match(make.names(trimws(as.character(exclusion$from_step_id %||% ""))), step_ids)
      if (is.na(from_index)) {
        y_center <- y_centers[[1]]
      } else if (length(y_centers) > from_index) {
        y_center <- (y_centers[[from_index]] + y_centers[[from_index + 1]]) / 2.0
      } else {
        y_center <- y_centers[[from_index]] - (y_gap / 2.0)
      }
      layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
        paste0("participant_exclusion_", exclusion_id),
        "exclusion_box",
        0.78,
        y_center - 0.048,
        0.96,
        y_center + 0.048
      )
      guide_boxes[[length(guide_boxes) + 1]] <- sidecar_box(
        paste0("flow_branch_", exclusion_id),
        "flow_branch_connector",
        0.74,
        y_center - 0.01,
        0.78,
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
    panel_boxes = list(sidecar_box(
      "participant_flow_main",
      "subfigure_panel",
      0.06,
      flow_panel_y0,
      0.98,
      flow_panel_y1,
      panel_id = if (length(rendered_panel_ids) == 1) rendered_panel_ids[[1]] else ""
    )),
    guide_boxes = guide_boxes,
    metrics = list(
      layout_mode = "participant_flow",
      layout_generation = "scholarskills_cohort_flow_v2",
      layout_policy = "text_aware_dynamic_height_no_overlap_v1",
      flow_visual_policy = "purpose_first_reporting_flow_no_legacy_card_shell",
      figure_title_policy = "metadata_only_no_drawn_title",
      reporting_flow_kind = "consort_strobe_participant_flow",
      dependency_profile_ref = "r_ggplot2_ggconsort_reporting_flow_v1",
      mature_dependency_intent = "ggconsort_capable_reporting_flow",
      source_renderer = "MAS/ReportingFlow::cohort_flow_figure",
      figure_purpose = "participant_accounting_and_strobe_consort_flow",
      rendered_title_policy = "figure_title_metadata_only_not_drawn_inside_plot",
      step_detail_render_policy = if (has_step_details) "visible_when_present" else "not_requested",
      step_detail_truncation_policy = "no_ellipsis_truncation_complete_wrapped_text",
      uses_ggconsort = TRUE,
      panel_ids = rendered_panel_ids,
      ggconsort_capable_prepared_environment_required = TRUE,
      renderer_family = "r_ggplot2",
      renderer_role = "default",
      figure_height_inches = output_height,
      participant_node_gap_fraction = node_gap,
      opl_dependency_run_context_ref = dependency_environment$run_context_ref %||% "",
      opl_dependency_run_context_fingerprint = dependency_environment$run_context_fingerprint %||% "",
      publication_runtime_receipt = identical(dependency_environment$status %||% "", "prepared"),
      gallery_preview_dependency_context = identical(dependency_environment$status %||% "", "gallery_preview"),
      steps = steps,
      exclusions = exclusions,
      endpoint_inventory = endpoint_inventory,
      design_panels = design_panels,
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
  output_width <- render_device_dimension(payload, "output_width_in", "MAS_DISPLAY_OUTPUT_WIDTH_IN", 7.2)
  output_height <- render_device_dimension(
    payload,
    "output_height_in",
    "MAS_DISPLAY_OUTPUT_HEIGHT_IN",
    participant_flow_default_height_in(payload)
  )
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
