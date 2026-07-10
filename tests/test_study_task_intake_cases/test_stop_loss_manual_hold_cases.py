from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_publishability_stop_loss_intake_preempts_reviewer_revision_route() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_id": "study-task::004-invasive-architecture::20260429T020000Z",
        "task_intake_kind": "publishability_stop_loss",
        "task_intent": (
            "临床专家反馈：垂体瘤004没有什么临床意义，Knosp分型的目的就是看侵袭性，"
            "当前结果没有新结论，论文不成立。请及时终止，建立早期止损机制。"
        ),
        "constraints": [
            "不要再按 reviewer revision 修 current_package 或 submission_minimal。",
            "MAS/MDS 自己也要判断可发表性，而不是一直包装发不了论文的稿件。",
        ],
    }

    override = module.build_task_intake_progress_override(payload)
    summary = module.summarize_task_intake(payload)

    assert module.task_intake_is_reviewer_revision(payload) is False
    assert module.task_intake_overrides_auto_manual_finish(payload) is True
    assert summary["stop_loss_intake"]["kind"] == "publishability_stop_loss"
    assert "revision_intake" not in summary
    assert override["current_required_action"] == "stop_runtime"
    assert override["paper_stage"] == "stop"
    assert override["quality_closure_truth"]["state"] == "stop_loss_recommended"
    assert override["quality_execution_lane"]["lane_id"] == "stop_loss"
    assert override["same_line_route_truth"]["route_target"] == "stop"


def test_publishability_stop_loss_task_intake_recommends_stop_runtime_action(tmp_path: Path) -> None:
    intake_module = importlib.import_module("med_autoscience.study_task_intake")
    outer_loop_intake = importlib.import_module("med_autoscience.controllers.study_outer_loop_task_intake")
    study_root = tmp_path / "studies" / "004-invasive-architecture"
    _write_json(
        intake_module.latest_task_intake_json_path(study_root=study_root),
        {
            "task_id": "study-task::004-invasive-architecture::20260429T020000Z",
            "task_intake_kind": "publishability_stop_loss",
            "task_intent": (
                "这篇论文没有临床意义；Knosp 本来就是看侵袭性，当前队列没有新结论，"
                "继续包装会浪费 token，应触发 publishability stop-loss。"
            ),
            "constraints": ["不要路由到 reviewer_revision。"],
        },
    )

    action = outer_loop_intake.recommended_task_intake_action(study_root=study_root)

    assert action is not None
    assert action["action_type"] == "stop_loss"
    assert action["route_target"] == "stop"
    assert action["controller_action_type"] == "stop_runtime"
    assert action["requires_controller_decision"] is True


def test_publishability_stop_loss_requires_structured_task_intake_contract() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_id": "study-task::004-invasive-architecture::20260429T020000Z",
        "task_intent": (
            "用户在背景里提到这条线可能没有临床意义、发不了论文，但没有给出 "
            "task_intake_kind=publishability_stop_loss。"
        ),
        "constraints": ["不要用自由文本关键词推断 runtime truth。"],
    }

    assert module.task_intake_requests_publishability_stop_loss(payload) is False
    assert module.build_publishability_stop_loss_intake(payload) is None
    assert module.build_publishability_stop_loss_progress_override(payload) is None


def test_manual_hold_intake_blocks_auto_recovery_without_stop_loss() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_id": "study-task::004-dpcc::20260505T130334Z",
        "task_intake_kind": "manual_hold",
        "task_intent": (
            "用户确认糖尿病004已经到达里程碑投稿包后手动停止；当前结果没有达到预期，"
            "暂不应由 MAS/MDS 自动恢复写入，等待形成新方案后再显式唤醒大改。"
        ),
        "constraints": [
            "保持当前论文线停驻；不得由 generic runtime repair 或 supervisor redrive 自动恢复写入。",
            "未来若重启必须先形成新的方案和显式 wakeup。",
        ],
    }

    override = module.build_task_intake_progress_override(payload)
    summary = module.summarize_task_intake(payload)

    assert module.task_intake_requests_manual_hold(payload) is True
    assert module.task_intake_overrides_auto_manual_finish(payload) is True
    assert "stop_loss_intake" not in summary
    assert summary["manual_hold_intake"]["kind"] == "manual_hold"
    assert summary["manual_hold_intake"]["auto_recovery_allowed"] is False
    assert override["current_required_action"] == "hold_until_explicit_wakeup"
    assert override["paper_stage"] == "manual_hold"
    assert override["quality_closure_truth"]["state"] == "manual_hold"
    assert override["quality_execution_lane"]["lane_id"] == "manual_hold"


def test_manual_hold_requires_structured_task_intake_contract() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_id": "study-task::004-dpcc::20260505T130334Z",
        "task_intent": (
            "用户描述历史上曾经手动停止，并讨论未来是否需要新方案；这只是说明背景，"
            "没有给出 task_intake_kind=manual_hold。"
        ),
        "constraints": ["不要用自由文本关键词推断 runtime truth。"],
    }

    assert module.task_intake_requests_manual_hold(payload) is False
    assert module.build_manual_hold_intake(payload) is None
    assert module.build_manual_hold_progress_override(payload) is None
