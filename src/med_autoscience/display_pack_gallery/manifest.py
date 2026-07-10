from __future__ import annotations

from collections import Counter
import json
from typing import Any

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_agent.figure_contract import figure_contract_policy
from med_autoscience.display_pack_agent.figure_workflow import figure_workflow_policy
from med_autoscience.display_pack_agent.composition_recipe_projection import (
    composition_recipe_discovery_payload,
)
from med_autoscience.display_pack_agent.publication_polish_policy import (
    publication_polish_policy,
)
from med_autoscience.display_pack_gallery_catalog import (
    TemplateRecord,
    ai_adaptation_policy,
    canonical_category_ontology,
    canonical_family_ontology,
    canonical_family_wording,
    canonical_catalog_default_records,
    canonical_records,
    default_surface_excluded_records,
    design_gallery_records,
    figure_family_policy,
    gallery_display_records,
    gallery_visual_records,
    gallery_template_family_ontology,
    non_visual_canonical_records,
    paper_derived_reference_records,
    reporting_flow_gallery_records,
    table_preview_gallery_records,
    visual_gallery_records,
)
from med_autoscience.display_pack_dependency_environment import (
    dependency_requirements_for_template_ids,
)
from med_autoscience.display_pack_renderer_policy import (
    default_surface_renderer_policy,
    renderer_policy_completion,
    renderer_policy_payload,
)
from med_autoscience.display_pack_gallery import paths
from med_autoscience.display_pack_gallery.assets import RenderedAsset
from med_autoscience.display_pack_gallery.composition_gallery import (
    build_composition_gallery_surface,
)
from med_autoscience.display_pack_gallery.lidocaineq_coverage import (
    LIDOCAINEQ_COVERAGE_ITEMS,
    lidocaineq_coverage_payload,
)
from med_autoscience.display_pack_gallery.quality import build_quality_audit


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
        "dependency_environment": dict(asset.dependency_environment or {}),
    }


def _layout_sidecar_path(asset: RenderedAsset) -> Any:
    if not asset.layout_ref:
        return None
    return paths.HTML_PATH.parent / asset.layout_ref


