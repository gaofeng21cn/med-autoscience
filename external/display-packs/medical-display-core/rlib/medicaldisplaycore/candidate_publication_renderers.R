# Publication-focused candidate renderers. Sourced by candidate_renderer.R after generic helpers.

candidate_plot_risk_layering <- function(payload) {
  bars <- c(
    lapply(payload$left_bars %|||% list(), function(item) c(item, list(panel = candidate_non_empty(payload$left_panel_title, "Predicted risk")))),
    lapply(payload$right_bars %|||% list(), function(item) c(item, list(panel = candidate_non_empty(payload$right_panel_title, "Observed risk"))))
  )
  if (length(bars) < 1) {
    return(candidate_plot_bars(payload))
  }
  risk_df <- do.call(rbind, lapply(seq_along(bars), function(index) {
    item <- bars[[index]]
    risk <- candidate_numeric(item$risk %||% item$value %||% item$observed_km_risk_5y %||% item$mean_predicted_risk_5y, 0)
    data.frame(
      panel = candidate_non_empty(item$panel, "Risk"),
      label = candidate_non_empty(item$label %||% item$group_label, sprintf("Band %d", index)),
      risk_percent = if (abs(risk) <= 1.0) risk * 100 else risk,
      cases = as.integer(candidate_numeric(item$cases %||% item$sample_size %||% item$n, 0)),
      events = as.integer(candidate_numeric(item$events %||% item$events_5y, 0)),
      stringsAsFactors = FALSE
    )
  }))
  risk_df$label <- factor(risk_df$label, levels = unique(risk_df$label))
  palette <- candidate_palette(payload)
  ggplot(risk_df, aes(x = label, y = risk_percent)) +
    geom_col(fill = palette$primary, width = 0.58) +
    geom_text(
      aes(label = sprintf("%.0f%%\n%d/%d", risk_percent, events, cases)),
      vjust = -0.24,
      lineheight = 0.9,
      size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.28,
      colour = palette$text
    ) +
    facet_wrap(~panel, nrow = 1) +
    coord_cartesian(ylim = c(0, max(risk_df$risk_percent, na.rm = TRUE) * 1.22)) +
    labs(
      title = candidate_non_empty(payload$title, "Risk layering by score band"),
      x = candidate_non_empty(payload$left_x_label %||% payload$x_label, ""),
      y = candidate_non_empty(payload$y_label, "Outcome risk (%)")
    ) +
    candidate_theme(payload) +
    theme(
      axis.text.x = element_text(angle = 0, hjust = 0.5),
      panel.grid.major.x = element_blank(),
      legend.position = "none"
    )
}

candidate_alteration_state <- function(item, default_state = "Altered") {
  mutation <- trimws(as.character(item$mutation_class %||% ""))
  cnv <- trimws(as.character(item$cnv_state %||% ""))
  if (nzchar(mutation) && nzchar(cnv)) {
    return("Multi-hit")
  }
  if (nzchar(mutation)) {
    normalized <- tolower(mutation)
    if (grepl("trunc|nonsense|frameshift", normalized)) {
      return("Truncating")
    }
    return("Missense")
  }
  if (nzchar(cnv)) {
    normalized <- tolower(cnv)
    if (grepl("amp", normalized)) {
      return("Amplification")
    }
    if (grepl("gain", normalized)) {
      return("Gain")
    }
    if (grepl("del|loss", normalized)) {
      return("Loss")
    }
    return(cnv)
  }
  default_state
}

candidate_discrete_alteration_scale <- function(payload, values, title) {
  palette <- candidate_palette(payload)
  named_values <- c(
    Missense = palette$primary,
    Truncating = style_color(payload, "audit", "audit", "#B64342"),
    Gain = palette$secondary,
    Amplification = style_color(payload, "series_4", "quaternary", "#D99A2B"),
    Loss = palette$heatmap_low,
    Deletion = style_color(payload, "series_5", "violet", "#6F63B6"),
    `Multi-hit` = palette$accent,
    Altered = palette$primary,
    Neutral = "#F4F6F8",
    Derivation = style_color(payload, "series_1", "primary", "#0B4F6C"),
    Validation = style_color(payload, "series_2", "secondary", "#2A9D8F"),
    Primary = style_color(payload, "series_3", "tertiary", "#B84A3A"),
    Metastatic = style_color(payload, "series_4", "quaternary", "#D99A2B")
  )
  present <- unique(as.character(values))
  scale_fill_manual(
    values = named_values[intersect(names(named_values), present)],
    drop = FALSE,
    name = NULL,
    guide = publication_legend_guides(payload, present)
  )
}

candidate_alteration_palette <- function(payload, values) {
  palette <- candidate_palette(payload)
  named_values <- c(
    Missense = palette$primary,
    Truncating = style_color(payload, "audit", "audit", "#B64342"),
    Gain = palette$secondary,
    Amplification = style_color(payload, "series_4", "quaternary", "#D99A2B"),
    Loss = palette$heatmap_low,
    Deletion = style_color(payload, "series_5", "violet", "#6F63B6"),
    `Multi-hit` = palette$accent,
    Altered = palette$primary,
    Neutral = "#F4F6F8",
    Derivation = style_color(payload, "series_1", "primary", "#0B4F6C"),
    Validation = style_color(payload, "series_2", "secondary", "#2A9D8F"),
    Primary = style_color(payload, "series_3", "tertiary", "#B84A3A"),
    Metastatic = style_color(payload, "series_4", "quaternary", "#D99A2B")
  )
  present <- intersect(names(named_values), unique(as.character(values)))
  named_values[present]
}

