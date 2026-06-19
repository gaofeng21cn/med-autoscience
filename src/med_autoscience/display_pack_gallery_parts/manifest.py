from __future__ import annotations

from collections import Counter
from typing import Any

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_gallery_catalog import (
    TemplateRecord,
    ai_adaptation_policy,
    canonical_category_ontology,
    canonical_family_ontology,
    canonical_family_wording,
    canonical_records,
    figure_family_policy,
    gallery_template_family_ontology,
    non_visual_canonical_records,
    visual_gallery_records,
)
from med_autoscience.display_pack_gallery_parts import paths
from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset
from med_autoscience.display_pack_gallery_parts.quality import build_quality_audit
from med_autoscience.display_pack_gallery_parts.taxonomy import LEGACY_PYTHON_BASELINE_EXCLUDED


def _asset_payload(asset: RenderedAsset) -> dict[str, Any]:
    return {
        "status": asset.status,
        "reason": asset.reason,
        "image_ref": asset.image_ref,
        "preview_image_ref": asset.preview_image_ref,
        "payload_ref": asset.payload_ref,
        "layout_ref": asset.layout_ref,
        "pdf_ref": asset.pdf_ref,
        "svg_ref": asset.svg_ref,
        "image_size_px": list(asset.image_size_px),
        "preview_image_size_px": list(asset.preview_image_size_px),
    }


def build_manifest(
    *,
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
    publish_docs: bool,
) -> dict[str, Any]:
    visual_records = visual_gallery_records(records)
    non_visual_records = non_visual_canonical_records(records)
    canonical_rendered_count = sum(
        1
        for record in visual_records
        if rendered[record.template_id].status == "rendered"
    )
    internal_rendered_count = sum(
        1
        for asset in rendered.values()
        if asset.status == "rendered"
    )
    baseline_rendered_count = sum(1 for asset in baseline_rendered.values() if asset.status == "rendered")
    quality_audit = build_quality_audit(
        visual_records=visual_records,
        non_visual_records=non_visual_records,
        rendered=rendered,
        baseline_rendered=baseline_rendered,
    )
    return {
        "schema_version": 6,
        "status": "rendered",
        "html_path": str(paths.HTML_PATH),
        "pdf_path": str(paths.PDF_PATH),
        "quality_audit_path": str(paths.QUALITY_AUDIT_PATH),
        "docs_pdf_path": str(paths.DOCS_PDF_PATH) if publish_docs else "",
        "docs_reference_path": str(paths.DOCS_REFERENCE_PATH) if publish_docs else "",
        "docs_quality_audit_path": str(paths.DOCS_QUALITY_AUDIT_PATH) if publish_docs else "",
        "template_count": len(visual_records),
        "active_template_count": len(visual_records),
        "non_visual_canonical_template_count": len(non_visual_records),
        "migration_inventory_template_count": len(records),
        "canonical_family_count": len(canonical_family_ontology()),
        "gallery_template_family_count": len({record.canonical_family_id for record in visual_records}),
        "canonical_template_count": sum(1 for record in records if record.migration_status == "canonical"),
        "default_visible_template_count": len(canonical_records(records)),
        "legacy_alias_template_count": sum(1 for record in records if record.migration_status == "migrated_alias"),
        "rendered_image_template_count": canonical_rendered_count,
        "internal_rendered_image_template_count": internal_rendered_count,
        "legacy_python_baseline_rendered_count": baseline_rendered_count,
        "renderer_family_counts": dict(sorted(Counter(record.renderer_family for record in records).items())),
        "style_profile_id": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["style_profile_id"],
        "journal_palette_ref": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["journal_palette_ref"],
        "preview_device": {"width_in": 5.0, "height_in": 5.0},
        "nature_skills_observed_head": paths.NATURE_SKILLS_HEAD,
        "excluded_legacy_python_baselines": list(LEGACY_PYTHON_BASELINE_EXCLUDED),
        "categories": dict(Counter(record.canonical_family_category for record in visual_records)),
        "non_visual_categories": dict(Counter(record.canonical_family_category for record in non_visual_records)),
        "figure_family_policy": figure_family_policy(),
        "ai_adaptation_policy": ai_adaptation_policy(),
        "quality_audit": quality_audit,
        "canonical_category_ontology": canonical_category_ontology(),
        "canonical_family_ontology": canonical_family_ontology(),
        "gallery_template_family_ontology": gallery_template_family_ontology(records),
        "template_surface_policy": {
            "gallery_default_surface": "visual_canonical_families_only",
            "active_inventory_is_visual_canonical_only": True,
            "canonical_non_visual_inventory_preserved_in_manifest": True,
            "migration_inventory_preserved_in_manifest": True,
            "migrated_alias_templates_hidden_from_default_cards": True,
            "explicit_alias_requests_migrate_to_canonical_template": True,
        },
        "templates": [
            _template_payload(
                record,
                rendered[record.template_id],
                baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")),
            )
            for record in visual_records
        ],
        "non_visual_inventory": [
            _template_payload(
                record,
                rendered[record.template_id],
                baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")),
            )
            for record in non_visual_records
        ],
        "migration_index": [
            {
                "template_id": record.template_id,
                "canonical_family_id": record.canonical_family_id,
                "canonical_template_id": record.canonical_template_id,
                "migration_status": record.migration_status,
                "default_visible": record.default_visible,
                "visual_gallery_visible": record in visual_records,
                "migration_reason": record.migration_reason,
            }
            for record in records
        ],
    }


def _template_payload(record: TemplateRecord, asset: RenderedAsset, baseline: RenderedAsset) -> dict[str, Any]:
    return {
        "template_id": record.template_id,
        "display_name": record.display_name,
        "audit_family": record.audit_family,
        "canonical_family_id": record.canonical_family_id,
        "canonical_family_title": record.canonical_family_title,
        "canonical_family_category": record.canonical_family_category,
        "canonical_template_id": record.canonical_template_id,
        "figure_archetype": record.figure_archetype,
        "canonical_family_wording": canonical_family_wording(record),
        "migration_status": record.migration_status,
        "default_visible": record.default_visible,
        "visual_gallery_visible": record.kind != "table_shell" and record.renderer_family != "n/a",
        "migrated_alias_template_ids": list(record.migrated_alias_template_ids),
        "migration_reason": record.migration_reason,
        "kind": record.kind,
        "renderer_family": record.renderer_family,
        "execution_mode": record.execution_mode,
        "paper_proven": record.paper_proven,
        "render_status": asset.status,
        "render_reason": asset.reason,
        "image_size_px": list(asset.image_size_px),
        "image_ref": asset.image_ref,
        "preview_image_size_px": list(asset.preview_image_size_px),
        "preview_image_ref": asset.preview_image_ref,
        "payload_ref": asset.payload_ref,
        "layout_ref": asset.layout_ref,
        "pdf_ref": asset.pdf_ref,
        "svg_ref": asset.svg_ref,
        "legacy_python_baseline": _asset_payload(baseline),
    }
