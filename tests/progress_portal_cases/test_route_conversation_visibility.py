from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_text
from tests.test_progress_portal import _progress_payload


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_study_workbench_projects_intervention_lane_as_readable_route_decision() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress={
            **_progress_payload(),
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "title": "优先收口同线质量硬阻塞",
                "route_target": "write",
                "route_target_label": "论文写作与结果收紧",
                "route_key_question": "把 10 条用户意见映射到修订计划",
                "route_summary": "最新 task intake 已重开同一论文线，先回到写作与结果收紧。",
                "repair_mode": "same_line_route_back",
                "recommended_action_id": "continue_write_stage",
            },
            "refs": {
                "controller_decision": "studies/001-risk/artifacts/controller_decisions/latest.json",
            },
        },
        cockpit={},
        runtime={},
        package={},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)

    route = payload["route_decision_trail"]
    route_map = payload["route_map"]
    assert route["status"] == "available"
    assert route["active_path"] == "write"
    assert route["winning_path"] == "write"
    assert route["nodes"][0]["route_id"] == "write"
    assert route["nodes"][0]["label"] == "论文写作与结果收紧"
    assert route["nodes"][0]["decision"] == "same_line_route_back"
    assert route["nodes"][0]["evidence_point"] == "把 10 条用户意见映射到修订计划"
    assert route["nodes"][0]["pivot_rationale"] == "最新 task intake 已重开同一论文线，先回到写作与结果收紧。"
    assert route_map["surface_kind"] == "mas_progress_portal_route_map"
    assert route_map["status"] == "available"
    assert {node["kind"] for node in route_map["nodes"]} >= {"stage", "route", "decision"}
    assert any(edge["kind"] == "advance" for edge in route_map["edges"])
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in route_map["source_refs"]
    assert "route-map-svg" in html
    assert "研究路线地图" in html
    assert "data-route-kind=\"route\"" in html
    assert "切换理由" in html
    assert "路线 / 决策" in html
    assert "当前路线：write" in html
    assert "论文写作与结果收紧" in html
    assert "最新 task intake 已重开同一论文线" in html


def test_study_workbench_route_map_fails_closed_without_route_lineage() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress=_progress_payload(),
        cockpit={},
        runtime={},
        package={},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)

    route_map = payload["route_map"]
    assert route_map["status"] == "missing"
    assert route_map["nodes"] == []
    assert route_map["edges"] == []
    assert route_map["conditions"]["missing"] == ["route_lineage"]
    assert "缺少研究路线来源" in html
    assert "本页面不从阶段文案、文件名或产物路径猜测路线。" in html


