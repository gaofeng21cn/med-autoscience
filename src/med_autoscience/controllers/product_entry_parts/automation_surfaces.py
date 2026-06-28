from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _build_automation_surface(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    product_entry_status: Mapping[str, Any],
) -> dict[str, Any]:
    summary = _non_empty_text(product_entry_status.get("summary")) or "MAS automation entry surface."
    del profile
    refresh_command = _json_surface_command(_paper_mission_inspect_command(profile_ref))
    domain_health_refresh = _build_shared_automation_descriptor(
        automation_id="mas_paper_mission_readback_refresh_loop",
        title="MAS paper mission readback refresh",
        owner="one-person-lab",
        trigger_kind="interval",
        target_surface_kind="paper_mission_readback_refresh",
        summary="由 OPL current_control_state 触发 MAS paper-mission readback refresh，保持 paper mission、owner handoff 和 attention queue refs 为最新状态。",
        readiness_status="automation_ready",
        gate_policy="publication_gated",
        output_expectation=[
            "refresh paper mission readback",
            "update workspace attention queue",
            "preserve controller decision lineage",
        ],
        target_command=refresh_command,
        domain_projection={
            "service_status_command": f"{_command_prefix(profile_ref)} study progress --profile {_profile_arg(profile_ref)}",
            "recommended_entry_surface": "workspace_cockpit",
        },
    )
    return _build_shared_automation_catalog(
        summary=summary,
        automations=[domain_health_refresh],
        readiness_summary=render_automation_ready_summary(),
    )


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
