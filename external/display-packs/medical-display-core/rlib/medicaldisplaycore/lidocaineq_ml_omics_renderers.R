# LidocaineQ/Figure_Template ML, omics, and explanation baselines.

lidocaine_rows <- function(payload, fields) {
  for (field_name in fields) {
    value <- payload[[field_name]]
    if (is.list(value) && length(value) > 0) {
      return(value)
    }
  }
  list()
}

lidocaine_panel_title <- function(payload, panel_id, fallback = "Panel", order_field = "panel_order") {
  panel_id <- trimws(as.character(panel_id %||% ""))
  panels <- payload[[order_field]] %||% list()
  if (is.list(panels) && length(panels) > 0) {
    for (panel in panels) {
      current_id <- trimws(as.character(panel$panel_id %||% ""))
      if (nzchar(panel_id) && identical(current_id, panel_id)) {
        return(lidocaine_non_empty(panel$panel_title %||% panel$title %||% panel$panel_label, fallback))
      }
    }
  }
  lidocaine_non_empty(panel_id, fallback)
}

lidocaine_threshold <- function(payload, key, fallback) {
  abs(lidocaine_numeric(payload[[key]], fallback))
}

lidocaine_feature_label <- function(item, fallback) {
  explicit_label <- item$label_text
  if (!is.null(explicit_label)) {
    return(trimws(as.character(explicit_label)))
  }
  lidocaine_non_empty(item$feature_label %||% item$feature %||% item$gene_label %||% item$label, fallback)
}

lidocaine_dot_dataframe <- function(display_payload, x_field = NULL) {
  points <- lidocaine_rows(display_payload, c("points", "programs"))
  if (length(points) < 1) {
    stop("points must contain at least one dotplot row")
  }
  dot_df <- do.call(rbind, lapply(seq_along(points), function(index) {
    item <- points[[index]]
    x_value <- item$x_value %||% item$feature_value
    x_label <- item$x %||% item$celltype_label %||% item$panel_id %||% item$cohort_label
    y_label <- item$y %||% item$marker_label %||% item$feature_label %||% item$pathway_label %||% item$program_label
    data.frame(
      x = if (!is.null(x_field)) {
        lidocaine_numeric(item[[x_field]], NA)
      } else if (!is.null(x_value)) {
        lidocaine_numeric(x_value, NA)
      } else {
        lidocaine_non_empty(x_label, sprintf("X%d", index))
      },
      y = lidocaine_non_empty(y_label, sprintf("Y%d", index)),
      value = lidocaine_numeric(item$value %||% item$effect_value %||% item$mean_abs_shap %||% item$score, 0),
      size = abs(lidocaine_numeric(item$size %||% item$size_value %||% item$support_n %||% item$count, 8)),
      stringsAsFactors = FALSE
    )
  }))
  if (all(is.finite(suppressWarnings(as.numeric(dot_df$x))))) {
    dot_df$x <- as.numeric(dot_df$x)
    dot_df$x_is_numeric <- TRUE
  } else {
    dot_df$x <- factor(dot_df$x, levels = unique(dot_df$x))
    dot_df$x_is_numeric <- FALSE
  }
  dot_df$y <- factor(dot_df$y, levels = rev(unique(dot_df$y)))
  dot_df
}

plot_lidocaine_pathway_enrichment <- function(display_payload) {
  dot_df <- lidocaine_dot_dataframe(display_payload, x_field = "x_value")
  ggplot(dot_df, aes(x = x, y = y, size = size, colour = value)) +
    geom_point(alpha = 0.9) +
    heatmap_colour_scale(display_payload, dot_df$value, name = lidocaine_non_empty(display_payload$effect_scale_label, "NES"), midpoint = 0) +
    scale_size_continuous(
      range = c(2.4, 7.4),
      name = lidocaine_non_empty(display_payload$size_scale_label, "Gene count"),
      breaks = continuous_scale_breaks(dot_df$size, max_breaks = 3)
    ) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Pathway enrichment dotplot"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Effect colour, support size"),
      x = lidocaine_non_empty(display_payload$x_label, "Gene ratio / enrichment score"),
      y = lidocaine_non_empty(display_payload$y_label)
    ) +
    lidocaine_publication_theme(display_payload) +
    theme_publication_colorbar(display_payload) +
    guides(size = guide_legend(nrow = 1, byrow = TRUE))
}

