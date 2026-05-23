from __future__ import annotations

from typing import Any

from med_autoscience.controllers.product_entry_parts.paper_orchestra_operator import (
    render_paper_orchestra_operator_projection_lines,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_markdown_sections import (
    append_ai_first_cross_study_completion,
    append_ai_first_operations_state,
    append_attention_queue,
    append_commands,
    append_delivery_inspection_state,
    append_medical_paper_ops_health_state,
    append_medical_paper_readiness_state,
    append_medical_paper_research_loop_state,
    append_medical_paper_v4_operations_state,
    append_phase2_user_loop,
    append_opl_current_control_state_handoff_dashboard,
    append_studies,
    append_user_loop,
    append_workspace_alerts,
    append_workspace_cockpit_header,
    append_workspace_supervision_sections,
)


def render_workspace_cockpit_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    append_workspace_cockpit_header(lines, payload)
    append_workspace_supervision_sections(lines, payload)
    append_medical_paper_readiness_state(lines, payload)
    append_medical_paper_v4_operations_state(lines, payload)
    append_medical_paper_ops_health_state(lines, payload)
    append_medical_paper_research_loop_state(lines, payload)
    append_delivery_inspection_state(lines, payload)
    append_ai_first_operations_state(lines, payload)
    append_ai_first_cross_study_completion(lines, payload)
    lines.extend(render_paper_orchestra_operator_projection_lines(payload.get("paper_orchestra_operator_projection") or {}))
    append_opl_current_control_state_handoff_dashboard(lines, payload.get("opl_current_control_state_handoff_dashboard") or {})
    append_workspace_alerts(lines, payload)
    append_attention_queue(lines, payload)
    append_user_loop(lines, payload)
    append_phase2_user_loop(lines, payload)
    append_commands(lines, payload)
    append_studies(lines, payload)
    return "\n".join(lines)
