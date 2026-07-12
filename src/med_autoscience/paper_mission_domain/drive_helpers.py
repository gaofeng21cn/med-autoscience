from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_domain.common import (
    _first_text,
    _mapping,
    _optional_text,
)
from med_autoscience.paper_mission_output_roots import (
    PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH,
    YANG_WORKSPACE_ROOT,
    _is_under_yang_workspace,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
)

def paper_mission_drive_output_roots(
    *,
    profile: Any,
    output_root: str | Path | None,
    run_id: str | None,
) -> dict[str, Path]:
    if output_root is not None:
        root = Path(output_root).expanduser().resolve()
        if _is_under_yang_workspace(root):
            selected_run_id = _optional_text(run_id) or root.name or "paper_mission_drive"
            workspace_root = yang_workspace_root_for_path(root)
            return {
                "root": root,
                "candidate_package": (
                    workspace_root / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / selected_run_id
                ),
            }
        selected_run_id = _optional_text(run_id) or "paper_mission_drive"
        return {
            "root": root,
            "candidate_package": root / "candidate_package",
        }
    selected_run_id = _optional_text(run_id) or "paper_mission_drive"
    workspace_root = Path(profile.workspace_root).expanduser().resolve()
    return {
        "root": workspace_root / "ops" / "medautoscience",
        "candidate_package": (
            workspace_root / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / selected_run_id
        ),
    }


def yang_workspace_root_for_path(path: Path) -> Path:
    normalized = path.expanduser().resolve()
    relative = normalized.relative_to(YANG_WORKSPACE_ROOT)
    return YANG_WORKSPACE_ROOT / relative.parts[0]


def paper_mission_drive_result(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    handoff_ready = _optional_text(handoff.get("handoff_status")) == (
        "ready_for_ai_route_context"
    )
    route = _mapping(consume_readback.get("ai_route_context"))
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    carrier_readback = _mapping(consume_readback.get("opl_stage_attempt_readback"))
    runtime_status = _optional_text(consume_readback.get("opl_stage_attempt_readback_status"))
    status = (
        "opl_stage_route_running"
        if runtime_status == "opl_runtime_attempt_running_observed"
        else "opl_terminal_closeout_observed"
        if runtime_status == "opl_runtime_terminal_readback_observed"
        else "opl_runtime_handoff_required"
        if handoff_ready
        else "waiting_for_owner_resolution"
    )
    if stage_closure_decision_missing(_mapping(stage_closure_decision)):
        status = "stage_closure_decision_missing"
    return {
        "status": status,
        "stage_closure_decision_ref": _mapping(stage_closure_decision).get(
            "decision_ref"
        ),
        "stage_closure_outcome": _mapping(
            _mapping(stage_closure_decision).get("outcome")
        ).get("kind"),
        "stage_terminal_decision": decision.get("decision_kind"),
        "route_command": route.get("command_kind"),
        "next_owner": _first_text(
            decision.get("next_owner"),
            handoff.get("next_owner"),
            _mapping(consume_readback.get("next_owner_or_human_decision")).get(
                "next_owner"
            ),
        ),
        "can_submit_to_opl_runtime": bool(handoff.get("can_submit_to_opl_runtime")),
        "opl_stage_attempt_readback_status": runtime_status,
        "provider_attempt_running_observed": (
            runtime_status == "opl_runtime_attempt_running_observed"
        ),
        "terminal_closeout_observed": (
            runtime_status == "opl_runtime_terminal_readback_observed"
        ),
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
    }
