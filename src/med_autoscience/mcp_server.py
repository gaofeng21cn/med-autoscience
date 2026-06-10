from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience import __version__
from med_autoscience.lazy_module_proxy import LazyModuleProxy as _LazyModuleProxy
from med_autoscience.action_catalog import (
    PRODUCT_ENTRY_CONTRACT_GAP_TEXT,
    action_catalog_metadata_by_mcp_tool,
    build_mas_action_catalog,
)
from med_autoscience.agent_tool_arsenal import (
    build_agent_tool_arsenal_index,
    build_capability_invocation_plan,
    build_tool_result_envelope_schema,
    get_tool_use_card,
)
from med_autoscience.authority_operation_command_catalog import (
    AUTHORITY_OPERATION_COMMANDS_BY_MCP_MODE,
    build_authority_product_entry_mode_schema,
    product_entry_description_modes_text,
)
from med_autoscience.mcp_server_parts.handler_adapter import (
    ToolHandler,
    call_mode_handler,
    optional_bool as _optional_bool,
    optional_float as _optional_float,
    optional_int as _optional_int,
    optional_mapping as _optional_mapping,
    optional_path as _optional_path,
    optional_string as _optional_string,
    require_path_list as _require_path_list,
    require_string as _require_string,
)
from med_autoscience.mcp_server_parts.tool_result_rendering import json_text, tool_text_result
from med_autoscience.mcp_server_parts.tool_registry import build_tool_registry, manifest_from_registry


PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "med-autoscience"


def _load_controller(module_name: str) -> Any:
    return import_module(f"med_autoscience.controllers.{module_name}")


def _load_doctor_module() -> Any:
    return import_module("med_autoscience.doctor")


def _load_overlay_installer() -> Any:
    return import_module("med_autoscience.overlay.installer")


def _load_profiles_module() -> Any:
    return import_module("med_autoscience.profiles")


artifact_lifecycle_operations_report = _LazyModuleProxy(lambda: _load_controller("artifact_lifecycle_operations_report"))
backend_audit = _LazyModuleProxy(lambda: _load_controller("backend_audit"))
delivery_authority_backfill_apply = _LazyModuleProxy(lambda: _load_controller("delivery_authority_backfill_apply"))
workspace_authority_migration_audit = _LazyModuleProxy(lambda: _load_controller("workspace_authority_migration_audit"))
continuous_soak_summary = _LazyModuleProxy(lambda: _load_controller("continuous_soak_summary"))
data_assets = _LazyModuleProxy(lambda: _load_controller("data_assets"))
external_research = _LazyModuleProxy(lambda: _load_controller("external_research"))
medical_literature_audit = _LazyModuleProxy(lambda: _load_controller("medical_literature_audit"))
medical_reporting_audit = _LazyModuleProxy(lambda: _load_controller("medical_reporting_audit"))
open_auto_research_soak = _LazyModuleProxy(lambda: _load_controller("open_auto_research_soak"))
portfolio_memory = _LazyModuleProxy(lambda: _load_controller("portfolio_memory"))
domain_health_diagnostic = _LazyModuleProxy(lambda: _load_controller("domain_health_diagnostic"))
startup_data_readiness_controller = _LazyModuleProxy(lambda: _load_controller("startup_data_readiness"))
study_progress = _LazyModuleProxy(lambda: _load_controller("study_progress"))
domain_status_projection = _LazyModuleProxy(lambda: _load_controller("domain_status_projection"))
workspace_init = _LazyModuleProxy(lambda: _load_controller("workspace_init"))
workspace_literature = _LazyModuleProxy(lambda: _load_controller("workspace_literature"))
doctor = _LazyModuleProxy(_load_doctor_module)
overlay_installer = _LazyModuleProxy(_load_overlay_installer)
profiles = _LazyModuleProxy(_load_profiles_module)
_PRODUCT_ENTRY_CONTRACT_GAP_TEXT = PRODUCT_ENTRY_CONTRACT_GAP_TEXT
ACTION_CATALOG = build_mas_action_catalog()
TOOL_REGISTRY = build_tool_registry(
    authority_operation_mode_schema=build_authority_product_entry_mode_schema(),
    authority_operation_modes_text=product_entry_description_modes_text(),
    authority_operation_contract_gap_text=_PRODUCT_ENTRY_CONTRACT_GAP_TEXT,
    action_catalog_metadata_by_tool=action_catalog_metadata_by_mcp_tool(ACTION_CATALOG),
)