candidate_annotation_short_label <- function(value) {
  normalized <- trimws(as.character(value %||% ""))
  known <- c(
    Derivation = "D",
    Validation = "V",
    Primary = "P",
    Metastatic = "M"
  )
  if (normalized %in% names(known)) {
    return(known[[normalized]])
  }
  toupper(substr(normalized, 1, 1))
}

candidate_plot_alteration_landscape <- function(payload) {
  genes <- vapply(payload$gene_order %|||% list(), function(item) candidate_non_empty(item$label, ""), character(1))
  samples <- vapply(payload$sample_order %|||% list(), function(item) candidate_non_empty(item$sample_id %||% item$label, ""), character(1))
  records <- payload$alteration_records %|||% list()
  if (length(genes) < 1 || length(samples) < 1 || length(records) < 1) {
    return(candidate_plot_matrix(payload))
  }
  base <- expand.grid(sample_id = samples, gene_label = genes, stringsAsFactors = FALSE)
  record_df <- do.call(rbind, lapply(records, function(item) {
    data.frame(
      sample_id = candidate_non_empty(item$sample_id, ""),
      gene_label = candidate_non_empty(item$gene_label %||% item$gene, ""),
      state = candidate_alteration_state(item),
      stringsAsFactors = FALSE
    )
  }))
  matrix_df <- merge(base, record_df, by = c("sample_id", "gene_label"), all.x = TRUE, sort = FALSE)
  matrix_df$state[is.na(matrix_df$state)] <- "Neutral"
  matrix_df$sample_id <- factor(matrix_df$sample_id, levels = samples)
  matrix_df$gene_label <- factor(matrix_df$gene_label, levels = rev(genes))
  annotation_tracks <- payload$sample_annotations %|||% list()
  annotation_df <- NULL
  if (length(annotation_tracks) > 0) {
    track_rows <- do.call(rbind, lapply(seq_along(annotation_tracks), function(track_index) {
      track <- annotation_tracks[[track_index]]
      values <- track$values %|||% list()
      do.call(rbind, lapply(seq_along(values), function(value_index) {
        item <- values[[value_index]]
        data.frame(
          sample_id = candidate_non_empty(item$sample_id, samples[[min(value_index, length(samples))]]),
          gene_label = candidate_non_empty(track$label %||% track$track_label, sprintf("Track %d", track_index)),
          state = candidate_non_empty(item$value %||% item$label, "Annotation"),
          annotation_label = candidate_annotation_short_label(item$value %||% item$label),
          track_index = track_index,
          stringsAsFactors = FALSE
        )
      }))
    }))
    track_rows$sample_id <- factor(track_rows$sample_id, levels = samples)
    track_rows$gene_label <- factor(track_rows$gene_label, levels = c(rev(genes), unique(track_rows$gene_label)))
    annotation_df <- track_rows
  }
  y_levels <- if (!is.null(annotation_df)) c(rev(genes), unique(as.character(annotation_df$gene_label))) else rev(genes)
  matrix_df$gene_label <- factor(matrix_df$gene_label, levels = y_levels)
  if (!is.null(annotation_df)) {
    annotation_df$gene_label <- factor(annotation_df$gene_label, levels = y_levels)
  }
  palette <- candidate_palette(payload)
  alteration_values <- candidate_alteration_palette(payload, matrix_df$state)
  annotation_values <- if (!is.null(annotation_df)) candidate_alteration_palette(payload, annotation_df$state) else character()
  fill_values <- c(alteration_values, annotation_values[setdiff(names(annotation_values), names(alteration_values))])
  plot <- ggplot() +
    geom_tile(data = matrix_df, aes(x = sample_id, y = gene_label, fill = state), colour = "white", linewidth = 0.42) +
    labs(
      title = candidate_non_empty(payload$title, "Genomic alteration landscape"),
      x = candidate_non_empty(payload$x_label, "Samples"),
      y = candidate_non_empty(payload$y_label, "Genes")
    ) +
    candidate_theme(payload) +
    theme(
      axis.text.x = element_text(angle = 0, hjust = 0.5, vjust = 0.5),
      panel.grid = element_blank(),
      legend.position = "bottom",
      legend.title = element_text(size = style_numeric(style_typography(payload), "legend_size", 6.8), colour = palette$text),
      legend.box = "vertical"
    )
  if (!is.null(annotation_df)) {
    plot <- plot +
      geom_tile(data = annotation_df, aes(x = sample_id, y = gene_label, fill = state), colour = "white", linewidth = 0.42) +
      geom_text(
        data = annotation_df,
        aes(x = sample_id, y = gene_label, label = annotation_label),
        colour = "white",
        size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.34,
        fontface = "bold"
      ) +
      theme(axis.text.y = element_text(size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.92))
  }
  plot +
    scale_fill_manual(
      values = fill_values,
      breaks = names(alteration_values),
      drop = FALSE,
      name = NULL,
      guide = publication_legend_guides(payload, names(alteration_values))
    )
}

