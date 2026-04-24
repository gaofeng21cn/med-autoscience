from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from . import cockpit_status_and_frontdesk_focus as _cockpit_status_and_frontdesk_focus

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_cockpit_status_and_frontdesk_focus)

def test_build_product_entry_manifest_passes_contract_bundle_via_named_shared_kwargs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}

    def _fake_build_family_product_entry_manifest(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "surface_kind": "product_entry_manifest",
            "target_domain_id": "med-autoscience",
        }

    monkeypatch.setattr(
        module,
        "_build_shared_family_product_entry_manifest",
        _fake_build_family_product_entry_manifest,
    )
    monkeypatch.setattr(module, "_validate_product_entry_manifest_contract", lambda payload: None)

    payload = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "product_entry_manifest"
    assert captured["schema_ref"] == module.PRODUCT_ENTRY_MANIFEST_SCHEMA_REF
    assert captured["domain_entry_contract"] == module._build_domain_entry_contract()
    assert captured["gateway_interaction_contract"] == module._build_gateway_interaction_contract()
    assert captured["session_continuity"]["surface_kind"] == "session_continuity"
    assert captured["progress_projection"]["surface_kind"] == "progress_projection"
    assert captured["artifact_inventory"]["surface_kind"] == "artifact_inventory"
    assert "schema_ref" not in captured["extra_payload"]
    assert "domain_entry_contract" not in captured["extra_payload"]
    assert "gateway_interaction_contract" not in captured["extra_payload"]


def test_build_product_frontdesk_leaves_contract_bundle_to_shared_manifest_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    captured: dict[str, object] = {}
    manifest = {
        "surface_kind": "product_entry_manifest",
        "manifest_version": 2,
        "manifest_kind": "med_autoscience_product_entry_manifest",
        "target_domain_id": "med-autoscience",
        "formal_entry": {
            "default": "CLI",
            "supported_protocols": ["MCP"],
            "internal_surface": "controller",
        },
        "product_entry_shell": {
            "product_frontdesk": {
                "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "surface_kind": "product_frontdesk",
            },
            "workspace_cockpit": {
                "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "surface_kind": "workspace_cockpit",
            },
            "submit_study_task": {
                "command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml",
                "surface_kind": "study_task_intake",
            },
            "launch_study": {
                "command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml",
                "surface_kind": "study_runtime_status",
            },
            "study_progress": {
                "command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml",
                "surface_kind": "study_progress",
            },
            "mainline_status": {
                "command": "uv run python -m med_autoscience.cli mainline-status",
                "surface_kind": "mainline_status",
            },
            "mainline_phase": {
                "command": "uv run python -m med_autoscience.cli mainline-phase",
                "surface_kind": "mainline_phase",
            },
        },
        "shared_handoff": {
            "direct_entry_builder": {
                "command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct",
                "entry_mode": "direct",
            },
            "opl_handoff_builder": {
                "command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode opl-handoff",
                "entry_mode": "opl-handoff",
            },
        },
        "summary": {
            "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"
        },
        "product_entry_preflight": {
            "surface_kind": "product_entry_preflight",
            "summary": "preflight ready",
            "ready_to_try_now": True,
            "recommended_check_command": "uv run python -m med_autoscience.cli doctor",
            "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
            "blocking_check_ids": [],
            "checks": [],
        },
        "product_entry_quickstart": {
            "surface_kind": "product_entry_quickstart",
            "recommended_step_id": "open_frontdesk",
            "summary": "open frontdesk first",
            "steps": [],
            "resume_contract": {
                "surface_kind": "workspace_cockpit",
                "session_locator_field": "profile_name",
            },
            "human_gate_ids": ["workspace_gate"],
        },
        "domain_entry_contract": module._build_domain_entry_contract(),
        "gateway_interaction_contract": module._build_gateway_interaction_contract(),
        "runtime_inventory": {"surface_kind": "runtime_inventory"},
        "task_lifecycle": {"surface_kind": "task_lifecycle"},
        "skill_catalog": {"surface_kind": "skill_catalog"},
        "automation": {"surface_kind": "automation"},
        "phase2_user_product_loop": {"surface_kind": "product_entry_program"},
        "product_entry_guardrails": {"surface_kind": "product_entry_guardrails"},
        "phase3_clearance_lane": {"surface_kind": "phase3_clearance_lane"},
        "phase4_backend_deconstruction": {"surface_kind": "backend_deconstruction_lane"},
        "phase5_platform_target": {"surface_kind": "phase5_platform_target"},
    }

    monkeypatch.setattr(module, "build_product_entry_manifest", lambda **kwargs: manifest)
    monkeypatch.setattr(
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "ready_for_task",
                "summary": "workspace ready",
                "should_intervene_now": False,
                "focus_scope": "workspace",
                "focus_study_id": None,
                "recommended_step_id": "submit_task",
                "recommended_command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml",
            },
            "attention_queue": [],
        },
    )

    def _fake_build_family_product_frontdesk_from_manifest(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "surface_kind": "product_frontdesk",
            "target_domain_id": "med-autoscience",
        }

    monkeypatch.setattr(
        module,
        "_build_shared_family_product_frontdesk_from_manifest",
        _fake_build_family_product_frontdesk_from_manifest,
    )
    monkeypatch.setattr(module, "_validate_product_frontdesk_contract", lambda payload: None)

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "product_frontdesk"
    assert captured["schema_ref"] == module.PRODUCT_FRONTDESK_SCHEMA_REF
    assert captured["shell_aliases"] == {
        "frontdesk": "product_frontdesk",
        "cockpit": "workspace_cockpit",
        "submit_task": "submit_study_task",
        "launch_study": "launch_study",
        "study_progress": "study_progress",
        "mainline_status": "mainline_status",
        "mainline_phase": "mainline_phase",
    }
    assert captured["product_entry_manifest"]["domain_entry_contract"] == manifest["domain_entry_contract"]
    assert captured["product_entry_manifest"]["gateway_interaction_contract"] == manifest["gateway_interaction_contract"]
    assert "domain_entry_contract" not in captured["extra_payload"]
    assert "gateway_interaction_contract" not in captured["extra_payload"]


