from __future__ import annotations

from tests.product_entry_cases import shared as _shared
from tests.product_entry_cases import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from tests.product_entry_cases import entry_status_focus_cases as _entry_status_focus_cases


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_entry_status_focus_cases)


def test_workspace_cockpit_projects_autonomy_soak_and_quality_followthrough() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    markdown = module.render_workspace_cockpit_markdown(
        {
            "profile_name": "test-profile",
            "workspace_root": "/tmp/test",
            "workspace_status": "ready",
            "workspace_supervision": {"service": {}, "study_counts": {}},
            "operator_brief": {
                "surface_kind": "workspace_operator_brief",
                "verdict": "monitor_only",
                "summary": "当前没有新的 workspace 级硬告警。",
                "should_intervene_now": False,
                "focus_scope": "study",
                "focus_study_id": "001-risk",
                "recommended_step_id": "inspect_progress",
                "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
                "current_focus": "看 publication_eval/latest.json 是否出现新的复评结论。",
            },
            "attention_queue": [
                {
                    "title": "001-risk 当前处在等待系统自动复评",
                    "summary": "当前在等系统自动复评；你现在不用介入，先等待复评回写。",
                    "recommended_step_id": "inspect_study_progress",
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
            "user_loop": {},
            "phase2_user_product_loop": {},
            "commands": {},
            "studies": [],
        }
    )

    assert "自治 Proof / Soak: 最近一次自治外环已转到“论文写作与结果收紧”" in markdown
    assert "质量复评跟进: 等待复评；当前修订计划已完成，下一步应由 MAS 发起 re-review。；看 publication_eval/latest.json 是否出现新的复评结论。" in markdown


def test_workspace_cockpit_attention_queue_carries_runtime_control_pickup_and_gate() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")

    payload = {
        "attention_queue": module._attention_queue(
            workspace_status="ready",
            workspace_supervision={"service": {"loaded": True}, "study_counts": {}},
            commands={},
            studies=[
                {
                "study_id": "001-risk",
                "current_stage": "runtime_soak",
                "current_stage_summary": "runtime soak 正在等待 artifact pickup 与 human gate 确认。",
                "current_blockers": ["需要人工确认后恢复。"],
                "next_system_action": "等待 human gate。",
                "intervention_lane": {
                    "lane_id": "wait_for_user",
                    "recommended_action_id": "human_gate",
                    "summary": "恢复前需要人工确认。",
                },
                "operator_status_card": {
                    "surface_kind": "study_operator_status_card",
                    "handling_state": "waiting_for_human_gate",
                    "user_visible_verdict": "恢复点已冻结；等待人工确认。",
                    "current_focus": "确认是否从冻结恢复点继续。",
                    "next_confirmation_signal": "人工批准后再恢复 runtime。",
                },
                "autonomy_contract": {
                    "summary": "当前自治状态停在 human gate。",
                    "restore_point": {
                        "summary": "恢复点已冻结；恢复前仍需人工确认。",
                        "human_gate_required": True,
                    },
                },
                "autonomy_soak_status": {
                    "summary": "最近一次自治外环已完成 soak dispatch。",
                    "next_confirmation_signal": "看 runtime_watch 是否刷新。",
                },
                "quality_closure_truth": {"summary": "质量闭环已进入 bundle-only 收口。"},
                "quality_review_followthrough": {
                    "summary": "复评已完成，等待 pickup。",
                    "next_confirmation_signal": "看 publication_eval/latest.json。",
                },
                "research_runtime_control_projection": {
                    "surface_kind": "research_runtime_control_projection",
                    "restore_point_surface": {
                        "surface_kind": "study_progress",
                        "field_path": "autonomy_contract.restore_point",
                        "summary": "恢复点已冻结；恢复前仍需人工确认。",
                    },
                    "artifact_pickup_surface": {
                        "surface_kind": "study_progress",
                        "field_path": "refs.evaluation_summary_path",
                        "pickup_refs": [
                            {
                                "ref_id": "publication_eval_path",
                                "path": "/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
                            }
                        ],
                    },
                    "research_gate_surface": {
                        "surface_kind": "study_progress",
                        "approval_gate_field": "needs_user_decision",
                        "approval_gate_required": True,
                        "approval_gate_owner": "mas_controller",
                        "interrupt_policy_field": "intervention_lane.recommended_action_id",
                        "interrupt_policy": "human_gate",
                    },
                },
                "recommended_command": (
                    "uv run python -m med_autoscience.cli study-progress "
                    "--profile profile.local.toml --study-id 001-risk"
                ),
                "recommended_commands": [],
                "recovery_contract": {
                    "contract_kind": "study_recovery_contract",
                    "lane_id": "wait_for_user",
                    "action_mode": "monitor_only",
                    "summary": "等待 human gate。",
                    "recommended_step_id": "inspect_study_progress",
                    "steps": [],
                },
                "needs_physician_decision": True,
                "supervision": {},
                "task_intake": {},
                "progress_freshness": {"status": "fresh"},
                }
            ],
        ),
    }
    payload["operator_brief"] = module._workspace_operator_brief(
        workspace_status="ready",
        workspace_alerts=[],
        attention_queue=payload["attention_queue"],
        studies=[],
        user_loop={},
        commands={},
    )

    attention_item = payload["attention_queue"][0]
    assert attention_item["research_runtime_control_projection"]["restore_point_surface"]["field_path"] == (
        "autonomy_contract.restore_point"
    )
    assert attention_item["research_runtime_control_projection"]["artifact_pickup_surface"]["pickup_refs"] == [
        {
            "ref_id": "publication_eval_path",
            "path": "/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
        }
    ]
    assert attention_item["research_runtime_control_projection"]["research_gate_surface"]["approval_gate_required"] is True
    assert (
        payload["operator_brief"]["research_runtime_control_projection"]["research_gate_surface"]["interrupt_policy"]
        == "human_gate"
    )
