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
  lines <- strwrap(trimws(as.character(label %||% "")), width = width, simplify = FALSE)[[1]]
  paste(lines, collapse = "\n")
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
    return(paste(strwrap(joined, width = 32, simplify = FALSE)[[1]], collapse = "\n"))
  }
  line_labels <- vapply(lines, cohort_design_line_label, character(1))
  line_labels <- line_labels[nzchar(trimws(line_labels))]
  if (length(line_labels) > 4) {
    line_labels <- c(line_labels[seq_len(4)], sprintf("+%d more", length(line_labels) - 4))
  }
  paste(vapply(line_labels, wrap_plain_label, character(1), width = 28), collapse = "\n")
}

cohort_endpoint_label <- function(endpoint) {
  label <- trimws(as.character(endpoint$label %||% endpoint$endpoint %||% "Endpoint"))
  event_n <- endpoint$n %||% endpoint$event_n
  event_text <- ""
  if (!is.null(event_n)) {
    event_text <- sprintf("Events: %s", format(as.integer(event_n), big.mark = ",", scientific = FALSE))
  }
  detail <- trimws(as.character(endpoint$detail %||% endpoint$status %||% ""))
  cohort_events <- character(0)
  event_match <- regexec("([0-9,]+)\\s+China events?\\s+and\\s+([0-9,]+)\\s+NHANES events?", detail, ignore.case = TRUE)
  event_parts <- regmatches(detail, event_match)[[1]]
  if (length(event_parts) == 3) {
    cohort_events <- sprintf("China %s; NHANES %s", event_parts[[2]], event_parts[[3]])
  } else if (nzchar(detail)) {
    cohort_events <- strwrap(detail, width = 42, simplify = FALSE)[[1]][[1]]
  }
  paste(
    c(
      wrap_plain_label(label, width = 28),
      wrap_plain_label(event_text, width = 28),
      wrap_plain_label(cohort_events, width = 30)
    )[nzchar(c(label, event_text, cohort_events))],
    collapse = "\n"
  )
}

add_context_card <- function(plot, payload, xmin, xmax, ymin, ymax, title, body, role = "flow_secondary") {
  fill <- style_color(payload, paste0(role, "_fill"), "#F4EFE8")
  edge <- style_color(payload, paste0(role, "_edge"), "#7B8794")
  text_colour <- style_color(payload, "flow_body_text", "#4B5563")
  title_colour <- style_color(payload, "flow_title_text", text_colour)
  plot +
    ggplot2::annotate(
      "rect",
      xmin = xmin,
      xmax = xmax,
      ymin = ymin,
      ymax = ymax,
      fill = fill,
      colour = edge,
      linewidth = 0.34
    ) +
    ggplot2::annotate(
      "text",
      x = xmin + 1.6,
      y = ymax - 2.8,
      label = wrap_plain_label(title, width = 24),
      hjust = 0,
      vjust = 1,
      fontface = "bold",
      size = 3.25,
      colour = title_colour,
      lineheight = 0.92
    ) +
    ggplot2::annotate(
      "text",
      x = xmin + 1.6,
      y = ymax - 9.0,
      label = body,
      hjust = 0,
      vjust = 1,
      size = 2.62,
      colour = text_colour,
      lineheight = 0.88
    )
}

cohort_step_plot_label <- function(step, index) {
  label <- trimws(as.character(step$label %||% ""))
  n <- suppressWarnings(as.integer(step$n))
  if (!nzchar(label) || is.na(n)) {
    stop(sprintf("cohort_flow_figure steps[%d] requires label and integer n", index))
  }
  paste(
    c(
      strwrap(label, width = 24, simplify = FALSE)[[1]],
      sprintf("n=%s", format(n, big.mark = ",", scientific = FALSE))
    ),
    collapse = "\n"
  )
}