def test_study_workbench_route_map_renders_clickable_node_details_and_conversation_anchors() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    conversation_payload = {
        "surface_kind": "mas_runtime_conversation_read_model",
        "selected_study_id": "001-risk",
        "timeline": [
            {
                "sequence": 1,
                "item_kind": "user_message",
                "study_id": "001-risk",
                "message_id": "msg-route-change",
                "source_ref": "studies/001-risk/artifacts/runtime/user_message_queue.json",
            },
            {
                "sequence": 2,
                "item_kind": "turn_receipt",
                "study_id": "001-risk",
                "run_id": "run-route-001",
                "turn_status": "completed",
                "source_ref": "studies/001-risk/artifacts/runtime/turn_receipts.jsonl",
            },
        ],
        "source_refs": [
            {"study_id": "001-risk", "source_ref": "studies/001-risk/artifacts/runtime/turn_receipts.jsonl"}
        ],
    }

    payload = parts.build_study_workbench_payload(
        progress={
            **_progress_payload(),
            "route_decision_trail": {
                "active_path": "analysis-route-b",
                "winning_path": "analysis-route-b",
                "nodes": [
                    {
                        "route_id": "analysis-route-a",
                        "label": "旧路线",
                        "evidence_point": "外部验证不足",
                        "blocked_reason": "外部验证未通过",
                        "superseded_by": "analysis-route-b",
                    },
                    {
                        "route_id": "analysis-route-b",
                        "label": "新路线",
                        "decision": "continue",
                        "evidence_point": "亚组证据更强",
                    },
                ],
                "source_refs": ["studies/001-risk/artifacts/controller_decisions/latest.json"],
            },
            "artifact_locators": [
                {
                    "group": "draft",
                    "label": "canonical manuscript draft",
                    "ref": "studies/001-risk/paper/manuscript.md",
                    "status": "fresh",
                }
            ],
        },
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-route-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
        conversation_payload=conversation_payload,
    )
    html = parts.render_study_workbench_sections(payload)

    edge_kinds = {edge["kind"] for edge in payload["route_map"]["edges"]}
    assert {"advance", "blocked", "reroute", "artifact_generated"} <= edge_kinds
    route_node = next(node for node in payload["route_map"]["nodes"] if node["id"] == "route-analysis-route-a")
    assert "conversation-seq-1" in route_node["conversation_refs"]
    run_node = next(node for node in payload["route_map"]["nodes"] if node["kind"] == "run")
    assert run_node["conversation_refs"] == ["conversation-seq-2"]
    assert 'class="route-node-link" href="#route-node-detail-route-analysis-route-a"' in html
    assert 'id="route-node-detail-route-analysis-route-a"' in html
    assert '<a href="#conversation-seq-1">conversation-seq-1</a>' in html
    assert '<a href="#conversation-seq-2">conversation-seq-2</a>' in html
    assert "产物：studies/001-risk/paper/manuscript.md" in html
    assert "route-edge--reroute" in html
    assert "route-edge--artifact-generated" in html
    assert 'id="conversation-seq-1"' in html
    assert 'id="conversation-seq-2"' in html


def test_study_workbench_conversation_prioritizes_human_messages_and_turns_over_event_refs() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    noisy_timeline = [
        {
            "sequence": index,
            "item_kind": "runtime_lifecycle_event",
            "study_id": "001-risk",
            "event_name": f"artifact_interact_{index}",
            "source_ref": "runtime/quests/001/artifacts/runtime/mas_runtime_events.jsonl",
        }
        for index in range(30)
    ]
    conversation_payload = {
        "surface_kind": "mas_runtime_conversation_read_model",
        "selected_study_id": "001-risk",
        "read_only": True,
        "timeline_summary": {
            "item_count": 33,
            "counts_by_kind": {
                "runtime_lifecycle_event": 30,
                "user_message": 1,
                "turn_receipt": 1,
                "latest_turn_receipt_ref": 1,
            },
        },
        "timeline": noisy_timeline
        + [
            {
                "sequence": 31,
                "item_kind": "user_message",
                "study_id": "001-risk",
                "message_id": "msg-reviewer-feedback",
                "message_status": "completed",
                "content_ref": "content_present",
                "source_ref": "runtime/quests/001/artifacts/runtime/user_message_queue.json",
            },
            {
                "sequence": 32,
                "item_kind": "turn_receipt",
                "study_id": "001-risk",
                "run_id": "run-001",
                "turn_reason": "queued_user_messages",
                "turn_status": "completed",
                "tool_refs": [{"kind": "tool", "value": "study_progress"}],
                "source_ref": "runtime/quests/001/artifacts/runtime/turn_receipts.jsonl",
            },
            {
                "sequence": 33,
                "item_kind": "latest_turn_receipt_ref",
                "study_id": "001-risk",
                "run_id": "run-001",
                "turn_reason": "continue_supervising_runtime",
                "turn_status": "completed",
                "source_ref": "runtime/quests/001/artifacts/runtime/latest_turn_receipt.json",
            },
        ],
        "source_refs": [],
    }

    payload = parts.build_study_workbench_payload(
        progress=_progress_payload(),
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
        conversation_payload=conversation_payload,
    )
    html = parts.render_study_workbench_sections(payload)
    kinds = [item["item_kind"] for item in payload["conversation"]["timeline_items"]]

    assert "user_message" in kinds
    assert "turn_receipt" in kinds
    assert "latest_turn_receipt_ref" in kinds
    assert payload["conversation"]["timeline_summary"]["counts_by_kind"]["user_message"] == 1
    assert "conversation-timeline" in html
    assert "conversation-item--user_message" in html
    assert "conversation-item--turn_receipt" in html
    assert "id=\"conversation-seq-31\"" in html
    assert "用户消息" in html
    assert "msg-reviewer-feedback" in html
    assert "执行回合" in html
    assert "queued_user_messages" in html
    assert "共 33 条；用户消息 1 条；执行回合 1 条；最近回合 1 条" in html


