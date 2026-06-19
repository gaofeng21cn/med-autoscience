from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def test_core_r_helper_consumes_publication_style_profile_tokens() -> None:
    assert shutil.which("Rscript") is not None
    repo_root = Path(__file__).resolve().parents[1]
    r_script = """
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/evidence_renderer.R")
source("display-packs/fenggaolab.org.medical-display-core/rlib/medicaldisplaycore/candidate_renderer.R")
payload <- list(
  title = "Probe",
  x_label = "x",
  y_label = "y",
  series = list(
    list(label = "Model", x = list(0, 1), y = list(0, 1)),
    list(label = "Comparator", x = list(0, 1), y = list(0, 0.8))
  ),
    reference_line = list(x = list(0, 1), y = list(0, 1)),
  render_context = list(
    style_profile_id = "probe",
    style_profile_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    palette = list(primary = "#123456", secondary = "#654321", neutral = "#999999", text = "#111111", grid = "#EEEEEE", heatmap_seq_low = "#F4F8FA", heatmap_seq_mid = "#9DD2D3", heatmap_seq_high = "#0B4F6C", heatmap_low = "#2B6CB0", heatmap_mid = "#F7F7F7", heatmap_high = "#B64342"),
    semantic_roles = list(model_curve = "primary", comparator_curve = "secondary", reference_line = "neutral", text = "text", grid_line = "grid", heatmap_seq_low = "heatmap_seq_low", heatmap_seq_mid = "heatmap_seq_mid", heatmap_seq_high = "heatmap_seq_high", heatmap_low = "heatmap_low", heatmap_mid = "heatmap_mid", heatmap_high = "heatmap_high"),
    style_roles = list(model_curve = "#123456", comparator_curve = "#654321", reference_line = "#999999", text = "#111111", grid_line = "#EEEEEE", heatmap_seq_low = "#F4F8FA", heatmap_seq_mid = "#9DD2D3", heatmap_seq_high = "#0B4F6C", heatmap_low = "#2B6CB0", heatmap_mid = "#F7F7F7", heatmap_high = "#B64342"),
    typography = list(font_family = "sans", base_size = 10, title_size = 13, axis_title_size = 11, tick_size = 9, legend_size = 7.2, colorbar_width = 5, colorbar_height = 42),
    stroke = list(primary_linewidth = 2.4, reference_linewidth = 1.2, grid_linewidth = 0.33),
    grid = list(major = TRUE, minor = FALSE, major_axis = "both", color = "#EEEEEE")
  )
)
plot <- build_evidence_plot("roc_curve_binary", payload)
built <- ggplot2::ggplot_build(plot)
stopifnot("#123456" %in% built$data[[1]]$colour)
stopifnot("#999999" %in% built$data[[2]]$colour)
theme_obj <- theme_publication(payload)
stopifnot(identical(theme_obj$plot.title$colour, "#111111"))
stopifnot(isTRUE(abs(theme_obj$panel.grid.major.x$linewidth - 0.33) < 1e-9))
layout <- build_layout_sidecar(plot, "roc_curve_binary", payload)
stopifnot(identical(layout$render_context$style_profile_id, "probe"))
stopifnot(identical(layout$style_profile$style_profile_sha256, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))
candidate_plot <- build_candidate_evidence_plot("time_to_event_decision_curve", payload)
candidate_built <- ggplot2::ggplot_build(candidate_plot)
stopifnot("#123456" %in% candidate_built$data[[1]]$colour)
heatmap_payload <- payload
heatmap_payload$cells <- list(
  list(x = "A", y = "Row 1", value = 0.10),
  list(x = "B", y = "Row 1", value = 0.45),
  list(x = "A", y = "Row 2", value = 0.70),
  list(x = "B", y = "Row 2", value = 0.95)
)
heatmap_payload$column_order <- list(list(label = "A"), list(label = "B"))
heatmap_payload$row_order <- list(list(label = "Row 1"), list(label = "Row 2"))
heatmap_plot <- build_evidence_plot("heatmap_group_comparison", heatmap_payload)
heatmap_built <- ggplot2::ggplot_build(heatmap_plot)
stopifnot("#0B4F6C" %in% heatmap_built$plot$scales$scales[[2]]$palette(1))
stopifnot(!("#B64342" %in% heatmap_built$data[[1]]$fill))
heatmap_layout <- build_layout_sidecar(heatmap_plot, "heatmap_group_comparison", heatmap_payload)
stopifnot(any(vapply(heatmap_layout$guide_boxes, function(item) identical(item$box_type, "colorbar"), logical(1))))
breaks <- continuous_scale_breaks(c(0.10, 0.45, 0.70, 0.95), max_breaks = 4)
stopifnot(length(breaks) <= 4)
stopifnot(publication_legend_guides(payload, c("a", "b", "c", "d"))$nrow == 2)
"""

    result = subprocess.run(
        ["Rscript", "-e", r_script],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
