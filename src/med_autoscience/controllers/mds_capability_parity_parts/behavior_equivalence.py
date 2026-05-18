from __future__ import annotations

import copy
from typing import Any, Mapping

from med_autoscience.controllers.mds_capability_parity_parts.paper_progress_degradation import (
    ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES,
    build_mds_paper_progress_degradation_classifier,
    paper_progress_degradation_for_surface,
    validate_behavior_surface_paper_progress,
    validate_paper_progress_degradation_classifier,
)


SCHEMA_VERSION = 1
PROVENANCE_REF = "docs/references/med-deepscientist/source_provenance.json"
MDS_FINAL_ROLE = "frozen_source_archive_or_historical_fixture_only"
ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES: tuple[str, ...] = (
    "behavior_equivalent",
    "purpose_equivalent_with_different_timing",
    "purpose_equivalent_with_authority_split",
    "partially_equivalent",
    "not_equivalent_retired",
    "historical_fixture_only",
)
ALLOWED_BEHAVIOR_OPERATOR_ACTIONS: tuple[str, ...] = (
    "use_mas_default",
    "use_mas_with_latency_awareness",
    "use_progress_portal",
    "use_explicit_archive_import_ref_only",
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
            "default_owner": "opl_provider_runtime_manager",
            "default_adapter": "opl",
            "legacy_diagnostic_adapters": ["local_launchd"],
            "optional_adapters": ["hermes_gateway_cron"],
            "tick_interval_seconds": 300,
            "tick_command": "opl family-runtime tick --source provider-scheduler --hydrate",
        },
        "behavior_difference": "MAS default supervision is scheduled ticks, not a resident HTTP/WebSocket daemon.",
        "default_user_impact": "Runtime drift detection can be delayed up to the scheduler interval; HTTP/WebSocket session continuity is not provided by MAS Runtime OS.",
        "mas_contract": "OPL provider/runtime manager owns the default outer scheduler cadence and MAS returns paper-progress SLO, owner receipts, typed blockers, and safe action refs; local LaunchAgent is legacy diagnostic cleanup only.",
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
            "cadence": "OPL provider scheduler replacement tick",
            "default_adapter": "opl",
            "legacy_diagnostic_adapters": ["local_launchd"],
            "optional_adapters": ["hermes_gateway_cron"],
            "interval_seconds": 300,
            "max_ticks": 1,
            "inner_turn_continuation_owner": "MAS Runtime Turn Lifecycle Kernel",
        },
        "behavior_difference": "MDS can supervise while the daemon is alive; MAS default outer supervision reacts on the next scheduled tick, while per-turn continuation is handled by the MAS turn kernel.",
        "default_user_impact": "Five-minute latency remains for outer drift detection and stale recovery, but normal turn-to-turn continuation no longer waits for the cron tick.",
        "mas_contract": "OPL scheduler replacement triggers provider SLO, MAS domain intake, and family-runtime tick; MAS keeps runtime_watch/progress freshness interpretation and MAS-owned recovery receipts.",
        "recommended_operator_action": "use_mas_with_latency_awareness",
    },
    {
        "surface_id": "turn_completion_continuation",
        "title": "Turn completion continuation",
        "equivalence_class": "behavior_equivalent",
        "mds_behavior": {
            "runner_completion_normalizes_state": True,
            "queued_user_messages_take_priority": True,
            "auto_continue_delay_seconds": 0.2,
            "human_or_terminal_gate_stops": True,
        },
        "mas_behavior": {
            "runner_completion_normalizes_state": True,
            "queued_user_messages_take_priority": True,
            "auto_continue_delay_seconds": 0.2,
            "human_or_terminal_gate_stops": True,
            "owner": "MAS Runtime Turn Lifecycle Kernel",
        },
        "behavior_difference": "MAS implements the continuation decision inside mas_runtime_core instead of depending on an external resident MDS daemon.",
        "default_user_impact": "A normal running quest can continue from one turn to the next without waiting for the 300s outer supervision tick.",
        "mas_contract": "schedule_turn, complete_turn_and_normalize, runner monitor, delayed auto_continue timer, user message queue and worker lease own per-quest turn continuation.",
        "recommended_operator_action": "use_mas_default",
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
            "runner_monitor": True,
            "worker_lease": True,
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
            "in_process_turn_continuation": "runner monitor plus complete_turn_and_normalize",
            "worker_restart": "MAS controller-authorized recovery action",
        },
        "behavior_difference": "MDS resumes at daemon startup; MAS resumes when the MAS scheduler invokes the next tick or an operator runs watch explicitly.",
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
            "runtime_turn_user_queue": True,
            "daemon_mailbox": False,
        },
        "behavior_difference": "MAS now has a quest-local user message queue for runtime turns plus durable task intake/controller handoff; chat connector background delivery remains outside default MAS.",
        "default_user_impact": "Research task intake and queued messages during active worker execution are covered; chat-like connector delivery is not a default MAS capability.",
        "mas_contract": "chat_quest writes user_message_queue and triggers schedule_turn; latest task intake, controller decision, owner_route and supervisor consume/dispatch own broader actionable work.",
        "recommended_operator_action": "use_mas_default",
    },
    {
        "surface_id": "progress_visibility",
        "title": "Progress visibility",
        "equivalence_class": "partially_equivalent",
        "mds_behavior": {
            "web_status": True,
            "api_status": True,
            "primary_scope": "project_or_quest",
            "paper_scoped_navigation": True,
        },
        "mas_behavior": {
            "progress_portal": True,
            "study_progress": True,
            "workspace_cockpit": True,
            "primary_scope": "workspace_shell_with_per_study_pages",
            "paper_scoped_navigation": "landed_per_study_pages",
            "route_decision_trail": "landed_read_only",
            "conversation_read_model": "landed_read_only_visible_panel",
            "portal_console_soak_user_parity_keys": True,
        },
        "behavior_difference": "MAS now has per-study Progress Portal pages, stable study deep links, a read-only route/decision trail helper, a visible per-study Conversation panel backed by the runtime conversation read model, and soak evidence keys, but full old-WebUI UX parity still needs real-workspace polish and interactive terminal attach gates.",
        "default_user_impact": "Users can inspect MAS progress without running MDS WebUI, enter a single-study workbench, and see executor conversation/timeline evidence; final WebUI user parity remains evidence-gated by real workspace soak and interactive safety gates.",
        "mas_contract": "Progress Portal consumes MAS payload refs, freshness, source refs, artifact locators, mas_progress_portal_study_workbench, mas_progress_portal_route_decision_trail, mas_runtime_conversation_read_model, and portal_console_soak evidence without reinterpreting study truth or medical quality.",
        "future_parity_candidate": "real_workspace_user_soak_and_interactive_gate_polish",
        "recommended_operator_action": "use_progress_portal",
    },
    {
        "surface_id": "webui_websocket_terminal_streaming",
        "title": "WebUI, WebSocket, and terminal streaming",
        "equivalence_class": "purpose_equivalent_with_different_timing",
        "mds_behavior": {"react_webui": True, "websocket_terminal_attach": True, "bash_log_streaming": True},
        "mas_behavior": {
            "progress_portal": "default progress and blocker entry",
            "live_console": "MAS-authored session/run/terminal/log observation shell",
            "stream_transport": "SSE snapshot/loopback stream for observation",
            "websocket_terminal_attach": "mas_owner_available_or_blocked_by_missing_terminal_input_owner",
            "terminal_attach_gate": "mas_terminal_attach_gate",
            "terminal_attach_owner": "mas_terminal_attach_owner",
            "authorized_portal_actions": "controller_authorized_apply_for_pause_resume_stop",
            "bash_log_streaming": "read-only terminal/log tail refs",
        },
        "behavior_difference": "MAS preserves the observation purpose through Progress Portal plus Live Console and now exposes explicit local-loopback authorized Portal actions for pause/resume/stop through MAS runtime owner surfaces; terminal attach/input/resize/detach is MAS-owner gated rather than owned by the old resident WebSocket path.",
        "default_user_impact": "Users now have MAS-owned progress, live observation surfaces, gated pause/resume/stop apply when Progress Portal is served with --enable-actions, and attach/input/resize/detach UI/API when a MAS terminal attach owner is available.",
        "mas_contract": "live-console-parity owns workspace/study/run, terminal.tail, log.tail, runtime.health, runtime.supervision and artifact.delta read models; mas_terminal_attach_gate fails closed by default and exposes mas_terminal_attach_owner attach/input/resize/detach endpoints when the owner contract is available.",
        "future_parity_candidate": "real_workspace_terminal_attach_owner_soak",
        "recommended_operator_action": "use_mas_with_latency_awareness",
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
        "equivalence_class": "purpose_equivalent_with_authority_split",
        "mds_behavior": {"memory_service": True, "lesson_store": True},
        "mas_behavior": {
            "portfolio_research_memory": True,
            "canonical_literature": True,
            "stage_knowledge_packet": True,
            "stage_memory_closeout_packet": True,
            "memory_write_router_receipt": True,
            "stage_recall_index": True,
            "quality_authority": False,
        },
        "behavior_difference": "MAS preserves the research-memory purpose through stage entry consumption and controlled closeout writeback, while splitting authority across workspace, study, quest, evidence, review, and controller owners instead of exposing a generic autonomous memory truth service.",
        "default_user_impact": "Codex stages can consume high-signal memory and literature at entry and submit reusable lessons, citation gaps, failed paths, reference-role updates, and claim-boundary decisions at closeout; those writes remain receipt-gated and cannot authorize quality, route, claim expansion, or publication readiness.",
        "mas_contract": "stage_knowledge_packet, stage_memory_closeout_packet, memory_write_router_receipt, stage_recall_index, portfolio/research_memory, canonical literature, reference context, evidence/review ledgers, and controller decisions share authority by owner boundary.",
        "remaining_gap_until_soak": "real-paper stage injection soak must keep proving consumed refs, accepted/rejected writes, route impact, and next owner in Progress/Portal surfaces.",
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
        "mas_behavior": {"external_mds_daemon_control": False, "mas_supervision_scheduler_control": False},
        "behavior_difference": "MAS does not control an MDS daemon lifecycle and no longer owns the default outer scheduler lifecycle.",
        "default_user_impact": "There is no MAS-native MDS daemon control path because the daemon is not a default dependency.",
        "mas_contract": "Default runtime-supervision commands delegate to the OPL provider scheduler replacement; local scheduler is physical-retired tombstone/provenance-only.",
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
            "canonical_owner": "opl_provider_runtime_manager",
            "default_adapter": "opl",
            "legacy_diagnostic_adapter": None,
            "optional_adapters": ["hermes_gateway_cron"],
        },
        "behavior_difference": "Workspace-local launchd/systemd/cron service templates are retired; their presence is cleanup evidence, not an active owner.",
        "default_user_impact": "Old host services must be removed instead of kept as an alternate supervision mode.",
        "mas_contract": "Retired workspace-local services are tombstone/provenance evidence; default scheduler status delegates to OPL provider replacement.",
        "recommended_operator_action": "retired_no_active_replacement",
    },
)