def _read_layout_sidecar(asset: RenderedAsset) -> dict[str, Any]:
    layout_path = _layout_sidecar_path(asset)
    if layout_path is None or not layout_path.is_file():
        return {}
    payload = json.loads(layout_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _layout_sidecar_readback(
    *,
    visual_records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
) -> dict[str, Any]:
    expected_style_profile_id = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["style_profile_id"]
    expected_journal_palette_ref = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["journal_palette_ref"]
    required_renderer_fields = (
        "renderer",
        "renderer_family",
        "renderer_role",
        "template_id",
        "data_fields",
        "panel_box_present",
    )
    rendered_template_ids: list[str] = []
    missing_renderer_metrics: list[str] = []
    unexpected_renderer_metrics: list[str] = []
    missing_style_profile: list[str] = []
    mismatched_style_profile: list[str] = []
    native_ratio_previews: list[str] = []
    for record in visual_records:
        asset = rendered[record.template_id]
        if asset.status != "rendered":
            continue
        rendered_template_ids.append(record.template_id)
        if asset.preview_image_ref == asset.image_ref:
            native_ratio_previews.append(record.template_id)
        sidecar = _read_layout_sidecar(asset)
        metrics = sidecar.get("metrics")
        if not isinstance(metrics, dict) or any(field not in metrics for field in required_renderer_fields):
            missing_renderer_metrics.append(record.template_id)
        elif metrics.get("renderer_family") != "r_ggplot2" or metrics.get("renderer_role") != "default":
            unexpected_renderer_metrics.append(record.template_id)
        style_profile = sidecar.get("style_profile")
        if not isinstance(style_profile, dict):
            missing_style_profile.append(record.template_id)
            continue
        if (
            style_profile.get("style_profile_id") != expected_style_profile_id
            or style_profile.get("journal_palette_ref") != expected_journal_palette_ref
        ):
            mismatched_style_profile.append(record.template_id)
    return {
        "schema_version": 1,
        "rendered_layout_sidecar_count": len(rendered_template_ids),
        "renderer_metrics_template_count": len(rendered_template_ids) - len(missing_renderer_metrics),
        "expected_renderer_family": "r_ggplot2",
        "expected_renderer_role": "default",
        "required_renderer_metric_fields": list(required_renderer_fields),
        "missing_renderer_metrics": missing_renderer_metrics,
        "unexpected_renderer_metrics": unexpected_renderer_metrics,
        "style_profile_template_count": len(rendered_template_ids) - len(missing_style_profile),
        "expected_style_profile_id": expected_style_profile_id,
        "expected_journal_palette_ref": expected_journal_palette_ref,
        "missing_style_profile": missing_style_profile,
        "mismatched_style_profile": mismatched_style_profile,
        "native_ratio_preview_template_count": len(native_ratio_previews),
        "native_ratio_previews": native_ratio_previews,
    }


def _source_renderer_readback(rendered: dict[str, RenderedAsset]) -> dict[str, str]:
    source_renderers: dict[str, str] = {}
    for template_id, asset in rendered.items():
        if asset.status != "rendered":
            continue
        sidecar = _read_layout_sidecar(asset)
        metrics = sidecar.get("metrics")
        if not isinstance(metrics, dict):
            continue
        source_renderer = metrics.get("source_renderer")
        if isinstance(source_renderer, str) and source_renderer.strip():
            source_renderers[template_id] = source_renderer.strip()
    return source_renderers


def _dependency_environment_readback(rendered: dict[str, RenderedAsset]) -> dict[str, Any]:
    tracked = {
        template_id: dict(asset.dependency_environment or {})
        for template_id, asset in rendered.items()
        if asset.dependency_environment
    }
    statuses = Counter(
        value.get("status", "unknown")
        for value in tracked.values()
    )
    prepared = {
        template_id: value
        for template_id, value in tracked.items()
        if value.get("status") == "prepared"
    }
    run_context_fingerprints = sorted(
        {
            value.get("run_context_fingerprint", "")
            for value in prepared.values()
            if value.get("run_context_fingerprint")
        }
    )
    return {
        "schema_version": 1,
        "tracked_template_count": len(tracked),
        "status_counts": dict(sorted(statuses.items())),
        "prepared_template_count": len(prepared),
        "prepared_template_ids": sorted(prepared),
        "run_context_fingerprints": run_context_fingerprints,
        "templates": tracked,
    }


def build_manifest(
    *,
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
    publish_docs: bool,
    render_cache_summary: dict[str, int] | None = None,
    force_render: bool = False,
    package_only: bool = False,
) -> dict[str, Any]:
    visual_records = gallery_display_records(records)
    design_records = design_gallery_records(records)
    reporting_flow_records = reporting_flow_gallery_records(records)
    table_preview_records = table_preview_gallery_records(records)
    all_gallery_visual_records = gallery_visual_records(records)
    canonical_visual_records = visual_gallery_records(records)
    non_visual_records = non_visual_canonical_records(records)
    catalog_default_records = canonical_catalog_default_records(records)
    default_excluded_records = default_surface_excluded_records(records)
    paper_derived_records = paper_derived_reference_records(records)
    lidocaineq_preview_template_ids = {item.mas_template_id for item in LIDOCAINEQ_COVERAGE_ITEMS}
    canonical_rendered_count = sum(
        1
        for record in visual_records
        if rendered[record.template_id].status == "rendered"
    )
    design_rendered_count = sum(
        1
        for record in [*reporting_flow_records, *design_records, *table_preview_records]
        if rendered[record.template_id].status == "rendered"
    )
    internal_rendered_count = sum(
        1
        for asset in rendered.values()
        if asset.status == "rendered"
    )
    quality_audit = build_quality_audit(
        records=records,
        visual_records=visual_records,
        non_visual_records=non_visual_records,
        design_records=design_records,
        reporting_flow_records=reporting_flow_records,
        table_preview_records=table_preview_records,
        default_surface_excluded_records=default_excluded_records,
        rendered=rendered,
        baseline_rendered=baseline_rendered,
    )
    layout_sidecar_readback = _layout_sidecar_readback(
        visual_records=visual_records,
        rendered=rendered,
    )
    palette = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["palette"]
    composition_recipe_surface = composition_recipe_discovery_payload(include_recipes=True)
    composition_gallery_surface = build_composition_gallery_surface(composition_recipe_surface, records)
    lidocaineq_coverage = lidocaineq_coverage_payload(
        rendered_by_template_id=rendered,
        source_renderer_by_template_id=_source_renderer_readback(rendered),
    )
    dependency_environment_readback = _dependency_environment_readback(rendered)
    return {
        "schema_version": 9,
        "status": "rendered",
        "force_render": force_render,
        "package_only": package_only,
        "render_cache_summary": dict(render_cache_summary or {}),
        "dependency_environment_readback": dependency_environment_readback,
        "html_path": str(paths.HTML_PATH),
        "pdf_path": str(paths.PDF_PATH),
        "quality_audit_path": str(paths.QUALITY_AUDIT_PATH),
        "docs_template_catalog_path": str(paths.DOCS_TEMPLATE_CATALOG_PATH) if publish_docs else "",
        "docs_gallery_review_package_owner": "ScholarSkills",
        "docs_gallery_review_package_ref": "/Users/gaofeng/workspace/mas-scholar-skills/gallery/medical-display/",
        "docs_gallery_review_package_status": "externalized_compact_review_refs",
        "template_count": len(all_gallery_visual_records),
        "active_template_count": len(visual_records),
        "evidence_gallery_template_count": len(visual_records),
        "lidocaineq_reference_template_count": len(LIDOCAINEQ_COVERAGE_ITEMS),
        "reporting_flow_gallery_template_count": len(reporting_flow_records),
        "design_gallery_template_count": len(design_records),
        "table_preview_gallery_template_count": len(table_preview_records),
        "visual_gallery_template_count": len(all_gallery_visual_records),
        "composition_recipe_gallery_count": composition_gallery_surface["composition_recipe_count"],
        "non_visual_canonical_template_count": len(non_visual_records),
        "current_template_count": len(catalog_default_records),
        "migration_inventory_template_count": len(records),
        "retired_alias_template_count": sum(
            len(record.migrated_alias_template_ids)
            for record in records
            if record.migration_status == "canonical"
        ),
        "canonical_family_count": len(canonical_family_ontology()),
        "gallery_template_family_count": len({record.canonical_family_id for record in canonical_visual_records}),
        "canonical_representative_template_count": len(canonical_visual_records),
        "canonical_template_count": sum(1 for record in records if record.migration_status == "canonical"),
        "catalog_default_visible_template_count": len(catalog_default_records),
        "default_visible_template_count": len(canonical_records(records)),
        "default_surface_excluded_template_count": len(default_excluded_records),
        "paper_derived_reference_template_count": len(paper_derived_records),
        "legacy_alias_template_count": sum(1 for record in records if record.migration_status == "migrated_alias"),
        "rendered_image_template_count": canonical_rendered_count,
        "rendered_design_image_template_count": design_rendered_count,
        "rendered_visual_gallery_template_count": canonical_rendered_count + design_rendered_count,
        "internal_rendered_image_template_count": internal_rendered_count,
        "renderer_family_counts": dict(sorted(Counter(record.renderer_family for record in records).items())),
        "style_profile_id": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["style_profile_id"],
        "journal_palette_ref": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["journal_palette_ref"],
        "palette_policy": {
            "style_profile_id": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["style_profile_id"],
            "journal_palette_ref": display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD["journal_palette_ref"],
            "categorical_roles": ["series_1", "series_2", "series_3", "series_4", "series_5", "series_6"],
            "heatmap_sequential_roles": ["heatmap_seq_low", "heatmap_seq_mid", "heatmap_seq_high"],
            "heatmap_diverging_roles": ["heatmap_low", "heatmap_mid", "heatmap_high"],
            "heatmap_sequential_palette": {
                key: palette[key]
                for key in ("heatmap_seq_low", "heatmap_seq_mid", "heatmap_seq_high")
            },
            "heatmap_diverging_palette": {
                key: palette[key]
                for key in ("heatmap_low", "heatmap_mid", "heatmap_high")
            },
            "matrix_heatmap_uses_shared_palette_roles": True,
        },
        "preview_device": {
            "policy": "template_reference_ratio",
            "fallback_width_in": 5.0,
            "fallback_height_in": 5.0,
        },
        "nature_skills_observed_head": paths.NATURE_SKILLS_HEAD,
        "categories": dict(Counter(record.canonical_family_category for record in visual_records)),
        "non_visual_categories": dict(Counter(record.canonical_family_category for record in non_visual_records)),
        "figure_family_policy": figure_family_policy(),
        "renderer_policy": default_surface_renderer_policy(),
        "renderer_policy_completion": renderer_policy_completion(records),
        "analysis_responsibility_counts": dict(
            sorted(
                Counter(
                    record.analysis_responsibility
                    for record in records
                    if record.default_visible
                ).items()
            )
        ),
        "analysis_responsibility_policy": {
            "computed_in_template": "Template renderer computes a bounded analysis workflow from declared raw input.",
            "validated_summary_required": "Template renderer accepts upstream validated analysis output only.",
            "illustration_shell": "Template is a non-statistical design or flow shell.",
            "table_shell": "Template accepts reviewed table values only.",
            "raw_request_fail_closed": True,
        },
        "publication_quality_profile_coverage": _publication_quality_profile_coverage(records),
        "layout_sidecar_readback": layout_sidecar_readback,
        "ai_adaptation_policy": ai_adaptation_policy(),
        "figure_contract_policy": figure_contract_policy(),
        "figure_workflow_policy": figure_workflow_policy(),
        "composition_recipe_surface": composition_recipe_surface,
        "composition_gallery_surface": composition_gallery_surface,
        "lidocaineq_reference_coverage": lidocaineq_coverage,
        "publication_polish_policy": publication_polish_policy(),
        "quality_audit": quality_audit,
        "canonical_category_ontology": canonical_category_ontology(),
        "canonical_family_ontology": canonical_family_ontology(),
        "gallery_template_family_ontology": gallery_template_family_ontology(records),
        "template_surface_policy": {
            "gallery_default_surface": "canonical_current_visual_gallery_templates",
            "evidence_gallery_default_surface": "canonical_current_r_ggplot2_evidence_templates",
            "reporting_flow_gallery_default_surface": "canonical_current_validated_reporting_flow_shells",
            "design_gallery_default_surface": "canonical_current_non_statistical_illustration_shell_templates",
            "table_preview_gallery_default_surface": "canonical_current_table_shell_preview_templates",
            "active_inventory_is_canonical_current_templates": True,
            "canonical_representatives_are_evidence_gallery_card_filter": True,
            "illustration_shells_are_design_gallery_cards": True,
            "validated_reporting_flow_shells_are_separate_gallery_cards": True,
            "table_shells_keep_table_authority_but_may_have_gallery_preview_cards": True,
            "canonical_non_visual_inventory_preserved_in_manifest": True,
            "migrated_alias_templates_rendered_when_they_are_current_r_ggplot2_evidence": False,
            "explicit_alias_requests_migrate_to_canonical_template": True,
            "evidence_figures_default_to_r_ggplot2": True,
            "python_evidence_templates_not_retained_without_advantage_proof": True,
            "python_illustration_shells_are_visible_design_gallery_cards": True,
            "python_illustration_shells_may_exist_but_are_not_mixed_into_ggplot2_evidence_gallery": True,
            "template_analysis_responsibility_required": True,
            "raw_analysis_inputs_must_match_computed_workflow_templates": True,
            "validated_summary_templates_fail_closed_on_raw_analysis_requests": True,
            "reporting_flow_dependency_profile": "r_ggplot2_ggconsort_reporting_flow_v1",
            "reporting_flow_requires_ggconsort_capable_prepared_environment": True,
            "reporting_flow_generated_fallback_claims_ggconsort": False,
            "medical_figure_family_mapping_required": True,
            "starter_recipe_profile_required": True,
            "style_palette_qa_profile_required": True,
            "composition_recipe_routing_required": True,
            "composition_recipes_are_page_level_not_gallery_cards": True,
            "composition_recipes_are_visible_in_gallery_storyboard_section": True,
        },
        "templates": [
            _template_payload(
                record,
                rendered[record.template_id],
            )
            for record in visual_records
        ],
        "reporting_flow_gallery_templates": [
            _template_payload(
                record,
                rendered[record.template_id],
                visual_gallery_visible=True,
            )
            for record in reporting_flow_records
        ],
        "design_gallery_templates": [
            _template_payload(
                record,
                rendered[record.template_id],
                visual_gallery_visible=True,
            )
            for record in design_records
        ],
        "table_preview_gallery_templates": [
            _template_payload(
                record,
                rendered[record.template_id],
                visual_gallery_visible=True,
            )
            for record in table_preview_records
        ],
        "non_visual_inventory": [
            _template_payload(
                record,
                rendered[record.template_id],
                visual_gallery_visible=record in [*reporting_flow_records, *design_records, *table_preview_records] or record.template_id in lidocaineq_preview_template_ids,
            )
            for record in non_visual_records
        ],
        "default_surface_excluded_inventory": [
            _template_payload(
                record,
                rendered[record.template_id],
            )
            for record in default_excluded_records
        ],
        "paper_derived_reference_inventory": [
            _template_payload(
                record,
                rendered[record.template_id],
                visual_gallery_visible=False,
            )
            for record in paper_derived_records
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
                "renderer_policy": renderer_policy_payload(record),
            }
            for record in records
        ],
        "retired_alias_index": [
            {
                "template_id": alias,
                "canonical_family_id": record.canonical_family_id,
                "canonical_template_id": record.canonical_template_id,
                "migration_status": "retired_alias",
                "default_visible": False,
                "visual_gallery_visible": False,
                "migration_reason": record.migration_reason,
            }
            for record in records
            if record.migration_status == "canonical"
            for alias in record.migrated_alias_template_ids
        ],
    }


