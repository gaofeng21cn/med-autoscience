from __future__ import annotations

from collections import Counter
from typing import Any

from med_autoscience.display_pack_gallery_catalog import TemplateRecord
from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset
from med_autoscience.display_pack_agent_parts.figure_contract import figure_contract_policy
from med_autoscience.display_pack_agent_parts.figure_workflow import figure_workflow_policy
from med_autoscience.display_pack_agent_parts.composition_recipe_projection import (
    composition_recipe_discovery_payload,
)
from med_autoscience.display_pack_agent_parts.publication_polish_policy import (
    publication_polish_policy,
)
from med_autoscience.display_pack_renderer_policy import (
    R_GGPLOT2_RENDERER,
    renderer_policy_completion,
    renderer_policy_payload,
)


EXTERNAL_QUALITY_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "ref_id": "nature_final_submission_artwork",
        "url": "https://www.nature.com/nature/for-authors/final-submission",
        "lesson": "Use consistent figure lettering, readable reduced-size labels, vector line art when possible, RGB color, and production-quality figure files.",
    },
    {
        "ref_id": "ggplot2_theme_system",
        "url": "https://ggplot2.tidyverse.org/reference/theme.html",
        "lesson": "Use a single theme system for titles, labels, fonts, backgrounds, gridlines, and legends so all evidence figures share one article-level visual grammar.",
    },
    {
        "ref_id": "ggsci_npg_palette",
        "url": "https://nanx.me/ggsci/reference/scale_npg.html",
        "lesson": "Nature Publishing Group inspired discrete palettes are mature ggplot2-compatible references for publication-style categorical roles.",
    },
    {
        "ref_id": "colorspace_hcl_palettes",
        "url": "https://colorspace.r-forge.r-project.org/",
        "lesson": "HCL-based qualitative, sequential and diverging palettes are a stable basis for article-level semantic color roles.",
    },
    {
        "ref_id": "viridis_perceptual_palette",
        "url": "https://sjmgarnier.github.io/viridis/",
        "lesson": "Perceptually uniform and color-vision-friendly sequential palettes are preferred for continuous matrix and density-like encodings.",
    },
    {
        "ref_id": "complexheatmap_color_mapping",
        "url": "https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html",
        "lesson": "Matrix heatmaps need fixed value-to-color mapping rather than per-plot drift; shared sequential and diverging mappings preserve cross-figure comparability.",
    },
    {
        "ref_id": "nature_skills_figure_contract",
        "url": "https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure",
        "lesson": "Figure work should start from core conclusion, evidence chain, panel hierarchy, backend-exclusive export, and final visual QA; MAS adapts this into a nonblocking R-first agent contract.",
    },
)

FAMILY_BASELINE_WARNINGS: dict[str, tuple[str, ...]] = {
    "coefficient_path_panel": ("coefficient_path_semantic_fit_review",),
    "genomic_alteration_landscape_panel": ("oncoprint_annotation_track_review",),
    "kaplan_meier_grouped": ("km_risk_table_and_censor_mark_review",),
    "model_complexity_audit_panel": ("multi_panel_readability_review",),
    "shap_waterfall_local_explanation_panel": ("multi_panel_readability_review",),
}

KIND_BASELINE_WARNINGS: dict[str, tuple[str, ...]] = {
    "illustration_shell": ("illustration_shell_style_review_required",),
}


def _baseline_quality_gates(record: TemplateRecord, asset: RenderedAsset) -> list[str]:
    gates = [
        "template_family_canonicalized",
        "medical_figure_family_mapped" if record.medical_family_ids else "medical_figure_family_missing",
        "starter_recipe_profile_present"
        if record.publication_quality_profile.get("starter_recipe_ids")
        else "starter_recipe_profile_missing",
        "style_palette_qa_profile_present"
        if (
            record.publication_quality_profile.get("style_profile_ids")
            and record.publication_quality_profile.get("palette_token_ids")
            and record.publication_quality_profile.get("qa_gate_ids")
        )
        else "style_palette_qa_profile_missing",
        "square_gallery_preview",
        "vector_export_available" if asset.pdf_ref or asset.svg_ref else "vector_export_missing",
        "semantic_palette_context",
        "synthetic_payload_only",
        "requires_ai_local_adaptation",
        "core_conclusion_before_plotting",
        "evidence_chain_maps_panels_to_claim",
        "journal_export_contract_before_paper_use",
        "final_visual_qa_required",
    ]
    if record.renderer_family == "r_ggplot2":
        gates.append("ggplot2_publication_theme")
        gates.append("r_ggplot2_default_evidence_backend")
    if record.kind == "illustration_shell" and record.renderer_family == "python":
        gates.append("python_renderer_style_alignment_required")
    return gates