def test_render_product_frontdesk_markdown_prefers_human_facing_labels() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_product_frontdesk_markdown(
        {
            "target_domain_id": "med-autoscience",
            "schema_ref": "product_frontdesk.schema.json",
            "recommended_action": "inspect_or_prepare_research_loop",
            "gateway_interaction_contract": {
                "frontdoor_owner": "opl_gateway_or_domain_gui",
                "user_interaction_mode": "natural_language_frontdoor",
            },
            "summary": {
                "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
            },
            "operator_brief": {
                "verdict": "attention_required",
                "summary": "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。",
                "should_intervene_now": True,
                "recommended_step_id": "handle_attention_item",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk"
                ),
                "focus_study_id": "001-risk",
                "current_focus": "优先同步投稿包镜像。",
                "next_confirmation_signal": "看 delivery_manifest 和 current_package 是否被刷新。",
            },
            "product_entry_quickstart": {
                "steps": [
                    {
                        "step_id": "open_frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "summary": "先打开前台入口。",
                    }
                ]
            },
            "product_entry_overview": {
                "summary": "当前 frontdesk 已对齐 workspace truth。",
                "progress_surface": {
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"
                },
                "resume_surface": {
                    "command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml --study-id 001-risk"
                },
            },
            "product_entry_start": {
                "summary": "先进入 frontdesk，再按需要恢复当前研究 loop。",
                "resume_surface": {
                    "command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml --study-id 001-risk"
                },
            },
            "product_entry_preflight": {
                "ready_to_try_now": True,
                "recommended_check_command": "uv run python -m med_autoscience.cli doctor --profile profile.local.toml",
            },
            "workspace_operator_brief": {
                "verdict": "attention_required",
                "summary": "当前 workspace 有关注项。",
                "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
            },
            "workspace_attention_queue_preview": [
                {
                    "title": "001-risk 当前需要刷新投稿包镜像",
                    "recommended_command": (
                        "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk"
                    ),
                    "operator_status_card": {
                        "handling_state": "paper_surface_refresh_in_progress",
                        "next_confirmation_signal": "看 delivery_manifest 是否刷新。",
                    },
                }
            ],
            "phase2_user_product_loop": {
                "summary": "当前先收口用户入口与研究 loop。",
                "recommended_step_id": "continue_study",
                "recommended_command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml --study-id 001-risk",
                "single_path": [
                    {
                        "step_id": "continue_study",
                        "command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml --study-id 001-risk",
                    }
                ],
            },
            "product_entry_guardrails": {
                "guardrail_classes": [
                    {
                        "guardrail_id": "workspace_supervision_gap",
                        "recommended_command": "uv run python -m med_autoscience.cli watch --profile profile.local.toml --apply",
                    }
                ]
            },
            "phase3_clearance_lane": {
                "summary": "优先恢复监督与交付镜像。",
                "recommended_step_id": "refresh_supervision",
                "recommended_command": "uv run python -m med_autoscience.cli watch --profile profile.local.toml --apply",
                "clearance_targets": [
                    {
                        "target_id": "workspace_supervision",
                        "commands": [
                            "uv run python -m med_autoscience.cli watch --profile profile.local.toml --apply"
                        ],
                    }
                ],
                "clearance_loop": [
                    {
                        "step_id": "refresh_supervision",
                        "command": "uv run python -m med_autoscience.cli watch --profile profile.local.toml --apply",
                    }
                ],
            },
            "phase4_backend_deconstruction": {
                "substrate_targets": [
                    {
                        "capability_id": "external_runtime_contract",
                        "summary": "继续把运行时 contract 收回共享基座。",
                    }
                ]
            },
            "phase5_platform_target": {},
            "entry_surfaces": {
                "frontdesk": {
                    "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml"
                }
            },
        }
    )

    assert "当前状态: 需要处理" in markdown
    assert "当前判断: MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。" in markdown
    assert "前台入口命令" in markdown
    assert "当前 workspace 判断: 当前 workspace 有关注项。" in markdown
    assert "当前关注项: 001-risk 当前需要刷新投稿包镜像" in markdown
    assert "recommended_action" not in markdown
    assert "frontdesk_command" not in markdown
    assert "recommended_command" not in markdown
    assert "operator_loop_command" not in markdown
    assert "verdict:" not in markdown
    assert "attention:" not in markdown
    assert "attention_state:" not in markdown
    assert "attention_next_signal:" not in markdown


