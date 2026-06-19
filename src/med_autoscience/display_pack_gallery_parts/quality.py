from __future__ import annotations

from collections import Counter
from typing import Any

from med_autoscience.display_pack_gallery_catalog import TemplateRecord
from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset
from med_autoscience.display_pack_renderer_policy import (
    R_GGPLOT2_RENDERER,
    renderer_policy_completion,
    renderer_policy_payload,
)


EXTERNAL_QUALITY_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "ref_id": "nature_final_submission_artwork",
        "url": "https://www.nature.com/nature/for-authors/final-submission",
        "lesson": "Use consistent sans-serif figure lettering, readable reduced-size labels, vector line art when possible, 0.25-1 pt final line weights, RGB color, and production-quality figure files.",
    },
    {
        "ref_id": "plos_figure_guidelines",
        "url": "https://journals.plos.org/plosone/s/figures",
        "lesson": "Keep figures at intended dimensions, 300-600 dpi, fonts in the 8-12 pt range for submitted artwork, and avoid low-resolution or upsampled elements.",
    },
    {
        "ref_id": "ggsci",
        "url": "https://github.com/nanxstats/ggsci",
        "lesson": "Scientific-journal-inspired palettes are useful references, but MAS keeps one semantic clinical palette instead of exposing many style presets.",
    },
    {
        "ref_id": "ggpubfigs",
        "url": "https://github.com/JLSteenwyk/ggpubfigs",
        "lesson": "Publication themes should be restrained and colorblind friendly; palette accessibility is part of the template quality floor.",
    },
)

FAMILY_BASELINE_BLOCKERS: dict[str, tuple[str, ...]] = {
    "atlas_spatial_panel": ("composition_density_risk", "python_current_style_gap"),
    "genomic_landscape_panel": ("low_information_density",),
    "submission_summary_panel": ("illustration_shell_style_gap",),
    "cohort_flow_and_design_panel": ("illustration_shell_style_gap",),
    "model_audit_panel": ("multi_panel_readability_risk",),
    "local_explanation_panel": ("multi_panel_readability_risk",),
    "response_explanation_panel": ("python_current_style_gap",),
}

KIND_BASELINE_BLOCKERS: dict[str, tuple[str, ...]] = {
    "illustration_shell": ("illustration_shell_style_gap",),
}


def _baseline_quality_gates(record: TemplateRecord, asset: RenderedAsset) -> list[str]:
    gates = [
        "template_family_canonicalized",
        "square_gallery_preview",
        "vector_export_available" if asset.pdf_ref or asset.svg_ref else "vector_export_missing",
        "semantic_palette_context",
        "synthetic_payload_only",
        "requires_ai_local_adaptation",
    ]
    if record.renderer_family == "r_ggplot2":
        gates.append("ggplot2_publication_theme")
    if record.renderer_family == "python":
        gates.append("python_renderer_style_alignment_required")
    return gates


def audit_template_quality(record: TemplateRecord, asset: RenderedAsset, baseline: RenderedAsset) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if asset.status != "rendered":
        blockers.append(f"render_status_{asset.status}")
    if record.renderer_family == "n/a" or record.kind == "table_shell":
        blockers.append("non_visual_template_not_gallery_card")
    if "vector_export_missing" in _baseline_quality_gates(record, asset):
        warnings.append("vector_export_missing")
    if record.renderer_family == "python":
        warnings.append("python_renderer_style_alignment_required")
        if record.kind == "evidence_figure":
            blockers.append("python_evidence_not_default_first_class")
    if baseline.status == "rendered":
        warnings.append("legacy_python_comparison_available")
    if baseline.status == "excluded":
        warnings.append("legacy_python_comparison_excluded_after_failed_render")
    blockers.extend(FAMILY_BASELINE_BLOCKERS.get(record.canonical_family_id, ()))
    blockers.extend(KIND_BASELINE_BLOCKERS.get(record.kind, ()))
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
        "status": status,
        "publication_ready_claim_authorized": False,
        "quality_gates": _baseline_quality_gates(record, asset),
        "blockers": unique_blockers,
        "warnings": unique_warnings,
        "recommended_next_actions": recommended_next_actions(record, unique_blockers, unique_warnings),
    }