def audit_template_quality(record: TemplateRecord, asset: RenderedAsset, baseline: RenderedAsset) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if asset.status != "rendered":
        blockers.append(f"render_status_{asset.status}")
    if record.renderer_family == "n/a" or record.kind == "table_shell":
        blockers.append("non_visual_template_not_gallery_card")
    if not record.medical_family_ids:
        blockers.append("medical_figure_family_mapping_missing")
    if not record.publication_quality_profile.get("starter_recipe_ids"):
        blockers.append("starter_recipe_profile_missing")
    if not record.publication_quality_profile.get("style_profile_ids"):
        blockers.append("style_profile_mapping_missing")
    if not record.publication_quality_profile.get("palette_token_ids"):
        blockers.append("palette_token_mapping_missing")
    if not record.publication_quality_profile.get("qa_gate_ids"):
        blockers.append("qa_gate_mapping_missing")
    if "vector_export_missing" in _baseline_quality_gates(record, asset):
        warnings.append("vector_export_missing")
    if record.kind == "illustration_shell" and record.renderer_family == "python":
        warnings.append("python_renderer_style_alignment_required")
    if record.kind == "evidence_figure" and record.renderer_family == "python":
        blockers.append("python_evidence_retained_without_advantage_proof")
    warnings.extend(FAMILY_BASELINE_WARNINGS.get(record.canonical_family_id, ()))
    warnings.extend(KIND_BASELINE_WARNINGS.get(record.kind, ()))
    if record.canonical_family_category in {"Matrix Pattern", "Model Explanation"}:
        warnings.append("legend_or_colorbar_overlap_risk")
    if record.canonical_family_category in {"Publication Shells and Tables", "Generalizability"}:
        warnings.append("composition_density_risk")

    unique_blockers = sorted(set(blockers))
    unique_warnings = sorted(set(warnings))
    status = "not_publication_ready" if unique_blockers else "lower_bound_review_required"
    return {
        "template_id": record.template_id,
        "canonical_family_id": record.canonical_family_id,
        "canonical_family_title": record.canonical_family_title,
        "category": record.canonical_family_category,
        "renderer_family": record.renderer_family,
        "renderer_policy": renderer_policy_payload(record),
        "medical_family_ids": list(record.medical_family_ids),
        "publication_quality_profile": dict(record.publication_quality_profile),
        "status": status,
        "publication_ready_claim_authorized": False,
        "quality_gates": _baseline_quality_gates(record, asset),
        "blockers": unique_blockers,
        "warnings": unique_warnings,
        "figure_contract_policy_ref": figure_contract_policy()["policy_id"],
        "figure_workflow_policy_ref": figure_workflow_policy()["policy_id"],
        "publication_polish_policy_ref": publication_polish_policy()["policy_id"],
        "recommended_next_actions": recommended_next_actions(record, unique_blockers, unique_warnings),
    }


def recommended_next_actions(record: TemplateRecord, blockers: list[str], warnings: list[str]) -> list[str]:
    actions = [
        "Use this template as a lower-bound starting point; AI may freely alter structure, layout, labels, scale, and composition for the paper-specific claim.",
        "Render-inspect-revise before any paper-facing use; do not accept the synthetic Gallery preview as final artwork.",
    ]
    if "python_renderer_style_alignment_required" in warnings:
        actions.append("Align design-shell typography, palette roles, export discipline, and composition with the MAS publication style profile.")
    if "legend_or_colorbar_overlap_risk" in warnings:
        actions.append("Check guide boxes after rendering; prefer direct labels or horizontal colorbars when tick labels collide.")
    if "km_risk_table_and_censor_mark_review" in warnings:
        actions.append("Verify risk table, censor marks, time scale, and event definition against the paper-local survival estimand.")
    if "oncoprint_annotation_track_review" in warnings:
        actions.append("Verify annotation tracks, sample ordering, alteration semantics, and shared heatmap palette roles.")
    if "multi_panel_readability_review" in warnings:
        actions.append("Rebalance panel hierarchy around the claim-bearing hero panel and recheck final-size labels.")
    if "python_evidence_retained_without_advantage_proof" in blockers:
        actions.append("Retire this Python evidence template or promote it only after documented advantage over the R/ggplot2 baseline and visual audit.")
    if record.kind == "illustration_shell":
        actions.append("Treat shell figures as editorial layouts requiring paper-local composition, not fixed statistical plot templates.")
    return actions


