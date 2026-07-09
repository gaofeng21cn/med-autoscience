from __future__ import annotations


def _phase2_loop_without_guarded_fields(value: dict[str, object]) -> dict[str, object]:
    normalized = _without_command_metadata(value)
    workflow_steps = []
    for item in normalized.get("workflow_steps") or []:
        step = dict(item)
        step.pop("guarded_operator_command", None)
        step.pop("action_result", None)
        step.pop("authority_contract", None)
        workflow_steps.append(step)
    normalized["workflow_steps"] = workflow_steps
    return normalized


def _without_command_metadata(value):
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            if key in {
                "can_execute",
                "can_generate_action",
                "command_ref",
                "command_role",
                "recommended_command_ref",
            }:
                continue
            if key == "authority" and item is False:
                continue
            normalized[key] = _without_command_metadata(item)
        return normalized
    if isinstance(value, list):
        return [_without_command_metadata(item) for item in value]
    return value


def _assert_guarded_workflow_steps(value: dict[str, object]) -> None:
    for step in value.get("workflow_steps") or []:
        guarded_command = dict(step.get("guarded_operator_command") or {})
        action_result = dict(step.get("action_result") or {})
        authority_contract = dict(step.get("authority_contract") or {})
        assert guarded_command["guard"] == "existing_product_entry_controller_guard"
        assert guarded_command["status"] == "guarded_pending"
        assert action_result["status"] == "guarded_pending"
        assert authority_contract["can_mutate_runtime"] is False
        assert authority_contract["can_authorize_quality"] is False
        assert authority_contract["can_authorize_submission"] is False


def assert_manifest_entry_and_lifecycle_surfaces(*, module, payload, profile, profile_ref) -> None:
    assert payload["artifact_inventory"]["surface_kind"] == "artifact_inventory"
    assert payload["executor_defaults"]["owner_callable_adapter_name"] == "codex_cli"
    assert payload["executor_defaults"]["chat_completion_only_executor_forbidden"] is True

    assert payload["domain_entry_contract"]["entry_adapter"] == "MedAutoScienceDomainEntry"
    assert payload["domain_entry_contract"]["domain_agent_entry_spec"]["agent_id"] == "mas"
    assert payload["user_interaction_contract"]["entry_owner"] == "opl_product_entry_or_domain_gui"
    assert payload["user_interaction_contract"]["command_surfaces_for_agent_consumption_only"] is True

    assert payload["product_entry_surface"]["shell_key"] == "product_entry_status"
    assert payload["operator_loop_surface"]["shell_key"] == "workspace_cockpit"
    assert set(payload["operator_loop_actions"]) >= {
        "open_loop",
        "submit_task",
        "continue_study",
        "inspect_progress",
    }

    assert payload["repo_mainline"]["program_id"] == "research-foundry-medical-mainline"
    assert payload["repo_mainline"]["current_program_phase_id"] == "phase_2_user_product_loop"
    assert payload["single_project_boundary"]["surface_kind"] == "single_project_boundary"
    assert [item["role_id"] for item in payload["single_project_boundary"]["mds_retained_roles"]] == [
        "external_source_archive",
        "historical_fixture_ref",
        "explicit_archive_import_ref",
    ]

    assert payload["task_lifecycle"]["surface_kind"] == "task_lifecycle"
    assert payload["task_lifecycle"]["progress_surface"]["surface_kind"] == "workspace_cockpit"
    assert payload["task_lifecycle"]["resume_surface"]["surface_kind"] == "launch_study"
    assert payload["task_lifecycle"]["human_gate_ids"] == [
        "study_user_decision_gate",
        "publication_release_gate",
    ]

    skill = payload["skill_catalog"]["skills"][0]
    assert skill["skill_id"] == "mas"
    assert skill["domain_projection"]["recommended_shell"] == "workspace_cockpit"
    assert set(skill["domain_projection"]["supporting_shell_keys"]) == {
        "workspace_cockpit",
        "submit_study_task",
        "launch_study",
        "study_progress",
    }

    assert payload["automation"]["surface_kind"] == "automation"
    assert payload["automation"]["automations"][0]["gate_policy"] == "publication_gated"
    assert payload["product_entry_overview"]["recommended_step_id"] == "open_product_entry"
    assert payload["product_entry_readiness"]["verdict"] == "runtime_ready_not_standalone_product"
    assert payload["product_entry_readiness"]["usable_now"] is True
    assert payload["product_entry_readiness"]["fully_automatic"] is False

    phase2 = payload["phase2_user_product_loop"]
    assert phase2["surface_kind"] == "phase2_user_product_loop_lane"
    assert [step["step_id"] for step in phase2["single_path"]] == [
        "open_product_entry",
        "inspect_workspace_inbox",
        "submit_task",
        "continue_study",
        "inspect_progress",
        "handle_human_gate",
    ]
    assert {step["step_id"] for step in _phase2_loop_without_guarded_fields(phase2)["workflow_steps"]} >= {
        "run_provider_literature_scout",
        "materialize_route_decision",
        "authorize_manuscript_drafting",
    }
    _assert_guarded_workflow_steps(phase2)