candidate_plot_cnv_recurrence <- function(payload) {
  regions <- vapply(payload$region_order %|||% list(), function(item) candidate_non_empty(item$label, ""), character(1))
  samples <- vapply(payload$sample_order %|||% list(), function(item) candidate_non_empty(item$sample_id %||% item$label, ""), character(1))
  records <- payload$cnv_records %|||% list()
  if (length(regions) < 1 || length(samples) < 1 || length(records) < 1) {
    return(candidate_plot_matrix(payload))
  }
  base <- expand.grid(sample_id = samples, region_label = regions, stringsAsFactors = FALSE)
  record_df <- do.call(rbind, lapply(records, function(item) {
    data.frame(
      sample_id = candidate_non_empty(item$sample_id, ""),
      region_label = candidate_non_empty(item$region_label %||% item$region, ""),
      state = candidate_alteration_state(list(cnv_state = item$cnv_state), default_state = "CNV"),
      stringsAsFactors = FALSE
    )
  }))
  matrix_df <- merge(base, record_df, by = c("sample_id", "region_label"), all.x = TRUE, sort = FALSE)
  matrix_df$state[is.na(matrix_df$state)] <- "Neutral"
  matrix_df$sample_id <- factor(matrix_df$sample_id, levels = samples)
  matrix_df$region_label <- factor(matrix_df$region_label, levels = rev(regions))
  ggplot(matrix_df, aes(x = sample_id, y = region_label, fill = state)) +
    geom_tile(colour = "white", linewidth = 0.42) +
    candidate_discrete_alteration_scale(payload, matrix_df$state, candidate_non_empty(payload$cnv_legend_title, "CNV state")) +
    labs(
      title = candidate_non_empty(payload$title, "CNV recurrence summary"),
      x = candidate_non_empty(payload$x_label, "Samples"),
      y = candidate_non_empty(payload$y_label, "Regions")
    ) +
    candidate_theme(payload) +
    theme(
      axis.text.x = element_text(angle = 0, hjust = 0.5, vjust = 0.5),
      panel.grid = element_blank(),
      legend.position = "bottom",
      legend.box = "vertical"
    )
}

candidate_plot_genomic_consequence <- function(payload) {
  points <- payload$consequence_points %|||% payload$points %|||% list()
  if (length(points) < 1) {
    return(candidate_plot_volcano(payload))
  }
  consequence_df <- do.call(rbind, lapply(seq_along(points), function(index) {
    item <- points[[index]]
    data.frame(
      panel = candidate_panel_title(payload, item$panel_id, "Consequence", order_field = "consequence_panel_order"),
      gene = candidate_non_empty(item$gene_label %||% item$feature_label %||% item$label_text, sprintf("Gene %d", index)),
      effect = candidate_numeric(item$effect_value %||% item$x, 0),
      significance = candidate_numeric(item$significance_value %||% item$y, 0),
      class = candidate_non_empty(item$regulation_class, "background"),
      stringsAsFactors = FALSE
    )
  }))
  consequence_df <- consequence_df[order(consequence_df$effect), , drop = FALSE]
  consequence_df$gene <- factor(consequence_df$gene, levels = consequence_df$gene)
  palette <- candidate_palette(payload)
  ggplot(consequence_df, aes(x = effect, y = gene, colour = class)) +
    geom_vline(xintercept = 0, colour = palette$reference, linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.55, linetype = "dashed") +
    geom_segment(aes(x = 0, xend = effect, y = gene, yend = gene), linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.0) * 0.28, alpha = 0.70, show.legend = FALSE) +
    geom_point(aes(size = significance), alpha = 0.88) +
    facet_wrap(~panel, nrow = 1) +
    scale_color_manual(
      values = c(upregulated = palette$volcano_up, downregulated = palette$volcano_down, background = palette$volcano_background),
      guide = publication_legend_guides(payload, consequence_df$class)
    ) +
    scale_size_continuous(
      range = c(2.4, 6.2),
      name = candidate_non_empty(payload$consequence_y_label, "-log10(q)"),
      breaks = continuous_scale_breaks(consequence_df$significance, max_breaks = 3)
    ) +
    labs(
      title = candidate_non_empty(payload$title, "Genomic alteration consequence panel"),
      x = candidate_non_empty(payload$consequence_x_label %||% payload$x_label, "Effect size"),
      y = ""
    ) +
    candidate_theme(payload) +
    guides(size = guide_legend(nrow = 1, byrow = TRUE)) +
    theme(
      legend.box = "vertical",
      panel.grid.major.y = element_line(colour = palette$grid, linewidth = 0.18)
    )
}

candidate_shap_rows <- function(payload) {
  rows <- candidate_items(payload, c("rows", "bars"))
  if (length(rows) < 1 && !is.null(payload$panels)) {
    rows <- unlist(lapply(payload$panels, function(panel) candidate_items(panel, c("rows", "bars"))), recursive = FALSE)
  }
  if (length(rows) < 1) {
    rows <- list(
      list(feature = "Age", value = 0.24, points = list(list(shap_value = -0.12, feature_value = 0.3), list(shap_value = 0.25, feature_value = 0.8))),
      list(feature = "Ki-67", value = 0.18, points = list(list(shap_value = -0.08, feature_value = 0.4), list(shap_value = 0.19, feature_value = 0.7)))
    )
  }
  rows
}