plot_lidocaine_celltype_marker_dotplot <- function(display_payload) {
  points <- lidocaine_rows(display_payload, c("points"))
  if (length(points) < 1) {
    stop("points must contain at least one cell-type marker record")
  }
  cell_order <- if (!is.null(display_payload$celltype_order)) {
    extract_label_vector(display_payload$celltype_order, "celltype_order")
  } else {
    unique(vapply(points, function(item) lidocaine_non_empty(item$celltype_label %||% item$x, ""), character(1)))
  }
  marker_order <- if (!is.null(display_payload$marker_order)) {
    extract_label_vector(display_payload$marker_order, "marker_order")
  } else {
    unique(vapply(points, function(item) lidocaine_non_empty(item$marker_label %||% item$y, ""), character(1)))
  }
  dot_df <- do.call(rbind, lapply(seq_along(points), function(index) {
    item <- points[[index]]
    data.frame(
      cell_type = lidocaine_non_empty(item$celltype_label %||% item$x, sprintf("Cell %d", index)),
      marker = lidocaine_non_empty(item$marker_label %||% item$y, sprintf("Marker %d", index)),
      pct = abs(lidocaine_numeric(item$size_value %||% item$pct_expression %||% item$size, 0)),
      avg = lidocaine_numeric(item$effect_value %||% item$avg_expression %||% item$value, 0),
      stringsAsFactors = FALSE
    )
  }))
  dot_df$cell_type <- factor(dot_df$cell_type, levels = rev(cell_order))
  dot_df$marker <- factor(dot_df$marker, levels = marker_order)
  ggplot(dot_df, aes(x = marker, y = cell_type, size = pct, colour = avg)) +
    geom_point(alpha = 0.9) +
    heatmap_colour_scale(display_payload, dot_df$avg, name = lidocaine_non_empty(display_payload$effect_scale_label, "Avg exp"), midpoint = 0) +
    scale_size_continuous(
      range = c(1.5, 8.0),
      name = lidocaine_non_empty(display_payload$size_scale_label, "Pct"),
      breaks = continuous_scale_breaks(dot_df$pct, max_breaks = 3)
    ) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Cell-type marker dotplot"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Expression percent and average expression"),
      x = lidocaine_non_empty(display_payload$x_label),
      y = lidocaine_non_empty(display_payload$y_label)
    ) +
    lidocaine_publication_theme(display_payload) +
    theme_publication_colorbar(display_payload) +
    guides(
      colour = publication_colorbar_guide(
        display_payload,
        title = lidocaine_non_empty(display_payload$effect_scale_label, "Avg exp"),
        bar_orientation = "horizontal"
      ),
      size = guide_legend(nrow = 1, byrow = TRUE, title.position = "top")
    ) +
    theme(
      legend.box = "vertical",
      legend.spacing.y = unit(1.5, "pt"),
      legend.margin = margin(2, 28, 6, 28, unit = "pt"),
      axis.text.x = element_text(angle = 35, hjust = 1),
      panel.grid.major = element_blank(),
      plot.margin = margin(8, 18, 14, 18, unit = "pt")
    )
}

lidocaine_volcano_dataframe <- function(display_payload) {
  points <- lidocaine_rows(display_payload, c("points", "consequence_points"))
  if (length(points) < 1) {
    stop("points must contain at least one volcano row")
  }
  do.call(rbind, lapply(seq_along(points), function(index) {
    item <- points[[index]]
    data.frame(
      panel = lidocaine_panel_title(display_payload, item$panel_id, "A"),
      feature = lidocaine_feature_label(item, sprintf("Feature %d", index)),
      effect = lidocaine_numeric(item$effect_value %||% item$x, 0),
      significance = lidocaine_numeric(item$significance_value %||% item$y, 0),
      class = lidocaine_non_empty(item$regulation_class %||% item$status, "NS"),
      label_text = lidocaine_non_empty(item$label_text),
      stringsAsFactors = FALSE
    )
  }))
}

plot_lidocaine_volcano <- function(display_payload) {
  volcano_df <- lidocaine_volcano_dataframe(display_payload)
  effect_threshold <- lidocaine_threshold(display_payload, "effect_threshold", 1)
  significance_threshold <- lidocaine_numeric(display_payload$significance_threshold, 1.3)
  normalized_class <- tolower(volcano_df$class)
  volcano_df$class <- ifelse(
    normalized_class %in% c("up", "upregulated"),
    "Up",
    ifelse(normalized_class %in% c("down", "downregulated"), "Down", "NS")
  )
  label_df <- volcano_df[
    nzchar(volcano_df$feature) &
      volcano_df$class != "NS" &
      (
        nzchar(volcano_df$label_text) |
          volcano_df$significance >= stats::quantile(volcano_df$significance, 0.88, na.rm = TRUE)
      ),
    ,
    drop = FALSE
  ]
  if (nrow(label_df) > 8) {
    label_df <- label_df[order(-label_df$significance), , drop = FALSE][seq_len(8), , drop = FALSE]
  }
  label_df$feature <- ifelse(nzchar(label_df$label_text), label_df$label_text, label_df$feature)
  x_range <- range(volcano_df$effect, na.rm = TRUE)
  x_span <- max(0.1, diff(x_range))
  if (nrow(label_df) > 0) {
    label_df$label_x <- label_df$effect + ifelse(label_df$effect < 0, -x_span * 0.025, x_span * 0.025)
    label_df$label_hjust <- ifelse(label_df$effect < 0, 1, 0)
  }
  plot <- ggplot(volcano_df, aes(effect, significance, colour = class)) +
    geom_point(size = 1.35, alpha = 0.78) +
    geom_vline(xintercept = c(-effect_threshold, effect_threshold), linetype = "dashed", linewidth = 0.45, colour = style_color(display_payload, "reference_line", "muted", "#64748B")) +
    geom_hline(yintercept = significance_threshold, linetype = "dashed", linewidth = 0.45, colour = style_color(display_payload, "reference_line", "muted", "#64748B")) +
    geom_text(
      data = label_df,
      aes(x = label_x, label = feature, hjust = label_hjust),
      show.legend = FALSE,
      size = 2.6,
      vjust = -0.55,
      colour = style_text_color(display_payload)
    ) +
    scale_colour_manual(
      values = c(
        Down = style_color(display_payload, "volcano_down", "volcano_down", "#2166AC"),
        NS = style_color(display_payload, "volcano_background", "volcano_background", "#CBD5E1"),
        Up = style_color(display_payload, "volcano_up", "volcano_up", "#B2182B")
      ),
      guide = publication_legend_guides(display_payload, volcano_df$class)
    ) +
    coord_cartesian(xlim = c(x_range[[1]] - x_span * 0.12, x_range[[2]] + x_span * 0.16), clip = "off") +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Volcano plot"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Differential-feature screening"),
      x = lidocaine_non_empty(display_payload$x_label, "log2 fold-change"),
      y = lidocaine_non_empty(display_payload$y_label, "-log10 adjusted P")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1, plot.margin = margin(9, 22, 9, 20))
  if (length(unique(volcano_df$panel)) > 1) {
    plot <- plot + facet_wrap(~panel)
  }
  plot
}

