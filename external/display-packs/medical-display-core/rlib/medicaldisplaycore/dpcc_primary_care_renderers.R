# Purpose-first renderers for the DPCC primary-care phenotype and treatment-gap paper.

dpcc_gap_rate_fields <- c(
  severe_glycemia_low_intensity_gap_rate = "Severe glycemia\nlow-intensity",
  uncontrolled_glycemia_no_drug_gap_rate = "Uncontrolled glycemia\nno drug",
  hypertension_no_antihypertensive_gap_rate = "Hypertension\nno antihypertensive",
  dyslipidemia_no_lipid_lowering_gap_rate = "Dyslipidemia\nno lipid-lowering"
)

dpcc_gap_patient_fields <- c(
  severe_glycemia_low_intensity_gap_patients = "Severe glycemia\nlow-intensity",
  uncontrolled_glycemia_no_drug_gap_patients = "Uncontrolled glycemia\nno drug",
  hypertension_no_antihypertensive_gap_patients = "Hypertension\nno antihypertensive",
  dyslipidemia_no_lipid_lowering_gap_patients = "Dyslipidemia\nno lipid-lowering"
)

dpcc_rows_df <- function(rows) {
  if (!is.list(rows) || length(rows) < 1) {
    stop("DPCC display payload requires non-empty rows")
  }
  do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    data.frame(
      row_index = index,
      phenotype_label = candidate_non_empty(item$phenotype_label, sprintf("Phenotype %d", index)),
      share_of_index_patients = candidate_numeric(item$share_of_index_patients, 0),
      severe_glycemia_low_intensity_gap_rate = if (is.null(item$severe_glycemia_low_intensity_gap_rate)) NA_real_ else candidate_numeric(item$severe_glycemia_low_intensity_gap_rate, NA_real_),
      uncontrolled_glycemia_no_drug_gap_rate = if (is.null(item$uncontrolled_glycemia_no_drug_gap_rate)) NA_real_ else candidate_numeric(item$uncontrolled_glycemia_no_drug_gap_rate, NA_real_),
      hypertension_no_antihypertensive_gap_rate = if (is.null(item$hypertension_no_antihypertensive_gap_rate)) NA_real_ else candidate_numeric(item$hypertension_no_antihypertensive_gap_rate, NA_real_),
      dyslipidemia_no_lipid_lowering_gap_rate = if (is.null(item$dyslipidemia_no_lipid_lowering_gap_rate)) NA_real_ else candidate_numeric(item$dyslipidemia_no_lipid_lowering_gap_rate, NA_real_),
      stringsAsFactors = FALSE
    )
  }))
}

dpcc_gap_rates_long_df <- function(rows_df) {
  do.call(rbind, lapply(names(dpcc_gap_rate_fields), function(field) {
    data.frame(
      phenotype_label = rows_df$phenotype_label,
      gap_label = unname(dpcc_gap_rate_fields[[field]]),
      gap_rate = rows_df[[field]],
      stringsAsFactors = FALSE
    )
  }))
}

dpcc_treatment_rows_df <- function(rows) {
  if (!is.list(rows) || length(rows) < 1) {
    stop("DPCC treatment-gap display payload requires non-empty rows")
  }
  do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    data.frame(
      row_index = index,
      phenotype_label = candidate_non_empty(item$phenotype_label, sprintf("Phenotype %d", index)),
      index_patients = candidate_numeric(item$index_patients, 0),
      severe_glycemia_low_intensity_gap_patients = candidate_numeric(item$severe_glycemia_low_intensity_gap_patients, 0),
      severe_glycemia_low_intensity_gap_rate = if (is.null(item$severe_glycemia_low_intensity_gap_rate)) NA_real_ else candidate_numeric(item$severe_glycemia_low_intensity_gap_rate, NA_real_),
      uncontrolled_glycemia_no_drug_gap_patients = candidate_numeric(item$uncontrolled_glycemia_no_drug_gap_patients, 0),
      uncontrolled_glycemia_no_drug_gap_rate = if (is.null(item$uncontrolled_glycemia_no_drug_gap_rate)) NA_real_ else candidate_numeric(item$uncontrolled_glycemia_no_drug_gap_rate, NA_real_),
      hypertension_no_antihypertensive_gap_patients = candidate_numeric(item$hypertension_no_antihypertensive_gap_patients, 0),
      hypertension_no_antihypertensive_gap_rate = if (is.null(item$hypertension_no_antihypertensive_gap_rate)) NA_real_ else candidate_numeric(item$hypertension_no_antihypertensive_gap_rate, NA_real_),
      dyslipidemia_no_lipid_lowering_gap_patients = candidate_numeric(item$dyslipidemia_no_lipid_lowering_gap_patients, 0),
      dyslipidemia_no_lipid_lowering_gap_rate = if (is.null(item$dyslipidemia_no_lipid_lowering_gap_rate)) NA_real_ else candidate_numeric(item$dyslipidemia_no_lipid_lowering_gap_rate, NA_real_),
      stringsAsFactors = FALSE
    )
  }))
}

