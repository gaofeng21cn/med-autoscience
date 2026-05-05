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
    assert payload["developer_supervisor"]["same_tick_actions"] == [
        "runtime supervisor-scan --apply-safe-actions --developer-supervisor-mode developer_apply_safe",
        "runtime supervisor-consume --mode developer_apply_safe --apply",
        "runtime supervisor-execute-dispatch --mode developer_apply_safe --apply",
    ]
    assert "execute_ready_default_executor_dispatches" in payload["developer_supervisor"]["repair_principles"]
    assert payload["guardrails"]["paper_package_mutation_allowed"] is False
    assert payload["guardrails"]["quality_gate_relaxation_allowed"] is False
