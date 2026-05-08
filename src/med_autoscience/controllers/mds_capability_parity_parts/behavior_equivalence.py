from __future__ import annotations

import copy
from typing import Any, Mapping


SCHEMA_VERSION = 1
PROVENANCE_REF = "docs/references/med-deepscientist/source_provenance.json"
MDS_FINAL_ROLE = "frozen_source_archive_or_historical_fixture_only"
ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES: tuple[str, ...] = (
    "behavior_equivalent",
    "purpose_equivalent_with_different_timing",
    "partially_equivalent",
    "not_equivalent_retired",
    "historical_fixture_only",
)
ALLOWED_BEHAVIOR_OPERATOR_ACTIONS: tuple[str, ...] = (
    "use_mas_default",
    "use_mas_with_latency_awareness",
    "use_progress_portal",
    "use_explicit_legacy_diagnostic_only",
    "retired_no_active_replacement",
    "use_historical_fixture_only",
)

BEHAVIOR_EQUIVALENCE_SURFACES: tuple[dict[str, Any], ...] = (
    {
        "surface_id": "daemon_residency",
        "title": "Daemon residency",
        "equivalence_class": "purpose_equivalent_with_different_timing",
        "mds_behavior": {
            "resident_process": True,
            "server": "ThreadingHTTPServer plus WebSocket server",
            "responds_without_scheduler_tick": True,
        },
        "mas_behavior": {
            "resident_process": False,
            "default_owner": "hermes_gateway_cron",
            "tick_interval_seconds": 300,
            "tick_command": "ops/medautoscience/bin/watch-runtime --interval-seconds 300 --max-ticks 1",
        },
        "behavior_difference": "MAS default supervision is scheduled ticks, not a resident HTTP/WebSocket daemon.",
        "default_user_impact": "Runtime drift detection can be delayed up to the scheduler interval; HTTP/WebSocket session continuity is not provided by MAS Runtime OS.",
        "mas_contract": "Hermes gateway cron runs one MAS runtime watch tick per interval and refreshes durable runtime/progress surfaces.",
        "recommended_operator_action": "use_mas_with_latency_awareness",
    },
    {
        "surface_id": "supervision_cadence",
        "title": "Supervision cadence",
        "equivalence_class": "purpose_equivalent_with_different_timing",
        "mds_behavior": {
            "cadence": "resident event loop plus worker/session callbacks",
            "can_react_between_ticks": True,
        },
        "mas_behavior": {
            "cadence": "Hermes cron scheduled one-shot tick",
            "interval_seconds": 300,
            "max_ticks": 1,
        },
        "behavior_difference": "MDS can react while the daemon is alive; MAS default reacts on the next scheduled tick.",
        "default_user_impact": "Five-minute supervision latency is acceptable for MAS paper runtime recovery but not equivalent to live interactive daemon responsiveness.",
        "mas_contract": "runtime watch tick writes runtime_watch/runtime_supervision/progress freshness and can trigger MAS-owned recovery.",
        "recommended_operator_action": "use_mas_with_latency_awareness",
    },
    {
        "surface_id": "quest_create_resume_pause_stop",
        "title": "Quest create/resume/pause/stop",
        "equivalence_class": "behavior_equivalent",
        "mds_behavior": {
            "quest_controls": ["create", "resume", "pause", "stop"],
            "owner": "MDS daemon API and quest service",
        },
        "mas_behavior": {
            "quest_controls": ["create", "resume", "pause", "stop"],
            "owner": "MAS Runtime OS and study runtime router",
        },
        "behavior_difference": "MAS uses controller/runtime surfaces rather than MDS daemon HTTP routes.",
        "default_user_impact": "Daily MAS operation can create, resume, pause, and stop study runtime without external MDS.",
        "mas_contract": "study_runtime_status, ensure_study_runtime, pause-runtime and runtime transport own lifecycle controls.",
        "recommended_operator_action": "use_mas_default",
    },
    {
        "surface_id": "live_worker_session_tracking",
        "title": "Live worker/session tracking",
        "equivalence_class": "purpose_equivalent_with_different_timing",
        "mds_behavior": {
            "session_store": True,
            "worker_threads": True,
            "live_session_api": True,
        },
        "mas_behavior": {
            "session_store": "durable runtime state and runtime_session read model",
            "worker_threads": False,
            "live_session_api": False,
        },
        "behavior_difference": "MAS observes worker state through durable state and ticks; it does not expose the MDS in-memory session store.",
        "default_user_impact": "Live/no-live truth is fail-closed and durable, but fine-grained in-memory session continuity is retired.",
        "mas_contract": "runtime_liveness_audit, active_run_id, worker_running, runtime_session and runtime supervision determine live status.",
        "recommended_operator_action": "use_mas_with_latency_awareness",
    },
    {
        "surface_id": "crash_recovery_auto_resume",
        "title": "Crash recovery and auto-resume",
        "equivalence_class": "purpose_equivalent_with_different_timing",
        "mds_behavior": {
            "startup_resume": "_resume_reconciled_quests",
            "worker_restart": "daemon-managed worker thread scheduling",
        },
        "mas_behavior": {
            "startup_resume": "recovery_intent plus runtime watch/ensure-study-runtime on scheduler tick",
            "worker_restart": "MAS controller-authorized recovery action",
        },
        "behavior_difference": "MDS resumes at daemon startup; MAS resumes when Hermes invokes the next MAS tick or an operator runs watch explicitly.",
        "default_user_impact": "Recovery is independent of MDS checkout but has scheduler-bound latency.",
        "mas_contract": "recovery_intent records the controller-owned recovery reason and safe_reconcile readiness; runtime_watch and study_runtime_router reconcile active-but-not-running state and escalate fail-closed.",
        "recommended_operator_action": "use_mas_with_latency_awareness",
    },
    {
        "surface_id": "queued_user_messages_mailbox",
        "title": "Queued user messages/mailbox",
        "equivalence_class": "partially_equivalent",
        "mds_behavior": {
            "queued_user_messages": True,
            "conversation_binding": True,
            "daemon_schedules_turns": True,
        },
        "mas_behavior": {
            "task_intake": True,
            "controller_handoff": True,
            "daemon_mailbox": False,
        },
        "behavior_difference": "MAS has durable task intake and controller handoff, not MDS-style daemon conversation mailbox scheduling.",
        "default_user_impact": "Research task intake is covered; chat-like connector mailbox behavior is not a default MAS capability.",
        "mas_contract": "latest task intake, controller decision, owner_route and supervisor consume/dispatch own actionable work.",
        "recommended_operator_action": "use_mas_default",
    },
    {
        "surface_id": "progress_visibility",
        "title": "Progress visibility",
        "equivalence_class": "behavior_equivalent",
        "mds_behavior": {"web_status": True, "api_status": True},
        "mas_behavior": {"progress_portal": True, "study_progress": True, "workspace_cockpit": True},
        "behavior_difference": "MAS uses Progress Portal/read models instead of MDS WebUI as the default visual entry.",
        "default_user_impact": "Users have a MAS-owned fixed place to inspect progress without running MDS WebUI.",
        "mas_contract": "Progress Portal consumes MAS payload refs, freshness, source refs and artifact locators without reinterpreting study truth.",
        "recommended_operator_action": "use_progress_portal",
    },
    {
        "surface_id": "webui_websocket_terminal_streaming",
        "title": "WebUI, WebSocket, and terminal streaming",
        "equivalence_class": "not_equivalent_retired",
        "mds_behavior": {"react_webui": True, "websocket_terminal_attach": True, "bash_log_streaming": True},
        "mas_behavior": {
            "progress_portal": "read-only snapshot or optional read-only refresh service",
            "websocket_terminal_attach": False,
            "bash_log_streaming": False,
        },
        "behavior_difference": "MAS Progress Portal replaces progress visibility, not interactive WebSocket terminal streaming.",
        "default_user_impact": "Interactive daemon console features are retired from default MAS operation.",
        "mas_contract": "Terminal/log inspection remains an operator debug activity, not a MAS default progress surface.",
        "recommended_operator_action": "retired_no_active_replacement",
    },
    {
        "surface_id": "connector_channel_background_delivery",
        "title": "Connector/channel background delivery",
        "equivalence_class": "not_equivalent_retired",
        "mds_behavior": {
            "background_connectors": ["QQ", "Slack", "Discord", "Telegram", "Weixin", "WhatsApp", "Feishu"],
            "connector_threads": True,
        },
        "mas_behavior": {"default_connector_threads": False, "handoff_refs": True},
        "behavior_difference": "MAS does not run MDS connector/channel background threads.",
        "default_user_impact": "Delivery through chat connectors is not part of default MAS monolith operation.",
        "mas_contract": "MAS emits durable handoff/progress/artifact refs; external apps may consume refs without becoming MAS truth.",
        "recommended_operator_action": "retired_no_active_replacement",
    },
    {
        "surface_id": "mcp_surface",
        "title": "MCP surface",
        "equivalence_class": "purpose_equivalent_with_different_timing",
        "mds_behavior": {"mcp_entrypoints": True, "daemon_backed": True},
        "mas_behavior": {"mcp_entrypoints": True, "daemon_backed": False},
        "behavior_difference": "MAS MCP calls owner surfaces directly; it does not route through MDS daemon MCP.",
        "default_user_impact": "MCP operation is covered for MAS truth/status/progress surfaces without external MDS.",
        "mas_contract": "MAS MCP remains adapter-only and cannot claim study/runtime/publication authority.",
        "recommended_operator_action": "use_mas_default",
    },
    {
        "surface_id": "gitops_state_management",
        "title": "GitOps state management",
        "equivalence_class": "not_equivalent_retired",
        "mds_behavior": {"root_git": True, "quest_git": True, "diff_log_reader": True},
        "mas_behavior": {"root_git": False, "quest_git": False, "runtime_lifecycle_sqlite": True},
        "behavior_difference": "MAS intentionally retired workspace root Git and quest Git as runtime lifecycle owners.",
        "default_user_impact": "Existing papers use SQLite/restore-proof lifecycle, not MDS GitOps behavior.",
        "mas_contract": "runtime_lifecycle.sqlite, restore index and migration ledger own runtime history/proof.",
        "recommended_operator_action": "retired_no_active_replacement",
    },
    {
        "surface_id": "memory_lesson_store",
        "title": "Memory and lesson store",
        "equivalence_class": "partially_equivalent",
        "mds_behavior": {"memory_service": True, "lesson_store": True},
        "mas_behavior": {"portfolio_research_memory": True, "incident_learning": True, "quality_authority": False},
        "behavior_difference": "MAS absorbs lessons as evidence/calibration, not as an autonomous runtime memory service.",
        "default_user_impact": "Reusable study memory is available through MAS memory surfaces; MDS memory behavior remains fixture/reference only.",
        "mas_contract": "portfolio/research_memory and incident learning read models are evidence-only.",
        "recommended_operator_action": "use_mas_default",
    },
    {
        "surface_id": "team_multiagent_coordination",
        "title": "Team and multi-agent coordination",
        "equivalence_class": "historical_fixture_only",
        "mds_behavior": {"team_service": True, "multiagent_patterns": True},
        "mas_behavior": {"controller_owner_route": True, "team_service": False},
        "behavior_difference": "MAS uses owner_route/controller coordination, not MDS team service.",
        "default_user_impact": "Research owner routing is covered; MDS team semantics are reference fixtures only.",
        "mas_contract": "owner_route -> consumer latest -> executor dispatch -> rescan owns coordination.",
        "recommended_operator_action": "use_historical_fixture_only",
    },
    {
        "surface_id": "artifact_interaction_handoff",
        "title": "Artifact interaction/handoff",
        "equivalence_class": "partially_equivalent",
        "mds_behavior": {"artifact_service": True, "interactive_artifact_api": True},
        "mas_behavior": {"artifact_os": True, "package_locator": True, "interactive_artifact_api": False},
        "behavior_difference": "MAS owns artifact inventory/package locator; interactive artifact mutation APIs are not default-retained.",
        "default_user_impact": "Package and artifact discovery are covered; interactive MDS artifact mutation is retired from default operation.",
        "mas_contract": "Artifact OS owns inventory, locator, delivery projection and rebuild proof.",
        "recommended_operator_action": "use_mas_default",
    },
    {
        "surface_id": "system_update_daemon_lifecycle_controls",
        "title": "System update and daemon lifecycle controls",
        "equivalence_class": "not_equivalent_retired",
        "mds_behavior": {"admin_shutdown": True, "system_update_action": True, "daemon_lifecycle_control": True},
        "mas_behavior": {"external_mds_daemon_control": False, "hermes_gateway_cron_control": True},
        "behavior_difference": "MAS does not control an MDS daemon lifecycle; it controls/removes MAS Hermes cron supervision jobs.",
        "default_user_impact": "There is no MAS-native MDS daemon control path because the daemon is not a default dependency.",
        "mas_contract": "runtime-ensure-supervision/runtime-remove-supervision manage Hermes gateway cron and retired legacy-service cleanup.",
        "recommended_operator_action": "retired_no_active_replacement",
    },
    {
        "surface_id": "workspace_local_host_service",
        "title": "Workspace-local host service",
        "equivalence_class": "not_equivalent_retired",
        "mds_behavior": {
            "workspace_local_launchd_or_systemd": "historical MAS bridge, not MDS daemon",
            "service_can_remain_loaded": True,
        },
        "mas_behavior": {
            "workspace_local_host_service": False,
            "retired_cleanup": True,
            "canonical_owner": "hermes_gateway_cron",
        },
        "behavior_difference": "Workspace-local launchd/systemd/cron service templates are retired; their presence is cleanup evidence, not an active owner.",
        "default_user_impact": "Old host services must be removed instead of kept as an alternate supervision mode.",
        "mas_contract": "runtime-ensure-supervision removes retired workspace-local services before registering or reporting Hermes supervision.",
        "recommended_operator_action": "retired_no_active_replacement",
    },
)