def _template_payload(
    record: TemplateRecord,
    asset: RenderedAsset,
    *,
    visual_gallery_visible: bool | None = None,
) -> dict[str, Any]:
    if visual_gallery_visible is None:
        visual_gallery_visible = record.kind == "evidence_figure" and record.renderer_family == "r_ggplot2"
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
        "analysis_responsibility": record.analysis_responsibility,
        "analysis_input_state": record.analysis_input_state,
        "medical_family_ids": list(record.medical_family_ids),
        "publication_quality_profile": dict(record.publication_quality_profile),
        "migration_status": record.migration_status,
        "resource_class": record.resource_class,
        "default_visible": record.default_visible,
        "visual_gallery_visible": visual_gallery_visible,
        "migrated_alias_template_ids": list(record.migrated_alias_template_ids),
        "migration_reason": record.migration_reason,
        "kind": record.kind,
        "renderer_family": record.renderer_family,
        "execution_mode": record.execution_mode,
        "paper_proven": record.paper_proven,
        "paper_provenance_refs": list(record.paper_provenance_refs),
        "renderer_policy": renderer_policy_payload(record),
        "dependency_requirements": dependency_requirements_for_template_ids(
            repo_root=paths.REPO_ROOT,
            template_ids={record.template_id, record.full_template_id},
        ),
        "dependency_environment": dict(asset.dependency_environment or {}),
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
        "render_cache_status": asset.render_cache_status,
        "render_cache_key": asset.render_cache_key,
    }


def _publication_quality_profile_coverage(records: list[TemplateRecord]) -> dict[str, Any]:
    records = [record for record in records if record.default_visible]
    missing_family = sorted(record.template_id for record in records if not record.medical_family_ids)
    missing_recipe = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("starter_recipe_ids")
    )
    missing_style = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("style_profile_ids")
    )
    missing_palette = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("palette_token_ids")
    )
    missing_qa = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("qa_gate_ids")
    )
    complete_count = len(records) - len(
        set(missing_family) | set(missing_recipe) | set(missing_style) | set(missing_palette) | set(missing_qa)
    )
    return {
        "schema_version": 1,
        "current_template_count": len(records),
        "complete_profile_template_count": complete_count,
        "complete_profile_percent": round(100 * complete_count / len(records)) if records else 0,
        "medical_family_missing_template_ids": missing_family,
        "starter_recipe_missing_template_ids": missing_recipe,
        "style_profile_missing_template_ids": missing_style,
        "palette_token_missing_template_ids": missing_palette,
        "qa_gate_missing_template_ids": missing_qa,
    }