def build_quality_audit(
    *,
    records: list[TemplateRecord],
    visual_records: list[TemplateRecord],
    non_visual_records: list[TemplateRecord],
    default_surface_excluded_records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
) -> dict[str, Any]:
    template_audits = [
        audit_template_quality(
            record,
            rendered[record.template_id],
            baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")),
        )
        for record in visual_records
    ]
    blocker_counts = Counter(
        blocker
        for audit in template_audits
        for blocker in audit["blockers"]
    )
    warning_counts = Counter(
        warning
        for audit in template_audits
        for warning in audit["warnings"]
    )
    blocked_count = sum(1 for audit in template_audits if audit["blockers"])
    ready_like_count = len(template_audits) - blocked_count
    profile_coverage = _publication_quality_profile_coverage(records)
    completion_by_category = _category_completion(
        records=records,
        visual_records=visual_records,
        non_visual_records=non_visual_records,
        default_surface_excluded_records=default_surface_excluded_records,
    )
    composition_recipe_surface = composition_recipe_discovery_payload(include_recipes=True)
    return {
        "schema_version": 1,
        "overall_status": "not_publication_ready",
        "publication_ready_claim_authorized": False,
        "quality_surface": "gallery_lower_bound_visual_audit",
        "visual_template_count": len(visual_records),
        "non_visual_template_count": len(non_visual_records),
        "lower_bound_review_required_count": ready_like_count,
        "blocked_template_count": blocked_count,
        "gallery_lower_bound_admission_status": (
            "gallery_lower_bound_passed_requires_paper_audit"
            if blocked_count == 0 and profile_coverage["complete_profile_percent"] == 100
            else "gallery_lower_bound_blocked"
        ),
        "publication_quality_profile_coverage": profile_coverage,
        "renderer_policy_completion": renderer_policy_completion(
            records
        ),
        "completion_by_category": completion_by_category,
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "quality_policy": {
            "default_gallery_claim": "lower_bound_reference_templates_only",
            "ai_authority": "ai_may_freely_modify_template_structure_layout_palette_labels_and_composition_for_paper_specific_claim",
            "not_authority": "gallery_does_not_authorize_publication_readiness_or_final_artwork_acceptance",
            "current_surface": "canonical_current_templates_not_input_data_specific_variants",
            "composition_recipe_policy": "page_level_recipes_organize_primitives_without_becoming_duplicate_gallery_cards",
            "required_before_paper_use": publication_polish_policy()["required_before_paper_use"],
            "required_workflow_before_paper_use": figure_workflow_policy()["paper_use_acceptance"],
            "composition_recipe_required_before_paper_use": [
                "composition_recipe_selected_or_explicitly_declined",
                "hero_panel_role_declared",
                "shared_legend_or_direct_label_strategy_declared",
                "programmatic_evidence_primitives_preserve_data_statistics_refs",
            ],
            "gallery_lower_bound_admission_requires": [
                "current_template_has_medical_family_mapping",
                "current_template_has_starter_recipe_profile",
                "current_template_has_style_palette_qa_profile",
                "default_gallery_render_has_square_preview",
                "default_gallery_render_has_vector_export_when_possible",
            ],
        },
        "figure_contract_policy": figure_contract_policy(),
        "figure_workflow_policy": figure_workflow_policy(),
        "composition_recipe_surface": composition_recipe_surface,
        "publication_polish_policy": publication_polish_policy(),
        "external_quality_references": list(EXTERNAL_QUALITY_REFERENCES),
        "templates": template_audits,
        "non_visual_inventory": [
            {
                "template_id": record.template_id,
                "canonical_family_id": record.canonical_family_id,
                "canonical_family_title": record.canonical_family_title,
                "kind": record.kind,
                "renderer_family": record.renderer_family,
                "status": "kept_out_of_image_gallery",
            }
            for record in non_visual_records
        ],
        "default_surface_excluded_inventory": [
            {
                "template_id": record.template_id,
                "canonical_family_id": record.canonical_family_id,
                "canonical_family_title": record.canonical_family_title,
                "category": record.canonical_family_category,
                "kind": record.kind,
                "renderer_family": record.renderer_family,
                "status": "kept_out_of_default_gallery",
                "reason": renderer_policy_payload(record)["default_surface_reason"],
            }
            for record in default_surface_excluded_records
        ],
        "retired_alias_inventory": [
            {
                "template_id": alias,
                "canonical_template_id": record.canonical_template_id,
                "canonical_family_id": record.canonical_family_id,
                "status": "retired_alias_not_gallery_card",
            }
            for record in records
            for alias in record.migrated_alias_template_ids
        ],
    }