dpcc_treatment_long_df <- function(rows_df) {
  rate_field_map <- c(
    severe_glycemia_low_intensity_gap_patients = "severe_glycemia_low_intensity_gap_rate",
    uncontrolled_glycemia_no_drug_gap_patients = "uncontrolled_glycemia_no_drug_gap_rate",
    hypertension_no_antihypertensive_gap_patients = "hypertension_no_antihypertensive_gap_rate",
    dyslipidemia_no_lipid_lowering_gap_patients = "dyslipidemia_no_lipid_lowering_gap_rate"
  )
  do.call(rbind, lapply(names(dpcc_gap_patient_fields), function(field) {
    rate_field <- rate_field_map[[field]]
    explicit_rate <- if (!is.null(rate_field) && rate_field %in% names(rows_df)) rows_df[[rate_field]] else NA_real_
    gap_percent <- ifelse(
      !is.na(explicit_rate),
      explicit_rate * 100,
      ifelse(rows_df$index_patients > 0, rows_df[[field]] / rows_df$index_patients * 100, 0)
    )
    data.frame(
      phenotype_label = rows_df$phenotype_label,
      gap_field = field,
      gap_label = unname(dpcc_gap_patient_fields[[field]]),
      gap_patients = rows_df[[field]],
      index_patients = rows_df$index_patients,
      gap_percent = gap_percent,
      stringsAsFactors = FALSE
    )
  }))
}

dpcc_source_renderer <- function(template_id) {
  switch(
    template_id,
    phenotype_gap_structure_figure = "MAS/DPCC::phenotype_gap_structure_figure",
    site_held_out_stability_figure = "MAS/DPCC::site_held_out_stability_figure",
    treatment_gap_alignment_figure = "MAS/DPCC::treatment_gap_alignment_figure",
    sprintf("MAS/DPCC::%s", template_id)
  )
}

dpcc_label_wrap <- function(values, width = 22) {
  vapply(values, function(value) paste(strwrap(as.character(value), width = width), collapse = "\n"), character(1))
}

dpcc_plot_phenotype_gap_structure <- function(payload) {
  rows_df <- dpcc_rows_df(payload$rows)
  rows_df$phenotype_label <- factor(rows_df$phenotype_label, levels = rev(rows_df$phenotype_label))
  heat_df <- dpcc_gap_rates_long_df(rows_df)
  heat_df$phenotype_label <- factor(heat_df$phenotype_label, levels = levels(rows_df$phenotype_label))
  heat_df$gap_label <- factor(heat_df$gap_label, levels = unname(dpcc_gap_rate_fields))
  heat_df$label <- ifelse(is.na(heat_df$gap_rate), "N/A", sprintf("%.0f%%", heat_df$gap_rate * 100))
  palette <- candidate_palette(payload)
  composition_plot <- ggplot(rows_df, aes(x = share_of_index_patients * 100, y = phenotype_label)) +
    geom_col(fill = palette$primary, width = 0.62) +
    geom_text(
      aes(label = sprintf("%.1f%%", share_of_index_patients * 100)),
      hjust = -0.12,
      size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.26,
      colour = palette$text
    ) +
    coord_cartesian(xlim = c(0, max(rows_df$share_of_index_patients * 100, na.rm = TRUE) * 1.20), clip = "off") +
    labs(
      title = candidate_non_empty(payload$composition_panel_title, "Phenotype share"),
      x = "Share of index cohort (%)",
      y = ""
    ) +
    candidate_theme(payload) +
    theme(axis.text.y = element_text(size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.82))
  heat_plot <- ggplot(heat_df, aes(x = gap_label, y = phenotype_label, fill = gap_rate)) +
    geom_tile(colour = "white", linewidth = 0.45) +
    geom_text(aes(label = label), size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.24, colour = palette$text) +
    scale_fill_gradient(
      low = style_color(payload, "heatmap_seq_low", "heatmap_seq_low", "#F4F8FA"),
      high = style_color(payload, "heatmap_seq_high", "heatmap_seq_high", "#0B4F6C"),
      limits = c(0, 1),
      na.value = "#ECEFF3",
      labels = function(x) sprintf("%.0f%%", x * 100),
      name = candidate_non_empty(payload$heatmap_scale_label, "Gap rate")
    ) +
    labs(
      title = candidate_non_empty(payload$heatmap_panel_title, "Treatment-gap pattern"),
      x = "",
      y = ""
    ) +
    candidate_theme(payload) +
    theme_publication_colorbar(payload) +
    theme(
      axis.text.x = element_text(angle = 28, hjust = 1, vjust = 1),
      axis.text.y = element_blank(),
      axis.ticks.y = element_blank(),
      legend.position = "right"
    )
  patchwork::wrap_plots(list(composition_plot, heat_plot), ncol = 2, widths = c(0.95, 1.25))
}