plot_lidocaine_genomic_consequence <- function(display_payload) {
  points <- lidocaine_rows(display_payload, c("consequence_points", "points"))
  if (length(points) < 1) {
    stop("consequence_points must contain at least one row")
  }
  effect_df <- do.call(rbind, lapply(seq_along(points), function(index) {
    item <- points[[index]]
    data.frame(
      alteration = lidocaine_non_empty(item$gene_label %||% item$feature_label %||% item$alteration %||% item$label_text, sprintf("Alteration %d", index)),
      estimate = lidocaine_numeric(item$estimate %||% item$effect_value %||% item$x, 1),
      lower = lidocaine_numeric(item$lower, NA),
      upper = lidocaine_numeric(item$upper, NA),
      q = lidocaine_non_empty(item$q_value %||% item$q %||% item$p_value, ""),
      stringsAsFactors = FALSE
    )
  }))
  missing_interval <- !is.finite(effect_df$lower) | !is.finite(effect_df$upper)
  effect_df$lower[missing_interval] <- pmax(0.05, effect_df$estimate[missing_interval] * 0.76)
  effect_df$upper[missing_interval] <- effect_df$estimate[missing_interval] * 1.32
  effect_df <- effect_df[order(effect_df$estimate), , drop = FALSE]
  effect_df$alteration <- factor(effect_df$alteration, levels = effect_df$alteration)
  label_x <- max(effect_df$upper, na.rm = TRUE) * 1.10
  ggplot(effect_df, aes(estimate, alteration)) +
    geom_vline(xintercept = lidocaine_numeric(display_payload$reference_value, 1), linetype = "dashed", colour = style_color(display_payload, "reference_line", "muted", "#64748B"), linewidth = 0.5) +
    geom_errorbar(aes(xmin = lower, xmax = upper), orientation = "y", width = 0.16, colour = style_color(display_payload, "model_curve", "primary", "#245A6B"), linewidth = 0.70) +
    geom_point(size = 2.4, colour = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A")) +
    geom_text(
      data = effect_df[nzchar(effect_df$q), , drop = FALSE],
      aes(x = label_x, label = paste0("FDR=", q)),
      hjust = 0,
      size = 3.0,
      colour = style_text_color(display_payload)
    ) +
    scale_x_log10(limits = c(max(0.1, min(effect_df$lower, na.rm = TRUE) * 0.72), label_x * 1.25)) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Genomic alteration consequence"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Functional or clinical effect summary"),
      x = lidocaine_non_empty(display_payload$consequence_x_label %||% display_payload$x_label, "Effect estimate"),
      y = NULL
    ) +
    lidocaine_publication_theme(display_payload)
}

