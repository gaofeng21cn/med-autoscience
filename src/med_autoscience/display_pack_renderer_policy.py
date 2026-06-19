from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


EVIDENCE_FIGURE_KIND = "evidence_figure"
ILLUSTRATION_SHELL_KIND = "illustration_shell"
TABLE_SHELL_KIND = "table_shell"
R_GGPLOT2_RENDERER = "r_ggplot2"
PYTHON_RENDERER = "python"


@dataclass(frozen=True)
class RendererPolicyDecision:
    surface_class: str
    default_surface_allowed: bool
    default_surface_reason: str
    statistical_evidence_authority: bool
    programmatic_precision_required: bool
    first_class_renderer_family: str
    python_renderer_role: str


class RendererPolicyRecord(Protocol):
    kind: str
    renderer_family: str
    default_visible: bool
    canonical_family_id: str
    canonical_template_id: str
    template_id: str


def default_surface_allowed_for(*, kind: str, renderer_family: str) -> bool:
    if kind == EVIDENCE_FIGURE_KIND:
        return renderer_family == R_GGPLOT2_RENDERER
    if kind == ILLUSTRATION_SHELL_KIND:
        return True
    return kind == TABLE_SHELL_KIND or renderer_family == "n/a"


def renderer_policy_for_record(record: RendererPolicyRecord) -> RendererPolicyDecision:
    kind = record.kind
    renderer = record.renderer_family
    if kind == EVIDENCE_FIGURE_KIND:
        if renderer == R_GGPLOT2_RENDERER:
            return RendererPolicyDecision(
                surface_class="programmatic_data_evidence",
                default_surface_allowed=True,
                default_surface_reason="r_ggplot2_evidence_first_class",
                statistical_evidence_authority=True,
                programmatic_precision_required=True,
                first_class_renderer_family=R_GGPLOT2_RENDERER,
                python_renderer_role="not_retained_for_data_evidence_without_advantage_proof",
            )
        return RendererPolicyDecision(
            surface_class="programmatic_data_evidence",
            default_surface_allowed=False,
            default_surface_reason="python_evidence_not_retained_without_documented_advantage_over_r_ggplot2",
            statistical_evidence_authority=True,
            programmatic_precision_required=True,
            first_class_renderer_family=R_GGPLOT2_RENDERER,
            python_renderer_role="retire_or_promote_only_after_documented_advantage_proof",
        )
    if kind == ILLUSTRATION_SHELL_KIND:
        return RendererPolicyDecision(
            surface_class="design_flow_or_graphical_shell",
            default_surface_allowed=True,
            default_surface_reason="illustration_shell_may_use_python_svg_or_imagegen_assisted_composition",
            statistical_evidence_authority=False,
            programmatic_precision_required=False,
            first_class_renderer_family="composition_or_svg",
            python_renderer_role="allowed_composition_backend",
        )
    return RendererPolicyDecision(
        surface_class="non_visual_or_tabular_shell",
        default_surface_allowed=False,
        default_surface_reason="not_a_visual_gallery_card",
        statistical_evidence_authority=False,
        programmatic_precision_required=False,
        first_class_renderer_family="not_applicable",
        python_renderer_role="not_applicable",
    )


def default_surface_renderer_policy() -> dict[str, object]:
    return {
        "policy_version": 1,
        "data_evidence_first_class_renderer": R_GGPLOT2_RENDERER,
        "data_evidence_default_rule": (
            "current evidence_figure templates are retained only when their renderer is R/ggplot2; "
            "a Python evidence template can re-enter only as a current audited template with documented "
            "advantage over the R/ggplot2 baseline"
        ),
        "python_evidence_default_allowed": False,
        "python_evidence_retention_rule": (
            "not retained in the current pack without documented advantage proof and visual audit"
        ),
        "python_evidence_allowed_roles": [],
        "design_flow_renderer_rule": (
            "illustration_shell templates may use SVG, Python composition, or imagegen-assisted "
            "art direction because they do not act as statistical evidence authority"
        ),
        "programmatic_precision_required_for": [EVIDENCE_FIGURE_KIND],
        "composition_expression_allowed_for": [ILLUSTRATION_SHELL_KIND],
    }


def renderer_policy_payload(record: RendererPolicyRecord) -> dict[str, object]:
    decision = renderer_policy_for_record(record)
    return {
        "surface_class": decision.surface_class,
        "default_surface_allowed": decision.default_surface_allowed,
        "default_surface_reason": decision.default_surface_reason,
        "statistical_evidence_authority": decision.statistical_evidence_authority,
        "programmatic_precision_required": decision.programmatic_precision_required,
        "first_class_renderer_family": decision.first_class_renderer_family,
        "python_renderer_role": decision.python_renderer_role,
    }


def renderer_policy_completion(records: list[RendererPolicyRecord]) -> dict[str, object]:
    all_evidence = [
        record
        for record in records
        if record.kind == EVIDENCE_FIGURE_KIND
    ]
    all_python_evidence = [
        record
        for record in all_evidence
        if record.renderer_family == PYTHON_RENDERER
    ]
    all_r_evidence = [
        record
        for record in all_evidence
        if record.renderer_family == R_GGPLOT2_RENDERER
    ]
    visible = [
        record
        for record in records
        if record.default_visible
        and default_surface_allowed_for(kind=record.kind, renderer_family=record.renderer_family)
    ]
    visual = [record for record in visible if record.kind != TABLE_SHELL_KIND and record.renderer_family != "n/a"]
    evidence = [record for record in visual if record.kind == EVIDENCE_FIGURE_KIND]
    illustration = [record for record in visual if record.kind == ILLUSTRATION_SHELL_KIND]
    python_evidence = [
        record
        for record in evidence
        if record.renderer_family == PYTHON_RENDERER
    ]
    r_evidence = [
        record
        for record in evidence
        if record.renderer_family == R_GGPLOT2_RENDERER
    ]
    r_evidence_family_ids = {
        record.canonical_family_id
        for record in all_r_evidence
    }
    python_only_family_ids = sorted(
        {
            record.canonical_family_id
            for record in all_python_evidence
            if record.canonical_family_id not in r_evidence_family_ids
        }
    )
    return {
        "default_visual_template_count": len(visual),
        "default_evidence_template_count": len(evidence),
        "default_r_ggplot2_evidence_template_count": len(r_evidence),
        "default_python_evidence_template_count": len(python_evidence),
        "default_illustration_shell_count": len(illustration),
        "default_surface_r_first_compliant": not python_evidence,
        "all_evidence_template_count": len(all_evidence),
        "all_r_ggplot2_evidence_template_count": len(all_r_evidence),
        "python_evidence_template_count": len(all_python_evidence),
        "python_evidence_retained_count": len(all_python_evidence),
        "current_inventory_r_first_compliant": not all_python_evidence,
        "python_evidence_template_ids": [record.template_id for record in all_python_evidence],
        "python_only_evidence_family_ids_without_default_r_representative": python_only_family_ids,
    }
