embedding_template_method <- function(template_id) {
  switch(
    template_id,
    pca_scatter_grouped = "pca",
    tsne_scatter_grouped = "tsne",
    umap_scatter_grouped = "umap",
    stop(sprintf("unsupported embedding template `%s`", template_id))
  )
}

embedding_method_labels <- function(method) {
  switch(
    method,
    pca = list(title = "PCA", x = "PC1", y = "PC2"),
    tsne = list(title = "t-SNE", x = "t-SNE 1", y = "t-SNE 2"),
    umap = list(title = "UMAP", x = "UMAP 1", y = "UMAP 2"),
    stop(sprintf("unsupported embedding method `%s`", method))
  )
}

embedding_input_mode <- function(display_payload) {
  mode <- tolower(trimws(as.character(display_payload$embedding_input_mode %||% "")))
  if (!nzchar(mode)) {
    mode <- if (!is.null(display_payload$feature_matrix)) "feature_matrix" else "precomputed"
  }
  if (!(mode %in% c("feature_matrix", "precomputed"))) {
    stop("embedding_input_mode must be `feature_matrix` or `precomputed`")
  }
  mode
}

embedding_numeric_option <- function(display_payload, key, fallback) {
  options <- display_payload$embedding_options %||% list()
  value <- options[[key]]
  if (is.null(value)) {
    value <- display_payload[[key]]
  }
  if (is.null(value)) {
    return(as.numeric(fallback))
  }
  numeric_value <- suppressWarnings(as.numeric(value))
  if (!is.finite(numeric_value)) as.numeric(fallback) else numeric_value
}

embedding_integer_option <- function(display_payload, key, fallback) {
  as.integer(round(embedding_numeric_option(display_payload, key, fallback)))
}

embedding_logical_option <- function(display_payload, key, fallback) {
  options <- display_payload$embedding_options %||% list()
  value <- options[[key]]
  if (is.null(value)) {
    value <- display_payload[[key]]
  }
  if (is.null(value)) {
    return(isTRUE(fallback))
  }
  if (is.logical(value)) {
    return(isTRUE(value))
  }
  tolower(trimws(as.character(value))) %in% c("true", "1", "yes", "on")
}

embedding_string_option <- function(display_payload, key, fallback) {
  options <- display_payload$embedding_options %||% list()
  value <- options[[key]]
  if (is.null(value)) {
    value <- display_payload[[key]]
  }
  text <- trimws(as.character(value %||% ""))
  if (!nzchar(text)) fallback else text
}

embedding_seed <- function(display_payload, method) {
  embedding_integer_option(
    display_payload,
    "seed",
    switch(method, pca = 0, tsne = 42, umap = 42)
  )
}

embedding_require_package <- function(package, method) {
  if (!requireNamespace(package, quietly = TRUE)) {
    stop(sprintf(
      "%s embedding requires R package `%s`; install it or provide explicit precomputed coordinates with embedding_input_mode=`precomputed`",
      method,
      package
    ))
  }
}

feature_matrix_dataframe <- function(display_payload) {
  rows <- display_payload$feature_matrix
  if (!is.list(rows) || length(rows) < 3) {
    stop("feature_matrix must contain at least three sample rows")
  }
  records <- lapply(seq_along(rows), function(index) {
    item <- rows[[index]]
    sample_id <- trimws(as.character(item$sample_id %||% item$id %||% sprintf("sample_%d", index)))
    group <- trimws(as.character(item$group %||% ""))
    features <- item$features
    if (!is.list(features) || length(features) < 2) {
      stop(sprintf("feature_matrix[%d].features must contain at least two numeric feature values", index))
    }
    feature_values <- vapply(features, function(value) {
      numeric_value <- suppressWarnings(as.numeric(value))
      if (!is.finite(numeric_value)) {
        stop(sprintf("feature_matrix[%d].features must contain only finite numeric values", index))
      }
      numeric_value
    }, numeric(1))
    list(sample_id = sample_id, group = group, features = feature_values)
  })
  feature_names <- names(records[[1]]$features)
  if (is.null(feature_names) || any(!nzchar(feature_names))) {
    feature_names <- paste0("feature_", seq_along(records[[1]]$features))
  }
  matrix_values <- do.call(rbind, lapply(seq_along(records), function(index) {
    values <- records[[index]]$features
    if (length(values) != length(feature_names)) {
      stop("all feature_matrix rows must contain the same number of features")
    }
    if (!is.null(names(values)) && any(nzchar(names(values)))) {
      missing <- setdiff(feature_names, names(values))
      extra <- setdiff(names(values), feature_names)
      if (length(missing) || length(extra)) {
        stop("all feature_matrix rows must contain the same named features")
      }
      values <- values[feature_names]
    }
    as.numeric(values)
  }))
  colnames(matrix_values) <- feature_names
  rownames(matrix_values) <- vapply(records, function(item) item$sample_id, character(1))
  groups <- vapply(records, function(item) item$group, character(1))
  if (any(!nzchar(groups))) {
    stop("feature_matrix rows must include non-empty group labels")
  }
  list(
    matrix = matrix_values,
    samples = data.frame(
      sample_id = rownames(matrix_values),
      group = groups,
      stringsAsFactors = FALSE
    ),
    feature_names = feature_names
  )
}

