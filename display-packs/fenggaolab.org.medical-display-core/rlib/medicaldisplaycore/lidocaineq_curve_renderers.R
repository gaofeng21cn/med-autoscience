# LidocaineQ/Figure_Template curve-family baselines.
# MAS adapts payload fields while keeping the reference grammar: square axes,
# dashed clinical reference lines, compact bottom legends, and the shared palette.

lidocaine_curve_dataframe <- function(series_payload, x_name = "x", y_name = "y", label_name = "label") {
  if (!is.list(series_payload) || length(series_payload) < 1) {
    stop("series must contain at least one curve")
  }
  frames <- lapply(seq_along(series_payload), function(index) {
    item <- series_payload[[index]]
    x <- as_numeric_vector(item[[x_name]], sprintf("series[%d].%s", index, x_name))
    y <- as_numeric_vector(item[[y_name]], sprintf("series[%d].%s", index, y_name))
    if (length(x) != length(y)) {
      stop(sprintf("series[%d].%s and series[%d].%s must have the same length", index, x_name, index, y_name))
    }
    data.frame(
      label = rep(lidocaine_non_empty(item[[label_name]], sprintf("Series %d", index)), length(x)),
      x = x,
      y = y,
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, frames)
}

lidocaine_curve_annotation <- function(display_payload, series_payload = display_payload$series) {
  annotation <- lidocaine_non_empty(display_payload$annotation)
  if (nzchar(annotation)) {
    return(annotation)
  }
  if (!is.list(series_payload) || length(series_payload) < 1) {
    return("")
  }
  labels <- vapply(series_payload, function(item) {
    label <- lidocaine_non_empty(item$label)
    item_annotation <- lidocaine_non_empty(item$annotation %||% item$auc_label)
    if (!nzchar(item_annotation)) {
      return("")
    }
    if (nzchar(label) && !grepl(label, item_annotation, fixed = TRUE)) {
      paste(label, item_annotation)
    } else {
      item_annotation
    }
  }, character(1))
  paste(labels[nzchar(labels)], collapse = "\n")
}

lidocaine_reference_dataframe <- function(reference_line) {
  if (is.null(reference_line)) {
    return(NULL)
  }
  data.frame(
    x = as_numeric_vector(reference_line$x, "reference_line.x"),
    y = as_numeric_vector(reference_line$y, "reference_line.y"),
    stringsAsFactors = FALSE
  )
}

lidocaine_curve_subtitle <- function(display_payload, fallback = "") {
  lidocaine_non_empty(display_payload$subtitle %||% display_payload$caption, fallback)
}

plot_lidocaine_roc_curve <- function(display_payload, template_id = "roc_curve_binary") {
  curve_df <- lidocaine_curve_dataframe(display_payload$series)
  reference_df <- lidocaine_reference_dataframe(display_payload$reference_line)
  palette_values <- lidocaine_palette(display_payload, curve_df$label)
  title <- if (identical(template_id, "time_dependent_roc_horizon")) {
    lidocaine_non_empty(display_payload$title, "Time-dependent ROC")
  } else {
    lidocaine_non_empty(display_payload$title, "ROC curve")
  }
  subtitle <- if (identical(template_id, "time_dependent_roc_horizon")) {
    lidocaine_curve_subtitle(display_payload, "AUC by landmark horizon")
  } else {
    lidocaine_curve_subtitle(display_payload, "Binary or horizon-specific discrimination")
  }
  plot <- ggplot(curve_df, aes(x, y, colour = label))
  if (!is.null(reference_df)) {
    plot <- plot + geom_line(
      data = reference_df,
      aes(x = x, y = y),
      inherit.aes = FALSE,
      linetype = "dashed",
      colour = style_color(display_payload, "reference_line", "muted", "#64748B"),
      linewidth = 0.55
    )
  } else {
    plot <- plot + geom_abline(
      slope = 1,
      intercept = 0,
      linetype = "dashed",
      colour = style_color(display_payload, "reference_line", "muted", "#64748B"),
      linewidth = 0.55
    )
  }
  plot <- plot +
    geom_line(linewidth = 0.95) +
    scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, curve_df$label)) +
    coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
    labs(
      title = title,
      subtitle = subtitle,
      x = lidocaine_non_empty(display_payload$x_label, "1 - Specificity"),
      y = lidocaine_non_empty(display_payload$y_label, "Sensitivity")
    ) +
    lidocaine_publication_theme(display_payload)
  annotation <- lidocaine_curve_annotation(display_payload)
  if (nzchar(annotation)) {
    plot <- plot + annotate(
      "text",
      x = 0.98,
      y = 0.13,
      hjust = 1,
      label = annotation,
      lineheight = 0.95,
      size = 3.1,
      colour = style_text_color(display_payload)
    )
  }
  plot
}

