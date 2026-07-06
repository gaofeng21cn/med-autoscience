from __future__ import annotations

from .common import (
    CORE_PACK_MODULE_ROOT,
    CORE_PACK_ROOT,
    CORE_PACK_SRC_ROOT,
    REPO_ROOT,
    SimpleNamespace,
    _candidate_request,
    importlib,
    json,
    os,
    subprocess,
    sys,
    tempfile,
    tomllib,
    Path,
)


def test_embedding_templates_use_feature_matrix_workflow_schema() -> None:
    expected = {
        "pca_scatter_grouped": "dimensionality_reduction_inputs_v1",
        "tsne_scatter_grouped": "dimensionality_reduction_inputs_v1",
        "umap_scatter_grouped": "dimensionality_reduction_inputs_v1",
    }

    for template_id, expected_schema in expected.items():
        payload = tomllib.loads((CORE_PACK_ROOT / "templates" / template_id / "template.toml").read_text(encoding="utf-8"))
        assert payload["input_schema_ref"] == expected_schema


def test_r_embedding_renderer_computes_pca_from_feature_matrix_without_reusing_points() -> None:
    r_script = r"""
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
core_pack_root <- normalizePath(Sys.getenv("MAS_CORE_DISPLAY_PACK_ROOT"), mustWork = TRUE)
source(file.path(core_pack_root, "rlib/medicaldisplaycore/evidence_renderer.R"))
payload <- list(
  title = "PCA probe",
  x_label = "PC1",
  y_label = "PC2",
  embedding_input_mode = "feature_matrix",
  source_feature_matrix_digest = "test-matrix",
  feature_matrix = list(
    list(sample_id = "S1", group = "A", features = list(f1 = -1.2, f2 = 0.6, f3 = -0.4)),
    list(sample_id = "S2", group = "A", features = list(f1 = -0.9, f2 = 0.4, f3 = -0.3)),
    list(sample_id = "S3", group = "B", features = list(f1 = 0.8, f2 = -0.5, f3 = 0.5)),
    list(sample_id = "S4", group = "B", features = list(f1 = 1.1, f2 = -0.7, f3 = 0.7))
  ),
  points = list(
    list(sample_id = "S1", x = 100, y = 100, group = "A"),
    list(sample_id = "S2", x = 100, y = 100, group = "A"),
    list(sample_id = "S3", x = 100, y = 100, group = "B"),
    list(sample_id = "S4", x = 100, y = 100, group = "B")
  )
)
plot <- build_evidence_plot("pca_scatter_grouped", payload)
built <- ggplot2::ggplot_build(plot)
stopifnot(!all(abs(built$data[[1]]$x - 100) < 1e-9))
metrics <- build_dimensionality_reduction_metrics(
  "pca_scatter_grouped",
  payload,
  list(x0 = 0.1, y0 = 0.1, x1 = 0.9, y1 = 0.9)
)
stopifnot(identical(metrics$embedding_method, "pca"))
stopifnot(identical(metrics$embedding_backend, "stats::prcomp"))
stopifnot(identical(metrics$embedding_input_mode, "feature_matrix"))
stopifnot(identical(metrics$source_feature_matrix_digest, "test-matrix"))
stopifnot(identical(metrics$analysis_provenance$sample_count, 4L))
stopifnot(identical(metrics$analysis_provenance$feature_count, 3L))
"""

    result = subprocess.run(
        ["Rscript", "-e", r_script],
        cwd=REPO_ROOT,
        env={**os.environ, "MAS_CORE_DISPLAY_PACK_ROOT": str(CORE_PACK_ROOT)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr


def test_r_embedding_renderer_requires_real_tsne_and_umap_backends() -> None:
    r_script = r"""
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
core_pack_root <- normalizePath(Sys.getenv("MAS_CORE_DISPLAY_PACK_ROOT"), mustWork = TRUE)
source(file.path(core_pack_root, "rlib/medicaldisplaycore/evidence_renderer.R"))
payload <- list(
  title = "Embedding probe",
  x_label = "x",
  y_label = "y",
  embedding_input_mode = "feature_matrix",
  feature_matrix = list(
    list(sample_id = "S1", group = "A", features = list(f1 = -1.2, f2 = 0.6, f3 = -0.4)),
    list(sample_id = "S2", group = "A", features = list(f1 = -0.9, f2 = 0.4, f3 = -0.3)),
    list(sample_id = "S3", group = "B", features = list(f1 = 0.8, f2 = -0.5, f3 = 0.5)),
    list(sample_id = "S4", group = "B", features = list(f1 = 1.1, f2 = -0.7, f3 = 0.7))
  )
)
if (!requireNamespace("Rtsne", quietly = TRUE)) {
  err <- tryCatch({ build_evidence_plot("tsne_scatter_grouped", payload); "" }, error = function(e) conditionMessage(e))
  stopifnot(grepl("Rtsne", err, fixed = TRUE))
}
if (!requireNamespace("uwot", quietly = TRUE)) {
  err <- tryCatch({ build_evidence_plot("umap_scatter_grouped", payload); "" }, error = function(e) conditionMessage(e))
  stopifnot(grepl("uwot", err, fixed = TRUE))
}
"""

    result = subprocess.run(
        ["Rscript", "-e", r_script],
        cwd=REPO_ROOT,
        env={**os.environ, "MAS_CORE_DISPLAY_PACK_ROOT": str(CORE_PACK_ROOT)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr


def test_publication_embedding_gallery_payload_drives_distinct_reduction_workflows() -> None:
    from med_autoscience.display_pack_gallery_parts.publication_payloads import PUBLICATION_R_DISPLAY_PAYLOADS

    payloads = {
        key: PUBLICATION_R_DISPLAY_PAYLOADS[key]
        for key in ("pca_scatter_grouped", "tsne_scatter_grouped", "umap_scatter_grouped")
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        payload_path = Path(tmpdir) / "embedding_payloads.json"
        payload_path.write_text(json.dumps(payloads), encoding="utf-8")
        r_script = """
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
core_pack_root <- normalizePath(Sys.getenv("MAS_CORE_DISPLAY_PACK_ROOT"), mustWork = TRUE)
source(file.path(core_pack_root, "rlib/medicaldisplaycore/evidence_renderer.R"))
med_autoscience_payloads <- jsonlite::fromJSON("__PAYLOAD_PATH__", simplifyVector = FALSE)
pca_payload <- med_autoscience_payloads$pca_scatter_grouped
tsne_payload <- med_autoscience_payloads$tsne_scatter_grouped
umap_payload <- med_autoscience_payloads$umap_scatter_grouped
stopifnot(is.null(pca_payload$points))
stopifnot(is.null(tsne_payload$points))
stopifnot(is.null(umap_payload$points))
stopifnot(identical(pca_payload$source_feature_matrix_digest, tsne_payload$source_feature_matrix_digest))
stopifnot(identical(pca_payload$source_feature_matrix_digest, umap_payload$source_feature_matrix_digest))
stopifnot(length(pca_payload$feature_matrix) == length(tsne_payload$feature_matrix))
stopifnot(length(pca_payload$feature_matrix) == length(umap_payload$feature_matrix))

if (requireNamespace("Rtsne", quietly = TRUE) && requireNamespace("uwot", quietly = TRUE)) {
  pca <- compute_embedding_result("pca_scatter_grouped", pca_payload)
  tsne <- compute_embedding_result("tsne_scatter_grouped", tsne_payload)
  umap <- compute_embedding_result("umap_scatter_grouped", umap_payload)
  stopifnot(identical(pca$provenance$backend, "stats::prcomp"))
  stopifnot(identical(tsne$provenance$backend, "Rtsne::Rtsne"))
  stopifnot(identical(umap$provenance$backend, "uwot::umap"))
  pca_xy <- round(as.matrix(pca$points[, c("x", "y")]), 6)
  tsne_xy <- round(as.matrix(tsne$points[, c("x", "y")]), 6)
  umap_xy <- round(as.matrix(umap$points[, c("x", "y")]), 6)
  stopifnot(!identical(pca_xy, tsne_xy))
  stopifnot(!identical(pca_xy, umap_xy))
  stopifnot(!identical(tsne_xy, umap_xy))
}
""".replace("__PAYLOAD_PATH__", payload_path.as_posix())

        result = subprocess.run(
            ["Rscript", "-e", r_script],
            cwd=REPO_ROOT,
            env={**os.environ, "MAS_CORE_DISPLAY_PACK_ROOT": str(CORE_PACK_ROOT)},
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )

    assert result.returncode == 0, result.stderr


def test_embedding_layout_sidecar_preserves_nonzero_panel_and_point_positions() -> None:
    from med_autoscience.display_pack_gallery_parts.publication_payloads import PUBLICATION_R_DISPLAY_PAYLOADS

    payload = PUBLICATION_R_DISPLAY_PAYLOADS["pca_scatter_grouped"]
    with tempfile.TemporaryDirectory() as tmpdir:
        payload_path = Path(tmpdir) / "pca_payload.json"
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        r_script = """
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
core_pack_root <- normalizePath(Sys.getenv("MAS_CORE_DISPLAY_PACK_ROOT"), mustWork = TRUE)
source(file.path(core_pack_root, "rlib/medicaldisplaycore/evidence_renderer.R"))
payload <- jsonlite::fromJSON("__PAYLOAD_PATH__", simplifyVector = FALSE)
plot <- build_evidence_plot("pca_scatter_grouped", payload)
sidecar <- build_layout_sidecar(plot, "pca_scatter_grouped", payload)
panel <- sidecar$panel_boxes[[1]]
stopifnot((panel$x1 - panel$x0) > 0.5)
stopifnot((panel$y1 - panel$y0) > 0.5)
point_keys <- vapply(
  sidecar$metrics$points,
  function(point) paste(round(point$x, 4), round(point$y, 4)),
  character(1)
)
stopifnot(length(unique(point_keys)) == length(point_keys))
""".replace("__PAYLOAD_PATH__", payload_path.as_posix())

        result = subprocess.run(
            ["Rscript", "-e", r_script],
            cwd=REPO_ROOT,
            env={**os.environ, "MAS_CORE_DISPLAY_PACK_ROOT": str(CORE_PACK_ROOT)},
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )

    assert result.returncode == 0, result.stderr
