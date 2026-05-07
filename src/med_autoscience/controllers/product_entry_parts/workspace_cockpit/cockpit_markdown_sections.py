from __future__ import annotations

from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_markdown_ai import (
    append_ai_first_cross_study_completion,
    append_ai_first_operations_state,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_markdown_header import (
    append_workspace_cockpit_header,
    append_workspace_supervision_sections,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_markdown_medical import (
    append_delivery_inspection_state,
    append_medical_paper_ops_health_state,
    append_medical_paper_readiness_state,
    append_medical_paper_research_loop_state,
    append_medical_paper_v4_operations_state,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_markdown_queue import (
    append_attention_queue,
    append_commands,
    append_phase2_user_loop,
    append_portable_supervisor_queue_dashboard,
    append_user_loop,
    append_workspace_alerts,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_markdown_studies import (
    append_studies,
)

__all__ = [
    "append_ai_first_cross_study_completion",
    "append_ai_first_operations_state",
    "append_attention_queue",
    "append_commands",
    "append_delivery_inspection_state",
    "append_medical_paper_ops_health_state",
    "append_medical_paper_readiness_state",
    "append_medical_paper_research_loop_state",
    "append_medical_paper_v4_operations_state",
    "append_phase2_user_loop",
    "append_portable_supervisor_queue_dashboard",
    "append_studies",
    "append_user_loop",
    "append_workspace_alerts",
    "append_workspace_cockpit_header",
    "append_workspace_supervision_sections",
]