plot_lidocaine_pr_curve <- function(display_payload) {
  curve_df <- lidocaine_curve_dataframe(display_payload$series)
  reference_df <- lidocaine_reference_dataframe(display_payload$reference_line)
  palette_values <- lidocaine_palette(display_payload, curve_df$label)
  plot <- ggplot(curve_df, aes(x, y, colour = label))
  if (!is.null(reference_df)) {
    plot <- plot + geom_line(
      data = reference_df,
      aes(x = x, y = y),
      inherit.aes = FALSE,
      linetype = "dashed",
      linewidth = 0.5,
      colour = style_color(display_payload, "reference_line", "muted", "#64748B")
    )
  }
  plot +
    geom_line(linewidth = 0.95) +
    scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, curve_df$label)) +
    coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Precision-recall curve"),
      subtitle = lidocaine_curve_subtitle(display_payload, "For imbalanced binary outcomes"),
      x = lidocaine_non_empty(display_payload$x_label, "Recall"),
      y = lidocaine_non_empty(display_payload$y_label, "Precision")
    ) +
    lidocaine_publication_theme(display_payload)
}

lidocaine_calibration_dataframe <- function(display_payload) {
  points <- display_payload$calibration_summary %||% display_payload$points
  if (is.list(points) && length(points) > 0) {
    return(do.call(rbind, lapply(seq_along(points), function(index) {
      item <- points[[index]]
      data.frame(
        label = lidocaine_non_empty(item$label %||% item$group_label, "Calibration"),
        predicted = lidocaine_numeric(item$predicted %||% item$predicted_risk, NA),
        observed = lidocaine_numeric(item$observed %||% item$observed_risk, NA),
        lower = lidocaine_numeric(item$lower, NA),
        upper = lidocaine_numeric(item$upper, NA),
        stringsAsFactors = FALSE
      )
    })))
  }
  series <- display_payload$series
  if (!is.list(series) || length(series) < 1) {
    stop("calibration payload must contain series, points, or calibration_summary")
  }
  do.call(rbind, lapply(seq_along(series), function(index) {
    item <- series[[index]]
    predicted <- as_numeric_vector(item$x %||% item$predicted, sprintf("series[%d].predicted", index))
    observed <- as_numeric_vector(item$y %||% item$observed, sprintf("series[%d].observed", index))
    if (length(predicted) != length(observed)) {
      stop(sprintf("series[%d] predicted and observed values must have the same length", index))
    }
    lower <- item$lower
    upper <- item$upper
    lower_values <- if (is.list(lower) && length(lower) == length(predicted)) {
      vapply(lower, function(value) lidocaine_numeric(value, NA), numeric(1))
    } else {
      rep(NA_real_, length(predicted))
    }
    upper_values <- if (is.list(upper) && length(upper) == length(predicted)) {
      vapply(upper, function(value) lidocaine_numeric(value, NA), numeric(1))
    } else {
      rep(NA_real_, length(predicted))
    }
    data.frame(
      label = rep(lidocaine_non_empty(item$label, sprintf("Series %d", index)), length(predicted)),
      predicted = predicted,
      observed = observed,
      lower = lower_values,
      upper = upper_values,
      stringsAsFactors = FALSE
    )
  }))
}

plot_lidocaine_calibration_curve <- function(display_payload) {
  calibration_df <- lidocaine_calibration_dataframe(display_payload)
  if (any(!is.finite(calibration_df$predicted)) || any(!is.finite(calibration_df$observed))) {
    stop("calibration predicted and observed values must be finite")
  }
  ribbon_df <- calibration_df[is.finite(calibration_df$lower) & is.finite(calibration_df$upper), , drop = FALSE]
  label_values <- unique(calibration_df$label)
  single_series <- length(label_values) <= 1
  plot <- ggplot(calibration_df, aes(predicted, observed)) +
    geom_abline(
      slope = 1,
      intercept = 0,
      linetype = "dashed",
      linewidth = 0.55,
      colour = style_color(display_payload, "reference_line", "muted", "#64748B")
    )
  if (nrow(ribbon_df) > 0) {
    if (single_series) {
      plot <- plot + geom_ribbon(
        data = ribbon_df,
        aes(ymin = lower, ymax = upper),
        fill = style_color(display_payload, "model_curve", "primary", "#245A6B"),
        colour = NA,
        alpha = 0.12,
        show.legend = FALSE
      )
    } else {
      plot <- plot + geom_ribbon(
        data = ribbon_df,
        aes(ymin = lower, ymax = upper, fill = label),
        colour = NA,
        alpha = 0.12,
        show.legend = FALSE
      )
    }
  }
  if (single_series) {
    plot <- plot +
      geom_line(linewidth = 0.90, colour = style_color(display_payload, "model_curve", "primary", "#245A6B")) +
      geom_point(size = 2.1, colour = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A"))
  } else {
    palette_values <- lidocaine_palette(display_payload, calibration_df$label)
    plot <- plot +
      geom_line(aes(colour = label), linewidth = 0.90) +
      geom_point(aes(colour = label), size = 2.1) +
      scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, calibration_df$label)) +
      scale_fill_manual(values = palette_values, guide = "none")
  }
  plot +
    coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Calibration curve"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Predicted probability vs observed risk"),
      x = lidocaine_non_empty(display_payload$x_label, "Predicted risk"),
      y = lidocaine_non_empty(display_payload$y_label, "Observed risk")
    ) +
    lidocaine_publication_theme(display_payload)
}

