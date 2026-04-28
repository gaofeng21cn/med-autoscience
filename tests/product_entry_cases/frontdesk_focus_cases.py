from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)


def test_build_product_frontdesk_uses_operator_status_card_for_now_summary(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(
        module,
        "build_product_entry_manifest",
        lambda **kwargs: {
            "surface_kind": "product_entry_manifest",
            "manifest_version": 2,
            "manifest_kind": "med_autoscience_product_entry_manifest",
            "target_domain_id": "med-autoscience",
            "formal_entry": {
                "default": "CLI",
                "supported_protocols": ["MCP"],
                "internal_surface": "controller",
            },
            "workspace_locator": {"profile_name": "test-profile"},
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
                    "surface_kind": "launch_study",
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
                }
            },
            "runtime": {"runtime_owner": "upstream_hermes_agent"},
            "product_entry_status": {"summary": "test status"},
            "frontdesk_surface": {
                "surface_kind": "product_frontdesk",
                "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "summary": "open frontdesk",
            },
            "operator_loop_surface": {
                "surface_kind": "workspace_cockpit",
                "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "summary": "open workspace cockpit",
            },
            "operator_loop_actions": {},
            "product_entry_start": {
                "surface_kind": "product_entry_start",
                "summary": "open frontdesk first",
                "recommended_mode_id": "open_frontdesk",
                "modes": [
                    {
                        "mode_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_surface": {
                    "surface_kind": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                    "session_locator_field": "profile_name",
                },
                "human_gate_ids": ["workspace_gate"],
            },
            "product_entry_overview": {
                "surface_kind": "product_entry_overview",
                "summary": "workspace overview",
                "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "progress_surface": {
                    "surface_kind": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                },
                "resume_surface": {
                    "surface_kind": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                    "session_locator_field": "profile_name",
                },
                "recommended_step_id": "open_frontdesk",
                "next_focus": ["open workspace cockpit"],
                "remaining_gaps_count": 0,
                "human_gate_ids": ["workspace_gate"],
            },
            "domain_entry_contract": {
                "entry_adapter": "MedAutoScienceDomainEntry",
                "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry",
                "product_entry_builder_command": "build-product-entry",
                "supported_commands": ["workspace-cockpit"],
                "command_contracts": [
                    {"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}
                ],
            },
            "gateway_interaction_contract": {
                "surface_kind": "gateway_interaction_contract",
                "frontdoor_owner": "opl_gateway_or_domain_gui",
                "user_interaction_mode": "natural_language_frontdoor",
                "user_commands_required": False,
                "command_surfaces_for_agent_consumption_only": True,
                "shared_downstream_entry": "MedAutoScienceDomainEntry",
                "shared_handoff_envelope": ["target_domain_id"],
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
            "product_entry_readiness": {
                "surface_kind": "product_entry_readiness",
                "verdict": "ready_for_task",
                "usable_now": True,
                "good_to_use_now": True,
                "fully_automatic": False,
                "summary": "workspace ready",
                "recommended_start_surface": "product_frontdesk",
                "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                "recommended_loop_surface": "workspace_cockpit",
                "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
                "blocking_gaps": [],
            },
            "product_entry_quickstart": {
                "surface_kind": "product_entry_quickstart",
                "recommended_step_id": "open_frontdesk",
                "summary": "open frontdesk first",
                "steps": [
                    {
                        "step_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_contract": {
                    "surface_kind": "workspace_cockpit",
                    "session_locator_field": "profile_name",
                },
                "human_gate_ids": ["workspace_gate"],
            },
            "family_orchestration": {
                "human_gates": [{"gate_id": "workspace_gate"}],
                "resume_contract": {
                    "surface_kind": "workspace_cockpit",
                    "session_locator_field": "profile_name",
                },
            },
            "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
            "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
            "summary": {
                "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"
            },
        },
    )
    monkeypatch.setattr(
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "attention_required",
                "summary": "generic summary",
                "should_intervene_now": True,
                "focus_scope": "study",
                "focus_study_id": "001-risk",
                "recommended_step_id": "handle_attention_item",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
            },
            "attention_queue": [
                {
                    "scope": "study",
                    "study_id": "001-risk",
                    "code": "study_quality_floor_blocker",
                    "title": "001-risk 当前需要刷新投稿包镜像",
                    "summary": "generic summary",
                    "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                    "operator_status_card": {
                        "surface_kind": "study_operator_status_card",
                        "handling_state": "paper_surface_refresh_in_progress",
                        "current_focus": "优先同步投稿包镜像。",
                        "next_confirmation_signal": "看 delivery_manifest 和 current_package 是否被刷新。",
                        "user_visible_verdict": "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。",
                    },
                }
            ],
        },
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
    markdown = module.render_product_frontdesk_markdown(payload)

    assert payload["operator_brief"]["summary"] == "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    assert payload["operator_brief"]["focus_study_id"] == "001-risk"
    assert "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。" in markdown


def test_build_product_frontdesk_uses_same_line_route_truth_for_current_focus(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(
        module,
        "build_product_entry_manifest",
        lambda **kwargs: {
            "surface_kind": "product_entry_manifest",
            "manifest_version": 2,
            "manifest_kind": "med_autoscience_product_entry_manifest",
            "target_domain_id": "med-autoscience",
            "formal_entry": {"default": "CLI", "supported_protocols": ["MCP"], "internal_surface": "controller"},
            "workspace_locator": {"profile_name": "test-profile"},
            "product_entry_shell": {
                "product_frontdesk": {"command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk"},
                "workspace_cockpit": {"command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "surface_kind": "workspace_cockpit"},
                "submit_study_task": {"command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml", "surface_kind": "study_task_intake"},
                "launch_study": {"command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml", "surface_kind": "launch_study"},
                "study_progress": {"command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml", "surface_kind": "study_progress"},
                "mainline_status": {"command": "uv run python -m med_autoscience.cli mainline-status", "surface_kind": "mainline_status"},
                "mainline_phase": {"command": "uv run python -m med_autoscience.cli mainline-phase", "surface_kind": "mainline_phase"},
            },
            "shared_handoff": {"direct_entry_builder": {"command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct", "entry_mode": "direct"}},
            "runtime": {"runtime_owner": "upstream_hermes_agent"},
            "product_entry_status": {"summary": "test status"},
            "frontdesk_surface": {"surface_kind": "product_frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "summary": "open frontdesk"},
            "operator_loop_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "summary": "open workspace cockpit"},
            "operator_loop_actions": {},
            "product_entry_start": {
                "surface_kind": "product_entry_start",
                "summary": "open frontdesk first",
                "recommended_mode_id": "open_frontdesk",
                "modes": [
                    {
                        "mode_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"},
                "human_gate_ids": ["workspace_gate"],
            },
            "product_entry_overview": {"surface_kind": "product_entry_overview", "summary": "workspace overview", "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "progress_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"}, "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "recommended_step_id": "open_frontdesk", "next_focus": ["open workspace cockpit"], "remaining_gaps_count": 0, "human_gate_ids": ["workspace_gate"]},
            "domain_entry_contract": {"entry_adapter": "MedAutoScienceDomainEntry", "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry", "product_entry_builder_command": "build-product-entry", "supported_commands": ["workspace-cockpit"], "command_contracts": [{"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}]},
            "gateway_interaction_contract": {"surface_kind": "gateway_interaction_contract", "frontdoor_owner": "opl_gateway_or_domain_gui", "user_interaction_mode": "natural_language_frontdoor", "user_commands_required": False, "command_surfaces_for_agent_consumption_only": True, "shared_downstream_entry": "MedAutoScienceDomainEntry", "shared_handoff_envelope": ["target_domain_id"]},
            "product_entry_preflight": {"surface_kind": "product_entry_preflight", "summary": "preflight ready", "ready_to_try_now": True, "recommended_check_command": "uv run python -m med_autoscience.cli doctor", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "blocking_check_ids": [], "checks": []},
            "product_entry_readiness": {"surface_kind": "product_entry_readiness", "verdict": "ready_for_task", "usable_now": True, "good_to_use_now": True, "fully_automatic": False, "summary": "workspace ready", "recommended_start_surface": "product_frontdesk", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_loop_surface": "workspace_cockpit", "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "blocking_gaps": []},
            "product_entry_quickstart": {
                "surface_kind": "product_entry_quickstart",
                "recommended_step_id": "open_frontdesk",
                "summary": "open frontdesk first",
                "steps": [
                    {
                        "step_id": "open_frontdesk",
                        "title": "Open frontdesk",
                        "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml",
                        "surface_kind": "product_frontdesk",
                        "summary": "open frontdesk",
                        "requires": [],
                    }
                ],
                "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"},
                "human_gate_ids": ["workspace_gate"],
            },
            "family_orchestration": {"human_gates": [{"gate_id": "workspace_gate"}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}},
            "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
            "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
            "summary": {"recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"},
        },
    )
    monkeypatch.setattr(
        module,
        "read_workspace_cockpit",
        lambda **kwargs: {
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "attention_required",
                "summary": "当前 workspace 有关注项。",
                "should_intervene_now": True,
                "focus_scope": "study",
                "focus_study_id": "001-risk",
                "recommended_step_id": "handle_attention_item",
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
            },
            "attention_queue": [
                {
                    "scope": "study",
                    "study_id": "001-risk",
                    "code": "study_quality_floor_blocker",
                    "title": "001-risk 当前先做 claim-evidence 修复",
                    "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“当前稿面最窄的 claim-evidence 修复动作是什么？”。",
                    "recommended_step_id": "inspect_study_progress",
                    "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                    "operator_status_card": {
                        "surface_kind": "study_operator_status_card",
                        "handling_state": "scientific_or_quality_repair_in_progress",
                        "next_confirmation_signal": "看 publication_eval/latest.json 是否继续收窄当前修复线。",
                        "user_visible_verdict": "MAS 正在处理当前论文线的质量修复。",
                    },
                    "same_line_route_truth": {
                        "surface_kind": "same_line_route_truth",
                        "same_line_state": "bounded_analysis",
                        "same_line_state_label": "有限补充分析",
                        "route_mode": "enter",
                        "route_target": "analysis-campaign",
                        "route_target_label": "补充分析与稳健性验证",
                        "summary": "当前论文线仍在同线质量修复；先进入 analysis-campaign 收口当前最窄 claim-evidence 缺口。",
                        "current_focus": "当前稿面最窄的 claim-evidence 修复动作是什么？",
                    },
                }
            ],
        },
    )

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["operator_brief"]["recommended_step_id"] == "inspect_study_progress"
    assert payload["operator_brief"]["current_focus"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"


def test_build_product_frontdesk_uses_quality_review_followthrough_for_monitor_focus(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(module, "build_product_entry_manifest", lambda **kwargs: {
        "surface_kind": "product_entry_manifest",
        "manifest_version": 2,
        "manifest_kind": "med_autoscience_product_entry_manifest",
        "target_domain_id": "med-autoscience",
        "formal_entry": {"default": "CLI", "supported_protocols": ["MCP"], "internal_surface": "controller"},
        "workspace_locator": {"profile_name": "test-profile"},
        "product_entry_shell": {
            "product_frontdesk": {"command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk"},
            "workspace_cockpit": {"command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "surface_kind": "workspace_cockpit"},
            "submit_study_task": {"command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml", "surface_kind": "study_task_intake"},
            "launch_study": {"command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml", "surface_kind": "launch_study"},
            "study_progress": {"command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml", "surface_kind": "study_progress"},
            "mainline_status": {"command": "uv run python -m med_autoscience.cli mainline-status", "surface_kind": "mainline_status"},
            "mainline_phase": {"command": "uv run python -m med_autoscience.cli mainline-phase", "surface_kind": "mainline_phase"},
        },
        "shared_handoff": {"direct_entry_builder": {"command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct", "entry_mode": "direct"}},
        "runtime": {"runtime_owner": "upstream_hermes_agent"},
        "product_entry_status": {"summary": "test status"},
        "frontdesk_surface": {"surface_kind": "product_frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "summary": "open frontdesk"},
        "operator_loop_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "summary": "open workspace cockpit"},
        "operator_loop_actions": {},
        "product_entry_start": {"surface_kind": "product_entry_start", "summary": "open frontdesk first", "recommended_mode_id": "open_frontdesk", "modes": [{"mode_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "product_entry_overview": {"surface_kind": "product_entry_overview", "summary": "workspace overview", "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "progress_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"}, "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "recommended_step_id": "open_frontdesk", "next_focus": ["open workspace cockpit"], "remaining_gaps_count": 0, "human_gate_ids": ["workspace_gate"]},
        "domain_entry_contract": {"entry_adapter": "MedAutoScienceDomainEntry", "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry", "product_entry_builder_command": "build-product-entry", "supported_commands": ["workspace-cockpit"], "command_contracts": [{"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}]},
        "gateway_interaction_contract": {"surface_kind": "gateway_interaction_contract", "frontdoor_owner": "opl_gateway_or_domain_gui", "user_interaction_mode": "natural_language_frontdoor", "user_commands_required": False, "command_surfaces_for_agent_consumption_only": True, "shared_downstream_entry": "MedAutoScienceDomainEntry", "shared_handoff_envelope": ["target_domain_id"]},
        "product_entry_preflight": {"surface_kind": "product_entry_preflight", "summary": "preflight ready", "ready_to_try_now": True, "recommended_check_command": "uv run python -m med_autoscience.cli doctor", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "blocking_check_ids": [], "checks": []},
        "product_entry_readiness": {"surface_kind": "product_entry_readiness", "verdict": "ready_for_task", "usable_now": True, "good_to_use_now": True, "fully_automatic": False, "summary": "workspace ready", "recommended_start_surface": "product_frontdesk", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_loop_surface": "workspace_cockpit", "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "blocking_gaps": []},
        "product_entry_quickstart": {"surface_kind": "product_entry_quickstart", "recommended_step_id": "open_frontdesk", "summary": "open frontdesk first", "steps": [{"step_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "family_orchestration": {"human_gates": [{"gate_id": "workspace_gate"}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}},
        "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
        "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
        "summary": {"recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"},
        "single_project_boundary": {"surface_kind": "single_project_boundary", "summary": "summary", "mas_owner_modules": ["controller_charter"], "mds_retained_roles": [{"role_id": "research_backend", "title": "Controlled research backend", "summary": "summary"}], "post_gate_only": ["physical monorepo absorb"], "not_now": ["not now"]},
    })
    monkeypatch.setattr(module, "read_workspace_cockpit", lambda **kwargs: {
        "operator_brief": {
            "surface_kind": "workspace_operator_brief",
            "verdict": "monitor_only",
            "summary": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
            "should_intervene_now": False,
            "focus_scope": "study",
            "focus_study_id": "001-risk",
            "recommended_step_id": "inspect_study_progress",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk",
            "current_focus": "看 publication_eval/latest.json 是否出现新的复评结论。",
        },
        "attention_queue": [],
    })

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["operator_brief"]["recommended_step_id"] == "open_workspace_cockpit"
    assert payload["operator_brief"]["current_focus"] == "看 publication_eval/latest.json 是否出现新的复评结论。"


def test_build_product_frontdesk_uses_gate_clearing_followthrough_for_attention_brief(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    followthrough_command = (
        "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml --study-id 001-risk"
    )
    followthrough_summary = "当前已按 gate-clearing batch 回放 deterministic 修复，正在等待新的 publication gate 结论。"
    next_signal = "看 replay 后的 publication gate 是否收窄 medical_publication_surface_blocked。"

    monkeypatch.setattr(module, "build_product_entry_manifest", lambda **kwargs: {
        "surface_kind": "product_entry_manifest",
        "manifest_version": 2,
        "manifest_kind": "med_autoscience_product_entry_manifest",
        "target_domain_id": "med-autoscience",
        "formal_entry": {"default": "CLI", "supported_protocols": ["MCP"], "internal_surface": "controller"},
        "workspace_locator": {"profile_name": "test-profile"},
        "product_entry_shell": {
            "product_frontdesk": {"command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk"},
            "workspace_cockpit": {"command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "surface_kind": "workspace_cockpit"},
            "submit_study_task": {"command": "uv run python -m med_autoscience.cli submit-study-task --profile profile.local.toml", "surface_kind": "study_task_intake"},
            "launch_study": {"command": "uv run python -m med_autoscience.cli launch-study --profile profile.local.toml", "surface_kind": "launch_study"},
            "study_progress": {"command": "uv run python -m med_autoscience.cli study-progress --profile profile.local.toml", "surface_kind": "study_progress"},
            "mainline_status": {"command": "uv run python -m med_autoscience.cli mainline-status", "surface_kind": "mainline_status"},
            "mainline_phase": {"command": "uv run python -m med_autoscience.cli mainline-phase", "surface_kind": "mainline_phase"},
        },
        "shared_handoff": {"direct_entry_builder": {"command": "uv run python -m med_autoscience.cli build-product-entry --entry-mode direct", "entry_mode": "direct"}},
        "runtime": {"runtime_owner": "upstream_hermes_agent"},
        "product_entry_status": {"summary": "test status"},
        "frontdesk_surface": {"surface_kind": "product_frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "summary": "open frontdesk"},
        "operator_loop_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "summary": "open workspace cockpit"},
        "operator_loop_actions": {},
        "product_entry_start": {"surface_kind": "product_entry_start", "summary": "open frontdesk first", "recommended_mode_id": "open_frontdesk", "modes": [{"mode_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "product_entry_overview": {"surface_kind": "product_entry_overview", "summary": "workspace overview", "frontdesk_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "operator_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "progress_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"}, "resume_surface": {"surface_kind": "workspace_cockpit", "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "session_locator_field": "profile_name"}, "recommended_step_id": "open_frontdesk", "next_focus": ["open workspace cockpit"], "remaining_gaps_count": 0, "human_gate_ids": ["workspace_gate"]},
        "domain_entry_contract": {"entry_adapter": "MedAutoScienceDomainEntry", "service_safe_surface_kind": "med_autoscience_service_safe_domain_entry", "product_entry_builder_command": "build-product-entry", "supported_commands": ["workspace-cockpit"], "command_contracts": [{"command": "workspace-cockpit", "required_fields": [], "optional_fields": []}]},
        "gateway_interaction_contract": {"surface_kind": "gateway_interaction_contract", "frontdoor_owner": "opl_gateway_or_domain_gui", "user_interaction_mode": "natural_language_frontdoor", "user_commands_required": False, "command_surfaces_for_agent_consumption_only": True, "shared_downstream_entry": "MedAutoScienceDomainEntry", "shared_handoff_envelope": ["target_domain_id"]},
        "product_entry_preflight": {"surface_kind": "product_entry_preflight", "summary": "preflight ready", "ready_to_try_now": True, "recommended_check_command": "uv run python -m med_autoscience.cli doctor", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "blocking_check_ids": [], "checks": []},
        "product_entry_readiness": {"surface_kind": "product_entry_readiness", "verdict": "ready_for_task", "usable_now": True, "good_to_use_now": True, "fully_automatic": False, "summary": "workspace ready", "recommended_start_surface": "product_frontdesk", "recommended_start_command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "recommended_loop_surface": "workspace_cockpit", "recommended_loop_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml", "blocking_gaps": []},
        "product_entry_quickstart": {"surface_kind": "product_entry_quickstart", "recommended_step_id": "open_frontdesk", "summary": "open frontdesk first", "steps": [{"step_id": "open_frontdesk", "title": "Open frontdesk", "command": "uv run python -m med_autoscience.cli product-frontdesk --profile profile.local.toml", "surface_kind": "product_frontdesk", "summary": "open frontdesk", "requires": []}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}, "human_gate_ids": ["workspace_gate"]},
        "family_orchestration": {"human_gates": [{"gate_id": "workspace_gate"}], "resume_contract": {"surface_kind": "workspace_cockpit", "session_locator_field": "profile_name"}},
        "schema_ref": "contracts/schemas/v1/product-entry-manifest.schema.json",
        "recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml",
        "summary": {"recommended_command": "uv run python -m med_autoscience.cli workspace-cockpit --profile profile.local.toml"},
        "single_project_boundary": {"surface_kind": "single_project_boundary", "summary": "summary", "mas_owner_modules": ["controller_charter"], "mds_retained_roles": [{"role_id": "research_backend", "title": "Controlled research backend", "summary": "summary"}], "post_gate_only": ["physical monorepo absorb"], "not_now": ["not now"]},
    })
    monkeypatch.setattr(module, "read_workspace_cockpit", lambda **kwargs: {
        "operator_brief": {
            "surface_kind": "workspace_operator_brief",
            "verdict": "attention_required",
            "summary": followthrough_summary,
            "should_intervene_now": True,
            "focus_scope": "study",
            "focus_study_id": "001-risk",
            "recommended_step_id": "inspect_gate_clearing_followthrough",
            "recommended_command": followthrough_command,
            "current_focus": next_signal,
        },
        "attention_queue": [
            {
                "study_id": "001-risk",
                "code": "study_quality_floor_blocker",
                "title": "001-risk 当前进入 gate-clearing followthrough",
                "summary": followthrough_summary,
                "recommended_step_id": "inspect_gate_clearing_followthrough",
                "recommended_command": followthrough_command,
                "operator_status_card": {
                    "handling_state": "monitor_only",
                },
                "gate_clearing_followthrough": {
                    "surface_kind": "gate_clearing_followthrough",
                    "state": "waiting_gate_replay",
                    "state_label": "等待 gate replay",
                    "summary": followthrough_summary,
                    "next_confirmation_signal": next_signal,
                    "recommended_step_id": "inspect_gate_clearing_followthrough",
                    "recommended_command": followthrough_command,
                },
            }
        ],
    })

    payload = module.build_product_frontdesk(profile=profile, profile_ref=profile_ref)

    assert payload["operator_brief"]["summary"] == followthrough_summary
    assert payload["operator_brief"]["recommended_step_id"] == "inspect_gate_clearing_followthrough"
    assert payload["operator_brief"]["recommended_command"] == followthrough_command
    assert payload["operator_brief"]["current_focus"] == next_signal