cohort_step_frame <- function(steps, step_ids) {
  y_top <- 90
  y_gap <- if (length(steps) > 1) min(22, max(14, 70 / (length(steps) - 1))) else 0
  data.frame(
    step_id = step_ids,
    label = vapply(seq_along(steps), function(index) cohort_step_plot_label(steps[[index]], index), character(1)),
    x = rep(4, length(steps)),
    y = y_top - (seq_along(steps) - 1) * y_gap,
    stringsAsFactors = FALSE
  )
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
      x = 26,
      y = step_df$y[[from_index]] - 6,
      stringsAsFactors = FALSE
    )
  }
  do.call(rbind, rows)
}

build_ggconsort_plot <- function(payload) {
  require_ggconsort()
  render_context <- payload$render_context %||% list()
  layout_override <- render_context$layout_override %||% list()
  show_figure_title <- style_bool(layout_override, "show_figure_title", FALSE)
  steps <- required_list(payload, "steps")
  exclusions <- payload$exclusions %||% list()
  endpoint_inventory <- payload$endpoint_inventory %||% list()
  design_panels <- payload$design_panels %||% list()
  step_ids <- vapply(seq_along(steps), function(index) cohort_step_id(steps[[index]], index), character(1))
  if (length(unique(step_ids)) != length(step_ids)) {
    stop("cohort_flow_figure step ids must be unique after ggconsort normalization")
  }

  step_df <- cohort_step_frame(steps, step_ids)
  exclusion_df <- cohort_exclusion_frame(exclusions, step_df, step_ids)
  node_width <- 32
  node_height <- 10
  exclusion_width <- 26
  exclusion_height <- 8
  plot_y_min <- min(52, min(step_df$y - node_height / 2) - 5)
  if (nrow(exclusion_df) > 0) {
    plot_y_min <- min(plot_y_min, min(exclusion_df$y - exclusion_height / 2) - 5)
  }
  connector_colour <- style_color(payload, "flow_connector", "#7B8794")
  node_fill <- style_color(payload, "flow_main_fill", "#FFFFFF")
  node_edge <- style_color(payload, "flow_main_edge", "#7B8794")
  exclusion_fill <- style_color(payload, "flow_exclusion_fill", "#F5ECE8")
  exclusion_edge <- style_color(payload, "flow_exclusion_edge", "#B57F7F")
  text_colour <- style_color(payload, "flow_body_text", "#111827")

  plot <- ggplot2::ggplot() +
    ggplot2::theme_void() +
    ggplot2::coord_cartesian(xlim = c(-18, 78), ylim = c(plot_y_min, 101), clip = "off")
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
          xend = exclusion_df$x[[index]] - exclusion_width / 2 + 1,
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
      size = 3.15,
      colour = text_colour,
      lineheight = 0.9
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
  if (length(endpoint_inventory) > 0) {
    endpoint <- endpoint_inventory[[1]]
    plot <- add_context_card(
      plot,
      payload,
      xmin = 30,
      xmax = 76,
      ymin = 76,
      ymax = 96,
      title = "Endpoint",
      body = cohort_endpoint_label(endpoint),
      role = "flow_context"
    )
  }
  if (length(design_panels) > 0) {
    panel <- design_panels[[1]]
    plot <- add_context_card(
      plot,
      payload,
      xmin = 30,
      xmax = 76,
      ymin = 56,
      ymax = 74,
      title = trimws(as.character(panel$title %||% panel$label %||% "Shared design")),
      body = cohort_design_panel_body(panel),
      role = "flow_secondary"
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

sidecar_box <- function(box_id, box_type, x0, y0, x1, y1) {
  list(
    box_id = box_id,
    box_type = box_type,
    x0 = min(as.numeric(x0), as.numeric(x1)),
    y0 = min(as.numeric(y0), as.numeric(y1)),
    x1 = max(as.numeric(x0), as.numeric(x1)),
    y1 = max(as.numeric(y0), as.numeric(y1))
  )
}

build_layout_sidecar <- function(payload, dependency_environment) {
  render_context <- payload$render_context %||% list()
  layout_override <- render_context$layout_override %||% list()
  show_figure_title <- style_bool(layout_override, "show_figure_title", FALSE)
  steps <- required_list(payload, "steps")
  exclusions <- payload$exclusions %||% list()
  endpoint_inventory <- payload$endpoint_inventory %||% list()
  design_panels <- payload$design_panels %||% list()
  step_ids <- vapply(seq_along(steps), function(index) cohort_step_id(steps[[index]], index), character(1))
  stack_top <- 0.835
  stack_bottom <- 0.08
  stack_span <- stack_top - stack_bottom
  step_count <- length(steps)
  node_height <- min(0.16, stack_span / max(1, step_count + 0.35 * max(0, step_count - 1)))
  node_height <- max(0.075, node_height)
  node_gap <- max(0.024, node_height * 0.35)
  y_gap <- if (step_count > 1) node_height + node_gap else 0
  y_top <- stack_top - node_height / 2
  flow_panel_y0 <- max(0.0, y_top - max(0, step_count - 1) * y_gap - node_height / 2 - 0.02)
  flow_panel_y1 <- min(1.0, y_top + node_height / 2 + 0.02)
  layout_boxes <- list()
  if (show_figure_title) {
    layout_boxes <- list(sidecar_box("title", "title", 0.05, 0.89, 0.95, 0.96))
  }
  guide_boxes <- list()
  flow_nodes <- list()
  for (index in seq_along(steps)) {
    y_center <- y_top - (index - 1) * y_gap
    box_id <- paste0("participant_step_", step_ids[[index]])
    layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
      box_id,
        "main_step",
      0.10,
      y_center - node_height / 2,
      0.40,
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
  if (length(endpoint_inventory) > 0) {
    layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
      "participant_endpoint_summary",
        "summary_panel",
      0.50,
      0.56,
      0.96,
      0.80
    )
    flow_nodes[[length(flow_nodes) + 1]] <- list(
      box_id = "participant_endpoint_summary",
      box_type = "summary_panel",
      line_count = 3L,
      max_line_chars = 30L,
      rendered_height_pt = 96.0,
      rendered_width_pt = 210.0,
      padding_pt = 9.0
    )
  }
  if (length(design_panels) > 0) {
    layout_boxes[[length(layout_boxes) + 1]] <- sidecar_box(
      "participant_design_summary",
        "summary_panel",
      0.50,
      0.26,
      0.96,
      0.52
    )
    flow_nodes[[length(flow_nodes) + 1]] <- list(
      box_id = "participant_design_summary",
      box_type = "summary_panel",
      line_count = 3L,
      max_line_chars = 32L,
      rendered_height_pt = 108.0,
      rendered_width_pt = 210.0,
      padding_pt = 9.0
    )
  }
  list(
    template_id = "cohort_flow_figure",
    device = list(x0 = 0.0, y0 = 0.0, x1 = 1.0, y1 = 1.0),
    layout_boxes = layout_boxes,
    panel_boxes = list(sidecar_box("participant_flow_main", "subfigure_panel", 0.06, flow_panel_y0, 0.98, flow_panel_y1)),
    guide_boxes = guide_boxes,
    metrics = list(
      layout_mode = "participant_flow",
      reporting_flow_kind = "consort_strobe_participant_flow",
      dependency_profile_ref = "r_ggplot2_ggconsort_reporting_flow_v1",
      mature_dependency_intent = "ggconsort_capable_reporting_flow",
      source_renderer = "MAS/ReportingFlow::cohort_flow_figure",
      figure_purpose = "participant_accounting_and_strobe_consort_flow",
      rendered_title_policy = "figure_title_metadata_only_not_drawn_inside_plot",
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
  output_height <- render_device_dimension(payload, "output_height_in", "MAS_DISPLAY_OUTPUT_HEIGHT_IN", 5.8)
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