dpcc_transition_rows_df <- function(rows) {
  if (!is.list(rows) || length(rows) < 1) {
    stop("DPCC transition display payload requires non-empty transition_rows")
  }
  do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    data.frame(
      source_phenotype_label = candidate_non_empty(item$source_phenotype_label, sprintf("Source %d", index)),
      target_phenotype_label = candidate_non_empty(item$target_phenotype_label, sprintf("Target %d", index)),
      patient_count = candidate_numeric(item$patient_count, 0),
      share_of_transition_patients = candidate_numeric(item$share_of_transition_patients, 0),
      stringsAsFactors = FALSE
    )
  }))
}

dpcc_site_fold_rows_df <- function(rows) {
  if (!is.list(rows) || length(rows) < 1) {
    stop("DPCC transition display payload requires non-empty site_fold_rows")
  }
  do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    data.frame(
      fold_id = candidate_non_empty(item$fold_id, sprintf("Site fold %d", index)),
      index_patients = candidate_numeric(item$index_patients, 0),
      share_of_index_patients = candidate_numeric(item$share_of_index_patients, 0),
      stringsAsFactors = FALSE
    )
  }))
}

dpcc_plot_transition_site_support <- function(payload) {
  transition_df <- dpcc_transition_rows_df(payload$transition_rows)
  source_levels <- unique(transition_df$source_phenotype_label)
  target_levels <- unique(transition_df$target_phenotype_label)
  transition_df$source_phenotype_label <- factor(transition_df$source_phenotype_label, levels = rev(source_levels))
  transition_df$target_phenotype_label <- factor(transition_df$target_phenotype_label, levels = target_levels)
  transition_df$label <- ifelse(
    transition_df$share_of_transition_patients >= 0.04,
    sprintf("%.1f%%", transition_df$share_of_transition_patients * 100),
    ""
  )
  site_df <- dpcc_site_fold_rows_df(payload$site_fold_rows)
  site_df$fold_id <- factor(site_df$fold_id, levels = site_df$fold_id)
  palette <- candidate_palette(payload)
  transition_plot <- ggplot(transition_df, aes(x = target_phenotype_label, y = source_phenotype_label, fill = share_of_transition_patients)) +
    geom_tile(colour = "white", linewidth = 0.45) +
    geom_text(aes(label = label), size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.24, colour = palette$text) +
    scale_fill_gradient(
      low = style_color(payload, "heatmap_seq_low", "heatmap_seq_low", "#F4F8FA"),
      high = style_color(payload, "heatmap_seq_high", "heatmap_seq_high", "#0B4F6C"),
      labels = function(x) sprintf("%.0f%%", x * 100),
      name = candidate_non_empty(payload$heatmap_scale_label, "Transition share")
    ) +
    labs(
      title = candidate_non_empty(payload$transition_panel_title, "Phenotype transition support"),
      x = "Follow-up phenotype",
      y = "Index phenotype"
    ) +
    candidate_theme(payload) +
    theme_publication_colorbar(payload) +
    theme(
      axis.text.x = element_text(angle = 35, hjust = 1, vjust = 1, size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.70),
      axis.text.y = element_text(size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.70),
      legend.position = "right"
    )
  site_plot <- ggplot(site_df, aes(x = share_of_index_patients * 100, y = fold_id)) +
    geom_col(fill = palette$secondary, width = 0.58) +
    geom_text(
      aes(label = sprintf("%.1f%%", share_of_index_patients * 100)),
      hjust = -0.12,
      size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.27,
      colour = palette$text
    ) +
    coord_cartesian(xlim = c(0, max(site_df$share_of_index_patients * 100, na.rm = TRUE) * 1.18), clip = "off") +
    labs(
      title = candidate_non_empty(payload$coverage_panel_title, "Site-held-out support"),
      x = "Share of index patients (%)",
      y = ""
    ) +
    candidate_theme(payload) +
    theme(panel.grid.major.y = element_blank())
  patchwork::wrap_plots(list(transition_plot, site_plot), ncol = 2, widths = c(1.50, 0.82))
}

