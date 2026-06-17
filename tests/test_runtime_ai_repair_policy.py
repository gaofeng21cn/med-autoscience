from __future__ import annotations

import importlib


def test_two_layer_ai_repair_policy_freezes_intervals_and_escalation_thresholds() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_ai_repair_policy")

    payload = module.two_layer_ai_repair_policy_payload()

    assert payload["surface"] == "two_layer_ai_repair_policy"
    assert payload["internal_ai_repair"]["monitor_interval_seconds"] == 300
    assert payload["internal_ai_repair"]["ai_doctor_timeout_seconds"] == 900
    assert payload["internal_ai_repair"]["no_progress_repair_after_seconds"] == 1800
    assert payload["internal_ai_repair"]["default_executor"]["executor_kind"] == "codex_cli_default"
    assert payload["developer_supervisor"]["heartbeat_interval_seconds"] == 3600
    assert payload["developer_supervisor"]["owner_pickup_overdue_after_hours"] == 2
    assert payload["developer_supervisor"]["developer_attention_after_hours"] == 6
    assert payload["developer_supervisor"]["default_enablement"] == {
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
    }
    assert payload["developer_supervisor"]["scope_policy"] == {
        "scope": "workspace_dynamic_active_studies",
        "new_mas_task_enrollment": "automatic_on_next_heartbeat",
        "hard_coded_study_allowlist_required": False,
    }
    assert payload["developer_supervisor"]["same_tick_actions"] == [
        "runtime domain-health-diagnostic --request-opl-stage-attempts --dry-run",
        "owner-route-reconcile --apply-safe-actions --developer-supervisor-mode developer_apply_safe",
        "runtime domain-action-request-materialize --mode developer_apply_safe --apply",
        "runtime domain-owner-action-dispatch --mode developer_apply_safe --apply",
    ]
    assert (
        "execute_only_after_opl_authorized_owner_callable_adapter"
        in payload["developer_supervisor"]["repair_principles"]
    )
    assert payload["guardrails"]["paper_package_mutation_allowed"] is False
    assert payload["guardrails"]["quality_gate_relaxation_allowed"] is False