def _tool_text_result(text: str, *, structured: dict[str, Any] | None = None, is_error: bool = False) -> dict[str, Any]:
    return tool_text_result(text, structured=structured, is_error=is_error)


def _json_text(payload: dict[str, Any]) -> str:
    return json_text(payload)


def _serialize_study_runtime_result(result: dict[str, Any]) -> dict[str, Any]:
    from med_autoscience.mcp_server_parts.projection_adapters import serialize_study_runtime_result

    return serialize_study_runtime_result(result)


def list_tools() -> list[dict[str, Any]]:
    return manifest_from_registry(TOOL_REGISTRY)


def build_tool_manifest() -> list[dict[str, Any]]:
    return list_tools()


def _call_doctor_report(arguments: dict[str, Any]) -> dict[str, Any]:
    profile = profiles.load_profile(_require_string(arguments, "profile_path"))
    report = doctor.build_doctor_report(profile)
    text = doctor.render_doctor_report(report)
    structured = {
        "profile": profile.name,
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "medical_overlay_ready": report.medical_overlay_ready,
    }
    return _tool_text_result(text, structured=structured)


def _call_show_profile(arguments: dict[str, Any]) -> dict[str, Any]:
    profile = profiles.load_profile(_require_string(arguments, "profile_path"))
    text = doctor.render_profile(profile)
    structured = {
        "name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "medical_overlay_scope": profile.medical_overlay_scope,
    }
    return _tool_text_result(text, structured=structured)


def _call_overlay_status(arguments: dict[str, Any]) -> dict[str, Any]:
    profile_path = arguments.get("profile_path")
    quest_root = arguments.get("quest_root")
    if bool(profile_path) == bool(quest_root):
        raise ValueError("Specify exactly one of profile_path or quest_root")
    if isinstance(profile_path, str):
        profile = profiles.load_profile(profile_path)
        result = overlay_installer.describe_medical_overlay(**doctor.overlay_request_from_profile(profile))
    else:
        result = overlay_installer.describe_medical_overlay(quest_root=Path(_require_string(arguments, "quest_root")))
    return _tool_text_result(_json_text(result), structured=result)


def _call_domain_health_diagnostic(arguments: dict[str, Any]) -> dict[str, Any]:
    quest_root = arguments.get("quest_root")
    runtime_root = arguments.get("runtime_root")
    if bool(quest_root) == bool(runtime_root):
        raise ValueError("Specify exactly one of quest_root or runtime_root")
    if isinstance(quest_root, str):
        result = domain_health_diagnostic.run_domain_health_diagnostic_for_quest(quest_root=Path(quest_root), apply=False)
    else:
        result = domain_health_diagnostic.run_domain_health_diagnostic_for_runtime(
            runtime_root=Path(_require_string(arguments, "runtime_root")),
            apply=False,
        )
    return _tool_text_result(_json_text(result), structured=result)


def _call_data_assets_status(arguments: dict[str, Any]) -> dict[str, Any]:
    result = data_assets.data_assets_status(workspace_root=Path(_require_string(arguments, "workspace_root")))
    return _tool_text_result(_json_text(result), structured=result)


def _call_portfolio_memory_status(arguments: dict[str, Any]) -> dict[str, Any]:
    result = portfolio_memory.portfolio_memory_status(workspace_root=Path(_require_string(arguments, "workspace_root")))
    return _tool_text_result(_json_text(result), structured=result)


def _call_init_portfolio_memory(arguments: dict[str, Any]) -> dict[str, Any]:
    result = portfolio_memory.init_portfolio_memory(workspace_root=Path(_require_string(arguments, "workspace_root")))
    return _tool_text_result(_json_text(result), structured=result)