plot_lidocaine_decision_curve <- function(display_payload, title_fallback = "Decision curve") {
  curve_df <- lidocaine_curve_dataframe(display_payload$series)
  reference_df <- lidocaine_reference_dataframe(display_payload$reference_line)
  palette_values <- lidocaine_palette(display_payload, curve_df$label)
  window <- display_payload$decision_focus_window %||% display_payload$axis_window %||% list()
  x_limits <- c(lidocaine_numeric(window$xmin, min(curve_df$x, na.rm = TRUE)), lidocaine_numeric(window$xmax, max(curve_df$x, na.rm = TRUE)))
  y_limits <- c(lidocaine_numeric(window$ymin, min(c(curve_df$y, 0), na.rm = TRUE)), lidocaine_numeric(window$ymax, max(c(curve_df$y, 0), na.rm = TRUE)))
  plot <- ggplot(curve_df, aes(x, y, colour = label)) +
    geom_hline(
      yintercept = 0,
      linewidth = 0.45,
      colour = style_color(display_payload, "reference_line", "muted", "#64748B")
    ) +
    geom_line(linewidth = 0.90) +
    scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, curve_df$label)) +
    coord_cartesian(xlim = x_limits, ylim = y_limits) +
    labs(
      title = lidocaine_non_empty(display_payload$title, title_fallback),
      subtitle = lidocaine_curve_subtitle(display_payload, "Net benefit across clinical thresholds"),
      x = lidocaine_non_empty(display_payload$x_label, "Threshold probability"),
      y = lidocaine_non_empty(display_payload$y_label, "Net benefit")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1)
  if (!is.null(reference_df)) {
    plot <- plot + geom_line(
      data = reference_df,
      aes(x = x, y = y),
      inherit.aes = FALSE,
      linetype = "dashed",
      linewidth = 0.45,
      colour = style_color(display_payload, "reference_line", "muted", "#64748B")
    )
  }
  plot
}

plot_lidocaine_multihorizon_calibration <- function(display_payload) {
  panels <- display_payload$panels
  if (is.list(panels) && length(panels) > 0) {
    calibration_df <- do.call(rbind, lapply(seq_along(panels), function(panel_index) {
      panel <- panels[[panel_index]]
      rows <- panel$calibration_summary
      if (!is.list(rows) || length(rows) < 1) {
        stop(sprintf("panels[%d].calibration_summary must contain at least one row", panel_index))
      }
      do.call(rbind, lapply(seq_along(rows), function(row_index) {
        item <- rows[[row_index]]
        data.frame(
          horizon = lidocaine_non_empty(panel$title %||% panel$panel_label, sprintf("Horizon %d", panel_index)),
          predicted = lidocaine_numeric(item$predicted_risk %||% item$predicted, NA),
          observed = lidocaine_numeric(item$observed_risk %||% item$observed, NA),
          stringsAsFactors = FALSE
        )
      }))
    }))
  } else {
    calibration_df <- lidocaine_calibration_dataframe(display_payload)
    calibration_df$horizon <- calibration_df$label
  }
  if (any(!is.finite(calibration_df$predicted)) || any(!is.finite(calibration_df$observed))) {
    stop("multi-horizon calibration predicted and observed values must be finite")
  }
  palette_values <- lidocaine_palette(display_payload, calibration_df$horizon)
  ggplot(calibration_df, aes(predicted, observed, colour = horizon)) +
    geom_abline(
      slope = 1,
      intercept = 0,
      linetype = "dashed",
      colour = style_color(display_payload, "reference_line", "muted", "#64748B"),
      linewidth = 0.50
    ) +
    geom_line(linewidth = 0.82) +
    geom_point(size = 1.8) +
    scale_colour_manual(values = palette_values, guide = publication_legend_guides(display_payload, calibration_df$horizon)) +
    coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Multi-horizon calibration"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Time-to-event predicted risk reliability"),
      x = lidocaine_non_empty(display_payload$x_label, "Predicted risk"),
      y = lidocaine_non_empty(display_payload$y_label, "Observed risk")
    ) +
    lidocaine_publication_theme(display_payload)
}
