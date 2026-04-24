from __future__ import annotations

from . import shared as _shared
from . import chunk_01 as _chunk_01
from . import chunk_02 as _chunk_02
from . import chunk_03 as _chunk_03

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_chunk_01)
_module_reexport(_chunk_02)
_module_reexport(_chunk_03)

def test_build_product_entry_manifest_projects_repo_shell_and_shared_handoff_templates(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            med_deepscientist_runtime_exists=True,
            medical_overlay_ready=True,
            external_runtime_contract={"ready": True},
            workspace_supervision_contract={
                "status": "loaded",
                "loaded": True,
                "summary": "Hermes-hosted runtime supervision 已在线。",
                "drift_reasons": [],
            },
        ),
    )

    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {
                "id": "f4_blocker_closeout",
                "status": "in_progress",
                "summary": "继续收口 blocker 并把用户入口壳压实。",
            },
            "current_program_phase": {
                "id": "phase_2_user_product_loop",
                "status": "in_progress",
                "summary": "把用户 inbox 与持续进度回路收成稳定壳。",
            },
            "next_focus": [
                "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
            ],
            "remaining_gaps": [
                "mature standalone medical product entry is still not landed",
            ],
        },
    )

    payload = module.build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
    )

    assert payload["surface_kind"] == "product_entry_manifest"
    assert payload["manifest_version"] == 2
    assert payload["manifest_kind"] == "med_autoscience_product_entry_manifest"
    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["formal_entry"]["default"] == "CLI"
    assert payload["formal_entry"]["supported_protocols"] == ["MCP"]
    assert payload["runtime"]["runtime_owner"] == "upstream_hermes_agent"
    assert payload["runtime"]["domain_owner"] == "med-autoscience"
    assert payload["runtime"]["executor_owner"] == "med_deepscientist"
    assert payload["runtime"]["runtime_substrate"] == "external_hermes_agent_target"
    assert payload["managed_runtime_contract"] == {
        "shared_contract_ref": "contracts/opl-gateway/managed-runtime-three-layer-contract.json",
        "runtime_owner": "upstream_hermes_agent",
        "domain_owner": "med-autoscience",
        "executor_owner": "med_deepscientist",
        "supervision_status_surface": {
            "surface_kind": "study_progress",
            "owner": "med-autoscience",
        },
        "attention_queue_surface": {
            "surface_kind": "workspace_cockpit",
            "owner": "med-autoscience",
        },
        "recovery_contract_surface": {
            "surface_kind": "study_runtime_status",
            "owner": "med-autoscience",
        },
        "fail_closed_rules": [
            "domain_supervision_cannot_bypass_runtime",
            "executor_cannot_declare_global_gate_clear",
            "runtime_cannot_invent_domain_publishability_truth",
        ],
    }
    assert payload["runtime_inventory"]["surface_kind"] == "runtime_inventory"
    assert payload["runtime_inventory"]["runtime_owner"] == "upstream_hermes_agent"
    assert payload["runtime_inventory"]["domain_owner"] == "med-autoscience"
    assert payload["runtime_inventory"]["executor_owner"] == "med_deepscientist"
    assert payload["runtime_inventory"]["substrate"] == "external_hermes_agent_target"
    assert payload["runtime_inventory"]["availability"] == "ready"
    assert payload["runtime_inventory"]["health_status"] == "healthy"
    assert payload["runtime_inventory"]["status_surface"]["ref_kind"] == "workspace_locator"
    assert payload["runtime_inventory"]["status_surface"]["ref"] == "studies/<study_id>/artifacts/runtime_watch/latest.json"
    assert payload["runtime_inventory"]["attention_surface"]["ref_kind"] == "json_pointer"
    assert payload["runtime_inventory"]["attention_surface"]["ref"] == "/operator_loop_surface"
    assert payload["runtime_inventory"]["recovery_surface"]["ref_kind"] == "json_pointer"
    assert payload["runtime_inventory"]["recovery_surface"]["ref"] == "/managed_runtime_contract/recovery_contract_surface"
    assert payload["runtime_inventory"]["workspace_binding"]["workspace_root"] == str(profile.workspace_root)
    assert payload["runtime_inventory"]["workspace_binding"]["profile_name"] == profile.name
    assert payload["runtime_inventory"]["domain_projection"]["managed_runtime_backend_id"] == profile.managed_runtime_backend_id
    assert payload["session_continuity"]["surface_kind"] == "session_continuity"
    assert payload["session_continuity"]["domain_agent_id"] == "mas"
    assert payload["session_continuity"]["restore_surface"]["surface_kind"] == "launch_study"
    assert payload["session_continuity"]["progress_surface"]["surface_kind"] == "study_progress"
    assert payload["session_continuity"]["artifact_surface"]["surface_kind"] == "study_runtime_status"
    assert payload["progress_projection"]["surface_kind"] == "progress_projection"
    assert payload["progress_projection"]["progress_surface"]["surface_kind"] == "workspace_cockpit"
    assert "studies/<study_id>/artifacts" in payload["progress_projection"]["inspect_paths"]
    assert payload["progress_projection"]["domain_projection"]["research_runtime_control_projection"] == {
        "surface_kind": "research_runtime_control_projection",
        "study_session_owner": {
            "runtime_owner": "upstream_hermes_agent",
            "study_owner": "med-autoscience",
            "executor_owner": "med_deepscientist",
        },
        "session_lineage_surface": {
            "surface_kind": "study_progress",
            "field_path": "family_checkpoint_lineage",
            "resume_contract_field": "family_checkpoint_lineage.resume_contract",
            "continuation_state_field": "continuation_state",
            "active_run_id_field": "supervision.active_run_id",
        },
        "restore_point_surface": {
            "surface_kind": "study_progress",
            "field_path": "autonomy_contract.restore_point",
            "lineage_anchor_field": "family_checkpoint_lineage.resume_contract",
            "summary_field": "autonomy_contract.restore_point.summary",
        },
        "progress_cursor_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
        },
        "progress_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
            "fallback_field_path": "next_system_action",
        },
        "artifact_inventory_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs",
        },
        "artifact_pickup_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs.evaluation_summary_path",
            "fallback_fields": [
                "refs.publication_eval_path",
                "refs.controller_decision_path",
                "refs.runtime_supervision_path",
                "refs.runtime_watch_report_path",
            ],
            "pickup_refs_field": "research_runtime_control_projection.artifact_pickup_surface.pickup_refs",
        },
        "command_templates": {
            "resume": (
                "uv run python -m med_autoscience.cli launch-study --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id>"
            ),
            "check_progress": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --format json"
            ),
            "check_runtime_status": (
                "uv run python -m med_autoscience.cli study-runtime-status --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --format json"
            ),
        },
        "research_gate_surface": {
            "surface_kind": "study_progress",
            "approval_gate_field": "needs_physician_decision",
            "approval_gate_required_field": "needs_physician_decision",
            "approval_gate_owner": "mas_controller",
            "interrupt_policy_field": "intervention_lane.recommended_action_id",
            "interrupt_policy_value_field": "intervention_lane.recommended_action_id",
            "gate_lane_field": "intervention_lane.lane_id",
            "gate_summary_field": "intervention_lane.summary",
            "human_gate_required_field": "autonomy_contract.restore_point.human_gate_required",
        },
    }
    assert payload["artifact_inventory"]["surface_kind"] == "artifact_inventory"
    assert payload["artifact_inventory"]["summary"]["deliverable_files_count"] == 0
    assert payload["artifact_inventory"]["summary"]["supporting_files_count"] == 5
    assert payload["artifact_inventory"]["summary"]["total_files_count"] == 5
    assert payload["artifact_inventory"]["supporting_files"][0]["kind"] == "supporting"
    assert any(
        entry.get("path") == "studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json"
        for entry in payload["artifact_inventory"]["supporting_files"]
    )
    assert payload["executor_defaults"]["default_executor_name"] == "codex_cli"
    assert payload["executor_defaults"]["default_executor_mode"] == "autonomous"
    assert payload["executor_defaults"]["default_model"] == "inherit_local_codex_default"
    assert payload["executor_defaults"]["default_reasoning_effort"] == "inherit_local_codex_default"
    assert payload["executor_defaults"]["executor_labels"] == {
        "codex_cli": "Codex CLI",
        "hermes_agent": "Hermes-Agent",
    }
    assert payload["executor_defaults"]["executor_statuses"] == {
        "codex_cli": "default",
        "hermes_agent": "experimental",
    }
    assert payload["executor_defaults"]["chat_completion_only_executor_forbidden"] is True
    assert payload["executor_defaults"]["hermes_agent_requires_full_agent_loop"] is True
    assert "default_executor" not in payload["executor_defaults"]
    assert "hermes_native_requires_full_agent_loop" not in payload["executor_defaults"]
    assert payload["executor_defaults"]["current_backend_chain"][1].endswith(
        "codex exec autonomous agent loop"
    )
    assert payload["executor_defaults"]["optional_executor_proofs"] == [
        {
            "executor_kind": "hermes_native_proof",
            "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
            "requires_full_agent_loop": True,
            "default_model": "inherit_local_hermes_default",
            "default_reasoning_effort": "inherit_local_hermes_default",
        }
    ]
    assert payload["workspace_locator"]["profile_name"] == profile.name
    assert payload["recommended_shell"] == "workspace_cockpit"
    assert payload["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["schema_ref"] == "contracts/schemas/v1/product-entry-manifest.schema.json"
    assert payload["domain_entry_contract"]["entry_adapter"] == "MedAutoScienceDomainEntry"
    assert payload["domain_entry_contract"]["product_entry_builder_command"] == "build-product-entry"
    assert payload["domain_entry_contract"]["domain_agent_entry_spec"]["agent_id"] == "mas"
    assert payload["domain_entry_contract"]["domain_agent_entry_spec"]["default_engine"] == "codex"
    assert payload["domain_entry_contract"]["domain_agent_entry_spec"]["entry_command"] == "product-frontdesk"
    assert payload["domain_entry_contract"]["domain_agent_entry_spec"]["manifest_command"] == "product-entry-manifest"
    assert payload["gateway_interaction_contract"]["frontdoor_owner"] == "opl_gateway_or_domain_gui"
    assert payload["gateway_interaction_contract"]["user_interaction_mode"] == "natural_language_frontdoor"
    assert payload["gateway_interaction_contract"]["command_surfaces_for_agent_consumption_only"] is True
    assert payload["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["frontdesk_surface"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["frontdesk_surface"]["surface_kind"] == "product_frontdesk"
    assert "research product frontdesk" in payload["frontdesk_surface"]["summary"]
    assert payload["operator_loop_surface"]["shell_key"] == "workspace_cockpit"
    assert payload["operator_loop_surface"]["command"] == payload["recommended_command"]
    assert payload["operator_loop_surface"]["surface_kind"] == "workspace_cockpit"
    assert "workspace 级用户 inbox" in payload["operator_loop_surface"]["summary"]
    assert payload["operator_loop_actions"]["open_loop"]["command"] == payload["recommended_command"]
    assert payload["operator_loop_actions"]["open_loop"]["surface_kind"] == "workspace_cockpit"
    assert payload["operator_loop_actions"]["submit_task"]["requires"] == ["study_id", "task_intent"]
    assert payload["operator_loop_actions"]["continue_study"]["requires"] == ["study_id"]
    assert payload["operator_loop_actions"]["inspect_progress"]["command"].endswith(
        "study-progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --format json"
    )
    assert payload["product_entry_quickstart"]["surface_kind"] == "product_entry_quickstart"
    assert payload["product_entry_quickstart"]["recommended_step_id"] == "open_frontdesk"
    assert [step["step_id"] for step in payload["product_entry_quickstart"]["steps"]] == [
        "open_frontdesk",
        "submit_task",
        "continue_study",
        "inspect_progress",
    ]
    assert payload["product_entry_quickstart"]["steps"][0]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_quickstart"]["steps"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_quickstart"]["steps"][2]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["product_entry_quickstart"]["steps"][3]["surface_kind"] == "study_progress"
    assert payload["repo_mainline"]["program_id"] == "research-foundry-medical-mainline"
    assert payload["repo_mainline"]["current_program_phase_id"] == "phase_2_user_product_loop"
    assert payload["repo_mainline"]["current_stage_summary"] == "继续收口 blocker 并把用户入口壳压实。"
    assert payload["repo_mainline"]["current_program_phase_summary"] == "把用户 inbox 与持续进度回路收成稳定壳。"
    assert payload["repo_mainline"]["next_focus"] == [
        "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
    ]
    assert payload["single_project_boundary"]["surface_kind"] == "single_project_boundary"
    assert list(payload["single_project_boundary"]["mas_owner_modules"]) == [
        "controller_charter",
        "runtime",
        "eval_hygiene",
    ]
    assert payload["capability_owner_boundary"]["surface_kind"] == "mas_capability_owner_boundary"
    assert payload["capability_owner_boundary"]["owner"] == "MedAutoScience"
    assert payload["capability_owner_boundary"]["proof_and_absorb_boundary"]["physical_absorb_status"] == (
        "blocked_post_gate"
    )
    assert [item["role_id"] for item in payload["single_project_boundary"]["mds_retained_roles"]] == [
        "research_backend",
        "behavior_equivalence_oracle",
        "upstream_intake_buffer",
    ]
    assert "physical monorepo absorb" in payload["single_project_boundary"]["post_gate_only"]
    assert payload["product_entry_status"]["summary"] == "继续收口 blocker 并把用户入口壳压实。"
    assert payload["product_entry_status"]["remaining_gaps_count"] == 1
    assert payload["product_entry_status"]["next_focus"] == [
        "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
    ]
    assert payload["task_lifecycle"]["surface_kind"] == "task_lifecycle"
    assert payload["task_lifecycle"]["task_kind"] == "mas_product_entry_mainline"
    assert payload["task_lifecycle"]["task_id"] == "research-foundry-medical-mainline:f4_blocker_closeout"
    assert payload["task_lifecycle"]["status"] == "in_progress"
    assert payload["task_lifecycle"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["task_lifecycle"]["progress_surface"]["surface_kind"] == "workspace_cockpit"
    assert payload["task_lifecycle"]["progress_surface"]["step_id"] == "inspect_workspace_inbox"
    assert payload["task_lifecycle"]["progress_surface"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["task_lifecycle"]["resume_surface"]["surface_kind"] == "launch_study"
    assert payload["task_lifecycle"]["resume_surface"]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["task_lifecycle"]["checkpoint_summary"]["surface_kind"] == "checkpoint_summary"
    assert payload["task_lifecycle"]["checkpoint_summary"]["status"] == "monitoring_required"
    assert payload["task_lifecycle"]["checkpoint_summary"]["lineage_ref"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        "label": "controller checkpoint lineage companion",
    }
    assert payload["task_lifecycle"]["checkpoint_summary"]["verification_ref"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
        "label": "runtime watch event companion",
    }
    assert payload["task_lifecycle"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert payload["task_lifecycle"]["domain_projection"]["current_program_phase_id"] == "phase_2_user_product_loop"
    assert payload["task_lifecycle"]["domain_projection"]["recommended_loop_surface"] == "workspace_cockpit"
    assert payload["task_lifecycle"]["domain_projection"]["recommended_loop_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["skill_catalog"]["surface_kind"] == "skill_catalog"
    assert payload["skill_catalog"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["skill_catalog"]["supported_commands"] == payload["domain_entry_contract"]["supported_commands"]
    assert payload["skill_catalog"]["command_contracts"] == payload["domain_entry_contract"]["command_contracts"]
    assert [item["skill_id"] for item in payload["skill_catalog"]["skills"]] == ["med-autoscience"]
    assert payload["skill_catalog"]["skills"][0]["target_surface_kind"] == "product_frontdesk"
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["skill_semantics"] == "domain_app"
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["skill_entry"] == "med-autoscience"
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["recommended_shell"] == "workspace_cockpit"
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["entry_shell_key"] == "product_frontdesk"
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["entry_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["supporting_shell_keys"] == [
        "workspace_cockpit",
        "submit_study_task",
        "launch_study",
        "study_progress",
    ]
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["shell_commands"]["submit_study_task"].endswith(
        "--study-id <study_id> --task-intent '<task_intent>'"
    )
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["shell_commands"]["study_progress"].endswith(
        "--study-id <study_id> --format json"
    )
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["runtime_continuity"] == {
        "surface_kind": "skill_runtime_continuity",
        "runtime_owner": "upstream_hermes_agent",
        "domain_owner": "med-autoscience",
        "executor_owner": "med_deepscientist",
        "session_locator_field": "study_id",
        "session_surface_ref": "/session_continuity",
        "progress_surface_ref": "/progress_projection/progress_surface",
        "artifact_surface_ref": "/artifact_inventory/artifact_surface",
        "restore_point_surface_ref": (
            "/progress_projection/domain_projection/research_runtime_control_projection/restore_point_surface"
        ),
        "recommended_resume_command": (
            "uv run python -m med_autoscience.cli launch-study --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id>"
        ),
        "recommended_progress_command": (
            "uv run python -m med_autoscience.cli study-progress --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id> --format json"
        ),
        "recommended_artifact_command": (
            "uv run python -m med_autoscience.cli study-runtime-status --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id> --format json"
        ),
    }
    assert payload["automation"]["surface_kind"] == "automation"
    assert payload["automation"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["automation"]["readiness_summary"].startswith("Automation-ready rule:")
    assert payload["automation"]["automations"] == [
        {
            "surface_kind": "automation_descriptor",
            "automation_id": "mas_runtime_supervision_loop",
            "title": "MAS runtime supervision loop",
            "owner": "med-autoscience",
            "trigger_kind": "interval",
            "target_surface_kind": "runtime_watch_refresh",
            "summary": "按监督节拍刷新 study runtime，保持恢复建议和 attention queue 为最新状态。",
            "readiness_status": "automation_ready",
            "gate_policy": "publication_gated",
            "output_expectation": [
                "refresh runtime watch",
                "update workspace attention queue",
                "preserve controller decision lineage",
            ],
            "target_command": (
                "uv run python -m med_autoscience.cli watch --runtime-root "
                + str(profile.runtime_root)
                + " --profile "
                + str(profile_ref.resolve())
                + " --ensure-study-runtimes --apply"
            ),
            "domain_projection": {
                "service_status_command": str(
                    profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
                ),
                "recommended_entry_surface": "workspace_cockpit",
            },
        }
    ]
    assert payload["product_entry_overview"]["surface_kind"] == "product_entry_overview"
    assert payload["product_entry_overview"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["product_entry_overview"]["frontdesk_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_overview"]["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["product_entry_overview"]["progress_surface"] == {
        "surface_kind": "study_progress",
        "command": (
            "uv run python -m med_autoscience.cli study-progress --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id> --format json"
        ),
        "step_id": "inspect_progress",
    }
    assert payload["product_entry_overview"]["resume_surface"] == {
        "surface_kind": "launch_study",
        "command": (
            "uv run python -m med_autoscience.cli launch-study --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id>"
        ),
        "session_locator_field": "study_id",
        "checkpoint_locator_field": "controller_decision_path",
    }
    assert payload["product_entry_overview"]["recommended_step_id"] == "open_frontdesk"
    assert payload["product_entry_overview"]["next_focus"] == [
        "继续把 workspace inbox、study progress 与恢复建议收成统一产品壳。",
    ]
    assert payload["product_entry_overview"]["remaining_gaps_count"] == 1
    assert payload["product_entry_overview"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    markdown = module.render_product_entry_manifest_markdown(payload)
    assert "Single-Project Boundary" in markdown
    assert "Capability Owner Boundary" in markdown
    assert "MAS capability `publication_quality_gate`" in markdown
    assert "MDS migration-only `research_backend`" in markdown
    assert "physical absorb: blocked_post_gate" in markdown
    assert "MDS 保留 `research_backend`" in markdown
    assert "post-gate only: physical monorepo absorb" in markdown
    assert payload["product_entry_readiness"] == {
        "surface_kind": "product_entry_readiness",
        "verdict": "runtime_ready_not_standalone_product",
        "usable_now": True,
        "good_to_use_now": False,
        "fully_automatic": False,
        "summary": (
            "当前可以作为 research frontdesk / CLI 主线使用，并通过稳定的 runtime 回路持续推进研究；"
            "但还不是成熟的独立医学产品前台。"
        ),
        "recommended_start_surface": "product_frontdesk",
        "recommended_start_command": (
            "uv run python -m med_autoscience.cli product-frontdesk --profile "
            + str(profile_ref.resolve())
        ),
        "recommended_loop_surface": "workspace_cockpit",
        "recommended_loop_command": (
            "uv run python -m med_autoscience.cli workspace-cockpit --profile "
            + str(profile_ref.resolve())
            + " --format json"
        ),
        "blocking_gaps": [
            "独立医学前台 / hosted product entry 仍未 landed。",
            "更多 workspace / host 的真实 clearance 与 study-local blocker 收口仍在继续。",
        ],
    }
    assert payload["phase2_user_product_loop"] == {
        "surface_kind": "phase2_user_product_loop_lane",
        "summary": "把启动 MAS、给 study 下任务、续跑、持续看进度、处理恢复建议和人工 gate 收成同一条用户回路。",
        "recommended_step_id": "open_frontdesk",
        "recommended_command": (
            "uv run python -m med_autoscience.cli product-frontdesk --profile "
            + str(profile_ref.resolve())
        ),
        "single_path": [
            {
                "step_id": "open_frontdesk",
                "title": "先打开 MAS 前台",
                "surface_kind": "product_frontdesk",
                "command": (
                    "uv run python -m med_autoscience.cli product-frontdesk --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "inspect_workspace_inbox",
                "title": "确认当前 workspace inbox / attention queue",
                "surface_kind": "workspace_cockpit",
                "command": (
                    "uv run python -m med_autoscience.cli workspace-cockpit --profile "
                    + str(profile_ref.resolve())
                    + " --format json"
                ),
            },
            {
                "step_id": "submit_task",
                "title": "给目标 study 写 durable task intake",
                "surface_kind": "study_task_intake",
                "command": (
                    "uv run python -m med_autoscience.cli submit-study-task --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --task-intent '<task_intent>'"
                ),
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑当前 study",
                "surface_kind": "launch_study",
                "command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看进度、阻塞和恢复建议",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
            {
                "step_id": "handle_human_gate",
                "title": "遇到人工 gate 时回到 progress / cockpit 做决策",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
        ],
        "operator_questions": [
            {
                "question": "用户现在怎么启动 MAS？",
                "answer_surface_kind": "product_frontdesk",
                "command": (
                    "uv run python -m med_autoscience.cli product-frontdesk --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "question": "用户怎么给 study 下任务？",
                "answer_surface_kind": "study_task_intake",
                "command": (
                    "uv run python -m med_autoscience.cli submit-study-task --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --task-intent '<task_intent>'"
                ),
            },
            {
                "question": "用户怎么持续看进度和恢复建议？",
                "answer_surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "product_frontdesk",
                "command": (
                    "uv run python -m med_autoscience.cli product-frontdesk --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "surface_kind": "workspace_cockpit",
                "command": (
                    "uv run python -m med_autoscience.cli workspace-cockpit --profile "
                    + str(profile_ref.resolve())
                    + " --format json"
                ),
            },
            {
                "surface_kind": "study_progress.operator_verdict",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
            {
                "surface_kind": "study_progress.recovery_contract",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
            {
                "surface_kind": "controller_decisions",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            },
        ],
    }
    assert payload["product_entry_preflight"] == {
        "surface_kind": "product_entry_preflight",
        "summary": "当前 product-entry 前置检查已通过，可以先复核 doctor 输出，再进入 research frontdesk。",
        "ready_to_try_now": True,
        "recommended_check_command": (
            "uv run python -m med_autoscience.cli doctor --profile "
            + str(profile_ref.resolve())
        ),
        "recommended_start_command": (
            "uv run python -m med_autoscience.cli product-frontdesk --profile "
            + str(profile_ref.resolve())
        ),
        "blocking_check_ids": [],
        "checks": [
            {
                "check_id": "workspace_root_exists",
                "title": "Workspace Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "workspace 根目录已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "runtime_root_exists",
                "title": "Runtime Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "runtime root 已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "studies_root_exists",
                "title": "Studies Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "studies 根目录已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "portfolio_root_exists",
                "title": "Portfolio Root Exists",
                "status": "pass",
                "blocking": True,
                "summary": "portfolio 根目录已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "research_backend_runtime_ready",
                "title": "Research Backend Runtime Ready",
                "status": "pass",
                "blocking": True,
                "summary": "受控 research backend runtime 已就位。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "medical_overlay_ready",
                "title": "Medical Overlay Ready",
                "status": "pass",
                "blocking": True,
                "summary": "medical overlay 已 ready。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "external_runtime_contract_ready",
                "title": "External Runtime Contract Ready",
                "status": "pass",
                "blocking": True,
                "summary": "external Hermes runtime contract 已 ready。",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "check_id": "workspace_supervision_contract_ready",
                "title": "Workspace Supervision Contract Ready",
                "status": "pass",
                "blocking": True,
                "summary": "workspace supervision owner 已收敛到 canonical Hermes supervision。",
                "command": (
                    "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                    + str(profile_ref.resolve())
                ),
            },
        ],
    }
    assert payload["product_entry_guardrails"] == {
        "surface_kind": "product_entry_guardrails",
        "summary": (
            "把卡住、没进度、监管掉线、需要人工决策和质量阻塞显式投影成可执行恢复回路，"
            "避免研究主线失去监管。"
        ),
        "guardrail_classes": [
            {
                "guardrail_id": "workspace_supervision_gap",
                "trigger": "workspace-cockpit attention queue / study-progress supervisor freshness",
                    "symptom": "Hermes-hosted supervision 未在线、supervisor tick stale/missing、托管恢复真相不再新鲜。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli watch --runtime-root "
                    + str(profile.runtime_root)
                    + " --profile "
                    + str(profile_ref.resolve())
                    + " --ensure-study-runtimes --apply"
                ),
            },
            {
                "guardrail_id": "study_progress_gap",
                "trigger": "study-progress progress_freshness / workspace-cockpit attention queue",
                "symptom": "当前 study 进度 stale 或 missing，疑似卡住、空转或没有新的明确推进证据。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "guardrail_id": "human_decision_gate",
                "trigger": "study-progress needs_physician_decision / controller decision gate",
                "symptom": "当前已前移到医生、PI 或 publication release 的人工判断节点。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "guardrail_id": "runtime_recovery_required",
                "trigger": "study-progress intervention_lane / runtime_supervision health_status / workspace-cockpit attention queue",
                "symptom": "托管运行恢复失败、健康降级或长期停在恢复态，当前必须优先处理 runtime recovery。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "guardrail_id": "quality_floor_blocker",
                "trigger": "study-progress intervention_lane / runtime watch figure-loop alerts / publication gate",
                "symptom": "研究输出质量、figure/reference floor 或 publication gate 出现硬阻塞，不能继续盲目长跑。",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
        ],
        "recovery_loop": [
            {
                "step_id": "inspect_workspace_inbox",
                "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile " + str(profile_ref.resolve()),
                "surface_kind": "workspace_cockpit",
            },
            {
                "step_id": "refresh_supervision",
                "command": (
                    "uv run python -m med_autoscience.cli watch --runtime-root "
                    + str(profile.runtime_root)
                    + " --profile "
                    + str(profile_ref.resolve())
                    + " --ensure-study-runtimes --apply"
                ),
                "surface_kind": "runtime_watch_refresh",
            },
            {
                "step_id": "inspect_study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
                "surface_kind": "study_progress",
            },
            {
                "step_id": "continue_or_relaunch",
                "command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
                "surface_kind": "launch_study",
            },
        ],
    }
    assert payload["phase3_clearance_lane"] == {
        "surface_kind": "phase3_host_clearance_lane",
        "summary": "Phase 3 把 external runtime、Hermes-hosted workspace supervision 和 study recovery proof 扩到更多 workspace/host，并保持 fail-closed。",
        "recommended_step_id": "external_runtime_contract",
        "recommended_command": (
            "uv run python -m med_autoscience.cli doctor --profile "
            + str(profile_ref.resolve())
        ),
        "clearance_targets": [
            {
                "target_id": "external_runtime_contract",
                "title": "Check external Hermes runtime contract",
                "commands": [
                    "uv run python -m med_autoscience.cli doctor --profile " + str(profile_ref.resolve()),
                    "uv run python -m med_autoscience.cli hermes-runtime-check --profile " + str(profile_ref.resolve()),
                ],
            },
            {
                "target_id": "supervisor_service",
                "title": "Keep Hermes-hosted workspace supervision online",
                "commands": [
                    (
                        "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                        + str(profile_ref.resolve())
                    ),
                    (
                        "uv run python -m med_autoscience.cli watch --runtime-root "
                        + str(profile.runtime_root)
                        + " --profile "
                        + str(profile_ref.resolve())
                        + " --ensure-study-runtimes --apply"
                    ),
                ],
            },
            {
                "target_id": "study_recovery_proof",
                "title": "Prove live study recovery and supervision",
                "commands": [
                    (
                        "uv run python -m med_autoscience.cli launch-study --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                    (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id <study_id>"
                    ),
                ],
            },
        ],
        "clearance_loop": [
            {
                "step_id": "external_runtime_contract",
                "title": "先确认 external Hermes runtime contract ready",
                "surface_kind": "doctor_runtime_contract",
                "command": (
                    "uv run python -m med_autoscience.cli doctor --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "hermes_runtime_check",
                "title": "确认 Hermes runtime 绑定证据",
                "surface_kind": "hermes_runtime_check",
                "command": (
                    "uv run python -m med_autoscience.cli hermes-runtime-check --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "supervisor_service",
                "title": "确认 workspace 常驻监管在线",
                "surface_kind": "workspace_supervisor_service",
                "command": (
                    "uv run python -m med_autoscience.cli runtime-supervision-status --profile "
                    + str(profile_ref.resolve())
                ),
            },
            {
                "step_id": "refresh_supervision",
                "title": "刷新 Hermes-hosted supervision tick",
                "surface_kind": "runtime_watch_refresh",
                "command": (
                    "uv run python -m med_autoscience.cli watch --runtime-root "
                    + str(profile.runtime_root)
                    + " --profile "
                    + str(profile_ref.resolve())
                    + " --ensure-study-runtimes --apply"
                ),
            },
            {
                "step_id": "study_recovery_proof",
                "title": "证明 live study recovery / progress supervision 成立",
                "surface_kind": "launch_study",
                "command": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "step_id": "inspect_study_progress",
                "title": "读取 study-progress proof",
                "surface_kind": "study_progress",
                "command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "doctor.external_runtime_contract",
                "command": "uv run python -m med_autoscience.cli doctor --profile " + str(profile_ref.resolve()),
            },
            {
                "surface_kind": "study_runtime_status.autonomous_runtime_notice",
                "command": (
                    "uv run python -m med_autoscience.cli study-runtime-status --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
            },
            {
                "surface_kind": "runtime_watch",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_watch" / "latest.json"),
            },
            {
                "surface_kind": "runtime_supervision",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_supervision" / "latest.json"),
            },
            {
                "surface_kind": "controller_decisions",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            },
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    }
    assert payload["phase4_backend_deconstruction"] == {
        "surface_kind": "phase4_backend_deconstruction_lane",
        "summary": "Phase 4 把可迁出的通用 runtime 能力继续迁向 substrate，同时诚实保留 controlled backend executor。",
        "substrate_targets": [
            {
                "capability_id": "session_run_watch_recovery",
                "owner": "upstream Hermes-Agent",
                "summary": "session / run / watch / recovery / scheduling / interruption 继续收归 outer runtime substrate。",
            },
            {
                "capability_id": "backend_generic_runtime_contract",
                "owner": "MedAutoScience controller boundary",
                "summary": "controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            },
        ],
        "backend_retained_now": [
            "MedDeepScientist CodexRunner autonomous executor chain",
            "backend-local agent/tool routing and Codex skills",
            "quest-local research execution, paper worktree, and daemon side effects",
        ],
        "current_backend_chain": [
            "med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist",
            "med_deepscientist CodexRunner -> codex exec autonomous agent loop",
        ],
        "optional_executor_proofs": [
            {
                "executor_kind": "hermes_native_proof",
                "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        "promotion_rules": [
            "no claim of backend retirement without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "no physical monorepo absorb before the external gate is cleared",
        ],
        "deconstruction_map_doc": "docs/program/med_deepscientist_deconstruction_map.md",
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    }
    assert payload["phase5_platform_target"] == {
        "surface_kind": "phase5_platform_target",
        "summary": (
            "Phase 5 的目标是把 MAS 继续收敛到 federation/platform-ready 形态，"
            "包括 post-gate monorepo、runtime core ingest 和更成熟的 direct product entry；"
            "但这些都必须建立在前四阶段真实成立之后。"
        ),
        "sequence_scope": "monorepo_landing_readiness",
        "current_readiness_summary": (
            "单项目长线已经完成 gateway/runtime truth 冻结，当前正在推进 user product loop hardening 与边界收紧；"
            "physical absorb 仍然严格属于 post-gate 工作。"
        ),
        "north_star_topology": {
            "domain_gateway": "Med Auto Science",
            "outer_runtime_substrate_owner": "upstream Hermes-Agent",
            "controlled_research_backend": "MedDeepScientist",
            "monorepo_status": "post_gate_target",
        },
        "target_internal_modules": [
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        "landing_sequence": [
            {
                "step_id": "freeze_gateway_runtime_truth",
                "title": "Freeze gateway/runtime truth",
                "status": "completed",
                "phase_id": "phase_1_mainline_established",
                "summary": "mainline topology、product-entry companions 与 post-gate platform wording 已冻结成 repo-tracked truth。",
            },
                {
                    "step_id": "stabilize_user_product_loop",
                    "title": "Stabilize user product loop",
                    "status": "in_progress",
                    "phase_id": "phase_2_user_product_loop",
                    "summary": (
                        "当前活跃步骤：用 autonomy / quality / single-project owner 三线继续收紧 MAS "
                        "owner truth，并把启动 / 下任务 / 看进度 / 看恢复建议收成稳定前台回路。"
                    ),
                },
            {
                "step_id": "clear_multi_workspace_host_gate",
                "title": "Clear multi-workspace / host gate",
                "status": "pending",
                "phase_id": "phase_3_multi_workspace_host_clearance",
                "summary": "把 runtime/service/recovery proof 扩到更多 workspace / host 后，才具备更大 cutover 资格。",
            },
            {
                "step_id": "freeze_backend_deconstruction_boundary",
                "title": "Freeze backend deconstruction boundary",
                "status": "pending",
                "phase_id": "phase_4_backend_deconstruction",
                "summary": "先把 substrate 与 backend retained-now 的边界继续收紧，再谈 executor 迁移或 ingest。",
            },
            {
                "step_id": "physical_monorepo_absorb",
                "title": "Physical monorepo absorb",
                "status": "blocked_post_gate",
                "phase_id": "phase_5_federation_platform_maturation",
                "summary": "只有在前面几步都稳定通过后，controller_charter / runtime / eval_hygiene 才能进入 post-gate 物理 monorepo absorb。",
            },
        ],
        "current_step_id": "stabilize_user_product_loop",
        "completed_step_ids": [
            "freeze_gateway_runtime_truth",
        ],
        "remaining_step_ids": [
            "clear_multi_workspace_host_gate",
            "freeze_backend_deconstruction_boundary",
            "physical_monorepo_absorb",
        ],
        "promotion_gates": [
            "phase_1_mainline_established",
            "phase_2_user_product_loop",
            "phase_3_multi_workspace_host_clearance",
            "phase_4_backend_deconstruction",
        ],
        "land_now": [
            "repo-tracked product-entry shell and family orchestration companions",
            "controller-owned runtime/progress/recovery truth",
            "CLI/MCP/controller entry surfaces that already support real work",
        ],
        "not_yet": [
            "physical monorepo absorb",
            "runtime core ingest across repos",
            "mature hosted standalone medical frontend",
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_federation_platform_maturation"
        ),
    }
    assert payload["product_entry_shell"]["workspace_cockpit"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["product_entry_shell"]["product_frontdesk"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_shell"]["submit_study_task"]["command"].endswith(
        "submit-study-task --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --task-intent '<task_intent>'"
    )
    assert payload["product_entry_shell"]["launch_study"]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["product_entry_shell"]["study_progress"]["command"].endswith(
        "study-progress --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --format json"
    )
    assert payload["shared_handoff"]["direct_entry_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode direct"
    )
    assert payload["shared_handoff"]["opl_handoff_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode opl-handoff"
    )
    assert payload["family_orchestration"]["human_gates"] == [
        {
            "gate_id": "study_physician_decision_gate",
            "title": "Study physician decision gate",
        },
        {
            "gate_id": "publication_release_gate",
            "title": "Publication release gate",
        },
    ]
    assert payload["family_orchestration"]["action_graph_ref"] == {
        "ref_kind": "json_pointer",
        "ref": "/family_orchestration/action_graph",
        "label": "mas family action graph",
    }
    assert payload["family_orchestration"]["action_graph"]["graph_id"] == (
        "mas_workspace_frontdoor_study_runtime_graph"
    )
    assert payload["family_orchestration"]["action_graph"]["target_domain_id"] == "med-autoscience"
    assert [node["node_id"] for node in payload["family_orchestration"]["action_graph"]["nodes"]] == [
        "step:open_frontdesk",
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert payload["family_orchestration"]["action_graph"]["edges"] == [
        {
            "from": "step:open_frontdesk",
            "to": "step:submit_task",
            "on": "new_task",
        },
        {
            "from": "step:open_frontdesk",
            "to": "step:continue_study",
            "on": "resume_study",
        },
        {
            "from": "step:open_frontdesk",
            "to": "step:inspect_progress",
            "on": "inspect_status",
        },
        {
            "from": "step:submit_task",
            "to": "step:continue_study",
            "on": "task_written",
        },
        {
            "from": "step:continue_study",
            "to": "step:inspect_progress",
            "on": "progress_refresh",
        },
    ]
    assert payload["family_orchestration"]["action_graph"]["entry_nodes"] == [
        "step:open_frontdesk",
    ]
    assert payload["family_orchestration"]["action_graph"]["exit_nodes"] == [
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert payload["family_orchestration"]["action_graph"]["human_gates"] == [
        {
            "gate_id": "study_physician_decision_gate",
            "trigger_nodes": ["step:continue_study"],
            "blocking": True,
        },
        {
            "gate_id": "publication_release_gate",
            "trigger_nodes": ["step:inspect_progress"],
            "blocking": True,
        },
    ]
    assert payload["family_orchestration"]["action_graph"]["checkpoint_policy"] == {
        "mode": "explicit_nodes",
        "checkpoint_nodes": [
            "step:submit_task",
            "step:continue_study",
            "step:inspect_progress",
        ],
    }
    assert payload["family_orchestration"]["resume_contract"] == {
        "surface_kind": "launch_study",
        "session_locator_field": "study_id",
        "checkpoint_locator_field": "controller_decision_path",
    }
    assert payload["family_orchestration"]["event_envelope_surface"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
        "label": "runtime watch event companion",
    }
    assert payload["family_orchestration"]["checkpoint_lineage_surface"] == {
        "ref_kind": "workspace_locator",
        "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        "label": "controller checkpoint lineage companion",
    }
    assert payload["product_entry_quickstart"]["resume_contract"] == payload["family_orchestration"]["resume_contract"]
    assert payload["product_entry_quickstart"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert payload["product_entry_start"]["surface_kind"] == "product_entry_start"
    assert payload["product_entry_start"]["recommended_mode_id"] == "open_frontdesk"
    assert [mode["mode_id"] for mode in payload["product_entry_start"]["modes"]] == [
        "open_frontdesk",
        "submit_task",
        "continue_study",
    ]
    assert payload["product_entry_start"]["modes"][0]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_start"]["modes"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_start"]["modes"][2]["surface_kind"] == "launch_study"
    assert payload["product_entry_start"]["resume_surface"] == payload["family_orchestration"]["resume_contract"]
    assert payload["product_entry_start"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert "standalone medical product entry" in payload["remaining_gaps"][0]
    start_markdown = module.render_product_entry_start_markdown(payload["product_entry_start"])
    assert "当前摘要" in start_markdown
    assert "建议入口" in start_markdown
    assert "恢复入口" in start_markdown
    assert "可用入口" in start_markdown
    assert "recommended_mode_id:" not in start_markdown
    assert "resume_surface:" not in start_markdown
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