embedding_pca_points <- function(display_payload) {
  data <- feature_matrix_dataframe(display_payload)
  center <- embedding_logical_option(display_payload, "center", TRUE)
  scale_features <- embedding_logical_option(display_payload, "scale", TRUE)
  fit <- stats::prcomp(data$matrix, center = center, scale. = scale_features, retx = TRUE)
  if (ncol(fit$x) < 2) {
    stop("PCA requires at least two principal components")
  }
  variance <- (fit$sdev^2) / sum(fit$sdev^2)
  list(
    points = data.frame(
      sample_id = data$samples$sample_id,
      x = as.numeric(fit$x[, 1]),
      y = as.numeric(fit$x[, 2]),
      group = data$samples$group,
      stringsAsFactors = FALSE
    ),
    provenance = list(
      method = "pca",
      backend = "stats::prcomp",
      input_mode = "feature_matrix",
      sample_count = nrow(data$matrix),
      feature_count = ncol(data$matrix),
      explained_variance = list(
        component_1 = round(as.numeric(variance[[1]]), 6),
        component_2 = round(as.numeric(variance[[2]]), 6)
      ),
      center = center,
      scale = scale_features
    )
  )
}

embedding_tsne_points <- function(display_payload) {
  embedding_require_package("Rtsne", "t-SNE")
  data <- feature_matrix_dataframe(display_payload)
  seed <- embedding_seed(display_payload, "tsne")
  perplexity <- embedding_numeric_option(display_payload, "perplexity", min(30, floor((nrow(data$matrix) - 1) / 3)))
  max_perplexity <- max(1, floor((nrow(data$matrix) - 2) / 3))
  perplexity <- min(perplexity, max_perplexity)
  theta <- embedding_numeric_option(display_payload, "theta", 0.5)
  max_iter <- embedding_integer_option(display_payload, "max_iter", 1000)
  initial_dims <- min(ncol(data$matrix), embedding_integer_option(display_payload, "initial_dims", 50))
  set.seed(seed)
  fit <- Rtsne::Rtsne(
    data$matrix,
    dims = 2,
    initial_dims = initial_dims,
    perplexity = perplexity,
    theta = theta,
    max_iter = max_iter,
    pca = TRUE,
    check_duplicates = FALSE,
    verbose = FALSE
  )
  list(
    points = data.frame(
      sample_id = data$samples$sample_id,
      x = as.numeric(fit$Y[, 1]),
      y = as.numeric(fit$Y[, 2]),
      group = data$samples$group,
      stringsAsFactors = FALSE
    ),
    provenance = list(
      method = "tsne",
      backend = "Rtsne::Rtsne",
      input_mode = "feature_matrix",
      sample_count = nrow(data$matrix),
      feature_count = ncol(data$matrix),
      seed = seed,
      perplexity = perplexity,
      theta = theta,
      max_iter = max_iter,
      initial_dims = initial_dims
    )
  )
}

