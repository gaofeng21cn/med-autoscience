from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_display_pack_config(repo_root: Path) -> None:
    (repo_root / "config").mkdir(parents=True)
    (repo_root / "config" / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "external/display-packs/medical-display-core"
version = "0.3.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_renderable_pack(repo_root: Path) -> None:
    pack_root = repo_root / "external" / "display-packs" / "medical-display-core"
    template_root = pack_root / "templates" / "roc_curve_binary"
    template_root.mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                'version = "0.3.0"',
                'display_api_version = "1"',
                'default_execution_mode = "subprocess"',
                'summary = "E2E renderable test pack"',
                'maintainer = "MAS tests"',
                'license = "MIT"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve"',
                'paper_family_ids = ["A"]',
                'audit_family = "Prediction Performance"',
                'renderer_family = "r_ggplot2"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'style_profile_ref = "paper_neutral_clinical_v1"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "subprocess"',
                f'entrypoint = "{sys.executable} render_subprocess.py --request {{request_json}}"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "render_subprocess.py").write_text(
        """
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    panel_ids = [str(item.get("panel_id") or "").strip() for item in request["display_payload"].get("panels", [])]
    panel_ids = [item for item in panel_ids if item]
    rendered_panel_ids = panel_ids if len(panel_ids) == 1 else []
    output_png_path = Path(request["output_png_path"])
    output_pdf_path = Path(request["output_pdf_path"])
    layout_sidecar_path = Path(request["layout_sidecar_path"])
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    layout_sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    output_png_path.write_text("PNG:" + request["template_id"], encoding="utf-8")
    output_pdf_path.write_text("%PDF:" + request["template_id"], encoding="utf-8")
    layout_sidecar_path.write_text(
        json.dumps(
            {
                "template_id": "roc_curve_binary",
                "device": {"width": 10.0, "height": 8.0},
                "layout_boxes": [
                    {"box_id": "title", "box_type": "title", "x0": 1.0, "y0": 0.1, "x1": 8.8, "y1": 0.55},
                    {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.2, "y0": 2.0, "x1": 0.7, "y1": 6.0},
                    {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 3.0, "y0": 7.2, "x1": 7.0, "y1": 7.7},
                ],
                "panel_boxes": [
                    {
                        "box_id": "panel",
                        "box_type": "panel",
                        "panel_id": rendered_panel_ids[0] if rendered_panel_ids else "",
                        "x0": 1.2,
                        "y0": 1.0,
                        "x1": 8.0,
                        "y1": 6.7,
                    }
                ],
                "guide_boxes": [
                    {"box_id": "legend", "box_type": "legend", "x0": 8.2, "y0": 1.0, "x1": 9.7, "y1": 2.0}
                ],
                "metrics": {
                    "series": [{"x": [0.0, 0.4, 1.0], "y": [0.0, 0.82, 1.0]}],
                    "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                    "panel_ids": rendered_panel_ids,
                },
                "render_context": request["display_payload"]["render_context"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\\n",
        encoding="utf-8",
    )
    print(json.dumps({"renderer": "subprocess", "figure_id": request["figure_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_subprocess_renderable_template(repo_root: Path) -> None:
    pack_root = repo_root / "external" / "display-packs" / "medical-display-core"
    template_root = pack_root / "templates" / "roc_curve_binary_ggplot2"
    template_root.mkdir(parents=True)
    (template_root / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary_ggplot2"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve (R/ggplot2 subprocess)"',
                'paper_family_ids = ["A"]',
                'audit_family = "Prediction Performance"',
                'renderer_family = "r_ggplot2"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'style_profile_ref = "paper_neutral_clinical_v1"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "subprocess"',
                f'entrypoint = "{sys.executable} render_subprocess.py --request {{request_json}}"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (template_root / "render_subprocess.py").write_text(
        """
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    panel_ids = [str(item.get("panel_id") or "").strip() for item in request["display_payload"].get("panels", [])]
    panel_ids = [item for item in panel_ids if item]
    rendered_panel_ids = panel_ids if len(panel_ids) == 1 else []
    output_png_path = Path(request["output_png_path"])
    output_pdf_path = Path(request["output_pdf_path"])
    layout_sidecar_path = Path(request["layout_sidecar_path"])
    for path in (output_png_path, output_pdf_path, layout_sidecar_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    output_png_path.write_text("PNG:subprocess:" + request["template_id"], encoding="utf-8")
    output_pdf_path.write_text("%PDF:subprocess:" + request["template_id"], encoding="utf-8")
    layout_sidecar_path.write_text(
        json.dumps(
            {
                "template_id": "roc_curve_binary_ggplot2",
                "device": {"width": 10.0, "height": 8.0},
                "layout_boxes": [
                    {"box_id": "title", "box_type": "title", "x0": 1.0, "y0": 0.1, "x1": 8.8, "y1": 0.55},
                    {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.2, "y0": 2.0, "x1": 0.7, "y1": 6.0},
                    {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 3.0, "y0": 7.2, "x1": 7.0, "y1": 7.7},
                ],
                "panel_boxes": [
                    {
                        "box_id": "panel",
                        "box_type": "panel",
                        "panel_id": rendered_panel_ids[0] if rendered_panel_ids else "",
                        "x0": 1.2,
                        "y0": 1.0,
                        "x1": 8.0,
                        "y1": 6.7,
                    }
                ],
                "guide_boxes": [
                    {"box_id": "legend", "box_type": "legend", "x0": 8.2, "y0": 1.0, "x1": 9.7, "y1": 2.0}
                ],
                "metrics": {
                    "series": [{"x": [0.0, 0.4, 1.0], "y": [0.0, 0.82, 1.0]}],
                    "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
                    "panel_ids": rendered_panel_ids,
                },
                "render_context": request["display_payload"]["render_context"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\\n",
        encoding="utf-8",
    )
    print(json.dumps({"renderer": "subprocess", "figure_id": request["figure_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_paper_inputs(paper_root: Path) -> None:
    _write_json(
        paper_root / "data" / "frozen" / "primary_curve.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-primary",
            "series": [{"x": [0.0, 0.4, 1.0], "y": [0.0, 0.82, 1.0]}],
        },
    )
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "claim_ref": "claim:primary-discrimination",
                    "data_ref": "paper/data/frozen/primary_curve.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                    "statistical_value_refs": ["analysis/statistics/auc_primary"],
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
        {
            "schema_version": 1,
            "figure_id": "F1",
            "intent_ref": "paper/figure_intent.json#/figures/F1",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/derivation",
                "endpoint_ref": "endpoint:mace",
                "model_ref": "model:cox-primary",
                "risk_horizon": "5y",
                "effect_estimate_ref": "analysis/statistics/auc_primary",
                "claim_role": "primary_evidence",
            },
            "panels": [
                {
                    "panel_id": "A",
                    "data_role": "discrimination",
                    "mark_role": "roc_curve",
                }
            ],
        },
    )
    _write_json(
        paper_root / "publication_style_profile.json",
        {
            "schema_version": 1,
            "style_profile_id": "paper_neutral_clinical_v1",
            "journal_palette_ref": "large_journal_safe_lancet_like_v1",
            "palette": {
                "primary": "#245A6B",
                "secondary": "#B89A6D",
                "neutral": "#6B7280",
                "text": "#102A43",
                "grid": "#D9E2EC",
                "background": "#FFFFFF",
                "heatmap_low": "#2166AC",
                "heatmap_mid": "#FFFFFF",
                "heatmap_high": "#B2182B",
            },
            "semantic_roles": {
                "model_curve": "primary",
                "comparator_curve": "secondary",
                "reference_line": "neutral",
                "text": "text",
                "grid_line": "grid",
                "figure_background": "background",
                "heatmap_low": "heatmap_low",
                "heatmap_mid": "heatmap_mid",
                "heatmap_high": "heatmap_high",
            },
            "typography": {
                "font_family": "sans",
                "base_size": 10.5,
                "title_size": 12.0,
                "axis_title_size": 10.8,
                "tick_size": 9.5,
                "legend_size": 9.2,
                "panel_label_size": 10.8,
            },
            "stroke": {
                "primary_linewidth": 2.0,
                "secondary_linewidth": 1.6,
                "reference_linewidth": 1.1,
                "grid_linewidth": 0.35,
                "marker_size": 4.2,
            },
            "grid": {
                "major": True,
                "minor": False,
                "major_axis": "both",
                "minor_axis": "none",
                "color": "#D9E2EC",
                "linetype": "solid",
            },
        },
    )
    _write_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_style_reference_bundle.json",
        {
            "schema_version": 1,
            "bundle_id": "lab-display-style-v1",
            "references": [
                {
                    "reference_id": "reference-roc",
                    "source_ref": "https://example.org/reference-paper",
                    "decision": "adopt",
                    "applies_to": ["fenggaolab.org.medical-display-core::roc_curve_binary"],
                    "style_notes": ["compact legend", "print-safe neutral reference line"],
                }
            ],
        },
    )


def _write_real_core_r_paper_inputs(paper_root: Path) -> None:
    _write_paper_inputs(paper_root)
    _write_json(
        paper_root / "data" / "frozen" / "primary_curve.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-primary",
            "title": "Primary ROC",
            "x_label": "1 - Specificity",
            "y_label": "Sensitivity",
            "series": [
                {
                    "label": "Primary model",
                    "x": [0.0, 0.2, 0.6, 1.0],
                    "y": [0.0, 0.72, 0.9, 1.0],
                },
                {
                    "label": "Comparator",
                    "x": [0.0, 0.3, 0.7, 1.0],
                    "y": [0.0, 0.58, 0.82, 1.0],
                },
            ],
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
        },
    )


def _write_cohort_flow_paper_inputs(paper_root: Path) -> None:
    _write_real_core_r_paper_inputs(paper_root)
    style_profile_path = paper_root / "publication_style_profile.json"
    style_profile = json.loads(style_profile_path.read_text(encoding="utf-8"))
    style_profile["palette"].update(
        {
            "light": "#F2F5F7",
            "primary_soft": "#D9EAF0",
            "secondary_soft": "#D8F0EB",
            "contrast": "#2F5D8A",
            "contrast_soft": "#E6EDF5",
            "audit": "#B64342",
            "audit_soft": "#F6CFCB",
        }
    )
    style_profile["semantic_roles"].update(
        {
            "flow_main_fill": "light",
            "flow_main_edge": "neutral",
            "flow_exclusion_fill": "audit_soft",
            "flow_exclusion_edge": "audit",
            "flow_primary_fill": "primary_soft",
            "flow_primary_edge": "primary",
            "flow_secondary_fill": "light",
            "flow_secondary_edge": "neutral",
            "flow_context_fill": "contrast_soft",
            "flow_context_edge": "contrast",
            "flow_audit_fill": "audit_soft",
            "flow_audit_edge": "audit",
            "flow_title_text": "text",
            "flow_body_text": "text",
            "flow_panel_label": "text",
            "flow_connector": "neutral",
        }
    )
    _write_json(style_profile_path, style_profile)
    _write_json(
        paper_root / "data" / "frozen" / "cohort_flow.json",
        {
            "schema_version": 1,
            "source_data_digest": "data-digest-cohort-flow",
            "title": "Study participant flow",
            "steps": [
                {"step_id": "screened", "label": "Screened", "n": 1200},
                {"step_id": "eligible", "label": "Eligible", "n": 980},
                {"step_id": "analysis", "label": "Analysis cohort", "n": 842},
            ],
            "exclusions": [
                {
                    "exclusion_id": "missing_baseline",
                    "from_step_id": "screened",
                    "label": "Missing baseline data",
                    "n": 220,
                },
                {
                    "exclusion_id": "lost_followup",
                    "from_step_id": "eligible",
                    "label": "Lost to follow-up",
                    "n": 138,
                },
            ],
            "endpoint_inventory": [
                {"endpoint_id": "mace", "label": "MACE", "n_events": 86},
            ],
            "design_panels": [],
            "comparison_summary": [],
        },
    )
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F_cohort",
                    "claim_ref": "claim:cohort-flow",
                    "data_ref": "paper/data/frozen/cohort_flow.json",
                    "template_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
                    "figure_kind": "illustration_shell",
                    "statistical_value_refs": ["paper/data/frozen/cohort_flow.json#/source_data_digest"],
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
        {
            "schema_version": 1,
            "figure_id": "F_cohort",
            "intent_ref": "paper/figure_intent.json#/figures/F_cohort",
            "template_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
            "figure_kind": "illustration_shell",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/derivation",
                "endpoint_ref": "endpoint:mace",
                "risk_horizon": "5y",
                "claim_role": "participant_flow",
            },
            "panels": [{"panel_id": "A", "data_role": "participant_flow", "mark_role": "flow_diagram"}],
        },
    )


def _install_fake_ggconsort_package(tmp_path: Path) -> Path:
    package_root = tmp_path / "fake-ggconsort"
    library_root = tmp_path / "managed-r-library"
    (package_root / "R").mkdir(parents=True)
    library_root.mkdir(parents=True)
    (package_root / "DESCRIPTION").write_text(
        "\n".join(
            (
                "Package: ggconsort",
                "Type: Package",
                "Title: Offline MAS Test Double for ggconsort",
                "Version: 0.0.0.9000",
                "Description: Minimal namespace used by MAS dependency run-context tests.",
                "License: MIT",
                "Encoding: UTF-8",
                "Imports: ggplot2",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "NAMESPACE").write_text(
        "\n".join(
            (
                "export(cohort_start)",
                "export(cohort_define)",
                "export(cohort_label)",
                "export(consort_box_add)",
                "export(consort_arrow_add)",
                "export(geom_consort)",
                "export(theme_consort)",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "R" / "ggconsort.R").write_text(
        """
cohort_start <- function(data, name) {
  result <- data.frame(x = numeric(0), y = numeric(0), label = character(0), stringsAsFactors = FALSE)
  attr(result, "name") <- name
  attr(result, "cohort_names") <- c(".full")
  attr(result, "labels") <- list()
  attr(result, "arrows") <- list()
  result
}

cohort_define <- function(consort, ...) {
  exprs <- as.list(substitute(list(...)))[-1L]
  attr(consort, "cohort_names") <- unique(c(attr(consort, "cohort_names"), names(exprs)))
  consort
}

cohort_label <- function(consort, ...) {
  labels <- list(...)
  unknown <- setdiff(names(labels), attr(consort, "cohort_names"))
  if (length(unknown) > 0L) {
    stop(sprintf("Unknown cohort names: %s", paste(unknown, collapse = ", ")))
  }
  attr(consort, "labels") <- c(attr(consort, "labels"), labels)
  consort
}

consort_box_add <- function(consort, id, x, y, label) {
  rbind(
    consort,
    data.frame(x = as.numeric(x), y = as.numeric(y), label = as.character(label), stringsAsFactors = FALSE)
  )
}

consort_arrow_add <- function(consort, ...) {
  attr(consort, "arrows") <- c(attr(consort, "arrows"), list(list(...)))
  consort
}

geom_consort <- function(...) {
  ggplot2::geom_blank(ggplot2::aes(x = x, y = y))
}

theme_consort <- function(margin_h = 8, margin_v = 2, ...) {
  ggplot2::theme_void()
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    completed = shutil.which("R")
    assert completed is not None
    import subprocess

    install_result = subprocess.run(
        ["R", "CMD", "INSTALL", "--library", str(library_root), str(package_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert install_result.returncode == 0, install_result.stderr
    return library_root


def _write_fake_dependency_run_context(paper_root: Path, *, r_library_root: Path) -> dict[str, object]:
    fingerprint = "sha256:test-ggconsort-run-context"
    run_context_ref = "paper/build/dependency_run_context.json"
    build_root = paper_root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        build_root / "dependency_run_context.json",
        {
            "schema_version": 1,
            "run_context_id": "test-ggconsort-run-context",
            "execution_fingerprint": fingerprint,
            "argv_prefix": [],
            "env_vars": {
                "R_LIBS_USER": str(r_library_root),
                "MAS_TEST_DEPENDENCY_ENV": "fake_ggconsort_managed_library",
            },
            "binary_paths": {},
        },
    )
    return {
        "status": "prepared",
        "failure_class": "",
        "lock_ref": "paper/build/dependency_environment_lock.json",
        "environment_ref": "test-ggconsort-managed-r-library",
        "cache_key": "test-ggconsort-managed-r-library",
        "target_platform": "test-platform",
        "run_context_ref": run_context_ref,
        "run_context_fingerprint": fingerprint,
    }


def _visual_audit_review() -> dict[str, object]:
    return {
        "audit_mode": "human_visual_review",
        "reviewer": {
            "provider": "mas-test-reviewer",
            "model": "fixture-human-review",
            "prompt_hash": "d" * 64,
        },
        "findings": [],
        "final_status": "clear",
    }


def _build_workspace(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    paper_root = tmp_path / "workspace" / "paper"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    _write_renderable_pack(repo_root)
    _write_paper_inputs(paper_root)
    return repo_root, paper_root


def test_materialize_display_pack_publication_manifest_runs_full_quality_loop(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest
    from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle
    from med_autoscience.publication_figure_quality_contract import (
        collect_publication_figure_quality_refs,
        load_figure_render_receipt,
        load_figure_visual_audit_receipt,
    )

    repo_root, paper_root = _build_workspace(tmp_path)
    trace_history_ref = "paper/provenance/agent_session_history.json"
    _write_json(
        paper_root / "provenance" / "agent_session_history.json",
        {
            "schema_version": 1,
            "messages": [
                {"role": "user", "content": "render figure F1"},
                {"role": "assistant", "content": "rendered F1 and reviewed visual receipt"},
            ],
        },
    )
    _write_json(
        paper_root / "build" / "provenance" / "agent_trace_refs.json",
        {
            "schema_version": 1,
            "refs": [
                {
                    "label": "codex_session_history",
                    "ref": trace_history_ref,
                    "required": True,
                }
            ],
        },
    )

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
    )

    assert result["status"] == "publication_manifested"
    assert result["publication_readiness_verdict"] is False
    assert result["authority_boundary"]["mas_publication_quality_authority"] is True
    assert result["authority_boundary"]["display_pack_lock_can_authorize_publication_readiness"] is False

    figure = result["figures"][0]
    assert figure["figure_id"] == "F1"
    assert figure["deterministic_qc"]["status"] == "pass"
    assert Path(figure["rendered_artifacts"]["png_path"]).exists()
    assert Path(figure["rendered_artifacts"]["pdf_path"]).exists()
    assert Path(figure["rendered_artifacts"]["layout_sidecar_path"]).exists()

    manifest_path = paper_root / "build" / "display_pack_publication_manifest.json"
    lock_path = paper_root / "build" / "display_pack_lock.json"
    provenance_index_path = paper_root / "build" / "provenance" / "figure_provenance_index.json"
    provenance_bundle_path = paper_root / "build" / "provenance" / "figures" / "F1" / "bundle.json"
    provenance_bundle_dir = provenance_bundle_path.parent
    artifact_manifest_path = paper_root / "build" / "display_artifact_manifest.F1.json"
    qc_path = paper_root / "qc" / "F1.layout_qc.json"
    assert manifest_path.exists()
    assert lock_path.exists()
    assert provenance_index_path.exists()
    assert provenance_bundle_path.exists()
    assert artifact_manifest_path.exists()
    assert qc_path.exists()
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    provenance_index = json.loads(provenance_index_path.read_text(encoding="utf-8"))
    provenance_bundle = json.loads(provenance_bundle_path.read_text(encoding="utf-8"))
    lock_payload = json.loads(lock_path.read_text(encoding="utf-8"))
    style_lock = lock_payload["publication_style_profile"]
    assert style_lock["status"] == "present"
    assert style_lock["style_profile_id"] == "paper_neutral_clinical_v1"
    assert style_lock["sha256"] == result["publication_style_profile"]["sha256"]
    assert manifest_payload["publication_style_profile"]["sha256"] == style_lock["sha256"]
    assert manifest_payload["figure_provenance_index_ref"] == "paper/build/provenance/figure_provenance_index.json"
    assert result["figure_provenance_index"]["bundle_count"] == 1
    assert provenance_index["bundles"][0]["figure_id"] == "F1"
    assert provenance_index["bundles"][0]["provenance_bundle_ref"] == (
        "paper/build/provenance/figures/F1/bundle.json"
    )
    assert provenance_index["bundles"][0]["provenance_readback_ref"] == (
        "paper/build/provenance/figures/F1/replay/manifest.json"
    )
    assert provenance_index["bundles"][0]["typed_issue_codes"] == []
    assert provenance_index["bundles"][0]["replay_status"] == "pass"
    for relative_path in (
        "README.md",
        "ro-crate-metadata.json",
        "code_refs.json",
        "inputs/manifest.json",
        "outputs/manifest.json",
        "environment/manifest.json",
        "agent_trace/manifest.json",
        "reviews/manifest.json",
        "replay/manifest.json",
    ):
        assert (provenance_bundle_dir / relative_path).exists()
    assert provenance_bundle["schema_version"] == "artifact-provenance-bundle.v1"
    assert provenance_bundle["bundle_id"] == "medautoscience:display-pack-figure:F1"
    assert provenance_bundle["domain_id"] == "medautoscience"
    assert trace_history_ref in provenance_bundle["refs"]["agent_trace"]
    assert provenance_bundle["metadata"]["agent_trace"]["codex_transcript"]["status"] == "ref_available"
    assert provenance_bundle["metadata"]["agent_trace"]["external_trace_refs"][0]["status"] == "present"
    assert provenance_bundle["missing_refs"] == []
    assert provenance_bundle["metadata"]["figure_id"] == "F1"
    assert provenance_bundle["metadata"]["code"]["template_id"] == "fenggaolab.org.medical-display-core::roc_curve_binary"
    assert provenance_bundle["metadata"]["input"]["data_refs"] == ["paper/data/frozen/primary_curve.json"]
    assert provenance_bundle["metadata"]["output"]["rendered_artifacts"]["png_ref"] == "paper/figures/generated/F1.png"
    assert provenance_bundle["metadata"]["replay"]["mode"] == "refs_only_no_rerun"
    assert provenance_bundle["metadata"]["replay"]["status"] == "pass"
    assert provenance_bundle["metadata"]["replay"]["dry_run_readback"]["mode"] == "refs_only_dry_run"
    assert provenance_bundle["metadata"]["replay"]["dry_run_readback"]["issue_codes"] == []
    assert provenance_bundle["typed_issues"] == []
    assert provenance_bundle["missing_refs"] == []
    assert provenance_bundle["authority_boundary"]["ledger_refs_only"] is True
    assert provenance_bundle["metadata"]["authority_boundary"]["does_not_rerun_or_rewrite_figures"] is True
    manifest_figure = manifest_payload["figures"][0]
    assert manifest_figure["provenance_bundle_ref"] == "paper/build/provenance/figures/F1/bundle.json"
    assert manifest_figure["provenance_bundle_hash"] == provenance_index["bundles"][0]["provenance_bundle_hash"]
    assert manifest_figure["provenance_readback_ref"] == "paper/build/provenance/figures/F1/replay/manifest.json"
    assert figure["publication_style_profile"]["sha256"] == style_lock["sha256"]
    assert figure["publication_style_profile"]["typography"]["font_family"] == "sans"
    assert figure["publication_style_profile"]["grid"]["color"] == "#D9E2EC"
    layout_sidecar = json.loads(Path(figure["rendered_artifacts"]["layout_sidecar_path"]).read_text(encoding="utf-8"))
    render_context = layout_sidecar["render_context"]
    assert layout_sidecar["panel_boxes"][0]["panel_id"] == "A"
    assert layout_sidecar["metrics"]["panel_ids"] == ["A"]
    assert render_context["style_profile_sha256"] == style_lock["sha256"]
    assert render_context["palette"]["primary"] == "#245A6B"
    assert render_context["style_roles"]["model_curve"] == "#245A6B"
    assert render_context["style_roles"]["model_curve"] == render_context["palette"][render_context["semantic_roles"]["model_curve"]]
    assert render_context["typography"]["font_family"] == "sans"
    assert render_context["grid"]["major"] is True
    assert render_context["stroke"]["grid_linewidth"] == 0.35

    visual_receipt = load_figure_visual_audit_receipt(paper_root / "figure_visual_audit_receipt.json")
    assert visual_receipt["inspected_artifacts"][0]["artifact_sha256"] == figure["rendered_artifacts"]["png_sha256"]
    assert visual_receipt["final_status"] == "clear"

    render_receipt = load_figure_render_receipt(paper_root / "figure_render_receipt.json")
    render_figure = render_receipt["figures"][0]
    assert render_figure["figure_id"] == "F1"
    assert render_figure["selected_backend"] == "r_ggplot2"
    assert render_figure["backend_exclusivity_proof"]["cross_backend_visual_fallback_used"] is False
    assert render_figure["backend_exclusivity_proof"]["observed_renderer_family"] == "r_ggplot2"
    assert set(render_figure["export_formats"]) == {"png", "pdf"}
    assert render_figure["editable_text_required"] is True
    assert render_figure["source_data_refs"] == ["paper/data/frozen/primary_curve.json"]
    assert render_figure["source_data_digests"]["paper/data/frozen/primary_curve.json"] == "data-digest-primary"
    assert render_figure["statistics_refs"] == ["analysis/statistics/auc_primary"]
    assert render_figure["visual_qa_ref"] == "paper/figure_visual_audit_receipt.json"
    assert render_figure["provenance_bundle_ref"] == "paper/build/provenance/figures/F1/bundle.json"
    assert render_figure["provenance_bundle_hash"] == provenance_index["bundles"][0]["provenance_bundle_hash"]
    assert render_figure["provenance_readback_ref"] == "paper/build/provenance/figures/F1/replay/manifest.json"
    assert render_receipt["authority_boundary"]["can_authorize_publication_readiness"] is False

    lifecycle = load_figure_polish_lifecycle(paper_root / "figure_polish_lifecycle.json")
    assert [event["state"] for event in lifecycle["events"]] == [
        "draft_rendered",
        "deterministic_qc_clear",
        "visual_audit_findings",
        "revised",
        "audit_clear",
        "publication_manifested",
    ]

    refs = collect_publication_figure_quality_refs(paper_root=paper_root)
    assert refs["figure_intent"]["status"] == "present"
    assert refs["medical_figure_spec"]["status"] == "present"
    assert refs["publication_style_profile"]["status"] == "present"
    assert refs["publication_style_profile"]["sha256"] == style_lock["sha256"]
    assert refs["figure_style_reference_bundle"]["status"] == "present"
    assert refs["figure_visual_audit_receipt"]["status"] == "present"
    assert refs["figure_render_receipt"]["status"] == "present"
    assert refs["figure_polish_lifecycle"]["status"] == "present"
    assert result["publication_figure_quality_refs"]["figure_render_receipt"]["status"] == "present"


def test_materialize_display_pack_publication_manifest_fails_when_declared_panels_are_not_rendered(
    tmp_path: Path,
) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    repo_root, paper_root = _build_workspace(tmp_path)
    _write_json(
        paper_root / "figure_spec.json",
        {
            "schema_version": 1,
            "figure_id": "F1",
            "intent_ref": "paper/figure_intent.json#/figures/F1",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/derivation",
                "endpoint_ref": "endpoint:mace",
                "model_ref": "model:cox-primary",
                "risk_horizon": "5y",
                "effect_estimate_ref": "analysis/statistics/auc_primary",
                "claim_role": "primary_evidence",
            },
            "panels": [
                {"panel_id": "A", "data_role": "discrimination", "mark_role": "roc_curve"},
                {"panel_id": "B", "data_role": "calibration", "mark_role": "calibration_curve"},
            ],
        },
    )

    with pytest.raises(ValueError, match=r"missing panel_id\(s\): A, B"):
        materialize_display_pack_publication_manifest(
            repo_root=repo_root,
            paper_root=paper_root,
            visual_audit_review=_visual_audit_review(),
        )

    assert not (paper_root / "figure_visual_audit_receipt.json").exists()
    assert not (paper_root / "figure_polish_lifecycle.json").exists()
    assert not (paper_root / "build" / "display_pack_publication_manifest.json").exists()


def test_cli_publication_display_pack_e2e_emits_manifest_json(tmp_path: Path, capsys) -> None:
    from med_autoscience import cli

    repo_root, paper_root = _build_workspace(tmp_path)

    exit_code = cli.main(
        [
            "publication",
            "display-pack-e2e",
            "--repo-root",
            str(repo_root),
            "--paper-root",
            str(paper_root),
            "--visual-audit-review-json",
            json.dumps(_visual_audit_review()),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "publication_manifested"
    assert payload["manifest_path"].endswith("paper/build/display_pack_publication_manifest.json")

    exit_code = cli.main(
        [
            "publication",
            "display-pack-provenance-bundles",
            "--repo-root",
            str(repo_root),
            "--paper-root",
            str(paper_root),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "materialized"
    assert payload["bundles"][0]["provenance_bundle_ref"] == "paper/build/provenance/figures/F1/bundle.json"


def test_materialize_figure_provenance_bundles_records_missing_refs(tmp_path: Path) -> None:
    from med_autoscience.display_pack_provenance_bundle import materialize_figure_provenance_bundles

    repo_root, paper_root = _build_workspace(tmp_path)
    restricted_output = tmp_path / "restricted-output.png"
    restricted_output.write_text("restricted", encoding="utf-8")
    _write_json(
        paper_root / "build" / "display_pack_publication_manifest.json",
        {
            "schema_version": 1,
            "status": "publication_manifested",
            "figures": [
                {
                    "figure_id": "F_missing",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "rendered_artifacts": {
                        "png_ref": "paper/figures/generated/F_missing.png",
                        "pdf_ref": str(restricted_output),
                        "layout_sidecar_ref": "paper/figures/generated/F_missing.layout.json",
                    },
                }
            ],
        },
    )

    result = materialize_figure_provenance_bundles(repo_root=repo_root, paper_root=paper_root)

    bundle_path = paper_root / "build" / "provenance" / "figures" / "F_missing" / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    missing_labels = {item["label"] for item in bundle["missing_refs"]}
    typed_issue_codes = {item["code"] for item in bundle["typed_issues"]}
    assert result["status"] == "materialized"
    assert "figure_render_receipt" in missing_labels
    assert "figure_visual_audit_receipt" in missing_labels
    assert "figure_polish_lifecycle" in missing_labels
    assert "rendered_output_0" in missing_labels
    assert result["bundles"][0]["typed_issue_count"] == len(bundle["typed_issues"])
    assert "missing_agent_trace" in typed_issue_codes
    assert "missing_review" in typed_issue_codes
    assert "missing_replay_command" in typed_issue_codes
    assert "missing_replay_request" in typed_issue_codes
    assert "missing_output_ref" in typed_issue_codes
    assert "restricted_ref" in typed_issue_codes
    assert result["bundles"][0]["provenance_readback_ref"] == (
        "paper/build/provenance/figures/F_missing/replay/manifest.json"
    )
    assert (bundle_path.parent / "README.md").exists()
    assert (bundle_path.parent / "ro-crate-metadata.json").exists()
    assert (bundle_path.parent / "replay" / "manifest.json").exists()
    replay_manifest = json.loads((bundle_path.parent / "replay" / "manifest.json").read_text(encoding="utf-8"))
    assert replay_manifest["metadata"]["dry_run_readback"]["status"] == "blocked"
    assert "missing_replay_request" in replay_manifest["metadata"]["dry_run_readback"]["issue_codes"]
    manifest_payload = json.loads((paper_root / "build" / "display_pack_publication_manifest.json").read_text(encoding="utf-8"))
    assert manifest_payload["figures"][0]["provenance_bundle_ref"] == (
        "paper/build/provenance/figures/F_missing/bundle.json"
    )
    assert bundle["metadata"]["agent_trace"]["codex_transcript"]["status"] == "restricted"


def test_materialize_display_pack_publication_manifest_runs_subprocess_renderer(tmp_path: Path) -> None:
    from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest

    repo_root, paper_root = _build_workspace(tmp_path)
    _write_subprocess_renderable_template(repo_root)
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F2",
                    "claim_ref": "claim:secondary-discrimination",
                    "data_ref": "paper/data/frozen/primary_curve.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
                    "figure_kind": "evidence_figure",
                    "statistical_value_refs": ["analysis/statistics/auc_secondary"],
                }
            ],
        },
    )
    _write_json(
        paper_root / "figure_spec.json",
        {
            "schema_version": 1,
            "figure_id": "F2",
            "intent_ref": "paper/figure_intent.json#/figures/F2",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary_ggplot2",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/validation",
                "endpoint_ref": "endpoint:mace",
                "model_ref": "model:cox-secondary",
                "risk_horizon": "5y",
                "effect_estimate_ref": "analysis/statistics/auc_secondary",
                "claim_role": "secondary_evidence",
            },
            "panels": [{"panel_id": "A", "data_role": "discrimination", "mark_role": "roc_curve"}],
        },
    )

    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=_visual_audit_review(),
    )

    figure = result["figures"][0]
    assert figure["figure_id"] == "F2"
    assert figure["render_result"]["execution_mode"] == "subprocess"
    assert figure["render_result"]["renderer_family"] == "r_ggplot2"
    assert figure["render_result"]["returncode"] == 0
    assert Path(figure["render_result"]["request_path"]).exists()
    assert Path(figure["render_result"]["stdout_path"]).read_text(encoding="utf-8").strip()
    assert Path(figure["rendered_artifacts"]["png_path"]).read_text(encoding="utf-8").startswith("PNG:subprocess:")
    request_payload = json.loads(Path(figure["render_result"]["request_path"]).read_text(encoding="utf-8"))
    render_context = request_payload["display_payload"]["render_context"]
    assert render_context["palette"]["secondary"] == "#B89A6D"
    assert render_context["semantic_roles"]["comparator_curve"] == "secondary"
    assert render_context["style_roles"]["comparator_curve"] == "#B89A6D"
    assert render_context["typography"]["base_size"] == 10.5
    assert render_context["stroke"]["reference_linewidth"] == 1.1
    assert render_context["grid"]["major_axis"] == "both"

from tests.test_display_pack_e2e_runtime_cases.real_r_and_multi_figure_cases import *  # noqa: F403,F401
