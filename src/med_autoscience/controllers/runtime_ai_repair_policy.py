from __future__ import annotations

from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts.queue_slo import (
    DEVELOPER_SUPERVISOR_ATTENTION_HOURS,
    OWNER_PICKUP_OVERDUE_HOURS,
)


SCHEMA_VERSION = 1
INTERNAL_AI_MONITOR_INTERVAL_SECONDS = 5 * 60
INTERNAL_AI_DOCTOR_TIMEOUT_SECONDS = 15 * 60
INTERNAL_NO_PROGRESS_REPAIR_AFTER_SECONDS = 30 * 60
DEVELOPER_HEARTBEAT_INTERVAL_SECONDS = 60 * 60


def default_executor_policy() -> dict[str, Any]:
    return {
        "executor_kind": "codex_cli_default",
        "executor_name": "Codex CLI",
        "executor_mode": "autonomous_agent_loop",
        "default_model_policy": "inherit_current_codex_configuration",
        "default_reasoning_effort_policy": "inherit_current_codex_configuration",
        "chat_completion_only_executor_forbidden": True,
    }


def two_layer_ai_repair_policy_payload() -> dict[str, Any]:
    return {
        "surface": "two_layer_ai_repair_policy",
        "schema_version": SCHEMA_VERSION,
        "internal_ai_repair": {
            "monitor_interval_seconds": INTERNAL_AI_MONITOR_INTERVAL_SECONDS,
            "ai_doctor_timeout_seconds": INTERNAL_AI_DOCTOR_TIMEOUT_SECONDS,
            "no_progress_repair_after_seconds": INTERNAL_NO_PROGRESS_REPAIR_AFTER_SECONDS,
            "trigger_principles": [
                "no_meaningful_progress",
                "same_fingerprint_loop",
                "read_churn_without_artifact_delta",
                "stale_truth_surface",
                "runtime_recovery_retry_budget_exhausted",
            ],
            "default_executor": default_executor_policy(),
        },
        "developer_supervisor": {
            "heartbeat_interval_seconds": DEVELOPER_HEARTBEAT_INTERVAL_SECONDS,
            "owner_pickup_overdue_after_hours": OWNER_PICKUP_OVERDUE_HOURS,
            "developer_attention_after_hours": DEVELOPER_SUPERVISOR_ATTENTION_HOURS,
            "default_enablement": {
                "authority_surface": "opl_family_user_config",
                "config_path": "~/Library/Application Support/OPL/state/developer-supervisor.json",
                "state_dir_env_override": "OPL_STATE_DIR",
                "workspace_profile_fields": [
                    "developer_supervisor_mode",
                    "github_username",
                    "mas_developer_github_usernames",
                ],
                "mas_developer_route": "direct_commit",
                "other_developer_route": "pull_request",
                "manual_enablement_supported": True,
                "unknown_github_user_fall_back_to": "external_observe",
            },
            "scope_policy": {
                "scope": "workspace_dynamic_active_studies",
                "new_mas_task_enrollment": "automatic_on_next_heartbeat",
                "hard_coded_study_allowlist_required": False,
            },
            "same_tick_actions": [
                "runtime domain-health-diagnostic --request-opl-stage-attempts --dry-run",
                "owner-route-reconcile --apply-safe-actions --developer-supervisor-mode developer_apply_safe",
                "OPL DomainProgressTransitionRuntime intake/readback",
                "OPL-authorized MAS owner-callable adapter or stable typed blocker",
            ],
            "repair_principles": [
                "consume_unowned_or_overdue_action_queue",
                "materialize_owner_callable_transition_request",
                "execute_only_after_opl_authorized_owner_callable_adapter",
                "preserve_owner_output_authority",
                "escalate_when_internal_ai_repair_did_not_apply",
            ],
        },
        "guardrails": {
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }


__all__ = [
    "DEVELOPER_HEARTBEAT_INTERVAL_SECONDS",
    "INTERNAL_AI_DOCTOR_TIMEOUT_SECONDS",
    "INTERNAL_AI_MONITOR_INTERVAL_SECONDS",
    "INTERNAL_NO_PROGRESS_REPAIR_AFTER_SECONDS",
    "default_executor_policy",
    "two_layer_ai_repair_policy_payload",
]