def test_launch_study_packages_monitoring_progress_and_commands(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "build_study_progress_projection",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": ["论文叙事或方法/结果书写面仍有硬阻塞。"],
            "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [
                {
                    "step_id": "inspect_study_progress",
                    "title": "读取当前研究进度",
                    "surface_kind": "study_progress",
                    "command": (
                        "uv run python -m med_autoscience.cli study-progress --profile "
                        + str(profile_ref.resolve())
                        + " --study-id 001-risk"
                    ),
                }
            ],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "quality_floor_blocker",
                "action_mode": "inspect_progress",
                "summary": "论文叙事或方法/结果书写面仍有硬阻塞。",
                "recommended_step_id": "inspect_study_progress",
                "steps": [
                    {
                        "step_id": "inspect_study_progress",
                        "title": "读取当前研究进度",
                        "surface_kind": "study_progress",
                        "command": (
                            "uv run python -m med_autoscience.cli study-progress --profile "
                            + str(profile_ref.resolve())
                            + " --study-id 001-risk"
                        ),
                    }
                ],
            },
            "needs_physician_decision": False,
            "supervision": {
                "browser_url": "http://127.0.0.1:20999",
                "quest_session_api_url": "http://127.0.0.1:20999/api/quests/quest-001/session",
                "active_run_id": "run-001",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "task_intake": {
                "task_intent": "优先发现卡住、无进度和 figure 质量回退，再决定是否继续自动推进。",
                "journal_target": "JAMA Network Open",
            },
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("launch_study should reuse the runtime status payload")),
    )

    payload = module.launch_study(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        entry_mode="full_research",
    )

    assert payload["study_id"] == "001-risk"
    assert payload["runtime_status"]["decision"] == "resume"
    assert payload["progress"]["supervision"]["browser_url"] == "http://127.0.0.1:20999"
    assert payload["progress"]["task_intake"]["journal_target"] == "JAMA Network Open"
    assert payload["progress"]["progress_freshness"]["status"] == "fresh"
    assert payload["progress"]["recovery_contract"]["action_mode"] == "inspect_progress"
    assert payload["commands"]["progress"].endswith("--study-id 001-risk")
    assert "workspace-cockpit" in payload["commands"]["cockpit"]

    markdown = module.render_launch_study_markdown(payload)
    assert "http://127.0.0.1:20999" in markdown
    assert "论文叙事或方法/结果书写面仍有硬阻塞。" in markdown
    assert "优先发现卡住、无进度和 figure 质量回退" in markdown
    assert "最近 12 小时内仍有明确研究推进记录" in markdown
    assert "恢复合同" in markdown