lidocaine_alteration_state <- function(item, default_state = "Altered") {
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

lidocaine_alteration_palette <- function(display_payload, values) {
  named_values <- c(
    Missense = style_color(display_payload, "model_curve", "primary", "#245A6B"),
    Truncating = style_color(display_payload, "volcano_up", "volcano_up", "#B2182B"),
    Gain = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A"),
    Amplification = style_color(display_payload, "series_3", "tertiary", "#D8A24A"),
    Loss = style_color(display_payload, "heatmap_low", "heatmap_low", "#2166AC"),
    Deletion = style_color(display_payload, "series_5", "violet", "#6D5BD0"),
    `Multi-hit` = style_color(display_payload, "series_4", "quaternary", "#2A9D8F"),
    Altered = style_color(display_payload, "model_curve", "primary", "#245A6B"),
    CNV = style_color(display_payload, "series_6", "muted", "#64748B"),
    Neutral = "#F4F6F8",
    Derivation = style_color(display_payload, "series_1", "primary", "#245A6B"),
    Validation = style_color(display_payload, "series_2", "secondary", "#8B3A3A"),
    Primary = style_color(display_payload, "series_3", "tertiary", "#D8A24A"),
    Metastatic = style_color(display_payload, "series_4", "quaternary", "#2A9D8F")
  )
  present <- intersect(names(named_values), unique(as.character(values)))
  named_values[present]
}

lidocaine_oncoprint_alter_fun <- function(alteration_type, alteration_colours) {
  force(alteration_type)
  force(alteration_colours)
  function(x, y, w, h) {
    grid::grid.rect(
      x,
      y,
      w * 0.90,
      h * 0.76,
      gp = grid::gpar(fill = alteration_colours[[alteration_type]], col = "white", lwd = 0.35)
    )
  }
}

plot_lidocaine_cnv_recurrence <- function(display_payload) {
  records <- display_payload$cnv_records %||% list()
  if (length(records) > 0) {
    first_record <- records[[1]]
    if (!is.null(first_record$chrom) || !is.null(first_record$event) || !is.null(first_record$freq)) {
      cnv_df <- do.call(rbind, lapply(seq_along(records), function(index) {
        item <- records[[index]]
        data.frame(
          chrom = lidocaine_non_empty(item$chrom %||% item$chromosome %||% item$region_label, sprintf("chr%d", index)),
          event = lidocaine_non_empty(item$event %||% item$cnv_state, "Gain"),
          freq = abs(lidocaine_numeric(item$freq %||% item$frequency %||% item$value, NA)),
          stringsAsFactors = FALSE
        )
      }))
      if (any(!is.finite(cnv_df$freq))) {
        stop("cnv recurrence frequency records must contain finite freq values")
      }
      chrom_levels <- unique(cnv_df$chrom)
      cnv_df$chrom <- factor(cnv_df$chrom, levels = chrom_levels)
      cnv_df$signed_freq <- ifelse(tolower(cnv_df$event) == "loss", -cnv_df$freq, cnv_df$freq)
      cnv_df$event <- factor(cnv_df$event, levels = c("Gain", "Loss"))
      return(ggplot(cnv_df, aes(chrom, signed_freq, fill = event)) +
        geom_col(width = 0.70, colour = "white", linewidth = 0.25) +
        geom_hline(yintercept = 0, colour = style_color(display_payload, "axis_line", "axis", "#13293D"), linewidth = 0.45) +
        scale_fill_manual(
          values = c(
            Gain = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A"),
            Loss = style_color(display_payload, "model_curve", "primary", "#245A6B")
          ),
          guide = publication_legend_guides(display_payload, c("Gain", "Loss"))
        ) +
        scale_y_continuous(labels = function(x) paste0(abs(round(x * 100)), "%")) +
        labs(
          title = lidocaine_non_empty(display_payload$title, "CNV recurrence summary"),
          subtitle = lidocaine_wrap_label(display_payload$subtitle %||% display_payload$caption, 72),
          x = lidocaine_non_empty(display_payload$x_label),
          y = lidocaine_non_empty(display_payload$y_label, "Sample frequency")
        ) +
        lidocaine_publication_theme(display_payload))
    } else {
      NULL
    }
  }
  regions <- if (!is.null(display_payload$region_order)) extract_label_vector(display_payload$region_order, "region_order") else character()
  samples <- if (!is.null(display_payload$sample_order)) {
    vapply(display_payload$sample_order, function(item) lidocaine_non_empty(item$sample_id %||% item$label, ""), character(1))
  } else {
    character()
  }
  if (length(regions) < 1 || length(samples) < 1 || length(records) < 1) {
    stop("cnv recurrence payload requires region_order, sample_order, and cnv_records")
  }
  base <- expand.grid(sample_id = samples, region_label = regions, stringsAsFactors = FALSE)
  record_df <- do.call(rbind, lapply(records, function(item) {
    data.frame(
      sample_id = lidocaine_non_empty(item$sample_id, ""),
      region_label = lidocaine_non_empty(item$region_label %||% item$region, ""),
      state = lidocaine_alteration_state(list(cnv_state = item$cnv_state), default_state = "CNV"),
      stringsAsFactors = FALSE
    )
  }))
  matrix_df <- merge(base, record_df, by = c("sample_id", "region_label"), all.x = TRUE, sort = FALSE)
  matrix_df$state[is.na(matrix_df$state)] <- "Neutral"
  matrix_df$sample_id <- factor(matrix_df$sample_id, levels = samples)
  matrix_df$region_label <- factor(matrix_df$region_label, levels = rev(regions))
  fill_values <- lidocaine_alteration_palette(display_payload, matrix_df$state)
  ggplot(matrix_df, aes(sample_id, region_label, fill = state)) +
    geom_tile(colour = "white", linewidth = 0.42) +
    scale_fill_manual(values = fill_values, drop = FALSE, name = NULL, guide = publication_legend_guides(display_payload, names(fill_values))) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "CNV recurrence summary"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Recurrent gains and losses"),
      x = lidocaine_non_empty(display_payload$x_label, "Samples"),
      y = lidocaine_non_empty(display_payload$y_label, "Regions")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(axis.text.x = element_text(angle = 0, hjust = 0.5), panel.grid = element_blank(), legend.box = "vertical")
}

plot_lidocaine_genomic_landscape <- function(display_payload) {
  if (!requireNamespace("maftools", quietly = TRUE)) {
    stop("genomic_alteration_landscape_panel requires OPL-prepared dependency package `maftools`; run OPL prepare/doctor for the MAS display profile")
  }
  genes <- if (!is.null(display_payload$gene_order)) extract_label_vector(display_payload$gene_order, "gene_order") else character()
  samples <- if (!is.null(display_payload$sample_order)) {
    vapply(display_payload$sample_order, function(item) lidocaine_non_empty(item$sample_id %||% item$label, ""), character(1))
  } else {
    character()
  }
  records <- display_payload$alteration_records %||% list()
  if (length(genes) < 1 || length(samples) < 1 || length(records) < 1) {
    stop("genomic landscape payload requires gene_order, sample_order, and alteration_records")
  }
  variant_classification_for_state <- function(state) {
    normalized <- tolower(trimws(as.character(state %||% "")))
    if (grepl("trunc|nonsense", normalized)) {
      return("Nonsense_Mutation")
    }
    if (grepl("frame.*ins|ampl|gain", normalized)) {
      return("Frame_Shift_Ins")
    }
    if (grepl("frame.*del|loss|del", normalized)) {
      return("Frame_Shift_Del")
    }
    if (grepl("splice", normalized)) {
      return("Splice_Site")
    }
    "Missense_Mutation"
  }
  maf_df <- do.call(rbind, lapply(seq_along(records), function(record_index) {
    item <- records[[record_index]]
    sample_id <- lidocaine_non_empty(item$sample_id, "")
    gene_label <- lidocaine_non_empty(item$gene_label %||% item$gene, "")
    if (!sample_id %in% samples || !gene_label %in% genes) {
      return(NULL)
    }
    state <- lidocaine_alteration_state(item)
    data.frame(
      Hugo_Symbol = gene_label,
      Chromosome = as.character((record_index %% 22) + 1),
      Start_Position = 100000 + record_index,
      End_Position = 100000 + record_index,
      Reference_Allele = "A",
      Tumor_Seq_Allele2 = "T",
      Variant_Classification = variant_classification_for_state(state),
      Variant_Type = "SNP",
      Tumor_Sample_Barcode = sample_id,
      stringsAsFactors = FALSE
    )
  }))
  if (!is.data.frame(maf_df) || nrow(maf_df) < 1) {
    stop("genomic landscape payload did not contain plottable alteration records")
  }
  clinical_df <- data.frame(Tumor_Sample_Barcode = samples, stringsAsFactors = FALSE)
  annotation_colours <- list()
  sample_annotations <- display_payload$sample_annotations %||% list()
  if (is.list(sample_annotations) && length(sample_annotations) > 0) {
    for (annotation_index in seq_along(sample_annotations)) {
      annotation <- sample_annotations[[annotation_index]]
      annotation_label <- make.names(lidocaine_non_empty(annotation$label, sprintf("Annotation%d", annotation_index)))
      values <- rep("", length(samples))
      names(values) <- samples
      for (value_item in annotation$values %||% list()) {
        sample_id <- lidocaine_non_empty(value_item$sample_id, "")
        if (sample_id %in% samples) {
          values[[sample_id]] <- lidocaine_non_empty(value_item$value, "")
        }
      }
      clinical_df[[annotation_label]] <- values
      annotation_colours[[annotation_label]] <- lidocaine_alteration_palette(display_payload, unique(values))
    }
  }
  variant_colours <- c(
    Missense_Mutation = style_color(display_payload, "model_curve", "primary", "#245A6B"),
    Nonsense_Mutation = style_color(display_payload, "volcano_up", "volcano_up", "#B2182B"),
    Frame_Shift_Del = style_color(display_payload, "heatmap_low", "heatmap_low", "#2166AC"),
    Frame_Shift_Ins = style_color(display_payload, "series_3", "tertiary", "#D8A24A"),
    Splice_Site = style_color(display_payload, "series_5", "violet", "#6D5BD0")
  )
  annotation_features <- setdiff(names(clinical_df), "Tumor_Sample_Barcode")
  maftools_draw <- function() {
    maf_obj <- maftools::read.maf(maf = maf_df, clinicalData = clinical_df, verbose = FALSE)
    old_par <- graphics::par(no.readonly = TRUE)
    on.exit(graphics::par(old_par), add = TRUE)
    graphics::par(mar = c(1.2, 1.2, 1.2, 1.2), xpd = NA)
    maftools::oncoplot(
      maf = maf_obj,
      genes = genes,
      top = length(genes),
      fontSize = style_numeric(style_typography(display_payload), "tick_size", 8.0) / 10,
      showTumorSampleBarcodes = FALSE,
      clinicalFeatures = annotation_features,
      sortByAnnotation = length(annotation_features) > 0,
      annotationColor = annotation_colours,
      colors = variant_colours,
      bgCol = "white",
      borderCol = NA
    )
  }
  structure(
    list(
      draw = maftools_draw,
      source_renderer = "LidocaineQ/Figure_Template::oncoplot_mutation"
    ),
    class = "lidocaine_base_graphics_plot"
  )
}

lidocaine_shap_rows <- function(display_payload) {
  rows <- lidocaine_rows(display_payload, c("rows", "bars"))
  if (length(rows) < 1 && is.list(display_payload$panels)) {
    rows <- unlist(lapply(display_payload$panels, function(panel) lidocaine_rows(panel, c("rows", "bars"))), recursive = FALSE)
  }
  if (length(rows) < 1) {
    stop("SHAP summary payload must contain rows with points")
  }
  rows
}

plot_lidocaine_shap_summary <- function(display_payload) {
  rows <- lidocaine_shap_rows(display_payload)
  shap_df <- do.call(rbind, lapply(seq_along(rows), function(row_index) {
    row <- rows[[row_index]]
    points <- row$points %||% list(list(shap_value = row$value %||% row$mean_abs_shap %||% 0, feature_value = 0.5))
    do.call(rbind, lapply(seq_along(points), function(point_index) {
      point <- points[[point_index]]
      data.frame(
        feature = lidocaine_non_empty(row$feature %||% row$label, sprintf("Feature %d", row_index)),
        shap = lidocaine_numeric(point$shap_value %||% point$value, 0),
        value = lidocaine_numeric(point$feature_value, point_index),
        stringsAsFactors = FALSE
      )
    }))
  }))
  shap_df$feature <- factor(shap_df$feature, levels = rev(unique(shap_df$feature)))
  ggplot(shap_df, aes(shap, feature, colour = value)) +
    geom_vline(xintercept = 0, linewidth = 0.45, colour = style_color(display_payload, "reference_line", "muted", "#64748B")) +
    geom_point(position = position_jitter(height = 0.18, width = 0, seed = 7), alpha = 0.78, size = 1.15) +
    scale_colour_gradient(
      low = style_color(display_payload, "model_curve", "primary", "#245A6B"),
      high = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A"),
      name = lidocaine_non_empty(display_payload$colorbar_label, "Feature value"),
      guide = publication_colorbar_guide(display_payload, title = lidocaine_non_empty(display_payload$colorbar_label, "Feature value"), bar_orientation = "horizontal")
    ) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "SHAP summary beeswarm"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Global feature contribution distribution"),
      x = lidocaine_non_empty(display_payload$x_label, "SHAP value"),
      y = NULL
    ) +
    lidocaine_publication_theme(display_payload) +
    theme_publication_colorbar(display_payload) +
    theme(aspect.ratio = 1)
}

