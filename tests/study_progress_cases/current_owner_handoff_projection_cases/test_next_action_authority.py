from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_handoff_user_visible_status_does_not_promote_opl_action_queue_without_canonical_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )
    existing_next_step = "等待 MAS canonical next action。"

    result = module.apply_current_owner_handoff_user_visible_status(
        {
            "study_id": "003-dpcc",
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "action_queue": [
                    {
                        "status": "queued",
                        "owner": "one-person-lab",
                        "action_type": "request_opl_stage_attempt",
                        "summary": "OPL receipt/action queue is diagnostic only.",
                    }
                ],
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_step": existing_next_step,
                "next_system_action": existing_next_step,
                "next_owner": "mas_authority_kernel",
            },
        }
    )

    assert "next_system_action" not in result
    assert result["user_visible_projection"]["next_system_action"] == existing_next_step
    assert "request_opl_stage_attempt" not in result["user_visible_projection"]["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "mas_authority_kernel"