candidate_plot_shap <- function(payload, mode = "beeswarm") {
  rows <- candidate_shap_rows(payload)
  if (identical(mode, "bar")) {
    bar_payload <- list(
      bars = lapply(rows, function(row) list(label = row$feature %||% row$label, value = row$value %||% row$mean_abs_shap)),
      title = payload$title,
      x_label = payload$x_label,
      y_label = payload$y_label,
      render_context = payload$render_context
    )
    return(candidate_plot_bars(bar_payload) + coord_flip())
  }
  frames <- lapply(seq_along(rows), function(row_index) {
    row <- rows[[row_index]]
    points <- row$points %||% list(list(shap_value = row$value %||% row$mean_abs_shap %||% 0, feature_value = 0.5))
    do.call(rbind, lapply(seq_along(points), function(point_index) {
      point <- points[[point_index]]
      data.frame(
        feature = candidate_non_empty(row$feature %||% row$label, sprintf("Feature %d", row_index)),
        shap_value = candidate_numeric(point$shap_value %||% point$value, 0),
        feature_value = candidate_numeric(point$feature_value, point_index),
        stringsAsFactors = FALSE
      )
    }))
  })
  shap_df <- do.call(rbind, frames)
  shap_df$feature <- factor(shap_df$feature, levels = rev(unique(shap_df$feature)))
  palette <- candidate_palette(payload)
  ggplot(shap_df, aes(x = shap_value, y = feature, colour = feature_value)) +
    geom_vline(xintercept = 0, colour = palette$reference, linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.6, linetype = "dashed") +
    geom_point(size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.56, alpha = 0.9, position = position_jitter(height = 0.12, width = 0)) +
    heatmap_colour_scale(payload, shap_df$feature_value, midpoint = median(shap_df$feature_value)) +
    labs(
      title = candidate_non_empty(payload$title, "R/ggplot2 candidate SHAP summary"),
      x = candidate_non_empty(payload$x_label, "SHAP value"),
      y = ""
    ) +
    candidate_theme(payload) +
    theme_publication_colorbar(payload)
}

candidate_plot_shap_dependence <- function(payload) {
  panels <- payload$panels %|||% list()
  if (length(panels) < 1) {
    return(candidate_plot_dot(payload))
  }
  dependence_df <- do.call(rbind, lapply(seq_along(panels), function(panel_index) {
    panel <- panels[[panel_index]]
    points <- panel$points %|||% list()
    if (length(points) < 1) {
      points <- list(list(feature_value = 0, shap_value = 0, interaction_value = 0.5))
    }
    do.call(rbind, lapply(points, function(point) {
      data.frame(
        panel = candidate_non_empty(panel$title %||% panel$feature %||% panel$panel_label, sprintf("Panel %d", panel_index)),
        feature_value = candidate_numeric(point$feature_value, 0),
        shap_value = candidate_numeric(point$shap_value, 0),
        interaction_value = candidate_numeric(point$interaction_value %||% point$feature_value, 0),
        stringsAsFactors = FALSE
      )
    }))
  }))
  palette <- candidate_palette(payload)
  ggplot(dependence_df, aes(x = feature_value, y = shap_value, colour = interaction_value)) +
    geom_hline(yintercept = 0, colour = palette$reference, linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.55, linetype = "dashed") +
    geom_smooth(aes(group = panel), method = "loess", formula = y ~ x, se = FALSE, colour = palette$primary, linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.0) * 0.42) +
    geom_point(size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.58, alpha = 0.88) +
    facet_wrap(~panel, nrow = 1, scales = "free_x") +
    heatmap_colour_scale(payload, dependence_df$interaction_value, name = candidate_non_empty(payload$colorbar_label, "Interaction")) +
    labs(
      title = candidate_non_empty(payload$title, "SHAP dependence panel"),
      x = candidate_non_empty(payload$x_label, "Feature value"),
      y = candidate_non_empty(payload$y_label, "SHAP value")
    ) +
    candidate_theme(payload) +
    theme_publication_colorbar(payload)
}

