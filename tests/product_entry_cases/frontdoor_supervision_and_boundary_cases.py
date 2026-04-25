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
