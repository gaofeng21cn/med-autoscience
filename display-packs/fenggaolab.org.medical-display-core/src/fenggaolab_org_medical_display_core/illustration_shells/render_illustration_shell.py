from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

from ..shared import (
    _require_namespaced_registry_id,
)
from .render_baseline_missingness_qc_panel import _render_baseline_missingness_qc_panel
from .render_center_coverage_batch_transportability_panel import _render_center_coverage_batch_transportability_panel
from .render_cohort_flow_figure import _render_cohort_flow_figure
from .render_design_evidence_composite_shell import _render_design_evidence_composite_shell
from .render_submission_graphical_abstract import _render_submission_graphical_abstract
from .render_transportability_recalibration_governance_panel import _render_transportability_recalibration_governance_panel
from .render_workflow_fact_sheet_panel import _render_workflow_fact_sheet_panel
from .validate_baseline_missingness_qc_panel_payload import _validate_baseline_missingness_qc_panel_payload
from .validate_center_coverage_batch_transportability_panel_payload import _validate_center_coverage_batch_transportability_panel_payload
from .validate_cohort_flow_payload import _validate_cohort_flow_payload
from .validate_design_evidence_composite_shell_payload import _validate_design_evidence_composite_shell_payload
from .validate_submission_graphical_abstract_payload import _validate_submission_graphical_abstract_payload
from .validate_transportability_recalibration_governance_panel_payload import _validate_transportability_recalibration_governance_panel_payload
from .validate_workflow_fact_sheet_panel_payload import _validate_workflow_fact_sheet_panel_payload


_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
_COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards"}
_COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def render_illustration_shell(
    *,
    template_id: str,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    payload_path: Path | None = None,
) -> dict[str, str]:
    _, template_short_id = _require_namespaced_registry_id(template_id, label="template_id")
    resolved_payload_path = payload_path or Path(f"<inline:{template_short_id}>")
    if template_short_id == "cohort_flow_figure":
        normalized_shell_payload = _validate_cohort_flow_payload(resolved_payload_path, shell_payload)
        title = str(normalized_shell_payload.get("title") or "Cohort flow").strip() or "Cohort flow"
        _render_cohort_flow_figure(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            title=title,
            steps=list(normalized_shell_payload["steps"]),
            exclusions=list(normalized_shell_payload["exclusions"]),
            endpoint_inventory=list(normalized_shell_payload["endpoint_inventory"]),
            design_panels=list(normalized_shell_payload["design_panels"]),
            layout_mode=str(normalized_shell_payload["layout_mode"]),
            comparison_summary=dict(normalized_shell_payload["comparison_summary"]),
            render_context=render_context,
        )
        return {
            "title": title,
            "caption": str(
                normalized_shell_payload.get("caption") or "Study cohort flow and analysis population accounting."
            ).strip(),
        }
    if template_short_id == "submission_graphical_abstract":
        normalized_shell_payload = _validate_submission_graphical_abstract_payload(resolved_payload_path, shell_payload)
        _render_submission_graphical_abstract(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        return {
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
        }
    if template_short_id == "workflow_fact_sheet_panel":
        normalized_shell_payload = _validate_workflow_fact_sheet_panel_payload(resolved_payload_path, shell_payload)
        _render_workflow_fact_sheet_panel(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        return {
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
        }
    if template_short_id == "design_evidence_composite_shell":
        normalized_shell_payload = _validate_design_evidence_composite_shell_payload(resolved_payload_path, shell_payload)
        _render_design_evidence_composite_shell(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        return {
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
        }
    if template_short_id == "baseline_missingness_qc_panel":
        normalized_shell_payload = _validate_baseline_missingness_qc_panel_payload(resolved_payload_path, shell_payload)
        _render_baseline_missingness_qc_panel(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        return {
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
        }
    if template_short_id == "center_coverage_batch_transportability_panel":
        normalized_shell_payload = _validate_center_coverage_batch_transportability_panel_payload(
            resolved_payload_path,
            shell_payload,
        )
        _render_center_coverage_batch_transportability_panel(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        return {
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
        }
    if template_short_id == "transportability_recalibration_governance_panel":
        normalized_shell_payload = _validate_transportability_recalibration_governance_panel_payload(
            resolved_payload_path,
            shell_payload,
        )
        _render_transportability_recalibration_governance_panel(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        return {
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
        }
    raise RuntimeError(f"unsupported illustration shell `{template_id}`")
