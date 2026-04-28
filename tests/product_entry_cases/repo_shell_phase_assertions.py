from __future__ import annotations

def _assert_phase3_clearance_lane(*, module, payload, profile, profile_ref) -> None:
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
        {"gate_id": "study_user_decision_gate", "title": "Study user decision gate"},
        {"gate_id": "publication_release_gate", "title": "Publication release gate"},
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

def _assert_phase4_backend_deconstruction_lane(*, module, payload, profile, profile_ref) -> None:
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
            "gate_id": "study_user_decision_gate",
            "legacy_gate_id": "study_physician_decision_gate",
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
        "study_user_decision_gate",
        "publication_release_gate",
    ]
    assert payload["product_entry_start"]["surface_kind"] == "product_entry_start"
    assert payload["product_entry_start"]["recommended_mode_id"] == "open_frontdesk"
    assert [mode["mode_id"] for mode in payload["product_entry_start"]["modes"]] == [
        "open_frontdesk",
        "submit_task",
        "continue_study",
    ]

def _assert_phase5_platform_target(*, module, payload, profile, profile_ref) -> None:
    assert payload["product_entry_start"]["modes"][0]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_start"]["modes"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_start"]["modes"][2]["surface_kind"] == "launch_study"
    assert payload["product_entry_start"]["resume_surface"] == payload["family_orchestration"]["resume_contract"]
    assert payload["product_entry_start"]["human_gate_ids"] == [
        "study_user_decision_gate",
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

def assert_manifest_phase_and_readiness_surfaces(*, module, payload, profile, profile_ref) -> None:
    _assert_phase3_clearance_lane(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_phase4_backend_deconstruction_lane(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_phase5_platform_target(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