plot_lidocaine_shap_dependence <- function(display_payload) {
  panels <- display_payload$panels %||% list()
  if (length(panels) < 1) {
    stop("SHAP dependence payload must contain panels")
  }
  dependence_df <- do.call(rbind, lapply(seq_along(panels), function(panel_index) {
    panel <- panels[[panel_index]]
    points <- panel$points %||% list()
    if (length(points) < 1) {
      stop(sprintf("panels[%d].points must contain at least one row", panel_index))
    }
    do.call(rbind, lapply(points, function(point) {
      data.frame(
        panel = lidocaine_non_empty(panel$title %||% panel$feature %||% panel$panel_label, sprintf("Panel %d", panel_index)),
        feature_value = lidocaine_numeric(point$feature_value, 0),
        shap = lidocaine_numeric(point$shap_value, 0),
        subgroup = lidocaine_non_empty(point$subgroup %||% point$group, ""),
        interaction_value = lidocaine_numeric(point$interaction_value %||% point$feature_value, 0),
        stringsAsFactors = FALSE
      )
    }))
  }))
  if (all(!nzchar(dependence_df$subgroup))) {
    dependence_df$subgroup <- ifelse(dependence_df$interaction_value >= stats::median(dependence_df$interaction_value), "High context", "Low context")
  }
  plot <- ggplot(dependence_df, aes(feature_value, shap, colour = subgroup)) +
    geom_point(alpha = 0.75, size = 1.5) +
    geom_smooth(method = "loess", formula = y ~ x, se = FALSE, linewidth = 0.80) +
    scale_colour_manual(values = lidocaine_palette(display_payload, dependence_df$subgroup), guide = publication_legend_guides(display_payload, dependence_df$subgroup)) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "SHAP dependence panel"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Feature value vs model contribution"),
      x = lidocaine_non_empty(display_payload$x_label, "Feature value"),
      y = lidocaine_non_empty(display_payload$y_label, "SHAP value")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1)
  if (length(unique(dependence_df$panel)) > 1) {
    plot <- plot + facet_wrap(~panel, nrow = 1, scales = "free_x")
  }
  plot
}