def _category_completion(
    *,
    records: list[TemplateRecord],
    visual_records: list[TemplateRecord],
    non_visual_records: list[TemplateRecord],
    default_surface_excluded_records: list[TemplateRecord],
) -> list[dict[str, Any]]:
    categories = sorted(
        {
            record.canonical_family_category
            for record in records
        }
    )
    rows: list[dict[str, Any]] = []
    for category in categories:
        visible = [record for record in visual_records if record.canonical_family_category == category]
        explicit_default_excluded = [
            record
            for record in default_surface_excluded_records
            if record.canonical_family_category == category
        ]
        default_r_family_ids = {
            record.canonical_family_id
            for record in visible
            if record.kind == "evidence_figure" and record.renderer_family == R_GGPLOT2_RENDERER
        }
        retained_python_evidence = [
            record
            for record in records
            if record.canonical_family_category == category
            and record.kind == "evidence_figure"
            and record.renderer_family == "python"
        ]
        non_visual = [
            record
            for record in non_visual_records
            if record.canonical_family_category == category
        ]
        evidence = [record for record in visible if record.kind == "evidence_figure"]
        r_evidence = [record for record in evidence if record.renderer_family == R_GGPLOT2_RENDERER]
        status = "done"
        if retained_python_evidence:
            status = "partial"
        if visible or non_visual:
            completion_percent = 100 if not retained_python_evidence else round(
                100 * len(visible) / (len(visible) + len(retained_python_evidence))
            )
        else:
            completion_percent = 0
        rows.append(
            {
                "category": category,
                "status": status,
                "completion_percent": completion_percent,
                "default_visual_families": len(visible),
                "default_r_ggplot2_evidence_families": len(r_evidence),
                "default_non_visual_families": len(non_visual),
                "default_surface_excluded_templates": len(explicit_default_excluded),
                "retained_python_evidence_templates": len(retained_python_evidence),
                "retained_python_evidence_template_ids": [record.template_id for record in retained_python_evidence],
            }
        )
    return rows


def _publication_quality_profile_coverage(records: list[TemplateRecord]) -> dict[str, Any]:
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
    incomplete = set(missing_family) | set(missing_recipe) | set(missing_style) | set(missing_palette) | set(missing_qa)
    complete_count = len(records) - len(incomplete)
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