RUNTIME_CONTINUITY_COMPLETION = {
    "surface": "mas_runtime_continuity_completion",
    "status": "landed",
    "owner": "MedAutoScience Runtime OS",
    "external_mds_repo_required": False,
    "mds_daemon_required": False,
    "active_scheduler": "hermes_gateway_cron",
    "default_tick_interval_seconds": 300,
    "runtime_session_read_model": {
        "surface_kind": "runtime_session_read_model",
        "role": "read_model",
        "read_only": True,
        "source_priority": [
            "study_runtime_status/runtime_liveness_audit",
            "runtime_lifecycle_store",
            "owner_route/dispatch_receipts",
            "legacy_diagnostic_fixture",
        ],
        "writes_authority_surface": False,
    },
    "recovery_intent_ledger": {
        "surface": "runtime_recovery_intent",
        "role": "controller_authorized_recovery_projection",
        "allowed_current_actions": [
            "await_next_tick",
            "safe_reconcile_ready",
            "recovering",
            "parked",
            "human_gate_required",
            "escalated",
        ],
        "writes_publication_truth": False,
        "writes_paper_package": False,
    },
    "safe_reconcile_trigger": {
        "surface_kind": "runtime_reconcile_trigger_projection",
        "role": "read_model_request_projection",
        "executes_reconcile": False,
        "writes_runtime": False,
        "dedupe_required": True,
        "blocked_current_truth": [
            "stale_owner_route",
            "manual_parked",
            "parked",
            "completed",
            "human_gate_required",
            "publication_gate_missing",
            "retry_exhausted",
        ],
    },
    "user_surface_projection": {
        "surfaces": [
            "study_progress",
            "workspace_cockpit",
            "product_entry_status",
            "progress_portal",
            "mcp_study_progress",
            "opl_handoff",
        ],
        "role": "read_model_projection",
        "reinterprets_study_truth": False,
    },
    "quality_ready_authorized": False,
    "publication_ready_authorized": False,
    "submission_ready_authorized": False,
}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def _behavior_surface_projection(surface: Mapping[str, Any]) -> dict[str, Any]:
    projection = copy.deepcopy(dict(surface))
    projection["provenance_ref"] = PROVENANCE_REF
    projection["mas_default_requires_external_mds"] = False
    projection["requires_mds_daemon_for_default_operation"] = False
    projection["quality_authority_allowed"] = False
    projection["publication_ready_authority_allowed"] = False
    return projection