RUNTIME_CONTINUITY_COMPLETION = {
    "surface": "mas_runtime_continuity_completion",
    "status": "landed",
    "owner": "MedAutoScience Runtime OS",
    "external_mds_repo_required": False,
    "mds_daemon_required": False,
    "active_scheduler": "opl_provider_runtime_manager",
    "active_scheduler_adapter": "opl",
    "legacy_diagnostic_scheduler": "mas_supervision_scheduler",
    "legacy_diagnostic_scheduler_adapter": "local",
    "optional_scheduler_adapters": ["hermes_gateway_cron"],
    "default_tick_interval_seconds": 300,
    "runtime_session_read_model": {
        "surface_kind": "runtime_session_read_model",
        "role": "read_model",
        "read_only": True,
        "source_priority": [
            "study_runtime_status/runtime_liveness_audit",
            "runtime_lifecycle_store",
            "owner_route/dispatch_receipts",
            "historical_fixture_ref",
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
    projection["paper_progress_degradation"] = paper_progress_degradation_for_surface(
        _text(projection.get("surface_id"))
    )
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
    paper_progress_classifier = build_mds_paper_progress_degradation_classifier(surfaces)
    return {
        "surface": "mds_behavior_equivalence_matrix",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "mds_final_role": MDS_FINAL_ROLE,
        "default_operation_requires_external_mds": False,
        "default_diagnostic_requires_external_mds": False,
        "default_supervision_owner": "opl_provider_runtime_manager",
        "default_scheduler_adapter": "opl",
        "optional_scheduler_adapters": ["hermes_gateway_cron"],
        "default_tick_interval_seconds": 300,
        "default_tick_max_ticks": 1,
        "default_tick_command": "opl family-runtime tick --source provider-scheduler --hydrate",
        "mas_default_runtime_is_resident_daemon": False,
        "mds_daemon_was_resident_http_websocket_server": True,
        "completion_claim": "default_independence_not_full_behavior_equivalence",
        "allowed_equivalence_classes": list(ALLOWED_BEHAVIOR_EQUIVALENCE_CLASSES),
        "allowed_operator_actions": list(ALLOWED_BEHAVIOR_OPERATOR_ACTIONS),
        "allowed_paper_progress_degradation_classes": list(ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES),
        "behavior_surfaces": surfaces,
        "paper_progress_degradation_classifier": paper_progress_classifier,
        "paper_progress_degradation_summary": paper_progress_classifier["summary"],
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
    validate_paper_progress_degradation_classifier(matrix, issues)
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
    if _text(matrix.get("default_supervision_owner")) != "opl_provider_runtime_manager":
        issues.append({"code": "behavior_matrix_default_supervision_owner_drift"})
    if _text(matrix.get("default_scheduler_adapter")) != "opl":
        issues.append({"code": "behavior_matrix_default_scheduler_adapter_drift"})
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
    if list(matrix.get("allowed_paper_progress_degradation_classes") or []) != list(
        ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES
    ):
        issues.append({"code": "behavior_matrix_allowed_paper_progress_degradation_classes_drift"})


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
    validate_behavior_surface_paper_progress(surface, surface_id, issues)
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
    if _text(value.get("active_scheduler")) != "opl_provider_runtime_manager":
        issues.append({"code": "runtime_continuity_active_scheduler_drift"})
    if _text(value.get("active_scheduler_adapter")) != "opl":
        issues.append({"code": "runtime_continuity_active_scheduler_adapter_drift"})
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