def recommended_next_actions(record: TemplateRecord, blockers: list[str], warnings: list[str]) -> list[str]:
    actions = [
        "Use this template as a lower-bound starting point; AI may freely alter structure, layout, labels, scale, and composition for the paper-specific claim.",
        "Render-inspect-revise before any paper-facing use; do not accept the synthetic Gallery preview as final artwork.",
    ]
    if "python_renderer_style_alignment_required" in warnings or "python_current_style_gap" in blockers:
        actions.append("Align Python renderer typography, palette roles, export discipline, and guide placement with the MAS publication style profile.")
    if "legend_or_colorbar_overlap_risk" in warnings:
        actions.append("Check guide boxes after rendering; prefer direct labels or horizontal colorbars when tick labels collide.")
    if "low_information_density" in blockers:
        actions.append("Replace sparse synthetic matrices with denser, biologically plausible rows/columns before claiming publication-level quality.")
    if "multi_panel_readability_risk" in blockers:
        actions.append("Split overloaded panels or enlarge the device when reduced-size labels are not readable.")
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
    ready_like_count = sum(1 for audit in template_audits if not audit["blockers"])
    completion_by_category = _category_completion(
        records=records,
        visual_records=visual_records,
        non_visual_records=non_visual_records,
        default_surface_excluded_records=default_surface_excluded_records,
    )
    return {
        "schema_version": 1,
        "overall_status": "not_publication_ready",
        "publication_ready_claim_authorized": False,
        "quality_surface": "gallery_lower_bound_visual_audit",
        "visual_template_count": len(visual_records),
        "non_visual_template_count": len(non_visual_records),
        "lower_bound_review_required_count": ready_like_count,
        "blocked_template_count": len(template_audits) - ready_like_count,
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
            "required_before_paper_use": [
                "paper_local_data_payload",
                "render_inspect_revise",
                "legend_colorbar_overlap_check",
                "reduced_size_readability_check",
                "vector_or_high_resolution_export_check",
            ],
        },
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
        python_only_family_ids = sorted(
            {
                record.canonical_family_id
                for record in records
                if record.canonical_family_category == category
                and record.kind == "evidence_figure"
                and record.renderer_family == "python"
                and record.canonical_family_id not in default_r_family_ids
            }
        )
        excluded_templates = [
            record
            for record in records
            if record.canonical_family_category == category
            and record.kind == "evidence_figure"
            and record.renderer_family == "python"
            and record.canonical_family_id in python_only_family_ids
        ]
        non_visual = [
            record
            for record in non_visual_records
            if record.canonical_family_category == category
        ]
        evidence = [record for record in visible if record.kind == "evidence_figure"]
        r_evidence = [record for record in evidence if record.renderer_family == R_GGPLOT2_RENDERER]
        status = "done"
        if explicit_default_excluded or excluded_templates:
            status = "partial"
        if visible or non_visual:
            completion_percent = 100 if not excluded_templates else round(
                100 * len(visible) / (len(visible) + len(python_only_family_ids))
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
                "non_default_python_evidence_families": len(python_only_family_ids),
                "non_default_python_evidence_template_ids": [record.template_id for record in excluded_templates],
            }
        )
    return rows


def build_quality_audit_markdown(audit: dict[str, Any]) -> str:
    blockers = audit["blocker_counts"]
    warnings = audit["warning_counts"]
    blocker_lines = "\n".join(f"| `{key}` | {value} |" for key, value in blockers.items()) or "| none | 0 |"
    warning_lines = "\n".join(f"| `{key}` | {value} |" for key, value in warnings.items()) or "| none | 0 |"
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
            f"{item['non_default_python_evidence_families']} |"
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

| Category | Status | Completion | Default visual | R/ggplot2 evidence | Non-default Python evidence |
| --- | --- | ---: | ---: | ---: | ---: |
{completion_lines}

## 默认面排除的 Python Evidence

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
{excluded_lines}

## 外部准则

{reference_lines}
"""
