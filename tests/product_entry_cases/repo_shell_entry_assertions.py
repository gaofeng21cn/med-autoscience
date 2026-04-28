from __future__ import annotations

def _assert_artifact_inventory_surface(*, module, payload, profile, profile_ref) -> None:
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

def _assert_executor_default_surface(*, module, payload, profile, profile_ref) -> None:
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

def _assert_artifact_inventory_and_executor_defaults(*, module, payload, profile, profile_ref) -> None:
    _assert_artifact_inventory_surface(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_executor_default_surface(module=module, payload=payload, profile=profile, profile_ref=profile_ref)

def _assert_entry_contract_surfaces(*, module, payload, profile, profile_ref) -> None:
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

def _assert_mainline_boundary_surface(*, module, payload, profile, profile_ref) -> None:
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

def _assert_task_lifecycle_surface(*, module, payload, profile, profile_ref) -> None:
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

def _assert_mainline_boundary_and_task_lifecycle(*, module, payload, profile, profile_ref) -> None:
    _assert_mainline_boundary_surface(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_task_lifecycle_surface(module=module, payload=payload, profile=profile, profile_ref=profile_ref)

def _assert_skill_catalog_projection(*, module, payload, profile, profile_ref) -> None:
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
        "study_user_decision_gate",
        "publication_release_gate",
    ]
    assert payload["task_lifecycle"]["domain_projection"]["current_program_phase_id"] == "phase_2_user_product_loop"
    assert payload["task_lifecycle"]["domain_projection"]["recommended_loop_surface"] == "workspace_cockpit"
    assert payload["task_lifecycle"]["domain_projection"]["recommended_loop_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["skill_catalog"]["surface_kind"] == "skill_catalog"
    assert payload["skill_catalog"]["summary"] == payload["product_entry_status"]["summary"]

def _assert_automation_surface(*, module, payload, profile, profile_ref) -> None:
    assert payload["skill_catalog"]["supported_commands"] == payload["domain_entry_contract"]["supported_commands"]
    assert payload["skill_catalog"]["command_contracts"] == payload["domain_entry_contract"]["command_contracts"]
    assert [item["skill_id"] for item in payload["skill_catalog"]["skills"]] == ["mas"]
    assert payload["skill_catalog"]["skills"][0]["target_surface_kind"] == "product_frontdesk"
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["skill_semantics"] == "domain_app"
    assert payload["skill_catalog"]["skills"][0]["domain_projection"]["skill_entry"] == "mas"
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

def _assert_product_entry_overview_surface(*, module, payload, profile, profile_ref) -> None:
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

def _assert_automation_and_product_overview(*, module, payload, profile, profile_ref) -> None:
    _assert_automation_surface(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_product_entry_overview_surface(module=module, payload=payload, profile=profile, profile_ref=profile_ref)

def _assert_readiness_and_phase2_loop(*, module, payload, profile, profile_ref) -> None:
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
        "study_user_decision_gate",
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

def assert_manifest_entry_and_lifecycle_surfaces(*, module, payload, profile, profile_ref) -> None:
    _assert_artifact_inventory_and_executor_defaults(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_entry_contract_surfaces(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_mainline_boundary_and_task_lifecycle(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_skill_catalog_projection(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_automation_and_product_overview(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_readiness_and_phase2_loop(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
