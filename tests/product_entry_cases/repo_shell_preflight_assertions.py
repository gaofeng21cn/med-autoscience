from __future__ import annotations


def assert_manifest_preflight_and_guardrail_surfaces(*, module, payload, profile, profile_ref) -> None:
    preflight = payload["product_entry_preflight"]
    assert preflight["surface_kind"] == "product_entry_preflight"
    assert preflight["ready_to_try_now"] is True
    assert preflight["blocking_check_ids"] == []
    assert {check["check_id"] for check in preflight["checks"]} >= {
        "workspace_root_exists",
        "runtime_root_exists",
        "studies_root_exists",
        "opl_provider_stage_runtime_ready",
        "workspace_domain_route_contract_ready",
    }
    assert preflight["recommended_check_command"].endswith(
        "doctor report --profile " + str(profile_ref.resolve())
    )
    assert preflight["recommended_start_command"].endswith(
        "opl app product-entry-status --agent med-autoscience --profile "
        + str(profile_ref.resolve())
        + " --format json"
    )

    guardrails = payload["product_entry_guardrails"]
    assert guardrails["surface_kind"] == "product_entry_guardrails"
    assert {item["guardrail_id"] for item in guardrails["guardrail_classes"]} >= {
        "workspace_supervision_gap",
        "study_progress_gap",
        "user_decision_gate",
        "runtime_recovery_required",
        "quality_floor_blocker",
    }
    assert [step["step_id"] for step in guardrails["recovery_loop"]] == [
        "inspect_workspace_inbox",
        "refresh_supervision",
        "inspect_study_progress",
        "continue_or_relaunch",
    ]
    assert all("command" in step for step in guardrails["recovery_loop"])
