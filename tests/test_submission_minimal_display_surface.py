from __future__ import annotations

import base64
import importlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

from med_autoscience import display_registry
from med_autoscience.controllers.submission_package_layout import resolve_submission_manifest_path
from tests.submission_minimal_cases.shared import lightweight_submission_exports, real_submission_exports

PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNg"
    "AAAAAgABSK+kcQAAAABJRU5ErkJggg=="
)


def _canonicalize_registry_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return normalized
    if display_registry.is_evidence_figure_template(normalized):
        return display_registry.get_evidence_figure_spec(normalized).template_id
    if display_registry.is_illustration_shell(normalized):
        return display_registry.get_illustration_shell_spec(normalized).shell_id
    if display_registry.is_table_shell(normalized):
        return display_registry.get_table_shell_spec(normalized).shell_id
    return normalized


def full_id(value: str) -> str:
    return _canonicalize_registry_id(value)


def _normalize_namespaced_ids(payload: Any) -> Any:
    if isinstance(payload, dict):
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized_value = _normalize_namespaced_ids(value)
            if key in {"requirement_key", "template_id", "shell_id", "table_shell_id"} and isinstance(
                normalized_value, str
            ):
                normalized_value = _canonicalize_registry_id(normalized_value)
            normalized[key] = normalized_value
        return normalized
    if isinstance(payload, list):
        return [_normalize_namespaced_ids(item) for item in payload]
    return payload


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_payload = _normalize_namespaced_ids(payload)
    path.write_text(json.dumps(normalized_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(PNG_1X1_BASE64))


def make_workspace(tmp_path: Path) -> Path:
    paper_root = tmp_path / "workspace" / "paper"
    write_text(
        paper_root / "build" / "review_manuscript.md",
        """---
title: "Display Surface Manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Test citation [@ref1].

# Main Figures

## Figure 1. Main figure

Caption.

![](../figures/F1_main.png)

# Main Tables

| Characteristic | Value |
| --- | --- |
| Age | 52 |
""",
    )
    write_text(
        paper_root / "references.bib",
        """@article{ref1,
  title={A primary source},
  author={Author, A.},
  journal={Journal},
  year={2024}
}
""",
    )
    write_png(paper_root / "figures" / "F1_main.png")
    write_text(paper_root / "figures" / "F1_main.pdf", "%PDF-1.4\n")
    write_text(paper_root / "tables" / "T1_summary.csv", "Characteristic,Value\nAge,52\n")
    write_text(paper_root / "tables" / "T1_summary.md", "| Characteristic | Value |\n| --- | --- |\n| Age | 52 |\n")
    write_text(paper_root / "paper.pdf", "%PDF-1.4\n")
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown": "paper/build/review_manuscript.md",
            "output_pdf": "paper/paper.pdf",
        },
    )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "roc_curve_binary",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "binary_prediction_curve_inputs_v1",
                    "qc_profile": "publication_evidence_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_evidence_curve",
                        "layout_sidecar_path": "paper/figures/generated/F1.layout.json",
                        "issues": [],
                    },
                    "title": "Main figure",
                    "export_paths": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
                }
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "table_shell_id": "table1_baseline_characteristics",
                    "paper_role": "main_text",
                    "input_schema_id": "baseline_characteristics_schema_v1",
                    "qc_profile": "publication_table_baseline",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Summary table",
                    "asset_paths": ["paper/tables/T1_summary.csv", "paper/tables/T1_summary.md"],
                }
            ],
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )
    return paper_root