dpcc_plot_treatment_gap_alignment <- function(payload) {
  rows_df <- dpcc_treatment_rows_df(payload$rows)
  long_df <- dpcc_treatment_long_df(rows_df)
  long_df$phenotype_label_wrapped <- dpcc_label_wrap(long_df$phenotype_label, width = 22)
  long_df$phenotype_label_wrapped <- factor(long_df$phenotype_label_wrapped, levels = rev(unique(long_df$phenotype_label_wrapped)))
  long_df$gap_label <- factor(long_df$gap_label, levels = unname(dpcc_gap_patient_fields))
  palette <- candidate_palette(payload)
  ggplot(long_df, aes(x = gap_percent, y = phenotype_label_wrapped)) +
    geom_col(fill = palette$primary, width = 0.62) +
    geom_text(
      aes(label = ifelse(
        gap_patients > 0,
        sprintf(
          "%.1f%% (n=%s)",
          gap_percent,
          format(round(gap_patients), big.mark = ",", scientific = FALSE)
        ),
        "0"
      )),
      hjust = -0.08,
      size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.20,
      colour = palette$text
    ) +
    facet_wrap(~gap_label, ncol = 2, scales = "fixed") +
    coord_cartesian(xlim = c(0, max(1, max(long_df$gap_percent, na.rm = TRUE) * 1.55)), clip = "off") +
    labs(
      title = NULL,
      x = "Recorded review signal (% of panel denominator)",
      y = candidate_non_empty(payload$y_label, "DPCC phenotype")
    ) +
    candidate_theme(payload) +
    theme(
      axis.text.y = element_text(size = style_numeric(style_typography(payload), "tick_size", 10.0) * 0.76),
      strip.text = element_text(size = style_numeric(style_typography(payload), "panel_label_size", 11.0) * 0.82, face = "bold"),
      panel.grid.major.y = element_blank()
    )
}

dpcc_metric_rows <- function(rows) {
  lapply(rows %|||% list(), function(item) {
    as.list(item)
  })
}