def build_quality_audit_markdown(audit: dict[str, Any]) -> str:
    blockers = audit["blocker_counts"]
    warnings = audit["warning_counts"]
    polish = audit["publication_polish_policy"]
    workflow = audit["figure_workflow_policy"]
    composition = audit["composition_recipe_surface"]
    blocker_lines = "\n".join(f"| `{key}` | {value} |" for key, value in blockers.items()) or "| none | 0 |"
    warning_lines = "\n".join(f"| `{key}` | {value} |" for key, value in warnings.items()) or "| none | 0 |"
    before_paper_lines = "\n".join(
        f"- `{item}`" for item in polish["required_before_paper_use"]
    )
    workflow_before_paper_lines = "\n".join(
        f"- `{item}`" for item in workflow["paper_use_acceptance"]
    )
    composition_before_paper_lines = "\n".join(
        f"- `{item}`" for item in audit["quality_policy"]["composition_recipe_required_before_paper_use"]
    )
    composition_recipe_lines = "\n".join(
        f"| `{item['recipe_id']}` | {item['title']} | {item['hero_panel_role']} |"
        for item in composition["recipes"]
    )
    high_risk_lines = "\n".join(
        f"| `{item['family']}` | {', '.join(f'`{check}`' for check in item['checks'])} |"
        for item in polish["high_risk_family_checks"]
    )
    template_lines = "\n".join(
        (
            f"| `{item['template_id']}` | {item['category']} | {item['renderer_family']} | "
            f"`{item['status']}` | {', '.join(f'`{blocker}`' for blocker in item['blockers']) or 'none'} |"
        )
        for item in audit["templates"]
    )
    completion_lines = "\n".join(
        (
            f"| {item['category']} | `{item['status']}` | {item['completion_percent']}% | "
            f"{item['default_visual_families']} | {item['default_r_ggplot2_evidence_families']} | "
            f"{item['retained_python_evidence_templates']} |"
        )
        for item in audit["completion_by_category"]
    )
    excluded_lines = "\n".join(
        (
            f"| `{item['template_id']}` | {item['category']} | {item['kind']} | "
            f"{item['renderer_family']} | `{item['reason']}` |"
        )
        for item in audit["default_surface_excluded_inventory"]
    ) or "| none | none | none | none | none |"
    reference_lines = "\n".join(
        f"- [{item['ref_id']}]({item['url']}): {item['lesson']}"
        for item in audit["external_quality_references"]
    )
    return f"""# MAS Display Pack Gallery Quality Audit

Owner: `MedAutoScience`
Purpose: `human_readable_quality_audit_for_display_pack_gallery`
State: `active_support`
Machine boundary: 人读质量审计。机器真相继续归 Gallery manifest、template descriptor、renderer source、layout sidecar、display lock、publication manifest、真实论文 artifact 和 owner receipt。

## 结论

当前 Gallery 是 `lower_bound_reference_templates_only`，不能声明为 publication-ready。模板提供质量下限和图型结构参考；AI 被授权按论文具体主张自由修改结构、排版、标签、配色和组合方式来拔高上限。

- overall_status: `{audit["overall_status"]}`
- publication_ready_claim_authorized: `{str(audit["publication_ready_claim_authorized"]).lower()}`
- visual template count: `{audit["visual_template_count"]}`
- non-visual inventory count: `{audit["non_visual_template_count"]}`
- lower-bound review required: `{audit["lower_bound_review_required_count"]}`
- blocked templates: `{audit["blocked_template_count"]}`
- publication polish policy: `{polish["policy_id"]}`
- figure workflow policy: `{workflow["policy_id"]}`
- composition recipe policy: `{composition["policy"]["policy_id"]}`
- composition recipes: `{composition["composition_recipe_count"]}`

## Paper-use 前置检查

{before_paper_lines}

## Figure Workflow 前置检查

{workflow_before_paper_lines}

## Composition Recipe 前置检查

{composition_before_paper_lines}

## 页面级 Composition Recipes

| Recipe | Title | Hero panel |
| --- | --- | --- |
{composition_recipe_lines}

## 高风险图族复核项

| Family | Checks |
| --- | --- |
{high_risk_lines}

## 主要阻断项

| Blocker | Templates |
| --- | ---: |
{blocker_lines}

## 主要风险项

| Warning | Templates |
| --- | ---: |
{warning_lines}

## 模板审计

| Template | Category | Renderer | Status | Blockers |
| --- | --- | --- | --- | --- |
{template_lines}

## 分类完成度

| Category | Status | Completion | Gallery visual | R/ggplot2 evidence | Current Python evidence |
| --- | --- | ---: | ---: | ---: | ---: |
{completion_lines}

## 当前 Python Evidence

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | evidence_figure | python | current_pack_retains_no_python_evidence_templates |

## 默认面排除的非视觉库存

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
{excluded_lines}

## 外部准则

{reference_lines}
"""