embedding_umap_points <- function(display_payload) {
  embedding_require_package("uwot", "UMAP")
  data <- feature_matrix_dataframe(display_payload)
  seed <- embedding_seed(display_payload, "umap")
  n_neighbors <- embedding_integer_option(display_payload, "n_neighbors", min(15, nrow(data$matrix) - 1))
  n_neighbors <- min(max(2, n_neighbors), nrow(data$matrix) - 1)
  min_dist <- embedding_numeric_option(display_payload, "min_dist", 0.1)
  metric <- embedding_string_option(display_payload, "metric", "euclidean")
  set.seed(seed)
  fit <- uwot::umap(
    data$matrix,
    n_neighbors = n_neighbors,
    n_components = 2,
    metric = metric,
    min_dist = min_dist,
    scale = TRUE,
    ret_model = FALSE,
    verbose = FALSE
  )
  list(
    points = data.frame(
      sample_id = data$samples$sample_id,
      x = as.numeric(fit[, 1]),
      y = as.numeric(fit[, 2]),
      group = data$samples$group,
      stringsAsFactors = FALSE
    ),
    provenance = list(
      method = "umap",
      backend = "uwot::umap",
      input_mode = "feature_matrix",
      sample_count = nrow(data$matrix),
      feature_count = ncol(data$matrix),
      seed = seed,
      n_neighbors = n_neighbors,
      min_dist = min_dist,
      metric = metric
    )
  )
}

precomputed_embedding_points <- function(display_payload, method) {
  points_payload <- display_payload$points
  if (!is.list(points_payload) || length(points_payload) < 1) {
    stop("precomputed embedding payloads must contain non-empty points")
  }
  point_df <- build_point_dataframe(points_payload)
  list(
    points = point_df,
    provenance = list(
      method = method,
      backend = "precomputed_coordinates",
      input_mode = "precomputed",
      sample_count = nrow(point_df),
      feature_count = NULL
    )
  )
}

compute_embedding_result <- function(template_id, display_payload) {
  method <- embedding_template_method(template_id)
  mode <- embedding_input_mode(display_payload)
  result <- if (identical(mode, "precomputed")) {
    precomputed_embedding_points(display_payload, method)
  } else {
    switch(
      method,
      pca = embedding_pca_points(display_payload),
      tsne = embedding_tsne_points(display_payload),
      umap = embedding_umap_points(display_payload)
    )
  }
  labels <- embedding_method_labels(method)
  result$labels <- labels
  result
}

plot_dimensionality_reduction_embedding <- function(template_id, display_payload) {
  result <- compute_embedding_result(template_id, display_payload)
  point_df <- result$points
  ggplot(point_df, aes(x = x, y = y, colour = group)) +
    geom_point(size = style_numeric(style_stroke(display_payload), "marker_size", 4.5) * 0.62, alpha = 0.9) +
    scale_color_manual(
      values = style_series_palette(display_payload, unique(point_df$group)),
      guide = publication_legend_guides(display_payload, point_df$group)
    ) +
    labs(
      title = trimws(as.character(display_payload$title %||% "")),
      x = trimws(as.character(display_payload$x_label %||% result$labels$x)),
      y = trimws(as.character(display_payload$y_label %||% result$labels$y))
    ) +
    theme_publication(display_payload)
}

embedding_point_metrics <- function(point_df, panel_box) {
  x_values <- as.numeric(point_df$x)
  y_values <- as.numeric(point_df$y)
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
  lapply(seq_len(nrow(point_df)), function(index) {
    list(
      sample_id = trimws(as.character(point_df$sample_id[[index]] %||% "")),
      x = map_value_to_panel_x(as.numeric(point_df$x[[index]]), panel_box, x_min, x_max),
      y = panel_box$y0 + ((as.numeric(point_df$y[[index]]) - y_min) / (y_max - y_min)) * (panel_box$y1 - panel_box$y0),
      group = trimws(as.character(point_df$group[[index]] %||% ""))
    )
  })
}

build_dimensionality_reduction_metrics <- function(template_id, display_payload, panel_box) {
  if (is.null(panel_box)) {
    return(list(points = list()))
  }
  result <- compute_embedding_result(template_id, display_payload)
  list(
    points = embedding_point_metrics(result$points, panel_box),
    embedding_method = result$provenance$method,
    embedding_backend = result$provenance$backend,
    embedding_input_mode = result$provenance$input_mode,
    source_feature_matrix_digest = trimws(as.character(display_payload$source_feature_matrix_digest %||% "")),
    analysis_provenance = result$provenance
  )
}