def test_progress_portal_materialization_surfaces_selected_study_conversation(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {"study_id": study_id, "quest_id": quest_id, "quest_root": str(quest_root), "active_run_id": "run-001"},
    )
    _write_json(
        quest_root / "artifacts" / "runtime" / "user_message_queue.json",
        {
            "pending": [
                {
                    "message_id": "msg-portal",
                    "content": "解释当前阻塞。",
                    "recorded_at": "2026-05-09T01:00:00+00:00",
                }
            ],
            "completed": [],
        },
    )
    write_text(
        quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl",
        json.dumps(
            {
                "run_id": "run-001",
                "reason": "user_message",
                "status": "completed",
                "recorded_at": "2026-05-09T01:01:00+00:00",
            },
            ensure_ascii=False,
        )
        + "\n",
    )

    result = module.materialize_progress_portal(
        profile=profile,
        study_id=study_id,
        progress_payload=_progress_payload(study_id),
        runtime_payload={"study_id": study_id, "active_run_id": "run-001"},
        package_payload={"study_id": study_id},
        generated_at="2026-05-09T01:02:00+00:00",
    )

    payload_path = Path(result["study_pages"][study_id]["payload_path"])
    html_path = Path(result["study_pages"][study_id]["html_path"])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")
    assert payload["study_workbench"]["conversation"]["status"] == "available"
    assert "执行器对话" in html
    assert "msg-portal" in html
    assert "run-001" in html
    assert "artifacts/runtime/conversation_read_model/latest.json" in payload["study_workbench"]["conversation"][
        "source_refs"
    ]


def test_progress_portal_materialized_unselected_study_pages_use_canonical_progress(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    selected_id = "001-risk"
    unselected_id = "002-risk"
    write_text(profile.studies_root / selected_id / "study.yaml", f"study_id: {selected_id}\n")
    write_text(profile.studies_root / unselected_id / "study.yaml", f"study_id: {unselected_id}\n")

    def fake_read_study_progress(**kwargs):
        assert kwargs["sync_runtime_summary"] is False
        if kwargs["study_id"] != unselected_id:
            return _progress_payload(kwargs["study_id"])
        return {
            **_progress_payload(unselected_id),
            "intervention_lane": {
                "route_target": "write",
                "route_target_label": "论文写作与结果收紧",
                "route_key_question": "把用户反馈映射到修订计划",
                "route_summary": "从泛化运行回到同线写作修订。",
                "repair_mode": "same_line_route_back",
            },
            "refs": {
                "controller_decision_path": f"studies/{unselected_id}/artifacts/controller_decisions/latest.json",
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.materialize_progress_portal(
        profile=profile,
        study_id=selected_id,
        progress_payload=_progress_payload(selected_id),
        cockpit_payload={
            "workspace_status": "active",
            "studies": [
                {"study_id": selected_id, "state_label": "选中论文线"},
                {
                    "study_id": unselected_id,
                    "state_label": "工作区行状态",
                    "operator_focus": "workspace row fallback only",
                },
            ],
        },
        generated_at="2026-05-09T01:02:00+00:00",
    )

    payload_path = Path(result["study_pages"][unselected_id]["payload_path"])
    html_path = Path(result["study_pages"][unselected_id]["html_path"])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")

    route = payload["study_workbench"]["route_decision_trail"]
    assert route["status"] == "available"
    assert route["active_path"] == "write"
    assert route["nodes"][0]["label"] == "论文写作与结果收紧"
    assert f"studies/{unselected_id}/artifacts/controller_decisions/latest.json" in route["source_refs"]
    assert "论文写作与结果收紧" in html
    assert "workspace row fallback only" not in html
    assert "切换论文线" in html
    assert "论文线入口" not in html
    assert f'href="../{selected_id}/index.html"' in html
    assert f'href="../{unselected_id}/index.html"' in html