dpcc_layout_override <- function(template_id, display_payload) {
  if (identical(template_id, "phenotype_gap_structure_figure")) {
    panels <- list(
      candidate_box("composition_panel", "composition_panel", 0.08, 0.18, 0.43, 0.84),
      candidate_box("gap_heatmap_panel", "gap_heatmap_panel", 0.54, 0.18, 0.84, 0.84)
    )
    return(list(
      layout_boxes = list(
        candidate_box("panel_label_A", "panel_label", 0.07, 0.10, 0.10, 0.14),
        candidate_box("panel_label_B", "panel_label", 0.53, 0.10, 0.56, 0.14),
        candidate_box("composition_title", "subplot_title", 0.14, 0.10, 0.38, 0.14),
        candidate_box("gap_title", "subplot_title", 0.60, 0.10, 0.82, 0.14),
        candidate_box("composition_x_axis_title", "x_axis_title", 0.18, 0.90, 0.34, 0.94),
        candidate_box("gap_x_axis_title", "x_axis_title", 0.64, 0.90, 0.80, 0.94),
        candidate_box("colorbar_title", "colorbar_title", 0.87, 0.18, 0.95, 0.22)
      ),
      panel_boxes = panels,
      guide_boxes = list(candidate_box("colorbar", "colorbar", 0.88, 0.26, 0.94, 0.80)),
      metrics = list(
        source_renderer = dpcc_source_renderer(template_id),
        figure_purpose = "phenotype_composition_plus_treatment_gap_matrix",
        rendered_title_policy = "figure_title_metadata_only_not_drawn_inside_plot",
        rows = dpcc_metric_rows(display_payload$rows),
        gap_labels = unname(dpcc_gap_rate_fields)
      )
    ))
  }
  if (identical(template_id, "site_held_out_stability_figure")) {
    return(list(
      layout_boxes = list(
        candidate_box("panel_label_A", "panel_label", 0.07, 0.10, 0.10, 0.14),
        candidate_box("panel_label_B", "panel_label", 0.58, 0.10, 0.61, 0.14),
        candidate_box("transition_title", "subplot_title", 0.16, 0.10, 0.42, 0.14),
        candidate_box("site_title", "subplot_title", 0.66, 0.10, 0.90, 0.14),
        candidate_box("transition_x_axis_title", "x_axis_title", 0.20, 0.90, 0.42, 0.94),
        candidate_box("transition_y_axis_title", "y_axis_title", 0.02, 0.36, 0.06, 0.62),
        candidate_box("site_x_axis_title", "x_axis_title", 0.66, 0.90, 0.84, 0.94),
        candidate_box("site_y_axis_title", "y_axis_title", 0.50, 0.36, 0.54, 0.62),
        candidate_box("colorbar_title", "colorbar_title", 0.90, 0.18, 0.97, 0.22)
      ),
      panel_boxes = list(
        candidate_box("transition_heatmap_panel", "transition_heatmap_panel", 0.09, 0.18, 0.49, 0.84),
        candidate_box("site_support_panel", "site_support_panel", 0.60, 0.18, 0.86, 0.84)
      ),
      guide_boxes = list(candidate_box("colorbar", "colorbar", 0.91, 0.26, 0.96, 0.80)),
      metrics = list(
        source_renderer = dpcc_source_renderer(template_id),
        figure_purpose = "phenotype_transition_stability_plus_site_held_out_support",
        rendered_title_policy = "figure_title_metadata_only_not_drawn_inside_plot",
        transition_cell_label_policy = "major_share_percent_only_no_counts",
        site_support_label_policy = "percent_only_counts_remain_in_table",
        transition_rows = dpcc_metric_rows(display_payload$transition_rows),
        site_fold_rows = dpcc_metric_rows(display_payload$site_fold_rows),
        visit_coverage = display_payload$visit_coverage %||% NULL,
        eligible_site_count = display_payload$eligible_site_count %||% NULL
      )
    ))
  }
  if (identical(template_id, "treatment_gap_alignment_figure")) {
    return(list(
      layout_boxes = list(
        candidate_box("panel_label_A", "panel_label", 0.07, 0.10, 0.10, 0.14),
        candidate_box("panel_label_B", "panel_label", 0.52, 0.10, 0.55, 0.14),
        candidate_box("panel_label_C", "panel_label", 0.07, 0.50, 0.10, 0.54),
        candidate_box("panel_label_D", "panel_label", 0.52, 0.50, 0.55, 0.54),
        candidate_box("gap_title_A", "subplot_title", 0.14, 0.10, 0.38, 0.14),
        candidate_box("gap_title_B", "subplot_title", 0.58, 0.10, 0.84, 0.14),
        candidate_box("gap_title_C", "subplot_title", 0.14, 0.50, 0.38, 0.54),
        candidate_box("gap_title_D", "subplot_title", 0.58, 0.50, 0.84, 0.54),
        candidate_box("shared_y_axis_title", "y_axis_title", 0.02, 0.34, 0.06, 0.64)
      ),
      panel_boxes = list(
        candidate_box("gap_count_panel_A", "gap_count_panel", 0.10, 0.16, 0.44, 0.42),
        candidate_box("gap_count_panel_B", "gap_count_panel", 0.56, 0.16, 0.90, 0.42),
        candidate_box("gap_count_panel_C", "gap_count_panel", 0.10, 0.58, 0.44, 0.84),
        candidate_box("gap_count_panel_D", "gap_count_panel", 0.56, 0.58, 0.90, 0.84)
      ),
      guide_boxes = list(),
      metrics = list(
        source_renderer = dpcc_source_renderer(template_id),
        figure_purpose = "recorded_treatment_review_gap_burden_small_multiples",
        rendered_title_policy = "figure_title_metadata_only_not_drawn_inside_plot",
        rows = dpcc_metric_rows(display_payload$rows),
        panels = lapply(names(dpcc_gap_patient_fields), function(field) {
          list(gap_field = field, gap_label = unname(dpcc_gap_patient_fields[[field]]))
        })
      )
    ))
  }
  NULL
}
