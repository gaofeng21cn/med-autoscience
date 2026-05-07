from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import open_auto_research_projection
from med_autoscience.controllers.medical_paper_ops_health import workspace_medical_paper_ops_health
from med_autoscience.controllers.medical_paper_research_loop import workspace_medical_paper_research_loop
from med_autoscience.controllers.medical_paper_v4_operations import workspace_v4_operations_state
from med_autoscience.controllers.product_entry_parts.paper_orchestra_operator import (
    build_workspace_paper_orchestra_operator_projection,
)

from med_autoscience.controllers.product_entry_parts.workspace_cockpit.readiness_and_delivery import (
    _workspace_delivery_inspection_state,
    _workspace_medical_paper_readiness_state,
    _workspace_portable_supervisor_queue_dashboard,
)
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.state_and_study_items import (
    _workspace_ai_first_cross_study_completion_projection,
    _workspace_ai_first_operations_state,
    _workspace_supervision_summary,
)
from med_autoscience.profiles import WorkspaceProfile


def workspace_health_cards(
    *,
    profile: WorkspaceProfile,
    study_roots: list[Path],
    studies: list[dict[str, Any]],
    service: dict[str, Any],
) -> dict[str, Any]:
    return {
        "workspace_supervision": _workspace_supervision_summary(studies=studies, service=service),
        "medical_paper_readiness_state": _workspace_medical_paper_readiness_state(studies=studies),
        "medical_paper_v4_operations_state": workspace_v4_operations_state(studies=studies),
        "medical_paper_ops_health_state": workspace_medical_paper_ops_health(studies=studies),
        "medical_paper_research_loop_state": workspace_medical_paper_research_loop(studies=studies),
        "ai_first_operations_state": _workspace_ai_first_operations_state(studies=studies),
        "ai_first_cross_study_completion_projection": _workspace_ai_first_cross_study_completion_projection(
            study_roots=study_roots,
            studies=studies,
        ),
        "paper_orchestra_operator_projection": build_workspace_paper_orchestra_operator_projection(
            studies=studies
        ),
        "open_auto_research_projection": open_auto_research_projection.build_workspace_open_auto_research_projection(
            studies=studies,
        ),
        "portable_supervisor_queue_dashboard": _workspace_portable_supervisor_queue_dashboard(
            profile=profile,
            studies=studies,
        ),
        "delivery_inspection_state": _workspace_delivery_inspection_state(studies=studies),
    }
