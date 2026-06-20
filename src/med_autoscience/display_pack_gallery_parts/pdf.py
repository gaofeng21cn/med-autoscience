from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from med_autoscience.display_pack_gallery_parts import paths


def _export_pdf() -> None:
    chrome_candidates = (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    )
    chrome = next((str(path) for path in chrome_candidates if path.exists()), None)
    if chrome is None:
        chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome is None:
        raise RuntimeError("Chrome/Chromium is required to export the gallery PDF")
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={paths.PDF_PATH}",
            f"file://{paths.HTML_PATH}",
        ],
        check=True,
        cwd=paths.REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
    )


def _copy_docs_gallery() -> None:
    paths.DOCS_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths.PDF_PATH, paths.DOCS_PDF_PATH)
    shutil.copy2(paths.REFERENCE_PATH, paths.DOCS_REFERENCE_PATH)
    shutil.copy2(paths.QUALITY_AUDIT_PATH, paths.DOCS_QUALITY_AUDIT_PATH)
    shutil.copy2(paths.STATUS_PATH, paths.DOCS_STATUS_PATH)
    _write_docs_manifest()


def _repo_relative_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        return value
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return value


def _write_docs_manifest() -> None:
    payload: dict[str, Any] = json.loads(paths.MANIFEST_PATH.read_text(encoding="utf-8"))
    docs_payload = _docs_manifest_payload(payload)
    paths.DOCS_MANIFEST_PATH.write_text(
        json.dumps(docs_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _docs_manifest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    path_fields = {
        key: _repo_relative_path(value)
        for key, value in payload.items()
        if key.endswith("_path") and isinstance(value, str)
    }
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_gallery_docs_manifest",
        "source_manifest_schema_version": payload.get("schema_version"),
        "status": payload.get("status"),
        **path_fields,
        "evidence_gallery_template_count": payload.get("evidence_gallery_template_count"),
        "reporting_flow_gallery_template_count": payload.get("reporting_flow_gallery_template_count"),
        "design_gallery_template_count": payload.get("design_gallery_template_count"),
        "visual_gallery_template_count": payload.get("visual_gallery_template_count"),
        "composition_recipe_gallery_count": payload.get("composition_recipe_gallery_count"),
        "current_template_count": payload.get("current_template_count"),
        "non_visual_canonical_template_count": payload.get("non_visual_canonical_template_count"),
        "retired_alias_template_count": payload.get("retired_alias_template_count"),
        "style_profile_id": payload.get("style_profile_id"),
        "journal_palette_ref": payload.get("journal_palette_ref"),
        "template_surface_policy": payload.get("template_surface_policy"),
        "palette_policy": payload.get("palette_policy"),
        "renderer_policy_completion": payload.get("renderer_policy_completion"),
        "analysis_responsibility_counts": payload.get("analysis_responsibility_counts"),
        "quality_summary": _quality_summary(payload),
        "composition_recipe_surface": payload.get("composition_recipe_surface"),
        "composition_gallery_surface": payload.get("composition_gallery_surface"),
        "evidence_gallery_templates": [
            {
                "template_id": item.get("template_id"),
                "canonical_family_id": item.get("canonical_family_id"),
                "canonical_family_title": item.get("canonical_family_title"),
                "canonical_family_category": item.get("canonical_family_category"),
                "renderer_family": item.get("renderer_family"),
                "analysis_responsibility": item.get("analysis_responsibility"),
                "medical_family_ids": item.get("medical_family_ids"),
                "preview_image_ref": item.get("preview_image_ref"),
                "pdf_ref": item.get("pdf_ref"),
                "layout_ref": item.get("layout_ref"),
            }
            for item in payload.get("templates", [])
            if isinstance(item, dict)
        ],
        "reporting_flow_gallery_templates": [
            {
                "template_id": item.get("template_id"),
                "canonical_family_id": item.get("canonical_family_id"),
                "canonical_family_title": item.get("canonical_family_title"),
                "canonical_family_category": item.get("canonical_family_category"),
                "renderer_family": item.get("renderer_family"),
                "analysis_responsibility": item.get("analysis_responsibility"),
                "analysis_input_state": item.get("analysis_input_state"),
                "medical_family_ids": item.get("medical_family_ids"),
                "preview_image_ref": item.get("preview_image_ref"),
                "image_ref": item.get("image_ref"),
                "svg_ref": item.get("svg_ref"),
                "pdf_ref": item.get("pdf_ref"),
                "layout_ref": item.get("layout_ref"),
            }
            for item in payload.get("reporting_flow_gallery_templates", [])
            if isinstance(item, dict)
        ],
        "design_gallery_templates": [
            {
                "template_id": item.get("template_id"),
                "canonical_family_id": item.get("canonical_family_id"),
                "canonical_family_title": item.get("canonical_family_title"),
                "canonical_family_category": item.get("canonical_family_category"),
                "renderer_family": item.get("renderer_family"),
                "analysis_responsibility": item.get("analysis_responsibility"),
                "medical_family_ids": item.get("medical_family_ids"),
                "preview_image_ref": item.get("preview_image_ref"),
                "image_ref": item.get("image_ref"),
                "svg_ref": item.get("svg_ref"),
                "pdf_ref": item.get("pdf_ref"),
                "layout_ref": item.get("layout_ref"),
            }
            for item in payload.get("design_gallery_templates", [])
            if isinstance(item, dict)
        ],
    }


def _quality_summary(payload: dict[str, Any]) -> dict[str, Any]:
    quality = payload.get("quality_audit")
    if not isinstance(quality, dict):
        return {}
    return {
        "overall_status": quality.get("overall_status"),
        "publication_ready_claim_authorized": quality.get("publication_ready_claim_authorized"),
        "visual_template_count": quality.get("visual_template_count"),
        "design_visual_template_count": quality.get("design_visual_template_count"),
        "total_gallery_visual_template_count": quality.get("total_gallery_visual_template_count"),
        "non_visual_template_count": quality.get("non_visual_template_count"),
        "blocked_template_count": quality.get("blocked_template_count"),
        "lower_bound_review_required_count": quality.get("lower_bound_review_required_count"),
        "gallery_lower_bound_admission_status": quality.get("gallery_lower_bound_admission_status"),
        "publication_quality_profile_coverage": quality.get("publication_quality_profile_coverage"),
    }