def test_launch_study_markdown_prefers_shared_human_status_narration() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    from opl_harness_shared.status_narration import build_status_narration_contract

    payload = {
        "study_id": "001-risk",
        "runtime_status": {"decision": "resume"},
        "progress": {
            "current_stage": "publication_supervision",
            "current_stage_summary": "旧版阶段摘要字段",
            "next_system_action": "旧版 next_system_action 字段",
            "current_blockers": ["当前论文交付目录与注册/合同约定不一致，需要先修正交付面。"],
            "status_narration_contract": build_status_narration_contract(
                contract_id="study-progress::001-risk",
                surface_kind="study_progress",
                stage={
                    "current_stage": "publication_supervision",
                    "recommended_next_stage": "bundle_stage_ready",
                },
                current_blockers=["当前论文交付目录与注册/合同约定不一致，需要先修正交付面。"],
                latest_update="论文主体内容已经完成，当前进入投稿打包收口。",
                next_step="优先核对 submission package 与 studies 目录中的交付面是否一致。",
            ),
            "supervision": {"browser_url": "http://127.0.0.1:20999", "active_run_id": "run-001"},
        },
        "commands": {},
    }

    markdown = module.render_launch_study_markdown(payload)

    assert "当前阶段: 论文可发表性监管" in markdown
    assert "当前判断: 当前状态：论文可发表性监管；下一阶段：投稿打包就绪；当前卡点：当前论文交付目录与注册/合同约定不一致，需要先修正交付面。" in markdown
    assert "下一步建议: 优先核对 submission package 与 studies 目录中的交付面是否一致。" in markdown
    assert "current_stage_summary:" not in markdown
    assert "next_system_action:" not in markdown


def test_launch_study_markdown_prefers_human_facing_labels() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    payload = {
        "study_id": "001-risk",
        "runtime_status": {"decision": "resume"},
        "progress": {
            "current_stage": "publication_supervision",
            "current_stage_summary": "论文可发表性监管。",
            "current_blockers": ["论文叙事或方法/结果书写面仍有硬阻塞。"],
            "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
            "supervision": {"browser_url": "http://127.0.0.1:20999", "active_run_id": "run-001"},
            "task_intake": {
                "task_intent": "优先发现卡住、无进度和 figure 质量回退，再决定是否继续自动推进。",
                "journal_target": "JAMA Network Open",
            },
            "progress_freshness": {"summary": "最近 12 小时内仍有明确研究推进记录。"},
            "recovery_contract": {"action_mode": "inspect_progress", "summary": "论文叙事仍需先修。"},
            "recommended_commands": [
                {
                    "title": "读取当前研究进度",
                    "command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk",
                }
            ],
        },
        "commands": {
            "progress": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk",
        },
    }

    markdown = module.render_launch_study_markdown(payload)

    assert "当前运行判断" in markdown
    assert "浏览器入口" in markdown
    assert "当前任务意图" in markdown
    assert "当前投稿目标" in markdown
    assert "进度信号" in markdown
    assert "恢复建议" in markdown
    assert "browser_url:" not in markdown
    assert "task_intent:" not in markdown
    assert "journal_target:" not in markdown
    assert "progress_signal:" not in markdown
    assert "action_mode:" not in markdown
    assert "summary:" not in markdown



