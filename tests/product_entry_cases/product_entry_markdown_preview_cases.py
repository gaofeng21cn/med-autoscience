from __future__ import annotations

from . import shared as _shared
from . import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from . import cockpit_status_and_entry_status_focus as _cockpit_status_and_entry_status_focus
from . import manifest_launch_and_task_intake as _manifest_launch_and_task_intake
from . import repo_shell_and_handoff_templates as _repo_shell_and_handoff_templates


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_cockpit_status_and_entry_status_focus)
_module_reexport(_manifest_launch_and_task_intake)
_module_reexport(_repo_shell_and_handoff_templates)


def _product_entry_status_payload(queue_item: dict[str, object]) -> dict[str, object]:
    return {
        "workspace_preview": None,
        "workspace_attention_queue_preview": [queue_item],
        "phase2_user_product_loop": {},
        "product_entry_guardrails": {},
        "phase3_clearance_lane": {"clearance_targets": [], "clearance_loop": []},
        "phase4_backend_deconstruction": {"substrate_targets": []},
        "phase5_platform_target": {"capability_targets": [], "readiness_gates": []},
        "remaining_gaps": [],
    }


def test_render_product_entry_status_markdown_hides_preview_raw_summary_keys() -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    queue_items = [
        {
            "title": "001-risk 当前需要优先恢复托管运行",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            "operator_status_card": {"handling_state": "runtime_recovering"},
            "autonomy_contract": {
                "summary": "恢复点已冻结；当前停在 resume_from_checkpoint，下一次确认看恢复信号。",
                "restore_point": {"summary": "当前恢复点采用 resume_from_checkpoint。"},
            },
        },
        {
            "title": "001-risk 当前已进入同线定稿与投稿包收尾",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            "quality_closure_truth": {"summary": "核心科学质量已经闭环。"},
        },
        {
            "title": "001-risk 当前先做 claim-evidence 修复",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            "quality_execution_lane": {"summary": "当前质量执行线聚焦 claim-evidence 修复。"},
            "quality_review_loop": {
                "current_phase_label": "等待复评",
                "recommended_next_phase_label": "发起复评",
                "summary": "当前修订计划已完成。",
            },
        },
        {
            "title": "001-risk 当前已进入同线定稿与投稿包收尾",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            "same_line_route_truth": {"summary": "当前同线路由已经收窄到定稿与投稿包收尾。"},
        },
        {
            "title": "001-risk 当前处在等待系统自动复评",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            "operator_status_card": {
                "handling_state": "monitor_only",
                "user_visible_verdict": "当前在等系统自动复评；你现在不用介入。",
                "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论。",
            },
            "autonomy_soak_status": {"summary": "最近一次自治外环已转到论文写作与结果收紧。"},
            "quality_review_loop": {
                "current_phase_label": "等待复评",
                "recommended_next_phase_label": "发起复评",
                "summary": "当前修订计划已完成。",
            },
            "quality_review_followthrough": {
                "state_label": "等待复评",
                "summary": "当前修订计划已完成。",
                "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论。",
            },
        },
        {
            "title": "001-risk 当前进入 gate-clearing followthrough",
            "recommended_command": "uv run python -m med_autoscience.cli study-progress --study-id 001-risk",
            "gate_clearing_followthrough": {
                "state_label": "等待 gate replay",
                "summary": "当前已按 gate-clearing batch 回放 deterministic 修复。",
                "next_confirmation_signal": "看 replay 后的 publication gate 是否收窄。",
            },
        },
        {
            "title": "001-risk 当前进入 quality-repair followthrough",
            "recommended_command": "uv run python -m med_autoscience.cli study quality-repair-batch --study-id 001-risk",
            "quality_repair_followthrough": {
                "state_label": "等待 quality gate replay",
                "summary": "当前已按 quality-repair batch 回放 deterministic 修复。",
                "next_confirmation_signal": "看 publication_eval/latest.json 是否继续收窄 quality blocker。",
            },
        },
    ]

    for queue_item in queue_items:
        markdown = module.render_product_entry_status_markdown(_product_entry_status_payload(queue_item))
        assert markdown.strip(), queue_item["title"]
        assert "summary:" not in markdown, queue_item["title"]


def test_product_entry_manifest_fails_closed_on_invalid_user_interaction_contract_shape(
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
                "summary": "MAS scheduler local adapter runtime supervision 已在线。",
                "drift_reasons": [],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_build_user_interaction_contract",
        lambda: {
            "surface_kind": "user_interaction_contract",
            "entry_owner": "",
        },
    )

    with pytest.raises(ValueError, match="user_interaction_contract"):
        module.build_product_entry_manifest(
            profile=profile,
            profile_ref=profile_ref,
        )