candidate_plot_shap_waterfall <- function(payload) {
  panels <- payload$panels %|||% list()
  panel <- if (length(panels) > 0) panels[[1]] else payload
  contributions <- panel$contributions %|||% list()
  if (length(contributions) < 1) {
    return(candidate_plot_effect(payload))
  }
  baseline <- candidate_numeric(panel$baseline_value %||% payload$baseline_value, 0)
  running <- baseline
  waterfall_df <- do.call(rbind, lapply(seq_along(contributions), function(index) {
    item <- contributions[[index]]
    contribution <- candidate_numeric(item$shap_value %||% item$value, 0)
    start <- running
    end <- start + contribution
    running <<- end
    data.frame(
      step = index,
      feature = candidate_non_empty(item$feature %||% item$label, sprintf("Feature %d", index)),
      feature_value = candidate_non_empty(item$feature_value_text, ""),
      start = start,
      end = end,
      xmin = min(start, end),
      xmax = max(start, end),
      direction = if (contribution >= 0) "Positive contribution" else "Negative contribution",
      contribution = contribution,
      stringsAsFactors = FALSE
    )
  }))
  waterfall_df$y_index <- rev(seq_len(nrow(waterfall_df)))
  predicted <- candidate_numeric(panel$predicted_value %||% payload$predicted_value, running)
  palette <- candidate_palette(payload)
  x_min <- min(waterfall_df$xmin, baseline, predicted, na.rm = TRUE)
  x_max <- max(waterfall_df$xmax, baseline, predicted, na.rm = TRUE)
  x_span <- max(0.1, x_max - x_min)
  waterfall_df$label_anchor <- waterfall_df$xmax + x_span * 0.035
  ggplot(waterfall_df) +
    geom_vline(xintercept = baseline, colour = palette$reference, linetype = "dotted", linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.56) +
    geom_vline(xintercept = predicted, colour = palette$accent, linetype = "dashed", linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.68) +
    geom_rect(aes(xmin = xmin, xmax = xmax, ymin = y_index - 0.34, ymax = y_index + 0.34, fill = direction), colour = "white", linewidth = 0.3) +
    geom_text(
      aes(x = label_anchor, y = y_index, label = sprintf("%+.2f", contribution)),
      hjust = 0,
      size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.30,
      colour = palette$text
    ) +
    scale_y_continuous(
      breaks = waterfall_df$y_index,
      labels = waterfall_df$feature,
      expand = expansion(mult = c(0.08, 0.15))
    ) +
    scale_fill_manual(
      values = c(`Positive contribution` = palette$tertiary %||% style_color(payload, "series_3", "tertiary", "#B84A3A"), `Negative contribution` = palette$heatmap_low),
      guide = publication_legend_guides(payload, waterfall_df$direction)
    ) +
    coord_cartesian(xlim = c(x_min - x_span * 0.18, x_max + x_span * 0.38), clip = "off") +
    labs(
      title = candidate_non_empty(payload$title, "Local SHAP waterfall explanation"),
      x = candidate_non_empty(payload$x_label, "Model output"),
      y = ""
    ) +
    candidate_theme(payload) +
    theme(plot.margin = margin(10, 40, 10, 12))
}

candidate_plot_coefficient_path <- function(payload) {
  steps <- payload$steps %|||% list()
  rows <- payload$coefficient_rows %|||% list()
  if (length(steps) < 2 || length(rows) < 1) {
    return(candidate_plot_dot(payload))
  }
  step_labels <- vapply(steps, function(item) candidate_non_empty(item$step_label %||% item$label, ""), character(1))
  step_ids <- vapply(steps, function(item) candidate_non_empty(item$step_id %||% item$step_label, ""), character(1))
  path_df <- do.call(rbind, lapply(rows, function(row) {
    points <- row$points %|||% list()
    do.call(rbind, lapply(points, function(point) {
      step_id <- candidate_non_empty(point$step_id, "")
      step_index <- match(step_id, step_ids)
      if (!is.finite(step_index)) {
        step_index <- candidate_numeric(point$step_order, 1)
      }
      data.frame(
        term = candidate_non_empty(row$row_label %||% row$label, "Term"),
        step = factor(step_labels[[max(1, min(length(step_labels), step_index))]], levels = step_labels),
        step_index = as.numeric(step_index),
        estimate = candidate_numeric(point$estimate, 1),
        lower = candidate_numeric(point$lower, candidate_numeric(point$estimate, 1) - 0.1),
        upper = candidate_numeric(point$upper, candidate_numeric(point$estimate, 1) + 0.1),
        stringsAsFactors = FALSE
      )
    }))
  }))
  palette <- candidate_palette(payload)
  ggplot(path_df, aes(x = step, y = estimate, group = term, colour = term)) +
    geom_hline(yintercept = candidate_numeric(payload$reference_value, 1), colour = palette$reference, linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.55, linetype = "dashed") +
    geom_line(linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.0) * 0.38) +
    geom_errorbar(aes(ymin = lower, ymax = upper), width = 0.10, linewidth = style_numeric(style_stroke(payload), "secondary_linewidth", 1.5) * 0.28) +
    geom_point(size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.54) +
    scale_color_manual(values = style_series_palette(payload, unique(path_df$term)), guide = publication_legend_guides(payload, path_df$term)) +
    labs(
      title = candidate_non_empty(payload$title, "Coefficient path across model stages"),
      x = candidate_non_empty(payload$step_legend_title, "Model stage"),
      y = candidate_non_empty(payload$x_label, "Adjusted effect estimate")
    ) +
    candidate_theme(payload) +
    theme(axis.text.x = element_text(angle = 20, hjust = 1))
}