def _behavior_equivalence_summary(surfaces: list[Mapping[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"surface_count": len(surfaces)}
    for equivalence_class in ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES:
        summary[equivalence_class] = sum(
            1 for surface in surfaces if _text(surface.get("equivalence_class")) == equivalence_class
        )
    summary["fully_equivalent_to_mds_daemon"] = False
    return summary


def build_mds_behavior_equivalence_matrix() -> dict[str, Any]:
    surfaces = [_behavior_surface_projection(surface) for surface in BEHAVIOR_EQUIVALENCE_SURFACES]
    return {
        "surface": "mds_behavior_equivalence_matrix",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "mds_final_role": MDS_FINAL_ROLE,
        "default_operation_requires_external_mds": False,
        "default_diagnostic_requires_external_mds": False,
        "default_supervision_owner": "hermes_gateway_cron",
        "default_tick_interval_seconds": 300,
        "default_tick_max_ticks": 1,
        "default_tick_command": "ops/medautoscience/bin/watch-runtime --interval-seconds 300 --max-ticks 1",
        "mas_default_runtime_is_resident_daemon": False,
        "mds_daemon_was_resident_http_websocket_server": True,
        "completion_claim": "default_independence_not_full_behavior_equivalence",
        "allowed_equivalence_classes": list(ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES),
        "allowed_operator_actions": list(ALLOWED_BEHAVIOR_OPERATOR_ACTIONS),
        "behavior_surfaces": surfaces,
        "runtime_continuity_completion": copy.deepcopy(RUNTIME_CONTINUITY_COMPLETION),
        "summary": _behavior_equivalence_summary(surfaces),
    }


def validate_mds_behavior_equivalence_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    _validate_behavior_matrix_header(matrix, issues)
    _validate_behavior_matrix_dependency_contract(matrix, issues)
    _validate_behavior_matrix_scheduler_contract(matrix, issues)
    _validate_behavior_matrix_claims(matrix, issues)
    _validate_behavior_matrix_allowed_values(matrix, issues)
    _validate_behavior_matrix_surfaces(matrix, issues)
    _validate_runtime_continuity_completion(matrix.get("runtime_continuity_completion"), issues)
    return {
        "surface": "mds_behavior_equivalence_matrix_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_behavior_matrix_header(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if _text(matrix.get("surface")) != "mds_behavior_equivalence_matrix":
        issues.append({"code": "wrong_behavior_matrix_surface"})
    if _text(matrix.get("owner")) != "MedAutoScience":
        issues.append({"code": "behavior_matrix_owner_drift"})
    if _text(matrix.get("mds_final_role")) != MDS_FINAL_ROLE:
        issues.append({"code": "behavior_matrix_mds_final_role_drift"})


def _validate_behavior_matrix_dependency_contract(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if matrix.get("default_operation_requires_external_mds") is not False:
        issues.append({"code": "behavior_matrix_external_mds_default_dependency"})
    if matrix.get("default_diagnostic_requires_external_mds") is not False:
        issues.append({"code": "behavior_matrix_external_mds_default_diagnostic_dependency"})


def _validate_behavior_matrix_scheduler_contract(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if _text(matrix.get("default_supervision_owner")) != "hermes_gateway_cron":
        issues.append({"code": "behavior_matrix_default_supervision_owner_drift"})
    if int(matrix.get("default_tick_interval_seconds") or 0) != 300:
        issues.append({"code": "behavior_matrix_default_tick_interval_drift"})
    if int(matrix.get("default_tick_max_ticks") or 0) != 1:
        issues.append({"code": "behavior_matrix_default_tick_max_ticks_drift"})


def _validate_behavior_matrix_claims(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if matrix.get("mas_default_runtime_is_resident_daemon") is not False:
        issues.append({"code": "behavior_matrix_resident_daemon_overclaim"})
    if matrix.get("mds_daemon_was_resident_http_websocket_server") is not True:
        issues.append({"code": "behavior_matrix_mds_daemon_source_fact_drift"})
    if _text(matrix.get("completion_claim")) != "default_independence_not_full_behavior_equivalence":
        issues.append({"code": "behavior_matrix_completion_claim_overbroad"})


def _validate_behavior_matrix_allowed_values(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if list(matrix.get("allowed_equivalence_classes") or []) != list(ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES):
        issues.append({"code": "behavior_matrix_allowed_equivalence_classes_drift"})
    if list(matrix.get("allowed_operator_actions") or []) != list(ALLOWED_BEHAVIOR_OPERATOR_ACTIONS):
        issues.append({"code": "behavior_matrix_allowed_operator_actions_drift"})


def _validate_behavior_matrix_surfaces(matrix: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    for surface in _list(matrix.get("behavior_surfaces")):
        if not isinstance(surface, Mapping):
            issues.append({"code": "invalid_behavior_surface"})
            continue
        _validate_behavior_surface(surface, issues)


def _validate_behavior_surface(surface: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    surface_id = _text(surface.get("surface_id"))
    equivalence_class = _text(surface.get("equivalence_class"))
    _validate_behavior_surface_identity(surface, surface_id, equivalence_class, issues)
    _validate_behavior_surface_content(surface, surface_id, issues)
    _validate_behavior_surface_authority(surface, surface_id, issues)


def _validate_behavior_surface_identity(
    surface: Mapping[str, Any],
    surface_id: str,
    equivalence_class: str,
    issues: list[dict[str, Any]],
) -> None:
    if not surface_id:
        issues.append({"code": "behavior_surface_missing_id"})
    if equivalence_class not in ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES:
        issues.append(
            {
                "code": "invalid_behavior_equivalence_class",
                "surface_id": surface_id,
                "equivalence_class": equivalence_class,
            }
        )
    if surface_id in {
        "daemon_residency",
        "webui_websocket_terminal_streaming",
        "connector_channel_background_delivery",
        "workspace_local_host_service",
    } and equivalence_class == "behavior_equivalent":
        issues.append({"code": f"{surface_id}_overclaimed_as_behavior_equivalent", "surface_id": surface_id})


def _validate_behavior_surface_content(
    surface: Mapping[str, Any],
    surface_id: str,
    issues: list[dict[str, Any]],
) -> None:
    for field in ("title", "behavior_difference", "default_user_impact", "mas_contract", "provenance_ref"):
        if not _text(surface.get(field)):
            issues.append({"code": f"behavior_surface_missing_{field}", "surface_id": surface_id})
    if not isinstance(surface.get("mds_behavior"), Mapping):
        issues.append({"code": "behavior_surface_missing_mds_behavior", "surface_id": surface_id})
    if not isinstance(surface.get("mas_behavior"), Mapping):
        issues.append({"code": "behavior_surface_missing_mas_behavior", "surface_id": surface_id})
    if _text(surface.get("recommended_operator_action")) not in ALLOWED_BEHAVIOR_OPERATOR_ACTIONS:
        issues.append({"code": "behavior_surface_invalid_operator_action", "surface_id": surface_id})


def _validate_behavior_surface_authority(
    surface: Mapping[str, Any],
    surface_id: str,
    issues: list[dict[str, Any]],
) -> None:
    if surface.get("mas_default_requires_external_mds") is not False:
        issues.append({"code": "behavior_surface_requires_external_mds_for_default_operation", "surface_id": surface_id})
    if surface.get("requires_mds_daemon_for_default_operation") is not False:
        issues.append({"code": "behavior_surface_requires_mds_daemon_for_default_operation", "surface_id": surface_id})
    if surface.get("quality_authority_allowed") is not False:
        issues.append({"code": "behavior_surface_quality_authority_allowed", "surface_id": surface_id})
    if surface.get("publication_ready_authority_allowed") is not False:
        issues.append({"code": "behavior_surface_publication_ready_authority_allowed", "surface_id": surface_id})


def _validate_runtime_continuity_completion(value: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(value, Mapping):
        issues.append({"code": "runtime_continuity_completion_missing"})
        return
    _validate_runtime_continuity_header(value, issues)
    _validate_runtime_continuity_session(value.get("runtime_session_read_model"), issues)
    _validate_runtime_continuity_trigger(value.get("safe_reconcile_trigger"), issues)
    _validate_runtime_continuity_user_projection(value.get("user_surface_projection"), issues)
    _validate_runtime_continuity_authority(value, issues)


def _validate_runtime_continuity_header(value: Mapping[str, Any], issues: list[dict[str, Any]]) -> None:
    if _text(value.get("surface")) != "mas_runtime_continuity_completion":
        issues.append({"code": "runtime_continuity_completion_wrong_surface"})
    if _text(value.get("status")) != "landed":
        issues.append({"code": "runtime_continuity_completion_not_landed"})
    if value.get("external_mds_repo_required") is not False:
        issues.append({"code": "runtime_continuity_external_mds_dependency"})
    if value.get("mds_daemon_required") is not False:
        issues.append({"code": "runtime_continuity_mds_daemon_dependency"})
    if _text(value.get("active_scheduler")) != "hermes_gateway_cron":
        issues.append({"code": "runtime_continuity_active_scheduler_drift"})
    if int(value.get("default_tick_interval_seconds") or 0) != 300:
        issues.append({"code": "runtime_continuity_tick_interval_drift"})


def _validate_runtime_continuity_session(session: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(session, Mapping):
        issues.append({"code": "runtime_continuity_session_read_model_missing"})
        return
    if _text(session.get("role")) != "read_model" or session.get("read_only") is not True:
        issues.append({"code": "runtime_continuity_session_role_drift"})
    if session.get("writes_authority_surface") is not False:
        issues.append({"code": "runtime_continuity_session_authority_write"})


def _validate_runtime_continuity_trigger(trigger: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(trigger, Mapping):
        issues.append({"code": "runtime_continuity_safe_trigger_missing"})
        return
    if trigger.get("executes_reconcile") is not False:
        issues.append({"code": "runtime_continuity_safe_trigger_executes_reconcile"})
    if trigger.get("writes_runtime") is not False:
        issues.append({"code": "runtime_continuity_safe_trigger_writes_runtime"})


def _validate_runtime_continuity_user_projection(
    user_projection: object,
    issues: list[dict[str, Any]],
) -> None:
    if not isinstance(user_projection, Mapping):
        issues.append({"code": "runtime_continuity_user_projection_missing"})
    elif user_projection.get("reinterprets_study_truth") is not False:
        issues.append({"code": "runtime_continuity_user_projection_reinterprets_truth"})


def _validate_runtime_continuity_authority(
    value: Mapping[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    for field in (
        "quality_ready_authorized",
        "publication_ready_authorized",
        "submission_ready_authorized",
    ):
        if value.get(field) is not False:
            issues.append({"code": f"runtime_continuity_{field}", "field": field})
