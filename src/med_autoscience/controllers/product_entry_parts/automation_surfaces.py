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
    refresh_command = (
        f"{_command_prefix(profile_ref)} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {_profile_arg(profile_ref)} --request-opl-stage-attempts --dry-run"
    )
    domain_health_refresh = _build_shared_automation_descriptor(
        automation_id="mas_domain_health_diagnostic_refresh_loop",
        title="MAS domain health diagnostic refresh",
        owner="one-person-lab",
        trigger_kind="interval",
        target_surface_kind="domain_health_diagnostic_refresh",
        summary="由 OPL current_control_state 触发 MAS domain diagnostic refresh，保持 owner handoff 和 attention queue refs 为最新状态。",
        readiness_status="automation_ready",
        gate_policy="publication_gated",
        output_expectation=[
            "refresh domain health diagnostic",
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