def test_submit_study_task_writes_durable_intake_and_updates_startup_brief_block(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    startup_brief_path = profile.workspace_root / "ops" / "med-deepscientist" / "startup_briefs" / "001-risk.md"
    write_text(startup_brief_path, "# Startup brief\n\n已有人工上下文。\n")

    payload = module.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="把当前研究收口到 SCI-ready 投稿标准，并持续自检卡点与质量退化。",
        journal_target="The Lancet Digital Health",
        constraints=("始终中文汇报", "不得跳过 publication gate"),
        evidence_boundary=("必须补齐外部验证",),
        trusted_inputs=("study.yaml", "数据字典"),
        reference_papers=("PMID:12345678",),
        first_cycle_outputs=("study-progress", "runtime_watch", "publication_eval/latest.json"),
    )

    latest_json = Path(payload["artifacts"]["latest_json"])
    latest_markdown = Path(payload["artifacts"]["latest_markdown"])
    written_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    startup_brief_text = startup_brief_path.read_text(encoding="utf-8")
    latest_markdown_text = latest_markdown.read_text(encoding="utf-8")

    assert latest_json.is_file()
    assert latest_markdown.is_file()
    assert written_payload["task_intent"].startswith("把当前研究收口到 SCI-ready 投稿标准")
    assert written_payload["journal_target"] == "The Lancet Digital Health"
    assert written_payload["constraints"] == ["始终中文汇报", "不得跳过 publication gate"]
    assert "MAS_TASK_INTAKE:BEGIN" in startup_brief_text
    assert "已有人工上下文。" in startup_brief_text
    assert "当前入口模式" in latest_markdown_text
    assert "当前投稿目标" in latest_markdown_text
    assert "entry_mode:" not in latest_markdown_text
    assert "journal_target:" not in latest_markdown_text
    assert "The Lancet Digital Health" in latest_markdown_text
    assert payload["study_root"] == str(study_root)