candidate_plot_model_complexity_audit <- function(payload) {
  metric_panels <- payload$metric_panels %|||% list()
  audit_panels <- payload$audit_panels %|||% list()
  rows <- c(
    unlist(lapply(metric_panels, function(panel) {
      lapply(panel$rows %|||% list(), function(row) c(row, list(panel = candidate_non_empty(panel$title, "Metric"), x_label = candidate_non_empty(panel$x_label, "Value"), reference_value = NULL)))
    }), recursive = FALSE),
    unlist(lapply(audit_panels, function(panel) {
      lapply(panel$rows %|||% list(), function(row) c(row, list(panel = candidate_non_empty(panel$title, "Audit"), x_label = candidate_non_empty(panel$x_label, "Value"), reference_value = panel$reference_value %||% NULL)))
    }), recursive = FALSE)
  )
  if (length(rows) < 1) {
    return(candidate_plot_dot(payload))
  }
  audit_df <- do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    data.frame(
      panel = candidate_non_empty(item$panel, "Panel"),
      label = candidate_non_empty(item$label, sprintf("Row %d", index)),
      value = candidate_numeric(item$value, 0),
      reference_value = if (is.null(item$reference_value)) NA_real_ else candidate_numeric(item$reference_value, NA_real_),
      stringsAsFactors = FALSE
    )
  }))
  panel_order <- unlist(payload$panel_order %|||% unique(audit_df$panel))
  audit_df$panel <- factor(audit_df$panel, levels = panel_order)
  audit_df$label <- factor(audit_df$label, levels = rev(unique(audit_df$label)))
  ref_df <- audit_df[is.finite(audit_df$reference_value), c("panel", "reference_value"), drop = FALSE]
  ref_df <- unique(ref_df)
  palette <- candidate_palette(payload)
  plot <- ggplot(audit_df, aes(x = value, y = label)) +
    geom_segment(aes(x = 0, xend = value, y = label, yend = label), colour = palette$primary, linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.0) * 0.28, alpha = 0.72) +
    geom_point(colour = palette$primary, size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.58) +
    facet_wrap(~panel, ncol = 1, scales = "free") +
    labs(
      title = candidate_non_empty(payload$title, "Model complexity audit"),
      x = "Metric value",
      y = ""
    ) +
    candidate_theme(payload) +
    theme(strip.text = element_text(hjust = 0), panel.spacing.y = unit(7, "pt"))
  if (nrow(ref_df) > 0) {
    plot <- plot + geom_vline(
      data = ref_df,
      aes(xintercept = reference_value),
      inherit.aes = FALSE,
      colour = palette$reference,
      linetype = "dashed",
      linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.52
    )
  }
  plot
}

candidate_plot_time_to_event_decision_curve <- function(payload) {
  curve_df <- candidate_curve_df(payload, series_fields = c("series"))
  curve_df$panel <- candidate_non_empty(payload$panel_a_title, "Net benefit")
  treated <- payload$treated_fraction_series %|||% list()
  treated_df <- if (length(treated) > 0) {
    data.frame(
      panel = candidate_non_empty(payload$panel_b_title, "Treated fraction"),
      label = candidate_non_empty(treated$label, "Classified high risk"),
      x = as.numeric(unlist(treated$x %|||% numeric())),
      y = as.numeric(unlist(treated$y %|||% numeric())),
      stringsAsFactors = FALSE
    )
  } else {
    data.frame(panel = character(), label = character(), x = numeric(), y = numeric(), stringsAsFactors = FALSE)
  }
  combined <- rbind(curve_df, treated_df)
  palette <- candidate_palette(payload)
  ggplot(combined, aes(x = x, y = y, colour = label)) +
    geom_line(linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.0) * 0.42) +
    geom_hline(yintercept = 0, colour = palette$reference, linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.50, linetype = "dashed") +
    facet_wrap(~panel, nrow = 1, scales = "free_y") +
    scale_color_manual(values = style_series_palette(payload, unique(combined$label)), guide = publication_legend_guides(payload, combined$label)) +
    labs(
      title = candidate_non_empty(payload$title, "Time-to-event decision curve"),
      x = candidate_non_empty(payload$x_label, "Threshold probability"),
      y = "Net benefit / fraction"
    ) +
    candidate_theme(payload) +
    coord_cartesian(xlim = range(combined$x, na.rm = TRUE))
}

transportability_verdict_label <- function(value) {
  normalized <- trimws(as.character(value %||% ""))
  known <- c(
    stable = "Stable",
    recalibration_required = "Recalibration",
    monitor = "Monitor",
    blocked = "Blocked"
  )
  if (normalized %in% names(known)) {
    return(known[[normalized]])
  }
  candidate_non_empty(normalized, "Review")
}

transportability_wrap_label <- function(value, width = 14) {
  label <- candidate_non_empty(value, "Review")
  paste(strwrap(label, width = width), collapse = "\n")
}

transportability_owner_action_label <- function(value) {
  normalized <- tolower(trimws(as.character(value %||% "")))
  if (grepl("recalibration", normalized)) {
    return("Recalibrate\nbefore use")
  }
  if (grepl("bounded", normalized) || grepl("report", normalized)) {
    return("Report as\nbounded")
  }
  if (grepl("within", normalized) || grepl("accept", normalized) || grepl("reference", normalized)) {
    return("Accept\nreference")
  }
  transportability_wrap_label(value, width = 13)
}

