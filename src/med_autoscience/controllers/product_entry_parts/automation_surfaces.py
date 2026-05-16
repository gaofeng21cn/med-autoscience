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
        f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply-supervisor-platform-repair --apply"
    )
    runtime_supervision = _build_shared_automation_descriptor(
        automation_id="mas_runtime_supervision_loop",
        title="MAS domain runtime projection refresh",
        owner="one-person-lab",
        trigger_kind="interval",
        target_surface_kind="runtime_watch_refresh",
        summary="由 OPL-owned scheduler transport 触发 MAS domain projection refresh，保持恢复建议和 attention queue 为最新状态。",
        readiness_status="automation_ready",
        gate_policy="publication_gated",
        output_expectation=[
            "refresh runtime watch",
            "update workspace attention queue",
            "preserve controller decision lineage",
        ],
        target_command=refresh_command,
        domain_projection={
            "service_status_command": f"{_command_prefix(profile_ref)} runtime supervision-status --profile {_profile_arg(profile_ref)}",
            "recommended_entry_surface": "workspace_cockpit",
        },
    )
    return _build_shared_automation_catalog(
        summary=summary,
        automations=[runtime_supervision],
        readiness_summary=render_automation_ready_summary(),
    )


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
