from __future__ import annotations

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
    FORBIDDEN_DOMAIN_AUTHORITY,
    build_agent_tool_arsenal_index,
)
from med_autoscience.authority_operation_command_catalog import (
    AUTHORITY_OPERATION_COMMANDS_BY_MCP_MODE,
    build_authority_product_entry_mode_schema,
    product_entry_description_modes_text,
)
from med_autoscience.mcp_server_parts.handler_adapter import (
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
from med_autoscience.mcp_server_parts.agent_tool_arsenal_handler import (
    call_agent_tool_arsenal,
)
from med_autoscience.mcp_server_parts.jsonrpc_transport import (
    error_response as _jsonrpc_error_response,
    handle_request as _handle_jsonrpc_request,
    serve as _serve_jsonrpc,
    success_response as _jsonrpc_success_response,
)
from med_autoscience.mcp_server_parts.tool_result_rendering import json_text, tool_text_result
from med_autoscience.scientific_capability_registry import (
    build_scientific_capability_registry,
    invoke_scientific_capability,
    resolve_scientific_capabilities,
)
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
display_pack_agent = _LazyModuleProxy(lambda: import_module("med_autoscience.display_pack_agent"))
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


def _optional_text_argument(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string when provided")
    return value.strip()


def _tool_manifest_by_name() -> dict[str, dict[str, Any]]:
    return {str(tool["name"]): tool for tool in list_tools()}


def _matching_tool_card(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
    mode = arguments.get("mode") if isinstance(arguments.get("mode"), str) else ""
    arsenal = build_agent_tool_arsenal_index(ACTION_CATALOG)
    for card in list(arsenal.get("tool_cards") or []):
        if not isinstance(card, dict) or card.get("tool_id") != tool_name:
            continue
        if mode and card.get("tool_mode") and card.get("tool_mode") != mode:
            continue
        return dict(card)
    return None


def _tool_result_envelope(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    raw_result: dict[str, Any],
) -> dict[str, Any]:
    structured = raw_result.get("structuredContent")
    payload = dict(structured) if isinstance(structured, dict) else {}
    manifest = _tool_manifest_by_name().get(tool_name, {})
    annotations = manifest.get("annotations") if isinstance(manifest.get("annotations"), dict) else {}
    card = _matching_tool_card(tool_name, arguments)
    tool_mode = arguments.get("mode") if isinstance(arguments.get("mode"), str) else ""
    is_error = bool(raw_result.get("isError"))
    text = ""
    content = raw_result.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            text = str(first.get("text") or "")
    recovery = _tool_result_recovery(
        tool_name=tool_name,
        payload=payload,
        card=card,
        is_error=is_error,
        result_summary=text,
    )
    envelope: dict[str, Any] = {
        **payload,
        "surface_kind": "mas_tool_result_envelope",
        "tool_id": tool_name,
        **({"tool_mode": tool_mode} if tool_mode else {}),
        "status": "failed" if is_error else "succeeded",
        "structured_payload": payload,
        "raw_surface_kind": str(
            payload.get("surface_kind")
            or payload.get("surface")
            or payload.get("status")
            or ""
        ),
        "structured_content_ref": f"mcp://{SERVER_NAME}/tools/{tool_name}/structuredContent",
        "result_summary": text[:500],
        **recovery,
        "recovery": recovery,
        "audit_trail": {
            "surface_kind": "mas_tool_audit_trail",
            "source_refs": [
                "src/med_autoscience/mcp_server.py",
                "src/med_autoscience/mcp_server_parts/tool_registry.py",
                "contracts/agent_tool_arsenal.json",
            ],
            "authority_flags": {
                "readOnlyHint": bool(annotations.get("readOnlyHint")),
                "destructiveHint": bool(annotations.get("destructiveHint")),
                "idempotentHint": bool(annotations.get("idempotentHint")),
                "openWorldHint": bool(annotations.get("openWorldHint")),
                "isError": is_error,
            },
            "allowed_write_refs": list(card.get("allowed_writes") or []) if card else [],
            "forbidden_authority": (
                list(card.get("forbidden_authority") or [])
                if card
                else list(FORBIDDEN_DOMAIN_AUTHORITY)
            ),
        },
        "authority_boundary": {
            "tool_result_envelope_is_authority_outcome": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "source_tool_card_ref": (
                f"contracts/agent_tool_arsenal.json#/tool_cards/{card.get('action_id')}"
                if card
                else ""
            ),
            **(
                dict(card.get("authority_effects") or {})
                if card
                else {}
            ),
        },
    }
    if is_error:
        envelope["error_class"] = "tool_execution_error"
    return envelope


def _tool_result_recovery(
    *,
    tool_name: str,
    payload: dict[str, Any],
    card: dict[str, Any] | None,
    is_error: bool,
    result_summary: str,
) -> dict[str, Any]:
    required_refs = list(card.get("required_refs") or card.get("input_refs") or []) if card else []
    missing_refs = _extract_missing_refs(payload, required_refs=required_refs, is_error=is_error)
    owner_needed = _owner_needed_from_payload(payload, is_error=is_error)
    receipt_refs = _extract_ref_list(payload, keys=("receipt_refs", "owner_receipt_refs"))
    typed_blocker_refs = _extract_ref_list(payload, keys=("typed_blocker_refs", "blocker_refs"))
    diagnostic_refs = _extract_ref_list(
        payload,
        keys=("diagnostic_refs", "evidence_refs", "source_refs"),
    )
    owner_receipt_ref = _string_or_empty(payload.get("owner_receipt_ref"))
    typed_blocker_ref = _string_or_empty(payload.get("typed_blocker_ref"))
    if owner_receipt_ref and owner_receipt_ref not in receipt_refs:
        receipt_refs.append(owner_receipt_ref)
    if typed_blocker_ref and typed_blocker_ref not in typed_blocker_refs:
        typed_blocker_refs.append(typed_blocker_ref)
    if missing_refs:
        retryability = "retry_after_refs"
    elif owner_needed:
        retryability = "owner_needed"
    elif is_error:
        retryability = "retry_safe"
    else:
        retryability = "retry_safe"
    next_safe_actions = _result_next_safe_actions(
        tool_name=tool_name,
        card=card,
        retryability=retryability,
        missing_refs=missing_refs,
        diagnostic_refs=diagnostic_refs,
        result_summary=result_summary,
    )
    return {
        "retryability": retryability,
        "staleness": {
            "source_fingerprint_required": bool(
                card
                and _string_or_empty(card.get("idempotency_policy"))
                != "read_only_no_side_effects"
            ),
            "source_refs": diagnostic_refs[:5],
            "current_owner_delta_bound": bool(card),
        },
        "missing_refs": missing_refs,
        "next_safe_actions": next_safe_actions,
        "owner_needed": owner_needed,
        "receipt_refs": receipt_refs,
        "typed_blocker_refs": typed_blocker_refs,
        "diagnostic_refs": diagnostic_refs,
        "no_forbidden_authority_claim": True,
    }


def _extract_missing_refs(
    payload: dict[str, Any],
    *,
    required_refs: list[Any],
    is_error: bool,
) -> list[str]:
    explicit = _extract_ref_list(payload, keys=("missing_refs", "required_missing_refs"))
    if explicit:
        return explicit
    if not is_error:
        return []
    return []


def _owner_needed_from_payload(payload: dict[str, Any], *, is_error: bool) -> bool:
    if bool(payload.get("owner_needed")):
        return True
    status = str(payload.get("status") or "").lower()
    if status in {"owner_needed", "blocked_owner_needed"}:
        return True
    blocker = payload.get("typed_blocker_ref") or payload.get("typed_blocker_refs")
    return bool(is_error and blocker)


def _result_next_safe_actions(
    *,
    tool_name: str,
    card: dict[str, Any] | None,
    retryability: str,
    missing_refs: list[str],
    diagnostic_refs: list[str],
    result_summary: str,
) -> list[dict[str, Any]]:
    if missing_refs:
        return [
            _tool_result_action_metadata({
                "action": "collect_missing_refs",
                "missing_refs": missing_refs,
            })
        ]
    if retryability == "owner_needed":
        return [_tool_result_action_metadata({"action": "surface_owner_needed"})]
    if retryability == "retry_safe" and "Unsupported" in result_summary:
        return [
            _tool_result_action_metadata({
                "action": "inspect_diagnostic_refs",
                "diagnostic_refs": diagnostic_refs,
            })
        ]
    if card and card.get("callability") == "mcp_runtime":
        return [
            _tool_result_action_metadata({
                "action": "consume_structured_payload",
                "tool_name": tool_name,
            })
        ]
    return [_tool_result_action_metadata({"action": "consume_structured_payload", "tool_name": tool_name})]


def _tool_result_action_metadata(action: dict[str, Any]) -> dict[str, Any]:
    return {
        **action,
        "authority": False,
        "can_execute": False,
        "can_generate_action": False,
        "action_role": "tool_result_consumption_metadata",
    }


def _extract_ref_list(payload: dict[str, Any], *, keys: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
        elif isinstance(value, (list, tuple)):
            refs.extend(str(item).strip() for item in value if str(item).strip())
    return list(dict.fromkeys(refs))


def _string_or_empty(value: object) -> str:
    return str(value or "").strip()


def _wrap_tool_result(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    raw_result: dict[str, Any],
) -> dict[str, Any]:
    structured = raw_result.get("structuredContent")
    if isinstance(structured, dict) and structured.get("surface_kind") == "mas_tool_result_envelope":
        return raw_result
    return {
        **raw_result,
        "structuredContent": _tool_result_envelope(
            tool_name=tool_name,
            arguments=arguments,
            raw_result=raw_result,
        ),
    }


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


def _call_display_pack_agent_discover(arguments: dict[str, Any]) -> dict[str, Any]:
    result = display_pack_agent.display_pack_capability_discover(
        repo_root=_optional_path(arguments, "repo_root"),
        paper_root=_optional_path(arguments, "paper_root"),
        include_templates=_optional_bool(arguments, "include_templates", default=False),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_display_pack_agent_plan(arguments: dict[str, Any]) -> dict[str, Any]:
    figure_request = _optional_mapping(arguments.get("figure_request"), field_name="figure_request")
    if figure_request is None:
        raise ValueError("figure_request is required for display_pack_agent plan mode")
    result = display_pack_agent.display_pack_figure_plan(
        repo_root=_optional_path(arguments, "repo_root"),
        paper_root=_optional_path(arguments, "paper_root"),
        figure_request=figure_request,
        max_recommendations=_optional_int(arguments, "max_recommendations") or 5,
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_display_pack_agent_preflight(arguments: dict[str, Any]) -> dict[str, Any]:
    template_id_value = arguments.get("template_id")
    if template_id_value is not None and (
        not isinstance(template_id_value, str) or not template_id_value.strip()
    ):
        raise ValueError("template_id must be a non-empty string when provided")
    result = display_pack_agent.display_pack_preflight(
        repo_root=_optional_path(arguments, "repo_root"),
        paper_root=_optional_path(arguments, "paper_root"),
        template_id=template_id_value.strip() if isinstance(template_id_value, str) else None,
        figure_request=_optional_mapping(arguments.get("figure_request"), field_name="figure_request"),
        check_runtime_dependencies=_optional_bool(
            arguments,
            "check_runtime_dependencies",
            default=True,
        ),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_display_pack_agent_render(arguments: dict[str, Any]) -> dict[str, Any]:
    result = display_pack_agent.display_pack_render(
        repo_root=_optional_path(arguments, "repo_root"),
        paper_root=_require_string(arguments, "paper_root"),
        figure_request=_optional_mapping(arguments.get("figure_request"), field_name="figure_request"),
        visual_audit_review=_optional_mapping(
            arguments.get("visual_audit_review"),
            field_name="visual_audit_review",
        ),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_display_pack_agent_orchestrate(arguments: dict[str, Any]) -> dict[str, Any]:
    result = display_pack_agent.display_pack_orchestrate(
        repo_root=_optional_path(arguments, "repo_root"),
        paper_root=_optional_path(arguments, "paper_root"),
        current_owner_delta=_optional_mapping(
            arguments.get("current_owner_delta"),
            field_name="current_owner_delta",
        ),
        claim_ref=_optional_text_argument(arguments, "claim_ref"),
        data_ref=_optional_text_argument(arguments, "data_ref"),
        paper_target=_optional_text_argument(arguments, "paper_target"),
        intent=_optional_text_argument(arguments, "intent"),
        figure_request=_optional_mapping(arguments.get("figure_request"), field_name="figure_request"),
        max_recommendations=_optional_int(arguments, "max_recommendations") or 5,
        check_runtime_dependencies=_optional_bool(
            arguments,
            "check_runtime_dependencies",
            default=True,
        ),
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_display_pack_agent(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="display_pack_agent",
        arguments=arguments,
        handlers={
            "discover": _call_display_pack_agent_discover,
            "orchestrate": _call_display_pack_agent_orchestrate,
            "plan": _call_display_pack_agent_plan,
            "preflight": _call_display_pack_agent_preflight,
            "render": _call_display_pack_agent_render,
        },
    )


def _call_scientific_capability_registry_index(arguments: dict[str, Any]) -> dict[str, Any]:
    result = build_scientific_capability_registry()
    return _tool_text_result(_json_text(result), structured=result)


def _call_scientific_capability_registry_resolve(arguments: dict[str, Any]) -> dict[str, Any]:
    current_owner_delta = _optional_mapping(
        arguments.get("current_owner_delta"),
        field_name="current_owner_delta",
    )
    result = resolve_scientific_capabilities(current_owner_delta=current_owner_delta)
    return _tool_text_result(_json_text(result), structured=result)


def _call_scientific_capability_registry_invoke(arguments: dict[str, Any]) -> dict[str, Any]:
    current_owner_delta = _optional_mapping(
        arguments.get("current_owner_delta"),
        field_name="current_owner_delta",
    )
    payload = _optional_mapping(arguments.get("payload"), field_name="payload") or {}
    result = invoke_scientific_capability(
        capability_id=_require_string(arguments, "capability_id"),
        current_owner_delta=current_owner_delta,
        study_root=_optional_path(arguments, "study_root"),
        apply=_optional_bool(arguments, "apply", default=False),
        payload=payload,
    )
    return _tool_text_result(_json_text(result), structured=result)


def _call_scientific_capability_registry(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_mode_handler(
        tool_name="scientific_capability_registry",
        arguments=arguments,
        handlers={
            "index": _call_scientific_capability_registry_index,
            "resolve": _call_scientific_capability_registry_resolve,
            "invoke": _call_scientific_capability_registry_invoke,
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


def _call_agent_tool_arsenal(arguments: dict[str, Any]) -> dict[str, Any]:
    return call_agent_tool_arsenal(
        arguments,
        action_catalog=ACTION_CATALOG,
        mcp_tool_manifest=list_tools(),
    )


TOOL_HANDLERS = {
    "doctor_audit": _call_doctor_audit,
    "workspace_readiness": _call_workspace_readiness,
    "research_assets": _call_research_assets,
    "study_progress": _call_study_progress,
    "open_auto_research_soak": _call_open_auto_research_soak,
    "publication_status": _call_publication_status,
    "display_pack_agent": _call_display_pack_agent,
    "scientific_capability_registry": _call_scientific_capability_registry,
    "authority_operations": _call_authority_operations,
    "agent_tool_arsenal": _call_agent_tool_arsenal,
}


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return _tool_text_result(f"Unknown tool: {name}", is_error=True)
    resolved_arguments = arguments or {}
    try:
        result = handler(resolved_arguments)
    except Exception as exc:
        result = _tool_text_result(f"{type(exc).__name__}: {exc}", is_error=True)
    return _wrap_tool_result(tool_name=name, arguments=resolved_arguments, raw_result=result)


def _success_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return _jsonrpc_success_response(request_id, result)


def _error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return _jsonrpc_error_response(request_id, code, message)


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    return _handle_jsonrpc_request(
        request,
        protocol_version=PROTOCOL_VERSION,
        server_name=SERVER_NAME,
        server_version=__version__,
        list_tools=list_tools,
        call_tool=call_tool,
    )


def serve() -> int:
    return _serve_jsonrpc(
        protocol_version=PROTOCOL_VERSION,
        server_name=SERVER_NAME,
        server_version=__version__,
        list_tools=list_tools,
        call_tool=call_tool,
    )


def entrypoint() -> None:
    raise SystemExit(serve())


if __name__ == "__main__":
    entrypoint()