candidate_plot_center_transportability_governance <- function(payload) {
  centers <- payload$centers %|||% list()
  if (length(centers) < 1) {
    return(candidate_plot_generalizability(payload))
  }
  center_df <- do.call(rbind, lapply(seq_along(centers), function(index) {
    item <- centers[[index]]
    data.frame(
      center_label = candidate_non_empty(item$center_label, sprintf("Center %d", index)),
      cohort_role = candidate_non_empty(item$cohort_role, ""),
      support_count = as.integer(candidate_numeric(item$support_count, 0)),
      event_count = as.integer(candidate_numeric(item$event_count, 0)),
      metric_estimate = candidate_numeric(item$metric_estimate, 0),
      metric_lower = candidate_numeric(item$metric_lower, candidate_numeric(item$metric_estimate, 0)),
      metric_upper = candidate_numeric(item$metric_upper, candidate_numeric(item$metric_estimate, 0)),
      max_shift = candidate_numeric(item$max_shift, 0),
      slope = candidate_numeric(item$slope, 1),
      oe_ratio = candidate_numeric(item$oe_ratio, 1),
      verdict = transportability_verdict_label(item$verdict),
      action = candidate_non_empty(item$action, "Review before deployment"),
      stringsAsFactors = FALSE
    )
  }))
  center_df$center_label <- factor(center_df$center_label, levels = rev(center_df$center_label))
  palette <- candidate_palette(payload)
  metric_plot <- ggplot(center_df, aes(x = metric_estimate, y = center_label, colour = verdict)) +
    geom_vline(
      xintercept = candidate_numeric(payload$metric_reference_value, median(center_df$metric_estimate)),
      colour = palette$reference,
      linetype = "dashed",
      linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.55
    ) +
    geom_errorbarh(aes(xmin = metric_lower, xmax = metric_upper), height = 0.13, linewidth = 0.42, alpha = 0.72) +
    geom_point(size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.62) +
    scale_color_manual(values = style_series_palette(payload, unique(center_df$verdict)), guide = publication_legend_guides(payload, center_df$verdict)) +
    scale_x_continuous(limits = c(0.70, 0.79), breaks = c(0.70, 0.73, 0.76, 0.79), labels = c("0.70", "0.73", "0.76", "0.79")) +
    labs(
      title = NULL,
      x = candidate_non_empty(payload$metric_x_label, "C-index"),
      y = ""
    ) +
    candidate_theme(payload) +
    theme(
      legend.position = "bottom",
      panel.grid.major.y = element_line(colour = palette$grid, linewidth = 0.18)
    )

  slope_lower <- candidate_numeric(payload$slope_acceptance_lower, 0.90)
  slope_upper <- candidate_numeric(payload$slope_acceptance_upper, 1.10)
  oe_lower <- candidate_numeric(payload$oe_ratio_acceptance_lower, 0.90)
  oe_upper <- candidate_numeric(payload$oe_ratio_acceptance_upper, 1.10)
  governance_df <- do.call(rbind, lapply(seq_len(nrow(center_df)), function(index) {
    row <- center_df[index, , drop = FALSE]
    slope_ok <- row$slope >= slope_lower && row$slope <= slope_upper
    oe_ok <- row$oe_ratio >= oe_lower && row$oe_ratio <= oe_upper
    calibration_label <- sprintf(
      "Slope %.2f; O/E %.2f",
      row$slope,
      row$oe_ratio
    )
    data.frame(
      center_label = as.character(row$center_label),
      verdict = as.character(row$verdict),
      slope = row$slope,
      oe_ratio = row$oe_ratio,
      calibration = calibration_label,
      calibration_status = if (slope_ok && oe_ok) "Within acceptance" else "Recalibration required",
      action = as.character(row$action),
      stringsAsFactors = FALSE
    )
  }))
  governance_df$center_label <- factor(governance_df$center_label, levels = rev(levels(center_df$center_label)))
  governance_df$calibration <- paste(
    sprintf("Slope %.2f", governance_df$slope),
    sprintf("O/E %.2f", governance_df$oe_ratio),
    governance_df$calibration_status,
    sep = "\n"
  )
  governance_df$action <- vapply(governance_df$action, transportability_owner_action_label, character(1))
  governance_long <- rbind(
    data.frame(center_label = governance_df$center_label, column = "Cohort", text = as.character(governance_df$center_label), verdict = governance_df$verdict, stringsAsFactors = FALSE),
    data.frame(center_label = governance_df$center_label, column = "Calibration check", text = governance_df$calibration, verdict = governance_df$verdict, stringsAsFactors = FALSE),
    data.frame(center_label = governance_df$center_label, column = "Owner action", text = governance_df$action, verdict = governance_df$verdict, stringsAsFactors = FALSE)
  )
  governance_long$column <- factor(governance_long$column, levels = c("Cohort", "Calibration check", "Owner action"))
  governance_long$text <- vapply(governance_long$text, transportability_wrap_label, character(1), width = 16)
  governance_plot <- ggplot(governance_long, aes(x = column, y = center_label, fill = verdict)) +
    geom_tile(colour = "white", linewidth = 0.6, alpha = 0.38) +
    geom_text(
      aes(label = text),
      size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.17,
      lineheight = 0.82,
      colour = palette$text
    ) +
    scale_fill_manual(values = style_series_palette(payload, unique(center_df$verdict)), guide = "none") +
    scale_x_discrete(position = "top") +
    labs(
      title = NULL,
      x = "",
      y = ""
    ) +
    candidate_theme(payload) +
    theme(
      axis.text.x = element_text(face = "bold", margin = margin(t = 4), size = rel(0.76)),
      axis.text.y = element_blank(),
      axis.title = element_blank(),
      axis.ticks = element_blank(),
      axis.line = element_blank(),
      panel.grid = element_blank()
    )

  patchwork::wrap_plots(
    list(metric_plot, governance_plot),
    ncol = 2,
    widths = c(0.92, 1.35)
  ) +
    patchwork::plot_annotation(
      tag_levels = "A",
      theme = theme(
        plot.title = element_blank(),
        plot.subtitle = element_blank(),
        plot.margin = margin(8, 10, 8, 10)
      )
    )
}