plot_lidocaine_shap_waterfall <- function(display_payload) {
  panel <- if (is.list(display_payload$panels) && length(display_payload$panels) > 0) display_payload$panels[[1]] else display_payload
  contributions <- panel$contributions %||% list()
  if (length(contributions) < 1) {
    stop("SHAP waterfall payload must contain contributions")
  }
  contribution_df <- do.call(rbind, lapply(seq_along(contributions), function(index) {
    item <- contributions[[index]]
    data.frame(
      feature = lidocaine_non_empty(item$feature %||% item$label, sprintf("Feature %d", index)),
      contribution = lidocaine_numeric(item$shap_value %||% item$value, 0),
      explicit_type = lidocaine_non_empty(item$contribution_type),
      stringsAsFactors = FALSE
    )
  }))
  baseline <- lidocaine_numeric(panel$baseline_value %||% display_payload$baseline_value, 0)
  final_value <- lidocaine_numeric(panel$predicted_value %||% display_payload$predicted_value, baseline + sum(contribution_df$contribution))
  if (!any(tolower(contribution_df$explicit_type) == "base")) {
    contribution_df <- rbind(
      data.frame(feature = "Baseline", contribution = baseline, explicit_type = "base", stringsAsFactors = FALSE),
      contribution_df
    )
    baseline <- 0
  }
  waterfall_df <- rbind(
    contribution_df,
    data.frame(feature = "Prediction", contribution = final_value, explicit_type = "final", stringsAsFactors = FALSE)
  )
  waterfall_df$step <- seq_len(nrow(waterfall_df))
  waterfall_df$start <- c(0, head(cumsum(waterfall_df$contribution), -1))
  waterfall_df$end <- cumsum(waterfall_df$contribution)
  waterfall_df$type <- ifelse(
    tolower(waterfall_df$explicit_type) %in% c("base", "final"),
    tolower(waterfall_df$explicit_type),
    ifelse(waterfall_df$contribution >= 0, "positive", "negative")
  )
  waterfall_df$feature <- factor(waterfall_df$feature, levels = waterfall_df$feature)
  ggplot(waterfall_df, aes(x = step)) +
    geom_segment(aes(xend = step, y = start, yend = end, colour = type), linewidth = 7, lineend = "butt") +
    geom_hline(yintercept = 0, linewidth = 0.45, colour = style_color(display_payload, "reference_line", "muted", "#64748B")) +
    scale_colour_manual(
      values = c(
        base = style_color(display_payload, "reference_line", "muted", "#64748B"),
        positive = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A"),
        negative = style_color(display_payload, "model_curve", "primary", "#245A6B"),
        final = style_color(display_payload, "series_3", "tertiary", "#D8A24A")
      ),
      guide = publication_legend_guides(display_payload, waterfall_df$type)
    ) +
    scale_x_continuous(breaks = waterfall_df$step, labels = waterfall_df$feature) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "SHAP waterfall explanation"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Single-patient local contribution"),
      x = NULL,
      y = lidocaine_non_empty(display_payload$y_label, "Prediction contribution")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(axis.text.x = element_text(angle = 35, hjust = 1), aspect.ratio = 0.66)
}

lidocaine_coefficient_path_dataframe <- function(display_payload) {
  path_points <- lidocaine_rows(display_payload, c("path_points", "coefficient_path", "coefficient_points"))
  if (length(path_points) > 0) {
    return(do.call(rbind, lapply(seq_along(path_points), function(index) {
      item <- path_points[[index]]
      data.frame(
        log_lambda = lidocaine_numeric(item$log_lambda %||% item$lambda, NA),
        coefficient = lidocaine_numeric(item$coefficient, NA),
        feature = lidocaine_non_empty(item$feature %||% item$label, sprintf("Feature %d", index)),
        stringsAsFactors = FALSE
      )
    })))
  }
  rows <- display_payload$coefficient_rows %||% list()
  steps <- display_payload$steps %||% list()
  if (length(rows) < 1 || length(steps) < 2) {
    stop("coefficient path payload must contain path_points or coefficient_rows plus steps")
  }
  step_ids <- vapply(steps, function(item) lidocaine_non_empty(item$step_id %||% item$step_label, ""), character(1))
  do.call(rbind, lapply(seq_along(rows), function(row_index) {
    row <- rows[[row_index]]
    points <- row$points %||% list()
    do.call(rbind, lapply(seq_along(points), function(point_index) {
      point <- points[[point_index]]
      step_id <- lidocaine_non_empty(point$step_id, "")
      step_index <- match(step_id, step_ids)
      if (!is.finite(step_index)) {
        step_index <- point_index
      }
      data.frame(
        log_lambda = lidocaine_numeric(point$log_lambda, -4 + (step_index - 1) * (5 / max(1, length(step_ids) - 1))),
        coefficient = log(lidocaine_numeric(point$estimate, 1)),
        feature = lidocaine_non_empty(row$row_label %||% row$label, sprintf("Feature %d", row_index)),
        stringsAsFactors = FALSE
      )
    }))
  }))
}

