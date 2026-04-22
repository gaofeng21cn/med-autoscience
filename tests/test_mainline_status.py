from __future__ import annotations

import importlib


def test_mainline_status_projects_ideal_state_current_stage_and_gaps() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    payload = module.read_mainline_status()

    assert payload["program_id"] == "research-foundry-medical-mainline"
    assert payload["current_stage"]["id"] == "mas_owner_truth_hardening"
    assert payload["current_stage"]["status"] == "in_progress"
    assert "F4 blocker" not in payload["current_stage"]["title"]
    assert "F4 blocker" not in payload["current_stage"]["summary"]
    assert payload["active_tranche_owner_truth"]["surface_kind"] == "active_tranche_owner_truth"
    assert [item["lane_id"] for item in payload["active_tranche_owner_truth"]["lanes"]] == [
        "autonomy",
        "quality",
        "single_project_owner",
    ]
    assert payload["active_tranche_owner_truth"]["owner"] == "MedAutoScience"
    assert [item["role_id"] for item in payload["active_tranche_owner_truth"]["mds_retained_roles"]] == [
        "research_backend",
        "behavior_equivalence_oracle",
        "upstream_intake_buffer",
    ]
    assert all(item["owner"].startswith("MAS") for item in payload["active_tranche_owner_truth"]["lanes"])
    assert payload["ideal_state"]["runtime_topology"]["outer_runtime_substrate_owner"] == "upstream Hermes-Agent"
    assert payload["ideal_state"]["runtime_topology"]["research_backend"] == "MedDeepScientist (controlled backend)"
    assert payload["single_project_boundary"]["surface_kind"] == "single_project_boundary"
    assert payload["single_project_boundary"]["mas_owner_modules"] == [
        "controller_charter",
        "runtime",
        "eval_hygiene",
    ]
    assert [item["role_id"] for item in payload["single_project_boundary"]["mds_retained_roles"]] == [
        "research_backend",
        "behavior_equivalence_oracle",
        "upstream_intake_buffer",
    ]
    assert "physical monorepo absorb" in payload["single_project_boundary"]["post_gate_only"]
    assert payload["current_program_phase"]["id"] == "phase_1_mainline_established"
    assert payload["current_program_phase"]["status"] == "in_progress"
    assert payload["current_program_phase"]["single_project_boundary"]["land_now"] == [
        "MAS 单项目 owner wording and repo-tracked truth",
        "docs/status/program/mainline boundary alignment",
        "user-visible wording that MDS is no longer a second long-term owner",
    ]
    assert [item["role_id"] for item in payload["current_program_phase"]["single_project_boundary"]["mds_retained_roles"]] == [
        "research_backend",
        "behavior_equivalence_oracle",
        "upstream_intake_buffer",
    ]
    assert "physical monorepo absorb" in payload["current_program_phase"]["single_project_boundary"]["post_gate_only"]
    assert len(payload["phase_ladder"]) == 5
    assert payload["phase_ladder"][1]["id"] == "phase_2_user_product_loop"
    assert payload["phase_ladder"][0]["usable_now"] is True
    assert [item["lane_id"] for item in payload["phase_ladder"][0]["active_tranche_owner_truth"]["lanes"]] == [
        "autonomy",
        "quality",
        "single_project_owner",
    ]
    assert payload["phase_ladder"][0]["single_project_boundary"]["mas_owner_modules"] == [
        "controller_charter",
        "runtime",
        "eval_hygiene",
    ]
    assert payload["phase2_user_product_loop"]["surface_kind"] == "phase2_user_product_loop_lane"
    assert payload["phase2_user_product_loop"]["recommended_step_id"] == "open_frontdesk"
    assert payload["phase2_user_product_loop"]["recommended_command"] == (
        "uv run python -m med_autoscience.cli product-frontdesk --profile <profile>"
    )
    assert payload["phase2_user_product_loop"]["single_path"][0]["step_id"] == "open_frontdesk"
    assert payload["phase2_user_product_loop"]["single_path"][3]["step_id"] == "continue_study"
    assert payload["phase2_user_product_loop"]["single_path"][5]["step_id"] == "handle_human_gate"
    assert payload["phase2_user_product_loop"]["proof_surfaces"] == [
        {
            "surface_kind": "product_frontdesk",
            "command": "uv run python -m med_autoscience.cli product-frontdesk --profile <profile>",
        },
        {
            "surface_kind": "workspace_cockpit",
            "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>",
        },
        {
            "surface_kind": "study_progress.operator_verdict",
            "command": (
                "uv run python -m med_autoscience.cli study-progress --profile <profile> "
                "--study-id <study_id>"
            ),
        },
        {
            "surface_kind": "study_progress.recovery_contract",
            "command": (
                "uv run python -m med_autoscience.cli study-progress --profile <profile> "
                "--study-id <study_id>"
            ),
        },
        {
            "surface_kind": "controller_decisions",
            "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        },
    ]
    assert payload["phase3_clearance_lane"]["surface_kind"] == "phase3_host_clearance_lane"
    assert payload["phase3_clearance_lane"]["recommended_step_id"] == "external_runtime_contract"
    assert payload["phase3_clearance_lane"]["recommended_command"] == (
        "uv run python -m med_autoscience.cli doctor --profile <profile>"
    )
    assert payload["phase3_clearance_lane"]["clearance_targets"][0]["target_id"] == "external_runtime_contract"
    assert payload["phase3_clearance_lane"]["proof_surfaces"] == [
        {
            "surface_kind": "doctor.external_runtime_contract",
            "command": "uv run python -m med_autoscience.cli doctor --profile <profile>",
        },
        {
            "surface_kind": "study_runtime_status.autonomous_runtime_notice",
            "command": (
                "uv run python -m med_autoscience.cli study-runtime-status --profile <profile> "
                "--study-id <study_id>"
            ),
        },
        {
            "surface_kind": "runtime_watch",
            "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
        },
        {
            "surface_kind": "runtime_supervision",
            "ref": "studies/<study_id>/artifacts/runtime_supervision/latest.json",
        },
        {
            "surface_kind": "controller_decisions",
            "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        },
    ]
    assert payload["phase3_clearance_lane"]["clearance_loop"][0]["step_id"] == "external_runtime_contract"
    assert payload["phase3_clearance_lane"]["clearance_loop"][3]["step_id"] == "refresh_supervision"
    assert payload["phase4_backend_deconstruction"]["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert payload["phase4_backend_deconstruction"]["substrate_targets"][0]["capability_id"] == "session_run_watch_recovery"
    assert payload["phase4_backend_deconstruction"]["deconstruction_map_doc"] == (
        "docs/program/med_deepscientist_deconstruction_map.md"
    )
    assert payload["platform_target"]["surface_kind"] == "phase5_platform_target"
    assert payload["platform_target"]["sequence_scope"] == "monorepo_landing_readiness"
    assert payload["platform_target"]["current_step_id"] == "stabilize_user_product_loop"
    assert payload["platform_target"]["completed_step_ids"] == ["freeze_gateway_runtime_truth"]
    assert payload["platform_target"]["landing_sequence"][0]["status"] == "completed"
    assert payload["platform_target"]["landing_sequence"][1]["status"] == "in_progress"
    assert payload["platform_target"]["landing_sequence"][-1]["status"] == "blocked_post_gate"
    assert payload["platform_target"]["target_internal_modules"] == [
        "controller_charter",
        "runtime",
        "eval_hygiene",
    ]
    assert payload["platform_target"]["north_star_topology"]["monorepo_status"] == "post_gate_target"
    assert payload["platform_target"]["promotion_gates"] == [
        "phase_1_mainline_established",
        "phase_2_user_product_loop",
        "phase_3_multi_workspace_host_clearance",
        "phase_4_backend_deconstruction",
    ]
    assert payload["source_docs"] == [
        "README.md",
        "docs/README.md",
        "docs/project.md",
        "docs/architecture.md",
        "docs/status.md",
        "docs/runtime/agent_runtime_interface.md",
        "docs/references/lightweight_product_entry_and_opl_handoff.md",
    ]
    assert payload["phase_ladder"][0]["phase_docs"] == [
        "docs/status.md",
        "docs/project.md",
        "docs/architecture.md",
    ]
    assert payload["phase_ladder"][1]["phase_docs"] == [
        "docs/README.md",
        "docs/runtime/agent_runtime_interface.md",
        "docs/references/lightweight_product_entry_and_opl_handoff.md",
    ]
    assert any(item["name"] == "workspace_cockpit" for item in payload["phase_ladder"][1]["entry_points"])
    assert any(item["id"] == "f3_real_study_soak_recovery_proof" for item in payload["completed_tranches"])
    assert any("standalone" in item for item in payload["remaining_gaps"])
    assert any("autonomy" in item for item in payload["next_focus"])
    assert any("quality" in item for item in payload["next_focus"])
    assert any("single-project owner" in item for item in payload["next_focus"])
    assert all("F4 blocker" not in item for item in payload["next_focus"])
    assert any("physical migration" in item for item in payload["explicitly_not_now"])
    assert any("second long-term owner" in item for item in payload["explicitly_not_now"])


def test_render_mainline_status_markdown_surfaces_stage_and_next_focus() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    markdown = module.render_mainline_status_markdown(module.read_mainline_status())

    assert "# Mainline Status" in markdown
    assert "当前 program" in markdown
    assert "当前主线阶段" in markdown
    assert "当前判断" in markdown
    assert "理想目标" in markdown
    assert "Active Tranche Owner Truth" in markdown
    assert "owner lane `autonomy`" in markdown
    assert "owner lane `quality`" in markdown
    assert "owner lane `single_project_owner`" in markdown
    assert "Single-Project Boundary" in markdown
    assert "MDS retained `research_backend`" in markdown
    assert "post-gate only: physical monorepo absorb" in markdown
    assert "Program Phases" in markdown
    assert "phase_1_mainline_established" in markdown
    assert "Phase 2 User Loop" in markdown
    assert "单一路径 `continue_study`" in markdown
    assert "推荐动作" in markdown
    assert "推荐命令" in markdown
    assert "Platform Target" in markdown
    assert "Monorepo Sequence" in markdown
    assert "stabilize_user_product_loop" in markdown
    assert "Phase 3 Clearance" in markdown
    assert "清障重点" in markdown
    assert "清障步骤 `refresh_supervision`" in markdown
    assert "Phase 4 Deconstruction" in markdown
    assert "Remaining Gaps" in markdown
    assert "Next Focus" in markdown
    assert "docs/README.md" in markdown
    assert "docs/runtime/agent_runtime_interface.md" in markdown
    assert "docs/program/research_foundry_medical_mainline.md" not in markdown
    assert "docs/references/research_foundry_medical_phase_ladder.md" not in markdown
    assert "program_id:" not in markdown
    assert "domain_gateway:" not in markdown
    assert "outer_runtime_substrate_owner:" not in markdown
    assert "entry_shape:" not in markdown
    assert "surface_kind:" not in markdown
    assert "sequence_scope:" not in markdown
    assert "monorepo_status:" not in markdown
    assert "F4 blocker" not in markdown


def test_mainline_phase_status_resolves_current_and_next_phase() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    current_payload = module.read_mainline_phase_status("current")
    next_payload = module.read_mainline_phase_status("next")

    assert current_payload["phase"]["id"] == "phase_1_mainline_established"
    assert current_payload["phase"]["usable_now"] is True
    assert [item["lane_id"] for item in current_payload["phase"]["active_tranche_owner_truth"]["lanes"]] == [
        "autonomy",
        "quality",
        "single_project_owner",
    ]
    assert current_payload["phase"]["single_project_boundary"]["land_now"] == [
        "MAS 单项目 owner wording and repo-tracked truth",
        "docs/status/program/mainline boundary alignment",
        "user-visible wording that MDS is no longer a second long-term owner",
    ]
    assert [item["role_id"] for item in current_payload["phase"]["single_project_boundary"]["mds_retained_roles"]] == [
        "research_backend",
        "behavior_equivalence_oracle",
        "upstream_intake_buffer",
    ]
    assert "physical monorepo absorb" in current_payload["phase"]["single_project_boundary"]["post_gate_only"]
    assert any(item["name"] == "mainline_status" for item in current_payload["phase"]["entry_points"])
    assert next_payload["phase"]["id"] == "phase_2_user_product_loop"
    assert any("workspace-cockpit" in item["command"] for item in next_payload["phase"]["entry_points"])


def test_render_mainline_phase_markdown_surfaces_entry_points_and_exit_criteria() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    markdown = module.render_mainline_phase_markdown(module.read_mainline_phase_status("phase_2_user_product_loop"))

    assert "# Mainline Phase" in markdown
    assert "当前阶段" in markdown
    assert "当前状态" in markdown
    assert "当前可用性" in markdown
    assert "当前摘要" in markdown
    assert "可用入口" in markdown
    assert "退出条件" in markdown
    assert "相关文档" in markdown
    assert "docs/runtime/agent_runtime_interface.md" in markdown
    assert "docs/references/research_foundry_medical_phase_ladder.md" not in markdown
    assert "phase_id:" not in markdown
    assert "phase_status:" not in markdown
    assert "usable_now:" not in markdown
    assert "summary:" not in markdown
    assert "purpose:" not in markdown


def test_render_mainline_phase_markdown_surfaces_current_tranche_boundary() -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")

    markdown = module.render_mainline_phase_markdown(module.read_mainline_phase_status("current"))

    assert "当前 tranche 边界" in markdown
    assert "Owner Truth Lanes" in markdown
    assert "owner lane `autonomy`" in markdown
    assert "owner lane `quality`" in markdown
    assert "owner lane `single_project_owner`" in markdown
    assert "当前 tranche 收口: MAS 单项目 owner wording and repo-tracked truth" in markdown
    assert "MDS 保留 `research_backend`" in markdown
    assert "post-gate only: physical monorepo absorb" in markdown
    assert "F4 blocker" not in markdown


def test_phase3_clearance_lane_uses_shared_builder(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")
    captured: dict[str, object] = {}

    monkeypatch.setattr(module, "_build_shared_clearance_target", lambda **kwargs: kwargs, raising=False)
    monkeypatch.setattr(module, "_build_shared_product_entry_program_step", lambda **kwargs: kwargs, raising=False)
    monkeypatch.setattr(module, "_build_shared_product_entry_program_surface", lambda **kwargs: kwargs, raising=False)

    def _fake_build_clearance_lane(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase3_host_clearance_lane"}

    monkeypatch.setattr(module, "_build_shared_clearance_lane", _fake_build_clearance_lane, raising=False)

    payload = module._phase3_clearance_lane()

    assert payload["surface_kind"] == "phase3_host_clearance_lane"
    assert captured["recommended_step_id"] == "external_runtime_contract"
    assert len(captured["clearance_targets"]) == 3
    assert len(captured["proof_surfaces"]) == 5


def test_phase4_backend_deconstruction_uses_shared_builder(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")
    captured: dict[str, object] = {}

    monkeypatch.setattr(module, "_build_shared_program_capability", lambda **kwargs: kwargs, raising=False)

    def _fake_build_backend_lane(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase4_backend_deconstruction_lane"}

    monkeypatch.setattr(module, "_build_shared_backend_deconstruction_lane", _fake_build_backend_lane, raising=False)

    payload = module._phase4_backend_deconstruction()

    assert payload["surface_kind"] == "phase4_backend_deconstruction_lane"
    assert len(captured["substrate_targets"]) == 2
    assert captured["deconstruction_map_doc"] == "docs/program/med_deepscientist_deconstruction_map.md"


def test_platform_target_uses_shared_builder(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.mainline_status")
    captured: dict[str, object] = {}

    monkeypatch.setattr(module, "_build_shared_program_sequence_step", lambda **kwargs: kwargs, raising=False)

    def _fake_build_platform_target(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"surface_kind": "phase5_platform_target", "landing_sequence": list(kwargs["landing_sequence"])}

    monkeypatch.setattr(module, "_build_shared_platform_target", _fake_build_platform_target, raising=False)

    payload = module._platform_target()

    assert payload["surface_kind"] == "phase5_platform_target"
    assert captured["sequence_scope"] == "monorepo_landing_readiness"
    assert captured["land_now"] == [
        "repo-tracked product-entry shell and family orchestration companions",
        "controller-owned runtime/progress/recovery truth",
        "CLI/MCP/controller entry surfaces that already support real work",
    ]
    assert len(captured["landing_sequence"]) == 5