candidate_plot_multihorizon_calibration <- function(payload) {
  panels <- payload$panels %|||% list()
  if (length(panels) < 1) {
    return(candidate_plot_curve(payload))
  }
  calibration_df <- do.call(rbind, lapply(seq_along(panels), function(panel_index) {
    panel <- panels[[panel_index]]
    rows <- panel$calibration_summary %|||% list()
    do.call(rbind, lapply(seq_along(rows), function(row_index) {
      row <- rows[[row_index]]
      data.frame(
        panel = candidate_non_empty(panel$title %||% panel$panel_label, sprintf("Horizon %d", panel_index)),
        group = candidate_non_empty(row$group_label, sprintf("Group %d", row_index)),
        predicted = candidate_numeric(row$predicted_risk, 0),
        observed = candidate_numeric(row$observed_risk, 0),
        stringsAsFactors = FALSE
      )
    }))
  }))
  max_axis <- max(calibration_df$predicted, calibration_df$observed, 0.05, na.rm = TRUE) * 1.12
  palette <- candidate_palette(payload)
  ggplot(calibration_df, aes(x = predicted, y = observed)) +
    geom_abline(slope = 1, intercept = 0, colour = palette$reference, linetype = "dashed", linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.55) +
    geom_line(aes(group = panel), colour = palette$primary, linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.0) * 0.36) +
    geom_point(aes(size = group), colour = palette$primary, fill = "white", shape = 21, stroke = 0.65) +
    geom_text(aes(label = group), vjust = -0.72, size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.28, colour = palette$text, show.legend = FALSE) +
    facet_wrap(~panel, nrow = 1) +
    coord_equal(xlim = c(0, max_axis), ylim = c(0, max_axis)) +
    scale_size_discrete(range = c(2.2, 3.6), guide = "none") +
    labs(
      title = candidate_non_empty(payload$title, "Grouped survival calibration"),
      x = candidate_non_empty(payload$x_label, "Predicted risk"),
      y = candidate_non_empty(payload$y_label, "Observed risk")
    ) +
    candidate_theme(payload) +
    theme(panel.grid.minor = element_blank())
}

candidate_plot_generalizability <- function(payload) {
  overview_rows <- payload$overview_rows %|||% list()
  subgroup_rows <- payload$subgroup_rows %|||% list()
  if (length(overview_rows) < 1 && length(subgroup_rows) < 1) {
    return(candidate_plot_effect(payload))
  }
  overview_df <- do.call(rbind, lapply(seq_along(overview_rows), function(index) {
    row <- overview_rows[[index]]
    label <- candidate_non_empty(row$cohort_label %||% row$label, sprintf("Cohort %d", index))
    data.frame(
      panel = candidate_non_empty(payload$overview_panel_title, "External cohorts"),
      label = label,
      series = c(candidate_non_empty(payload$primary_label, "Locked model"), candidate_non_empty(payload$comparator_label, "Comparator")),
      estimate = c(candidate_numeric(row$metric_value, 0), candidate_numeric(row$comparator_metric_value, 0)),
      lower = NA_real_,
      upper = NA_real_,
      stringsAsFactors = FALSE
    )
  }))
  subgroup_df <- do.call(rbind, lapply(seq_along(subgroup_rows), function(index) {
    row <- subgroup_rows[[index]]
    estimate <- candidate_numeric(row$estimate, 0)
    data.frame(
      panel = candidate_non_empty(payload$subgroup_panel_title, "Subgroups"),
      label = candidate_non_empty(row$subgroup_label %||% row$label, sprintf("Subgroup %d", index)),
      series = candidate_non_empty(payload$primary_label, "Locked model"),
      estimate = estimate,
      lower = candidate_numeric(row$lower, estimate),
      upper = candidate_numeric(row$upper, estimate),
      stringsAsFactors = FALSE
    )
  }))
  combined <- rbind(overview_df, subgroup_df)
  combined$label <- factor(combined$label, levels = rev(unique(combined$label)))
  palette <- candidate_palette(payload)
  ggplot(combined, aes(x = estimate, y = label, colour = series)) +
    geom_vline(xintercept = candidate_numeric(payload$subgroup_reference_value, 0.8), colour = palette$reference, linetype = "dashed", linewidth = style_numeric(style_stroke(payload), "reference_linewidth", 1.0) * 0.52) +
    geom_segment(
      data = combined[is.finite(combined$lower) & is.finite(combined$upper), ],
      aes(x = lower, xend = upper, y = label, yend = label),
      linewidth = style_numeric(style_stroke(payload), "primary_linewidth", 2.0) * 0.32,
      show.legend = FALSE
    ) +
    geom_point(size = style_numeric(style_stroke(payload), "marker_size", 4.5) * 0.58) +
    facet_wrap(~panel, nrow = 1, scales = "free_y") +
    scale_color_manual(values = style_series_palette(payload, unique(combined$series)), guide = publication_legend_guides(payload, combined$series)) +
    scale_x_continuous(
      limits = c(0.72, 0.88),
      breaks = c(0.75, 0.80, 0.85),
      labels = c("0.75", "0.80", "0.85")
    ) +
    labs(
      title = candidate_non_empty(payload$title, "Generalizability and subgroup composite"),
      x = candidate_non_empty(payload$overview_x_label %||% payload$subgroup_x_label, "Metric"),
      y = ""
    ) +
    candidate_theme(payload)
}