plot_lidocaine_coefficient_path <- function(display_payload) {
  path_df <- lidocaine_coefficient_path_dataframe(display_payload)
  if (any(!is.finite(path_df$log_lambda)) || any(!is.finite(path_df$coefficient))) {
    stop("coefficient path values must be finite")
  }
  ggplot(path_df, aes(log_lambda, coefficient, colour = feature, group = feature)) +
    geom_hline(yintercept = 0, linewidth = 0.45, colour = style_color(display_payload, "reference_line", "muted", "#64748B")) +
    geom_vline(
      xintercept = lidocaine_numeric(display_payload$selected_log_lambda, stats::median(path_df$log_lambda)),
      linetype = "dashed",
      linewidth = 0.5,
      colour = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A")
    ) +
    geom_line(linewidth = 0.82) +
    scale_colour_manual(values = lidocaine_palette(display_payload, path_df$feature), guide = publication_legend_guides(display_payload, path_df$feature)) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Coefficient path panel"),
      subtitle = lidocaine_wrap_label(lidocaine_curve_subtitle(display_payload, "Regularization path with selected lambda"), 74),
      x = lidocaine_non_empty(display_payload$x_label, "log(lambda)"),
      y = lidocaine_non_empty(display_payload$y_label, "Coefficient")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1)
}

lidocaine_risk_layer_dataframe <- function(display_payload) {
  rows <- display_payload$risk_group_summaries %||% list()
  if (length(rows) < 1) {
    rows <- display_payload$bars %||% list()
  }
  if (length(rows) < 1) {
    rows <- display_payload$left_bars %||% list()
  }
  if (length(rows) < 1) {
    rows <- display_payload$right_bars %||% list()
  }
  if (length(rows) < 1) {
    stop("risk layering payload must contain risk_group_summaries, bars, left_bars, or right_bars")
  }
  risk_df <- do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    event_rate <- lidocaine_numeric(
      item$event_rate %||% item$risk %||% item$value %||% item$observed_km_risk_5y %||% item$mean_predicted_risk_5y,
      NA
    )
    data.frame(
      layer = lidocaine_non_empty(item$layer %||% item$label %||% item$group_label, sprintf("Band %d", index)),
      event_rate = event_rate,
      lower = lidocaine_numeric(item$lower %||% item$ci_lower, NA),
      upper = lidocaine_numeric(item$upper %||% item$ci_upper, NA),
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(risk_df$event_rate))) {
    stop("risk layering event_rate values must be finite")
  }
  risk_df$lower[!is.finite(risk_df$lower)] <- pmax(0, risk_df$event_rate[!is.finite(risk_df$lower)] - 0.04)
  risk_df$upper[!is.finite(risk_df$upper)] <- pmin(1, risk_df$event_rate[!is.finite(risk_df$upper)] + 0.06)
  risk_df$layer <- factor(risk_df$layer, levels = risk_df$layer)
  risk_df
}

plot_lidocaine_risk_layering <- function(display_payload) {
  risk_df <- lidocaine_risk_layer_dataframe(display_payload)
  y_max <- max(c(risk_df$upper, risk_df$event_rate), na.rm = TRUE)
  percent_scale <- y_max <= 1.001
  y_limit <- if (percent_scale) min(1, max(0.60, y_max * 1.18)) else y_max * 1.18
  ggplot(risk_df, aes(layer, event_rate)) +
    geom_col(
      fill = style_color(display_payload, "model_curve", "primary", "#245A6B"),
      width = 0.68,
      alpha = 0.88
    ) +
    geom_errorbar(
      aes(ymin = lower, ymax = upper),
      width = 0.14,
      linewidth = 0.55,
      colour = style_text_color(display_payload)
    ) +
    geom_line(
      aes(group = 1),
      linewidth = 0.55,
      colour = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A")
    ) +
    geom_point(
      size = 2.0,
      colour = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A")
    ) +
    scale_y_continuous(
      labels = if (percent_scale) function(x) paste0(round(x * 100), "%") else waiver(),
      limits = c(0, y_limit),
      expand = c(0, 0)
    ) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Monotonic risk layering"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Risk strata show a clinical gradient"),
      x = lidocaine_non_empty(display_payload$x_label),
      y = lidocaine_non_empty(display_payload$y_label, if (percent_scale) "Event rate" else "Event count")
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(panel.grid.major.x = element_blank())
}