def test_build_product_entry_reuses_latest_task_intake_and_shared_handoff_envelope(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    study_root = write_study(profile.workspace_root, "001-risk")

    task_payload = module.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="把当前研究推进到可投稿的 SCI-ready 稳态。",
        entry_mode="full_research",
        journal_target="JAMA Network Open",
        evidence_boundary=("必须保留 publication gate",),
        first_cycle_outputs=("study-progress", "runtime_watch"),
    )

    payload = module.build_product_entry(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        direct_entry_mode="opl-handoff",
    )

    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["task_intent"] == task_payload["task_intent"]
    assert payload["entry_mode"] == "opl-handoff"
    assert payload["workspace_locator"]["study_id"] == "001-risk"
    assert payload["workspace_locator"]["study_root"] == str(study_root)
    assert payload["runtime_session_contract"]["managed_entry_mode"] == "full_research"
    assert payload["runtime_session_contract"]["managed_runtime_backend_id"] == profile.managed_runtime_backend_id
    assert payload["domain_payload"]["journal_target"] == "JAMA Network Open"
    assert payload["domain_payload"]["evidence_boundary"] == ["必须保留 publication gate"]
    assert payload["return_surface_contract"]["entry_adapter"] == "MedAutoScienceDomainEntry"
    assert payload["return_surface_contract"]["default_formal_entry"] == "CLI"
    assert payload["return_surface_contract"]["supported_entry_modes"] == ["direct", "opl-handoff"]
    assert payload["return_surface_contract"]["single_project_boundary"]["surface_kind"] == "single_project_boundary"
    assert list(payload["return_surface_contract"]["single_project_boundary"]["mas_owner_modules"]) == [
        "controller_charter",
        "runtime",
        "eval_hygiene",
    ]
    assert payload["return_surface_contract"]["capability_owner_boundary"]["surface_kind"] == (
        "mas_capability_owner_boundary"
    )
    assert payload["return_surface_contract"]["capability_owner_boundary"]["owner"] == "MedAutoScience"
    assert [
        item["capability_id"]
        for item in payload["return_surface_contract"]["capability_owner_boundary"]["mas_owned_capabilities"]
    ] == [
        "research_entry",
        "study_task_intake",
        "controller_outer_loop",
        "progress_truth_projection",
        "publication_quality_gate",
        "runtime_recovery",
        "program_mainline_truth",
    ]
    assert all(
        item["migration_only"] is True
        for item in payload["return_surface_contract"]["capability_owner_boundary"]["mds_migration_only_roles"]
    )
    assert payload["return_surface_contract"]["capability_owner_boundary"]["proof_and_absorb_boundary"][
        "physical_absorb_status"
    ] == "blocked_post_gate"
    assert payload["return_surface_contract"]["study_progress_projection_contract"] == {
        "surface_kind": "study_progress_projection_contract",
        "command": (
            "uv run python -m med_autoscience.cli study-progress --profile "
            + str(profile_ref.resolve())
            + " --study-id 001-risk --format json"
        ),
        "needs_physician_decision_field": "needs_physician_decision",
        "intervention_lane_field": "intervention_lane",
        "operator_status_card_field": "operator_status_card",
        "autonomy_contract_field": "autonomy_contract",
        "restore_point_field": "autonomy_contract.restore_point",
        "human_gate_required_field": "autonomy_contract.restore_point.human_gate_required",
        "recovery_contract_field": "recovery_contract",
        "continuation_state_field": "continuation_state",
        "family_checkpoint_lineage_field": "family_checkpoint_lineage",
        "autonomy_soak_status_field": "autonomy_soak_status",
        "quality_closure_truth_field": "quality_closure_truth",
        "quality_execution_lane_field": "quality_execution_lane",
        "same_line_route_truth_field": "same_line_route_truth",
        "same_line_route_surface_field": "same_line_route_surface",
        "quality_repair_batch_followthrough_field": "quality_repair_batch_followthrough",
        "quality_review_followthrough_field": "quality_review_followthrough",
        "gate_clearing_batch_followthrough_field": "gate_clearing_batch_followthrough",
        "research_runtime_control_projection_field": "research_runtime_control_projection",
        "artifact_pickup_field": "research_runtime_control_projection.artifact_pickup_surface",
        "artifact_pickup_refs_field": "research_runtime_control_projection.artifact_pickup_surface.pickup_refs",
        "runtime_human_gate_field": "research_runtime_control_projection.research_gate_surface",
    }
    assert payload["return_surface_contract"]["research_runtime_control_projection_contract"] == {
        "surface_kind": "research_runtime_control_projection_contract",
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
                + " --study-id 001-risk"
            ),
            "check_progress": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk --format json"
            ),
            "check_runtime_status": (
                "uv run python -m med_autoscience.cli study-runtime-status --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
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
    assert payload["return_surface_contract"]["domain_entry_contract"]["service_safe_surface_kind"] == (
        "med_autoscience_service_safe_domain_entry"
    )
    assert payload["return_surface_contract"]["domain_entry_contract"]["supported_commands"] == [
        "workspace-cockpit",
        "product-frontdesk",
        "product-preflight",
        "product-start",
        "product-entry-manifest",
        "skill-catalog",
        "study-progress",
        "study-runtime-status",
        "launch-study",
        "submit-study-task",
        "build-product-entry",
    ]
    assert payload["return_surface_contract"]["domain_entry_contract"]["domain_agent_entry_spec"] == {
        "surface_kind": "domain_agent_entry_spec",
        "agent_id": "mas",
        "title": "MAS Domain Agent Entry (v1)",
        "description": "MAS 通过 domain agent entry contract 暴露可审计的入口与进度语义，用于研究任务与投稿包的受控推进。",
        "default_engine": "codex",
        "workspace_requirement": "required",
        "locator_schema": {
            "required_fields": ["profile_ref"],
            "optional_fields": ["study_id", "entry_mode"],
        },
        "codex_entry_strategy": "domain_agent_entry",
        "artifact_conventions": "paper_and_submission_package",
        "progress_conventions": "study_runtime_narration",
        "entry_command": "product-frontdesk",
        "manifest_command": "product-entry-manifest",
    }
    assert payload["return_surface_contract"]["gateway_interaction_contract"] == {
        "surface_kind": "gateway_interaction_contract",
        "frontdoor_owner": "opl_gateway_or_domain_gui",
        "user_interaction_mode": "natural_language_frontdoor",
        "user_commands_required": False,
        "command_surfaces_for_agent_consumption_only": True,
        "shared_downstream_entry": "MedAutoScienceDomainEntry",
        "shared_handoff_envelope": [
            "target_domain_id",
            "task_intent",
            "entry_mode",
            "workspace_locator",
            "runtime_session_contract",
            "return_surface_contract",
        ],
    }
    assert payload["return_surface_contract"]["progress_command"].endswith(
        "--study-id 001-risk --format json"
    )
    assert payload["commands"]["workspace_cockpit"].endswith(
        "workspace-cockpit --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["commands"]["launch_study"].endswith("--study-id 001-risk")
    markdown = module.render_build_product_entry_markdown(payload)
    assert "当前任务意图" in markdown
    assert "当前投稿目标" in markdown
    assert "单项目边界摘要" in markdown
    assert "进度真相命令" in markdown
    assert "自治 proof 字段" in markdown
    assert "质量复评跟进字段" in markdown
    assert "gate-clearing 跟进字段" in markdown
    assert "当前入口模式" in markdown
    assert "目标域" in markdown
    assert "task_intent:" not in markdown
    assert "journal_target:" not in markdown
    assert "entry_mode:" not in markdown
    assert "target_domain_id:" not in markdown
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