def _call_workspace_literature_status(arguments: dict[str, Any]) -> dict[str, Any]:
    result = workspace_literature.workspace_literature_status(
        workspace_root=Path(_require_string(arguments, "workspace_root"))
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_init_workspace_literature(arguments: dict[str, Any]) -> dict[str, Any]:
    result = workspace_literature.init_workspace_literature(
        workspace_root=Path(_require_string(arguments, "workspace_root"))
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_external_research_status(arguments: dict[str, Any]) -> dict[str, Any]:
    result = external_research.external_research_status(workspace_root=Path(_require_string(arguments, "workspace_root")))
    return _tool_text_result(_json_text(result), structured=result)


def _call_prepare_external_research(arguments: dict[str, Any]) -> dict[str, Any]:
    as_of_date = arguments.get("as_of_date")
    if as_of_date is not None and (not isinstance(as_of_date, str) or not as_of_date.strip()):
        raise ValueError("as_of_date must be a non-empty string when provided")
    result = external_research.prepare_external_research(
        workspace_root=Path(_require_string(arguments, "workspace_root")),
        as_of_date=as_of_date if isinstance(as_of_date, str) else None,
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_startup_data_readiness(arguments: dict[str, Any]) -> dict[str, Any]:
    result = startup_data_readiness_controller.startup_data_readiness(
        workspace_root=Path(_require_string(arguments, "workspace_root"))
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_backend_audit(arguments: dict[str, Any]) -> dict[str, Any]:
    profile = profiles.load_profile(_require_string(arguments, "profile_path"))
    result = backend_audit.run_backend_audit(profile, refresh=_optional_bool(arguments, "refresh"))
    return _tool_text_result(_json_text(result), structured=result)


def _call_progress_projection(arguments: dict[str, Any]) -> dict[str, Any]:
    from med_autoscience.mcp_server_parts.projection_adapters import render_progress_projection_result

    profile = profiles.load_profile(_require_string(arguments, "profile_path"))
    result = domain_status_projection.progress_projection(
        profile=profile,
        study_id=arguments.get("study_id") if isinstance(arguments.get("study_id"), str) else None,
        study_root=_optional_path(arguments, "study_root"),
        entry_mode=arguments.get("entry_mode") if isinstance(arguments.get("entry_mode"), str) else None,
        sync_runtime_summary=False,
    )
    return render_progress_projection_result(result)


def _call_study_progress(arguments: dict[str, Any]) -> dict[str, Any]:
    from med_autoscience.mcp_server_parts.projection_adapters import render_study_progress_result

    profile = profiles.load_profile(_require_string(arguments, "profile_path"))
    result = study_progress.read_study_progress(
        profile=profile,
        study_id=arguments.get("study_id") if isinstance(arguments.get("study_id"), str) else None,
        study_root=_optional_path(arguments, "study_root"),
        entry_mode=arguments.get("entry_mode") if isinstance(arguments.get("entry_mode"), str) else None,
        sync_runtime_summary=False,
    )
    return render_study_progress_result(result)


def _call_open_auto_research_soak(arguments: dict[str, Any]) -> dict[str, Any]:
    from med_autoscience.mcp_server_parts.projection_adapters import render_open_auto_research_soak_result

    profile = profiles.load_profile(_require_string(arguments, "profile_path"))
    result = open_auto_research_soak.run_open_auto_research_soak(
        profile=profile,
        study_id=arguments.get("study_id") if isinstance(arguments.get("study_id"), str) else None,
        study_root=_optional_path(arguments, "study_root"),
        entry_mode=arguments.get("entry_mode") if isinstance(arguments.get("entry_mode"), str) else None,
        allow_controller_writes=_optional_bool(arguments, "allow_controller_writes"),
    )
    return render_open_auto_research_soak_result(
        result,
        allow_controller_writes=_optional_bool(arguments, "allow_controller_writes"),
    )


def _call_init_workspace(arguments: dict[str, Any]) -> dict[str, Any]:
    result = workspace_init.init_workspace(
        workspace_root=Path(_require_string(arguments, "workspace_root")),
        workspace_name=_require_string(arguments, "workspace_name"),
        default_publication_profile=_optional_string(
            arguments,
            "default_publication_profile",
            default="general_medical_journal",
        ),
        default_citation_style=_optional_string(
            arguments,
            "default_citation_style",
            default="AMA",
        ),
        dry_run=_optional_bool(arguments, "dry_run"),
        force=_optional_bool(arguments, "force"),
        initialize_git=_optional_bool(arguments, "initialize_git", default=False),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_medical_literature_audit(arguments: dict[str, Any]) -> dict[str, Any]:
    result = medical_literature_audit.run_controller(
        quest_root=Path(_require_string(arguments, "quest_root")),
        apply=_optional_bool(arguments, "apply"),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_medical_reporting_audit(arguments: dict[str, Any]) -> dict[str, Any]:
    result = medical_reporting_audit.run_controller(
        quest_root=Path(_require_string(arguments, "quest_root")),
        apply=_optional_bool(arguments, "apply"),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_migration_audit(arguments: dict[str, Any]) -> dict[str, Any]:
    result = workspace_authority_migration_audit.run_migration_audit(
        workspace_roots=_require_path_list(arguments, "workspace_roots", mode="workspace_authority_migration_audit"),
        dry_run=True,
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_backfill_apply(arguments: dict[str, Any]) -> dict[str, Any]:
    result = delivery_authority_backfill_apply.run_backfill_apply(
        workspace_roots=_require_path_list(arguments, "workspace_roots", mode="delivery_authority_backfill_apply"),
        apply=_optional_bool(arguments, "apply", default=False),
        authority_snapshot=_optional_mapping(arguments.get("authority_snapshot"), field_name="authority_snapshot"),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_lifecycle_report(arguments: dict[str, Any]) -> dict[str, Any]:
    result = artifact_lifecycle_operations_report.run_lifecycle_operations_report(
        workspace_roots=_require_path_list(arguments, "workspace_roots", mode="lifecycle_report"),
        deep=_optional_bool(arguments, "deep", default=False),
        max_files=_optional_int(arguments, "max_files"),
        max_seconds=_optional_float(arguments, "max_seconds"),
    )
    render_markdown = _optional_bool(arguments, "markdown", default=False)
    text = (
        artifact_lifecycle_operations_report.render_lifecycle_operations_report_markdown(result)
        if render_markdown
        else _json_text(result)
    )
    return _tool_text_result(text, structured=result)


def _call_governance_report(arguments: dict[str, Any]) -> dict[str, Any]:
    result = _call_lifecycle_report(arguments)
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        governed = {
            **structured,
            "surface": "storage_governance_report",
            "source_surface": structured.get("surface"),
        }
        result["structuredContent"] = governed
        if result["content"] and result["content"][0]["text"].lstrip().startswith("{"):
            result["content"][0]["text"] = _json_text(governed)
    return result


def _call_continuous_soak_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    result = continuous_soak_summary.build_continuous_soak_summary(
        workspace_roots=_require_path_list(arguments, "workspace_roots", mode="continuous_soak_summary"),
        deep=_optional_bool(arguments, "deep", default=False),
        max_files=_optional_int(arguments, "max_files"),
        max_seconds=_optional_float(arguments, "max_seconds"),
    )
    return _tool_text_result(_json_text(result), structured=result)


_AUTHORITY_PRODUCT_ENTRY_HANDLERS: dict[str, ToolHandler] = {
    "workspace_authority_migration_audit": _call_migration_audit,
    "delivery_authority_backfill_apply": _call_backfill_apply,
    "storage_governance_report": _call_governance_report,
    "artifact_lifecycle_report": _call_lifecycle_report,
    "artifact_lifecycle_continuous_soak_summary": _call_continuous_soak_summary,
}
_MISSING_AUTHORITY_PRODUCT_ENTRY_HANDLERS = (
    set(AUTHORITY_OPERATION_COMMANDS_BY_MCP_MODE) - set(_AUTHORITY_PRODUCT_ENTRY_HANDLERS)
)
if _MISSING_AUTHORITY_PRODUCT_ENTRY_HANDLERS:
    raise RuntimeError(
        "authority MCP handler drift: "
        f"missing_modes={sorted(_MISSING_AUTHORITY_PRODUCT_ENTRY_HANDLERS)}"
    )


def _call_doctor_audit(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="doctor_audit",
        arguments=arguments,
        handlers={
            "report": _call_doctor_report,
            "profile": _call_show_profile,
            "overlay_status": _call_overlay_status,
            "backend_audit": _call_backend_audit,
        },
    )


def _call_workspace_readiness(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="workspace_readiness",
        arguments=arguments,
        handlers={
            "init_workspace": _call_init_workspace,
            "startup_data_readiness": _call_startup_data_readiness,
            "portfolio_memory_status": _call_portfolio_memory_status,
            "init_portfolio_memory": _call_init_portfolio_memory,
            "workspace_literature_status": _call_workspace_literature_status,
            "init_workspace_literature": _call_init_workspace_literature,
        },
    )


def _call_research_assets(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="research_assets",
        arguments=arguments,
        handlers={
            "data_assets_status": _call_data_assets_status,
            "external_research_status": _call_external_research_status,
            "prepare_external_research": _call_prepare_external_research,
        },
    )


def _call_publication_status(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="publication_status",
        arguments=arguments,
        handlers={
            "medical_literature_audit": _call_medical_literature_audit,
            "medical_reporting_audit": _call_medical_reporting_audit,
        },
    )


def _call_authority_operations(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="authority_operations",
        arguments=arguments,
        handlers={
            **_AUTHORITY_PRODUCT_ENTRY_HANDLERS,
        },
    )


def _call_agent_tool_arsenal_index(arguments: dict[str, Any]) -> dict[str, Any]:
    result = build_agent_tool_arsenal_index(ACTION_CATALOG)
    return _tool_text_result(_json_text(result), structured=result)


def _call_agent_tool_arsenal_card(arguments: dict[str, Any]) -> dict[str, Any]:
    result = get_tool_use_card(_require_string(arguments, "tool_id"))
    return _tool_text_result(_json_text(result), structured=result)


def _call_agent_tool_arsenal_plan(arguments: dict[str, Any]) -> dict[str, Any]:
    current_owner_delta = _optional_mapping(
        arguments.get("current_owner_delta"),
        field_name="current_owner_delta",
    )
    if current_owner_delta is None:
        raise ValueError("current_owner_delta is required for agent_tool_arsenal plan mode")
    result = build_capability_invocation_plan(current_owner_delta=current_owner_delta)
    return _tool_text_result(_json_text(result), structured=result)


def _call_agent_tool_arsenal_result_envelope_schema(arguments: dict[str, Any]) -> dict[str, Any]:
    result = build_tool_result_envelope_schema()
    return _tool_text_result(_json_text(result), structured=result)


def _call_agent_tool_arsenal(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="agent_tool_arsenal",
        arguments=arguments,
        handlers={
            "index": _call_agent_tool_arsenal_index,
            "card": _call_agent_tool_arsenal_card,
            "plan": _call_agent_tool_arsenal_plan,
            "result_envelope_schema": _call_agent_tool_arsenal_result_envelope_schema,
        },
    )


TOOL_HANDLERS = {
    "doctor_audit": _call_doctor_audit,
    "workspace_readiness": _call_workspace_readiness,
    "research_assets": _call_research_assets,
    "study_progress": _call_study_progress,
    "open_auto_research_soak": _call_open_auto_research_soak,
    "publication_status": _call_publication_status,
    "authority_operations": _call_authority_operations,
    "agent_tool_arsenal": _call_agent_tool_arsenal,
}


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return _tool_text_result(f"Unknown tool: {name}", is_error=True)
    try:
        return handler(arguments or {})
    except Exception as exc:
        return _tool_text_result(f"{type(exc).__name__}: {exc}", is_error=True)


def _success_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def _error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") if isinstance(request.get("params"), dict) else {}

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _success_response(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {
                        "listChanged": False,
                    }
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": __version__,
                },
            },
        )
    if method == "ping":
        return _success_response(request_id, {})
    if method == "tools/list":
        return _success_response(request_id, {"tools": list_tools()})
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str) or not name:
            return _error_response(request_id, -32602, "tools/call requires params.name")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        return _success_response(request_id, call_tool(name, arguments))
    if request_id is None:
        return None
    return _error_response(request_id, -32601, f"Method not found: {method}")


def serve() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _error_response(None, -32700, f"Parse error: {exc}")
        else:
            if not isinstance(request, dict):
                response = _error_response(None, -32600, "Invalid request")
            else:
                response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


def entrypoint() -> None:
    raise SystemExit(serve())


if __name__ == "__main__":
    entrypoint()