def test_create_submission_minimal_package_preserves_display_surface_metadata(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    dump_json(
        paper_root / "build" / "display_pack_lock.json",
        {
            "schema_version": 2,
            "enabled_packs": [
                {
                    "pack_id": "fenggaolab.org.medical-display-core",
                    "version": "0.2.0",
                    "requested_version": "0.2.0",
                    "source_kind": "git_repo",
                    "declared_in": "repo",
                    "manifest_sha256": "a" * 64,
                    "source_path": "../display-core-git",
                }
            ],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["figures"][0]["template_id"] == full_id("roc_curve_binary")
    assert manifest["figures"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert manifest["figures"][0]["pack_version"] == "0.2.0"
    assert manifest["figures"][0]["pack_source_kind"] == "git_repo"
    assert manifest["figures"][0]["renderer_family"] == "r_ggplot2"
    assert manifest["figures"][0]["qc_profile"] == "publication_evidence_curve"
    assert manifest["tables"][0]["table_shell_id"] == full_id("table1_baseline_characteristics")
    assert manifest["tables"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert manifest["tables"][0]["pack_manifest_sha256"] == "a" * 64
    assert manifest["tables"][0]["qc_profile"] == "publication_table_baseline"
    assert manifest["display_pack_lock_path"] == "paper/build/display_pack_lock.json"
    assert manifest["enabled_display_packs"][0]["version"] == "0.2.0"
    assert manifest["enabled_display_packs"][0]["source_kind"] == "git_repo"


def test_create_submission_minimal_package_preserves_figure_quality_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    dump_json(
        paper_root / "build" / "display_pack_lock.json",
        {
            "schema_version": 2,
            "enabled_packs": [],
            "publication_figure_quality_refs": {
                "figure_intent": {"path": "paper/figure_intent.json", "status": "present", "sha256": "a" * 64},
                "figure_style_reference_bundle": {
                    "path": "paper/figure_style_reference_bundle.json",
                    "status": "missing",
                },
                "figure_visual_audit_receipt": {
                    "path": "paper/figure_visual_audit_receipt.json",
                    "status": "present",
                    "sha256": "b" * 64,
                },
                "medical_figure_spec": {"path": "paper/figure_spec.json", "status": "present", "sha256": "c" * 64},
                "figure_polish_lifecycle": {
                    "path": "paper/figure_polish_lifecycle.json",
                    "status": "present",
                    "sha256": "d" * 64,
                },
                "ai_illustration_receipt": {"path": "paper/ai_illustration_receipt.json", "status": "missing"},
            },
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    refs = manifest["publication_figure_quality_refs"]
    assert refs["figure_intent"]["path"] == "paper/figure_intent.json"
    assert refs["medical_figure_spec"]["path"] == "paper/figure_spec.json"
    assert refs["figure_visual_audit_receipt"]["status"] == "present"
    assert refs["figure_polish_lifecycle"]["status"] == "present"
    assert refs["ai_illustration_receipt"]["status"] == "missing"


def test_create_submission_minimal_package_hydrates_compile_report_from_current_draft(
    tmp_path: Path,
    writable_authority_route_context: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    (paper_root / "build" / "compile_report.json").unlink()
    write_text(
        paper_root / "draft.md",
        """---
title: "Current Draft Manuscript"
bibliography: references.bib
link-citations: true
---

# Abstract

Current draft citation [@ref1].

# Main Figures

## Figure 1. Main figure

Caption.

![](figures/F1_main.png)
""",
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/draft.md",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=writable_authority_route_context,
    )

    compile_report = json.loads((paper_root / "build" / "compile_report.json").read_text(encoding="utf-8"))
    assert compile_report["status"] == "current_draft_compile_source_hydrated"
    assert compile_report["source_markdown_path"] == "paper/draft.md"
    assert manifest["source_hydration"]["source_compile_report_status"] == "generated_from_current_draft"
    assert "paper/build/compile_report.json" in manifest["source_hydration"]["hydrated_files"]
    assert manifest["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"


def test_create_submission_minimal_package_refreshes_stale_compile_report_from_newer_current_draft(
    tmp_path: Path,
    writable_authority_route_context: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    write_text(
        paper_root / "draft.md",
        """---
title: "Newer Current Draft"
bibliography: references.bib
link-citations: true
---

# Abstract

Newer current draft abstract.

# Methods

Newer current draft methods.
""",
    )
    compile_report_path = paper_root / "build" / "compile_report.json"
    os.utime(compile_report_path, (1000, 1000))
    os.utime(paper_root / "draft.md", (2000, 2000))

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=writable_authority_route_context,
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    compile_report = json.loads(compile_report_path.read_text(encoding="utf-8"))
    assert "Newer Current Draft" in submission_text
    assert "Newer current draft methods." in submission_text
    assert "Display Surface Manuscript" not in submission_text
    assert compile_report["status"] == "current_draft_compile_source_hydrated"
    assert compile_report["source_markdown_path"] == "paper/draft.md"
    assert manifest["source_hydration"]["source_compile_report_status"] == "refreshed_from_current_draft"
    assert "paper/build/compile_report.json" in manifest["source_hydration"]["hydrated_files"]


def test_create_submission_minimal_package_preserves_current_draft_table_body_over_stale_catalog(
    tmp_path: Path,
    writable_authority_route_context: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    write_text(
        paper_root / "draft.md",
        """---
title: "Current Draft With Table"
bibliography: references.bib
link-citations: true
---

# Abstract

Current draft abstract.

# Main Tables

### Table 1. Current review table

| Characteristic | Value |
| --- | --- |
| Current row | 99 |
""",
    )
    os.utime(paper_root / "build" / "compile_report.json", (1000, 1000))
    os.utime(paper_root / "tables" / "T1_summary.md", (1000, 1000))
    os.utime(paper_root / "draft.md", (2000, 2000))

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=writable_authority_route_context,
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "Current row" in submission_text
    assert "99" in submission_text
    assert "Age | 52" not in submission_text


def test_create_submission_minimal_package_refreshes_stage_native_current_body_paper_root(
    tmp_path: Path,
    writable_authority_route_context: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    seed_root = make_workspace(tmp_path / "seed")
    paper_root = (
        tmp_path
        / "study"
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    shutil.copytree(seed_root, paper_root)
    write_text(
        paper_root / "draft.md",
        """---
title: "Stage Native Current Body Draft"
bibliography: references.bib
link-citations: true
---

# Abstract

Stage-native current body abstract.

# Methods

Stage-native current body methods.
""",
    )
    compile_report_path = paper_root / "build" / "compile_report.json"
    os.utime(compile_report_path, (1000, 1000))
    os.utime(paper_root / "draft.md", (2000, 2000))

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=writable_authority_route_context,
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "Stage Native Current Body Draft" in submission_text
    assert "Stage-native current body methods." in submission_text
    assert "Display Surface Manuscript" not in submission_text
    assert manifest["source_hydration"]["source_root"] == str(paper_root.resolve())
    assert manifest["source_hydration"]["source_compile_report_status"] == "refreshed_from_current_draft"


def test_create_submission_minimal_package_preserves_newer_target_draft_when_hydrating_current_body(
    tmp_path: Path,
    writable_authority_route_context: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    study_root = tmp_path / "workspace"
    paper_root = make_workspace(tmp_path)
    current_body_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    shutil.copytree(paper_root, current_body_paper_root)
    write_text(
        current_body_paper_root / "draft.md",
        """---
title: "Older Current Body Draft"
bibliography: references.bib
link-citations: true
---

# Abstract

Older current-body draft.
""",
    )
    write_text(
        paper_root / "draft.md",
        """---
title: "Newer Target Draft"
bibliography: references.bib
link-citations: true
---

# Abstract

Newer target draft abstract.

# Methods

Newer target draft methods.
""",
    )
    os.utime(current_body_paper_root / "draft.md", (1000, 1000))
    os.utime(current_body_paper_root / "build" / "compile_report.json", (1000, 1000))
    os.utime(paper_root / "draft.md", (2000, 2000))
    os.utime(paper_root / "build" / "compile_report.json", (1000, 1000))

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=writable_authority_route_context,
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "Newer Target Draft" in submission_text
    assert "Newer target draft methods." in submission_text
    assert "Older Current Body Draft" not in submission_text
    assert manifest["source_hydration"]["source_compile_report_status"] == "refreshed_from_current_draft"


def test_create_submission_minimal_package_hydrates_delivery_required_ledgers_from_current_body(
    tmp_path: Path,
    writable_authority_route_context: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    study_root = tmp_path / "workspace"
    paper_root = study_root / "paper"
    current_body_paper_root = (
        study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper"
    )
    make_workspace(tmp_path)
    (paper_root / "evidence_ledger.json").unlink(missing_ok=True)
    (paper_root / "review" / "review_ledger.json").unlink(missing_ok=True)
    dump_json(
        current_body_paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "ledger_id": "current-body-evidence-ledger",
            "claims": [],
        },
    )
    dump_json(
        current_body_paper_root / "review" / "review_ledger.json",
        {
            "schema_version": 1,
            "ledger_id": "current-body-review-ledger",
            "review_items": [],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=writable_authority_route_context,
    )

    assert (paper_root / "evidence_ledger.json").exists()
    assert (paper_root / "review" / "review_ledger.json").exists()
    assert "paper/evidence_ledger.json" in manifest["source_hydration"]["hydrated_files"]
    assert "paper/review/review_ledger.json" in manifest["source_hydration"]["hydrated_files"]
    assert (paper_root / "submission_minimal" / "audit" / "evidence_ledger.json").exists()


def test_create_submission_minimal_package_hydrates_current_body_manuscript_and_tables(
    tmp_path: Path,
    writable_authority_route_context: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    study_root = tmp_path / "workspace"
    paper_root = make_workspace(tmp_path)
    current_body_paper_root = (
        study_root / "artifacts" / "stage_outputs" / "_body_authority" / "paper_authority_cutover" / "current_body" / "paper"
    )
    (paper_root / "build" / "compile_report.json").unlink()
    write_text(paper_root / "draft.md", "# Stale root draft\n\nOld text.\n")
    write_text(
        current_body_paper_root / "draft.md",
        """# Current body manuscript

## Abstract

Current authority abstract.

## Results

Current authority results.

## Discussion

Current authority discussion.
""",
    )
    dump_json(
        current_body_paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T2",
                    "table_shell_id": "performance_summary",
                    "paper_role": "main_text",
                    "title": "Current performance table",
                    "asset_paths": ["paper/tables/generated/T2_current_performance.md"],
                },
                {
                    "table_id": "T3",
                    "table_shell_id": "grouped_calibration",
                    "paper_role": "main_text",
                    "title": "Current decile calibration",
                    "asset_paths": ["paper/tables/generated/T3_current_deciles.md"],
                },
            ],
        },
    )
    write_text(
        current_body_paper_root / "tables" / "generated" / "T2_current_performance.md",
        "| Metric | Value |\n| --- | --- |\n| C-index | 0.734 |\n",
    )
    write_text(
        current_body_paper_root / "tables" / "generated" / "T3_current_deciles.md",
        "| Decile | Events |\n| --- | ---: |\n| 10 | 214 |\n",
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
        route_context=writable_authority_route_context,
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "Current authority abstract." in submission_text
    assert "Old text." not in submission_text
    assert "## Table 2. Current performance table" in submission_text
    assert "| C-index | 0.734 |" in submission_text
    assert "## Table 3. Current decile calibration" in submission_text
    assert "| 10 | 214 |" in submission_text
    assert "paper/draft.md" in manifest["source_hydration"]["hydrated_files"]
    assert "paper/tables/table_catalog.json" in manifest["source_hydration"]["hydrated_files"]
    assert "paper/tables/generated/T3_current_deciles.md" in manifest["source_hydration"]["hydrated_files"]


def test_create_submission_minimal_package_preserves_canonical_main_display_headings(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "# Main Figures" in submission_text
    assert "# Main Tables" in submission_text
    assert "# Figures" not in submission_text
    assert "# Tables" not in submission_text


def test_create_submission_minimal_package_preserves_main_tables_with_peer_table_headings(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    write_text(
        paper_root / "build" / "review_manuscript.md",
        """---
title: "Display Surface Manuscript"
bibliography: ../references.bib
link-citations: true
---

## Abstract

Structured abstract.

## Introduction

Clinical setup.

## Materials and Methods

Study design.

## Results

Main result.

## Discussion

Interpretation.

# Main Tables

# Baseline cohort and burden characteristics by Knosp strata

| Characteristic | Value |
| --- | --- |
| Age | 52 |

# Comparative performance for the bounded non-GTR extension

| Model | AUROC |
| --- | --- |
| Knosp + diameter | 0.80 |

# Main Figures

## Figure 1. Main figure

Caption.

![](../figures/F1_main.png)
""",
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "# Main Tables" in submission_text
    assert "## Baseline cohort and burden characteristics by Knosp strata" in submission_text
    assert "## Comparative performance for the bounded non-GTR extension" in submission_text
    assert "| Knosp + diameter | 0.80 |" in submission_text


def test_create_submission_minimal_package_materializes_catalog_tables_when_source_has_no_main_tables_section(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    write_text(
        paper_root / "build" / "review_manuscript.md",
        """---
title: "Display Surface Manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Test citation [@ref1].

# Main Figures

## Figure 1. Main figure

Caption.

![](../figures/F1_main.png)
""",
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_text = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "# Main Tables" in submission_text
    assert "## Table 1. Summary table" in submission_text
    assert "| Characteristic | Value |" in submission_text
    assert "| Age | 52 |" in submission_text


def test_create_submission_minimal_package_prunes_legacy_top_level_figure_and_table_exports(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)

    write_png(paper_root / "figures" / "Figure1.png")
    write_text(paper_root / "figures" / "Figure1.pdf", "%PDF-1.4\n")
    write_text(paper_root / "figures" / "Figure1.shell.json", "{\"keep\": true}\n")
    write_text(paper_root / "tables" / "Table1.csv", "legacy,stale\n")
    write_text(paper_root / "tables" / "Table1.md", "| legacy | stale |\n")

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert not (paper_root / "figures" / "Figure1.png").exists()
    assert not (paper_root / "figures" / "Figure1.pdf").exists()
    assert (paper_root / "figures" / "Figure1.shell.json").exists()
    assert not (paper_root / "tables" / "Table1.csv").exists()
    assert not (paper_root / "tables" / "Table1.md").exists()
    assert manifest["pruned_legacy_paths"] == [
        "paper/figures/Figure1.pdf",
        "paper/figures/Figure1.png",
        "paper/tables/Table1.csv",
        "paper/tables/Table1.md",
    ]


def test_create_submission_minimal_package_preserves_second_stage_display_entries(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    workspace_root = paper_root.parent

    write_png(paper_root / "figures" / "F14_validation.png")
    write_text(paper_root / "figures" / "F14_validation.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F17_generalizability.png")
    write_text(paper_root / "figures" / "F17_generalizability.pdf", "%PDF-1.4\n")
    write_text(
        paper_root / "tables" / "T2_performance.md",
        "| Metric | Development | External |\n| --- | --- | --- |\n| C-index | 0.81 | 0.77 |\n",
    )
    write_text(
        paper_root / "tables" / "T3_interpretation.md",
        "| Clinical Item | Observed signal | Interpretation |\n| --- | --- | --- |\n| High risk | Higher burden | Intensify follow-up |\n",
    )

    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"].extend(
        [
            {
                "figure_id": "F14",
                "template_id": "time_to_event_discrimination_calibration_panel",
                "renderer_family": "r_ggplot2",
                "paper_role": "main_text",
                "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
                "qc_profile": "publication_evidence_curve",
                "qc_result": {
                    "status": "pass",
                    "checked_at": "2026-04-03T10:00:00+00:00",
                    "engine_id": "display_layout_qc_v1",
                    "qc_profile": "publication_evidence_curve",
                    "layout_sidecar_path": "paper/figures/generated/F14.layout.json",
                    "issues": [],
                },
                "title": "Validation discrimination and calibration",
                "export_paths": ["paper/figures/F14_validation.pdf", "paper/figures/F14_validation.png"],
            },
            {
                "figure_id": "F17",
                "template_id": "generalizability_subgroup_composite_panel",
                "renderer_family": "r_ggplot2",
                "paper_role": "supplementary",
                "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
                "qc_profile": "publication_generalizability_subgroup_composite_panel",
                "qc_result": {
                    "status": "pass",
                    "checked_at": "2026-04-03T10:00:00+00:00",
                    "engine_id": "display_layout_qc_v1",
                    "qc_profile": "publication_generalizability_subgroup_composite_panel",
                    "layout_sidecar_path": "paper/figures/generated/F17.layout.json",
                    "issues": [],
                },
                "title": "Multicenter generalizability",
                "export_paths": ["paper/figures/F17_generalizability.pdf", "paper/figures/F17_generalizability.png"],
            },
        ]
    )
    dump_json(figure_catalog_path, figure_catalog)

    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table_catalog = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    table_catalog["tables"].extend(
        [
            {
                "table_id": "T2",
                "table_shell_id": "table2_time_to_event_performance_summary",
                "paper_role": "main_text",
                "input_schema_id": "time_to_event_performance_summary_v1",
                "qc_profile": "publication_table_performance",
                "qc_result": {"status": "pass", "issues": []},
                "title": "Time-to-event performance summary",
                "asset_paths": ["paper/tables/T2_performance.md"],
            },
            {
                "table_id": "T3",
                "table_shell_id": "table3_clinical_interpretation_summary",
                "paper_role": "supplementary",
                "input_schema_id": "clinical_interpretation_summary_v1",
                "qc_profile": "publication_table_interpretation",
                "qc_result": {"status": "pass", "issues": []},
                "title": "Clinical interpretation summary",
                "asset_paths": ["paper/tables/T3_interpretation.md"],
            },
        ]
    )
    dump_json(table_catalog_path, table_catalog)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    figures_by_id = {item["figure_id"]: item for item in manifest["figures"]}
    tables_by_id = {item["table_id"]: item for item in manifest["tables"]}

    assert set(figures_by_id) == {"F1", "F14", "F17"}
    assert figures_by_id["F14"]["template_id"] == full_id("time_to_event_discrimination_calibration_panel")
    assert figures_by_id["F14"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F14"]["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert figures_by_id["F17"]["template_id"] == full_id("generalizability_subgroup_composite_panel")
    assert figures_by_id["F17"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F17"]["qc_profile"] == "publication_generalizability_subgroup_composite_panel"
    assert len(figures_by_id["F14"]["output_paths"]) == 2
    assert all((workspace_root / output_path).exists() for output_path in figures_by_id["F14"]["output_paths"])
    assert all((workspace_root / output_path).exists() for output_path in figures_by_id["F17"]["output_paths"])

    assert set(tables_by_id) == {"T1", "T2", "T3"}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("table2_time_to_event_performance_summary")
    assert tables_by_id["T2"]["qc_profile"] == "publication_table_performance"
    assert tables_by_id["T3"]["table_shell_id"] == full_id("table3_clinical_interpretation_summary")
    assert tables_by_id["T3"]["qc_profile"] == "publication_table_interpretation"
    assert tables_by_id["T2"]["output_paths"][0].endswith(".md")
    assert tables_by_id["T3"]["output_paths"][0].endswith(".md")
    assert (workspace_root / tables_by_id["T2"]["output_paths"][0]).exists()
    assert (workspace_root / tables_by_id["T3"]["output_paths"][0]).exists()


def test_create_submission_minimal_package_preserves_001_direct_migration_display_entries(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)
    workspace_root = paper_root.parent

    write_png(paper_root / "figures" / "F1_cohort_flow.png")
    write_text(paper_root / "figures" / "F1_cohort_flow.svg", "<svg><text>flow</text></svg>\n")
    write_png(paper_root / "figures" / "F2_validation.png")
    write_text(paper_root / "figures" / "F2_validation.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F3_risk_group_summary.png")
    write_text(paper_root / "figures" / "F3_risk_group_summary.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F4_dca.png")
    write_text(paper_root / "figures" / "F4_dca.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F5_generalizability.png")
    write_text(paper_root / "figures" / "F5_generalizability.pdf", "%PDF-1.4\n")
    write_text(
        paper_root / "tables" / "T2_performance.md",
        "| Metric | Development | External |\n| --- | --- | --- |\n| C-index | 0.81 | 0.77 |\n",
    )

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "cohort_flow_figure",
                    "renderer_family": "python",
                    "paper_role": "main_text",
                    "input_schema_id": "cohort_flow_shell_inputs_v1",
                    "qc_profile": "publication_illustration_flow",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Cohort derivation and endpoint inventory",
                    "export_paths": ["paper/figures/F1_cohort_flow.png", "paper/figures/F1_cohort_flow.svg"],
                },
                {
                    "figure_id": "F2",
                    "template_id": "time_to_event_discrimination_calibration_panel",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
                    "qc_profile": "publication_evidence_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_evidence_curve",
                        "layout_sidecar_path": "paper/figures/generated/F2.layout.json",
                        "issues": [],
                    },
                    "title": "Discrimination and grouped calibration",
                    "export_paths": ["paper/figures/F2_validation.pdf", "paper/figures/F2_validation.png"],
                },
                {
                    "figure_id": "F3",
                    "template_id": "time_to_event_risk_group_summary",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_grouped_inputs_v1",
                    "qc_profile": "publication_survival_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_survival_curve",
                        "layout_sidecar_path": "paper/figures/generated/F3.layout.json",
                        "issues": [],
                    },
                    "title": "Primary risk-group summary",
                    "export_paths": ["paper/figures/F3_risk_group_summary.pdf", "paper/figures/F3_risk_group_summary.png"],
                },
                {
                    "figure_id": "F4",
                    "template_id": "time_to_event_decision_curve",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_decision_curve_inputs_v1",
                    "qc_profile": "publication_decision_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_decision_curve",
                        "layout_sidecar_path": "paper/figures/generated/F4.layout.json",
                        "issues": [],
                    },
                    "title": "Time-to-event decision curve",
                    "export_paths": ["paper/figures/F4_dca.pdf", "paper/figures/F4_dca.png"],
                },
                {
                    "figure_id": "F5",
                    "template_id": "generalizability_subgroup_composite_panel",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
                    "qc_profile": "publication_generalizability_subgroup_composite_panel",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_generalizability_subgroup_composite_panel",
                        "layout_sidecar_path": "paper/figures/generated/F5.layout.json",
                        "issues": [],
                    },
                    "title": "Internal multicenter generalizability",
                    "export_paths": ["paper/figures/F5_generalizability.pdf", "paper/figures/F5_generalizability.png"],
                },
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "table_shell_id": "table1_baseline_characteristics",
                    "paper_role": "main_text",
                    "input_schema_id": "baseline_characteristics_schema_v1",
                    "qc_profile": "publication_table_baseline",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Summary table",
                    "asset_paths": ["paper/tables/T1_summary.csv", "paper/tables/T1_summary.md"],
                },
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Time-to-event performance summary",
                    "asset_paths": ["paper/tables/T2_performance.md"],
                },
            ],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    figures_by_id = {item["figure_id"]: item for item in manifest["figures"]}
    tables_by_id = {item["table_id"]: item for item in manifest["tables"]}
    manifest_path = resolve_submission_manifest_path(paper_root / "submission_minimal")
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert set(figures_by_id) == {"F1", "F2", "F3", "F4", "F5"}
    assert figures_by_id["F1"]["template_id"] == full_id("cohort_flow_figure")
    assert figures_by_id["F1"]["renderer_family"] == "python"
    assert figures_by_id["F5"]["template_id"] == full_id("generalizability_subgroup_composite_panel")
    assert figures_by_id["F5"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F5"]["qc_profile"] == "publication_generalizability_subgroup_composite_panel"
    assert manifest_payload["naming_map"]["figures"]["F5"] == "Figure5"
    assert all((workspace_root / output_path).exists() for output_path in figures_by_id["F5"]["output_paths"])

    assert set(tables_by_id) == {"T1", "T2"}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("table2_time_to_event_performance_summary")
    assert tables_by_id["T2"]["qc_profile"] == "publication_table_performance"
    assert manifest_payload["naming_map"]["tables"]["T2"] == "Table2"
    assert (workspace_root / tables_by_id["T2"]["output_paths"][0]).exists()


def test_create_submission_minimal_package_accepts_table_catalog_csv_and_markdown_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)

    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "title": "Summary table",
                    "paper_role": "main_text",
                    "csv_path": str((paper_root / "tables" / "T1_summary.csv").resolve()),
                    "markdown_path": str((paper_root / "tables" / "T1_summary.md").resolve()),
                }
            ],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["tables"][0]["table_id"] == "T1"
    assert manifest["naming_map"]["tables"]["T1"] == "Table1"
    assert (paper_root / "submission_minimal" / "tables" / "Table1.csv").exists()
    assert (paper_root / "submission_minimal" / "tables" / "Table1.md").exists()


def test_create_submission_minimal_package_accepts_prefixed_catalog_ids_and_direct_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "Figure1",
                    "title": "Main figure",
                    "pdf_path": str((paper_root / "figures" / "F1_main.pdf").resolve()),
                    "png_path": str((paper_root / "figures" / "F1_main.png").resolve()),
                }
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "Table1",
                    "title": "Summary table",
                    "paper_role": "main_text",
                    "csv_path": str((paper_root / "tables" / "T1_summary.csv").resolve()),
                    "markdown_path": str((paper_root / "tables" / "T1_summary.md").resolve()),
                }
            ],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["naming_map"]["figures"]["Figure1"] == "Figure1"
    assert manifest["naming_map"]["tables"]["Table1"] == "Table1"
    assert (paper_root / "submission_minimal" / "figures" / "Figure1.pdf").exists()
    assert (paper_root / "submission_minimal" / "figures" / "Figure1.png").exists()
    assert (paper_root / "submission_minimal" / "tables" / "Table1.csv").exists()
    assert (paper_root / "submission_minimal" / "tables" / "Table1.md").exists()


def test_create_submission_minimal_package_resets_stale_generated_assets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_workspace(tmp_path)

    stale_path = paper_root / "submission_minimal" / "tables" / "stale.txt"
    write_text(stale_path, "stale")

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert not stale_path.exists()
