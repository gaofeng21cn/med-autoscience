from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from . import cockpit_status_and_frontdesk_focus as _cockpit_status_and_frontdesk_focus
from . import manifest_launch_and_task_intake as _manifest_launch_and_task_intake
from . import repo_shell_and_handoff_templates as _repo_shell_and_handoff_templates

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_cockpit_status_and_frontdesk_focus)
_module_reexport(_manifest_launch_and_task_intake)
_module_reexport(_repo_shell_and_handoff_templates)

def test_build_product_frontdesk_projects_frontdoor_over_current_workspace_loop(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = tmp_path / "profile.local.toml"
    profile = make_profile(tmp_path)

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
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "ready_for_task",
                "summary": "当前 workspace 已 ready，下一步先给目标 study 写 durable task intake。",
                "should_intervene_now": False,
                "focus_scope": "workspace",
                "focus_study_id": None,
                "recommended_step_id": "submit_task",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli submit-study-task --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --task-intent '<task_intent>'"
                ),
            },
            "attention_queue": [],
        },
    )

    payload = module.build_product_frontdesk(
        profile=profile,
        profile_ref=profile_ref,
    )

    assert payload["surface_kind"] == "product_frontdesk"
    assert payload["recommended_action"] == "inspect_or_prepare_research_loop"
    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["schema_ref"] == "contracts/schemas/v1/product-frontdesk.schema.json"
    assert payload["domain_entry_contract"]["entry_adapter"] == "MedAutoScienceDomainEntry"
    assert payload["gateway_interaction_contract"]["frontdoor_owner"] == "opl_gateway_or_domain_gui"
    assert payload["gateway_interaction_contract"]["user_interaction_mode"] == "natural_language_frontdoor"
    assert payload["gateway_interaction_contract"]["user_commands_required"] is False
    assert payload["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["frontdesk_surface"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["operator_loop_surface"]["shell_key"] == "workspace_cockpit"
    assert payload["operator_loop_actions"]["open_loop"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["entry_surfaces"]["frontdesk"]["command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["entry_surfaces"]["cockpit"]["command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["entry_surfaces"]["direct_entry_builder"]["command"].endswith(
        "build-product-entry --profile " + str(profile_ref.resolve()) + " --study-id <study_id> --entry-mode direct"
    )
    assert payload["summary"]["frontdesk_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["summary"]["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["product_entry_overview"]["summary"] == payload["product_entry_status"]["summary"]
    assert payload["product_entry_overview"]["progress_surface"]["surface_kind"] == "study_progress"
    assert payload["product_entry_overview"]["resume_surface"]["surface_kind"] == "launch_study"
    assert payload["product_entry_overview"]["resume_surface"]["command"].endswith(
        "launch-study --profile " + str(profile_ref.resolve()) + " --study-id <study_id>"
    )
    assert payload["product_entry_readiness"]["surface_kind"] == "product_entry_readiness"
    assert payload["product_entry_readiness"]["verdict"] == "runtime_ready_not_standalone_product"
    assert payload["product_entry_readiness"]["usable_now"] is True
    assert payload["product_entry_readiness"]["good_to_use_now"] is False
    assert payload["product_entry_preflight"]["surface_kind"] == "product_entry_preflight"
    assert payload["product_entry_preflight"]["ready_to_try_now"] is True
    assert payload["product_entry_preflight"]["recommended_check_command"].endswith(
        "doctor --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_preflight"]["recommended_start_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["product_entry_preflight"]["blocking_check_ids"] == []
    assert [check["check_id"] for check in payload["product_entry_preflight"]["checks"]] == [
        "workspace_root_exists",
        "runtime_root_exists",
        "studies_root_exists",
        "portfolio_root_exists",
        "research_backend_runtime_ready",
        "medical_overlay_ready",
        "external_runtime_contract_ready",
        "workspace_supervision_contract_ready",
    ]
    assert payload["product_entry_readiness"]["recommended_start_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["phase2_user_product_loop"]["recommended_command"].endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )
    assert payload["phase2_user_product_loop"]["single_path"][2]["surface_kind"] == "study_task_intake"
    assert payload["phase2_user_product_loop"]["proof_surfaces"][1]["surface_kind"] == "workspace_cockpit"
    assert payload["operator_brief"] == {
        "surface_kind": "product_frontdesk_operator_brief",
        "verdict": "ready_for_task",
        "summary": "当前 workspace 已 ready，下一步先给目标 study 下任务，再启动研究。",
        "should_intervene_now": False,
        "focus_scope": "workspace",
        "focus_study_id": None,
        "recommended_step_id": "submit_task",
        "recommended_command": (
            "uv run python -m med_autoscience.cli submit-study-task --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id> --task-intent '<task_intent>'"
        ),
    }
    assert payload["workspace_operator_brief"]["verdict"] == "ready_for_task"
    assert payload["workspace_attention_queue_preview"] == []
    assert payload["product_entry_guardrails"]["surface_kind"] == "product_entry_guardrails"
    assert payload["product_entry_guardrails"]["guardrail_classes"][0]["guardrail_id"] == "workspace_supervision_gap"
    assert payload["product_entry_guardrails"]["guardrail_classes"][3]["guardrail_id"] == "runtime_recovery_required"
    assert payload["product_entry_guardrails"]["guardrail_classes"][4]["guardrail_id"] == "quality_floor_blocker"
    assert payload["product_entry_guardrails"]["recovery_loop"][1]["step_id"] == "refresh_supervision"
    assert payload["phase3_clearance_lane"]["surface_kind"] == "phase3_host_clearance_lane"
    assert payload["phase3_clearance_lane"]["recommended_step_id"] == "external_runtime_contract"
    assert payload["phase3_clearance_lane"]["clearance_targets"][1]["target_id"] == "supervisor_service"
    assert payload["phase3_clearance_lane"]["clearance_loop"][2]["step_id"] == "supervisor_service"
    assert payload["phase4_backend_deconstruction"]["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert payload["phase4_backend_deconstruction"]["current_backend_chain"][1].endswith(
        "codex exec autonomous agent loop"
    )
    assert payload["phase5_platform_target"]["surface_kind"] == "phase5_platform_target"
    assert payload["phase5_platform_target"]["current_step_id"] == "stabilize_user_product_loop"
    assert payload["phase5_platform_target"]["north_star_topology"]["monorepo_status"] == "post_gate_target"
    assert payload["single_project_boundary"]["surface_kind"] == "single_project_boundary"
    assert list(payload["single_project_boundary"]["mas_owner_modules"]) == [
        "controller_charter",
        "runtime",
        "eval_hygiene",
    ]
    assert payload["product_entry_quickstart"]["recommended_step_id"] == "open_frontdesk"
    assert payload["product_entry_quickstart"]["steps"][2]["step_id"] == "continue_study"
    assert payload["product_entry_quickstart"]["steps"][2]["requires"] == ["study_id"]
    assert payload["product_entry_start"]["surface_kind"] == "product_entry_start"


def test_workspace_cockpit_flags_supervision_owner_drift_even_when_study_progress_is_fresh(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

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
                "status": "legacy_only",
                "loaded": False,
                "summary": "检测到 legacy workspace-local runtime supervision service 仍在运行，当前 canonical Hermes supervision 尚未接管。",
                "drift_reasons": ["legacy_service_loaded"],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_workspace_supervision",
        lambda profile: {
            "manager": "launchd",
            "status": "legacy_only",
            "loaded": False,
            "summary": "检测到 legacy workspace-local runtime supervision service 仍在运行，当前 canonical Hermes supervision 尚未接管。",
            "drift_reasons": ["legacy_service_loaded"],
            "legacy_service": {"loaded": True, "service_exists": True},
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {
                "id": "f4_blocker_closeout",
                "status": "in_progress",
                "summary": "当前主线仍在 blocker 收口与 product-entry hardening。",
            },
            "current_program_phase": {
                "id": "phase_1_mainline_established",
                "status": "in_progress",
                "summary": "当前仍在第一阶段尾声。",
            },
            "next_focus": ["keep runtime truth visible"],
            "explicitly_not_now": [],
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": [],
            "next_system_action": "继续当前主线。",
            "intervention_lane": {
                "lane_id": "monitor_only",
                "title": "继续监督当前 study",
                "severity": "info",
                "summary": "当前继续监督即可。",
                "recommended_action_id": "inspect_progress",
            },
            "operator_verdict": {
                "surface_kind": "study_operator_verdict",
                "verdict_id": "study_operator_verdict::001-risk::monitor_only",
                "study_id": "001-risk",
                "lane_id": "monitor_only",
                "severity": "info",
                "decision_mode": "monitor_only",
                "needs_intervention": False,
                "focus_scope": "study",
                "summary": "当前继续监督即可。",
                "reason_summary": "当前继续监督即可。",
                "primary_step_id": "inspect_progress",
                "primary_surface_kind": "study_progress",
                "primary_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "monitor_only",
                "action_mode": "inspect_progress",
                "summary": "当前继续监督即可。",
                "recommended_step_id": "inspect_progress",
                "steps": [],
            },
            "needs_physician_decision": False,
            "supervision": {
                "browser_url": "http://127.0.0.1:21001",
                "quest_session_api_url": None,
                "active_run_id": "run-001",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert payload["workspace_status"] == "blocked"
    assert payload["workspace_supervision"]["service"]["status"] == "legacy_only"
    assert payload["attention_queue"][0]["code"] == "workspace_supervisor_service_not_loaded"
    assert payload["attention_queue"][0]["recommended_command"].endswith(
        "runtime-supervision-status --profile " + str(profile_ref.resolve())
    )


def test_build_product_frontdesk_preflight_blocks_on_workspace_supervision_owner_drift(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = tmp_path / "profile.local.toml"
    profile = make_profile(tmp_path)

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
                "status": "legacy_only",
                "loaded": False,
                "summary": "检测到 legacy workspace-local runtime supervision service 仍在运行，当前 canonical Hermes supervision 尚未接管。",
                "drift_reasons": ["legacy_service_loaded"],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "ready_for_task",
                "summary": "当前 workspace 已 ready，下一步先给目标 study 写 durable task intake。",
                "should_intervene_now": False,
                "focus_scope": "workspace",
                "focus_study_id": None,
                "recommended_step_id": "submit_task",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli submit-study-task --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --task-intent '<task_intent>'"
                ),
            },
            "attention_queue": [],
        },
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["product_entry_preflight"]["ready_to_try_now"] is False
    assert "workspace_supervision_contract_ready" in payload["product_entry_preflight"]["blocking_check_ids"]
    assert payload["operator_brief"]["verdict"] == "preflight_blocked"
    assert "legacy workspace-local runtime supervision service" in payload["product_entry_preflight"]["summary"]
    assert payload["product_entry_start"]["recommended_mode_id"] == "open_frontdesk"
    assert payload["product_entry_start"]["modes"][1]["mode_id"] == "submit_task"
    assert payload["product_entry_start"]["modes"][1]["requires"] == ["study_id", "task_intent"]
    assert payload["product_entry_start"]["resume_surface"]["surface_kind"] == "launch_study"
    assert payload["product_entry_start"]["human_gate_ids"] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]
    assert payload["family_orchestration"]["action_graph_ref"]["ref"] == "/family_orchestration/action_graph"
    assert payload["family_orchestration"]["action_graph"]["graph_id"] == (
        "mas_workspace_frontdoor_study_runtime_graph"
    )
    assert len(payload["family_orchestration"]["action_graph"]["nodes"]) == 4
    assert len(payload["family_orchestration"]["action_graph"]["edges"]) == 5
    assert payload["family_orchestration"]["resume_contract"]["surface_kind"] == "launch_study"
    assert payload["family_orchestration"]["human_gates"][0]["gate_id"] == "study_physician_decision_gate"
    assert payload["product_entry_manifest"]["frontdesk_surface"]["shell_key"] == "product_frontdesk"
    assert payload["product_entry_manifest"]["manifest_version"] == 2
    assert payload["product_entry_manifest"]["product_entry_readiness"] == payload["product_entry_readiness"]
    assert payload["product_entry_manifest"]["product_entry_preflight"] == payload["product_entry_preflight"]
    assert payload["product_entry_manifest"]["product_entry_start"] == payload["product_entry_start"]
    assert payload["product_entry_manifest"]["product_entry_guardrails"] == payload["product_entry_guardrails"]
    assert payload["product_entry_manifest"]["capability_owner_boundary"]["owner"] == "MedAutoScience"
    assert payload["product_entry_manifest"]["phase3_clearance_lane"] == payload["phase3_clearance_lane"]
    assert payload["product_entry_manifest"]["phase4_backend_deconstruction"] == payload["phase4_backend_deconstruction"]
    assert payload["product_entry_manifest"]["phase5_platform_target"] == payload["phase5_platform_target"]
    assert payload["product_entry_manifest"]["runtime_inventory"] == payload["runtime_inventory"]
    assert payload["product_entry_manifest"]["task_lifecycle"] == payload["task_lifecycle"]
    assert payload["product_entry_manifest"]["skill_catalog"] == payload["skill_catalog"]
    assert payload["product_entry_manifest"]["automation"] == payload["automation"]

    markdown = module.render_product_frontdesk_markdown(payload)
    assert "Now" in markdown
    assert "Single-Project Boundary" in markdown
    assert "Capability Owner Boundary" in markdown
    assert "MAS capability `progress_truth_projection`" in markdown
    assert "MDS migration-only `upstream_intake_buffer`" in markdown
    assert "MDS 保留 `research_backend`" in markdown
    assert "Single Path" in markdown
    assert "Workspace Preview" in markdown


def test_validate_single_project_boundary_fails_closed_on_missing_roles() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    with pytest.raises(ValueError, match="mds_retained_roles 不能为空"):
        module._validate_single_project_boundary(
            {
                "surface_kind": "single_project_boundary",
                "summary": "summary",
                "mas_owner_modules": ["controller_charter"],
                "mds_retained_roles": [],
                "post_gate_only": ["physical monorepo absorb"],
                "not_now": ["treating MedDeepScientist as a second long-term owner"],
            },
            context="test.single_project_boundary",
        )


def test_validate_single_project_boundary_fails_closed_on_missing_not_now() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    with pytest.raises(ValueError, match="not_now 不能为空"):
        module._validate_single_project_boundary(
            {
                "surface_kind": "single_project_boundary",
                "summary": "summary",
                "mas_owner_modules": ["controller_charter"],
                "mds_retained_roles": [
                    {
                        "role_id": "research_backend",
                        "title": "Controlled research backend",
                        "summary": "summary",
                    }
                ],
                "post_gate_only": ["physical monorepo absorb"],
                "not_now": [],
            },
            context="test.single_project_boundary",
        )


def test_render_product_frontdesk_markdown_shows_autonomy_contract_preview() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前需要优先恢复托管运行",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "operator_status_card": {
                        "handling_state": "runtime_recovering",
                    },
                    "autonomy_contract": {
                        "summary": "恢复点已冻结；当前停在 resume_from_checkpoint，下一次确认看恢复信号。",
                        "restore_point": {
                            "summary": "当前恢复点采用 resume_from_checkpoint；最近一次续跑原因是运行停在未变化的定稿总结态。",
                        },
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert "恢复点已冻结；当前停在 resume_from_checkpoint，下一次确认看恢复信号。" in markdown
    assert "当前恢复点采用 resume_from_checkpoint；最近一次续跑原因是运行停在未变化的定稿总结态。" in markdown
    assert "Phase 2 User Loop" in markdown
    assert "Guardrails" in markdown
    assert "workspace_supervision_gap" in markdown
    assert "Phase 3 Clearance" in markdown
    assert "推荐动作" in markdown
    assert "清障步骤 `refresh_supervision`" in markdown
    assert "external_runtime_contract" in markdown
    assert "Phase 4 Deconstruction" in markdown
    assert "session_run_watch_recovery" in markdown
    assert "Platform Target" in markdown
    assert "Monorepo Sequence" in markdown
    assert "stabilize_user_product_loop" in markdown
    assert "post_gate_target" in markdown
    assert "summary:" not in markdown


def test_render_product_frontdesk_markdown_shows_quality_closure_preview() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前已进入同线定稿与投稿包收尾",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "quality_closure_truth": {
                        "summary": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert "质量闭环: 核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。" in markdown


def test_render_product_frontdesk_markdown_shows_quality_execution_lane_preview() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前先做 claim-evidence 修复",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "quality_execution_lane": {
                        "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“哪一轮最小补充分析足以恢复当前 claim-evidence 支撑？”。",
                    },
                    "quality_review_loop": {
                        "current_phase_label": "等待复评",
                        "recommended_next_phase_label": "发起复评",
                        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert "质量执行线: 当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“哪一轮最小补充分析足以恢复当前 claim-evidence 支撑？”。" in markdown


def test_render_product_frontdesk_markdown_shows_same_line_route_truth_preview() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前已进入同线定稿与投稿包收尾",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "same_line_route_truth": {
                        "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert "同线路由: 当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。" in markdown


def test_render_product_frontdesk_markdown_shows_autonomy_soak_and_quality_followthrough_preview() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前处在等待系统自动复评",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "autonomy_soak_status": {
                        "summary": "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。",
                    },
                    "quality_review_loop": {
                        "current_phase_label": "等待复评",
                        "recommended_next_phase_label": "发起复评",
                        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                    },
                    "quality_review_followthrough": {
                        "state_label": "等待复评",
                        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review。",
                        "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert "自治 Proof / Soak: 最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。" in markdown
    assert "质量复评跟进: 等待复评；当前修订计划已完成，下一步应由 MAS 发起 re-review。；看 publication_eval/latest.json 是否出现新的复评结论。" in markdown
    assert (
        "质量评审闭环: 等待复评 -> 发起复评；当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。"
        in markdown
    )


def test_render_product_frontdesk_markdown_shows_gate_clearing_followthrough_preview() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前进入 gate-clearing followthrough",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "gate_clearing_followthrough": {
                        "state_label": "等待 gate replay",
                        "summary": "当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。",
                        "next_confirmation_signal": "看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert (
        "gate-clearing 跟进: 等待 gate replay；当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。；看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。"
        in markdown
    )


def test_render_product_frontdesk_markdown_shows_quality_repair_followthrough_preview() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前进入 quality-repair followthrough",
                    "recommended_command": "uv run python -m med_autoscience.cli study quality-repair-batch --study-id 001-risk",
                    "quality_repair_followthrough": {
                        "state_label": "等待 quality gate replay",
                        "summary": "当前已按 quality-repair batch 回放 deterministic 修复，正在等待新的 publication eval 结论。",
                        "next_confirmation_signal": "看 publication_eval/latest.json 是否继续收窄 quality blocker。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert (
        "quality-repair 跟进: 等待 quality gate replay；当前已按 quality-repair batch 回放 deterministic 修复，正在等待新的 publication eval 结论。；看 publication_eval/latest.json 是否继续收窄 quality blocker。"
        in markdown
    )


def test_product_entry_manifest_fails_closed_on_invalid_gateway_interaction_contract_shape(
    monkeypatch,
    tmp_path: Path,
) -> None:
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
        module,
        "_build_gateway_interaction_contract",
        lambda: {
            "surface_kind": "gateway_interaction_contract",
            "frontdoor_owner": "",
        },
    )

    with pytest.raises(ValueError, match="gateway_interaction_contract"):
        module.build_product_entry_manifest(
            profile=profile,
            profile_ref=profile_ref,
        )


def test_startup_contract_appends_latest_task_intake_context(monkeypatch, tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    startup_module = importlib.import_module("med_autoscience.controllers.study_runtime_startup")
    resolution_module = importlib.import_module("med_autoscience.controllers.study_runtime_resolution")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="优先发现并修复卡住、无进度、figure 质量坏循环等系统性问题。",
        constraints=("先保 runtime supervision truth",),
    )

    monkeypatch.setattr(
        startup_module.startup_boundary_gate_controller,
        "evaluate_startup_boundary",
        lambda **kwargs: {
            "allow_compute_stage": False,
            "required_first_anchor": "scout",
            "effective_custom_profile": "startup_boundary_blocked",
            "legacy_code_execution_allowed": False,
            "missing_requirements": ["paper_framing"],
        },
    )
    monkeypatch.setattr(
        startup_module.runtime_reentry_gate_controller,
        "evaluate_runtime_reentry",
        lambda **kwargs: {"allow_runtime_entry": True},
    )
    monkeypatch.setattr(
        startup_module.journal_shortlist_controller,
        "resolve_journal_shortlist",
        lambda **kwargs: {"status": "not_started", "shortlist": [], "candidate_count": 0, "uncovered_shortlist_entries": []},
    )
    monkeypatch.setattr(
        startup_module.medical_analysis_contract_controller,
        "resolve_medical_analysis_contract_for_study",
        lambda **kwargs: {"status": "resolved"},
    )
    monkeypatch.setattr(
        startup_module.medical_reporting_contract_controller,
        "resolve_medical_reporting_contract_for_study",
        lambda **kwargs: {"status": "resolved", "reporting_guideline_family": "TRIPOD"},
    )

    payload = startup_module._build_startup_contract(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        study_payload=resolution_module._load_yaml_dict(study_root / "study.yaml"),
        execution={"startup_contract_profile": "paper_required_autonomous", "launch_profile": "continue_existing_state"},
    )

    assert payload["task_intake_ref"]["study_id"] == "001-risk"
    assert "figure 质量坏循环" in payload["custom_brief"]


def test_submit_study_task_enqueues_task_context_for_live_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')

    class FakeBackend:
        BACKEND_ID = "fake"
        ENGINE_ID = "fake-engine"

        def chat_quest(
            self,
            *,
            runtime_root: Path,
            quest_id: str,
            text: str,
            source: str,
            reply_to_interaction_id: str | None = None,
            decision_response: dict[str, object] | None = None,
        ) -> dict[str, object]:
            assert runtime_root == profile.managed_runtime_home
            assert quest_id == "001-risk"
            assert source == "codex-study-task-intake"
            assert reply_to_interaction_id is None
            assert decision_response is None
            assert "优先清理 publication gate 文面阻塞" in text
            assert "不要继续泛化分析" in text
            assert "只使用现有证据" in text
            return {"ok": True, "message": {"id": "msg-formal-001"}}

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: FakeBackend())
    monkeypatch.setattr(
        product_entry.user_message,
        "enqueue_user_message",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("formal live submit should not fall back to queue")),
    )

    result = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="优先清理 publication gate 文面阻塞。",
        constraints=("不要继续泛化分析",),
        evidence_boundary=("只使用现有证据",),
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    runtime_intervention = result["runtime_intervention"]

    assert runtime_intervention["intervention_enqueued"] is True
    assert runtime_intervention["quest_status"] == "running"
    assert runtime_intervention["message_id"] == "msg-formal-001"
    assert runtime_intervention["reason"] == "live_runtime_task_context_submitted"
    assert queue["pending"] == []
    assert runtime_state["pending_user_message_count"] == 0


def test_submit_study_task_uses_managed_quest_id_for_live_runtime_intervention(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk", quest_id="001-risk-managed")
    short_quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    managed_quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk-managed"
    write_text(managed_quest_root / "quest.yaml", "id: 001-risk-managed\n")
    write_text(
        managed_quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk-managed",
                "status": "running",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(managed_quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')

    class FakeBackend:
        BACKEND_ID = "fake"
        ENGINE_ID = "fake-engine"

        def chat_quest(
            self,
            *,
            runtime_root: Path,
            quest_id: str,
            text: str,
            source: str,
            reply_to_interaction_id: str | None = None,
            decision_response: dict[str, object] | None = None,
        ) -> dict[str, object]:
            assert runtime_root == profile.managed_runtime_home
            assert quest_id == "001-risk-managed"
            assert source == "codex-study-task-intake"
            assert "根据审稿意见修订 manuscript" in text
            return {"ok": True, "message": {"id": "msg-managed-quest"}}

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: FakeBackend())

    result = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="根据审稿意见修订 manuscript。",
    )

    runtime_intervention = result["runtime_intervention"]
    assert not short_quest_root.exists()
    assert runtime_intervention["quest_id"] == "001-risk-managed"
    assert runtime_intervention["quest_root"] == str(managed_quest_root)
    assert runtime_intervention["intervention_enqueued"] is True
    assert runtime_intervention["message_id"] == "msg-managed-quest"
    assert runtime_intervention["reason"] == "live_runtime_task_context_submitted"


def test_submit_study_task_falls_back_to_durable_queue_when_backend_chat_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    runtime_backend = importlib.import_module("med_autoscience.runtime_backend")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "active_interaction_id": "progress-1",
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / ".ds" / "user_message_queue.json", '{"version": 1, "pending": [], "completed": []}\n')

    monkeypatch.setattr(runtime_backend, "resolve_managed_runtime_backend", lambda execution: None)

    result = product_entry.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="优先比较不同省份的生物制剂使用意向。",
        constraints=("保留多中心分层分析",),
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    runtime_intervention = result["runtime_intervention"]

    assert runtime_intervention["intervention_enqueued"] is True
    assert runtime_intervention["delivery_mode"] == "durable_queue_fallback"
    assert runtime_intervention["reason"] == "live_runtime_task_context_enqueued_fallback"
    assert len(queue["pending"]) == 1
    assert "优先比较不同省份的生物制剂使用意向" in queue["pending"][0]["content"]
    assert "保留多中心分层分析" in queue["pending"][0]["content"]
    assert runtime_state["pending_user_message_count"] == 1


def test_build_product_entry_preflight_uses_shared_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile_ref = tmp_path / "profile.local.toml"
    doctor_report = SimpleNamespace(
        workspace_exists=True,
        runtime_exists=True,
        studies_exists=True,
        portfolio_exists=True,
        med_deepscientist_runtime_exists=True,
        medical_overlay_ready=True,
        external_runtime_contract={"ready": True},
        workspace_supervision_contract={"loaded": True},
    )
    captured: dict[str, object] = {}

    def _fake_build_preflight(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "product_entry_preflight", "checks": list(kwargs["checks"])}

    monkeypatch.setattr(module, "_build_shared_product_entry_preflight", _fake_build_preflight)

    payload = module._build_product_entry_preflight(doctor_report=doctor_report, profile_ref=profile_ref)

    assert payload["surface_kind"] == "product_entry_preflight"
    assert len(captured["checks"]) == 8
    assert str(captured["recommended_check_command"]).endswith("doctor --profile " + str(profile_ref.resolve()))
    assert str(captured["recommended_start_command"]).endswith(
        "product-frontdesk --profile " + str(profile_ref.resolve())
    )


def test_build_product_entry_guardrails_uses_shared_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}

    def _fake_build_guardrails(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "surface_kind": "product_entry_guardrails",
            "guardrail_classes": list(kwargs["guardrail_classes"]),
            "recovery_loop": list(kwargs["recovery_loop"]),
        }

    monkeypatch.setattr(module, "_build_shared_product_entry_guardrails", _fake_build_guardrails)

    payload = module._build_product_entry_guardrails(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "product_entry_guardrails"
    assert len(captured["guardrail_classes"]) == 5
    assert len(captured["recovery_loop"]) == 4


def test_build_phase3_clearance_lane_uses_shared_builder(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}

    def _fake_build_lane(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase3_host_clearance_lane", "proof_surfaces": list(kwargs["proof_surfaces"])}

    monkeypatch.setattr(module, "_build_shared_clearance_lane", _fake_build_lane)

    payload = module._build_phase3_clearance_lane(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "phase3_host_clearance_lane"
    assert str(captured["recommended_command"]).endswith("doctor --profile " + str(profile_ref.resolve()))
    assert len(captured["clearance_targets"]) == 3
    assert len(captured["clearance_loop"]) == 6
    assert len(captured["proof_surfaces"]) == 5


def test_build_phase4_backend_deconstruction_uses_shared_builder(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    captured: dict[str, object] = {}

    def _fake_build_lane(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase4_backend_deconstruction_lane", "substrate_targets": list(kwargs["substrate_targets"])}

    monkeypatch.setattr(module, "_build_shared_backend_deconstruction_lane", _fake_build_lane)

    payload = module._build_phase4_backend_deconstruction()

    assert payload["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert len(captured["substrate_targets"]) == 2
    assert captured["deconstruction_map_doc"] == "docs/program/med_deepscientist_deconstruction_map.md"


def test_build_phase5_platform_target_uses_shared_builder(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    captured: dict[str, object] = {}

    def _fake_build_platform(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase5_platform_target", "landing_sequence": list(kwargs["landing_sequence"])}

    monkeypatch.setattr(module, "_build_shared_platform_target", _fake_build_platform)

    payload = module._build_phase5_platform_target()

    assert payload["surface_kind"] == "phase5_platform_target"
    assert captured["sequence_scope"] == "monorepo_landing_readiness"
    assert len(captured["landing_sequence"]) == 5


def test_build_product_entry_manifest_uses_shared_family_product_entry_orchestration(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}

    def _fake_build_family_product_entry_orchestration(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "action_graph_ref": {
                "ref_kind": "json_pointer",
                "ref": "/family_orchestration/action_graph",
                "label": "mas family action graph",
            },
            "version": "family-action-graph.v1",
            "action_graph": {
                "graph_id": str(kwargs["graph_id"]),
                "target_domain_id": str(kwargs["target_domain_id"]),
                "graph_kind": str(kwargs["graph_kind"]),
                "graph_version": str(kwargs["graph_version"]),
                "nodes": list(kwargs["nodes"]),
                "edges": list(kwargs["edges"]),
                "entry_nodes": list(kwargs["entry_nodes"]),
                "exit_nodes": list(kwargs["exit_nodes"]),
                "human_gates": list(kwargs["human_gates"]),
                "checkpoint_policy": {
                    "mode": "explicit_nodes",
                    "checkpoint_nodes": list(kwargs["checkpoint_nodes"]),
                },
            },
            "human_gates": list(kwargs["human_gate_previews"]),
            "resume_contract": {
                "surface_kind": str(kwargs["resume_surface_kind"]),
                "session_locator_field": str(kwargs["session_locator_field"]),
                "checkpoint_locator_field": str(kwargs["checkpoint_locator_field"]),
            },
            "event_envelope_surface": dict(kwargs["event_envelope_surface"]),
            "checkpoint_lineage_surface": dict(kwargs["checkpoint_lineage_surface"]),
        }

    monkeypatch.setattr(
        module,
        "_build_shared_family_product_entry_orchestration",
        _fake_build_family_product_entry_orchestration,
    )

    payload = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)

    assert payload["family_orchestration"]["action_graph"]["graph_id"] == "mas_workspace_frontdoor_study_runtime_graph"
    assert captured["graph_kind"] == "study_runtime_orchestration"
    assert [node["node_id"] for node in captured["nodes"]] == [
        "step:open_frontdesk",
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert [edge["on"] for edge in captured["edges"]] == [
        "new_task",
        "resume_study",
        "inspect_status",
        "task_written",
        "progress_refresh",
    ]
    assert captured["entry_nodes"] == ["step:open_frontdesk"]
    assert captured["exit_nodes"] == ["step:continue_study", "step:inspect_progress"]
    assert captured["checkpoint_nodes"] == [
        "step:submit_task",
        "step:continue_study",
        "step:inspect_progress",
    ]
    assert [gate["gate_id"] for gate in captured["human_gate_previews"]] == [
        "study_physician_decision_gate",
        "publication_release_gate",
    ]


def test_render_product_frontdesk_markdown_shows_auto_re_review_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "workspace_preview": None,
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前处在等待系统自动复评",
                    "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                    "operator_status_card": {
                        "handling_state": "monitor_only",
                        "user_visible_verdict": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
                        "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
                    },
                    "quality_review_loop": {
                        "current_phase_label": "等待复评",
                        "recommended_next_phase_label": "发起复评",
                        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                    },
                }
            ],
            "phase2_user_product_loop": {},
            "product_entry_guardrails": {},
            "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
            "phase4_backend_deconstruction": {"substrate_targets": []},
            "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
            "remaining_gaps": [],
        }
    )

    assert "当前处理结论: 当前在等系统自动复评；你现在不用介入，先等待复评回写。" in markdown
    assert "下一确认信号: 看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。" in markdown
    assert "质量评审闭环: 等待复评 -> 发起复评；当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。" in markdown


def test_build_skill_catalog_projects_recommended_shell_and_direct_activation_hints(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_text(
        profile.workspace_root / "contracts" / "runtime-program" / "current-program.json",
        json.dumps(
            {
                "schema_version": 1,
                "program_id": "research-foundry-medical-mainline",
                "title": "Medical Research Mainline",
                "current_phase_id": "phase_2_user_product_loop",
                "phases": [
                    {
                        "phase_id": "phase_2_user_product_loop",
                        "label": "Phase 2",
                        "status": "active",
                        "summary": "继续收口 blocker 并把用户入口壳压实。",
                        "exit_criteria": ["todo"],
                    }
                ],
                "active_tranche_id": "f4_blocker_closeout",
            },
            ensure_ascii=False,
        ),
    )
    write_study(profile.workspace_root, "001-risk")

    payload = module.build_skill_catalog(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "skill_catalog"
    assert payload["recommended_shell"] == "workspace_cockpit"
    assert payload["recommended_command"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["manifest_command"].endswith(
        "product-entry-manifest --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["skills"][0]["domain_projection"]["skill_entry"] == "mas"
    assert payload["skills"][0]["domain_projection"]["recommended_shell"] == "workspace_cockpit"
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