plot_lidocaine_generalizability <- function(display_payload) {
  rows <- c(display_payload$overview_rows %||% list(), display_payload$subgroup_rows %||% list())
  if (length(rows) < 1) {
    stop("generalizability payload must contain overview_rows or subgroup_rows")
  }
  general_df <- do.call(rbind, lapply(seq_along(rows), function(index) {
    row <- rows[[index]]
    metric <- lidocaine_numeric(row$metric_value %||% row$estimate %||% row$value, NA)
    data.frame(
      cohort = lidocaine_non_empty(row$cohort_label %||% row$subgroup_label %||% row$label, sprintf("Cohort %d", index)),
      metric = metric,
      lower = lidocaine_numeric(row$lower, metric),
      upper = lidocaine_numeric(row$upper, metric),
      family = if (!is.null(row$cohort_label)) "Cohort" else "Subgroup",
      stringsAsFactors = FALSE
    )
  }))
  if (any(!is.finite(general_df$metric))) {
    stop("generalizability metric values must be finite")
  }
  general_df$cohort <- factor(general_df$cohort, levels = rev(general_df$cohort))
  ggplot(general_df, aes(metric, cohort, colour = family)) +
    geom_vline(xintercept = lidocaine_numeric(display_payload$subgroup_reference_value, 0.8), linetype = "dashed", linewidth = 0.5, colour = style_color(display_payload, "reference_line", "muted", "#64748B")) +
    geom_errorbar(aes(xmin = lower, xmax = upper), orientation = "y", width = 0.18, linewidth = 0.65) +
    geom_point(size = 2.4) +
    scale_colour_manual(values = lidocaine_palette(display_payload, general_df$family), guide = publication_legend_guides(display_payload, general_df$family)) +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Generalizability composite"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Performance stability across cohorts and subgroups"),
      x = lidocaine_non_empty(display_payload$overview_x_label %||% display_payload$subgroup_x_label, "AUC / C-index"),
      y = NULL
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(aspect.ratio = 1)
}

plot_lidocaine_model_complexity <- function(display_payload) {
  complexity_points <- display_payload$complexity_points %||% display_payload$points %||% list()
  if (length(complexity_points) > 0) {
    complexity_df <- do.call(rbind, lapply(seq_along(complexity_points), function(index) {
      item <- complexity_points[[index]]
      features <- lidocaine_numeric(item$features %||% item$feature_count %||% item$n_features, NA)
      rbind(
        data.frame(
          features = features,
          auc = lidocaine_numeric(item$cv_auc %||% item$cross_validation_auc, NA),
          metric = "Cross-validation",
          stringsAsFactors = FALSE
        ),
        data.frame(
          features = features,
          auc = lidocaine_numeric(item$external_auc %||% item$validation_auc, NA),
          metric = "External validation",
          stringsAsFactors = FALSE
        )
      )
    }))
    if (any(!is.finite(complexity_df$features)) || any(!is.finite(complexity_df$auc))) {
      stop("model complexity points must contain finite features, cv_auc, and external_auc values")
    }
    selected_feature_count <- lidocaine_numeric(display_payload$selected_feature_count, stats::median(complexity_df$features))
    y_limits <- range(complexity_df$auc, na.rm = TRUE)
    y_pad <- max(0.02, diff(y_limits) * 0.22)
    return(ggplot(complexity_df, aes(features, auc, colour = metric)) +
      geom_line(linewidth = 0.85) +
      geom_point(size = 2.1) +
      geom_vline(
        xintercept = selected_feature_count,
        linetype = "dashed",
        colour = style_color(display_payload, "comparator_curve", "secondary", "#8B3A3A"),
        linewidth = 0.50
      ) +
      scale_colour_manual(values = lidocaine_palette(display_payload, complexity_df$metric), guide = publication_legend_guides(display_payload, complexity_df$metric)) +
      scale_y_continuous(limits = c(max(0, y_limits[[1]] - y_pad), min(1, y_limits[[2]] + y_pad))) +
      labs(
        title = lidocaine_non_empty(display_payload$title, "Model complexity audit"),
        subtitle = lidocaine_curve_subtitle(display_payload, "Performance vs feature count"),
        x = lidocaine_non_empty(display_payload$x_label, "Number of retained features"),
        y = lidocaine_non_empty(display_payload$y_label, "AUC")
      ) +
      lidocaine_publication_theme(display_payload) +
      theme(aspect.ratio = 1))
  }
  metric_panels <- display_payload$metric_panels %||% list()
  audit_panels <- display_payload$audit_panels %||% list()
  rows <- c(
    unlist(lapply(metric_panels, function(panel) {
      lapply(panel$rows %||% list(), function(row) c(row, list(panel = lidocaine_non_empty(panel$title, "Metric"))))
    }), recursive = FALSE),
    unlist(lapply(audit_panels, function(panel) {
      lapply(panel$rows %||% list(), function(row) c(row, list(panel = lidocaine_non_empty(panel$title, "Audit"))))
    }), recursive = FALSE)
  )
  if (length(rows) < 1) {
    stop("model complexity payload must contain metric or audit rows")
  }
  audit_df <- do.call(rbind, lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    data.frame(
      panel = lidocaine_non_empty(item$panel, "Panel"),
      label = lidocaine_non_empty(item$label, sprintf("Row %d", index)),
      value = lidocaine_numeric(item$value, 0),
      stringsAsFactors = FALSE
    )
  }))
  audit_df$label <- factor(audit_df$label, levels = rev(unique(audit_df$label)))
  ggplot(audit_df, aes(value, label)) +
    geom_segment(aes(x = 0, xend = value, y = label, yend = label), colour = style_color(display_payload, "model_curve", "primary", "#245A6B"), linewidth = 0.58, alpha = 0.72) +
    geom_point(colour = style_color(display_payload, "model_curve", "primary", "#245A6B"), size = 2.2) +
    facet_wrap(~panel, ncol = 1, scales = "free") +
    labs(
      title = lidocaine_non_empty(display_payload$title, "Model complexity audit"),
      subtitle = lidocaine_curve_subtitle(display_payload, "Performance and stability review"),
      x = "Metric value",
      y = NULL
    ) +
    lidocaine_publication_theme(display_payload) +
    theme(strip.text = element_text(hjust = 0), panel.spacing.y = unit(7, "pt"))
}
