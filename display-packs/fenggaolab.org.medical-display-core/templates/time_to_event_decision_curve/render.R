#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
request_path <- Sys.getenv("MAS_DISPLAY_RENDER_REQUEST", unset = "")
if (length(args) == 2 && identical(args[[1]], "--request")) {
  request_path <- args[[2]]
}
if (!nzchar(request_path)) {
  stop("expected --request <request_json> or MAS_DISPLAY_RENDER_REQUEST")
}
old_source_only <- Sys.getenv("MAS_DISPLAY_RENDERER_SOURCE_ONLY", unset = "")
Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = "1")
source(file.path("..", "..", "rlib", "medicaldisplaycore", "evidence_renderer.R"))
source(file.path("..", "..", "rlib", "medicaldisplaycore", "candidate_renderer.R"))
if (nzchar(old_source_only)) {
  Sys.setenv(MAS_DISPLAY_RENDERER_SOURCE_ONLY = old_source_only)
} else {
  Sys.unsetenv("MAS_DISPLAY_RENDERER_SOURCE_ONLY")
}
render_evidence_request(request_path, expected_template_id = "time_to_event_decision_curve")
