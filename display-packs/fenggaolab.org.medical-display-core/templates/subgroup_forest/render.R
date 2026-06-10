#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
request_path <- Sys.getenv("MAS_DISPLAY_RENDER_REQUEST", unset = "")
if (length(args) == 2 && identical(args[[1]], "--request")) {
  request_path <- args[[2]]
}
if (!nzchar(request_path)) {
  stop("expected --request <request_json> or MAS_DISPLAY_RENDER_REQUEST")
}
source(file.path("..", "..", "rlib", "medicaldisplaycore", "evidence_renderer.R"))
render_evidence_request(request_path, expected_template_id = "subgroup_forest")
